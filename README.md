# Teste Prático – Engenharia de Dados

Este repositório contém a resolução do desafio prático de Engenharia de Dados, com foco em:

- Desenvolvimento de pipelines com PySpark
- Organização de dados em um Data Lake com arquitetura em camadas (Medalhão)
- Validação de qualidade dos dados
- Testes unitários
- Infraestrutura como código (IaC) com Terraform

---

## Ambiente de Execução

Para simulação da infraestrutura AWS, utilizei o **Databricks Community Edition**, com os seguintes componentes:

| Componente AWS            | Equivalente na Solução             |
|---------------------------|-------------------------------------|
| S3 Buckets (Bronze/Silver)| DBFS com caminhos distintos         |
| Glue Data Catalog         | Metastore do Databricks             |
| Glue Jobs                 | Scripts em notebooks PySpark        |
| Glue Partições            | Partições Delta + `anomesdia`       |
| Athena                    | Acesso via notebooks Spark          |

---

## Estrutura de Pastas

```bash
├── 1.ETL/
│   └── script.py                  # Pipeline de ingestão, limpeza e escrita em Bronze/Silver
├── 2.AnaliseDados/
│   ├── analise.txt                # Top 5 clientes com mais atualizações + média de idade
│   └── analise_dados.py           # Código com as consultas
├── 3.DesenhodeArquitetura/
│   ├── desenho.jpg                # Diagrama da arquitetura AWS CDC com Data Lake
│   └── explicacao.txt             # Justificativa e descrição dos componentes usados
├── 4.DataQuality/
│   └── script_data_quality.py     # Validações de nulos, duplicidade, valores válidos
├── 5.TesteUnitario/
│   ├── unit_test.py               # Testes Pytest para função de qualidade dos dados
│   └── resultados.txt             # Log da execução dos testes
└── 6.InfraAsCode/
    └── script.tf                  # Script Terraform para criação de Glue Job
