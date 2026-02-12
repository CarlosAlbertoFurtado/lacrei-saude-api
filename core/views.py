"""
Health check view para monitoramento da aplicação.
"""

from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint para monitoramento.
    Verifica conectividade com o banco de dados.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        health = {
            "status": "healthy",
            "database": "connected",
        }

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            health["status"] = "unhealthy"
            health["database"] = f"disconnected: {str(e)}"
            return Response(health, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health, status=status.HTTP_200_OK)
