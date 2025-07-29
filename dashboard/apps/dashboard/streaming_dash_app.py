"""
Streaming Dashboard - Visualização de dados em tempo real
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import time
from typing import Dict, List, Any
import structlog

logger = structlog.get_logger()

def create_streaming_dashboard():
    """
    Cria o dashboard de streaming com gráficos em tempo real.
    """
    
    app = dash.Dash(__name__, 
                    external_stylesheets=[
                        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
                    ])
    
    # Layout do dashboard
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("📊 Dashboard de Streaming - Dados em Tempo Real", 
                   className="text-center mb-4"),
            html.P("Monitoramento de dados de ações da B3 em tempo real", 
                  className="text-center text-muted")
        ], className="mb-4"),
        
        # Controles
        html.Div([
            html.Div([
                html.Label("Ticker:", className="form-label"),
                dcc.Input(
                    id='ticker-input',
                    type='text',
                    placeholder='Ex: PETR4',
                    value='PETR4',
                    className="form-control"
                )
            ], className="col-md-3"),
            
            html.Div([
                html.Label("Intervalo de Atualização (segundos):", className="form-label"),
                dcc.Slider(
                    id='update-interval',
                    min=1,
                    max=30,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(1, 31, 5)},
                    className="mt-2"
                )
            ], className="col-md-6"),
            
            html.Div([
                html.Label("Status:", className="form-label"),
                html.Div(id='streaming-status', className="badge bg-success")
            ], className="col-md-3")
        ], className="row mb-4"),
        
        # Gráficos
        html.Div([
            # Gráfico de Preços em Tempo Real
            html.Div([
                html.H4("📈 Preços em Tempo Real", className="mb-3"),
                dcc.Graph(id='price-chart', style={'height': '400px'})
            ], className="col-md-8"),
            
            # Estatísticas Rápidas
            html.Div([
                html.H4("📊 Estatísticas", className="mb-3"),
                html.Div(id='stats-cards', className="row")
            ], className="col-md-4")
        ], className="row mb-4"),
        
        # Gráficos de Indicadores
        html.Div([
            # Volume
            html.Div([
                html.H4("📊 Volume de Negociação", className="mb-3"),
                dcc.Graph(id='volume-chart', style={'height': '300px'})
            ], className="col-md-6"),
            
            # Variação Percentual
            html.Div([
                html.H4("📈 Variação Percentual", className="mb-3"),
                dcc.Graph(id='variation-chart', style={'height': '300px'})
            ], className="col-md-6")
        ], className="row mb-4"),
        
        # Tabela de Dados Recentes
        html.Div([
            html.H4("📋 Dados Recentes", className="mb-3"),
            html.Div(id='recent-data-table', className="table-responsive")
        ], className="mb-4"),
        
        # Intervalo de atualização
        dcc.Interval(
            id='interval-component',
            interval=5000,  # 5 segundos
            n_intervals=0
        ),
        
        # Store para dados
        dcc.Store(id='streaming-data-store'),
        
        # Logs
        html.Div([
            html.H4("📝 Logs de Streaming", className="mb-3"),
            html.Div(id='streaming-logs', className="bg-light p-3 rounded", 
                    style={'max-height': '200px', 'overflow-y': 'auto'})
        ])
    ], className="container-fluid p-4")
    
    # Callbacks
    @app.callback(
        Output('streaming-data-store', 'data'),
        Output('streaming-status', 'children'),
        Output('streaming-status', 'className'),
        Input('interval-component', 'n_intervals'),
        Input('ticker-input', 'value'),
        State('update-interval', 'value')
    )
    def update_streaming_data(n_intervals, ticker, update_interval):
        """
        Atualiza dados de streaming.
        """
        try:
            # Simula dados de streaming (em produção, viria da API)
            current_time = datetime.now()
            
            # Gera dados simulados baseados no ticker
            base_price = 50.0 + hash(ticker) % 100  # Preço base único por ticker
            variation = np.sin(current_time.timestamp() / 100) * 2  # Variação senoidal
            current_price = base_price + variation
            
            # Dados simulados
            streaming_data = {
                'timestamp': current_time.isoformat(),
                'ticker': ticker.upper(),
                'price': round(current_price, 2),
                'volume': int(1000000 + np.random.normal(0, 100000)),
                'variation': round(variation, 2),
                'variation_percent': round((variation / base_price) * 100, 2),
                'high': round(current_price + abs(variation), 2),
                'low': round(current_price - abs(variation), 2),
                'open': round(base_price, 2)
            }
            
            status_text = f"🟢 Ativo - {ticker.upper()}"
            status_class = "badge bg-success"
            
            logger.info("Dados de streaming atualizados", 
                       ticker=ticker,
                       price=streaming_data['price'],
                       variation_percent=streaming_data['variation_percent'])
            
            return streaming_data, status_text, status_class
            
        except Exception as e:
            logger.error("Erro ao atualizar dados de streaming", error=str(e))
            return {}, "🔴 Erro", "badge bg-danger"
    
    @app.callback(
        Output('price-chart', 'figure'),
        Input('streaming-data-store', 'data'),
        Input('ticker-input', 'value')
    )
    def update_price_chart(streaming_data, ticker):
        """
        Atualiza gráfico de preços.
        """
        if not streaming_data:
            return go.Figure().add_annotation(
                text="Aguardando dados...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Simula histórico de preços
        current_time = datetime.now()
        times = [current_time - timedelta(minutes=i) for i in range(30, 0, -1)]
        times.append(current_time)
        
        base_price = float(streaming_data['price'])
        prices = [base_price + np.sin(t.timestamp() / 100) * 2 for t in times]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=times,
            y=prices,
            mode='lines+markers',
            name=f'{ticker} - Preço',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Preços em Tempo Real - {ticker}",
            xaxis_title="Tempo",
            yaxis_title="Preço (R$)",
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
    
    @app.callback(
        Output('volume-chart', 'figure'),
        Input('streaming-data-store', 'data'),
        Input('ticker-input', 'value')
    )
    def update_volume_chart(streaming_data, ticker):
        """
        Atualiza gráfico de volume.
        """
        if not streaming_data:
            return go.Figure().add_annotation(
                text="Aguardando dados...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Simula histórico de volume
        current_time = datetime.now()
        times = [current_time - timedelta(minutes=i) for i in range(30, 0, -1)]
        times.append(current_time)
        
        base_volume = int(streaming_data['volume'])
        volumes = [base_volume + np.random.normal(0, 100000) for _ in times]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=times,
            y=volumes,
            name=f'{ticker} - Volume',
            marker_color='#ff7f0e'
        ))
        
        fig.update_layout(
            title=f"Volume de Negociação - {ticker}",
            xaxis_title="Tempo",
            yaxis_title="Volume",
            showlegend=True,
            height=300
        )
        
        return fig
    
    @app.callback(
        Output('variation-chart', 'figure'),
        Input('streaming-data-store', 'data'),
        Input('ticker-input', 'value')
    )
    def update_variation_chart(streaming_data, ticker):
        """
        Atualiza gráfico de variação percentual.
        """
        if not streaming_data:
            return go.Figure().add_annotation(
                text="Aguardando dados...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Simula histórico de variação
        current_time = datetime.now()
        times = [current_time - timedelta(minutes=i) for i in range(30, 0, -1)]
        times.append(current_time)
        
        base_variation = float(streaming_data['variation_percent'])
        variations = [base_variation + np.sin(t.timestamp() / 100) * 2 for t in times]
        
        fig = go.Figure()
        
        # Linha de variação
        fig.add_trace(go.Scatter(
            x=times,
            y=variations,
            mode='lines+markers',
            name=f'{ticker} - Variação %',
            line=dict(color='#2ca02c', width=2),
            marker=dict(size=6)
        ))
        
        # Linha zero
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig.update_layout(
            title=f"Variação Percentual - {ticker}",
            xaxis_title="Tempo",
            yaxis_title="Variação (%)",
            showlegend=True,
            height=300
        )
        
        return fig
    
    @app.callback(
        Output('stats-cards', 'children'),
        Input('streaming-data-store', 'data')
    )
    def update_stats_cards(streaming_data):
        """
        Atualiza cards de estatísticas.
        """
        if not streaming_data:
            return []
        
        cards = [
            html.Div([
                html.Div([
                    html.H5("Preço Atual", className="card-title"),
                    html.H3(f"R$ {streaming_data['price']}", className="text-primary")
                ], className="card-body")
            ], className="card mb-2"),
            
            html.Div([
                html.Div([
                    html.H5("Variação", className="card-title"),
                    html.H3(f"{streaming_data['variation_percent']}%", 
                           className="text-success" if streaming_data['variation_percent'] >= 0 else "text-danger")
                ], className="card-body")
            ], className="card mb-2"),
            
            html.Div([
                html.Div([
                    html.H5("Volume", className="card-title"),
                    html.H3(f"{streaming_data['volume']:,}", className="text-info")
                ], className="card-body")
            ], className="card mb-2"),
            
            html.Div([
                html.Div([
                    html.H5("Última Atualização", className="card-title"),
                    html.H6(datetime.now().strftime("%H:%M:%S"), className="text-muted")
                ], className="card-body")
            ], className="card")
        ]
        
        return cards
    
    @app.callback(
        Output('recent-data-table', 'children'),
        Input('streaming-data-store', 'data')
    )
    def update_recent_data_table(streaming_data):
        """
        Atualiza tabela de dados recentes.
        """
        if not streaming_data:
            return html.P("Aguardando dados...", className="text-muted")
        
        # Simula dados recentes
        recent_data = []
        current_time = datetime.now()
        
        for i in range(10):
            time_point = current_time - timedelta(minutes=i*2)
            base_price = float(streaming_data['price'])
            variation = np.sin(time_point.timestamp() / 100) * 2
            price = base_price + variation
            
            recent_data.append({
                'timestamp': time_point.strftime("%H:%M:%S"),
                'price': round(price, 2),
                'volume': int(streaming_data['volume'] + np.random.normal(0, 50000)),
                'variation': round(variation, 2)
            })
        
        # Cria tabela
        table_header = html.Thead(html.Tr([
            html.Th("Horário"),
            html.Th("Preço (R$)"),
            html.Th("Volume"),
            html.Th("Variação")
        ]))
        
        table_body = html.Tbody([
            html.Tr([
                html.Td(row['timestamp']),
                html.Td(f"R$ {row['price']}"),
                html.Td(f"{row['volume']:,}"),
                html.Td(f"{row['variation']:+.2f}", 
                       className="text-success" if row['variation'] >= 0 else "text-danger")
            ]) for row in recent_data
        ])
        
        return html.Table([table_header, table_body], className="table table-striped")
    
    @app.callback(
        Output('streaming-logs', 'children'),
        Input('streaming-data-store', 'data')
    )
    def update_streaming_logs(streaming_data):
        """
        Atualiza logs de streaming.
        """
        if not streaming_data:
            return html.P("Aguardando dados de streaming...", className="text-muted")
        
        current_time = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{current_time}] {streaming_data['ticker']}: R$ {streaming_data['price']} ({streaming_data['variation_percent']:+.2f}%)"
        
        return html.P(log_entry, className="mb-1")
    
    return app


def create_streaming_dashboard_app():
    """
    Factory function para criar o dashboard de streaming.
    """
    return create_streaming_dashboard() 