#!/usr/bin/env python3
"""
Script para testar a API
"""

import requests
import json

def test_api():
    try:
        print("Testando API...")
        response = requests.get('http://localhost:8000/api/stocks/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tipo de dados: {type(data)}")
            print(f"Conteúdo: {data}")
            if isinstance(data, list):
                print(f"Total de registros: {len(data)}")
                if data and len(data) > 0:
                    print(f"Primeiro registro: {data[0]}")
                    print(f"Último registro: {data[-1]}")
            else:
                print(f"Dados não são uma lista: {data}")
        else:
            print(f"Erro: {response.text}")
            
    except Exception as e:
        print(f"Erro ao testar API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api() 