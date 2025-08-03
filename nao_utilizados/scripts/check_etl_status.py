#!/usr/bin/env python3
"""
Script para verificar o status do pipeline ETL e mostrar estatísticas dos dados carregados
"""

import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import structlog

# Configurar logging
logger = structlog.get_logger()

# Carregar variáveis de ambiente
load_dotenv()

def check_etl_status():
    """Verifica o status do pipeline ETL"""
    
    # Configurações do banco de dados
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'b3_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(**db_config)
        
        print("🔍 Verificando status do pipeline ETL...")
        print("=" * 50)
        
        # Verificar tabelas
        check_tables(conn)
        
        # Verificar dados carregados
        check_data_loaded(conn)
        
        # Verificar metadados
        check_metadata(conn)
        
        # Verificar qualidade dos dados
        check_data_quality(conn)
        
        # Verificar performance
        check_performance(conn)
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do ETL: {e}")
        print(f"❌ Erro: {e}")

def check_tables(conn):
    """Verifica se as tabelas foram criadas corretamente"""
    print("\n📋 Verificando tabelas...")
    
    cursor = conn.cursor()
    
    # Verificar tabelas existentes
    cursor.execute("""
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('stock_data', 'technical_indicators', 'data_metadata')
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    expected_tables = ['stock_data', 'technical_indicators', 'data_metadata']
    existing_tables = [table[0] for table in tables]
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - NÃO ENCONTRADA")
    
    cursor.close()

def check_data_loaded(conn):
    """Verifica dados carregados nas tabelas"""
    print("\n📊 Verificando dados carregados...")
    
    cursor = conn.cursor()
    
    # Contar registros em cada tabela
    tables = ['stock_data', 'technical_indicators', 'data_metadata']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📈 {table}: {count:,} registros")
            
            # Verificar período dos dados
            if table == 'stock_data':
                cursor.execute("""
                    SELECT MIN(date), MAX(date), COUNT(DISTINCT ticker)
                    FROM stock_data
                """)
                min_date, max_date, ticker_count = cursor.fetchone()
                print(f"   📅 Período: {min_date} a {max_date}")
                print(f"   🏷️  Tickers únicos: {ticker_count}")
                
        except Exception as e:
            print(f"❌ Erro ao verificar {table}: {e}")
    
    cursor.close()

def check_metadata(conn):
    """Verifica metadados dos dados carregados"""
    print("\n📋 Verificando metadados...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                ticker,
                data_source,
                start_date,
                end_date,
                total_records,
                data_quality_score,
                processing_status,
                last_updated
            FROM data_metadata
            ORDER BY last_updated DESC
        """)
        
        metadata = cursor.fetchall()
        
        if metadata:
            print("📊 Metadados encontrados:")
            for row in metadata:
                ticker, source, start, end, records, quality, status, updated = row
                print(f"   🏷️  {ticker} ({source})")
                print(f"      📅 {start} a {end} ({records:,} registros)")
                print(f"      📊 Qualidade: {quality:.2f} | Status: {status}")
                print(f"      🕒 Última atualização: {updated}")
                print()
        else:
            print("⚠️  Nenhum metadado encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao verificar metadados: {e}")
    
    cursor.close()

def check_data_quality(conn):
    """Verifica qualidade dos dados"""
    print("\n🔍 Verificando qualidade dos dados...")
    
    cursor = conn.cursor()
    
    try:
        # Verificar valores nulos
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN open IS NULL THEN 1 END) as null_open,
                COUNT(CASE WHEN close IS NULL THEN 1 END) as null_close,
                COUNT(CASE WHEN volume IS NULL THEN 1 END) as null_volume,
                COUNT(CASE WHEN high < low THEN 1 END) as invalid_high_low
            FROM stock_data
        """)
        
        total, null_open, null_close, null_volume, invalid_hl = cursor.fetchone()
        
        print(f"📊 Total de registros: {total:,}")
        print(f"❌ Valores nulos - Open: {null_open}, Close: {null_close}, Volume: {null_volume}")
        print(f"⚠️  Registros com High < Low: {invalid_hl}")
        
        # Verificar duplicatas
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT ticker, date) as duplicates
            FROM stock_data
        """)
        
        duplicates = cursor.fetchone()[0]
        print(f"🔄 Duplicatas: {duplicates}")
        
        # Calcular score de qualidade
        quality_score = 1.0
        if total > 0:
            quality_score -= (null_open + null_close + null_volume) / (total * 3)
            quality_score -= invalid_hl / total
            quality_score -= duplicates / total
        
        quality_score = max(0, min(1, quality_score))
        print(f"📈 Score de qualidade: {quality_score:.2f}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar qualidade: {e}")
    
    cursor.close()

def check_performance(conn):
    """Verifica performance e índices"""
    print("\n⚡ Verificando performance...")
    
    cursor = conn.cursor()
    
    try:
        # Verificar índices
        cursor.execute("""
            SELECT 
                indexname,
                tablename,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename IN ('stock_data', 'technical_indicators', 'data_metadata')
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print("📊 Índices encontrados:")
            for index in indexes:
                print(f"   🔗 {index[0]} em {index[1]}")
        else:
            print("⚠️  Nenhum índice encontrado")
        
        # Verificar tamanho das tabelas
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename IN ('stock_data', 'technical_indicators', 'data_metadata')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        sizes = cursor.fetchall()
        
        print("\n💾 Tamanho das tabelas:")
        for size in sizes:
            print(f"   📦 {size[1]}: {size[2]}")
        
        # Teste de performance simples
        start_time = datetime.now()
        cursor.execute("SELECT COUNT(*) FROM stock_data WHERE ticker = 'PETR4'")
        count = cursor.fetchone()[0]
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        print(f"\n⏱️  Tempo de consulta simples: {query_time:.2f}ms")
        
    except Exception as e:
        print(f"❌ Erro ao verificar performance: {e}")
    
    cursor.close()

def generate_report():
    """Gera relatório completo"""
    print("\n📄 Gerando relatório...")
    
    # Verificar se o diretório logs existe
    os.makedirs('logs', exist_ok=True)
    
    # Redirecionar output para arquivo
    report_file = f"logs/etl_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Redirecionar stdout para arquivo
        original_stdout = sys.stdout
        sys.stdout = f
        
        print("=" * 60)
        print("RELATÓRIO DE STATUS DO PIPELINE ETL")
        print("=" * 60)
        print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        check_etl_status()
        
        # Restaurar stdout
        sys.stdout = original_stdout
    
    print(f"📄 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verificar status do pipeline ETL')
    parser.add_argument('--report', action='store_true', help='Gerar relatório completo')
    
    args = parser.parse_args()
    
    if args.report:
        generate_report()
    else:
        check_etl_status() 