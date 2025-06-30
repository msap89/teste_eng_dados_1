# Teste Prático - Engenharia de Dados

## Proposta

Este repositório contém a solução da **Etapa 1 - ETL** do desafio técnico de Engenharia de Dados, com foco em:

- Transformações utilizando PySpark
- Simulação de um Data Lake com camadas Raw, Bronze e Silver
- Particionamento físico por data de processamento
- Escrita em formato Delta Lake
- Deduplicação e tratamento de dados com regras de negócio
- Práticas modernas como Merge (CDC)

---

## Tecnologias Utilizadas

- Databricks Community Edition
- Apache Spark (PySpark)
- Delta Lake
- DBFS (Databricks File System)

---

## Simulação de Infraestrutura AWS

Como o ambiente real da AWS (com Glue, S3 e IAM) não estava disponível neste cenário, utilizei o **Databricks Community Edition** como plataforma de execução. Abaixo, explico como cada item foi adaptado:

| Componente | Equivalente na Solução |
|------------|-------------------------|
| S3 Buckets (`bronze`, `silver`, `raw`) | DBFS: `dbfs:/mnt/bucket-...` |
| Glue Data Catalog | Metastore do Databricks (com `CREATE TABLE ... USING DELTA`) |
| Glue Partitioning (partição lógica) | Particionamento Delta gerenciado automaticamente |
| Glue Job | Script único de ETL em PySpark |
| Athena para leitura | Notebooks Spark para visualização |

---

## Lógica de Particionamento

A coluna `anomesdia` foi criada dinamicamente usando a data de processamento (`current_date()`), no formato `yyyyMMdd`. Essa coluna foi utilizada como **partição física** tanto na Bronze quanto na Silver.

> Como o Delta Lake gerencia automaticamente os metadados de partição, não é necessário (nem permitido) usar comandos como `MSCK REPAIR TABLE`. Ao registrar a tabela com `CREATE TABLE USING DELTA LOCATION`, o particionamento é reconhecido e mantido.

---

## Etapa 1 - ETL (Detalhada)

### Input
- Arquivo CSV: `clientes_sinteticos.csv`
- Estrutura e tipos foram definidos com `StructType` e `StructField`

### Transformações

- Leitura com schema explícito
- Criação da coluna `anomesdia`
- Conversão do nome dos clientes para caixa alta (`upper`)
- Renomeio da coluna `telefone_cliente` → `num_telefone_cliente`
- Aplicação de regex para manter somente números no formato: **(NN)NNNNN-NNNN** — inválidos são tratados como `null`
- Deduplicação com `Window` para manter somente o registro mais recente por `cod_cliente`

### Output

- **Bronze:** 
  - Formato: Parquet
  - Particionado por `anomesdia`
  - Local: `dbfs:/mnt/bucket-bronze/tabela_cliente_landing`

- **Silver:** 
  - Formato: Delta Lake
  - Lógica de CDC com `merge` incremental usando `cod_cliente`
  - Particionado por `anomesdia`
  - Local: `dbfs:/mnt/bucket-silver/tb_cliente`

### Observações Técnicas

- A escrita no formato Delta permite que as atualizações na camada Silver simulem comportamentos reais de CDC (Change Data Capture), semelhantes ao uso do Glue Jobs com Update em tabelas Delta no S3.
- O código foi implementado como **um único script sequencial**, conforme exigido no desafio.
- O uso do metastore do Databricks com `CREATE TABLE USING DELTA LOCATION` substitui o comportamento do Glue Data Catalog neste ambiente simulado.

---

## Estrutura de Pastas

```bash
├── 1.ETL/
   └── script_etl.py           # Código PySpark com toda a lógica de Bronze e Silver
```
# Etapa 2 – Análise de Dados

## Introdução

Este documento apresenta os resultados da análise realizada sobre o arquivo `clientes_sinteticos.csv`, utilizando as camadas Bronze e Silver do Data Lake.  

Foram analisados:  
- Os clientes que mais sofreram atualizações na base (utilizando a camada Bronze, que mantém o histórico completo).  
- A média de idade dos clientes (utilizando a camada Silver, com dados tratados e deduplicados).

---

## Resultados

### 1. Top 5 clientes com mais atualizações (a partir da Bronze):

| cod_cliente | count |   nm_cliente     |
|-------------|-------|------------------|
| 479         | 5     | JASMINE BAUTISTA |
| 396         | 5     | SARAH ALLEN      |
| 878         | 5     | JENNIFER JARVIS  |
| 855         | 4     | DAVID PETERS     |
| 925         | 3     | CHRISTIAN GATES  |

Observa-se que os clientes com IDs 479, 396 e 878 são os que mais tiveram registros atualizados na base, indicando maior movimentação ou revisões de cadastro.

---

### 2. Média de idade dos clientes (a partir da Silver):

| media_idade |
|-------------|
| 51.15       |

A média de idade foi calculada considerando a diferença entre a data atual e a data de nascimento (`dt_nascimento_cliente`). O valor indica um perfil de clientes com idade média de aproximadamente 51 anos.

---

## Considerações Finais

- Todo o processamento foi realizado em PySpark.  
- Esses resultados contribuem para uma melhor compreensão do comportamento da base de clientes e podem orientar decisões estratégicas futuras.

## 3. Desenho de Arquitetura
#### Descrição

A arquitetura proposta visa capturar dados de cadastros de clientes hospedados em um banco **RDS MySQL**, realizar **CDC (Change Data Capture)** e armazená-los em um **Data Lake** estruturado no padrão **Medalhão (Bronze, Silver e Gold)**.

---

#### Arquitetura Proposta
![image](https://github.com/user-attachments/assets/0c5980df-2276-4ffb-8d64-7febd3d58fe9)

#### Componentes e Fluxo

- **RDS MySQL**: origem dos dados transacionais.
- **AWS DMS**: realiza CDC no banco MySQL e envia alterações para o Kinesis Data Streams.
- **Kinesis Data Streams**: entrega eventos em tempo real para processamento.
- **AWS Glue Streaming ETL**: consome os dados do Kinesis e realiza transformações mínimas, gravando na camada **Bronze**.
- **Camada Bronze (S3)**: armazena os dados brutos com histórico completo.
- **Athena**: permite análises exploratórias diretamente sobre os dados brutos da Bronze.
- **AWS Glue Batch ETL**: transforma e limpa os dados da Bronze para Silver, e da Silver para Gold.
  - **Silver**: dados deduplicados, validados e normalizados.
  - **Gold**: dados agregados e modelados para consumo analítico.
- **Amazon QuickSight**: ferramenta de visualização conectada diretamente à camada Gold.
- **Governança com Lake Formation + Glue Data Catalog**:
  - **Lake Formation** gerencia permissões de acesso a dados no nível de usuário e coluna.
  - **Glue Data Catalog** armazena os metadados de todas as tabelas do lake.

---

#### Benefícios

- Arquitetura escalável, segura e real-time.
- Segregação clara de responsabilidades por camada (Medalhão).
- Governança completa com controle de acesso e catalogação.
- Permite tanto exploração ad-hoc quanto painéis analíticos empresariais.

---

## 4. Validação de Qualidade dos Dados (Data Quality)

A qualidade dos dados é fundamental para garantir a confiabilidade das análises e decisões derivadas do dataset de clientes. Nesta etapa, foi implementada a função `data_quality` que realiza validações importantes na camada Silver, como:

- Verificação de valores nulos em colunas críticas (`cod_cliente`, `nm_cliente`, `dt_nascimento_cliente`, `dt_atualizacao`).
- Detecção de clientes duplicados pelo código do cliente.
- Identificação de valores negativos na coluna de renda.
- Validação dos valores permitidos na coluna `tp_pessoa` (apenas "PF" ou "PJ").

A função retorna um dicionário com indicadores booleanos que refletem o status da qualidade dos dados.

## 5. Testes Unitários

Para garantir a robustez da função de validação, foi desenvolvida uma suíte de testes unitários utilizando a biblioteca `pytest`. Os testes cobrem cenários positivos (dados válidos) e negativos (dados com problemas), assegurando que a função `data_quality` se comporte conforme esperado.

A abordagem facilita a manutenção futura, possibilita integração com pipelines de CI/CD e contribui para a entrega de um pipeline confiável e de alta qualidade.

