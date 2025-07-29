#!/usr/bin/env python3
"""
Script para aguardar o banco de dados PostgreSQL estar disponível
"""

import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def wait_for_db():
    """Aguarda o banco de dados estar disponível"""
    
    # Configurações do banco de dados
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'b3_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    print(f"🔍 Tentando conectar ao PostgreSQL em {db_config['host']}:{db_config['port']}...")
    
    max_attempts = 30
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            # Tentar conectar ao banco de dados
            conn = psycopg2.connect(**db_config)
            conn.close()
            print("✅ Conexão com PostgreSQL estabelecida com sucesso!")
            return True
            
        except OperationalError as e:
            print(f"❌ Tentativa {attempt}/{max_attempts} falhou: {e}")
            
            if attempt == max_attempts:
                print("💥 Falha ao conectar ao banco de dados após todas as tentativas")
                sys.exit(1)
            
            attempt += 1
            time.sleep(2)  # Aguardar 2 segundos antes da próxima tentativa
    
    return False

if __name__ == "__main__":
    wait_for_db() 