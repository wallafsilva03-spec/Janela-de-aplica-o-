"""Diagnóstico da ClimAPI: descobre variáveis e o formato do endpoint de dados.

Roda no GitHub Actions (onde a API é acessível). Não imprime token/chaves.
"""
from __future__ import annotations

import json

from . import config
from .embrapa_client import EmbrapaClimAPI


def _get(cliente: EmbrapaClimAPI, caminho: str, limite: int = 700) -> None:
    url = f"{config.BASE_URL}{caminho}"
    try:
        r = cliente._sessao.get(
            url,
            headers={"Authorization": f"Bearer {cliente.autenticar()}"},
            timeout=60,
        )
        corpo = r.text[:limite].replace("\n", " ")
        print(f"[{r.status_code}] GET {caminho}\n        -> {corpo}\n")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] GET {caminho} -> {type(e).__name__}: {e}\n")


def main() -> None:
    cliente = EmbrapaClimAPI()
    cliente.autenticar()
    print("=== Lista completa de variáveis (GET /ncep-gfs) ===")
    try:
        bruto = cliente.listar_variaveis()
        nomes = [v.get("nome") for v in bruto] if isinstance(bruto, list) else bruto
        print("VARIÁVEIS:", json.dumps(nomes, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        print("Falha ao listar:", e)
    print()

    lon, lat = -47.8103, -21.1775
    var = "apcpsfc"  # variável confirmada na lista

    print("=== Descobrindo o formato do endpoint de dados ===")
    # 2 segmentos: o backend deve dizer quais parâmetros faltam
    _get(cliente, f"/ncep-gfs/{var}")
    # query params (várias convenções de nome)
    _get(cliente, f"/ncep-gfs/{var}?longitude={lon}&latitude={lat}")
    _get(cliente, f"/ncep-gfs/{var}?lon={lon}&lat={lat}")
    _get(cliente, f"/ncep-gfs/{var}?long={lon}&lat={lat}")
    # coordenadas juntas em um segmento
    _get(cliente, f"/ncep-gfs/{var}/{lon},{lat}")
    _get(cliente, f"/ncep-gfs/{var}/{lat},{lon}")
    # coordenada única por vez
    _get(cliente, f"/ncep-gfs/{var}/{lon}")
    # recurso plural
    _get(cliente, f"/ncep-gfs/previsao/{var}?longitude={lon}&latitude={lat}")


if __name__ == "__main__":
    main()
