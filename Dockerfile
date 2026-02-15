FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV DJANGO_SETTINGS_MODULE=core.settings.base

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies via pip (faster than Poetry in Docker)
COPY pyproject.toml poetry.lock /app/
RUN pip install --no-cache-dir poetry==1.8.4 \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main \
    && pip uninstall -y poetry

# Copy the project
COPY . /app/

# Make entrypoint executable and create logs dir
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command: gunicorn
CMD ["gunicorn", "core.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "3", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
