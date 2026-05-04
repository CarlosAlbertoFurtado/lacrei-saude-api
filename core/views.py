"""
Health check e métricas views para monitoramento e observabilidade.

Decisão técnica: Separar endpoints de health check (liveness/readiness)
e métricas para melhor integração com orquestradores (K8s, ECS) e
ferramentas de monitoramento.
"""

import platform
import time

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint detalhado para monitoramento e observabilidade.

    Combina liveness e readiness checks:
    - Liveness: A aplicação está rodando? (sempre true se responder)
    - Readiness: A aplicação está pronta para receber tráfego? (banco OK)

    Usado pelo AWS ALB/ECS para Blue/Green deploy e auto-healing.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "environment": getattr(settings, "DJANGO_SETTINGS_MODULE", "unknown"),
            "version": "2.0.0",
            "checks": {
                "database": {"status": "ok", "latency_ms": None},
                "system": {
                    "platform": platform.system(),
                    "python_version": platform.python_version(),
                },
            },
        }

        try:
            # Verifica conexão e latência do banco
            db_start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_latency = (time.time() - db_start) * 1000
            health["checks"]["database"]["latency_ms"] = round(db_latency, 2)

            # Contagem para métricas de negócio
            from apps.consultas.models import Consulta
            from apps.profissionais.models import Profissional

            health["metrics"] = {
                "total_profissionais": Profissional.objects.count(),
                "total_consultas": Consulta.objects.count(),
                "consultas_futuras": (
                    Consulta.objects.filter(data__gte=time.time()).count()
                    if False
                    else None
                ),  # Placeholder para query futura
            }

            # Métricas de consultas futuras usando timezone
            from django.utils import timezone

            health["metrics"]["consultas_futuras"] = Consulta.objects.filter(
                data__gte=timezone.now()
            ).count()

        except Exception as e:
            health["status"] = "unhealthy"
            health["checks"]["database"] = {
                "status": "error",
                "error": str(e),
            }
            return Response(health, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health, status=status.HTTP_200_OK)


class ReadinessCheckView(APIView):
    """
    Readiness probe simplificado para orquestradores.

    Retorna 200 se o banco está acessível, 503 caso contrário.
    Sem payload pesado - otimizado para alta frequência de polling.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return Response({"ready": True}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"ready": False}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class LivenessCheckView(APIView):
    """
    Liveness probe para orquestradores.

    Sempre retorna 200 se a aplicação está rodando.
    Não verifica dependências externas.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"alive": True}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    """
    Endpoint de métricas para observabilidade.

    Expõe métricas coletadas pelo MetricsMiddleware:
    - Contagem de requests por método e status
    - Latência (avg, p50, p95, p99)
    - Taxa de erros
    - Uptime

    Em produção, proteger com autenticação ou rede interna.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            from core.middleware.metrics_middleware import MetricsCollector

            collector = MetricsCollector()
            metrics = collector.get_metrics()

            # Adicionar métricas de negócio
            from django.utils import timezone

            from apps.consultas.models import Consulta
            from apps.profissionais.models import Profissional

            metrics["business"] = {
                "total_profissionais": Profissional.objects.count(),
                "total_consultas": Consulta.objects.count(),
                "consultas_futuras": Consulta.objects.filter(
                    data__gte=timezone.now()
                ).count(),
            }

            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
