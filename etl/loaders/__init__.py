"""
Módulo de carregadores de dados para o projeto Data Master 2.

Este módulo contém classes e funções para carregar dados processados:
- Carregamento para PostgreSQL
- Validação de dados antes da carga
- Tratamento de erros de conexão
- Logging de operações de carga
"""

from .postgres_loader import PostgresLoader

__all__ = ['PostgresLoader'] 