#!/usr/bin/env python3
"""
Script para testar a função de status do banco
"""

import psycopg2
import os

def test_db_status():
    try:
        # Conecta ao banco
        conn = psycopg2.connect(
            host='postgres',
            port='5432',
            database='datamaster2',
            user='postgres',
            password='password'
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
        
        # Última atualização de stock_data
        cursor.execute("SELECT MAX(updated_at) FROM stock_data")
        stock_data_last_update = cursor.fetchone()[0]
        print(f"DEBUG: stock_data_last_update = {stock_data_last_update}")
        
        # Última atualização de technical_indicators
        cursor.execute("SELECT MAX(updated_at) FROM technical_indicators")
        indicators_last_update = cursor.fetchone()[0]
        print(f"DEBUG: indicators_last_update = {indicators_last_update}")
        
        # Amostra de dados
        sample_data = []
        if stock_data_count > 0:
            cursor.execute("""
                SELECT date, ticker, close, volume 
                FROM stock_data 
                ORDER BY date DESC, ticker 
                LIMIT 5
            """)
            sample_data = [
                {
                    'date': row[0].strftime('%d/%m/%Y') if row[0] else '',
                    'ticker': row[1],
                    'close': float(row[2]) if row[2] else 0,
                    'volume': int(row[3]) if row[3] else 0
                }
                for row in cursor.fetchall()
            ]
            print(f"DEBUG: sample_data = {sample_data}")
        
        cursor.close()
        conn.close()
        
        print(f"RESULTADO: {stock_data_count} registros em stock_data")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_status() 