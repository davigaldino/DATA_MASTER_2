"""
Carregador para banco de dados PostgreSQL.

Este módulo contém a classe PostgresLoader que é responsável por:
- Conectar ao banco PostgreSQL
- Criar tabelas se não existirem
- Carregar dados processados
- Validar integridade dos dados
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Any
import structlog
import os
from datetime import datetime

logger = structlog.get_logger(__name__)


class PostgresLoader:
    """
    Classe para carregar dados processados no PostgreSQL.
    
    Esta classe gerencia a conexão com o banco de dados PostgreSQL
    e implementa métodos para carregar dados de ações e indicadores.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Inicializa o carregador PostgreSQL.
        
        Args:
            connection_string (str, optional): String de conexão com o banco
        """
        if connection_string:
            self.connection_string = connection_string
        else:
            # Usa variáveis de ambiente
            self.connection_string = (
                f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
                f"{os.getenv('DB_PASSWORD', 'password')}@"
                f"{os.getenv('DB_HOST', 'localhost')}:"
                f"{os.getenv('DB_PORT', '5432')}/"
                f"{os.getenv('DB_NAME', 'datamaster2')}"
            )
        
        self.engine = None
        self._create_tables()
    
    def _create_tables(self):
        """Verifica se as tabelas do Django existem."""
        try:
            self.engine = create_engine(self.connection_string)
            
            # Verifica se as tabelas existem
            check_tables_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('stock_data', 'technical_indicators', 'data_metadata')
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(check_tables_sql))
                existing_tables = [row[0] for row in result]
                
                required_tables = ['stock_data', 'technical_indicators', 'data_metadata']
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if missing_tables:
                    logger.warning("Tabelas faltando", missing_tables=missing_tables)
                    logger.info("Execute 'python manage.py migrate' no Django para criar as tabelas")
                else:
                                logger.info("Todas as tabelas necessárias existem", tables=existing_tables)
            
        except Exception as e:
            logger.error("Erro ao verificar tabelas", error=str(e))
            raise
    
    def load_stock_data(self, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Carrega dados de ações no banco de dados.
        
        Args:
            df (pd.DataFrame): DataFrame com dados de ações
            batch_size (int): Tamanho do lote para inserção
            
        Returns:
            Dict[str, Any]: Relatório da operação de carga
        """
        try:
            logger.info("Iniciando carregamento de dados de ações", rows=len(df))
            
            # Insere dados em lotes usando SQLAlchemy
            inserted_count = 0
            with self.engine.begin() as conn:
                for i in range(0, len(df), batch_size):
                    batch_df = df.iloc[i:i + batch_size]
                    
                    # Prepara dados para inserção
                    data_to_insert = []
                    for _, row in batch_df.iterrows():
                        data_to_insert.append({
                            'datetime': row['datetime'],
                            'ticker': row['ticker'],
                            'open': row.get('open'),
                            'close': row['close'],
                            'high': row.get('high'),
                            'low': row.get('low'),
                            'volume': row.get('volume')
                        })
                    
                    # Insere o lote
                    insert_sql = """
                    INSERT INTO stock_data (date, ticker, open, close, high, low, volume)
                    VALUES (:datetime, :ticker, :open, :close, :high, :low, :volume)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        close = EXCLUDED.close,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        volume = EXCLUDED.volume,
                        updated_at = CURRENT_TIMESTAMP
                    """
                    
                    conn.execute(text(insert_sql), data_to_insert)
                    inserted_count += len(data_to_insert)
                    
                    logger.debug("Lote inserido", batch_number=i//batch_size + 1,
                               inserted_in_batch=len(data_to_insert))
            
            # Atualiza metadados
            self._update_metadata('stock_data', df)
            
            logger.info("Carregamento de dados de ações concluído", 
                       total_inserted=inserted_count)
            
            return {
                'table': 'stock_data',
                'inserted_count': inserted_count,
                'total_rows': len(df),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error("Erro durante carregamento de dados de ações", error=str(e))
            raise
    
    def load_technical_indicators(self, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Carrega indicadores técnicos no banco de dados.
        
        Args:
            df (pd.DataFrame): DataFrame com indicadores técnicos
            batch_size (int): Tamanho do lote para inserção
            
        Returns:
            Dict[str, Any]: Relatório da operação de carga
        """
        try:
            logger.info("Iniciando carregamento de indicadores técnicos", rows=len(df))
            
            # Insere dados linha por linha para evitar problemas com placeholders
            inserted_count = 0
            with self.engine.begin() as conn:
                for _, row in df.iterrows():
                    # Converte a data para o formato correto
                    if isinstance(row['date'], str):
                        from datetime import datetime
                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    else:
                        date_obj = row['date']
                    
                    insert_sql = """
                    INSERT INTO technical_indicators (
                        date, ticker, daily_return, log_return, cumulative_return,
                        sma_5, sma_10, sma_20, sma_50, sma_200,
                        ema_5, ema_10, ema_20, ema_50, ema_200,
                        true_range, atr_14, volatility_20,
                        bb_upper, bb_middle, bb_lower, bb_width, bb_position,
                        rsi_14, macd, macd_signal, macd_histogram,
                        stochastic_k, stochastic_d, williams_r,
                        obv, vpt, mfi_14
                    ) VALUES (
                        :date, :ticker, :daily_return, :log_return, :cumulative_return,
                        :sma_5, :sma_10, :sma_20, :sma_50, :sma_200,
                        :ema_5, :ema_10, :ema_20, :ema_50, :ema_200,
                        :true_range, :atr_14, :volatility_20,
                        :bb_upper, :bb_middle, :bb_lower, :bb_width, :bb_position,
                        :rsi_14, :macd, :macd_signal, :macd_histogram,
                        :stochastic_k, :stochastic_d, :williams_r,
                        :obv, :vpt, :mfi_14
                    )
                    ON CONFLICT (date, ticker) DO UPDATE SET
                        daily_return = EXCLUDED.daily_return,
                        log_return = EXCLUDED.log_return,
                        cumulative_return = EXCLUDED.cumulative_return,
                        sma_5 = EXCLUDED.sma_5, sma_10 = EXCLUDED.sma_10, sma_20 = EXCLUDED.sma_20,
                        sma_50 = EXCLUDED.sma_50, sma_200 = EXCLUDED.sma_200,
                        ema_5 = EXCLUDED.ema_5, ema_10 = EXCLUDED.ema_10, ema_20 = EXCLUDED.ema_20,
                        ema_50 = EXCLUDED.ema_50, ema_200 = EXCLUDED.ema_200,
                        true_range = EXCLUDED.true_range, atr_14 = EXCLUDED.atr_14, volatility_20 = EXCLUDED.volatility_20,
                        bb_upper = EXCLUDED.bb_upper, bb_middle = EXCLUDED.bb_middle,
                        bb_lower = EXCLUDED.bb_lower, bb_width = EXCLUDED.bb_width, bb_position = EXCLUDED.bb_position,
                        rsi_14 = EXCLUDED.rsi_14, macd = EXCLUDED.macd,
                        macd_signal = EXCLUDED.macd_signal, macd_histogram = EXCLUDED.macd_histogram,
                        stochastic_k = EXCLUDED.stochastic_k, stochastic_d = EXCLUDED.stochastic_d, williams_r = EXCLUDED.williams_r,
                        obv = EXCLUDED.obv, vpt = EXCLUDED.vpt, mfi_14 = EXCLUDED.mfi_14,
                        updated_at = CURRENT_TIMESTAMP
                    """
                    
                    params = {
                        'date': date_obj,
                        'ticker': row['ticker'],
                        'daily_return': row.get('daily_return'),
                        'log_return': row.get('daily_log_return'),
                        'cumulative_return': row.get('cumulative_return'),
                        'sma_5': row.get('sma_5'), 'sma_10': row.get('sma_10'), 'sma_20': row.get('sma_20'),
                        'sma_50': row.get('sma_50'), 'sma_200': row.get('sma_200'),
                        'ema_5': row.get('ema_5'), 'ema_10': row.get('ema_10'), 'ema_20': row.get('ema_20'),
                        'ema_50': row.get('ema_50'), 'ema_200': row.get('ema_200'),
                        'true_range': row.get('tr'), 'atr_14': row.get('atr_14'), 'volatility_20': row.get('volatility_20d'),
                        'bb_upper': row.get('bb_upper'), 'bb_middle': row.get('bb_middle'),
                        'bb_lower': row.get('bb_lower'), 'bb_width': row.get('bb_width'), 'bb_position': row.get('bb_position'),
                        'rsi_14': row.get('rsi_14'), 'macd': row.get('macd'),
                        'macd_signal': row.get('macd_signal'), 'macd_histogram': row.get('macd_histogram'),
                        'stochastic_k': row.get('stoch_k'), 'stochastic_d': row.get('stoch_d'), 'williams_r': row.get('williams_r'),
                        'obv': row.get('obv'), 'vpt': row.get('vpt'), 'mfi_14': row.get('mfi')
                    }
                    
                    conn.execute(text(insert_sql), params)
                    inserted_count += 1
                    
                    if inserted_count % 100 == 0:
                        logger.debug("Indicadores inseridos", count=inserted_count)
            
            # Atualiza metadados
            self._update_metadata('technical_indicators', df)
            
            logger.info("Carregamento de indicadores técnicos concluído", 
                       total_inserted=inserted_count)
            
            return {
                'table': 'technical_indicators',
                'inserted_count': inserted_count,
                'total_rows': len(df),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error("Erro durante carregamento de indicadores técnicos", error=str(e))
            raise
    
    def _update_metadata(self, table_name: str, df: pd.DataFrame):
        """
        Atualiza metadados da tabela.
        
        Args:
            table_name (str): Nome da tabela
            df (pd.DataFrame): DataFrame carregado
        """
        try:
            metadata_sql = """
            INSERT INTO data_metadata (table_name, last_update, record_count, date_range_start, date_range_end, tickers)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (table_name) DO UPDATE SET
                last_update = EXCLUDED.last_update,
                record_count = EXCLUDED.record_count,
                date_range_start = EXCLUDED.date_range_start,
                date_range_end = EXCLUDED.date_range_end,
                tickers = EXCLUDED.tickers
            """
            
            with self.engine.begin() as conn:
                conn.execute(text(metadata_sql), (
                    table_name,
                    datetime.now(),
                    len(df),
                    df['datetime'].min() if 'datetime' in df.columns else None,
                    df['datetime'].max() if 'datetime' in df.columns else None,
                    list(df['ticker'].unique()) if 'ticker' in df.columns else []
                ))
            
            logger.info("Metadados atualizados", table=table_name)
            
        except Exception as e:
            logger.error("Erro ao atualizar metadados", table=table_name, error=str(e))
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém informações sobre uma tabela.
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            Dict[str, Any]: Informações da tabela
        """
        try:
            with self.engine.connect() as conn:
                # Conta registros
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                record_count = count_result.scalar()
                
                # Obtém metadados
                metadata_result = conn.execute(text(
                    "SELECT * FROM data_metadata WHERE table_name = :table_name"
                ), {'table_name': table_name})
                metadata = metadata_result.fetchone()
                
                info = {
                    'table_name': table_name,
                    'record_count': record_count,
                    'metadata': metadata._asdict() if metadata else None
                }
                
                logger.info("Informações da tabela obtidas", table=table_name, info=info)
                return info
                
        except Exception as e:
            logger.error("Erro ao obter informações da tabela", table=table_name, error=str(e))
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o banco de dados.
        
        Returns:
            bool: True se a conexão for bem-sucedida
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Conexão com banco de dados testada com sucesso")
            return True
        except Exception as e:
            logger.error("Erro ao testar conexão com banco de dados", error=str(e))
            return False 