
from connection import get_spark
from pyspark.sql import functions as F


def executar_silver(spark):

    print("Iniciando camada Silver...")

    spark.sql("""
        CREATE SCHEMA IF NOT EXISTS
        workspace.bcb_silver
    """)

    # Leitura da camada Bronze

    bronze = spark.table(
        "workspace.bcb_bronze.sgs_raw"
    )

    total_bronze = bronze.count()

    # Conversao dos tipos de dados

    tratado = (
        bronze
        .withColumn(
            "data",
            F.expr(
                "CAST(try_to_timestamp(data_raw, 'dd/MM/yyyy') AS DATE)"
            )
        )
        .withColumn(
            "valor",
            F.expr(
                "try_cast(valor_raw AS DECIMAL(18,6))"
            )
        )
        .withColumn(
            "extraido_em",
            F.expr("try_cast(extraido_em AS TIMESTAMP)")
        )
    )

    # Regras de qualidade

    tratado = tratado.withColumn(
        "motivo_rejeicao",
        F.when(
            F.col("codigo_serie").isNull(),
            "Codigo da serie invalido"
        )
        .when(
            F.col("data").isNull(),
            "Data invalida"
        )
        .when(
            F.col("valor").isNull(),
            "Valor invalido"
        )
        .when(
            F.col("extraido_em").isNull(),
            "Timestamp de extracao invalido"
        )
    )

    # Separacao dos registros

    rejeitados = tratado.filter(
        F.col("motivo_rejeicao").isNotNull()
    )

    validos = tratado.filter(
        F.col("motivo_rejeicao").isNull()
    )

    # Identificacao de valores conflitantes

    conflitos = (
        validos
        .groupBy("codigo_serie", "data")
        .agg(
            F.countDistinct("valor").alias("valores_distintos")
        )
        .filter(F.col("valores_distintos") > 1)
    )

    if conflitos.count() > 0:
        raise ValueError(
            "Valores conflitantes para a mesma serie e data"
        )

    # Remocao de duplicidades

    silver = (
        validos
        .dropDuplicates(["codigo_serie", "data"])
        .select(
            "codigo_serie",
            "indicador",
            "frequencia",
            "unidade",
            "data",
            "valor",
            "fonte",
            "extraido_em"
        )
    )

    # Metricas de qualidade

    total_validos = silver.count()
    total_rejeitados = rejeitados.count()

    duplicados = (
        total_bronze
        - total_validos
        - total_rejeitados
    )

    if total_validos == 0:
        raise ValueError("Camada Silver vazia")

    # Persistencia dos registros rejeitados

    (
        rejeitados.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(
            "workspace.bcb_silver.data_quality"
        )
    )

    # Persistencia da camada Silver

    (
        silver.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(
            "workspace.bcb_silver.economic_indicators"
        )
    )

    # Relatorio de processamento

    print("\nRELATORIO DE QUALIDADE")
    print("-" * 40)

    print(f"Registros Bronze: {total_bronze}")
    print(f"Registros Silver: {total_validos}")
    print(f"Registros rejeitados: {total_rejeitados}")
    print(f"Duplicidades removidas: {duplicados}")

    qualidade = total_validos / total_bronze * 100

    print(f"Taxa de aproveitamento: {qualidade:.2f}%")

    print("\nSchema da camada Silver:")

    silver.printSchema()

    silver.show(5, truncate=False)

    print("\nCamada Silver concluida!")


if __name__ == "__main__":

    spark = get_spark()

    try:
        executar_silver(spark)
    finally:
        spark.stop()
