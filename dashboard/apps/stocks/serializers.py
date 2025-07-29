"""
Serializers Django REST Framework para dados de ações.

Este módulo define os serializers que convertem os modelos Django
em JSON e vice-versa para a API REST.
"""

from rest_framework import serializers
from .models import StockData, TechnicalIndicators, DataMetadata


class StockDataSerializer(serializers.ModelSerializer):
    """
    Serializer para dados básicos de ações.
    """
    
    daily_return = serializers.ReadOnlyField()
    price_change = serializers.ReadOnlyField()
    formatted_close = serializers.SerializerMethodField()
    formatted_open = serializers.SerializerMethodField()
    formatted_high = serializers.SerializerMethodField()
    formatted_low = serializers.SerializerMethodField()
    
    class Meta:
        model = StockData
        fields = [
            'id', 'date', 'ticker', 'open', 'close', 'high', 'low', 'volume',
            'daily_return', 'price_change', 'formatted_close', 'formatted_open',
            'formatted_high', 'formatted_low', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_formatted_close(self, obj):
        """Formata o preço de fechamento em reais."""
        if obj.close:
            return f"R$ {obj.close:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return None
    
    def get_formatted_open(self, obj):
        """Formata o preço de abertura em reais."""
        if obj.open:
            return f"R$ {obj.open:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return None
    
    def get_formatted_high(self, obj):
        """Formata o preço máximo em reais."""
        if obj.high:
            return f"R$ {obj.high:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return None
    
    def get_formatted_low(self, obj):
        """Formata o preço mínimo em reais."""
        if obj.low:
            return f"R$ {obj.low:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return None


class TechnicalIndicatorsSerializer(serializers.ModelSerializer):
    """
    Serializer para indicadores técnicos.
    """
    
    rsi_signal = serializers.ReadOnlyField()
    macd_signal_type = serializers.ReadOnlyField()
    bb_signal = serializers.ReadOnlyField()
    
    class Meta:
        model = TechnicalIndicators
        fields = [
            'id', 'date', 'ticker',
            'daily_return', 'log_return', 'cumulative_return',
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            'true_range', 'atr_14', 'volatility_20',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'stochastic_k', 'stochastic_d', 'williams_r',
            'obv', 'vpt', 'mfi_14',
            'rsi_signal', 'macd_signal_type', 'bb_signal',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockDataWithIndicatorsSerializer(serializers.ModelSerializer):
    """
    Serializer que combina dados de ações com indicadores técnicos.
    """
    
    indicators = serializers.SerializerMethodField()
    daily_return = serializers.ReadOnlyField()
    price_change = serializers.ReadOnlyField()
    formatted_close = serializers.SerializerMethodField()
    
    class Meta:
        model = StockData
        fields = [
            'id', 'date', 'ticker', 'open', 'close', 'high', 'low', 'volume',
            'daily_return', 'price_change', 'formatted_close',
            'indicators', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_indicators(self, obj):
        """Busca indicadores técnicos para a mesma data e ticker."""
        from .models import TechnicalIndicators
        
        try:
            indicators = TechnicalIndicators.objects.filter(
                date=obj.date,
                ticker=obj.ticker
            )
            if indicators.exists():
                return TechnicalIndicatorsSerializer(indicators.first()).data
            return None
        except Exception:
            return None
    
    def get_formatted_close(self, obj):
        """Formata o preço de fechamento em reais."""
        if obj.close:
            return f"R$ {obj.close:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return None


class DataMetadataSerializer(serializers.ModelSerializer):
    """
    Serializer para metadados das tabelas.
    """
    
    class Meta:
        model = DataMetadata
        fields = [
            'id', 'table_name', 'last_update', 'record_count',
            'date_range_start', 'date_range_end', 'tickers', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StockSummarySerializer(serializers.Serializer):
    """
    Serializer para resumo de dados de ações.
    """
    
    ticker = serializers.CharField()
    total_records = serializers.IntegerField()
    date_range_start = serializers.DateField()
    date_range_end = serializers.DateField()
    current_price = serializers.DecimalField(max_digits=10, decimal_places=4)
    price_change_1d = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    price_change_1w = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    price_change_1m = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    price_change_1y = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    current_rsi = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    current_macd = serializers.DecimalField(max_digits=10, decimal_places=6, allow_null=True)
    volatility_20d = serializers.DecimalField(max_digits=10, decimal_places=6, allow_null=True)
    formatted_current_price = serializers.SerializerMethodField()
    
    def get_formatted_current_price(self, obj):
        """Formata o preço atual em reais."""
        if obj.get('current_price'):
            return f"R$ {obj['current_price']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


class ChartDataSerializer(serializers.ModelSerializer):
    """
    Serializer para dados de gráficos.
    """
    
    class Meta:
        model = StockData
        fields = [
            'date', 'ticker', 'open', 'close', 'high', 'low', 'volume'
        ]


class FilterOptionsSerializer(serializers.Serializer):
    """
    Serializer para opções de filtro disponíveis.
    """
    
    tickers = serializers.ListField(child=serializers.CharField())
    date_range_start = serializers.DateField()
    date_range_end = serializers.DateField()
    indicators = serializers.ListField(child=serializers.CharField()) 