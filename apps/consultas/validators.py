"""
Validadores de domínio para Consultas Médicas.

Decisão técnica: Validações de negócio centralizadas separadamente
dos serializers. Regras como "não agendar no passado" e "profissional
deve existir" são regras de DOMÍNIO, não de API.
"""

from django.utils import timezone

from apps.profissionais.models import Profissional
from core.domain import (
    AgendamentoRetroativoException,
    NotFoundException,
    ValidationException,
)


class ConsultaValidator:
    """Validador de regras de negócio para Consultas."""

    @classmethod
    def validate_data_consulta(cls, data_consulta, is_update=False):
        """
        Valida que a data da consulta é futura.

        Em atualizações, permite manter a data existente.
        """
        if data_consulta is None:
            raise ValidationException(
                "A data da consulta é obrigatória.",
                field="data",
            )

        if not is_update and data_consulta < timezone.now():
            raise AgendamentoRetroativoException()

        if is_update and data_consulta < timezone.now():
            raise ValidationException(
                "Não é possível alterar uma consulta para uma data retroativa.",
                field="data",
            )

        return data_consulta

    @classmethod
    def validate_profissional_exists(cls, profissional_id):
        """Verifica se o profissional existe no sistema."""
        if not Profissional.objects.filter(pk=profissional_id).exists():
            raise NotFoundException("Profissional", profissional_id)
        return profissional_id

    @classmethod
    def validate_observacoes(cls, observacoes):
        """Valida observações (campo opcional com limite de tamanho)."""
        if observacoes and len(observacoes) > 5000:
            raise ValidationException(
                "As observações devem ter no máximo 5000 caracteres.",
                field="observacoes",
            )
        return observacoes

    @classmethod
    def validate_agendamento(cls, data):
        """Executa todas as validações para agendamento de consulta."""
        if "data" in data:
            cls.validate_data_consulta(data["data"])
        if "profissional" in data and hasattr(data["profissional"], "pk"):
            cls.validate_profissional_exists(data["profissional"].pk)
        if "observacoes" in data:
            cls.validate_observacoes(data["observacoes"])
        return data
