"""
Camada de Serviço para Profissionais da Saúde.

Esta camada encapsula a lógica de negócio do domínio de Profissionais,
desacoplando-a das Views e Serializers.

Responsabilidades:
- Orquestrar operações CRUD com regras de negócio
- Validar invariantes de domínio antes de persistir
- Emitir logs estruturados de operações
- Lançar exceções de domínio (não HTTP) em caso de erro
"""

import logging

from django.db import transaction
from django.db.models import Count

from core.domain import (
    NotFoundException,
    ProfissionalComConsultasException,
)

from .models import Profissional
from .validators import ProfissionalValidator

logger = logging.getLogger("apps")


class ProfissionalService:
    """
    Serviço que gerencia a lógica de negócio de Profissionais.

    Todas as operações lançam exceções de domínio (core.domain)
    em vez de exceções HTTP, permitindo reuso em contextos
    não-HTTP (CLI, tasks Celery, etc).
    """

    @staticmethod
    def list_profissionais(queryset=None):
        """
        Retorna a lista de profissionais com anotações de performance.
        """
        if queryset is None:
            queryset = Profissional.objects.all()
        return queryset.annotate(total_consultas=Count("consultas"))

    @staticmethod
    def get_profissional(profissional_id):
        """
        Busca um profissional por ID.
        Lança NotFoundException se não encontrado.
        """
        try:
            return Profissional.objects.get(pk=profissional_id)
        except Profissional.DoesNotExist:
            raise NotFoundException("Profissional", profissional_id)

    @staticmethod
    @transaction.atomic
    def create_profissional(data):
        """
        Cria um novo profissional no sistema.

        Executa validações de domínio antes de persistir.
        """
        ProfissionalValidator.validate_all(data)

        profissional = Profissional.objects.create(**data)
        logger.info(
            "Serviço: Profissional criado com sucesso: ID=%d, Nome=%s",
            profissional.id,
            profissional.nome_social,
        )
        return profissional

    @staticmethod
    @transaction.atomic
    def update_profissional(profissional, data):
        """
        Atualiza os dados de um profissional existente.

        Executa validações de domínio nos campos alterados.
        """
        ProfissionalValidator.validate_all(data)

        for field, value in data.items():
            setattr(profissional, field, value)
        profissional.save()
        logger.info("Serviço: Profissional ID=%d atualizado.", profissional.id)
        return profissional

    @staticmethod
    @transaction.atomic
    def delete_profissional(profissional):
        """
        Remove um profissional do sistema.

        Lança ProfissionalComConsultasException se houver consultas
        vinculadas (regra de integridade referencial de negócio).
        """
        total_consultas = profissional.consultas.count()
        if total_consultas > 0:
            raise ProfissionalComConsultasException(profissional.id, total_consultas)

        profissional_id = profissional.id
        profissional.delete()
        logger.info("Serviço: Profissional ID=%d removido.", profissional_id)
        return True
