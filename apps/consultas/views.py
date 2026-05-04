"""
Views para o app de Consultas Médicas.

Decisão técnica: Além do CRUD padrão, implementa uma action customizada
para buscar consultas por profissional (requisito do desafio).

Segurança:
- Autenticação JWT obrigatória em todos os endpoints
- Permissão IsAuthenticated para controle de acesso
- Logging de todas as operações CRUD
"""

import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Consulta
from .serializers import ConsultaListSerializer, ConsultaSerializer
from .services.consulta_service import ConsultaService

logger = logging.getLogger("apps")


@extend_schema_view(
    list=extend_schema(
        summary="Listar consultas",
        description="Retorna a lista paginada de consultas médicas.",
        tags=["Consultas"],
    ),
    create=extend_schema(
        summary="Agendar consulta",
        description="Agenda uma nova consulta médica vinculada a um profissional.",
        tags=["Consultas"],
    ),
    retrieve=extend_schema(
        summary="Detalhar consulta",
        description="Retorna os detalhes de uma consulta específica.",
        tags=["Consultas"],
    ),
    update=extend_schema(
        summary="Atualizar consulta",
        description="Atualiza todos os dados de uma consulta.",
        tags=["Consultas"],
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente consulta",
        description="Atualiza parcialmente os dados de uma consulta.",
        tags=["Consultas"],
    ),
    destroy=extend_schema(
        summary="Cancelar consulta",
        description="Remove uma consulta do sistema.",
        tags=["Consultas"],
    ),
)
class ConsultaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD completo de Consultas Médicas.

    Endpoints:
    - GET    /api/consultas/                              - Listar todas
    - POST   /api/consultas/                              - Criar nova
    - GET    /api/consultas/{id}/                         - Detalhar
    - PUT    /api/consultas/{id}/                         - Atualizar completo
    - PATCH  /api/consultas/{id}/                         - Atualizar parcial
    - DELETE /api/consultas/{id}/                         - Excluir
    - GET    /api/consultas/por-profissional/{prof_id}/   - Buscar por profissional
    """

    # Autenticação e Permissões explícitas
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Consulta.objects.select_related("profissional").all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["profissional", "data"]
    search_fields = ["profissional__nome_social", "observacoes"]
    ordering_fields = ["data", "created_at"]
    ordering = ["-data"]

    def get_serializer_class(self):
        if self.action == "list" or self.action == "por_profissional":
            return ConsultaListSerializer
        return ConsultaSerializer

    def get_queryset(self):
        return ConsultaService.list_consultas(super().get_queryset())

    def perform_create(self, serializer):
        try:
            consulta = ConsultaService.agendar_consulta(serializer.validated_data)
            serializer.instance = consulta
        except ValueError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"data": str(e)})

    def perform_update(self, serializer):
        try:
            consulta = ConsultaService.atualizar_consulta(
                self.get_object(), serializer.validated_data
            )
            serializer.instance = consulta
        except ValueError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"data": str(e)})

    def perform_destroy(self, instance):
        ConsultaService.cancelar_consulta(instance)

    @action(detail=False, methods=["get"], url_path="por-profissional/(?P<profissional_id>[^/.]+)")
    def por_profissional(self, request, profissional_id=None):
        """Busca consultas vinculadas a um ID de profissional."""
        consultas = ConsultaService.buscar_por_profissional(profissional_id)
        page = self.paginate_queryset(consultas)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)
