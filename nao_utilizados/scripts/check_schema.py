#!/usr/bin/env python3
"""
Script para verificar o schema da tabela technical_indicators.
"""

import psycopg2

def check_schema():
    try:
        conn = psycopg2.connect(
            host='postgres',
            port='5432',
            database='datamaster2',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        
        # Verificar colunas da tabela technical_indicators
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'technical_indicators' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Colunas na tabela technical_indicators:")
        for col in columns:
            print(f"  {col[0]} ({col[1]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_schema() 