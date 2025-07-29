#!/usr/bin/env python3
"""
Script para configurar o banco de dados PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def setup_database():
    """Configura o banco de dados PostgreSQL"""
    
    # Configurações do banco de dados
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'b3_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    print("🔧 Configurando banco de dados PostgreSQL...")
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Ler e executar script SQL de inicialização
        sql_file_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
        
        if os.path.exists(sql_file_path):
            print("📄 Executando script de inicialização do banco...")
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Executar o script SQL
            cursor.execute(sql_script)
            print("✅ Script de inicialização executado com sucesso!")
        else:
            print("⚠️ Arquivo init_db.sql não encontrado, pulando inicialização...")
        
        # Criar índices adicionais para performance
        print("📊 Criando índices para otimização...")
        
        # Índices para tabela stock_data
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stock_data_ticker_date ON stock_data(ticker, date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_data_date ON stock_data(date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_data_ticker ON stock_data(ticker);",
            "CREATE INDEX IF NOT EXISTS idx_stock_data_volume ON stock_data(volume);",
            "CREATE INDEX IF NOT EXISTS idx_stock_data_close ON stock_data(close);"
        ]
        
        # Índices para tabela technical_indicators
        indexes.extend([
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_ticker_date ON technical_indicators(ticker, date);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_rsi ON technical_indicators(rsi);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_macd ON technical_indicators(macd);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_sma_20 ON technical_indicators(sma_20);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_ema_20 ON technical_indicators(ema_20);"
        ])
        
        # Executar criação de índices
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"⚠️ Aviso ao criar índice: {e}")
        
        print("✅ Índices criados com sucesso!")
        
        # Verificar tabelas criadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('stock_data', 'technical_indicators', 'data_metadata')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"📋 Tabelas disponíveis: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        print("🎉 Configuração do banco de dados concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao configurar banco de dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database() 