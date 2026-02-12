"""
Middleware de logging de requisições HTTP.

Decisão técnica: Implementar logging de acesso e erros diretamente
no middleware para ter visibilidade completa de todas as requisições,
independente da view. Isso permite monitoramento e auditoria.
"""

import logging
import time

logger = logging.getLogger("core.middleware")


class RequestLoggingMiddleware:
    """
    Middleware que registra logs de acesso e erros para todas as requisições.

    Registra:
    - Método HTTP, path, IP do cliente
    - Status code da resposta
    - Tempo de processamento
    - Erros (status >= 400)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Captura informações da requisição
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.get_full_path()
        user = getattr(request, "user", None)
        user_info = str(user) if user and user.is_authenticated else "anonymous"

        response = self.get_response(request)

        # Calcula tempo de processamento
        duration = time.time() - start_time
        status_code = response.status_code

        # Log de acesso
        log_message = (
            f"{method} {path} | "
            f"Status: {status_code} | "
            f"User: {user_info} | "
            f"IP: {client_ip} | "
            f"Duration: {duration:.3f}s"
        )

        if status_code >= 500:
            logger.error(log_message)
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return response

    def _get_client_ip(self, request):
        """Obtém o IP real do cliente, considerando proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
