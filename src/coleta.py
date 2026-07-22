"""Coleta diária: baixa a previsão, calcula os indicadores e gera o painel.

Uso:
    python -m src.coleta                  # coleta real (precisa das chaves)
    python -m src.coleta --apenas-padrao  # só as cidades marcadas como padrão
    python -m src.coleta --listar-variaveis  # imprime as variáveis da sua conta
    python -m src.coleta --exemplo        # gera dados sintéticos p/ testar o painel
"""
from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime, timedelta, timezone

from . import config, dashboard
from .embrapa_client import EmbrapaClimAPI, LimiteRequisicoesError
from .indicadores import (
    classificar,
    delta_t,
    montar_serie_cidade,
    resumir,
)

FUSO_BR = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)


# --------------------------------------------------------------------------
# Coleta real
# --------------------------------------------------------------------------
def coletar(apenas_padrao: bool = False) -> dict:
    cidades = config.carregar_cidades(apenas_padrao=apenas_padrao)
    cliente = EmbrapaClimAPI()
    resultado_cidades: list[dict] = []

    for cid in cidades:
        try:
            # Descobre a rodada (data) mais recente uma vez por cidade e reusa
            # para todas as variáveis, garantindo instantes alinhados.
            itens = list(config.VARIAVEIS.items())
            datas = cliente.datas(itens[0][1])
            if not datas:
                print(f"[aviso] Sem datas disponíveis para {cid['nome']}; pulando.")
                continue
            data = datas[0]
            series_brutas = {
                nome: cliente.serie(codigo, cid["lon"], cid["lat"], data)
                for nome, codigo in itens
            }
        except LimiteRequisicoesError as e:
            print(f"[aviso] {e} Parando em {cid['nome']}.")
            break

        linha = montar_serie_cidade(series_brutas)
        resultado_cidades.append({
            "id": cid["id"],
            "nome": cid["nome"],
            "uf": cid.get("uf", ""),
            "regiao": cid.get("regiao", ""),
            "lat": cid["lat"],
            "lon": cid["lon"],
            "serie": linha,
            "resumo": resumir(linha),
        })
        print(f"[ok] {cid['nome']}: {len(linha)} instantes "
              f"({cliente.requisicoes} requisições até agora)")

    return _montar_resultado(resultado_cidades, cliente.requisicoes)


def _montar_resultado(cidades: list[dict], requisicoes: int, exemplo: bool = False) -> dict:
    return {
        "gerado_em": datetime.now(FUSO_BR).isoformat(timespec="minutes"),
        "fonte": "Embrapa ClimAPI v1 — modelo NCEP/GFS (NOAA)",
        "regiao": "Sudeste",
        "requisicoes_usadas": requisicoes,
        "limite_requisicoes": config.LIMITE_REQUISICOES,
        "limiares": config.LIMIARES,
        "exemplo": exemplo,
        "cidades": cidades,
    }


# --------------------------------------------------------------------------
# Dados de exemplo (para testar o painel sem consumir a API)
# --------------------------------------------------------------------------
def gerar_exemplo() -> dict:
    """Gera séries sintéticas realistas (ciclo diário) para as cidades padrão."""
    cidades = config.carregar_cidades(apenas_padrao=True)
    inicio = datetime.now(FUSO_BR).replace(minute=0, second=0, microsecond=0)
    rnd = random.Random(42)
    resultado: list[dict] = []

    for i, cid in enumerate(cidades):
        linha: list[dict] = []
        base_temp = 24 + i * 1.5
        for h in range(0, 120, 3):  # 5 dias, passo de 3 h
            t = inicio + timedelta(hours=h)
            hora = t.hour
            # Ciclo diário: mais quente e seco à tarde; úmido de madrugada.
            temp = base_temp + 6 * math.sin((hora - 9) / 24 * 2 * math.pi) + rnd.uniform(-1, 1)
            umid = 70 - 22 * math.sin((hora - 9) / 24 * 2 * math.pi) + rnd.uniform(-4, 4)
            umid = max(25, min(98, umid))
            vento = max(0.5, 6 + 4 * math.sin((hora - 12) / 24 * 2 * math.pi) + rnd.uniform(-2, 2))
            precip = round(max(0.0, rnd.uniform(-3, 1)), 1) if rnd.random() < 0.25 else 0.0
            temp = round(temp, 1)
            umid = round(umid, 0)
            vento = round(vento, 1)
            dt = delta_t(temp, umid)
            linha.append({
                "data": t.isoformat(timespec="minutes"),
                "temp_c": temp,
                "umidade": umid,
                "vento_kmh": vento,
                "precip_mm": precip,
                "delta_t": dt,
                "classe": classificar(temp, umid, vento, precip, dt),
            })
        resultado.append({
            "id": cid["id"], "nome": cid["nome"], "uf": cid.get("uf", ""),
            "regiao": cid.get("regiao", ""), "lat": cid["lat"], "lon": cid["lon"],
            "serie": linha, "resumo": resumir(linha),
        })
    return _montar_resultado(resultado, requisicoes=0, exemplo=True)


# --------------------------------------------------------------------------
# Persistência
# --------------------------------------------------------------------------
def salvar(resultado: dict) -> None:
    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    hoje = datetime.now(FUSO_BR).strftime("%Y-%m-%d")
    (config.DADOS_DIR / f"{hoje}.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (config.DADOS_DIR / "latest.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard.gerar(resultado)
    print(f"[ok] Painel atualizado em {config.DOCS_DIR / 'index.html'}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Monitor de janela de aplicação de herbicida (ClimAPI).")
    ap.add_argument("--apenas-padrao", action="store_true",
                    help="Coleta apenas as cidades marcadas como padrão no config.")
    ap.add_argument("--listar-variaveis", action="store_true",
                    help="Imprime as variáveis disponíveis no recurso /ncep-gfs e sai.")
    ap.add_argument("--exemplo", action="store_true",
                    help="Gera dados sintéticos (não chama a API) para testar o painel.")
    args = ap.parse_args()

    if args.listar_variaveis:
        cliente = EmbrapaClimAPI()
        print(json.dumps(cliente.listar_variaveis(), ensure_ascii=False, indent=2))
        return

    resultado = gerar_exemplo() if args.exemplo else coletar(apenas_padrao=args.apenas_padrao)
    salvar(resultado)


if __name__ == "__main__":
    main()
