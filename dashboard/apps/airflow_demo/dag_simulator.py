"""
Simulador de DAG do Apache Airflow
Emula o comportamento do Airflow para demonstração
"""

import threading
import time
import pandas as pd
import os
import sys
from datetime import datetime
from django.utils import timezone
from django.db import transaction

# Adicionar o diretório do projeto ao path para importar módulos ETL
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'etl'))

from .models import DAGRun, TaskInstance


class DAGSimulator:
    """Simulador de execução de DAG do Airflow"""
    
    def __init__(self, dag_run_id):
        self.dag_run_id = dag_run_id
        self.dag_run = None
        self.task_instances = {}
        self.data = None
        self.transformed_data = None
        
        # Definir as tarefas e suas dependências
        self.tasks = {
            'start': {
                'dependencies': [],
                'executor': self._execute_start,
                'description': 'Iniciando pipeline de dados'
            },
            'extract_data': {
                'dependencies': ['start'],
                'executor': self._execute_extract_data,
                'description': 'Extraindo dados do arquivo CSV'
            },
            'transform_data': {
                'dependencies': ['extract_data'],
                'executor': self._execute_transform_data,
                'description': 'Transformando dados e calculando indicadores'
            },
            'load_to_postgres': {
                'dependencies': ['transform_data'],
                'executor': self._execute_load_postgres,
                'description': 'Carregando dados no PostgreSQL'
            },
            'load_to_mongodb': {
                'dependencies': ['transform_data'],
                'executor': self._execute_load_mongodb,
                'description': 'Carregando dados no MongoDB'
            },
            'validate_data': {
                'dependencies': ['load_to_postgres', 'load_to_mongodb'],
                'executor': self._execute_validate_data,
                'description': 'Validando qualidade dos dados'
            },
            'end': {
                'dependencies': ['validate_data'],
                'executor': self._execute_end,
                'description': 'Finalizando pipeline'
            }
        }
    
    def run_dag(self):
        """Executa o DAG completo"""
        try:
            # Obter o DAG Run
            self.dag_run = DAGRun.objects.get(run_id=self.dag_run_id)
            
            # Atualizar status para RUNNING
            self._update_dag_status('RUNNING')
            self._log_message(f"🚀 Iniciando execução do DAG: {self.dag_run.dag_name}")
            
            # Criar instâncias de tarefas
            self._create_task_instances()
            
            # Executar tarefas em ordem topológica
            execution_order = self._get_execution_order()
            
            for task_id in execution_order:
                if not self._can_execute_task(task_id):
                    continue
                
                # Executar tarefa
                success = self._execute_task(task_id)
                
                if not success:
                    self._update_dag_status('FAILED')
                    return False
            
            # Finalizar DAG
            self._update_dag_status('SUCCESS')
            self._log_message("✅ Pipeline executado com sucesso!")
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro na execução do DAG: {str(e)}")
            self._update_dag_status('FAILED')
            return False
    
    def _create_task_instances(self):
        """Cria as instâncias de tarefas no banco"""
        with transaction.atomic():
            for task_id in self.tasks.keys():
                task_instance = TaskInstance.objects.create(
                    dag_run=self.dag_run,
                    task_id=task_id,
                    status='QUEUED'
                )
                self.task_instances[task_id] = task_instance
            
            # Atualizar total de tarefas no DAG Run
            self.dag_run.total_tasks = len(self.tasks)
            self.dag_run.save()
    
    def _get_execution_order(self):
        """Retorna a ordem de execução das tarefas"""
        return ['start', 'extract_data', 'transform_data', 'load_to_postgres', 'load_to_mongodb', 'validate_data', 'end']
    
    def _can_execute_task(self, task_id):
        """Verifica se uma tarefa pode ser executada baseado nas dependências"""
        dependencies = self.tasks[task_id]['dependencies']
        
        for dep in dependencies:
            if dep in self.task_instances:
                dep_instance = self.task_instances[dep]
                if dep_instance.status != 'SUCCESS':
                    return False
        
        return True
    
    def _execute_task(self, task_id):
        """Executa uma tarefa específica"""
        try:
            task_instance = self.task_instances[task_id]
            task_info = self.tasks[task_id]
            
            # Atualizar status para RUNNING
            self._update_task_status(task_id, 'RUNNING')
            task_instance.start_time = timezone.now()
            task_instance.save()
            
            self._log_message(f"🔄 Executando tarefa: {task_id} - {task_info['description']}")
            
            # Simular delay para tornar mais realista
            time.sleep(1)
            
            # Executar a tarefa
            success = task_info['executor']()
            
            if success:
                self._update_task_status(task_id, 'SUCCESS')
                self.dag_run.completed_tasks += 1
                self._log_message(f"✅ Tarefa {task_id} concluída com sucesso")
            else:
                self._update_task_status(task_id, 'FAILED')
                self.dag_run.failed_tasks += 1
                self._log_message(f"❌ Tarefa {task_id} falhou")
            
            # Calcular duração
            task_instance.end_time = timezone.now()
            if task_instance.start_time:
                duration = (task_instance.end_time - task_instance.start_time).total_seconds()
                task_instance.duration_seconds = duration
            task_instance.save()
            
            self.dag_run.save()
            return success
            
        except Exception as e:
            self._log_message(f"❌ Erro na tarefa {task_id}: {str(e)}")
            self._update_task_status(task_id, 'FAILED')
            return False
    
    def _update_task_status(self, task_id, status):
        """Atualiza o status de uma tarefa"""
        if task_id in self.task_instances:
            task_instance = self.task_instances[task_id]
            task_instance.status = status
            task_instance.save()
    
    def _update_dag_status(self, status):
        """Atualiza o status do DAG Run"""
        self.dag_run.status = status
        if status in ['SUCCESS', 'FAILED']:
            self.dag_run.end_time = timezone.now()
        self.dag_run.save()
    
    def _log_message(self, message):
        """Adiciona uma mensagem ao log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if self.dag_run.log_output:
            self.dag_run.log_output += log_entry
        else:
            self.dag_run.log_output = log_entry
        
        self.dag_run.save()
    
    # Executores de tarefas
    def _execute_start(self):
        """Tarefa de início"""
        time.sleep(0.5)
        return True
    
    def _execute_extract_data(self):
        """Extrai dados do arquivo CSV"""
        try:
            # Solução definitiva: usar o arquivo CSV real
            # Vamos tentar múltiplos caminhos possíveis para encontrar o arquivo
            possible_paths = [
                # Caminho 1: relativo ao diretório atual do Django
                os.path.join(os.getcwd(), '..', 'data', 'test_small.csv'),
                # Caminho 2: relativo ao arquivo atual
                os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'data', 'test_small.csv'),
                # Caminho 3: absoluto baseado no diretório do projeto
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'test_small.csv'),
                # Caminho 4: direto no diretório data
                'data/test_small.csv',
                # Caminho 5: relativo ao diretório dashboard
                '../data/test_small.csv',
                # Caminho 6: absoluto hardcoded para o projeto
                'C:/Users/davi_/OneDrive/SANTANDER/ENGENHARIA_DE_DADOS/DATA_MASTER_2/data/test_small.csv'
            ]
            
            csv_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    csv_path = path
                    break
            
            if csv_path is None:
                self._log_message(f"❌ Arquivo não encontrado em nenhum dos caminhos tentados:")
                for path in possible_paths:
                    self._log_message(f"   - {path}")
                return False
            
            self._log_message(f"🔍 Procurando arquivo em: {csv_path}")
            
            self._log_message(f"📁 Lendo arquivo: {csv_path}")
            
            # Ler o CSV
            self.data = pd.read_csv(csv_path)
            
            # Renomear coluna datetime para Date
            if 'datetime' in self.data.columns:
                self.data = self.data.rename(columns={'datetime': 'Date'})
            
            # Verificar se a coluna Ticker existe (pode ser 'ticker' em minúsculo)
            if 'ticker' in self.data.columns:
                self.data = self.data.rename(columns={'ticker': 'Ticker'})
            
            # Verificar se as colunas necessárias existem
            required_columns = ['Date', 'Ticker', 'open', 'close', 'high', 'low', 'volume']
            missing_columns = [col for col in required_columns if col not in self.data.columns]
            if missing_columns:
                self._log_message(f"❌ Colunas ausentes: {missing_columns}")
                self._log_message(f"📊 Colunas disponíveis: {list(self.data.columns)}")
                return False
            
            self._log_message(f"✅ Extração concluída: {len(self.data)} registros")
            self._log_message(f"📊 Colunas: {list(self.data.columns)}")
            self._log_message(f"📅 Período: {self.data['Date'].min()} a {self.data['Date'].max()}")
            self._log_message(f"🏢 Tickers únicos: {self.data['Ticker'].nunique()}")
            
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro na extração: {str(e)}")
            return False
    
    def _execute_transform_data(self):
        """Transforma dados e calcula indicadores técnicos"""
        try:
            if self.data is None:
                self._log_message("❌ Nenhum dado para transformar")
                return False
            
            self._log_message(f"🔄 Transformando {len(self.data)} registros")
            
            # Converter coluna de data
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            
            # Ordenar por ticker e data
            self.data = self.data.sort_values(['Ticker', 'Date'])
            
            # Calcular indicadores técnicos
            self._log_message("🔄 Calculando indicadores técnicos...")
            
            indicators_data = []
            
            # Verificar se temos dados suficientes para calcular indicadores
            unique_dates = self.data['Date'].nunique()
            unique_tickers = self.data['Ticker'].nunique()
            
            self._log_message(f"📊 Análise dos dados: {unique_dates} datas únicas, {unique_tickers} tickers únicos")
            
            if unique_dates < 2:
                self._log_message("⚠️ Dados insuficientes para indicadores técnicos (precisa de múltiplas datas)")
                self._log_message("🔄 Aplicando transformações básicas...")
                
                # Transformação básica sem indicadores técnicos
                self.transformed_data = self.data.copy()
                
                # Adicionar colunas básicas
                self.transformed_data['price_change'] = 0  # Sem mudança pois só tem 1 data
                self.transformed_data['price_change_pct'] = 0
                self.transformed_data['volume_normalized'] = self.transformed_data['volume'] / self.transformed_data['volume'].max()
                
                # Simular alguns indicadores básicos
                self.transformed_data['close_ma_1'] = self.transformed_data['close']
                self.transformed_data['volume_ma_1'] = self.transformed_data['volume']
                self.transformed_data['rsi'] = 50  # Valor neutro
                self.transformed_data['macd'] = 0
                self.transformed_data['bb_middle'] = self.transformed_data['close']
                self.transformed_data['bb_upper'] = self.transformed_data['close'] * 1.02
                self.transformed_data['bb_lower'] = self.transformed_data['close'] * 0.98
                
            else:
                # Lógica original para múltiplas datas
                for ticker in self.data['Ticker'].unique():
                    ticker_data = self.data[self.data['Ticker'] == ticker].copy()
                    
                    if len(ticker_data) > 5:
                        # Médias móveis
                        ticker_data['close_ma_20'] = ticker_data['close'].rolling(window=min(20, len(ticker_data))).mean()
                        ticker_data['close_ma_50'] = ticker_data['close'].rolling(window=min(50, len(ticker_data))).mean()
                        ticker_data['volume_ma_10'] = ticker_data['volume'].rolling(window=min(10, len(ticker_data))).mean()
                        
                        # RSI
                        delta = ticker_data['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(ticker_data))).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(ticker_data))).mean()
                        rs = gain / loss
                        ticker_data['rsi'] = 100 - (100 / (1 + rs))
                        
                        # MACD
                        exp1 = ticker_data['close'].ewm(span=12).mean()
                        exp2 = ticker_data['close'].ewm(span=26).mean()
                        ticker_data['macd'] = exp1 - exp2
                        ticker_data['macd_signal'] = ticker_data['macd'].ewm(span=9).mean()
                        
                        # Bandas de Bollinger
                        ticker_data['bb_middle'] = ticker_data['close'].rolling(window=min(20, len(ticker_data))).mean()
                        bb_std = ticker_data['close'].rolling(window=min(20, len(ticker_data))).std()
                        ticker_data['bb_upper'] = ticker_data['bb_middle'] + (bb_std * 2)
                        ticker_data['bb_lower'] = ticker_data['bb_middle'] - (bb_std * 2)
                        
                        indicators_data.append(ticker_data)
                
                # Combinar dados apenas se temos indicadores calculados
                if indicators_data:
                    self.transformed_data = pd.concat(indicators_data, ignore_index=True)
                    self.transformed_data = self.transformed_data.dropna()
                else:
                    # Fallback se não conseguimos calcular indicadores
                    self.transformed_data = self.data.copy()
            
            self._log_message(f"✅ Transformação concluída: {len(self.transformed_data)} registros válidos")
            self._log_message(f"📊 Indicadores calculados para {self.transformed_data['Ticker'].nunique()} tickers")
            
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro na transformação: {str(e)}")
            return False
    
    def _execute_load_postgres(self):
        """Carrega dados no PostgreSQL"""
        try:
            if self.transformed_data is None:
                self._log_message("❌ Nenhum dado transformado para carregar")
                return False
            
            self._log_message("🔄 Carregando dados no PostgreSQL...")
            self._log_message(f"📊 Dados para carregar: {len(self.transformed_data)} registros")
            
            # Simular carregamento no PostgreSQL
            time.sleep(2)
            
            self._log_message("✅ Dados carregados no PostgreSQL com sucesso")
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro no carregamento PostgreSQL: {str(e)}")
            return False
    
    def _execute_load_mongodb(self):
        """Carrega dados no MongoDB"""
        try:
            if self.transformed_data is None:
                self._log_message("❌ Nenhum dado transformado para carregar")
                return False
            
            self._log_message("🔄 Carregando dados no MongoDB...")
            self._log_message(f"📊 Dados para carregar: {len(self.transformed_data)} registros")
            
            # Simular carregamento no MongoDB
            time.sleep(1.5)
            
            self._log_message("✅ Dados carregados no MongoDB com sucesso")
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro no carregamento MongoDB: {str(e)}")
            return False
    
    def _execute_validate_data(self):
        """Valida a qualidade dos dados"""
        try:
            self._log_message("🔄 Validando qualidade dos dados...")
            
            # Simular validações
            time.sleep(1)
            
            # Validações simuladas
            self._log_message("✅ Validação de integridade: OK")
            self._log_message("✅ Validação de completude: OK")
            self._log_message("✅ Validação de consistência: OK")
            self._log_message("✅ Validação de precisão: OK")
            
            self._log_message("✅ Validação de dados concluída com sucesso")
            return True
            
        except Exception as e:
            self._log_message(f"❌ Erro na validação: {str(e)}")
            return False
    
    def _execute_end(self):
        """Tarefa de finalização"""
        time.sleep(0.5)
        self._log_message("🎉 Pipeline finalizado com sucesso!")
        return True


def run_dag_async(dag_run_id):
    """Executa o DAG em uma thread separada"""
    simulator = DAGSimulator(dag_run_id)
    simulator.run_dag() 