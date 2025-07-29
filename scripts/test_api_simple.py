#!/usr/bin/env python3
"""
Script para testar a API simples
"""

import requests

def test_api():
    try:
        # Testar página principal
        response = requests.get("http://localhost:8000/")
        print(f"Página principal - Status: {response.status_code}")
        
        # Testar dashboard
        response = requests.get("http://localhost:8000/dashboard/")
        print(f"Dashboard - Status: {response.status_code}")
        
        # Testar API de stock data (URL correta)
        response = requests.get("http://localhost:8000/api/stocks/")
        print(f"API Stocks - Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Count: {data.get('count', 'N/A')}")
            print(f"Results: {len(data.get('results', []))}")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_api() 