"""
Django settings for Production environment.

Decisão técnica: Produção tem as configurações de segurança mais restritivas.
HSTS longo, SSL obrigatório, e throttling mais conservador.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Security - máximo rigor em produção
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allowed hosts para produção AWS
ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="api.lacrei-saude.com.br",
    cast=Csv(),
)

# CORS para produção
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="https://lacrei-saude.com.br,https://www.lacrei-saude.com.br",
    cast=Csv(),
)

# Throttling mais conservador em produção
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "30/hour",
    "user": "150/hour",
}

# Logging - apenas erros e acessos importantes
LOGGING["loggers"]["apps"]["level"] = "WARNING"  # noqa: F405
