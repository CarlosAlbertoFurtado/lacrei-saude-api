"""
Custom exception handler para a API.

Decisão técnica: Centralizar o tratamento de erros para garantir
que todas as respostas de erro sigam um formato JSON consistente,
facilitando o consumo pela frontend e debugging.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    """
    Handler customizado que garante respostas de erro em formato padronizado.
    Também registra erros no log para monitoramento.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "error": True,
            "status_code": response.status_code,
            "message": _get_error_message(response),
            "details": (
                response.data
                if isinstance(response.data, dict)
                else {"detail": response.data}
            ),
        }

        # Log de erros do servidor (5xx)
        if response.status_code >= 500:
            logger.error(
                "Erro do servidor: %s | View: %s | Status: %d",
                str(exc),
                context.get("view", "unknown"),
                response.status_code,
            )
        # Log de erros do cliente (4xx)
        elif response.status_code >= 400:
            logger.warning(
                "Erro do cliente: %s | View: %s | Status: %d",
                str(exc),
                context.get("view", "unknown"),
                response.status_code,
            )

        response.data = error_data
    else:
        # Exceção não tratada pelo DRF
        logger.exception("Exceção não tratada: %s", str(exc))
        response = Response(
            {
                "error": True,
                "status_code": 500,
                "message": "Erro interno do servidor.",
                "details": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_message(response):
    """Extrai uma mensagem legível do response de erro."""
    if isinstance(response.data, dict):
        if "detail" in response.data:
            return str(response.data["detail"])
        # Pegar a primeira mensagem de erro de validação
        for field, errors in response.data.items():
            if isinstance(errors, list) and errors:
                return f"{field}: {errors[0]}"
            elif isinstance(errors, str):
                return f"{field}: {errors}"
    elif isinstance(response.data, list) and response.data:
        return str(response.data[0])
    return "Erro na requisição."
