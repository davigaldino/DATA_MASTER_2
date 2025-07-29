# 🔒 Mascaramento de Dados - Data Masking

## 📋 Visão Geral

O mascaramento de dados é uma técnica fundamental de segurança da informação que protege dados sensíveis substituindo valores reais por dados fictícios ou criptografados, mantendo a estrutura e funcionalidade dos dados originais.

## 🎯 Objetivos do Mascaramento

### 1. **Proteção de Dados Sensíveis**
- Preservar a privacidade de informações pessoais
- Cumprir regulamentações (LGPD, GDPR, SOX)
- Reduzir riscos de vazamento de dados

### 2. **Ambientes de Desenvolvimento e Teste**
- Permitir desenvolvimento seguro com dados realistas
- Facilitar testes sem expor dados sensíveis
- Manter conformidade em ambientes não-produtivos

### 3. **Análise e Relatórios**
- Compartilhar insights sem expor dados originais
- Permitir demonstrações públicas
- Facilitar colaboração entre equipes

## 🛠️ Técnicas de Mascaramento

### 1. **Substituição (Substitution)**
```python
# Exemplo: Substituir nomes reais por nomes fictícios
original_data = ["João Silva", "Maria Santos", "Pedro Costa"]
masked_data = ["Carlos Oliveira", "Ana Pereira", "Lucas Ferreira"]
```

### 2. **Hashing**
```python
import hashlib

def hash_sensitive_data(data):
    """Aplica hash SHA-256 em dados sensíveis."""
    return hashlib.sha256(str(data).encode()).hexdigest()

# Exemplo
cpf_original = "123.456.789-00"
cpf_masked = hash_sensitive_data(cpf_original)
# Resultado: "a1b2c3d4e5f6..."
```

### 3. **Tokenização**
```python
import uuid

def tokenize_data(data):
    """Substitui dados por tokens únicos."""
    token_map = {}
    
    def get_token(value):
        if value not in token_map:
            token_map[value] = str(uuid.uuid4())
        return token_map[value]
    
    return [get_token(item) for item in data]

# Exemplo
emails_original = ["user1@company.com", "user2@company.com"]
emails_tokenized = tokenize_data(emails_original)
# Resultado: ["550e8400-e29b-41d4-a716-446655440000", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
```

### 4. **Anonimização**
```python
def anonymize_data(data, fields_to_anonymize):
    """Remove ou generaliza dados identificáveis."""
    anonymized = data.copy()
    
    for field in fields_to_anonymize:
        if field in anonymized:
            if field == 'age':
                # Generaliza idade para faixas
                age = anonymized[field]
                if age < 25:
                    anonymized[field] = "18-24"
                elif age < 35:
                    anonymized[field] = "25-34"
                else:
                    anonymized[field] = "35+"
            elif field == 'location':
                # Generaliza localização
                anonymized[field] = "Região"
            else:
                anonymized[field] = "***"
    
    return anonymized
```

### 5. **Criptografia**
```python
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data, key):
    """Criptografa dados sensíveis."""
    f = Fernet(key)
    return f.encrypt(str(data).encode()).decode()

def decrypt_sensitive_data(encrypted_data, key):
    """Descriptografa dados sensíveis."""
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
```

## 📊 Aplicação no Contexto de Dados Financeiros

### Dados Sensíveis em Mercado Financeiro

1. **Informações Pessoais**
   - CPF/CNPJ de investidores
   - Endereços residenciais
   - Números de telefone
   - Endereços de e-mail

2. **Dados de Transações**
   - Valores de investimentos
   - Histórico de operações
   - Saldos de contas
   - Informações bancárias

3. **Dados Corporativos**
   - Estratégias de trading
   - Posições de portfólio
   - Informações confidenciais de empresas

### Estratégias de Mascaramento para Dados Financeiros

```python
class FinancialDataMasker:
    """Mascarador específico para dados financeiros."""
    
    def __init__(self):
        self.name_mapping = {
            "João Silva": "Investidor A",
            "Maria Santos": "Investidor B",
            "Empresa XYZ": "Empresa Alpha"
        }
    
    def mask_investor_data(self, data):
        """Mascara dados de investidores."""
        masked = data.copy()
        
        # Mascara CPF/CNPJ
        if 'cpf' in masked:
            masked['cpf'] = f"***.***.***-{masked['cpf'][-2:]}"
        
        # Mascara nome
        if 'name' in masked:
            masked['name'] = self.name_mapping.get(masked['name'], "Investidor")
        
        # Mascara valores (mantém proporção)
        if 'investment_value' in masked:
            original_value = masked['investment_value']
            masked['investment_value'] = original_value * 0.1  # 10% do valor original
        
        return masked
    
    def mask_transaction_data(self, data):
        """Mascara dados de transações."""
        masked = data.copy()
        
        # Mascara valores mantendo proporções relativas
        if 'transaction_value' in masked:
            base_value = 1000  # Valor base para demonstração
            masked['transaction_value'] = base_value + (masked['transaction_value'] % 1000)
        
        # Mascara timestamps (mantém ordem cronológica)
        if 'timestamp' in masked:
            # Converte para data relativa
            masked['timestamp'] = f"2024-{masked['timestamp'][5:]}"
        
        return masked
```

## 🔧 Implementação no Projeto DATA_MASTER_2

### Estrutura de Mascaramento

```python
# etl/transformers/data_masking.py
import pandas as pd
import hashlib
import uuid
from typing import Dict, List, Any

class DataMasker:
    """Implementação de mascaramento de dados para o projeto."""
    
    def __init__(self, masking_config: Dict[str, Any]):
        self.config = masking_config
        self.token_map = {}
    
    def mask_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica mascaramento em um DataFrame."""
        masked_df = df.copy()
        
        for column, mask_type in self.config.items():
            if column in masked_df.columns:
                if mask_type == 'hash':
                    masked_df[column] = masked_df[column].apply(self._hash_value)
                elif mask_type == 'token':
                    masked_df[column] = masked_df[column].apply(self._tokenize_value)
                elif mask_type == 'anonymize':
                    masked_df[column] = masked_df[column].apply(self._anonymize_value)
        
        return masked_df
    
    def _hash_value(self, value):
        """Aplica hash SHA-256."""
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    
    def _tokenize_value(self, value):
        """Substitui por token único."""
        if value not in self.token_map:
            self.token_map[value] = str(uuid.uuid4())[:8]
        return self.token_map[value]
    
    def _anonymize_value(self, value):
        """Anonimiza valor."""
        return "***"
```

### Configuração de Mascaramento

```python
# Configuração para dados de ações (exemplo)
MASKING_CONFIG = {
    'investor_id': 'hash',
    'investor_name': 'token',
    'account_number': 'hash',
    'transaction_id': 'token',
    'sensitive_notes': 'anonymize'
}

# Aplicação no pipeline ETL
def apply_data_masking(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica mascaramento de dados no pipeline ETL."""
    masker = DataMasker(MASKING_CONFIG)
    return masker.mask_dataframe(df)
```

## 📋 Boas Práticas

### 1. **Consistência**
- Manter consistência entre ambientes
- Usar mapeamentos fixos para tokens
- Preservar relacionamentos entre dados

### 2. **Reversibilidade**
- Implementar mecanismos de reversão quando necessário
- Manter logs de mascaramento
- Documentar processos de desmascaramento

### 3. **Performance**
- Otimizar algoritmos de mascaramento
- Usar processamento em lotes
- Implementar cache para tokens

### 4. **Segurança**
- Proteger chaves de criptografia
- Implementar controle de acesso
- Auditar processos de mascaramento

## 🚀 Implementação Futura

### Roadmap de Mascaramento

1. **Fase 1: Mascaramento Básico**
   - Implementar técnicas básicas (hash, tokenização)
   - Configurar para dados de teste
   - Documentar processos

2. **Fase 2: Mascaramento Avançado**
   - Implementar criptografia
   - Adicionar anonimização
   - Criar interfaces de configuração

3. **Fase 3: Automação**
   - Integrar com pipeline ETL
   - Implementar detecção automática de dados sensíveis
   - Criar dashboards de monitoramento

### Integração com Observabilidade

```python
# Logs de mascaramento
logger.info("Aplicando mascaramento de dados", 
           records_processed=len(df),
           masking_rules=len(MASKING_CONFIG),
           sensitive_fields=list(MASKING_CONFIG.keys()))

# Métricas de mascaramento
metrics = {
    'records_masked': len(df),
    'fields_masked': len(MASKING_CONFIG),
    'masking_time_ms': processing_time,
    'masking_errors': error_count
}
```

## 📚 Referências

- [OWASP Data Masking](https://owasp.org/www-project-data-masking/)
- [NIST Guidelines for Data Masking](https://csrc.nist.gov/publications/detail/sp/800-188/final)
- [GDPR Data Protection](https://gdpr.eu/data-protection/)
- [LGPD - Lei Geral de Proteção de Dados](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

---

**Nota:** Esta documentação serve como referência para implementação de mascaramento de dados em projetos de Engenharia de Dados, garantindo conformidade com regulamentações e boas práticas de segurança. 