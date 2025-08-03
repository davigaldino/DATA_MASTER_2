# 📁 Arquivos Não Utilizados

Esta pasta contém arquivos que foram identificados como não utilizados na aplicação principal, mas que podem ser úteis para referência futura ou desenvolvimento.

## 📋 Estrutura

```
nao_utilizados/
├── scripts/                    # Scripts de teste e desenvolvimento
│   ├── check_csv.py           # Verificação de arquivos CSV
│   ├── check_etl_status.py    # Verificação de status ETL
│   ├── check_schema.py        # Verificação de schema do banco
│   ├── check_tickers.py       # Verificação de tickers
│   ├── test_api.py            # Teste da API
│   ├── test_api_simple.py     # Teste simples da API
│   ├── test_db_status.py      # Teste de status do banco
│   └── test_django_db.py      # Teste do banco Django
├── etl/                       # Módulos ETL não utilizados
│   ├── extractors/
│   │   ├── streaming_extractor.py  # Extrator de streaming
│   │   └── yfinance_extractor.py   # Extrator YFinance
│   └── loaders/
│       └── mongodb_loader.py       # Loader MongoDB
├── test_small.csv             # Arquivo de dados pequeno para teste
├── EXEMPLO_USO.md             # Exemplo de uso da aplicação
├── GUIA_APRESENTACAO.md       # Guia para apresentação
└── GUIA_REPRODUCAO.md         # Guia de reprodução
```

## 🔍 Descrição dos Arquivos

### Scripts de Teste
- **check_*.py**: Scripts para verificação de diferentes aspectos da aplicação
- **test_*.py**: Scripts para testes de funcionalidades específicas

### Módulos ETL
- **streaming_extractor.py**: Extrator para dados em streaming (não implementado)
- **yfinance_extractor.py**: Extrator para dados do Yahoo Finance (não implementado)
- **mongodb_loader.py**: Loader para MongoDB (não utilizado)

### Dados e Documentação
- **test_small.csv**: Arquivo pequeno para testes rápidos
- **Documentação**: Guias e exemplos de uso

## ⚠️ Importante

Estes arquivos foram movidos para esta pasta para manter a aplicação principal limpa, mas podem ser úteis para:
- Desenvolvimento futuro
- Referência de implementação
- Testes específicos
- Documentação adicional

## 🔄 Como Restaurar

Para restaurar qualquer arquivo, simplesmente mova-o de volta para sua localização original na estrutura do projeto. 