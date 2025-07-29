"""
DAG do Apache Airflow para pipeline ETL de dados da B3
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.email_operator import EmailOperator
from airflow.models import Variable
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from etl.extractors.csv_extractor import CSVExtractor
from etl.extractors.yfinance_extractor import YFinanceExtractor
from etl.transformers.data_cleaner import DataCleaner
from etl.transformers.technical_indicators import TechnicalIndicators
from etl.loaders.postgres_loader import PostgresLoader
import structlog

# Configurar logging
logger = structlog.get_logger()

# Argumentos padrão do DAG
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Criar o DAG
dag = DAG(
    'b3_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL para dados da B3',
    schedule_interval='0 2 * * *',  # Executar diariamente às 2h da manhã
    catchup=False,
    tags=['b3', 'etl', 'stocks', 'brazil'],
)

def extract_csv_data(**context):
    """Extrair dados do arquivo CSV histórico"""
    logger.info("Iniciando extração de dados CSV")
    
    try:
        extractor = CSVExtractor()
        
        # Obter parâmetros do contexto do Airflow
        tickers = context['dag_run'].conf.get('tickers', None)
        start_date = context['dag_run'].conf.get('start_date', None)
        end_date = context['dag_run'].conf.get('end_date', None)
        
        # Extrair dados
        df = extractor.extract(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date
        )
        
        # Salvar dados extraídos para uso nas próximas tarefas
        context['task_instance'].xcom_push(key='csv_data', value=df.to_json())
        
        logger.info(f"Extração CSV concluída: {len(df)} registros")
        return f"Extraídos {len(df)} registros do CSV"
        
    except Exception as e:
        logger.error(f"Erro na extração CSV: {e}")
        raise

def extract_yfinance_data(**context):
    """Extrair dados complementares do Yahoo Finance"""
    logger.info("Iniciando extração de dados Yahoo Finance")
    
    try:
        extractor = YFinanceExtractor()
        
        # Obter tickers para atualização
        tickers = context['dag_run'].conf.get('tickers', ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA'])
        period = context['dag_run'].conf.get('period', '1y')
        
        # Extrair dados históricos
        df = extractor.extract_historical_data(
            tickers=tickers,
            period=period
        )
        
        # Salvar dados extraídos
        context['task_instance'].xcom_push(key='yfinance_data', value=df.to_json())
        
        logger.info(f"Extração Yahoo Finance concluída: {len(df)} registros")
        return f"Extraídos {len(df)} registros do Yahoo Finance"
        
    except Exception as e:
        logger.error(f"Erro na extração Yahoo Finance: {e}")
        raise

def clean_data(**context):
    """Limpar e validar dados"""
    logger.info("Iniciando limpeza de dados")
    
    try:
        cleaner = DataCleaner()
        
        # Obter dados das tarefas anteriores
        csv_data = context['task_instance'].xcom_pull(task_ids='extract_csv_data', key='csv_data')
        yfinance_data = context['task_instance'].xcom_pull(task_ids='extract_yfinance_data', key='yfinance_data')
        
        import pandas as pd
        
        # Combinar dados
        df_csv = pd.read_json(csv_data) if csv_data else pd.DataFrame()
        df_yf = pd.read_json(yfinance_data) if yfinance_data else pd.DataFrame()
        
        if not df_csv.empty and not df_yf.empty:
            df_combined = pd.concat([df_csv, df_yf], ignore_index=True)
        elif not df_csv.empty:
            df_combined = df_csv
        elif not df_yf.empty:
            df_combined = df_yf
        else:
            raise ValueError("Nenhum dado disponível para limpeza")
        
        # Limpar dados
        df_cleaned = cleaner.clean_data(df_combined)
        
        # Salvar dados limpos
        context['task_instance'].xcom_push(key='cleaned_data', value=df_cleaned.to_json())
        
        logger.info(f"Limpeza concluída: {len(df_cleaned)} registros válidos")
        return f"Limpos {len(df_cleaned)} registros"
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise

def calculate_indicators(**context):
    """Calcular indicadores técnicos"""
    logger.info("Iniciando cálculo de indicadores técnicos")
    
    try:
        indicators = TechnicalIndicators()
        
        # Obter dados limpos
        cleaned_data = context['task_instance'].xcom_pull(task_ids='clean_data', key='cleaned_data')
        
        import pandas as pd
        df = pd.read_json(cleaned_data)
        
        # Calcular indicadores
        df_with_indicators = indicators.calculate_all_indicators(df)
        
        # Separar dados de ações e indicadores
        stock_columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        indicator_columns = [col for col in df_with_indicators.columns if col not in stock_columns]
        
        df_stocks = df_with_indicators[stock_columns].copy()
        df_indicators = df_with_indicators[['ticker', 'date'] + indicator_columns].copy()
        
        # Salvar dados separados
        context['task_instance'].xcom_push(key='stock_data', value=df_stocks.to_json())
        context['task_instance'].xcom_push(key='indicator_data', value=df_indicators.to_json())
        
        logger.info(f"Cálculo de indicadores concluído: {len(df_with_indicators)} registros")
        return f"Calculados indicadores para {len(df_with_indicators)} registros"
        
    except Exception as e:
        logger.error(f"Erro no cálculo de indicadores: {e}")
        raise

def load_stock_data(**context):
    """Carregar dados de ações no PostgreSQL"""
    logger.info("Iniciando carregamento de dados de ações")
    
    try:
        loader = PostgresLoader()
        
        # Obter dados de ações
        stock_data = context['task_instance'].xcom_pull(task_ids='calculate_indicators', key='stock_data')
        
        import pandas as pd
        df_stocks = pd.read_json(stock_data)
        
        # Carregar dados
        records_loaded = loader.load_stock_data(df_stocks)
        
        logger.info(f"Carregamento de ações concluído: {records_loaded} registros")
        return f"Carregados {records_loaded} registros de ações"
        
    except Exception as e:
        logger.error(f"Erro no carregamento de ações: {e}")
        raise

def load_indicators(**context):
    """Carregar indicadores técnicos no PostgreSQL"""
    logger.info("Iniciando carregamento de indicadores técnicos")
    
    try:
        loader = PostgresLoader()
        
        # Obter dados de indicadores
        indicator_data = context['task_instance'].xcom_pull(task_ids='calculate_indicators', key='indicator_data')
        
        import pandas as pd
        df_indicators = pd.read_json(indicator_data)
        
        # Carregar indicadores
        records_loaded = loader.load_technical_indicators(df_indicators)
        
        logger.info(f"Carregamento de indicadores concluído: {records_loaded} registros")
        return f"Carregados {records_loaded} registros de indicadores"
        
    except Exception as e:
        logger.error(f"Erro no carregamento de indicadores: {e}")
        raise

def update_metadata(**context):
    """Atualizar metadados dos dados carregados"""
    logger.info("Atualizando metadados")
    
    try:
        loader = PostgresLoader()
        
        # Obter informações das tarefas anteriores
        csv_records = context['task_instance'].xcom_pull(task_ids='extract_csv_data')
        yf_records = context['task_instance'].xcom_pull(task_ids='extract_yfinance_data')
        stock_records = context['task_instance'].xcom_pull(task_ids='load_stock_data')
        indicator_records = context['task_instance'].xcom_pull(task_ids='load_indicators')
        
        # Atualizar metadados
        metadata = {
            'total_records': stock_records,
            'indicators_calculated': indicator_records,
            'last_updated': datetime.now().isoformat(),
            'processing_status': 'completed'
        }
        
        loader.update_metadata(metadata)
        
        logger.info("Metadados atualizados com sucesso")
        return "Metadados atualizados"
        
    except Exception as e:
        logger.error(f"Erro na atualização de metadados: {e}")
        raise

# Definir tarefas
extract_csv_task = PythonOperator(
    task_id='extract_csv_data',
    python_callable=extract_csv_data,
    dag=dag,
)

extract_yfinance_task = PythonOperator(
    task_id='extract_yfinance_data',
    python_callable=extract_yfinance_data,
    dag=dag,
)

clean_data_task = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    dag=dag,
)

calculate_indicators_task = PythonOperator(
    task_id='calculate_indicators',
    python_callable=calculate_indicators,
    dag=dag,
)

load_stock_data_task = PythonOperator(
    task_id='load_stock_data',
    python_callable=load_stock_data,
    dag=dag,
)

load_indicators_task = PythonOperator(
    task_id='load_indicators',
    python_callable=load_indicators,
    dag=dag,
)

update_metadata_task = PythonOperator(
    task_id='update_metadata',
    python_callable=update_metadata,
    dag=dag,
)

# Definir dependências
[extract_csv_task, extract_yfinance_task] >> clean_data_task
clean_data_task >> calculate_indicators_task
calculate_indicators_task >> [load_stock_data_task, load_indicators_task]
[load_stock_data_task, load_indicators_task] >> update_metadata_task 