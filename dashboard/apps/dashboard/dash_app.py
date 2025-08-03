"""
Aplicação Dash integrada ao Django.

Este módulo cria a aplicação Dash que será servida pelo Django,
fornecendo dashboards interativos para análise de dados de ações.
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da aplicação Dash
def create_dash_app(server):
    """
    Cria e configura a aplicação Dash.
    
    Args:
        server: Servidor Django
        
    Returns:
        dash.Dash: Aplicação Dash configurada
    """
    print("=== CREATING DASH APP ===")
    
    # Cria a aplicação Dash
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dashboard/',
        external_stylesheets=[
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
        ],
        suppress_callback_exceptions=True
    )
    
    # Layout principal
    dash_app.layout = html.Div([
        # Header
        html.Div([
            html.H1("AlphaScan - Análise de Ações B3", 
                   className="text-center mb-4 text-primary"),
            html.P("Dashboard interativo para análise de dados históricos da Bolsa Brasileira",
                   className="text-center text-muted mb-4")
        ], className="container-fluid bg-light py-4"),
        
        # Filtros
        html.Div([
            html.Div([
                html.Label("Ticker:", className="form-label"),
                dcc.Dropdown(
                    id='ticker-dropdown',
                    placeholder="Selecione um ticker...",
                    className="mb-3"
                )
            ], className="col-md-3"),
            
            html.Div([
                html.Label("Período:", className="form-label"),
                dcc.Dropdown(
                    id='period-dropdown',
                    options=[
                        {'label': '1 Mês', 'value': '1m'},
                        {'label': '3 Meses', 'value': '3m'},
                        {'label': '6 Meses', 'value': '6m'},
                        {'label': '1 Ano', 'value': '1y'},
                        {'label': '2 Anos', 'value': '2y'},
                        {'label': '5 Anos', 'value': '5y'}
                    ],
                    value='1y',
                    className="mb-3"
                )
            ], className="col-md-4"),
            
            html.Div([
                html.Label("Indicadores:", className="form-label"),
                dcc.Checklist(
                    id='indicators-checklist',
                    options=[
                        {'label': 'Médias Móveis', 'value': 'sma'},
                        {'label': 'Bollinger Bands', 'value': 'bb'},
                        {'label': 'Volume', 'value': 'volume'},
                        {'label': 'RSI', 'value': 'rsi'},
                        {'label': 'MACD', 'value': 'macd'}
                    ],
                    value=['sma'],
                    className="mb-3"
                )
            ], className="col-md-3"),
            
            html.Div([
                html.Button("Atualizar", id="update-button", 
                           className="btn btn-primary mt-4")
            ], className="col-md-2")
        ], className="row mb-4", style={'padding': '20px'}),
        
        # Gráficos
        html.Div([
            # Gráfico principal de preços
            html.Div([
                dcc.Graph(id='price-chart', style={'height': '500px'})
            ], className="col-12 mb-4"),
            
            # Gráficos de indicadores
            html.Div([
                html.Div([
                    dcc.Graph(id='volume-chart', style={'height': '300px'})
                ], className="col-md-6"),
                
                html.Div([
                    dcc.Graph(id='rsi-chart', style={'height': '300px'})
                ], className="col-md-6")
            ], className="row mb-4"),
            
            html.Div([
                html.Div([
                    dcc.Graph(id='macd-chart', style={'height': '300px'})
                ], className="col-md-6"),
                
                html.Div([
                    dcc.Graph(id='bb-chart', style={'height': '300px'})
                ], className="col-md-6")
            ], className="row mb-4")
        ], className="container-fluid"),
        
        # Estatísticas
        html.Div([
            html.H3("Estatísticas", className="mb-3"),
            html.Div(id='stats-container', className="row")
        ], className="container-fluid mb-4"),
        
        # Loading
        dcc.Loading(id="loading-1", type="default"),
        dcc.Loading(id="loading-2", type="default"),
        
        # Store para dados
        dcc.Store(id='chart-data-store'),
        dcc.Store(id='stats-data-store')
    ])
    
    return dash_app


# Callbacks

@callback(
    Output('chart-data-store', 'data'),
    Input('period-dropdown', 'value'),
    Input('ticker-dropdown', 'value')
)
def update_data_on_period_change(period, ticker):
    """Atualiza dados quando o período ou ticker muda."""
    print(f"=== CALLBACK EXECUTED ===")
    print(f"period: {period}")
    print(f"ticker: {ticker}")
    print(f"period type: {type(period)}")
    print(f"ticker type: {type(ticker)}")
    
    if not ticker or not period:
        print("Retornando vazio - ticker ou period não fornecidos")
        return {}
    
    # Calcular datas baseado no período selecionado
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
    
    start_date = start_date.date()
    end_date = base_date.date()
    
    print(f"Calculated dates: {start_date} to {end_date}")
    
    try:
        # Buscar dados reais da API Django usando o parâmetro period
        data = fetch_real_data(ticker, period=period)
        
        if not data:
            # Fallback para dados simulados
            print("API não disponível, usando dados simulados")
            data = generate_sample_data(ticker, start_date, end_date, period=period)
        
        return data
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return generate_sample_data(ticker, start_date, end_date, period=period)
@callback(
    Output('ticker-dropdown', 'options'),
    Output('ticker-dropdown', 'value'),
    Input('update-button', 'n_clicks')
)
def update_ticker_options(n_clicks):
    print(f"=== update_ticker_options called ===")
    print(f"n_clicks: {n_clicks}")
    """Atualiza as opções de tickers disponíveis."""
    try:
        # Em produção, isso seria uma chamada para a API
        # Por enquanto, retorna tickers fixos
        options = [
            {'label': 'PETR4 - Petrobras', 'value': 'PETR4'},
            {'label': 'VALE3 - Vale', 'value': 'VALE3'},
            {'label': 'ITUB4 - Itaú', 'value': 'ITUB4'},
            {'label': 'BBDC4 - Bradesco', 'value': 'BBDC4'},
            {'label': 'ABEV3 - Ambev', 'value': 'ABEV3'},
        ]
        return options, 'PETR4'
    except Exception as e:
        print(f"Erro ao carregar tickers: {e}")
        return [], None











@callback(
    Output('price-chart', 'figure'),
    Input('chart-data-store', 'data'),
    Input('indicators-checklist', 'value')
)
def update_price_chart(data, indicators):
    """Atualiza o gráfico principal de preços."""
    if not data:
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        
        # Cria subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('Preços', 'Volume'),
            row_width=[0.7, 0.3]
        )
        
        # Gráfico de candlestick
        fig.add_trace(
            go.Candlestick(
                x=df['datetime'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC'
            ),
            row=1, col=1
        )
        
        # Adiciona médias móveis se selecionadas
        if 'sma' in indicators:
            if 'sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['datetime'],
                        y=df['sma_20'],
                        mode='lines',
                        name='SMA 20',
                        line=dict(color='orange', width=1)
                    ),
                    row=1, col=1
                )
            
            if 'sma_50' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['datetime'],
                        y=df['sma_50'],
                        mode='lines',
                        name='SMA 50',
                        line=dict(color='blue', width=1)
                    ),
                    row=1, col=1
                )
        
        # Adiciona Bollinger Bands se selecionadas
        if 'bb' in indicators:
            if all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
                fig.add_trace(
                    go.Scatter(
                        x=df['datetime'],
                        y=df['bb_upper'],
                        mode='lines',
                        name='BB Superior',
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['datetime'],
                        y=df['bb_middle'],
                        mode='lines',
                        name='BB Média',
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['datetime'],
                        y=df['bb_lower'],
                        mode='lines',
                        name='BB Inferior',
                        line=dict(color='gray', width=1, dash='dash'),
                        fill='tonexty'
                    ),
                    row=1, col=1
                )
        
        # Gráfico de volume
        if 'volume' in indicators and 'volume' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df['datetime'],
                    y=df['volume'],
                    name='Volume',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
        
        # Atualiza layout
        fig.update_layout(
            title=f'Análise Técnica - {data[0]["ticker"] if data else ""}',
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de preços: {e}")
        return go.Figure()


@callback(
    Output('volume-chart', 'figure'),
    Input('chart-data-store', 'data')
)
def update_volume_chart(data):
    """Atualiza o gráfico de volume."""
    if not data or 'volume' not in data[0]:
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=df['datetime'],
                y=df['volume'],
                name='Volume',
                marker_color='lightblue'
            )
        )
        
        fig.update_layout(
            title='Volume de Negociação',
            xaxis_title='Data',
            yaxis_title='Volume',
            height=300
        )
        
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de volume: {e}")
        return go.Figure()


@callback(
    Output('rsi-chart', 'figure'),
    Input('chart-data-store', 'data')
)
def update_rsi_chart(data):
    """Atualiza o gráfico de RSI."""
    if not data or 'rsi_14' not in data[0]:
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['rsi_14'],
                mode='lines',
                name='RSI 14',
                line=dict(color='purple', width=2)
            )
        )
        
        # Linhas de referência
        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                     annotation_text="Sobrecomprado")
        fig.add_hline(y=30, line_dash="dash", line_color="green", 
                     annotation_text="Sobrevendido")
        
        fig.update_layout(
            title='RSI (Relative Strength Index)',
            xaxis_title='Data',
            yaxis_title='RSI',
            yaxis=dict(range=[0, 100]),
            height=300
        )
        
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de RSI: {e}")
        return go.Figure()


@callback(
    Output('macd-chart', 'figure'),
    Input('chart-data-store', 'data')
)
def update_macd_chart(data):
    """Atualiza o gráfico de MACD."""
    if not data or 'macd' not in data[0]:
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('MACD', 'Histograma'),
            row_width=[0.7, 0.3]
        )
        
        # MACD
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        if 'macd_signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['datetime'],
                    y=df['macd_signal'],
                    mode='lines',
                    name='Sinal',
                    line=dict(color='red', width=2)
                ),
                row=1, col=1
            )
        
        # Histograma
        if 'macd_histogram' in df.columns:
            colors = ['green' if val >= 0 else 'red' for val in df['macd_histogram']]
            fig.add_trace(
                go.Bar(
                    x=df['datetime'],
                    y=df['macd_histogram'],
                    name='Histograma',
                    marker_color=colors
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            title='MACD (Moving Average Convergence Divergence)',
            height=400,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de MACD: {e}")
        return go.Figure()


@callback(
    Output('bb-chart', 'figure'),
    Input('chart-data-store', 'data')
)
def update_bb_chart(data):
    """Atualiza o gráfico de Bollinger Bands."""
    if not data or not all(col in data[0] for col in ['bb_upper', 'bb_middle', 'bb_lower']):
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        # Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['bb_upper'],
                mode='lines',
                name='BB Superior',
                line=dict(color='gray', width=1, dash='dash')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['bb_middle'],
                mode='lines',
                name='BB Média',
                line=dict(color='gray', width=1, dash='dash')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['bb_lower'],
                mode='lines',
                name='BB Inferior',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty'
            )
        )
        
        # Preço
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['close'],
                mode='lines',
                name='Preço',
                line=dict(color='black', width=2)
            )
        )
        
        fig.update_layout(
            title='Bollinger Bands',
            xaxis_title='Data',
            yaxis_title='Preço',
            height=300
        )
        
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de Bollinger Bands: {e}")
        return go.Figure()


@callback(
    Output('stats-container', 'children'),
    Input('chart-data-store', 'data')
)
def update_stats(data):
    """Atualiza as estatísticas."""
    if not data:
        return []
    
    try:
        df = pd.DataFrame(data)
        
        # Calcula estatísticas básicas
        current_price = df['close'].iloc[-1]
        price_change = df['close'].iloc[-1] - df['close'].iloc[0]
        price_change_pct = (price_change / df['close'].iloc[0]) * 100
        
        stats = [
            html.Div([
                html.H4("Preço Atual", className="text-center"),
                html.H2(f"R$ {current_price:.2f}", className="text-center text-primary")
            ], className="col-md-3"),
            
            html.Div([
                html.H4("Variação Total", className="text-center"),
                html.H2(f"{price_change_pct:.2f}%", 
                       className=f"text-center {'text-success' if price_change_pct >= 0 else 'text-danger'}")
            ], className="col-md-3"),
            
            html.Div([
                html.H4("Volume Médio", className="text-center"),
                html.H2(f"{df['volume'].mean():,.0f}", className="text-center text-info")
            ], className="col-md-3"),
            
            html.Div([
                html.H4("Volatilidade", className="text-center"),
                html.H2(f"{df['close'].pct_change().std() * 100:.2f}%", className="text-center text-warning")
            ], className="col-md-3")
        ]
        
        return stats
        
    except Exception as e:
        print(f"Erro ao calcular estatísticas: {e}")
        return []


def fetch_real_data(ticker, start_date=None, end_date=None, period=None):
    """Busca dados reais da API Django."""
    try:
        # Configurar URL da API
        api_base_url = os.getenv('DJANGO_API_URL', 'http://localhost:8000/api')
        
        # Parâmetros da requisição
        params = {
            'ticker': ticker,
            'format': 'json'
        }
        
        # Adicionar parâmetros se fornecidos
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if period:
            params['period'] = period
        
        # Log para debug
        print(f"=== DEBUG: fetch_real_data ===")
        print(f"Ticker: {ticker}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        print(f"API URL: {api_base_url}/stocks/with_indicators/")
        print(f"Params: {params}")
        
        # Fazer requisição para a API - URL com indicadores
        response = requests.get(f"{api_base_url}/stocks/with_indicators/", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Response Status: {response.status_code}")
            print(f"Data received: {len(data) if data else 0} records")
            if data:
                print(f"First record date: {data[0]['date']}")
                print(f"Last record date: {data[-1]['date']}")
            
            if data:
                # Converter para formato esperado pelo dashboard
                formatted_data = []
                for item in data:
                    formatted_item = {
                        'datetime': item['date'],
                        'ticker': item['ticker'],
                        'open': float(item['open']),
                        'high': float(item['high']),
                        'low': float(item['low']),
                        'close': float(item['close']),
                        'volume': int(item['volume'])
                    }
                    
                    # Adicionar indicadores técnicos se disponíveis
                    if 'indicators' in item and item['indicators']:
                        # Pega o primeiro indicador (deve ser o mesmo dia)
                        indicator = item['indicators'][0] if item['indicators'] else {}
                        formatted_item.update({
                            'sma_20': float(indicator.get('sma_20', 0)) if indicator.get('sma_20') else None,
                            'sma_50': float(indicator.get('sma_50', 0)) if indicator.get('sma_50') else None,
                            'rsi_14': float(indicator.get('rsi_14', 0)) if indicator.get('rsi_14') else None,
                            'macd': float(indicator.get('macd', 0)) if indicator.get('macd') else None,
                            'macd_signal': float(indicator.get('macd_signal', 0)) if indicator.get('macd_signal') else None,
                            'macd_histogram': float(indicator.get('macd_histogram', 0)) if indicator.get('macd_histogram') else None,
                            'bb_upper': float(indicator.get('bb_upper', 0)) if indicator.get('bb_upper') else None,
                            'bb_middle': float(indicator.get('bb_middle', 0)) if indicator.get('bb_middle') else None,
                            'bb_lower': float(indicator.get('bb_lower', 0)) if indicator.get('bb_lower') else None,
                        })
                    
                    formatted_data.append(formatted_item)
                
                print(f"Dados reais carregados: {len(formatted_data)} registros para {ticker}")
                return formatted_data
            else:
                print(f"Nenhum dado encontrado para {ticker}")
                return []
        else:
            print(f"Erro na API: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
        return []


def generate_sample_data(ticker, start_date, end_date, period=None):
    """Gera dados de exemplo para demonstração."""
    import numpy as np
    
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
    
    # Remove fins de semana
    dates = dates[dates.weekday < 5]
    
    # Gera preços simulados
    np.random.seed(42)  # Para reprodutibilidade
    n_days = len(dates)
    
    # Preço inicial
    initial_price = 50.0
    
    # Gera retornos logarítmicos
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
            'datetime': date,
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