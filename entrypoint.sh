#!/bin/bash
set -e

echo "============================================"
echo "  Lacrei Saúde API - Inicialização"
echo "============================================"

# Aguardar banco de dados
echo "[1/5] Aguardando banco de dados PostgreSQL..."
while ! python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='${DB_NAME:-lacrei_saude}',
        user='${DB_USER:-lacrei_user}',
        password='${DB_PASSWORD:-lacrei_password_secure}',
        host='${DB_HOST:-db}',
        port='${DB_PORT:-5432}'
    )
    conn.close()
    print('OK')
except Exception as e:
    print(f'Aguardando... {e}')
    exit(1)
" 2>/dev/null; do
    sleep 2
done
echo "✅ Banco de dados conectado!"

# Executar migrações
echo "[2/5] Executando migrações..."
python manage.py migrate --noinput
echo "✅ Migrações aplicadas!"

# Criar superusuário automático (se não existir)
echo "[3/5] Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lacrei.com', 'admin123')
    print('✅ Superusuário criado: admin / admin123')
else:
    print('✅ Superusuário já existe.')
"

# Coletar arquivos estáticos
echo "[4/5] Coletando arquivos estáticos..."
python manage.py collectstatic --noinput 2>/dev/null || true
echo "✅ Arquivos estáticos coletados!"

# Iniciar servidor
echo "[5/5] Iniciando servidor..."
echo "============================================"
echo "  🏥 Lacrei Saúde API"
echo "  📍 http://localhost:8000"
echo "  📖 Swagger: http://localhost:8000/api/docs/"
echo "  🔑 Login: admin / admin123"
echo "  🔗 Token: POST /api/auth/token/"
echo "============================================"

exec "$@"
