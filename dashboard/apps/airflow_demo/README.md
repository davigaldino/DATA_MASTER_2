# Airflow Demo App

## Descrição

O app `airflow_demo` é uma demonstração interativa de orquestração de dados que simula o funcionamento do Apache Airflow. Ele permite visualizar em tempo real a execução de um DAG (Directed Acyclic Graph) com tarefas de ETL, incluindo progresso, logs e métricas.

## Funcionalidades

### 1. Simulação de DAG
- **Tarefas do DAG:**
  - `start`: Operador dummy que inicia o processo
  - `extract_data`: Lê dados do arquivo `data/test_small.csv`
  - `transform_data`: Aplica transformações e calcula indicadores técnicos
  - `load_to_postgres`: Carrega dados no PostgreSQL
  - `load_to_mongodb`: Carrega dados no MongoDB
  - `validate_data`: Executa validação de qualidade dos dados
  - `end`: Operador dummy que finaliza o processo

### 2. Interface Visual
- **Painel de Controle:** Botões para iniciar execução e limpar histórico
- **Status do DAG:** Exibe o status geral e progresso das tarefas
- **Visualização do DAG:** Representação gráfica das tarefas e dependências
- **Métricas:** Tempo total de execução e duração por tarefa
- **Logs:** Exibição em tempo real dos logs de execução

### 3. Modelos de Dados
- **DAGRun:** Registra execuções do DAG com status e métricas
- **TaskInstance:** Registra execução individual de cada tarefa

## Como Usar

1. **Acesse a URL:** `http://localhost:8000/dashboard/airflow-demo/`
2. **Inicie a Execução:** Clique em "Iniciar Execução do DAG"
3. **Monitore o Progresso:** Acompanhe a execução em tempo real
4. **Visualize os Resultados:** Veja logs, métricas e status das tarefas

## Estrutura do Projeto

```
airflow_demo/
├── __init__.py
├── apps.py              # Configuração do app
├── models.py            # Modelos DAGRun e TaskInstance
├── dag_simulator.py     # Lógica de simulação do DAG
├── views.py             # Views Django
├── urls.py              # URLs do app
├── templates/
│   └── airflow_demo/
│       └── index.html   # Template principal
└── README.md           # Este arquivo
```

## Dependências

- **Django:** Framework web
- **Pandas:** Manipulação de dados
- **Threading:** Execução assíncrona
- **Módulos ETL:** Reutiliza lógica dos módulos `etl/`

## Arquivo de Dados

O app utiliza o arquivo `data/test_small.csv` como fonte de dados para a demonstração, garantindo execução rápida e controlada.

## Integração

O app está integrado ao projeto principal através de:
- URLs incluídas em `dashboard/urls.py`
- App registrado em `dashboard/settings.py`
- Navegação disponível no template base

## Tecnologias Utilizadas

- **Backend:** Django, Python
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Banco de Dados:** PostgreSQL (via Django ORM)
- **Processamento:** Pandas, módulos ETL customizados 