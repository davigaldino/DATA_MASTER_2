"""
Módulo de extratores de dados para o projeto Data Master 2.

Este módulo contém classes e funções para extrair dados de diferentes fontes:
- Arquivo CSV histórico da B3
- APIs externas (Yahoo Finance)
- Outras fontes de dados financeiros
"""

from .csv_extractor import CSVExtractor
from .yfinance_extractor import YFinanceExtractor

__all__ = ['CSVExtractor', 'YFinanceExtractor'] 