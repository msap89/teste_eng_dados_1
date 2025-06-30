# Databricks notebook source
pip install pytest --quiet

# COMMAND ----------

# MAGIC %run ../ETL/data_quality

# COMMAND ----------

import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[*]").appName("TestesQualidade").getOrCreate()

def test_valores_validos(spark):
    data = [
        (1, "Cliente A", "1990-01-01", "2024-01-01", "PF", 1000.0),
        (2, "Cliente B", "1985-05-05", "2024-01-01", "PJ", 3000.0)
    ]
    df = spark.createDataFrame(data, ["cod_cliente", "nm_cliente", "dt_nascimento_cliente", "dt_atualizacao", "tp_pessoa", "vl_renda"])

    result = data_quality(df)

    assert result["colunas_criticas_sem_nulos"]
    assert result["sem_duplicados"]
    assert result["renda_valida"]
    assert result["tp_pessoa_valida"]

def test_valores_invalidos(spark):
    data = [
        (1, None, None, "2024-01-01", "XX", -500.0),
        (1, "Cliente Repetido", "1990-01-01", None, "PJ", 2000.0)
    ]
    df = spark.createDataFrame(data, ["cod_cliente", "nm_cliente", "dt_nascimento_cliente", "dt_atualizacao", "tp_pessoa", "vl_renda"])

    result = data_quality(df)

    assert not result["colunas_criticas_sem_nulos"]
    assert not result["sem_duplicados"]
    assert not result["renda_valida"]
    assert not result["tp_pessoa_valida"]