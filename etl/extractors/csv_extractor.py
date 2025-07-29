"""
Extrator para dados CSV históricos da B3.

Este módulo contém a classe CSVExtractor que é responsável por:
- Ler o arquivo b3_stocks_1994_2020.csv
- Validar a estrutura dos dados
- Retornar um DataFrame pandas com os dados processados
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class CSVExtractor:
    """
    Classe para extrair dados históricos da B3 a partir de arquivo CSV.
    
    Esta classe lê o arquivo b3_stocks_1994_2020.csv e retorna os dados
    em formato pandas DataFrame para posterior processamento.
    """
    
    def __init__(self, file_path: str = "data/b3_stocks_1994_2020.csv"):
        """
        Inicializa o extrator CSV.
        
        Args:
            file_path (str): Caminho para o arquivo CSV com dados históricos
        """
        self.file_path = Path(file_path)
        self.expected_columns = ['datetime', 'ticker', 'open', 'close', 'high', 'low', 'volume']
        
    def extract(self, tickers: Optional[list] = None, 
                start_date: Optional[str] = None, 
                end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Extrai dados do arquivo CSV com opções de filtro.
        
        Args:
            tickers (list, optional): Lista de tickers para filtrar
            start_date (str, optional): Data de início no formato YYYY-MM-DD
            end_date (str, optional): Data de fim no formato YYYY-MM-DD
            
        Returns:
            pd.DataFrame: DataFrame com os dados extraídos
            
        Raises:
            FileNotFoundError: Se o arquivo CSV não for encontrado
            ValueError: Se a estrutura do arquivo for inválida
        """
        try:
            logger.info("Iniciando extração de dados CSV", file_path=str(self.file_path))
            
            # Verifica se o arquivo existe
            if not self.file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")
            
            # Lê o arquivo CSV
            df = pd.read_csv(self.file_path)
            
            # Valida a estrutura do arquivo
            self._validate_structure(df)
            
            # Converte a coluna datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Adiciona coluna date para compatibilidade com o banco
            df['date'] = df['datetime'].dt.date
            
            # Aplica filtros se fornecidos
            if tickers:
                logger.info("Aplicando filtro por tickers", tickers=tickers, total_rows_before=len(df))
                df = df[df['ticker'].isin(tickers)]
                logger.info("Filtro por tickers aplicado", tickers=tickers, rows_after=len(df))
            
            if start_date:
                logger.info("Aplicando filtro por data de início", start_date=start_date, rows_before=len(df))
                df = df[df['datetime'] >= pd.to_datetime(start_date)]
                logger.info("Filtro por data de início aplicado", start_date=start_date, rows_after=len(df))
            
            if end_date:
                logger.info("Aplicando filtro por data de fim", end_date=end_date, rows_before=len(df))
                df = df[df['datetime'] <= pd.to_datetime(end_date)]
                logger.info("Filtro por data de fim aplicado", end_date=end_date, rows_after=len(df))
            
            # Ordena por datetime e ticker
            df = df.sort_values(['datetime', 'ticker']).reset_index(drop=True)
            
            logger.info("Extração CSV concluída com sucesso", 
                       total_rows=len(df), 
                       date_range=f"{df['datetime'].min()} a {df['datetime'].max()}")
            
            return df
            
        except Exception as e:
            logger.error("Erro durante extração CSV", error=str(e), file_path=str(self.file_path))
            raise
    
    def _validate_structure(self, df: pd.DataFrame) -> None:
        """
        Valida a estrutura do DataFrame extraído.
        
        Args:
            df (pd.DataFrame): DataFrame a ser validado
            
        Raises:
            ValueError: Se a estrutura for inválida
        """
        # Verifica se todas as colunas esperadas estão presentes
        missing_columns = set(self.expected_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Colunas ausentes no arquivo CSV: {missing_columns}")
        
        # Verifica se há dados
        if df.empty:
            raise ValueError("Arquivo CSV está vazio")
        
        # Verifica tipos de dados básicos
        numeric_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='raise')
                except ValueError:
                    raise ValueError(f"Coluna {col} contém valores não numéricos")
        
        logger.info("Estrutura do arquivo CSV validada com sucesso", 
                   columns=list(df.columns), 
                   rows=len(df))
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados sobre o arquivo CSV.
        
        Returns:
            Dict[str, Any]: Dicionário com metadados do arquivo
        """
        try:
            if not self.file_path.exists():
                return {"error": "Arquivo não encontrado"}
            
            # Lê apenas as primeiras linhas para obter metadados
            df_sample = pd.read_csv(self.file_path, nrows=1000)
            
            metadata = {
                "file_path": str(self.file_path),
                "file_size_mb": self.file_path.stat().st_size / (1024 * 1024),
                "columns": list(df_sample.columns),
                "sample_rows": len(df_sample),
                "date_range": {
                    "start": df_sample['datetime'].min() if 'datetime' in df_sample.columns else None,
                    "end": df_sample['datetime'].max() if 'datetime' in df_sample.columns else None
                },
                "unique_tickers": df_sample['ticker'].nunique() if 'ticker' in df_sample.columns else None
            }
            
            logger.info("Metadados do arquivo CSV obtidos", metadata=metadata)
            return metadata
            
        except Exception as e:
            logger.error("Erro ao obter metadados do arquivo CSV", error=str(e))
            return {"error": str(e)} 