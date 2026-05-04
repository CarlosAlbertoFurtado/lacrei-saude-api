"""
Camada de Serviço para Consultas Médicas.

Esta camada encapsula a lógica de negócio do domínio de Consultas,
incluindo validações complexas e integrações.

Responsabilidades:
- Validar regras de agendamento (data futura, profissional ativo)
- Orquestrar criação/atualização/cancelamento de consultas
- Emitir logs de auditoria estruturados
- Lançar exceções de domínio (não HTTP) em caso de erro
"""

import logging

from django.db import transaction
from django.utils import timezone

from core.domain import (
    AgendamentoRetroativoException,
    NotFoundException,
    ValidationException,
)

from ..models import Consulta

logger = logging.getLogger("apps")


class ConsultaService:
    """
    Serviço que gerencia a lógica de negócio de Consultas.

    Todas as operações lançam exceções de domínio (core.domain)
    em vez de exceções HTTP, permitindo reuso em contextos
    não-HTTP (CLI, tasks Celery, etc).
    """

    @staticmethod
    def list_consultas(queryset=None):
        """
        Retorna a lista de consultas com select_related para performance.
        """
        if queryset is None:
            queryset = Consulta.objects.all()
        return queryset.select_related("profissional")

    @staticmethod
    def get_consulta(consulta_id):
        """
        Busca uma consulta por ID.
        Lança NotFoundException se não encontrada.
        """
        try:
            return Consulta.objects.select_related("profissional").get(pk=consulta_id)
        except Consulta.DoesNotExist:
            raise NotFoundException("Consulta", consulta_id)

    @staticmethod
    @transaction.atomic
    def agendar_consulta(data):
        """
        Agenda uma nova consulta médica.

        Validações de domínio:
        - Data deve ser futura (AgendamentoRetroativoException)
        - Profissional deve existir
        """
        data_consulta = data.get("data")

        # Regra de negócio: Não permitir agendamento retroativo
        if data_consulta and data_consulta < timezone.now():
            raise AgendamentoRetroativoException()

        consulta = Consulta.objects.create(**data)
        logger.info(
            "Serviço: Consulta agendada com sucesso: ID=%d, Profissional=%s, Data=%s",
            consulta.id,
            consulta.profissional.nome_social,
            consulta.data.isoformat(),
        )
        return consulta

    @staticmethod
    @transaction.atomic
    def atualizar_consulta(consulta, data):
        """
        Atualiza os dados de uma consulta existente.

        Validações de domínio:
        - Se a data mudar, deve ser futura
        """
        data_consulta = data.get("data")
        if data_consulta and data_consulta < timezone.now():
            raise ValidationException(
                "Não é possível alterar uma consulta para uma data retroativa.",
                field="data",
            )

        for field, value in data.items():
            setattr(consulta, field, value)
        consulta.save()
        logger.info("Serviço: Consulta ID=%d atualizada.", consulta.id)
        return consulta

    @staticmethod
    @transaction.atomic
    def cancelar_consulta(consulta):
        """
        Remove uma consulta do sistema.
        """
        consulta_id = consulta.id
        consulta.delete()
        logger.info("Serviço: Consulta ID=%d cancelada.", consulta_id)
        return True

    @staticmethod
    def buscar_por_profissional(profissional_id):
        """
        Busca todas as consultas de um profissional específico.
        """
        return Consulta.objects.filter(profissional_id=profissional_id).select_related(
            "profissional"
        )
