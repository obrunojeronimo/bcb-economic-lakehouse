
from connection import get_spark
from extract import extrair_todas_series


def executar_bronze(spark):

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

    spark.sql("""
        CREATE SCHEMA IF NOT EXISTS
        workspace.bcb_bronze
    """)

    (
        df.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(
            "workspace.bcb_bronze.sgs_raw"
        )
    )

    tabela = spark.table(
        "workspace.bcb_bronze.sgs_raw"
    )

    print(f"Registros armazenados: {tabela.count()}")

    tabela.show(5, truncate=False)


if __name__ == "__main__":

    spark = get_spark()

    try:
        executar_bronze(spark)
    finally:
        spark.stop()
