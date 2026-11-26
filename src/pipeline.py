
import logging
from time import perf_counter

from connection import get_spark
from bronze import executar_bronze
from silver import executar_silver
from gold import executar_gold


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("bcb-pipeline")


def main():

    inicio = perf_counter()
    spark = None

    logger.info("Iniciando BCB Economic Lakehouse")

    try:

        spark = get_spark()

        etapas = [
            ("BRONZE", executar_bronze),
            ("SILVER", executar_silver),
            ("GOLD", executar_gold)
        ]

        for nome, executar in etapas:

            inicio_etapa = perf_counter()

            logger.info("Iniciando etapa %s", nome)

            executar(spark)

            duracao = perf_counter() - inicio_etapa

            logger.info(
                "Etapa %s concluida em %.2f segundos",
                nome,
                duracao
            )

        logger.info("Pipeline concluido com sucesso")

    except Exception:

        logger.exception("Falha durante a execucao do pipeline")

        raise

    finally:

        if spark is not None:
            spark.stop()

        logger.info(
            "Tempo total: %.2f segundos",
            perf_counter() - inicio
        )


if __name__ == "__main__":
    main()
