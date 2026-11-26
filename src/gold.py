
from connection import get_spark
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def executar_gold(spark):

    print("Iniciando camada Gold...")

    spark.sql("""
        CREATE SCHEMA IF NOT EXISTS
        workspace.bcb_gold
    """)

    silver = spark.table(
        "workspace.bcb_silver.economic_indicators"
    )

    # 1. Consolidacao mensal dos indicadores

    mensal = (
        silver
        .withColumn(
            "mes",
            F.trunc("data", "month")
        )
        .groupBy(
            "mes",
            "codigo_serie",
            "indicador",
            "unidade",
            "frequencia"
        )
        .agg(
            F.round(
                F.avg("valor"), 6
            ).alias("valor_medio"),

            F.min("valor").alias("valor_minimo"),

            F.max("valor").alias("valor_maximo"),

            F.max_by(
                "valor", "data"
            ).alias("ultimo_valor"),

            F.max("data").alias("ultima_observacao"),

            F.count("*").alias("observacoes")
        )
    )

    # 2. Ultima observacao de cada indicador

    janela = (
        Window
        .partitionBy("codigo_serie")
        .orderBy(F.col("data").desc())
    )

    recentes = (
        silver
        .withColumn(
            "rn",
            F.row_number().over(janela)
        )
        .filter(F.col("rn") == 1)
        .drop("rn")
    )

    # 3. Base mensal para analises estatisticas

    features = (
        mensal
        .groupBy("mes")
        .agg(

            F.max(
                F.when(
                    F.col("codigo_serie") == 432,
                    F.col("ultimo_valor")
                )
            ).alias("meta_selic"),

            F.max(
                F.when(
                    F.col("codigo_serie") == 433,
                    F.col("ultimo_valor")
                )
            ).alias("ipca_mensal"),

            F.max(
                F.when(
                    F.col("codigo_serie") == 1,
                    F.col("valor_medio")
                )
            ).alias("dolar_medio"),

            F.max(
                F.when(
                    F.col("codigo_serie") == 4390,
                    F.col("ultimo_valor")
                )
            ).alias("selic_mensal"),

            F.max(
                F.when(
                    F.col("codigo_serie") == 13522,
                    F.col("ultimo_valor")
                )
            ).alias("ipca_12_meses")

        )
        .withColumn("ano", F.year("mes"))
        .withColumn("mes_numero", F.month("mes"))
    )

    # 4. Persistencia das tabelas Delta

    tabelas = {
        "monthly_indicators": mensal,
        "latest_indicators": recentes,
        "economic_features": features
    }

    for nome, dataframe in tabelas.items():

        destino = f"workspace.bcb_gold.{nome}"

        (
            dataframe.write
            .format("delta")
            .mode("overwrite")
            .saveAsTable(destino)
        )

        print(
            f"{nome}: "
            f"{spark.table(destino).count()} registros"
        )

    # 5. Validacao dos resultados

    print("\nULTIMOS INDICADORES ECONOMICOS")

    recentes.select(
        "indicador",
        "data",
        "valor",
        "unidade"
    ).orderBy("indicador").show(truncate=False)

    print("\nBASE MENSAL PARA CIENCIA DE DADOS")

    features.orderBy(
        F.col("mes").desc()
    ).show(10, truncate=False)

    print("\nCamada Gold concluida!")


if __name__ == "__main__":

    spark = get_spark()

    try:
        executar_gold(spark)
    finally:
        spark.stop()
