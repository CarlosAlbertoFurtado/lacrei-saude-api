"""
Views para o app de Profissionais da Saúde.

Decisão técnica: Utiliza ModelViewSet para CRUD completo com mínimo
de código, mantendo consistência e boa prática DRF.
A listagem usa um serializer mais leve para performance.

Segurança:
- Autenticação JWT obrigatória em todos os endpoints
- Permissão IsAuthenticated para controle de acesso
- Logging de todas as operações CRUD

Arquitetura:
- Views são finas: delegam lógica de negócio para a camada de serviço
- Exceções de domínio são traduzidas em respostas HTTP adequadas
"""

import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.domain import (
    ProfissionalComConsultasException,
)

from .models import Profissional
from .serializers import ProfissionalListSerializer, ProfissionalSerializer
from .services import ProfissionalService

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

    # Autenticação e Permissões explícitas
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
        return ProfissionalService.list_profissionais(super().get_queryset())

    def perform_create(self, serializer):
        profissional = ProfissionalService.create_profissional(
            serializer.validated_data
        )
        # O serializer precisa ser populado com a instância criada
        serializer.instance = profissional

    def perform_update(self, serializer):
        profissional = ProfissionalService.update_profissional(
            self.get_object(), serializer.validated_data
        )
        serializer.instance = profissional

    def perform_destroy(self, instance):
        """Delega exclusão para a camada de serviço."""
        ProfissionalService.delete_profissional(instance)

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescreve destroy para traduzir exceções de domínio em respostas HTTP.

        A lógica de verificação de consultas vinculadas está na camada de serviço
        (ProfissionalService.delete_profissional), mantendo a view fina.
        """
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProfissionalComConsultasException as exc:
            return Response(
                {
                    "error": True,
                    "code": exc.code,
                    "message": exc.message,
                },
                status=status.HTTP_409_CONFLICT,
            )
