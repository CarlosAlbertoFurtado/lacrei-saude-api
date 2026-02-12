"""
Script auxiliar para gerar migrações sem depender do PostgreSQL.
Usa SQLite temporariamente apenas para o comando makemigrations.
"""

import os
import sys

import django
from django.conf import settings

# Forçar uso do SQLite para geração de migrações
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")

# Override database para SQLite
from core.settings import base

base.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    call_command("makemigrations", "profissionais", "consultas", verbosity=2)
    print("\n✅ Migrações geradas com sucesso!")
