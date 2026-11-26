"""Testes unitários da configuração e extração da API SGS."""

from dataclasses import dataclass

import pytest

from src.extract import SerieConfig, carregar_configuracao, extrair_serie

SERIE: SerieConfig = {
    "codigo": 433,
    "nome": "ipca",
    "frequencia": "mensal",
    "unidade": "% a.m.",
}


@dataclass
class RespostaFalsa:
    """Resposta HTTP mínima para os testes de extração."""

    dados: list[dict[str, str]]

    def raise_for_status(self) -> None:
        """Simula uma resposta HTTP bem sucedida."""

    def json(self) -> object:
        """Devolve as observações configuradas pelo teste."""
        return self.dados


@dataclass
class SessaoFalsa:
    """Sessão que confirma os parâmetros usados na chamada SGS."""

    resposta: RespostaFalsa

    def get(self, url: str, *, params: dict[str, str], timeout: int) -> RespostaFalsa:
        """Confere a chamada e retorna a resposta preparada."""
        assert url.endswith("/bcdata.sgs.433/dados")
        assert params["formato"] == "json"
        assert timeout == 60
        return self.resposta

    def close(self) -> None:
        """Simula o encerramento da sessão HTTP."""


def test_configuracao() -> None:
    """Confere a presença de cinco séries com códigos únicos."""
    config = carregar_configuracao()

    assert len(config["series"]) >= 5

    codigos = [s["codigo"] for s in config["series"]]

    assert len(codigos) == len(set(codigos))


def test_extracao_valida() -> None:
    """Confere os campos preservados da resposta HTTP simulada."""
    session = SessaoFalsa(RespostaFalsa([{"data": "01/01/2020", "valor": "0.21"}]))

    dados = extrair_serie(session, SERIE, "01/01/2020", "31/01/2020")

    assert len(dados) == 1
    assert dados[0]["codigo_serie"] == 433
    assert dados[0]["valor_raw"] == "0.21"
    assert dados[0]["data_raw"] == "01/01/2020"
    assert "extraido_em" in dados[0]
    assert "fonte" in dados[0]


def test_resposta_vazia() -> None:
    """Uma resposta sem observações deve interromper a extração."""
    session = SessaoFalsa(RespostaFalsa([]))

    with pytest.raises(ValueError):
        _ = extrair_serie(session, SERIE, "01/01/2020", "31/01/2020")


def test_preservacao_valor_negativo() -> None:
    """Valores negativos devem continuar no formato original da API."""
    session = SessaoFalsa(RespostaFalsa([{"data": "01/01/2020", "valor": "-0.32"}]))

    dados = extrair_serie(session, SERIE, "01/01/2020", "31/01/2020")

    assert dados[0]["valor_raw"] == "-0.32"
