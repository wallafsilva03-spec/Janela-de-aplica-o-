"""Diagnóstico da ClimAPI: descobre os códigos de variável e o formato do endpoint.

Roda no GitHub Actions (onde a API é acessível) e imprime:
  - status e corpo do GET /ncep-gfs (lista de variáveis disponíveis);
  - testes de algumas estruturas de URL candidatas para uma variável.

Não imprime o token nem as chaves. Uso temporário para acertar a config.
"""
from __future__ import annotations

import json

import requests

from . import config
from .embrapa_client import EmbrapaClimAPI


def _tenta(cliente: EmbrapaClimAPI, caminho: str) -> None:
    url = f"{config.BASE_URL}{caminho}"
    try:
        r = cliente._sessao.get(
            url,
            headers={"Authorization": f"Bearer {cliente.autenticar()}"},
            timeout=60,
        )
        corpo = r.text[:600].replace("\n", " ")
        print(f"[{r.status_code}] GET {caminho}\n        -> {corpo}\n")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] GET {caminho} -> {type(e).__name__}: {e}\n")


def main() -> None:
    cliente = EmbrapaClimAPI()
    print("=== Autenticando ===")
    try:
        cliente.autenticar()
        print("Token obtido com sucesso.\n")
    except Exception as e:  # noqa: BLE001
        print(f"Falha na autenticação: {type(e).__name__}: {e}")
        return

    print("=== Lista de recursos/variáveis (GET /ncep-gfs) ===")
    _tenta(cliente, "/ncep-gfs")

    # Ponto de Ribeirão Preto para os testes.
    lon, lat = -47.8103, -21.1775

    print("=== Testando estruturas de URL candidatas ===")
    # Descobrimos os códigos de variável a partir da resposta de /ncep-gfs;
    # por ora testamos alguns candidatos comuns e as duas ordens de coordenada.
    candidatos_var = ["tmp2m", "tmax", "tmin", "tmed", "temperatura", "temp",
                       "t2m", "tmpsfc", "ur", "umidade"]
    for var in candidatos_var:
        _tenta(cliente, f"/ncep-gfs/{var}/{lon}/{lat}")   # var / lon / lat
    # ordem alternativa lat/lon com a primeira candidata
    _tenta(cliente, f"/ncep-gfs/tmp2m/{lat}/{lon}")
    # sufixo de recurso alternativo
    _tenta(cliente, "/ncep-gfs/variaveis")
    _tenta(cliente, "/ncep-gfs/variables")


if __name__ == "__main__":
    main()
