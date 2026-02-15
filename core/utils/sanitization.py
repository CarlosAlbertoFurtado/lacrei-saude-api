"""
Utilitários de sanitização de dados.

Decisão técnica: Usar a biblioteca bleach para sanitizar inputs HTML/XSS
combinado com validações do Django/DRF para proteção em múltiplas camadas.
O Django ORM já protege contra SQL Injection nativamente via queries
parametrizadas, então não precisamos de proteção adicional neste nível.
"""

import re

import bleach


def sanitize_string(value: str) -> str:
    """
    Sanitiza uma string removendo tags HTML e caracteres perigosos.

    Args:
        value: String a ser sanitizada.

    Returns:
        String limpa e segura.
    """
    if not isinstance(value, str):
        return value

    # Remove tags HTML
    cleaned = bleach.clean(value, tags=[], strip=True)

    # Remove caracteres de controle (exceto newline e tab)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Trim whitespace excessivo
    cleaned = " ".join(cleaned.split())

    return cleaned.strip()


def sanitize_dict(data: dict, fields: list[str] | None = None) -> dict:
    """
    Sanitiza campos de texto em um dicionário.

    Args:
        data: Dicionário com dados a sanitizar.
        fields: Lista de campos para sanitizar.
            Se None, sanitiza todos os campos string.

    Returns:
        Dicionário com dados sanitizados.
    """
    sanitized = data.copy()

    for key, value in sanitized.items():
        if fields and key not in fields:
            continue
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)

    return sanitized
