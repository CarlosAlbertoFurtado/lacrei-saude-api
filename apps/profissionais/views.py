"""
Views para o app de Profissionais da Saúde.

Decisão técnica: Utiliza ModelViewSet para CRUD completo com mínimo
de código, mantendo consistência e boa prática DRF.
A listagem usa um serializer mais leve para performance.
"""

import logging

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Profissional
from .serializers import ProfissionalListSerializer, ProfissionalSerializer

logger = logging.getLogger("apps")


@extend_schema_view(
    list=extend_schema(
        summary="Listar profissionais",
        description="Retorna a lista paginada de profissionais da saúde cadastrados.",
        tags=["Profissionais"],
    ),
    create=extend_schema(
        summary="Cadastrar profissional",
        description="Cadastra um novo profissional da saúde.",
        tags=["Profissionais"],
    ),
    retrieve=extend_schema(
        summary="Detalhar profissional",
        description="Retorna os detalhes de um profissional específico.",
        tags=["Profissionais"],
    ),
    update=extend_schema(
        summary="Atualizar profissional",
        description="Atualiza todos os dados de um profissional.",
        tags=["Profissionais"],
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente profissional",
        description="Atualiza parcialmente os dados de um profissional.",
        tags=["Profissionais"],
    ),
    destroy=extend_schema(
        summary="Excluir profissional",
        description="Remove um profissional do sistema.",
        tags=["Profissionais"],
    ),
)
class ProfissionalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD completo de Profissionais da Saúde.

    Endpoints:
    - GET    /api/profissionais/          - Listar todos
    - POST   /api/profissionais/          - Criar novo
    - GET    /api/profissionais/{id}/     - Detalhar
    - PUT    /api/profissionais/{id}/     - Atualizar completo
    - PATCH  /api/profissionais/{id}/     - Atualizar parcial
    - DELETE /api/profissionais/{id}/     - Excluir
    """

    queryset = Profissional.objects.all()
    filterset_fields = ["profissao"]
    search_fields = ["nome_social", "profissao"]
    ordering_fields = ["nome_social", "profissao", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProfissionalListSerializer
        return ProfissionalSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.annotate(total_consultas=Count("consultas"))
        return queryset

    def perform_create(self, serializer):
        profissional = serializer.save()
        logger.info(
            "Profissional criado: ID=%d, Nome=%s",
            profissional.id,
            profissional.nome_social,
        )

    def perform_update(self, serializer):
        profissional = serializer.save()
        logger.info(
            "Profissional atualizado: ID=%d, Nome=%s",
            profissional.id,
            profissional.nome_social,
        )

    def perform_destroy(self, instance):
        logger.info(
            "Profissional excluído: ID=%d, Nome=%s",
            instance.id,
            instance.nome_social,
        )
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Verificar se há consultas vinculadas
        if instance.consultas.exists():
            return Response(
                {
                    "error": True,
                    "message": (
                        "Não é possível excluir este profissional pois existem "
                        "consultas vinculadas. Exclua as consultas primeiro."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
