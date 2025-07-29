#!/usr/bin/env python3
"""
Script principal para executar o pipeline ETL completo.

Este script orquestra todo o processo de:
1. Extração de dados (CSV + Yahoo Finance)
2. Transformação e limpeza
3. Cálculo de indicadores técnicos
4. Carregamento no PostgreSQL
"""

import sys
import os
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from etl.extractors import CSVExtractor, YFinanceExtractor
from etl.transformers import DataCleaner, TechnicalIndicators
from etl.loaders import PostgresLoader
import structlog

# Configura logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ETLPipeline:
    """
    Classe principal para orquestrar o pipeline ETL.
    
    Esta classe coordena todas as etapas do processo ETL:
    - Extração de dados de múltiplas fontes
    - Transformação e enriquecimento
    - Carregamento no banco de dados
    """
    
    def __init__(self, config: dict = None):
        """
        Inicializa o pipeline ETL.
        
        Args:
            config (dict): Configurações do pipeline
        """
        self.config = config or {}
        self.csv_extractor = CSVExtractor()
        self.yfinance_extractor = YFinanceExtractor()
        self.data_cleaner = DataCleaner()
        self.technical_indicators = TechnicalIndicators()
        self.postgres_loader = PostgresLoader()
        
        # Estatísticas do pipeline
        self.stats = {
            'start_time': None,
            'end_time': None,
            'extraction_stats': {},
            'transformation_stats': {},
            'loading_stats': {},
            'errors': []
        }
    
    def run(self, 
            tickers: list = None, 
            start_date: str = None, 
            end_date: str = None,
            include_yfinance: bool = True,
            calculate_indicators: bool = True) -> dict:
        """
        Executa o pipeline ETL completo.
        
        Args:
            tickers (list): Lista de tickers para processar
            start_date (str): Data de início (YYYY-MM-DD)
            end_date (str): Data de fim (YYYY-MM-DD)
            include_yfinance (bool): Se deve incluir dados do Yahoo Finance
            calculate_indicators (bool): Se deve calcular indicadores técnicos
            
        Returns:
            dict: Estatísticas do pipeline
        """
        try:
            self.stats['start_time'] = datetime.now()
            logger.info("Iniciando pipeline ETL", 
                       tickers=tickers, 
                       start_date=start_date, 
                       end_date=end_date)
            
            # Etapa 1: Extração
            raw_data = self._extract_data(tickers, start_date, end_date, include_yfinance)
            
            # Etapa 2: Transformação
            cleaned_data = self._transform_data(raw_data)
            
            # Etapa 3: Cálculo de indicadores (opcional)
            if calculate_indicators:
                enriched_data = self._calculate_indicators(cleaned_data)
            else:
                enriched_data = cleaned_data
            
            # Etapa 4: Carregamento
            self._load_data(cleaned_data, enriched_data)
            
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            logger.info("Pipeline ETL concluído com sucesso", 
                       duration_seconds=duration.total_seconds(),
                       stats=self.stats)
            
            return self.stats
            
        except Exception as e:
            self.stats['errors'].append(str(e))
            logger.error("Erro durante execução do pipeline ETL", error=str(e))
            raise
    
    def _extract_data(self, tickers: list, start_date: str, end_date: str, include_yfinance: bool) -> dict:
        """
        Executa a etapa de extração de dados.
        
        Args:
            tickers (list): Lista de tickers
            start_date (str): Data de início
            end_date (str): Data de fim
            include_yfinance (bool): Se deve incluir Yahoo Finance
            
        Returns:
            dict: Dados extraídos de todas as fontes
        """
        logger.info("Iniciando etapa de extração")
        
        extracted_data = {}
        
        # Extração de dados CSV
        try:
            csv_data = self.csv_extractor.extract(tickers, start_date, end_date)
            extracted_data['csv'] = csv_data
            self.stats['extraction_stats']['csv'] = {
                'rows': len(csv_data),
                'tickers': csv_data['ticker'].nunique() if not csv_data.empty else 0,
                'date_range': {
                    'start': csv_data['datetime'].min() if not csv_data.empty else None,
                    'end': csv_data['datetime'].max() if not csv_data.empty else None
                }
            }
            logger.info("Extração CSV concluída", stats=self.stats['extraction_stats']['csv'])
            
        except Exception as e:
            logger.error("Erro na extração CSV", error=str(e))
            self.stats['errors'].append(f"Erro CSV: {str(e)}")
            extracted_data['csv'] = None
        
        # Extração de dados Yahoo Finance (opcional)
        if include_yfinance and tickers:
            try:
                yf_data = self.yfinance_extractor.extract_historical_data(
                    tickers, start_date, end_date
                )
                extracted_data['yfinance'] = yf_data
                self.stats['extraction_stats']['yfinance'] = {
                    'rows': len(yf_data),
                    'tickers': yf_data['ticker'].nunique() if not yf_data.empty else 0,
                    'date_range': {
                        'start': yf_data['datetime'].min() if not yf_data.empty else None,
                        'end': yf_data['datetime'].max() if not yf_data.empty else None
                    }
                }
                logger.info("Extração Yahoo Finance concluída", 
                           stats=self.stats['extraction_stats']['yfinance'])
                
            except Exception as e:
                logger.error("Erro na extração Yahoo Finance", error=str(e))
                self.stats['errors'].append(f"Erro Yahoo Finance: {str(e)}")
                extracted_data['yfinance'] = None
        
        return extracted_data
    
    def _transform_data(self, extracted_data: dict) -> dict:
        """
        Executa a etapa de transformação e limpeza.
        
        Args:
            extracted_data (dict): Dados extraídos
            
        Returns:
            dict: Dados transformados
        """
        logger.info("Iniciando etapa de transformação")
        
        transformed_data = {}
        
        # Combina dados de diferentes fontes
        all_data = []
        
        if extracted_data.get('csv') is not None and not extracted_data['csv'].empty:
            all_data.append(extracted_data['csv'])
        
        if extracted_data.get('yfinance') is not None and not extracted_data['yfinance'].empty:
            all_data.append(extracted_data['yfinance'])
        
        if not all_data:
            logger.warning("Nenhum dado extraído para transformar")
            return {}
        
        # Combina todos os dados
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicatas baseadas em datetime e ticker
        combined_data = combined_data.drop_duplicates(subset=['datetime', 'ticker'], keep='last')
        
        # Aplica limpeza
        cleaned_data = self.data_cleaner.clean_data(combined_data)
        
        transformed_data['cleaned'] = cleaned_data
        
        self.stats['transformation_stats'] = {
            'original_rows': len(combined_data),
            'cleaned_rows': len(cleaned_data),
            'removed_rows': len(combined_data) - len(cleaned_data),
            'tickers': cleaned_data['ticker'].nunique() if not cleaned_data.empty else 0,
            'date_range': {
                'start': cleaned_data['datetime'].min() if not cleaned_data.empty else None,
                'end': cleaned_data['datetime'].max() if not cleaned_data.empty else None
            }
        }
        
        logger.info("Transformação concluída", stats=self.stats['transformation_stats'])
        
        return transformed_data
    
    def _calculate_indicators(self, transformed_data: dict) -> dict:
        """
        Calcula indicadores técnicos.
        
        Args:
            transformed_data (dict): Dados transformados
            
        Returns:
            dict: Dados com indicadores calculados
        """
        logger.info("Iniciando cálculo de indicadores técnicos")
        
        if 'cleaned' not in transformed_data or transformed_data['cleaned'].empty:
            logger.warning("Nenhum dado limpo para calcular indicadores")
            return transformed_data
        
        cleaned_data = transformed_data['cleaned']
        
        # Calcula indicadores técnicos
        enriched_data = self.technical_indicators.calculate_all_indicators(cleaned_data)
        
        transformed_data['enriched'] = enriched_data
        
        # Atualiza estatísticas
        indicators_summary = self.technical_indicators.get_indicators_summary(enriched_data)
        self.stats['transformation_stats']['indicators'] = indicators_summary
        
        logger.info("Cálculo de indicadores concluído", indicators_summary=indicators_summary)
        
        return transformed_data
    
    def _load_data(self, cleaned_data: dict, enriched_data: dict):
        """
        Executa a etapa de carregamento no banco de dados.
        
        Args:
            cleaned_data (dict): Dados limpos
            enriched_data (dict): Dados enriquecidos
        """
        logger.info("Iniciando etapa de carregamento")
        
        # Testa conexão com banco
        if not self.postgres_loader.test_connection():
            raise Exception("Falha na conexão com banco de dados")
        
        # Carrega dados limpos
        if 'cleaned' in cleaned_data and not cleaned_data['cleaned'].empty:
            try:
                load_result = self.postgres_loader.load_stock_data(cleaned_data['cleaned'])
                self.stats['loading_stats']['stock_data'] = load_result
                logger.info("Dados de ações carregados", result=load_result)
                
            except Exception as e:
                logger.error("Erro ao carregar dados de ações", error=str(e))
                self.stats['errors'].append(f"Erro carregamento ações: {str(e)}")
        
        # Carrega indicadores técnicos
        if 'enriched' in enriched_data and not enriched_data['enriched'].empty:
            try:
                indicators_result = self.postgres_loader.load_technical_indicators(enriched_data['enriched'])
                self.stats['loading_stats']['technical_indicators'] = indicators_result
                logger.info("Indicadores técnicos carregados", result=indicators_result)
                
            except Exception as e:
                logger.error("Erro ao carregar indicadores técnicos", error=str(e))
                self.stats['errors'].append(f"Erro carregamento indicadores: {str(e)}")
        
        logger.info("Carregamento concluído", stats=self.stats['loading_stats'])


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description='Pipeline ETL para dados de ações B3')
    
    parser.add_argument('--tickers', nargs='+', help='Lista de tickers para processar')
    parser.add_argument('--start-date', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Data de fim (YYYY-MM-DD)')
    parser.add_argument('--no-yfinance', action='store_true', help='Não incluir dados do Yahoo Finance')
    parser.add_argument('--no-indicators', action='store_true', help='Não calcular indicadores técnicos')
    parser.add_argument('--config', help='Arquivo de configuração JSON')
    
    args = parser.parse_args()
    
    # Configurações padrão
    config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Valores padrão se não especificados
    if not args.tickers:
        args.tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3']
    
    if not args.start_date:
        args.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Executa pipeline
    pipeline = ETLPipeline(config)
    
    try:
        stats = pipeline.run(
            tickers=args.tickers,
            start_date=args.start_date,
            end_date=args.end_date,
            include_yfinance=not args.no_yfinance,
            calculate_indicators=not args.no_indicators
        )
        
        print("Pipeline ETL executado com sucesso!")
        print(f"Duração: {stats['end_time'] - stats['start_time']}")
        print(f"Erros: {len(stats['errors'])}")
        
        if stats['errors']:
            print("Erros encontrados:")
            for error in stats['errors']:
                print(f"  - {error}")
        
    except Exception as e:
        print(f"Erro durante execução do pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 