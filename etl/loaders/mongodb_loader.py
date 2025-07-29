"""
MongoDB Loader - Armazena dados de streaming em tempo real
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import structlog
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = structlog.get_logger()

class MongoDBLoader:
    """
    Loader para MongoDB - Otimizado para dados de streaming em tempo real.
    """
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 database_name: str = "b3_streaming", collection_name: str = "stock_data"):
        """
        Inicializa o loader MongoDB.
        
        Args:
            connection_string: String de conexão MongoDB
            database_name: Nome do banco de dados
            collection_name: Nome da coleção
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """
        Estabelece conexão com MongoDB.
        """
        try:
            logger.info("Conectando ao MongoDB", 
                       connection_string=self.connection_string,
                       database=self.database_name,
                       collection=self.collection_name)
            
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Testa conexão
            self.client.admin.command('ping')
            
            logger.info("Conexão MongoDB estabelecida com sucesso")
            
        except PyMongoError as e:
            logger.error("Erro ao conectar ao MongoDB", error=str(e))
            raise
    
    def disconnect(self):
        """
        Fecha conexão com MongoDB.
        """
        if self.client:
            self.client.close()
            logger.info("Conexão MongoDB fechada")
    
    def create_indexes(self):
        """
        Cria índices para otimizar consultas de streaming.
        """
        try:
            # Índice composto para consultas por ticker e data
            self.collection.create_index([
                ("ticker", 1),
                ("date", -1)
            ])
            
            # Índice para timestamp de inserção
            self.collection.create_index([
                ("inserted_at", -1)
            ])
            
            # Índice para consultas por período
            self.collection.create_index([
                ("date", -1),
                ("ticker", 1)
            ])
            
            logger.info("Índices MongoDB criados com sucesso")
            
        except PyMongoError as e:
            logger.error("Erro ao criar índices MongoDB", error=str(e))
            raise
    
    def load_streaming_batch(self, batch_data: Dict[str, Any]) -> bool:
        """
        Carrega um lote de dados de streaming.
        
        Args:
            batch_data: Dicionário com dados do lote
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if not self.collection:
                self.connect()
            
            # Prepara documentos para inserção
            documents = []
            timestamp = datetime.now()
            
            for record in batch_data['data']:
                document = {
                    'ticker': record['ticker'],
                    'date': record['date'],
                    'open': record['open'],
                    'high': record['high'],
                    'low': record['low'],
                    'close': record['close'],
                    'volume': record['volume'],
                    'streaming_batch': batch_data['batch_number'],
                    'streaming_timestamp': batch_data['timestamp'],
                    'inserted_at': timestamp
                }
                documents.append(document)
            
            # Insere documentos
            result = self.collection.insert_many(documents)
            
            logger.info("Lote de streaming carregado no MongoDB", 
                       batch_number=batch_data['batch_number'],
                       records_inserted=len(result.inserted_ids))
            
            return True
            
        except PyMongoError as e:
            logger.error("Erro ao carregar lote de streaming no MongoDB", 
                        error=str(e),
                        batch_number=batch_data.get('batch_number', 'unknown'))
            return False
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos dados de streaming.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            if not self.collection:
                return {'status': 'not_connected'}
            
            total_records = self.collection.count_documents({})
            unique_tickers = len(self.collection.distinct('ticker'))
            
            # Última atualização
            latest_record = self.collection.find_one(
                sort=[('inserted_at', -1)]
            )
            
            stats = {
                'status': 'connected',
                'total_records': total_records,
                'unique_tickers': unique_tickers,
                'last_update': latest_record['inserted_at'].isoformat() if latest_record else None
            }
            
            return stats
            
        except PyMongoError as e:
            logger.error("Erro ao obter estatísticas MongoDB", error=str(e))
            return {'status': 'error', 'error': str(e)}
    
    def get_recent_data(self, ticker: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retorna dados recentes de streaming.
        
        Args:
            ticker: Ticker específico (opcional)
            limit: Limite de registros
            
        Returns:
            Lista de documentos
        """
        try:
            if not self.collection:
                return []
            
            query = {}
            if ticker:
                query['ticker'] = ticker
            
            cursor = self.collection.find(query).sort('inserted_at', -1).limit(limit)
            documents = list(cursor)
            
            # Converte ObjectId para string para serialização
            for doc in documents:
                doc['_id'] = str(doc['_id'])
                if 'inserted_at' in doc:
                    doc['inserted_at'] = doc['inserted_at'].isoformat()
            
            return documents
            
        except PyMongoError as e:
            logger.error("Erro ao obter dados recentes", error=str(e))
            return []
    
    def clear_streaming_data(self) -> bool:
        """
        Limpa todos os dados de streaming.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if not self.collection:
                return False
            
            result = self.collection.delete_many({})
            
            logger.info("Dados de streaming limpos", deleted_count=result.deleted_count)
            
            return True
            
        except PyMongoError as e:
            logger.error("Erro ao limpar dados de streaming", error=str(e))
            return False


def create_mongodb_loader(connection_string: str = None, **kwargs) -> MongoDBLoader:
    """
    Factory function para criar loader MongoDB.
    
    Args:
        connection_string: String de conexão MongoDB
        **kwargs: Argumentos adicionais para MongoDBLoader
        
    Returns:
        Instância de MongoDBLoader
    """
    if connection_string is None:
        connection_string = "mongodb://localhost:27017/"
    
    return MongoDBLoader(connection_string, **kwargs) 