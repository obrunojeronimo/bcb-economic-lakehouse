"""Testes da ordem das camadas e do encerramento da sessão Spark."""

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from src import pipeline


@dataclass
class SparkFalso:
    """Sessão mínima que registra se o pipeline a encerrou."""

    encerrado: bool = False

    def stop(self) -> None:
        """Registra a liberação da sessão."""
        self.encerrado = True


def _registrar(
    nome: str, chamadas: list[tuple[str, object]]
) -> Callable[[object], None]:
    """Cria uma etapa falsa que registra ordem e identidade da sessão."""

    def executar(spark: object) -> None:
        """Registra uma chamada da etapa."""
        chamadas.append((nome, spark))

    return executar


def test_pipeline_executa_camadas_em_ordem(monkeypatch: pytest.MonkeyPatch) -> None:
    """A orquestração deve executar Bronze, Silver e Gold na mesma sessão."""
    spark = SparkFalso()
    chamadas: list[tuple[str, object]] = []
    monkeypatch.setattr(pipeline, "get_spark", Mock(return_value=spark))
    monkeypatch.setattr(pipeline, "executar_bronze", _registrar("BRONZE", chamadas))
    monkeypatch.setattr(pipeline, "executar_silver", _registrar("SILVER", chamadas))
    monkeypatch.setattr(pipeline, "executar_gold", _registrar("GOLD", chamadas))

    pipeline.main()

    assert chamadas == [
        ("BRONZE", spark),
        ("SILVER", spark),
        ("GOLD", spark),
    ]
    assert spark.encerrado


def test_pipeline_encerra_sessao_apos_falha(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uma falha na Silver deve ser propagada e impedir a etapa Gold."""
    spark = SparkFalso()
    chamadas: list[tuple[str, object]] = []

    def falhar_na_silver(sessao: object) -> None:
        """Simula uma falha após registrar a sessão usada pela Silver."""
        chamadas.append(("SILVER", sessao))
        raise ValueError("falha na Silver")

    monkeypatch.setattr(pipeline, "get_spark", Mock(return_value=spark))
    monkeypatch.setattr(pipeline, "executar_bronze", _registrar("BRONZE", chamadas))
    monkeypatch.setattr(pipeline, "executar_silver", falhar_na_silver)
    monkeypatch.setattr(pipeline, "executar_gold", _registrar("GOLD", chamadas))

    with pytest.raises(ValueError, match="falha na Silver"):
        pipeline.main()

    assert chamadas == [("BRONZE", spark), ("SILVER", spark)]
    assert spark.encerrado
