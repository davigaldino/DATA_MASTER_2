#!/usr/bin/env python3
"""
Script para testar a função Django de status do banco
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.dashboard.settings')
sys.path.append('/app')
django.setup()

import psycopg2
from django.conf import settings

def test_django_db():
    try:
        print("Configurações do Django:")
        print(f"HOST: {settings.DATABASES['default']['HOST']}")
        print(f"PORT: {settings.DATABASES['default']['PORT']}")
        print(f"NAME: {settings.DATABASES['default']['NAME']}")
        print(f"USER: {settings.DATABASES['default']['USER']}")
        print(f"PASSWORD: {settings.DATABASES['default']['PASSWORD']}")
        
        # Conecta ao banco
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD']
        )
        
        cursor = conn.cursor()
        
        # Conta registros em stock_data
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        stock_data_count = cursor.fetchone()[0]
        print(f"DEBUG: stock_data_count = {stock_data_count}")
        
        # Conta registros em technical_indicators
        cursor.execute("SELECT COUNT(*) FROM technical_indicators")
        indicators_count = cursor.fetchone()[0]
        print(f"DEBUG: indicators_count = {indicators_count}")
        
        cursor.close()
        conn.close()
        
        print(f"RESULTADO: {stock_data_count} registros em stock_data")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_django_db() 