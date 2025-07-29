"""
Extrator para dados do Yahoo Finance.

Este módulo contém a classe YFinanceExtractor que é responsável por:
- Extrair dados históricos de ações brasileiras via Yahoo Finance
- Tratar rate limits e falhas de API
- Retornar dados em formato consistente com o CSV histórico
"""

import yfinance as yf
import pandas as pd
import time
from typing import List, Optional, Dict, Any
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class YFinanceExtractor:
    """
    Classe para extrair dados de ações brasileiras via Yahoo Finance.
    
    Esta classe utiliza a biblioteca yfinance para obter dados históricos
    e em tempo real de ações listadas na B3.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 1):
        """
        Inicializa o extrator Yahoo Finance.
        
        Args:
            max_retries (int): Número máximo de tentativas em caso de falha
            retry_delay (int): Delay entre tentativas em segundos
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Mapeamento de tickers B3 para Yahoo Finance
        self.ticker_mapping = {
            'PETR4': 'PETR4.SA',
            'VALE3': 'VALE3.SA',
            'ITUB4': 'ITUB4.SA',
            'BBDC4': 'BBDC4.SA',
            'ABEV3': 'ABEV3.SA',
            'WEGE3': 'WEGE3.SA',
            'RENT3': 'RENT3.SA',
            'LREN3': 'LREN3.SA',
            'MGLU3': 'MGLU3.SA',
            'JBSS3': 'JBSS3.SA',
            'IBOV': '^BVSP',  # Índice Bovespa
        }
    
    def extract_historical_data(self, 
                              tickers: List[str], 
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              period: str = "1y") -> pd.DataFrame:
        """
        Extrai dados históricos para uma lista de tickers.
        
        Args:
            tickers (List[str]): Lista de tickers para extrair
            start_date (str, optional): Data de início (YYYY-MM-DD)
            end_date (str, optional): Data de fim (YYYY-MM-DD)
            period (str): Período padrão se não especificar datas
            
        Returns:
            pd.DataFrame: DataFrame com dados históricos
        """
        try:
            logger.info("Iniciando extração de dados históricos via Yahoo Finance", 
                       tickers=tickers, start_date=start_date, end_date=end_date)
            
            all_data = []
            
            for ticker in tickers:
                ticker_data = self._extract_single_ticker(ticker, start_date, end_date, period)
                if ticker_data is not None and not ticker_data.empty:
                    all_data.append(ticker_data)
                
                # Delay para evitar rate limits
                time.sleep(self.retry_delay)
            
            if not all_data:
                logger.warning("Nenhum dado foi extraído com sucesso")
                return pd.DataFrame()
            
            # Combina todos os dados
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Padroniza o formato
            combined_df = self._standardize_format(combined_df)
            
            logger.info("Extração histórica concluída", 
                       total_rows=len(combined_df), 
                       tickers_processed=len(all_data))
            
            return combined_df
            
        except Exception as e:
            logger.error("Erro durante extração histórica", error=str(e))
            raise
    
    def extract_realtime_data(self, tickers: List[str]) -> pd.DataFrame:
        """
        Extrai dados em tempo real para uma lista de tickers.
        
        Args:
            tickers (List[str]): Lista de tickers para extrair
            
        Returns:
            pd.DataFrame: DataFrame com dados em tempo real
        """
        try:
            logger.info("Iniciando extração de dados em tempo real", tickers=tickers)
            
            all_data = []
            
            for ticker in tickers:
                ticker_data = self._extract_realtime_single_ticker(ticker)
                if ticker_data is not None:
                    all_data.append(ticker_data)
                
                time.sleep(self.retry_delay)
            
            if not all_data:
                logger.warning("Nenhum dado em tempo real foi extraído")
                return pd.DataFrame()
            
            # Combina todos os dados
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Padroniza o formato
            combined_df = self._standardize_format(combined_df)
            
            logger.info("Extração em tempo real concluída", 
                       total_rows=len(combined_df), 
                       tickers_processed=len(all_data))
            
            return combined_df
            
        except Exception as e:
            logger.error("Erro durante extração em tempo real", error=str(e))
            raise
    
    def _extract_single_ticker(self, 
                              ticker: str, 
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Extrai dados históricos para um único ticker.
        
        Args:
            ticker (str): Ticker para extrair
            start_date (str, optional): Data de início
            end_date (str, optional): Data de fim
            period (str): Período padrão
            
        Returns:
            Optional[pd.DataFrame]: DataFrame com dados ou None se falhar
        """
        yf_ticker = self.ticker_mapping.get(ticker, f"{ticker}.SA")
        
        for attempt in range(self.max_retries):
            try:
                logger.debug("Tentativa de extração", ticker=ticker, attempt=attempt + 1)
                
                # Cria objeto Ticker
                ticker_obj = yf.Ticker(yf_ticker)
                
                # Extrai dados históricos
                if start_date and end_date:
                    hist_data = ticker_obj.history(start=start_date, end=end_date)
                else:
                    hist_data = ticker_obj.history(period=period)
                
                if hist_data.empty:
                    logger.warning("Dados vazios para ticker", ticker=ticker)
                    return None
                
                # Adiciona coluna ticker
                hist_data['ticker'] = ticker
                
                # Reseta índice para incluir datetime como coluna
                hist_data = hist_data.reset_index()
                
                # Renomeia colunas para padrão
                hist_data = hist_data.rename(columns={
                    'Date': 'datetime',
                    'Open': 'open',
                    'Close': 'close',
                    'High': 'high',
                    'Low': 'low',
                    'Volume': 'volume'
                })
                
                logger.debug("Extração bem-sucedida", ticker=ticker, rows=len(hist_data))
                return hist_data
                
            except Exception as e:
                logger.warning("Tentativa falhou", ticker=ticker, attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Backoff exponencial
                else:
                    logger.error("Todas as tentativas falharam", ticker=ticker, error=str(e))
                    return None
        
        return None
    
    def _extract_realtime_single_ticker(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Extrai dados em tempo real para um único ticker.
        
        Args:
            ticker (str): Ticker para extrair
            
        Returns:
            Optional[pd.DataFrame]: DataFrame com dados ou None se falhar
        """
        yf_ticker = self.ticker_mapping.get(ticker, f"{ticker}.SA")
        
        try:
            ticker_obj = yf.Ticker(yf_ticker)
            
            # Obtém informações em tempo real
            info = ticker_obj.info
            
            # Cria DataFrame com dados atuais
            current_data = pd.DataFrame([{
                'datetime': pd.Timestamp.now(),
                'ticker': ticker,
                'open': info.get('open', None),
                'close': info.get('currentPrice', info.get('regularMarketPrice', None)),
                'high': info.get('dayHigh', None),
                'low': info.get('dayLow', None),
                'volume': info.get('volume', None)
            }])
            
            return current_data
            
        except Exception as e:
            logger.error("Erro ao extrair dados em tempo real", ticker=ticker, error=str(e))
            return None
    
    def _standardize_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Padroniza o formato do DataFrame para consistência.
        
        Args:
            df (pd.DataFrame): DataFrame a ser padronizado
            
        Returns:
            pd.DataFrame: DataFrame padronizado
        """
        if df.empty:
            return df
        
        # Garante que datetime seja datetime
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Converte colunas numéricas
        numeric_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove linhas com valores nulos críticos
        df = df.dropna(subset=['datetime', 'ticker', 'close'])
        
        # Ordena por datetime e ticker
        df = df.sort_values(['datetime', 'ticker']).reset_index(drop=True)
        
        return df
    
    def get_available_tickers(self) -> List[str]:
        """
        Retorna lista de tickers disponíveis no mapeamento.
        
        Returns:
            List[str]: Lista de tickers disponíveis
        """
        return list(self.ticker_mapping.keys())
    
    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        Obtém informações básicas sobre um ticker.
        
        Args:
            ticker (str): Ticker para consultar
            
        Returns:
            Dict[str, Any]: Informações do ticker
        """
        try:
            yf_ticker = self.ticker_mapping.get(ticker, f"{ticker}.SA")
            ticker_obj = yf.Ticker(yf_ticker)
            info = ticker_obj.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', 'N/A')),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'currency': info.get('currency', 'BRL')
            }
            
        except Exception as e:
            logger.error("Erro ao obter informações do ticker", ticker=ticker, error=str(e))
            return {'ticker': ticker, 'error': str(e)} 