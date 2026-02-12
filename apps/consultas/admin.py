from django.contrib import admin

from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ["id", "profissional", "data", "created_at"]
    list_filter = ["data", "profissional__profissao", "created_at"]
    search_fields = ["profissional__nome_social", "observacoes"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-data"]
    raw_id_fields = ["profissional"]
