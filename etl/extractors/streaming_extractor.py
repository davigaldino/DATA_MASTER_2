"""
Streaming Data Extractor - Simula ingestão de dados em tempo real
"""

import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import Iterator, Dict, Any
import structlog

logger = structlog.get_logger()

class StreamingExtractor:
    """
    Simula streaming de dados em tempo real a partir do CSV histórico.
    Envia dados em pequenos lotes com atraso configurável.
    """
    
    def __init__(self, csv_file_path: str, batch_size: int = 10, delay_seconds: float = 1.0):
        """
        Inicializa o extrator de streaming.
        
        Args:
            csv_file_path: Caminho para o arquivo CSV histórico
            batch_size: Número de registros por lote
            delay_seconds: Atraso entre lotes em segundos
        """
        self.csv_file_path = csv_file_path
        self.batch_size = batch_size
        self.delay_seconds = delay_seconds
        self.data = None
        self.current_index = 0
        
    def load_historical_data(self) -> pd.DataFrame:
        """
        Carrega dados históricos do CSV.
        
        Returns:
            DataFrame com dados históricos
        """
        try:
            logger.info("Carregando dados históricos para streaming", file=self.csv_file_path)
            
            # Carrega dados do CSV
            df = pd.read_csv(self.csv_file_path)
            
            # Converte datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            
            # Ordena por data e ticker
            df = df.sort_values(['date', 'ticker']).reset_index(drop=True)
            
            logger.info("Dados históricos carregados", 
                       total_records=len(df), 
                       date_range=f"{df['date'].min()} a {df['date'].max()}")
            
            return df
            
        except Exception as e:
            logger.error("Erro ao carregar dados históricos", error=str(e))
            raise
    
    def start_streaming(self, tickers: list = None, start_date: str = None, end_date: str = None) -> Iterator[Dict[str, Any]]:
        """
        Inicia o streaming de dados.
        
        Args:
            tickers: Lista de tickers para filtrar (opcional)
            start_date: Data de início (opcional)
            end_date: Data de fim (opcional)
            
        Yields:
            Dicionário com dados do lote atual
        """
        try:
            # Carrega dados históricos
            if self.data is None:
                self.data = self.load_historical_data()
            
            # Aplica filtros
            filtered_data = self.data.copy()
            
            if tickers:
                filtered_data = filtered_data[filtered_data['ticker'].isin(tickers)]
                logger.info("Filtro por tickers aplicado", tickers=tickers)
            
            if start_date:
                start_dt = pd.to_datetime(start_date).date()
                filtered_data = filtered_data[filtered_data['date'] >= start_dt]
                logger.info("Filtro por data de início aplicado", start_date=start_date)
            
            if end_date:
                end_dt = pd.to_datetime(end_date).date()
                filtered_data = filtered_data[filtered_data['date'] <= end_dt]
                logger.info("Filtro por data de fim aplicado", end_date=end_date)
            
            total_records = len(filtered_data)
            logger.info("Iniciando streaming de dados", 
                       total_records=total_records,
                       batch_size=self.batch_size,
                       delay_seconds=self.delay_seconds)
            
            # Processa dados em lotes
            for i in range(0, total_records, self.batch_size):
                batch_data = filtered_data.iloc[i:i + self.batch_size]
                
                # Converte lote para formato de streaming
                streaming_batch = {
                    'timestamp': datetime.now().isoformat(),
                    'batch_number': (i // self.batch_size) + 1,
                    'total_batches': (total_records + self.batch_size - 1) // self.batch_size,
                    'records_count': len(batch_data),
                    'data': batch_data.to_dict('records')
                }
                
                logger.info("Enviando lote de streaming", 
                           batch_number=streaming_batch['batch_number'],
                           records_count=len(batch_data))
                
                yield streaming_batch
                
                # Atraso entre lotes
                if i + self.batch_size < total_records:
                    time.sleep(self.delay_seconds)
            
            logger.info("Streaming concluído", total_batches=streaming_batch['total_batches'])
            
        except Exception as e:
            logger.error("Erro durante streaming", error=str(e))
            raise
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do streaming.
        
        Returns:
            Dicionário com estatísticas
        """
        if self.data is None:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'total_records': len(self.data),
            'unique_tickers': self.data['ticker'].nunique(),
            'date_range': {
                'start': self.data['date'].min().isoformat(),
                'end': self.data['date'].max().isoformat()
            },
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds
        }


def create_streaming_extractor(csv_file_path: str, **kwargs) -> StreamingExtractor:
    """
    Factory function para criar extrator de streaming.
    
    Args:
        csv_file_path: Caminho para o arquivo CSV
        **kwargs: Argumentos adicionais para StreamingExtractor
        
    Returns:
        Instância de StreamingExtractor
    """
    return StreamingExtractor(csv_file_path, **kwargs) 