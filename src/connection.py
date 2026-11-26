from databricks.connect import DatabricksSession


def get_spark():
    return (
        DatabricksSession.builder
        .serverless()
        .profile("DEFAULT")
        .getOrCreate()
    )


if __name__ == "__main__":

    spark = get_spark()

    print("Catálogos disponíveis:")
    spark.sql("SHOW CATALOGS").show()

    print("Teste de processamento remoto:")
    spark.range(5).show()