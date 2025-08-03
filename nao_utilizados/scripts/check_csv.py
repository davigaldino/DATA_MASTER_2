#!/usr/bin/env python3
"""
Script para verificar os dados do CSV
"""

import pandas as pd
import sys
import os

def main():
    csv_path = 'data/b3_stocks_1994_2020.csv'
    
    if not os.path.exists(csv_path):
        print(f"Arquivo não encontrado: {csv_path}")
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        print("=== ANÁLISE DO DATASET CSV ===")
        print(f"Total de registros: {len(df):,}")
        print(f"Tickers únicos: {df['ticker'].nunique()}")
        print(f"Colunas: {list(df.columns)}")
        
        # Verificar se existe coluna de data
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        print(f"Colunas de data encontradas: {date_columns}")
        
        if date_columns:
            date_col = date_columns[0]
            print(f"Período usando '{date_col}': {df[date_col].min()} até {df[date_col].max()}")
        
        print("\n=== PRIMEIROS 10 TICKERS ===")
        tickers = df['ticker'].unique()[:10]
        for ticker in tickers:
            ticker_data = df[df['ticker'] == ticker]
            print(f"{ticker}: {len(ticker_data)} registros")
        
        print("\n=== AMOSTRA DE DADOS ===")
        print(df.head())
        
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 