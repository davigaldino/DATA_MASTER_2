"""
Views Django para o dashboard.

Este módulo define as views que servem o dashboard principal
e integram com a aplicação Dash.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request):
    """
    View principal do dashboard.
    
    Renderiza a página principal do dashboard com a aplicação Dash integrada.
    """
    try:
        context = {
            'title': 'AlphaScan - Dashboard',
            'user': request.user,
        }
        return render(request, 'dashboard/home.html', context)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {str(e)}")
        return render(request, 'dashboard/error.html', {'error': str(e)})


@login_required
@csrf_exempt
def dashboard_api(request):
    """
    API do dashboard para comunicação com a aplicação Dash.
    
    Fornece endpoints para obter dados e configurações do dashboard.
    """
    try:
        if request.method == 'GET':
            # Retorna configurações do dashboard
            config = {
                'available_tickers': [
                    'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3',
                    'WEGE3', 'RENT3', 'LREN3', 'MGLU3', 'JBSS3'
                ],
                'default_period': '1y',
                'indicators': [
                    'sma', 'ema', 'bb', 'rsi', 'macd', 'volume'
                ],
                'chart_types': [
                    'candlestick', 'line', 'area', 'bar'
                ]
            }
            return JsonResponse(config)
        
        elif request.method == 'POST':
            # Processa requisições POST
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'get_data':
                # Retorna dados para gráficos
                ticker = data.get('ticker')
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                # Em produção, isso buscaria dados do banco
                # Por enquanto, retorna dados simulados
                period = data.get('period', '1y')  # Default para 1 ano
                response_data = {
                    'success': True,
                    'data': generate_sample_data(ticker, start_date, end_date, period=period)
                }
                return JsonResponse(response_data)
            
            elif action == 'get_indicators':
                # Retorna indicadores técnicos
                ticker = data.get('ticker')
                
                response_data = {
                    'success': True,
                    'indicators': get_technical_indicators(ticker)
                }
                return JsonResponse(response_data)
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Ação não reconhecida'
                }, status=400)
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Método não permitido'
            }, status=405)
            
    except Exception as e:
        logger.error(f"Erro na API do dashboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)


def generate_sample_data(ticker, start_date, end_date, period=None):
    """
    Gera dados de exemplo para demonstração.
    
    Em produção, isso buscaria dados reais do banco de dados.
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Se period for fornecido, calcular datas baseado no período
    if period:
        base_date = datetime(2017, 12, 31)  # Fim de 2017
        
        if period == '1m':
            start_date = base_date - timedelta(days=30)
        elif period == '3m':
            start_date = base_date - timedelta(days=90)
        elif period == '6m':
            start_date = base_date - timedelta(days=180)
        elif period == '1y':
            start_date = base_date - timedelta(days=365)
        elif period == '2y':
            start_date = base_date - timedelta(days=730)
        elif period == '5y':
            start_date = base_date - timedelta(days=1825)
        else:
            start_date = base_date - timedelta(days=365)
        
        end_date = base_date
    
    # Converte strings para datetime
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    print(f"Gerando dados simulados para período: {period} - {start.date()} a {end.date()}")
    
    # Gera datas
    dates = pd.date_range(start=start, end=end, freq='D')
    dates = dates[dates.weekday < 5]  # Remove fins de semana
    
    # Gera preços simulados
    np.random.seed(42)
    n_days = len(dates)
    initial_price = 50.0
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # Gera dados OHLCV
    data = []
    for i, date in enumerate(dates):
        price = prices[i]
        
        # Simula OHLC
        open_price = price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.01)))
        close_price = price
        
        # Volume
        volume = np.random.randint(1000000, 10000000)
        
        # Indicadores técnicos simulados
        sma_20 = np.mean(prices[max(0, i-19):i+1]) if i >= 19 else None
        sma_50 = np.mean(prices[max(0, i-49):i+1]) if i >= 49 else None
        
        # RSI simulado
        rsi = 50 + np.random.normal(0, 15)
        rsi = max(0, min(100, rsi))
        
        # MACD simulado
        macd = np.random.normal(0, 0.5)
        macd_signal = macd + np.random.normal(0, 0.1)
        macd_histogram = macd - macd_signal
        
        # Bollinger Bands simuladas
        if sma_20:
            bb_std = np.std(prices[max(0, i-19):i+1])
            bb_upper = sma_20 + (2 * bb_std)
            bb_middle = sma_20
            bb_lower = sma_20 - (2 * bb_std)
        else:
            bb_upper = bb_middle = bb_lower = None
        
        data.append({
            'datetime': date.isoformat(),
            'ticker': ticker,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume,
            'sma_20': round(sma_20, 2) if sma_20 else None,
            'sma_50': round(sma_50, 2) if sma_50 else None,
            'rsi_14': round(rsi, 2),
            'macd': round(macd, 4),
            'macd_signal': round(macd_signal, 4),
            'macd_histogram': round(macd_histogram, 4),
            'bb_upper': round(bb_upper, 2) if bb_upper else None,
            'bb_middle': round(bb_middle, 2) if bb_middle else None,
            'bb_lower': round(bb_lower, 2) if bb_lower else None,
        })
    
    return data


def get_technical_indicators(ticker):
    """
    Retorna indicadores técnicos para um ticker.
    
    Em produção, isso buscaria dados reais do banco de dados.
    """
    import numpy as np
    
    # Simula indicadores técnicos
    np.random.seed(42)
    
    return {
        'rsi_14': round(50 + np.random.normal(0, 15), 2),
        'rsi_21': round(50 + np.random.normal(0, 15), 2),
        'macd': round(np.random.normal(0, 0.5), 4),
        'macd_signal': round(np.random.normal(0, 0.5), 4),
        'sma_20': round(50 + np.random.normal(0, 5), 2),
        'sma_50': round(50 + np.random.normal(0, 5), 2),
        'volatility_20d': round(np.random.uniform(0.1, 0.3), 4),
        'bb_position': round(np.random.uniform(0, 1), 4),
        'volume_ratio': round(np.random.uniform(0.5, 2.0), 2),
    } 