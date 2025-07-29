# 🚀 Guia de Reprodução - Data Master 2

Este guia fornece instruções detalhadas para reproduzir o projeto de análise de dados da B3 em sua máquina local.

## 📋 Pré-requisitos

### Software Necessário
- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Docker e Docker Compose** - [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **PostgreSQL** (opcional, se não usar Docker) - [Download PostgreSQL](https://www.postgresql.org/download/)

### Recursos do Sistema
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **Espaço em Disco**: Mínimo 2GB livres
- **Sistema Operacional**: Windows 10+, macOS 10.14+, ou Linux

## 🔧 Configuração Inicial

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/data-master-2.git
cd data-master-2
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar o arquivo .env com suas configurações
# Use um editor de texto de sua preferência
```

**Configurações importantes no arquivo `.env`:**

```env
# Django
DJANGO_SECRET_KEY=sua-chave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=b3_data
DB_USER=postgres
DB_PASSWORD=sua-senha-postgres

# API Keys (opcional)
YAHOO_FINANCE_API_KEY=sua-api-key-yahoo
ALPHA_VANTAGE_API_KEY=sua-api-key-alpha-vantage

# Configurações do Dashboard
DASHBOARD_HOST=localhost
DASHBOARD_PORT=8000
```

### 3. Preparar o Dataset

Certifique-se de que o arquivo `b3_stocks_1994_2020.csv` está na raiz do projeto:

```bash
# Verificar se o arquivo existe
ls -la b3_stocks_1994_2020.csv
```

Se o arquivo não existir, você pode:
- Baixá-lo do repositório original
- Usar dados simulados (o sistema tem fallback automático)

## 🐳 Execução com Docker (Recomendado)

### 1. Construir e Iniciar os Containers

```bash
# Construir as imagens
docker-compose build

# Iniciar todos os serviços
docker-compose up -d
```

### 2. Verificar Status dos Serviços

```bash
# Verificar se todos os containers estão rodando
docker-compose ps

# Ver logs dos serviços
docker-compose logs -f web
docker-compose logs -f postgres
docker-compose logs -f airflow
```

### 3. Executar ETL Inicial

```bash
# Executar o pipeline ETL
docker-compose exec web python scripts/run_etl.py --all

# Ou executar etapas específicas
docker-compose exec web python scripts/run_etl.py --extract --transform --load
```

### 4. Acessar as Aplicações

- **Dashboard Django**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **Airflow**: http://localhost:8080 (admin/admin)
- **API REST**: http://localhost:8000/api/

## 💻 Execução Local (Sem Docker)

### 1. Configurar Ambiente Python

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados PostgreSQL

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco de dados
CREATE DATABASE b3_data;

# Sair do psql
\q

# Executar script de inicialização
python scripts/setup_database.py
```

### 3. Configurar Django

```bash
# Navegar para o diretório do dashboard
cd dashboard

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput
```

### 4. Executar ETL

```bash
# Voltar para a raiz do projeto
cd ..

# Executar pipeline ETL
python scripts/run_etl.py --all
```

### 5. Iniciar Servidor Django

```bash
# Navegar para o diretório do dashboard
cd dashboard

# Iniciar servidor
python manage.py runserver
```

## 📊 Execução do Pipeline ETL

### Opções de Execução

```bash
# Executar pipeline completo
python scripts/run_etl.py --all

# Executar etapas específicas
python scripts/run_etl.py --extract
python scripts/run_etl.py --transform
python scripts/run_etl.py --load

# Filtrar por ticker específico
python scripts/run_etl.py --all --tickers PETR4,VALE3

# Filtrar por período
python scripts/run_etl.py --all --start-date 2020-01-01 --end-date 2020-12-31

# Ver ajuda
python scripts/run_etl.py --help
```

### Monitoramento do ETL

```bash
# Ver logs em tempo real
tail -f logs/etl.log

# Verificar status no banco de dados
python scripts/check_etl_status.py
```

## 🎯 Uso do Dashboard

### 1. Acessar o Dashboard

Abra seu navegador e acesse: http://localhost:8000

### 2. Fazer Login

- **Usuário**: admin
- **Senha**: admin123 (ou a senha configurada no .env)

### 3. Navegar pelo Dashboard

1. **Selecionar Ticker**: Escolha uma ação da lista
2. **Definir Período**: Selecione o intervalo de datas
3. **Escolher Indicadores**: Marque os indicadores técnicos desejados
4. **Visualizar Gráficos**: Analise os dados nos diferentes gráficos

### 4. Funcionalidades Disponíveis

- **Gráfico de Candlestick**: Preços OHLC com indicadores
- **Volume**: Volume de negociação
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Bandas de Bollinger
- **Estatísticas**: Resumo dos dados

## 🔍 API REST

### Endpoints Disponíveis

```bash
# Listar dados de ações
GET /api/stocks/stock-data/

# Filtrar por ticker
GET /api/stocks/stock-data/?ticker=PETR4

# Filtrar por período
GET /api/stocks/stock-data/?start_date=2020-01-01&end_date=2020-12-31

# Indicadores técnicos
GET /api/stocks/technical-indicators/

# Metadados
GET /api/stocks/data-metadata/

# Opções de filtro
GET /api/stocks/filter-options/
```

### Exemplo de Uso da API

```bash
# Usando curl
curl "http://localhost:8000/api/stocks/stock-data/?ticker=PETR4&format=json"

# Usando Python
import requests
response = requests.get("http://localhost:8000/api/stocks/stock-data/", 
                       params={'ticker': 'PETR4'})
data = response.json()
```

## 🛠️ Solução de Problemas

### Problemas Comuns

#### 1. Erro de Conexão com Banco de Dados

```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres

# Verificar logs
docker-compose logs postgres

# Reiniciar serviço
docker-compose restart postgres
```

#### 2. Erro de Permissão no Docker

```bash
# No Linux/macOS, pode ser necessário ajustar permissões
sudo chown -R $USER:$USER .

# Ou executar com privilégios
sudo docker-compose up -d
```

#### 3. Porta Já em Uso

```bash
# Verificar portas em uso
netstat -tulpn | grep :8000

# Parar processo que está usando a porta
sudo kill -9 <PID>

# Ou alterar porta no docker-compose.yml
```

#### 4. Erro de Memória

```bash
# Aumentar memória do Docker
# No Docker Desktop: Settings > Resources > Memory

# Ou reduzir recursos no docker-compose.yml
```

### Logs e Debugging

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de serviço específico
docker-compose logs web
docker-compose logs postgres
docker-compose logs airflow

# Seguir logs em tempo real
docker-compose logs -f web
```

## 📈 Monitoramento e Observabilidade

### Logs Estruturados

Os logs são salvos em:
- `logs/etl.log` - Logs do pipeline ETL
- `logs/django.log` - Logs da aplicação Django
- `logs/airflow.log` - Logs do Airflow

### Métricas de Performance

```bash
# Verificar uso de recursos
docker stats

# Verificar tamanho do banco de dados
docker-compose exec postgres psql -U postgres -d b3_data -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## 🔄 Atualizações e Manutenção

### Atualizar Código

```bash
# Parar serviços
docker-compose down

# Atualizar código
git pull origin main

# Reconstruir e reiniciar
docker-compose build
docker-compose up -d
```

### Backup do Banco de Dados

```bash
# Criar backup
docker-compose exec postgres pg_dump -U postgres b3_data > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T postgres psql -U postgres b3_data < backup_file.sql
```

### Limpeza de Dados

```bash
# Limpar dados antigos
python scripts/cleanup_old_data.py --days 365

# Reindexar banco de dados
python scripts/reindex_database.py
```

## 📚 Recursos Adicionais

### Documentação
- [Django Documentation](https://docs.djangoproject.com/)
- [Dash Documentation](https://dash.plotly.com/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Comunidade
- [Stack Overflow](https://stackoverflow.com/questions/tagged/django)
- [GitHub Issues](https://github.com/seu-usuario/data-master-2/issues)

## 🆘 Suporte

Se encontrar problemas:

1. **Verificar logs**: Use `docker-compose logs` para identificar erros
2. **Consultar documentação**: Verifique a documentação das tecnologias
3. **Criar issue**: Abra uma issue no GitHub com detalhes do problema
4. **Contato**: Entre em contato através do email do projeto

---

**🎉 Parabéns!** Você configurou com sucesso o projeto Data Master 2. Agora pode explorar os dados da B3 através do dashboard interativo e API REST. 