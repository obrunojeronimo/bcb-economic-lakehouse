"""Ingestão das séries SGS na tabela Delta Bronze."""

from pyspark.sql import SparkSession

from .connection import get_spark
from .extract import extrair_todas_series


def executar_bronze(spark: SparkSession) -> None:
    """Extrai as séries e sobrescreve a tabela Bronze com os valores originais."""
    print("Iniciando camada Bronze...")

    registros = extrair_todas_series()

    schema = """
        codigo_serie INT,
        indicador STRING,
        frequencia STRING,
        unidade STRING,
        data_raw STRING,
        valor_raw STRING,
        fonte STRING,
        extraido_em STRING
    """

    df = spark.createDataFrame(registros, schema)

    _ = spark.sql("""
        CREATE SCHEMA IF NOT EXISTS
        workspace.bcb_bronze
    """)

    (
        df.write.format("delta")
        .mode("overwrite")
        .saveAsTable("workspace.bcb_bronze.sgs_raw")
    )

    tabela = spark.table("workspace.bcb_bronze.sgs_raw")

    print(f"Registros armazenados: {tabela.count()}")

    tabela.show(5, truncate=False)


if __name__ == "__main__":
    spark_session = get_spark()

    try:
        executar_bronze(spark_session)
    finally:
        spark_session.stop()
