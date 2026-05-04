"""
Middleware de métricas para observabilidade.

Decisão técnica: Coleta métricas de requisições in-memory para exposição
via endpoint /api/metrics/. Em produção, estas métricas podem ser exportadas
para serviços como AWS CloudWatch, Datadog ou Prometheus.

Métricas coletadas:
- Contagem de requisições por método e status code
- Latência média, p50, p95 e p99
- Taxa de erros (4xx e 5xx)
- Uptime da aplicação
"""

import logging
import statistics
import threading
import time
from collections import defaultdict

logger = logging.getLogger("core.middleware")


class MetricsCollector:
    """
    Coletor de métricas thread-safe.

    Armazena métricas in-memory com janela de tempo configurável.
    Para produção em múltiplas instâncias, substituir por Redis ou
    serviço de métricas externo (CloudWatch, Prometheus).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.start_time = time.time()
        self._request_count = defaultdict(int)
        self._status_count = defaultdict(int)
        self._latencies = []
        self._error_count = 0
        self._max_latency_samples = 10000  # Limitar memória
        self._data_lock = threading.Lock()

    def record_request(self, method, path, status_code, duration):
        """Registra uma requisição processada."""
        with self._data_lock:
            self._request_count[method] += 1
            self._status_count[status_code] += 1

            if len(self._latencies) >= self._max_latency_samples:
                self._latencies = self._latencies[-5000:]
            self._latencies.append(duration)

            if status_code >= 400:
                self._error_count += 1

    def get_metrics(self):
        """Retorna snapshot das métricas coletadas."""
        with self._data_lock:
            total_requests = sum(self._request_count.values())
            uptime = time.time() - self.start_time

            latency_stats = {}
            if self._latencies:
                sorted_latencies = sorted(self._latencies)
                latency_stats = {
                    "avg_ms": round(statistics.mean(sorted_latencies) * 1000, 2),
                    "p50_ms": round(
                        sorted_latencies[len(sorted_latencies) // 2] * 1000, 2
                    ),
                    "p95_ms": round(
                        sorted_latencies[int(len(sorted_latencies) * 0.95)] * 1000, 2
                    ),
                    "p99_ms": round(
                        sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000, 2
                    ),
                }

            return {
                "uptime_seconds": round(uptime, 2),
                "total_requests": total_requests,
                "requests_per_method": dict(self._request_count),
                "responses_per_status": dict(self._status_count),
                "error_rate": (
                    round(self._error_count / total_requests * 100, 2)
                    if total_requests > 0
                    else 0
                ),
                "latency": latency_stats,
            }

    def reset(self):
        """Reseta as métricas (útil para testes)."""
        with self._data_lock:
            self._request_count.clear()
            self._status_count.clear()
            self._latencies.clear()
            self._error_count = 0


class MetricsMiddleware:
    """
    Middleware que coleta métricas de todas as requisições HTTP.

    As métricas ficam disponíveis via MetricsCollector.get_metrics()
    e são expostas no endpoint /api/metrics/.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.collector = MetricsCollector()

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time
        self.collector.record_request(
            method=request.method,
            path=request.get_full_path(),
            status_code=response.status_code,
            duration=duration,
        )

        return response
