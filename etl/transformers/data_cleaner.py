"""
Transformador para limpeza e validação de dados.

Este módulo contém a classe DataCleaner que é responsável por:
- Limpar dados ausentes e duplicados
- Validar tipos de dados
- Corrigir inconsistências
- Padronizar formatos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class DataCleaner:
    """
    Classe para limpeza e validação de dados financeiros.
    
    Esta classe implementa métodos para limpar, validar e padronizar
    dados de ações antes do processamento.
    """
    
    def __init__(self):
        """Inicializa o limpador de dados."""
        self.validation_rules = {
            'datetime': {'type': 'datetime', 'required': True},
            'ticker': {'type': 'string', 'required': True},
            'open': {'type': 'numeric', 'min': 0, 'required': True},
            'close': {'type': 'numeric', 'min': 0, 'required': True},
            'high': {'type': 'numeric', 'min': 0, 'required': True},
            'low': {'type': 'numeric', 'min': 0, 'required': True},
            'volume': {'type': 'numeric', 'min': 0, 'required': False}
        }
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executa o processo completo de limpeza de dados.
        
        Args:
            df (pd.DataFrame): DataFrame com dados brutos
            
        Returns:
            pd.DataFrame: DataFrame limpo e validado
        """
        try:
            logger.info("Iniciando limpeza de dados", initial_rows=len(df))
            
            # Faz uma cópia para não modificar o original
            cleaned_df = df.copy()
            
            # Aplica todas as etapas de limpeza
            cleaned_df = self._remove_duplicates(cleaned_df)
            cleaned_df = self._handle_missing_values(cleaned_df)
            cleaned_df = self._validate_data_types(cleaned_df)
            cleaned_df = self._fix_data_inconsistencies(cleaned_df)
            cleaned_df = self._remove_outliers(cleaned_df)
            cleaned_df = self._validate_business_rules(cleaned_df)
            
            # Ordena e reseta índice
            cleaned_df = cleaned_df.sort_values(['datetime', 'ticker']).reset_index(drop=True)
            
            logger.info("Limpeza de dados concluída", 
                       final_rows=len(cleaned_df), 
                       removed_rows=len(df) - len(cleaned_df))
            
            return cleaned_df
            
        except Exception as e:
            logger.error("Erro durante limpeza de dados", error=str(e))
            raise
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove registros duplicados.
        
        Args:
            df (pd.DataFrame): DataFrame com possíveis duplicatas
            
        Returns:
            pd.DataFrame: DataFrame sem duplicatas
        """
        initial_count = len(df)
        
        # Remove duplicatas baseadas em datetime e ticker
        df_clean = df.drop_duplicates(subset=['datetime', 'ticker'], keep='last')
        
        removed_count = initial_count - len(df_clean)
        if removed_count > 0:
            logger.info("Duplicatas removidas", removed_count=removed_count)
        
        return df_clean
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trata valores ausentes de acordo com regras específicas.
        
        Args:
            df (pd.DataFrame): DataFrame com valores ausentes
            
        Returns:
            pd.DataFrame: DataFrame com valores ausentes tratados
        """
        initial_count = len(df)
        
        # Remove linhas com valores ausentes em colunas críticas
        critical_columns = ['datetime', 'ticker', 'close']
        df_clean = df.dropna(subset=critical_columns)
        
        # Para outras colunas numéricas, pode usar interpolação ou forward fill
        numeric_columns = ['open', 'high', 'low', 'volume']
        for col in numeric_columns:
            if col in df_clean.columns:
                # Agrupa por ticker e aplica forward fill
                df_clean[col] = df_clean.groupby('ticker')[col].fillna(method='ffill')
                # Se ainda houver valores nulos, usa backward fill
                df_clean[col] = df_clean.groupby('ticker')[col].fillna(method='bfill')
        
        removed_count = initial_count - len(df_clean)
        if removed_count > 0:
            logger.info("Linhas com valores ausentes removidas", removed_count=removed_count)
        
        return df_clean
    
    def _validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida e converte tipos de dados.
        
        Args:
            df (pd.DataFrame): DataFrame com tipos a serem validados
            
        Returns:
            pd.DataFrame: DataFrame com tipos corretos
        """
        # Converte datetime
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        
        # Converte ticker para string
        if 'ticker' in df.columns:
            df['ticker'] = df['ticker'].astype(str).str.upper()
        
        # Converte colunas numéricas
        numeric_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info("Tipos de dados validados e convertidos")
        return df
    
    def _fix_data_inconsistencies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Corrige inconsistências nos dados.
        
        Args:
            df (pd.DataFrame): DataFrame com possíveis inconsistências
            
        Returns:
            pd.DataFrame: DataFrame com inconsistências corrigidas
        """
        # Corrige inconsistências de preços
        if all(col in df.columns for col in ['open', 'close', 'high', 'low']):
            # High deve ser >= max(open, close)
            df['high'] = df[['high', 'open', 'close']].max(axis=1)
            
            # Low deve ser <= min(open, close)
            df['low'] = df[['low', 'open', 'close']].min(axis=1)
            
            # Volume não pode ser negativo
            if 'volume' in df.columns:
                df['volume'] = df['volume'].clip(lower=0)
        
        logger.info("Inconsistências de dados corrigidas")
        return df
    
    def _remove_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """
        Remove outliers usando diferentes métodos.
        
        Args:
            df (pd.DataFrame): DataFrame com possíveis outliers
            method (str): Método para detecção de outliers ('iqr', 'zscore')
            
        Returns:
            pd.DataFrame: DataFrame sem outliers
        """
        initial_count = len(df)
        
        if method == 'iqr':
            df_clean = self._remove_outliers_iqr(df)
        elif method == 'zscore':
            df_clean = self._remove_outliers_zscore(df)
        else:
            logger.warning("Método de outlier não reconhecido, mantendo dados originais")
            return df
        
        removed_count = initial_count - len(df_clean)
        if removed_count > 0:
            logger.info("Outliers removidos", removed_count=removed_count, method=method)
        
        return df_clean
    
    def _remove_outliers_iqr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers usando o método IQR (Interquartile Range).
        
        Args:
            df (pd.DataFrame): DataFrame com outliers
            
        Returns:
            pd.DataFrame: DataFrame sem outliers
        """
        df_clean = df.copy()
        
        # Aplica IQR para colunas de preço
        price_columns = ['open', 'close', 'high', 'low']
        
        for col in price_columns:
            if col in df_clean.columns:
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Remove outliers
                df_clean = df_clean[
                    (df_clean[col] >= lower_bound) & 
                    (df_clean[col] <= upper_bound)
                ]
        
        return df_clean
    
    def _remove_outliers_zscore(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        Remove outliers usando Z-score.
        
        Args:
            df (pd.DataFrame): DataFrame com outliers
            threshold (float): Limite do Z-score para considerar outlier
            
        Returns:
            pd.DataFrame: DataFrame sem outliers
        """
        df_clean = df.copy()
        
        # Aplica Z-score para colunas de preço
        price_columns = ['open', 'close', 'high', 'low']
        
        for col in price_columns:
            if col in df_clean.columns:
                z_scores = np.abs((df_clean[col] - df_clean[col].mean()) / df_clean[col].std())
                df_clean = df_clean[z_scores < threshold]
        
        return df_clean
    
    def _validate_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida regras de negócio específicas para dados financeiros.
        
        Args:
            df (pd.DataFrame): DataFrame a ser validado
            
        Returns:
            pd.DataFrame: DataFrame validado
        """
        initial_count = len(df)
        
        # Remove registros com preços zero ou negativos
        price_columns = ['open', 'close', 'high', 'low']
        for col in price_columns:
            if col in df.columns:
                df = df[df[col] > 0]
        
        # Remove registros com volume negativo
        if 'volume' in df.columns:
            df = df[df['volume'] >= 0]
        
        # Remove registros com datas futuras
        if 'datetime' in df.columns:
            current_time = pd.Timestamp.now()
            df = df[df['datetime'] <= current_time]
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.info("Registros removidos por violação de regras de negócio", 
                       removed_count=removed_count)
        
        return df
    
    def get_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict:
        """
        Gera relatório detalhado da limpeza de dados.
        
        Args:
            original_df (pd.DataFrame): DataFrame original
            cleaned_df (pd.DataFrame): DataFrame limpo
            
        Returns:
            Dict: Relatório de limpeza
        """
        report = {
            'original_rows': len(original_df),
            'cleaned_rows': len(cleaned_df),
            'removed_rows': len(original_df) - len(cleaned_df),
            'removal_percentage': round((len(original_df) - len(cleaned_df)) / len(original_df) * 100, 2),
            'date_range': {
                'original': {
                    'start': original_df['datetime'].min() if 'datetime' in original_df.columns else None,
                    'end': original_df['datetime'].max() if 'datetime' in original_df.columns else None
                },
                'cleaned': {
                    'start': cleaned_df['datetime'].min() if 'datetime' in cleaned_df.columns else None,
                    'end': cleaned_df['datetime'].max() if 'datetime' in cleaned_df.columns else None
                }
            },
            'tickers': {
                'original': original_df['ticker'].nunique() if 'ticker' in original_df.columns else 0,
                'cleaned': cleaned_df['ticker'].nunique() if 'ticker' in cleaned_df.columns else 0
            }
        }
        
        logger.info("Relatório de limpeza gerado", report=report)
        return report 