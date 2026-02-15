"""
Django settings for Staging environment.

Decisão técnica: Staging replica produção o mais próximo possível,
mas com DEBUG habilitável e logging mais verboso para facilitar
identificação de problemas antes do deploy em produção.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600  # 1 hora em staging
SECURE_HSTS_PRELOAD = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Allowed hosts para staging AWS
ALLOWED_HOSTS = config(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS",
    default="staging.lacrei-saude.com.br",
    cast=Csv(),  # noqa: F405
)

# CORS para staging
CORS_ALLOWED_ORIGINS = config(  # noqa: F405
    "CORS_ALLOWED_ORIGINS",
    default="https://staging.lacrei-saude.com.br",
    cast=Csv(),  # noqa: F405
)

# Logging mais detalhado em staging
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
