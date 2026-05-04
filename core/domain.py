"""
Exceções de domínio para a Lacrei Saúde API.

Decisão técnica: Exceções de domínio permitem separar erros de negócio
de erros de infraestrutura. Views traduzem essas exceções em respostas HTTP
adequadas, mantendo a camada de serviço agnóstica ao protocolo HTTP.
"""


class DomainException(Exception):
    """Exceção base para erros de domínio/negócio."""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code or "domain_error"
        super().__init__(self.message)


class ValidationException(DomainException):
    """Erro de validação de regra de negócio."""

    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message, code="validation_error")


class ConflictException(DomainException):
    """Erro de conflito de estado (ex: excluir entidade com dependências)."""

    def __init__(self, message):
        super().__init__(message, code="conflict_error")


class NotFoundException(DomainException):
    """Entidade não encontrada no domínio."""

    def __init__(self, entity_name, entity_id):
        self.entity_name = entity_name
        self.entity_id = entity_id
        message = f"{entity_name} com ID={entity_id} não encontrado(a)."
        super().__init__(message, code="not_found")


class AgendamentoRetroativoException(ValidationException):
    """Tentativa de agendar consulta em data passada."""

    def __init__(self):
        super().__init__(
            "Não é possível agendar uma consulta em data retroativa.",
            field="data",
        )


class ProfissionalComConsultasException(ConflictException):
    """Tentativa de excluir profissional com consultas vinculadas."""

    def __init__(self, profissional_id, total_consultas):
        self.profissional_id = profissional_id
        self.total_consultas = total_consultas
        message = (
            f"Não é possível excluir o profissional ID={profissional_id} "
            f"pois existem {total_consultas} consulta(s) vinculada(s). "
            f"Exclua as consultas primeiro."
        )
        super().__init__(message)
