"""Indicadores agronômicos da janela de aplicação.

Combina as séries brutas (temperatura, umidade, precipitação e vento) em uma
única linha do tempo por cidade e, para cada instante, calcula:
  - velocidade do vento (km/h) a partir das componentes U e V;
  - Delta-T (°C), o índice-padrão de pulverização;
  - a classe da janela: "favoravel", "atencao" ou "desfavoravel".
"""
from __future__ import annotations

import math

from .config import LIMIARES


# --------------------------------------------------------------------------
# Conversões de unidade (tolerantes à unidade de origem)
# --------------------------------------------------------------------------
def para_celsius(valor: float) -> float:
    """Kelvin -> °C. Se já vier em °C (valor plausível), mantém."""
    return valor - 273.15 if valor > 100 else valor


def vento_ms_para_kmh(ms: float) -> float:
    return ms * 3.6


def velocidade_vento_kmh(u_ms: float, v_ms: float) -> float:
    return vento_ms_para_kmh(math.hypot(u_ms, v_ms))


def delta_t(temp_c: float, umidade_pct: float) -> float:
    """Delta-T = temperatura de bulbo seco - temperatura de bulbo úmido.

    Bulbo úmido pela aproximação de Stull (2011), válida para UR de 5–99 %
    e temperaturas usuais de campo.
    """
    ur = max(1.0, min(100.0, umidade_pct))
    tw = (
        temp_c * math.atan(0.151977 * math.sqrt(ur + 8.313659))
        + math.atan(temp_c + ur)
        - math.atan(ur - 1.676331)
        + 0.00391838 * ur**1.5 * math.atan(0.023101 * ur)
        - 4.686035
    )
    return round(temp_c - tw, 2)


# --------------------------------------------------------------------------
# Classificação da janela
# --------------------------------------------------------------------------
def _dentro(valor: float, faixa: tuple[float, float]) -> bool:
    return faixa[0] <= valor <= faixa[1]


def classificar(temp_c: float, umidade: float, vento_kmh: float,
                precip_mm: float, dt: float) -> str:
    """Devolve 'favoravel', 'atencao' ou 'desfavoravel' para um instante."""
    lv = LIMIARES["vento_kmh"]
    lt = LIMIARES["temp_c"]
    lu = LIMIARES["umidade"]
    ld = LIMIARES["delta_t"]

    # Reprovações duras -> desfavorável.
    if precip_mm > LIMIARES["precip_mm_max"]:
        return "desfavoravel"
    if not _dentro(vento_kmh, lv["aceitavel"]):
        return "desfavoravel"
    if temp_c > lt["aceitavel_max"]:
        return "desfavoravel"
    if umidade < lu["aceitavel_min"]:
        return "desfavoravel"
    if not _dentro(dt, ld["aceitavel"]):
        return "desfavoravel"

    # Tudo na faixa ideal -> favorável.
    if (
        _dentro(vento_kmh, lv["ideal"])
        and temp_c <= lt["ideal_max"]
        and umidade >= lu["ideal_min"]
        and _dentro(dt, ld["ideal"])
    ):
        return "favoravel"

    # Dentro do aceitável, mas fora do ideal -> atenção.
    return "atencao"


# --------------------------------------------------------------------------
# Montagem da linha do tempo por cidade
# --------------------------------------------------------------------------
def _indexar(serie: list[dict]) -> dict[str, float]:
    return {reg["data"]: reg["valor"] for reg in serie}


def montar_serie_cidade(series_brutas: dict[str, list[dict]]) -> list[dict]:
    """Cruza as séries por instante e calcula os indicadores derivados.

    ``series_brutas`` mapeia nomes lógicos -> lista de {data, valor}:
    'temperatura', 'umidade', 'precipitacao', 'vento_u', 'vento_v'.
    """
    temp = _indexar(series_brutas.get("temperatura", []))
    umid = _indexar(series_brutas.get("umidade", []))
    prec = _indexar(series_brutas.get("precipitacao", []))
    vu = _indexar(series_brutas.get("vento_u", []))
    vv = _indexar(series_brutas.get("vento_v", []))

    # Usa os instantes da temperatura como eixo de referência.
    instantes = sorted(temp.keys())
    linha: list[dict] = []
    for t in instantes:
        if t not in umid or t not in vu or t not in vv:
            continue
        temp_c = round(para_celsius(temp[t]), 1)
        umidade = round(umid[t], 0)
        vento = round(velocidade_vento_kmh(vu[t], vv[t]), 1)
        precip = round(prec.get(t, 0.0), 2)
        dt = delta_t(temp_c, umidade)
        linha.append({
            "data": t,
            "temp_c": temp_c,
            "umidade": umidade,
            "vento_kmh": vento,
            "precip_mm": precip,
            "delta_t": dt,
            "classe": classificar(temp_c, umidade, vento, precip, dt),
        })
    return linha


def resumir(linha: list[dict]) -> dict:
    """Resumo executivo da cidade para os cartões do painel."""
    favoraveis = [p for p in linha if p["classe"] == "favoravel"]
    proxima = favoraveis[0]["data"] if favoraveis else None
    return {
        "horas_favoraveis": len(favoraveis),
        "horas_atencao": sum(1 for p in linha if p["classe"] == "atencao"),
        "horas_desfavoraveis": sum(1 for p in linha if p["classe"] == "desfavoravel"),
        "total_instantes": len(linha),
        "proxima_janela": proxima,
    }
