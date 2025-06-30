# Databricks notebook source

# MAGIC %run ../ETL/data_quality

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, regexp_extract, lit, date_format, row_number, current_date, when
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
from delta.tables import DeltaTable

# COMMAND ----------

# --------------------------------------
# Etapa Bronze (ler da Raw)
# --------------------------------------

# COMMAND ----------

schema = StructType([
    StructField("cod_cliente", IntegerType(), True)
    ,StructField("nm_cliente", StringType(), True)
    ,StructField("nm_pais_cliente", StringType(), True)
    ,StructField("nm_cidade_cliente", StringType(), True)
    ,StructField("nm_rua_cliente", StringType(), True)
    ,StructField("num_casa_cliente", IntegerType(), True)
    ,StructField("telefone_cliente", StringType(), True)
    ,StructField("dt_nascimento_cliente", DateType(), True)
    ,StructField("dt_atualizacao", DateType(), True)
    ,StructField("tp_pessoa", StringType(), True)
    ,StructField("vl_renda", DoubleType(), True)
])

# COMMAND ----------

df = (
    spark.read
    .option("header", "true")      
    .schema(schema)
    .option("delimiter", ",")
    .csv("dbfs:/mnt/bucket-raw/clientes/clientes_sinteticos.csv")
)

# COMMAND ----------

#adicionando coluna de partição 'anomesdia'
df = df.withColumn("anomesdia", date_format(current_date(), "yyyyMMdd"))

# COMMAND ----------

df.write \
    .partitionBy("anomesdia") \
    .mode("overwrite") \
    .parquet("dbfs:/mnt/bucket-bronze/tabela_cliente_landing")

# COMMAND ----------

# --------------------------------------
# Etapa Silver (ler da Bronze)
# --------------------------------------

df_bronze = spark.read.format("parquet").load("dbfs:/mnt/bucket-bronze/tabela_cliente_landing")

# COMMAND ----------

regex_pattern = r"^\(\d{2}\)\d{5}-\d{4}$"

df_bronze = (
    df_bronze.withColumnRenamed("telefone_cliente", "num_telefone_cliente")
             .withColumn("nm_cliente", upper(col("nm_cliente")))
             .withColumn(
                 "num_telefone_cliente",
                 when(col("num_telefone_cliente").rlike(regex_pattern), col("num_telefone_cliente"))
                 .otherwise(None)
             )
)


# COMMAND ----------

#remoção das dupplicatas
window_spec = Window.partitionBy("cod_cliente").orderBy(col("dt_atualizacao").desc())

df_final = (
    df_bronze.withColumn("row_number", row_number().over(window_spec))
             .filter(col("row_number") == 1)
             .drop("row_number")
)

# COMMAND ----------

#escrita no bucket (simulado) na silver
silver_path = "dbfs:/mnt/bucket-silver/tb_cliente"

#verifica se existe a tabela na silver
if DeltaTable.isDeltaTable(spark, silver_path):
    delta_table = DeltaTable.forPath(spark, silver_path)

    delta_table.alias("target").merge(
        source = df_final.alias("source"),
        condition="target.cod_cliente = source.cod_cliente"
    ).whenMatchedUpdate(
        condition = "source.dt_atualizacao > target.dt_atualizacao",
        set={
            "nm_cliente": "source.nm_cliente",
            "nm_pais_cliente": "source.nm_pais_cliente",
            "nm_cidade_cliente": "source.nm_cidade_cliente",
            "nm_rua_cliente": "source.nm_rua_cliente",
            "num_casa_cliente": "source.num_casa_cliente",
            "num_telefone_cliente": "source.num_telefone_cliente",
            "dt_nascimento_cliente": "source.dt_nascimento_cliente",
            "dt_atualizacao": "source.dt_atualizacao",
            "tp_pessoa": "source.tp_pessoa",
            "vl_renda": "source.vl_renda",
            "anomesdia": "source.anomesdia"
        }
    ).whenNotMatchedInsertAll()

else:
    df_final.write.format("delta").partitionBy("anomesdia").mode("overwrite").save(silver_path)

# COMMAND ----------

# --------------------------------------
# Validação da qualidade dos dados
# --------------------------------------
data_quality(df_final)

# COMMAND ----------

# --------------------------------------
# Registro da tabela e partição lógica
# --------------------------------------
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS default.tb_cliente
    USING DELTA
    LOCATION '{silver_path}'
""")
