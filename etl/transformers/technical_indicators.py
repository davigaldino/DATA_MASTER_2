"""
Transformador para cálculo de indicadores técnicos.

Este módulo contém a classe TechnicalIndicators que é responsável por:
- Calcular médias móveis (simples e exponencial)
- Calcular indicadores de volatilidade
- Calcular RSI, MACD e outros indicadores
- Calcular retornos e outras métricas financeiras
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class TechnicalIndicators:
    """
    Classe para cálculo de indicadores técnicos financeiros.
    
    Esta classe implementa métodos para calcular diversos indicadores
    técnicos utilizados em análise de mercado de ações.
    """
    
    def __init__(self):
        """Inicializa o calculador de indicadores técnicos."""
        pass
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula todos os indicadores técnicos disponíveis.
        
        Args:
            df (pd.DataFrame): DataFrame com dados de preços
            
        Returns:
            pd.DataFrame: DataFrame enriquecido com indicadores
        """
        try:
            logger.info("Iniciando cálculo de indicadores técnicos", initial_rows=len(df))
            
            # Calcula indicadores básicos em sequência
            enriched_df = self._calculate_returns(df)
            enriched_df = self._calculate_moving_averages(enriched_df)
            enriched_df = self._calculate_volatility_indicators(enriched_df)
            enriched_df = self._calculate_momentum_indicators(enriched_df)
            enriched_df = self._calculate_volume_indicators(enriched_df)
            
            # Remove apenas linhas onde TODAS as colunas de indicadores são NaN
            # Preserva linhas que têm pelo menos alguns indicadores válidos
            indicator_columns = [col for col in enriched_df.columns if col not in 
                               ['datetime', 'date', 'ticker', 'open', 'close', 'high', 'low', 'volume']]
            
            if indicator_columns:
                # Remove linhas onde TODOS os indicadores são NaN
                enriched_df = enriched_df.dropna(subset=indicator_columns, how='all')
            
            logger.info("Cálculo de indicadores técnicos concluído", 
                       final_rows=len(enriched_df))
            
            return enriched_df
            
        except Exception as e:
            logger.error("Erro durante cálculo de indicadores", error=str(e))
            raise
    
    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula retornos diários, semanais e mensais.
        
        Args:
            df (pd.DataFrame): DataFrame com dados de preços
            
        Returns:
            pd.DataFrame: DataFrame com retornos calculados
        """
        result_dfs = []
        for ticker in df['ticker'].unique():
            ticker_mask = df['ticker'] == ticker
            ticker_data = df.loc[ticker_mask].sort_values('date').copy()
            
            # Retorno diário
            ticker_data['daily_return'] = ticker_data['close'].pct_change()
            
            # Retorno logarítmico diário
            ticker_data['daily_log_return'] = ticker_data['close'].apply(np.log).diff()
            
            # Retorno acumulado
            ticker_data['cumulative_return'] = ticker_data['daily_return'].cumsum()
            
            # Retorno desde o início
            if len(ticker_data) > 0:
                total_return = (ticker_data['close'].iloc[-1] / ticker_data['close'].iloc[0]) - 1
                ticker_data['total_return'] = total_return
            else:
                ticker_data['total_return'] = 0
            
            result_dfs.append(ticker_data)
        
        result_df = pd.concat(result_dfs, ignore_index=True)
        logger.info("Retornos calculados")
        return result_df
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        periods = [5, 10, 20, 50, 100, 200]
        result_dfs = []
        for ticker in df['ticker'].unique():
            ticker_mask = df['ticker'] == ticker
            ticker_data = df.loc[ticker_mask].sort_values('date').copy()
            for period in periods:
                ticker_data[f'sma_{period}'] = ticker_data['close'].rolling(window=period).mean()
                ticker_data[f'ema_{period}'] = ticker_data['close'].ewm(span=period).mean()
                ticker_data[f'price_vs_sma_{period}_pct'] = ((ticker_data['close'] - ticker_data[f'sma_{period}']) / ticker_data[f'sma_{period}']) * 100
            result_dfs.append(ticker_data)
        result_df = pd.concat(result_dfs, ignore_index=True)
        logger.info("Médias móveis calculadas", periods=periods)
        return result_df
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        periods = [5, 10, 20, 30]
        result_dfs = []
        for ticker in df['ticker'].unique():
            ticker_mask = df['ticker'] == ticker
            ticker_data = df.loc[ticker_mask].sort_values('date').copy()
            for period in periods:
                if 'daily_return' in ticker_data.columns:
                    ticker_data[f'volatility_{period}d'] = ticker_data['daily_return'].rolling(window=period).std() * np.sqrt(252)
            tr_values = []
            for i in range(len(ticker_data)):
                if i == 0:
                    tr = ticker_data['high'].iloc[i] - ticker_data['low'].iloc[i]
                else:
                    tr1 = ticker_data['high'].iloc[i] - ticker_data['low'].iloc[i]
                    tr2 = abs(ticker_data['high'].iloc[i] - ticker_data['close'].iloc[i-1])
                    tr3 = abs(ticker_data['low'].iloc[i] - ticker_data['close'].iloc[i-1])
                    tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            ticker_data['tr'] = tr_values
            ticker_data['atr_14'] = ticker_data['tr'].rolling(window=14).mean()
            bb_middle = ticker_data['close'].rolling(window=20).mean()
            bb_std = ticker_data['close'].rolling(window=20).std()
            ticker_data['bb_middle'] = bb_middle
            ticker_data['bb_upper'] = bb_middle + (bb_std * 2)
            ticker_data['bb_lower'] = bb_middle - (bb_std * 2)
            ticker_data['bb_width'] = (ticker_data['bb_upper'] - ticker_data['bb_lower']) / ticker_data['bb_middle']
            ticker_data['bb_position'] = (ticker_data['close'] - ticker_data['bb_lower']) / (ticker_data['bb_upper'] - ticker_data['bb_lower'])
            result_dfs.append(ticker_data)
        result_df = pd.concat(result_dfs, ignore_index=True)
        logger.info("Indicadores de volatilidade calculados")
        return result_df
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        result_dfs = []
        for ticker in df['ticker'].unique():
            ticker_mask = df['ticker'] == ticker
            ticker_data = df.loc[ticker_mask].sort_values('date').copy()
            delta = ticker_data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            ticker_data['rsi_14'] = 100 - (100 / (1 + rs))
            gain21 = delta.where(delta > 0, 0).rolling(window=21).mean()
            loss21 = (-delta.where(delta < 0, 0)).rolling(window=21).mean()
            rs21 = gain21 / loss21
            ticker_data['rsi_21'] = 100 - (100 / (1 + rs21))
            ema_12 = ticker_data['close'].ewm(span=12).mean()
            ema_26 = ticker_data['close'].ewm(span=26).mean()
            ticker_data['macd'] = ema_12 - ema_26
            ticker_data['macd_signal'] = ticker_data['macd'].ewm(span=9).mean()
            ticker_data['macd_histogram'] = ticker_data['macd'] - ticker_data['macd_signal']
            lowest_low = ticker_data['low'].rolling(window=14).min()
            highest_high = ticker_data['high'].rolling(window=14).max()
            ticker_data['stoch_k'] = 100 * ((ticker_data['close'] - lowest_low) / (highest_high - lowest_low))
            ticker_data['stoch_d'] = ticker_data['stoch_k'].rolling(window=3).mean()
            highest_high_w = ticker_data['high'].rolling(window=14).max()
            lowest_low_w = ticker_data['low'].rolling(window=14).min()
            ticker_data['williams_r'] = -100 * ((highest_high_w - ticker_data['close']) / (highest_high_w - lowest_low_w))
            result_dfs.append(ticker_data)
        result_df = pd.concat(result_dfs, ignore_index=True)
        logger.info("Indicadores de momentum calculados")
        return result_df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        result_dfs = []
        for ticker in df['ticker'].unique():
            ticker_mask = df['ticker'] == ticker
            ticker_data = df.loc[ticker_mask].sort_values('date').copy()
            ticker_data['volume_sma_20'] = ticker_data['volume'].rolling(window=20).mean()
            ticker_data['volume_ratio'] = ticker_data['volume'] / ticker_data['volume_sma_20']
            obv = [ticker_data['volume'].iloc[0]]
            for i in range(1, len(ticker_data)):
                if ticker_data['close'].iloc[i] > ticker_data['close'].iloc[i-1]:
                    obv.append(obv[-1] + ticker_data['volume'].iloc[i])
                elif ticker_data['close'].iloc[i] < ticker_data['close'].iloc[i-1]:
                    obv.append(obv[-1] - ticker_data['volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            ticker_data['obv'] = obv
            vpt = [0]
            for i in range(1, len(ticker_data)):
                if 'daily_return' in ticker_data.columns:
                    vpt.append(vpt[-1] + ticker_data['volume'].iloc[i] * ticker_data['daily_return'].iloc[i])
                else:
                    vpt.append(vpt[-1])
            ticker_data['vpt'] = vpt
            typical_price = (ticker_data['high'] + ticker_data['low'] + ticker_data['close']) / 3
            money_flow = typical_price * ticker_data['volume']
            positive_flow = pd.Series(0, index=typical_price.index)
            negative_flow = pd.Series(0, index=typical_price.index)
            for i in range(1, len(typical_price)):
                if typical_price.iloc[i] > typical_price.iloc[i-1]:
                    positive_flow.iloc[i] = money_flow.iloc[i]
                elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                    negative_flow.iloc[i] = money_flow.iloc[i]
            positive_mf = positive_flow.rolling(window=14).sum()
            negative_mf = negative_flow.rolling(window=14).sum()
            ticker_data['mfi'] = 100 - (100 / (1 + (positive_mf / negative_mf)))
            result_dfs.append(ticker_data)
        result_df = pd.concat(result_dfs, ignore_index=True)
        logger.info("Indicadores de volume calculados")
        return result_df
    
    def get_indicators_summary(self, df: pd.DataFrame) -> Dict:
        """
        Gera resumo dos indicadores calculados.
        
        Args:
            df (pd.DataFrame): DataFrame com indicadores
            
        Returns:
            Dict: Resumo dos indicadores
        """
        # Identifica colunas de indicadores
        indicator_columns = [col for col in df.columns if col not in 
                           ['datetime', 'ticker', 'open', 'close', 'high', 'low', 'volume']]
        
        summary = {
            'total_indicators': len(indicator_columns),
            'indicator_categories': {
                'returns': [col for col in indicator_columns if 'return' in col.lower()],
                'moving_averages': [col for col in indicator_columns if 'sma' in col or 'ema' in col],
                'volatility': [col for col in indicator_columns if 'volatility' in col or 'bb_' in col or 'atr' in col],
                'momentum': [col for col in indicator_columns if any(x in col for x in ['rsi', 'macd', 'stoch', 'williams'])],
                'volume': [col for col in indicator_columns if 'volume' in col or 'obv' in col or 'mfi' in col or 'vpt' in col]
            },
            'data_points': len(df),
            'tickers': df['ticker'].nunique() if 'ticker' in df.columns else 0
        }
        
        logger.info("Resumo dos indicadores gerado", summary=summary)
        return summary 