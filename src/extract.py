
import json
import requests

from pathlib import Path
from datetime import datetime, timezone, date
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_PATH = BASE_DIR / "config" / "series.json"

BASE_URL = "https://api.bcb.gov.br/dados/serie"


def carregar_configuracao():
    with open(CONFIG_PATH, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def criar_sessao():
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    session = requests.Session()

    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry)
    )

    return session


def extrair_serie(session, serie, data_inicial, data_final):

    codigo = serie["codigo"]

    url = f"{BASE_URL}/bcdata.sgs.{codigo}/dados"

    params = {
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final
    }

    response = session.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    dados = response.json()

    if not isinstance(dados, list) or not dados:
        raise ValueError(f"Resposta inválida ou vazia: SGS {codigo}")

    extraido_em = datetime.now(
        timezone.utc
    ).isoformat()

    registros = []

    for item in dados:

        registros.append({
            "codigo_serie": codigo,
            "indicador": serie["nome"],
            "frequencia": serie["frequencia"],
            "unidade": serie["unidade"],
            "data_raw": item["data"],
            "valor_raw": item["valor"],
            "fonte": url,
            "extraido_em": extraido_em
        })

    return registros


def extrair_todas_series():

    config = carregar_configuracao()

    data_inicial = config["data_inicial"]

    data_final = date.today().strftime("%d/%m/%Y")

    registros = []

    with criar_sessao() as session:

        for serie in config["series"]:

            dados = extrair_serie(
                session,
                serie,
                data_inicial,
                data_final
            )

            registros.extend(dados)

            print(
                f'{serie["nome"]}: '
                f'{len(dados)} registros extraídos'
            )

    return registros


if __name__ == "__main__":

    dados = extrair_todas_series()

    print(f"\nTotal de registros: {len(dados)}")

    print("\nPrimeiro registro:")
    print(json.dumps(
        dados[0],
        indent=4,
        ensure_ascii=False
    ))
