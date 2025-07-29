#!/usr/bin/env python3
"""
Script para verificar dados dos tickers específicos
"""

import pandas as pd

def main():
    df = pd.read_csv('data/b3_stocks_1994_2020.csv')
    tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4']
    
    print("=== DADOS DOS TICKERS ===")
    for ticker in tickers:
        data = df[df['ticker'] == ticker]
        print(f"{ticker}: {len(data)} registros")
        if len(data) > 0:
            print(f"  Período: {data['datetime'].min()} até {data['datetime'].max()}")
            print(f"  Dados em 2017: {len(data[data['datetime'].str.startswith('2017')])} registros")
        print()

if __name__ == "__main__":
    main() 