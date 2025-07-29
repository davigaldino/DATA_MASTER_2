"""
Modelos Django para dados de ações e indicadores técnicos.

Este módulo define os modelos que representam as tabelas do banco de dados
para armazenar dados de ações e indicadores técnicos calculados.
"""

from django.db import models
from django.utils import timezone


class StockData(models.Model):
    """
    Modelo para dados básicos de ações.
    
    Representa os dados OHLCV (Open, High, Low, Close, Volume) de uma ação
    em uma data específica.
    """
    
    date = models.DateField('Data')
    ticker = models.CharField('Ticker', max_length=10)
    open = models.DecimalField('Preço de Abertura', max_digits=10, decimal_places=4, null=True, blank=True)
    close = models.DecimalField('Preço de Fechamento', max_digits=10, decimal_places=4)
    high = models.DecimalField('Preço Máximo', max_digits=10, decimal_places=4, null=True, blank=True)
    low = models.DecimalField('Preço Mínimo', max_digits=10, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField('Volume', null=True, blank=True)
    created_at = models.DateTimeField('Data de Criação', default=timezone.now)
    updated_at = models.DateTimeField('Data de Atualização', auto_now=True)
    
    class Meta:
        db_table = 'stock_data'
        verbose_name = 'Dado de Ação'
        verbose_name_plural = 'Dados de Ações'
        unique_together = ['date', 'ticker']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['ticker']),
            models.Index(fields=['date', 'ticker']),
        ]
        ordering = ['-date', 'ticker']
    
    def __str__(self):
        return f"{self.ticker} - {self.date.strftime('%Y-%m-%d')} - R$ {self.close}"
    
    @property
    def daily_return(self):
        """Calcula o retorno diário em percentual."""
        if self.open and self.open > 0:
            return ((self.close - self.open) / self.open) * 100
        return None
    
    @property
    def price_change(self):
        """Calcula a variação absoluta do preço."""
        if self.open:
            return self.close - self.open
        return None


class TechnicalIndicators(models.Model):
    """
    Modelo para indicadores técnicos calculados.
    
    Armazena todos os indicadores técnicos calculados para uma ação
    em uma data específica.
    """
    
    date = models.DateField('Data')
    ticker = models.CharField('Ticker', max_length=10)
    
    # Retornos
    daily_return = models.DecimalField('Retorno Diário', max_digits=10, decimal_places=6, null=True, blank=True)
    log_return = models.DecimalField('Retorno Log', max_digits=10, decimal_places=6, null=True, blank=True)
    cumulative_return = models.DecimalField('Retorno Acumulado', max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Médias móveis
    sma_5 = models.DecimalField('SMA 5', max_digits=10, decimal_places=4, null=True, blank=True)
    sma_10 = models.DecimalField('SMA 10', max_digits=10, decimal_places=4, null=True, blank=True)
    sma_20 = models.DecimalField('SMA 20', max_digits=10, decimal_places=4, null=True, blank=True)
    sma_50 = models.DecimalField('SMA 50', max_digits=10, decimal_places=4, null=True, blank=True)
    sma_200 = models.DecimalField('SMA 200', max_digits=10, decimal_places=4, null=True, blank=True)
    
    ema_5 = models.DecimalField('EMA 5', max_digits=10, decimal_places=4, null=True, blank=True)
    ema_10 = models.DecimalField('EMA 10', max_digits=10, decimal_places=4, null=True, blank=True)
    ema_20 = models.DecimalField('EMA 20', max_digits=10, decimal_places=4, null=True, blank=True)
    ema_50 = models.DecimalField('EMA 50', max_digits=10, decimal_places=4, null=True, blank=True)
    ema_200 = models.DecimalField('EMA 200', max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Volatilidade
    true_range = models.DecimalField('True Range', max_digits=10, decimal_places=4, null=True, blank=True)
    atr_14 = models.DecimalField('ATR 14', max_digits=10, decimal_places=4, null=True, blank=True)
    volatility_20 = models.DecimalField('Volatilidade 20', max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Bollinger Bands
    bb_upper = models.DecimalField('BB Superior', max_digits=10, decimal_places=4, null=True, blank=True)
    bb_middle = models.DecimalField('BB Média', max_digits=10, decimal_places=4, null=True, blank=True)
    bb_lower = models.DecimalField('BB Inferior', max_digits=10, decimal_places=4, null=True, blank=True)
    bb_width = models.DecimalField('BB Largura', max_digits=10, decimal_places=4, null=True, blank=True)
    bb_position = models.DecimalField('BB Posição', max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Momentum
    rsi_14 = models.DecimalField('RSI 14', max_digits=10, decimal_places=4, null=True, blank=True)
    macd = models.DecimalField('MACD', max_digits=10, decimal_places=4, null=True, blank=True)
    macd_signal = models.DecimalField('MACD Sinal', max_digits=10, decimal_places=4, null=True, blank=True)
    macd_histogram = models.DecimalField('MACD Histograma', max_digits=10, decimal_places=4, null=True, blank=True)
    stochastic_k = models.DecimalField('Estocástico K', max_digits=10, decimal_places=4, null=True, blank=True)
    stochastic_d = models.DecimalField('Estocástico D', max_digits=10, decimal_places=4, null=True, blank=True)
    williams_r = models.DecimalField('Williams %R', max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Volume
    obv = models.BigIntegerField('OBV', null=True, blank=True)
    vpt = models.DecimalField('VPT', max_digits=20, decimal_places=4, null=True, blank=True)
    mfi_14 = models.DecimalField('MFI 14', max_digits=10, decimal_places=4, null=True, blank=True)
    
    created_at = models.DateTimeField('Data de Criação', default=timezone.now)
    updated_at = models.DateTimeField('Data de Atualização', auto_now=True)
    
    class Meta:
        db_table = 'technical_indicators'
        verbose_name = 'Indicador Técnico'
        verbose_name_plural = 'Indicadores Técnicos'
        unique_together = ['date', 'ticker']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['ticker']),
            models.Index(fields=['date', 'ticker']),
        ]
        ordering = ['-date', 'ticker']
    
    def __str__(self):
        return f"{self.ticker} - {self.date.strftime('%Y-%m-%d')} - RSI: {self.rsi_14}"
    
    @property
    def rsi_signal(self):
        """Retorna o sinal do RSI."""
        if self.rsi_14 is None:
            return 'Neutro'
        elif self.rsi_14 > 70:
            return 'Sobrecomprado'
        elif self.rsi_14 < 30:
            return 'Sobrevendido'
        else:
            return 'Neutro'
    
    @property
    def macd_signal_type(self):
        """Retorna o tipo de sinal do MACD."""
        if self.macd is None or self.macd_signal is None:
            return 'Neutro'
        elif self.macd > self.macd_signal:
            return 'Compra'
        elif self.macd < self.macd_signal:
            return 'Venda'
        else:
            return 'Neutro'
    
    @property
    def bb_signal(self):
        """Retorna o sinal das Bandas de Bollinger."""
        if self.bb_upper is None or self.bb_lower is None:
            return 'Neutro'
        # Aqui você precisaria do preço atual para determinar o sinal
        # Por enquanto, retorna neutro
        return 'Neutro'


class DataMetadata(models.Model):
    """
    Modelo para metadados das tabelas de dados.
    
    Armazena informações sobre as tabelas de dados, incluindo
    última atualização, número de registros, etc.
    """
    
    table_name = models.CharField('Nome da Tabela', max_length=50, unique=True)
    last_update = models.DateTimeField('Última Atualização')
    record_count = models.IntegerField('Número de Registros')
    date_range_start = models.DateTimeField('Início do Período', null=True, blank=True)
    date_range_end = models.DateTimeField('Fim do Período', null=True, blank=True)
    tickers = models.JSONField('Tickers', default=list)
    created_at = models.DateTimeField('Data de Criação', default=timezone.now)
    
    class Meta:
        db_table = 'data_metadata'
        verbose_name = 'Metadado'
        verbose_name_plural = 'Metadados'
        ordering = ['-last_update']
    
    def __str__(self):
        return f"{self.table_name} - {self.last_update.strftime('%Y-%m-%d %H:%M')} - {self.record_count} registros" 