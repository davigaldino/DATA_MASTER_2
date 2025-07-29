# 📊 Exemplos de Uso - Data Master 2

Este documento fornece exemplos práticos de como usar o projeto Data Master 2 para análise de dados da B3.

## 🚀 Início Rápido

### 1. Execução com Docker (Mais Simples)

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/data-master-2.git
cd data-master-2

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Iniciar todos os serviços
docker-compose up -d

# Executar ETL inicial
docker-compose exec web python scripts/run_etl.py --all

# Acessar dashboard
# Abra: http://localhost:8000
```

### 2. Execução Local

```bash
# Configurar ambiente Python
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
python scripts/setup_database.py

# Executar ETL
python scripts/run_etl.py --all

# Iniciar Django
cd dashboard
python manage.py runserver
```

## 📊 Exemplos de Pipeline ETL

### Execução Completa do ETL

```bash
# Executar todo o pipeline
python scripts/run_etl.py --all

# Saída esperada:
# 🔍 Iniciando pipeline ETL...
# 📥 Extraindo dados do CSV...
# 🧹 Limpando dados...
# 📈 Calculando indicadores técnicos...
# 💾 Carregando dados no PostgreSQL...
# ✅ Pipeline ETL concluído com sucesso!
```

### Execução por Etapas

```bash
# Apenas extração
python scripts/run_etl.py --extract

# Apenas transformação
python scripts/run_etl.py --transform

# Apenas carregamento
python scripts/run_etl.py --load

# Extração e transformação
python scripts/run_etl.py --extract --transform
```

### Filtros Específicos

```bash
# Filtrar por tickers específicos
python scripts/run_etl.py --all --tickers PETR4,VALE3,ITUB4

# Filtrar por período
python scripts/run_etl.py --all --start-date 2020-01-01 --end-date 2020-12-31

# Combinar filtros
python scripts/run_etl.py --all --tickers PETR4 --start-date 2020-01-01 --end-date 2020-12-31
```

## 🔍 Exemplos de Uso da API

### Consultas Básicas

```python
import requests
import pandas as pd

# Configurar URL base
BASE_URL = "http://localhost:8000/api"

# 1. Listar todos os dados de ações
response = requests.get(f"{BASE_URL}/stocks/stock-data/")
data = response.json()
print(f"Total de registros: {data['count']}")

# 2. Filtrar por ticker
response = requests.get(f"{BASE_URL}/stocks/stock-data/?ticker=PETR4")
petr4_data = response.json()

# 3. Filtrar por período
response = requests.get(f"{BASE_URL}/stocks/stock-data/?start_date=2020-01-01&end_date=2020-12-31")
period_data = response.json()

# 4. Combinar filtros
response = requests.get(f"{BASE_URL}/stocks/stock-data/?ticker=PETR4&start_date=2020-01-01&end_date=2020-12-31")
filtered_data = response.json()
```

### Análise de Dados com Pandas

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Buscar dados
response = requests.get("http://localhost:8000/api/stocks/stock-data/?ticker=PETR4&format=json")
data = response.json()

# Converter para DataFrame
df = pd.DataFrame(data['results'])
df['date'] = pd.to_datetime(df['date'])

# Análise básica
print("Estatísticas de PETR4:")
print(f"Período: {df['date'].min()} a {df['date'].max()}")
print(f"Preço atual: R$ {df['close'].iloc[-1]:.2f}")
print(f"Variação total: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")

# Gráfico de preços
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['close'])
plt.title('Evolução do Preço - PETR4')
plt.xlabel('Data')
plt.ylabel('Preço (R$)')
plt.grid(True)
plt.show()
```

### Análise de Indicadores Técnicos

```python
# Buscar indicadores técnicos
response = requests.get("http://localhost:8000/api/stocks/technical-indicators/?ticker=PETR4")
indicators = response.json()

# Converter para DataFrame
df_indicators = pd.DataFrame(indicators['results'])

# Análise de RSI
rsi_data = df_indicators[['date', 'rsi_14']].dropna()
print("Análise RSI:")
print(f"RSI atual: {rsi_data['rsi_14'].iloc[-1]:.2f}")
print(f"RSI médio: {rsi_data['rsi_14'].mean():.2f}")

# Identificar sinais de sobrecompra/sobrevenda
sobrecompra = rsi_data[rsi_data['rsi_14'] > 70]
sobrevenda = rsi_data[rsi_data['rsi_14'] < 30]

print(f"Dias em sobrecompra: {len(sobrecompra)}")
print(f"Dias em sobrevenda: {len(sobrevenda)}")
```

## 📈 Exemplos de Dashboard

### Configuração de Gráficos

```python
# Exemplo de configuração de gráfico no dashboard
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Criar gráfico de candlestick com volume
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    subplot_titles=('Preços', 'Volume'),
    row_width=[0.7, 0.3]
)

# Adicionar candlestick
fig.add_trace(
    go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ),
    row=1, col=1
)

# Adicionar volume
fig.add_trace(
    go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume'
    ),
    row=2, col=1
)

fig.update_layout(
    title='Análise Técnica - PETR4',
    xaxis_rangeslider_visible=False
)

fig.show()
```

### Filtros Interativos

```python
# Exemplo de filtros no dashboard
import dash
from dash import dcc, html, Input, Output

# Dropdown para tickers
dcc.Dropdown(
    id='ticker-dropdown',
    options=[
        {'label': 'PETR4 - Petrobras', 'value': 'PETR4'},
        {'label': 'VALE3 - Vale', 'value': 'VALE3'},
        {'label': 'ITUB4 - Itaú', 'value': 'ITUB4'},
    ],
    value='PETR4'
)

# Seletor de período
dcc.DatePickerRange(
    id='date-range',
    start_date='2020-01-01',
    end_date='2020-12-31'
)

# Checklist de indicadores
dcc.Checklist(
    id='indicators-checklist',
    options=[
        {'label': 'SMA 20', 'value': 'sma_20'},
        {'label': 'RSI', 'value': 'rsi'},
        {'label': 'MACD', 'value': 'macd'},
    ],
    value=['sma_20', 'rsi']
)
```

## 🔧 Exemplos de Monitoramento

### Verificar Status do ETL

```bash
# Verificar status geral
python scripts/check_etl_status.py

# Gerar relatório completo
python scripts/check_etl_status.py --report
```

### Monitoramento com Docker

```bash
# Ver logs em tempo real
docker-compose logs -f web

# Verificar uso de recursos
docker stats

# Verificar status dos containers
docker-compose ps
```

### Logs Estruturados

```python
import structlog

# Configurar logging
logger = structlog.get_logger()

# Exemplo de uso
logger.info("Iniciando processamento", ticker="PETR4", records=1000)
logger.warning("Dados incompletos encontrados", ticker="VALE3", missing_fields=["volume"])
logger.error("Erro na API", error="Connection timeout", retry_count=3)
```

## 📊 Exemplos de Análise Avançada

### Análise de Correlação

```python
import numpy as np
import pandas as pd
import requests

# Buscar dados de múltiplos tickers
tickers = ['PETR4', 'VALE3', 'ITUB4']
dataframes = {}

for ticker in tickers:
    response = requests.get(f"http://localhost:8000/api/stocks/stock-data/?ticker={ticker}")
    data = response.json()
    df = pd.DataFrame(data['results'])
    df['date'] = pd.to_datetime(df['date'])
    dataframes[ticker] = df.set_index('date')['close']

# Criar DataFrame com todos os preços
prices_df = pd.DataFrame(dataframes)
prices_df = prices_df.dropna()

# Calcular correlação
correlation_matrix = prices_df.corr()
print("Matriz de Correlação:")
print(correlation_matrix)

# Visualizar correlação
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Correlação entre Ações')
plt.show()
```

### Análise de Volatilidade

```python
# Calcular volatilidade móvel
def calculate_volatility(prices, window=20):
    returns = prices.pct_change()
    volatility = returns.rolling(window=window).std() * np.sqrt(252) * 100
    return volatility

# Aplicar para PETR4
petr4_volatility = calculate_volatility(df['close'])

# Gráfico de volatilidade
plt.figure(figsize=(12, 6))
plt.plot(df['date'], petr4_volatility)
plt.title('Volatilidade Móvel (20 dias) - PETR4')
plt.xlabel('Data')
plt.ylabel('Volatilidade Anualizada (%)')
plt.grid(True)
plt.show()

print(f"Volatilidade média: {petr4_volatility.mean():.2f}%")
print(f"Volatilidade atual: {petr4_volatility.iloc[-1]:.2f}%")
```

### Análise de Tendência

```python
# Calcular médias móveis
df['sma_20'] = df['close'].rolling(window=20).mean()
df['sma_50'] = df['close'].rolling(window=50).mean()
df['ema_20'] = df['close'].ewm(span=20).mean()

# Identificar tendências
df['trend'] = np.where(df['sma_20'] > df['sma_50'], 'Alta', 'Baixa')

# Análise de tendência
trend_analysis = df.groupby('trend').agg({
    'close': ['count', 'mean', 'std'],
    'volume': 'mean'
}).round(2)

print("Análise de Tendência:")
print(trend_analysis)
```

## 🚀 Exemplos de Produção

### Configuração de Airflow

```python
# Exemplo de DAG para execução diária
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'b3_daily_etl',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # Diariamente às 2h
    catchup=False
)

# Tarefas do DAG
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_function,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_function,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_function,
    dag=dag
)

# Dependências
extract_task >> transform_task >> load_task
```

### Configuração de Monitoramento

```python
# Exemplo de alertas
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    """Enviar alerta por email"""
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = 'alerts@data-master.com'
    msg['To'] = 'admin@data-master.com'
    
    # Configurar servidor SMTP
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('user', 'password')
    server.send_message(msg)
    server.quit()

# Exemplo de uso
def check_data_quality():
    """Verificar qualidade dos dados"""
    # Verificar dados recentes
    response = requests.get("http://localhost:8000/api/stocks/stock-data/?date__gte=today")
    data = response.json()
    
    if data['count'] == 0:
        send_alert(
            "ALERTA: Dados não carregados",
            "Nenhum dado foi carregado hoje. Verificar pipeline ETL."
        )
```

## 📚 Recursos Adicionais

### Documentação das APIs

```bash
# Acessar documentação da API
curl http://localhost:8000/api/

# Listar endpoints disponíveis
curl http://localhost:8000/api/stocks/
```

### Comandos Úteis

```bash
# Backup do banco de dados
docker-compose exec postgres pg_dump -U postgres b3_data > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U postgres b3_data < backup.sql

# Limpar dados antigos
python scripts/cleanup_old_data.py --days 365

# Reindexar banco de dados
python scripts/reindex_database.py
```

---

**💡 Dica:** Use o dashboard interativo para explorar os dados de forma visual e intuitiva. A API REST permite integração com outras ferramentas e análises personalizadas. 