#!/usr/bin/env python3
"""
Script para criar superusuário Django automaticamente
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from dotenv import load_dotenv

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

# Carregar variáveis de ambiente
load_dotenv()

def create_superuser():
    """Cria um superusuário se não existir"""
    
    User = get_user_model()
    
    # Verificar se já existe um superusuário
    if User.objects.filter(is_superuser=True).exists():
        print("👤 Superusuário já existe")
        return
    
    # Obter credenciais do superusuário das variáveis de ambiente
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    
    try:
        # Criar superusuário
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superusuário criado com sucesso: {username}")
        print(f"📧 Email: {email}")
        print(f"🔑 Senha: {password}")
        
    except Exception as e:
        print(f"❌ Erro ao criar superusuário: {e}")

if __name__ == "__main__":
    create_superuser() 