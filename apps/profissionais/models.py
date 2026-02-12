"""
Models para o app de Profissionais da Saúde.

Decisão técnica: O modelo Profissional contém os campos exigidos pelo desafio
(nome_social, profissao, endereco, contato). Campos de auditoria (created_at,
updated_at) foram adicionados como boa prática para rastreabilidade.
Índices foram criados nos campos mais buscados para performance.
"""

from django.db import models


class Profissional(models.Model):
    """
    Modelo representando um profissional da saúde.

    Campos obrigatórios conforme o desafio:
    - Nome social
    - Profissão
    - Endereço
    - Contato
    """

    nome_social = models.CharField(
        max_length=255,
        verbose_name="Nome Social",
        help_text="Nome social do profissional da saúde.",
    )
    profissao = models.CharField(
        max_length=255,
        verbose_name="Profissão",
        help_text="Profissão ou especialidade do profissional.",
    )
    endereco = models.TextField(
        verbose_name="Endereço",
        help_text="Endereço completo do profissional.",
    )
    contato = models.CharField(
        max_length=255,
        verbose_name="Contato",
        help_text="Informação de contato (e-mail ou telefone).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["nome_social"], name="idx_profissional_nome"),
            models.Index(fields=["profissao"], name="idx_profissional_profissao"),
        ]

    def __str__(self):
        return f"{self.nome_social} - {self.profissao}"
