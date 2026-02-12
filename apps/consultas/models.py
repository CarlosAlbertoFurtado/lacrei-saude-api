"""
Models para o app de Consultas Médicas.

Decisão técnica: A consulta possui um vínculo direto com o profissional
via ForeignKey com related_name='consultas', permitindo buscar todas as
consultas de um profissional de forma eficiente.
O on_delete=PROTECT foi escolhido para evitar exclusão acidental de
profissionais que possuem consultas vinculadas.
"""

from django.db import models
from django.utils import timezone


class Consulta(models.Model):
    """
    Modelo representando uma consulta médica.

    Campos obrigatórios conforme o desafio:
    - Data da consulta
    - Profissional vinculado (chave estrangeira)
    """

    data = models.DateTimeField(
        verbose_name="Data da Consulta",
        help_text="Data e hora da consulta médica.",
    )
    profissional = models.ForeignKey(
        "profissionais.Profissional",
        on_delete=models.PROTECT,
        related_name="consultas",
        verbose_name="Profissional",
        help_text="Profissional da saúde responsável pela consulta.",
    )
    observacoes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações",
        help_text="Observações adicionais sobre a consulta (opcional).",
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
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=["data"], name="idx_consulta_data"),
            models.Index(fields=["profissional"], name="idx_consulta_profissional"),
        ]

    def __str__(self):
        return f"Consulta #{self.id} - {self.profissional.nome_social} em {self.data.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_future(self):
        """Verifica se a consulta é futura."""
        return self.data > timezone.now()
