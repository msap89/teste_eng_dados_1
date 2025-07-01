# Databricks notebook source
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, datediff, current_date

# COMMAND ----------

# ----------------------------------------------
# Análise 1 - Top 5 clientes com mais atualizações
# ----------------------------------------------

# Usar camada Bronze (possui histórico completo)
df_bronze = spark.read.parquet("dbfs:/mnt/bucket-bronze/tabela_cliente_landing")

# COMMAND ----------

top_5 = (
    df_bronze.groupBy("cod_cliente")
    .count()
    .orderBy(col("count").desc())
    .limit(5)
)

# COMMAND ----------

display(top_5)

# COMMAND ----------

# ----------------------------------------------
# Análise 2 - Média de idade dos clientes
# ----------------------------------------------

df_silver = spark.read.format("delta").load("dbfs:/mnt/bucket-silver/tb_cliente")

# COMMAND ----------

df_idade = df_silver.withColumn(
    "idade", 
    datediff(current_date(), col("dt_nascimento_cliente")) / 365.25
)

media_idade = df_idade.agg(avg("idade").alias("media_idade"))

# COMMAND ----------

display(media_idade)
