"""Criação da sessão remota do Databricks Connect."""

from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession


def get_spark() -> SparkSession:
    """Obtém uma sessão serverless usando o perfil local DEFAULT."""
    return DatabricksSession.builder.serverless().profile("DEFAULT").getOrCreate()


if __name__ == "__main__":
    spark_session = get_spark()

    try:
        print("Catálogos disponíveis:")
        spark_session.sql("SHOW CATALOGS").show()

        print("Teste de processamento remoto:")
        spark_session.range(5).show()
    finally:
        spark_session.stop()
