"""Extração das séries temporais da API SGS do Banco Central."""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol, TypedDict, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_PATH = BASE_DIR / "config" / "series.json"

BASE_URL = "https://api.bcb.gov.br/dados/serie"


class SerieConfig(TypedDict):
    """Metadados de uma série conforme config/series.json."""

    codigo: int
    nome: str
    frequencia: str
    unidade: str


class ExtractConfig(TypedDict):
    """Intervalo inicial e séries configuradas para extração."""

    data_inicial: str
    series: list[SerieConfig]


class RegistroBruto(TypedDict):
    """Registro no formato esperado pelo schema da camada Bronze."""

    codigo_serie: int
    indicador: str
    frequencia: str
    unidade: str
    data_raw: str
    valor_raw: str
    fonte: str
    extraido_em: str


class RespostaSGS(Protocol):
    """Operações da resposta HTTP usadas pela extração."""

    def raise_for_status(self) -> None:
        """Propaga falhas HTTP antes de ler os dados."""
        ...

    def json(self) -> object:
        """Retorna o conteúdo JSON recebido da API."""
        ...


class SessaoSGS(Protocol):
    """Operações de consulta e ciclo de vida da sessão HTTP SGS."""

    def get(self, url: str, *, params: dict[str, str], timeout: int) -> RespostaSGS:
        """Consulta uma série com parâmetros e timeout definidos."""
        ...

    def close(self) -> None:
        """Libera os recursos da sessão HTTP."""
        ...


def carregar_configuracao() -> ExtractConfig:
    """Lê a configuração de séries localizada na raiz do projeto."""
    with CONFIG_PATH.open(encoding="utf-8") as arquivo:
        return cast(ExtractConfig, json.load(arquivo))


def criar_sessao() -> requests.Session:
    """Cria uma sessão HTTP com retry para falhas transitórias do SGS."""
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    session = requests.Session()

    session.mount("https://", HTTPAdapter(max_retries=retry))

    return session


def extrair_serie(
    session: SessaoSGS,
    serie: SerieConfig,
    data_inicial: str,
    data_final: str,
) -> list[RegistroBruto]:
    """Extrai uma série, preservando datas e valores como textos originais."""
    codigo = serie["codigo"]

    url = f"{BASE_URL}/bcdata.sgs.{codigo}/dados"

    params = {
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
    }

    response = session.get(url, params=params, timeout=60)

    response.raise_for_status()

    dados = response.json()

    if not isinstance(dados, list) or not dados:
        raise ValueError(f"Resposta inválida ou vazia: SGS {codigo}")

    extraido_em = datetime.now(timezone.utc).isoformat()

    registros: list[RegistroBruto] = []

    for item in cast(list[dict[str, str]], dados):
        registros.append(
            {
                "codigo_serie": codigo,
                "indicador": serie["nome"],
                "frequencia": serie["frequencia"],
                "unidade": serie["unidade"],
                "data_raw": item["data"],
                "valor_raw": item["valor"],
                "fonte": url,
                "extraido_em": extraido_em,
            }
        )

    return registros


def extrair_todas_series() -> list[RegistroBruto]:
    """Extrai todas as séries configuradas desde a data inicial até hoje."""
    config = carregar_configuracao()

    data_inicial = config["data_inicial"]

    data_final = date.today().strftime("%d/%m/%Y")

    registros: list[RegistroBruto] = []

    with criar_sessao() as session:
        for serie in config["series"]:
            dados = extrair_serie(session, serie, data_inicial, data_final)

            registros.extend(dados)

            print(f"{serie['nome']}: {len(dados)} registros extraídos")

    return registros


if __name__ == "__main__":
    registros_extraidos = extrair_todas_series()

    print(f"\nTotal de registros: {len(registros_extraidos)}")

    print("\nPrimeiro registro:")
    print(
        json.dumps(
            registros_extraidos[0],
            indent=4,
            ensure_ascii=False,
        )
    )
