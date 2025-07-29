"""
Views Django REST Framework para API de dados de ações.

Este módulo define as views que fornecem endpoints da API REST
para acessar dados de ações e indicadores técnicos.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # Comentado temporariamente
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Max, Min, Avg
from django.utils import timezone
from datetime import timedelta
import logging

from .models import StockData, TechnicalIndicators, DataMetadata
from .serializers import (
    StockDataSerializer, TechnicalIndicatorsSerializer, 
    StockDataWithIndicatorsSerializer, DataMetadataSerializer,
    StockSummarySerializer, ChartDataSerializer, FilterOptionsSerializer
)

logger = logging.getLogger(__name__)


class StockDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para dados básicos de ações.
    
    Fornece endpoints para listar e detalhar dados de ações,
    com filtros por ticker, data e outros parâmetros.
    """
    
    queryset = StockData.objects.all()
    serializer_class = StockDataSerializer
    permission_classes = []  # Removido temporariamente para dashboard funcionar
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ticker', 'date']
    search_fields = ['ticker']
    ordering_fields = ['date', 'close', 'volume']
    ordering = ['-date']
    
    def get_queryset(self):
        """Personaliza o queryset com filtros adicionais."""
        queryset = super().get_queryset()
        
        # Filtro por período
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filtro por múltiplos tickers
        tickers = self.request.query_params.getlist('tickers')
        if tickers:
            queryset = queryset.filter(ticker__in=tickers)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Retorna resumo dos dados de ações."""
        try:
            ticker = request.query_params.get('ticker')
            if not ticker:
                return Response(
                    {'error': 'Parâmetro ticker é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtém dados da ação
            stock_data = StockData.objects.filter(ticker=ticker).order_by('-date')
            if not stock_data.exists():
                return Response(
                    {'error': f'Nenhum dado encontrado para o ticker {ticker}'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            latest = stock_data.first()
            earliest = stock_data.last()
            
            # Calcula variações de preço
            now = timezone.now()
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(days=7)
            one_month_ago = now - timedelta(days=30)
            one_year_ago = now - timedelta(days=365)
            
            price_1d = stock_data.filter(date__gte=one_day_ago.date()).first()
            price_1w = stock_data.filter(date__gte=one_week_ago.date()).first()
            price_1m = stock_data.filter(date__gte=one_month_ago.date()).first()
            price_1y = stock_data.filter(date__gte=one_year_ago.date()).first()
            
            # Obtém indicadores técnicos mais recentes
            latest_indicators = TechnicalIndicators.objects.filter(
                ticker=ticker
            ).order_by('-date').first()
            
            # Calcula estatísticas
            stats = stock_data.aggregate(
                max_price=Max('close'),
                min_price=Min('close'),
                avg_price=Avg('close'),
                max_volume=Max('volume'),
                avg_volume=Avg('volume')
            )
            
            # Prepara dados de resposta
            summary_data = {
                'ticker': ticker,
                'latest_price': float(latest.close),
                'latest_date': latest.date.strftime('%Y-%m-%d'),
                'price_change_1d': float(latest.close - price_1d.close) if price_1d else None,
                'price_change_1w': float(latest.close - price_1w.close) if price_1w else None,
                'price_change_1m': float(latest.close - price_1m.close) if price_1m else None,
                'price_change_1y': float(latest.close - price_1y.close) if price_1y else None,
                'max_price': float(stats['max_price']) if stats['max_price'] else None,
                'min_price': float(stats['min_price']) if stats['min_price'] else None,
                'avg_price': float(stats['avg_price']) if stats['avg_price'] else None,
                'max_volume': int(stats['max_volume']) if stats['max_volume'] else None,
                'avg_volume': int(stats['avg_volume']) if stats['avg_volume'] else None,
                'indicators': {
                    'rsi_14': float(latest_indicators.rsi_14) if latest_indicators and latest_indicators.rsi_14 else None,
                    'macd': float(latest_indicators.macd) if latest_indicators and latest_indicators.macd else None,
                    'volatility_20d': float(latest_indicators.volatility_20d) if latest_indicators and latest_indicators.volatility_20d else None,
                } if latest_indicators else None
            }
            
            return Response(summary_data)
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo para {ticker}: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def chart_data(self, request):
        """Retorna dados formatados para gráficos."""
        try:
            ticker = request.query_params.get('ticker')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not ticker:
                return Response(
                    {'error': 'Parâmetro ticker é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Filtra dados
            queryset = StockData.objects.filter(ticker=ticker)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            # Ordena por data
            queryset = queryset.order_by('date')
            
            # Serializa dados
            serializer = ChartDataSerializer(queryset, many=True)
            
            return Response({
                'ticker': ticker,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados de gráfico para {ticker}: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def with_indicators(self, request):
        """Retorna dados de ações com indicadores técnicos incluídos."""
        try:
            ticker = request.query_params.get('ticker')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not ticker:
                return Response(
                    {'error': 'Parâmetro ticker é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Filtra dados
            queryset = StockData.objects.filter(ticker=ticker)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            # Ordena por data
            queryset = queryset.order_by('date')
            
            # Serializa dados com indicadores
            serializer = StockDataWithIndicatorsSerializer(queryset, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados com indicadores para {ticker}: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TechnicalIndicatorsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para indicadores técnicos.
    
    Fornece endpoints para acessar indicadores técnicos calculados,
    com filtros e análises específicas.
    """
    
    queryset = TechnicalIndicators.objects.all()
    serializer_class = TechnicalIndicatorsSerializer
    permission_classes = []  # Removido temporariamente para dashboard funcionar
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ticker', 'date']
    search_fields = ['ticker']
    ordering_fields = ['date', 'rsi_14', 'macd', 'volatility_20d']
    ordering = ['-date']
    
    def get_queryset(self):
        """Personaliza o queryset com filtros adicionais."""
        queryset = super().get_queryset()
        
        # Filtro por período
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filtro por múltiplos tickers
        tickers = self.request.query_params.getlist('tickers')
        if tickers:
            queryset = queryset.filter(ticker__in=tickers)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def signals(self, request):
        """Retorna sinais de compra/venda baseados nos indicadores."""
        try:
            ticker = request.query_params.get('ticker')
            if not ticker:
                return Response(
                    {'error': 'Parâmetro ticker é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtém indicadores mais recentes
            indicators = TechnicalIndicators.objects.filter(
                ticker=ticker
            ).order_by('-date')[:30]  # Últimos 30 dias
            
            if not indicators.exists():
                return Response(
                    {'error': f'Nenhum indicador encontrado para o ticker {ticker}'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calcula sinais
            signals = []
            for indicator in indicators:
                signal = self._calculate_overall_signal(indicator)
                signals.append({
                    'date': indicator.date.strftime('%Y-%m-%d'),
                    'rsi_signal': indicator.rsi_signal,
                    'macd_signal': indicator.macd_signal_type,
                    'bb_signal': indicator.bb_signal,
                    'overall_signal': signal,
                    'rsi_14': float(indicator.rsi_14) if indicator.rsi_14 else None,
                    'macd': float(indicator.macd) if indicator.macd else None,
                    'macd_signal': float(indicator.macd_signal) if indicator.macd_signal else None,
                })
            
            return Response({
                'ticker': ticker,
                'signals': signals
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais para {ticker}: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_overall_signal(self, indicator):
        """Calcula sinal geral baseado em múltiplos indicadores."""
        signals = []
        
        # RSI
        if indicator.rsi_14:
            if indicator.rsi_14 > 70:
                signals.append('Venda')
            elif indicator.rsi_14 < 30:
                signals.append('Compra')
            else:
                signals.append('Neutro')
        
        # MACD
        if indicator.macd and indicator.macd_signal:
            if indicator.macd > indicator.macd_signal:
                signals.append('Compra')
            else:
                signals.append('Venda')
        
        # Se não há sinais, retorna neutro
        if not signals:
            return 'Neutro'
        
        # Conta sinais
        buy_signals = signals.count('Compra')
        sell_signals = signals.count('Venda')
        
        if buy_signals > sell_signals:
            return 'Compra'
        elif sell_signals > buy_signals:
            return 'Venda'
        else:
            return 'Neutro'


class DataMetadataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para metadados das tabelas.
    
    Fornece informações sobre o estado dos dados no sistema.
    """
    
    queryset = DataMetadata.objects.all()
    serializer_class = DataMetadataSerializer
    permission_classes = []  # Removido temporariamente para dashboard funcionar
    
    @action(detail=False, methods=['get'])
    def system_status(self, request):
        """Retorna status geral do sistema."""
        try:
            # Conta registros
            stock_count = StockData.objects.count()
            indicators_count = TechnicalIndicators.objects.count()
            
            # Última atualização
            latest_stock = StockData.objects.order_by('-date').first()
            latest_indicator = TechnicalIndicators.objects.order_by('-date').first()
            
            # Tickers disponíveis
            tickers = StockData.objects.values_list('ticker', flat=True).distinct()
            
            # Período de dados
            date_range = StockData.objects.aggregate(
                min_date=Min('date'),
                max_date=Max('date')
            )
            
            status_data = {
                'stock_data': {
                    'count': stock_count,
                    'last_update': latest_stock.date.strftime('%Y-%m-%d') if latest_stock else None,
                    'tickers': list(tickers),
                    'date_range': {
                        'start': date_range['min_date'].strftime('%Y-%m-%d') if date_range['min_date'] else None,
                        'end': date_range['max_date'].strftime('%Y-%m-%d') if date_range['max_date'] else None,
                    }
                },
                'technical_indicators': {
                    'count': indicators_count,
                    'last_update': latest_indicator.date.strftime('%Y-%m-%d') if latest_indicator else None,
                },
                'system': {
                    'status': 'operational',
                    'timestamp': timezone.now().isoformat()
                }
            }
            
            return Response(status_data)
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FilterOptionsViewSet(viewsets.ViewSet):
    """
    ViewSet para opções de filtro disponíveis.
    """
    
    permission_classes = []  # Removido temporariamente para dashboard funcionar
    
    @action(detail=False, methods=['get'])
    def available_options(self, request):
        """Retorna opções disponíveis para filtros."""
        try:
            # Tickers disponíveis
            tickers = StockData.objects.values_list('ticker', flat=True).distinct().order_by('ticker')
            
            # Período de dados
            date_range = StockData.objects.aggregate(
                min_date=Min('date'),
                max_date=Max('date')
            )
            
            options = {
                'tickers': list(tickers),
                'date_range': {
                    'start': date_range['min_date'].strftime('%Y-%m-%d') if date_range['min_date'] else None,
                    'end': date_range['max_date'].strftime('%Y-%m-%d') if date_range['max_date'] else None,
                },
                'indicators': [
                    'rsi_14', 'rsi_21', 'macd', 'macd_signal', 'macd_histogram',
                    'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_100', 'sma_200',
                    'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
                    'volatility_5d', 'volatility_10d', 'volatility_20d', 'volatility_30d',
                    'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
                    'stoch_k', 'stoch_d', 'williams_r', 'obv', 'vpt', 'mfi'
                ]
            }
            
            return Response(options)
            
        except Exception as e:
            logger.error(f"Erro ao obter opções de filtro: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 