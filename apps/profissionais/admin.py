from django.contrib import admin

from .models import Profissional


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ["id", "nome_social", "profissao", "contato", "created_at"]
    list_filter = ["profissao", "created_at"]
    search_fields = ["nome_social", "profissao", "contato"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
