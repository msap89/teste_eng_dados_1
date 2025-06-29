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
│   ├── script_etl.py           # Código PySpark com toda a lógica de Bronze e Silver
