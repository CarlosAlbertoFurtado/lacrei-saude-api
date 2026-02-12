"""
Serializers para o app de Profissionais da Saúde.

Decisão técnica: Sanitização de inputs é feita diretamente no serializer
usando o utilitário bleach, garantindo que dados maliciosos sejam removidos
antes de chegarem ao banco de dados.
"""

from rest_framework import serializers

from core.utils.sanitization import sanitize_string

from .models import Profissional


class ProfissionalSerializer(serializers.ModelSerializer):
    """
    Serializer para CRUD de Profissional.

    Inclui sanitização de todos os campos de texto para proteção
    contra XSS e injeção de HTML.
    """

    class Meta:
        model = Profissional
        fields = [
            "id",
            "nome_social",
            "profissao",
            "endereco",
            "contato",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_nome_social(self, value):
        """Valida e sanitiza o nome social."""
        value = sanitize_string(value)
        if len(value) < 2:
            raise serializers.ValidationError(
                "O nome social deve ter pelo menos 2 caracteres."
            )
        if len(value) > 255:
            raise serializers.ValidationError(
                "O nome social deve ter no máximo 255 caracteres."
            )
        return value

    def validate_profissao(self, value):
        """Valida e sanitiza a profissão."""
        value = sanitize_string(value)
        if len(value) < 2:
            raise serializers.ValidationError(
                "A profissão deve ter pelo menos 2 caracteres."
            )
        return value

    def validate_endereco(self, value):
        """Valida e sanitiza o endereço."""
        value = sanitize_string(value)
        if len(value) < 5:
            raise serializers.ValidationError(
                "O endereço deve ter pelo menos 5 caracteres."
            )
        return value

    def validate_contato(self, value):
        """Valida e sanitiza o contato."""
        value = sanitize_string(value)
        if len(value) < 5:
            raise serializers.ValidationError(
                "O contato deve ter pelo menos 5 caracteres."
            )
        return value


class ProfissionalListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de profissionais.
    Retorna apenas campos essenciais para performance.
    """

    total_consultas = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Profissional
        fields = [
            "id",
            "nome_social",
            "profissao",
            "contato",
            "total_consultas",
        ]
