# Databricks notebook source
def data_quality(df_final):
    from pyspark.sql.functions import col, count, when

    resultado = {}

    colunas_criticas = ["cod_cliente", "nm_cliente", "dt_nascimento_cliente", "dt_atualizacao"]
    null_counts = df_final.select([
        count(when(col(c).isNull(), c)).alias(c) for c in colunas_criticas
    ]).collect()[0].asDict()
    resultado["colunas_criticas_sem_nulos"] = all(v == 0 for v in null_counts.values())

    duplicados = (
        df_final.groupBy("cod_cliente")
        .count()
        .filter(col("count") > 1)
        .count()
    )
    resultado["sem_duplicados"] = duplicados == 0

    renda_negativa = df_final.filter(col("vl_renda") < 0).count()
    resultado["renda_valida"] = renda_negativa == 0

    tp_pessoa_invalido = df_final.filter(~col("tp_pessoa").isin("PF", "PJ")).count()
    resultado["tp_pessoa_valida"] = tp_pessoa_invalido == 0

    return resultado