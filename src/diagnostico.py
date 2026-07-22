"""Diagnóstico da ClimAPI: fecha o formato do endpoint de dados (var/data/coords)."""
from __future__ import annotations

from . import config
from .embrapa_client import EmbrapaClimAPI


def _get(cliente: EmbrapaClimAPI, caminho: str, limite: int = 500) -> None:
    url = f"{config.BASE_URL}{caminho}"
    try:
        r = cliente._sessao.get(
            url, headers={"Authorization": f"Bearer {cliente.autenticar()}"}, timeout=60)
        print(f"[{r.status_code}] GET {caminho}\n        -> {r.text[:limite]}\n")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] GET {caminho} -> {type(e).__name__}: {e}\n")


def main() -> None:
    cliente = EmbrapaClimAPI()
    cliente.autenticar()
    var = "tmpsfc"
    lon, lat = -47.8103, -21.1775

    # descobre a data mais recente disponível
    datas = cliente._get(f"/ncep-gfs/{var}")
    data = datas[0] if isinstance(datas, list) and datas else "2026-07-22"
    print(f"Data mais recente: {data}\n")

    print("=== var / data (+ variações de coordenada) ===")
    _get(cliente, f"/ncep-gfs/{var}/{data}")
    _get(cliente, f"/ncep-gfs/{var}/{data}?longitude={lon}&latitude={lat}")
    _get(cliente, f"/ncep-gfs/{var}/{data}/{lon}/{lat}")
    _get(cliente, f"/ncep-gfs/{var}/{data}/{lat}/{lon}")
    _get(cliente, f"/ncep-gfs/{var}/{data}/{lon},{lat}")


if __name__ == "__main__":
    main()
