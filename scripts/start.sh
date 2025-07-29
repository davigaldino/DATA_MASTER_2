#!/bin/bash

# Script de inicialização para a aplicação Django
# Este script é executado como entrypoint no container Docker

set -e

echo "🚀 Iniciando aplicação Django..."

# Aguardar o banco de dados estar disponível
echo "⏳ Aguardando PostgreSQL..."
python scripts/wait_for_db.py

# Executar migrações
echo "📦 Executando migrações do banco de dados..."
python dashboard/manage.py migrate

# Coletar arquivos estáticos
echo "🎨 Coletando arquivos estáticos..."
python dashboard/manage.py collectstatic --noinput

# Criar superusuário se não existir
echo "👤 Verificando superusuário..."
python scripts/create_superuser.py

# Iniciar o servidor Django
echo "🌐 Iniciando servidor Django na porta 8000..."
exec python dashboard/manage.py runserver 0.0.0.0:8000 