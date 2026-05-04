"""
Middleware de Correlation ID para rastreamento de requisições.

Decisão técnica: Cada requisição recebe um ID único (UUID4) que é propagado
nos logs e retornado no header da resposta. Isso permite rastrear uma
requisição de ponta a ponta em ambientes distribuídos.

Integração:
- Logs: O correlation_id é incluído em todas as mensagens de log
- Response Headers: Retornado como X-Correlation-ID
- Upstream: Se recebido via header, reutiliza o ID existente (para tracing distribuído)
"""

import logging
import threading
import uuid

logger = logging.getLogger("core.middleware")

# Thread-local storage para o correlation ID
_correlation_id = threading.local()


def get_correlation_id():
    """Retorna o correlation ID da requisição atual (thread-safe)."""
    return getattr(_correlation_id, "value", None)


class CorrelationIdMiddleware:
    """
    Middleware que gera/propaga um Correlation ID único por requisição.

    Se o cliente enviar X-Correlation-ID no header, o valor é reutilizado.
    Caso contrário, um novo UUID4 é gerado.

    O ID é disponibilizado via:
    - `get_correlation_id()` para uso em qualquer parte do código
    - Header `X-Correlation-ID` na resposta
    """

    HEADER_NAME = "X-Correlation-ID"
    META_KEY = "HTTP_X_CORRELATION_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Reutilizar ID do upstream ou gerar novo
        correlation_id = request.META.get(self.META_KEY, str(uuid.uuid4()))

        # Armazenar no thread-local
        _correlation_id.value = correlation_id

        # Disponibilizar no request para views/serializers
        request.correlation_id = correlation_id

        response = self.get_response(request)

        # Incluir no header da resposta
        response[self.HEADER_NAME] = correlation_id

        # Limpar thread-local
        _correlation_id.value = None

        return response


class CorrelationIdFilter(logging.Filter):
    """
    Filtro de logging que injeta o correlation_id em todos os log records.

    Uso no LOGGING config:
        'filters': {
            'correlation_id': {
                '()': 'core.middleware.correlation_middleware.CorrelationIdFilter',
            },
        }
    """

    def filter(self, record):
        record.correlation_id = get_correlation_id() or "-"
        return True
