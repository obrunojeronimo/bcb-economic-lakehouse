
from unittest.mock import Mock

import pytest

from src.extract import (
    carregar_configuracao,
    extrair_serie
)


SERIE = {
    "codigo": 433,
    "nome": "ipca",
    "frequencia": "mensal",
    "unidade": "% a.m."
}


def test_configuracao():

    config = carregar_configuracao()

    assert len(config["series"]) >= 5

    codigos = [
        s["codigo"]
        for s in config["series"]
    ]

    assert len(codigos) == len(set(codigos))


def test_extracao_valida():

    session = Mock()

    session.get.return_value.json.return_value = [
        {
            "data": "01/01/2020",
            "valor": "0.21"
        }
    ]

    dados = extrair_serie(
        session,
        SERIE,
        "01/01/2020",
        "31/01/2020"
    )

    assert len(dados) == 1
    assert dados[0]["codigo_serie"] == 433
    assert dados[0]["valor_raw"] == "0.21"
    assert dados[0]["data_raw"] == "01/01/2020"
    assert "extraido_em" in dados[0]
    assert "fonte" in dados[0]


def test_resposta_vazia():

    session = Mock()

    session.get.return_value.json.return_value = []

    with pytest.raises(ValueError):

        extrair_serie(
            session,
            SERIE,
            "01/01/2020",
            "31/01/2020"
        )


def test_preservacao_valor_negativo():

    session = Mock()

    session.get.return_value.json.return_value = [
        {
            "data": "01/01/2020",
            "valor": "-0.32"
        }
    ]

    dados = extrair_serie(
        session,
        SERIE,
        "01/01/2020",
        "31/01/2020"
    )

    assert dados[0]["valor_raw"] == "-0.32"
