"""
Validadores de domínio para Profissionais da Saúde.

Decisão técnica: Validações de negócio centralizadas neste módulo,
separadas dos serializers (validação de API) e dos models (validação de banco).
Isso permite reusar as mesmas regras em contextos não-HTTP (CLI, tasks, etc).
"""

import re

from core.domain import ValidationException


class ProfissionalValidator:
    """Validador de regras de negócio para Profissionais."""

    NOME_MIN_LENGTH = 2
    NOME_MAX_LENGTH = 255
    PROFISSAO_MIN_LENGTH = 2
    CONTATO_MIN_LENGTH = 5
    ENDERECO_MIN_LENGTH = 5

    # Profissões reconhecidas pelo sistema (extensível)
    PROFISSOES_VALIDAS = [
        "Medicina",
        "Psicologia",
        "Enfermagem",
        "Fisioterapia",
        "Nutrição",
        "Odontologia",
        "Fonoaudiologia",
        "Farmácia",
        "Terapia Ocupacional",
        "Serviço Social",
        "Endocrinologia",
        "Cardiologia",
        "Dermatologia",
        "Psiquiatria",
    ]

    @classmethod
    def validate_nome_social(cls, nome):
        """Valida o nome social do profissional."""
        if not nome or not nome.strip():
            raise ValidationException(
                "O nome social é obrigatório.",
                field="nome_social",
            )
        if len(nome.strip()) < cls.NOME_MIN_LENGTH:
            raise ValidationException(
                f"O nome social deve ter pelo menos {cls.NOME_MIN_LENGTH} caracteres.",
                field="nome_social",
            )
        if len(nome) > cls.NOME_MAX_LENGTH:
            raise ValidationException(
                f"O nome social deve ter no máximo {cls.NOME_MAX_LENGTH} caracteres.",
                field="nome_social",
            )
        # Não permitir nomes com apenas números
        if nome.strip().isdigit():
            raise ValidationException(
                "O nome social não pode conter apenas números.",
                field="nome_social",
            )
        return nome

    @classmethod
    def validate_contato(cls, contato):
        """Valida informação de contato (e-mail ou telefone)."""
        if not contato or not contato.strip():
            raise ValidationException(
                "O contato é obrigatório.",
                field="contato",
            )
        if len(contato.strip()) < cls.CONTATO_MIN_LENGTH:
            raise ValidationException(
                f"O contato deve ter pelo menos {cls.CONTATO_MIN_LENGTH} caracteres.",
                field="contato",
            )
        return contato

    @classmethod
    def validate_endereco(cls, endereco):
        """Valida o endereço do profissional."""
        if not endereco or not endereco.strip():
            raise ValidationException(
                "O endereço é obrigatório.",
                field="endereco",
            )
        if len(endereco.strip()) < cls.ENDERECO_MIN_LENGTH:
            raise ValidationException(
                f"O endereço deve ter pelo menos {cls.ENDERECO_MIN_LENGTH} caracteres.",
                field="endereco",
            )
        return endereco

    @classmethod
    def validate_all(cls, data):
        """Executa todas as validações de negócio nos dados do profissional."""
        if "nome_social" in data:
            cls.validate_nome_social(data["nome_social"])
        if "contato" in data:
            cls.validate_contato(data["contato"])
        if "endereco" in data:
            cls.validate_endereco(data["endereco"])
        return data
