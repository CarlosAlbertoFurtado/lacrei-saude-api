"""
Serializers para o app de Consultas Médicas.

Decisão técnica: Validação detalhada para garantir integridade dos dados.
Consultas não podem ser agendadas no passado (exceto em atualizações)
e o profissional vinculado precisa existir.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.profissionais.serializers import ProfissionalSerializer
from core.utils.sanitization import sanitize_string

from .models import Consulta


class ConsultaSerializer(serializers.ModelSerializer):
    """
    Serializer para CRUD de Consulta.

    Inclui validação de data e sanitização de observações.
    Na leitura, retorna os dados completos do profissional.
    """

    profissional_detail = ProfissionalSerializer(
        source="profissional", read_only=True
    )

    class Meta:
        model = Consulta
        fields = [
            "id",
            "data",
            "profissional",
            "profissional_detail",
            "observacoes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_data(self, value):
        """Valida que a data da consulta não está no passado."""
        if not self.instance and value < timezone.now():
            raise serializers.ValidationError(
                "Não é possível agendar uma consulta no passado."
            )
        return value

    def validate_observacoes(self, value):
        """Sanitiza as observações."""
        if value:
            return sanitize_string(value)
        return value


class ConsultaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de consultas.
    """

    profissional_nome = serializers.CharField(
        source="profissional.nome_social", read_only=True
    )
    profissional_profissao = serializers.CharField(
        source="profissional.profissao", read_only=True
    )
    is_future = serializers.BooleanField(read_only=True)

    class Meta:
        model = Consulta
        fields = [
            "id",
            "data",
            "profissional",
            "profissional_nome",
            "profissional_profissao",
            "observacoes",
            "is_future",
            "created_at",
        ]
