"""Servidor do painel com botão "Atualizar agora".

Guarda as chaves da ClimAPI no lado do servidor (lidas do ambiente/.env) e
expõe:
  GET  /              -> serve o painel (docs/index.html)
  GET  /dados         -> devolve o último resultado salvo (dados/latest.json)
  POST /api/atualizar -> faz a coleta AO VIVO na Embrapa, salva e devolve o JSON

Rode localmente com:
    pip install -r requirements.txt
    set -a && source .env && set +a
    python -m src.servidor
E abra http://127.0.0.1:8000

As chaves NUNCA são enviadas ao navegador — só os dados já processados.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify

from . import coleta, config

app = Flask(__name__)

# Idade máxima (horas) do latest.json antes de o servidor buscar dados reais
# de novo. Mantém o painel com a previsão atual sem estourar o teto da API:
# uma coleta a cada poucas horas é compartilhada por todos os visitantes.
_MAX_IDADE_H = float(os.getenv("PAINEL_MAX_IDADE_HORAS", "3"))
# Intervalo mínimo entre tentativas de coleta (evita marteladas na API quando
# ela está fora do ar ou o teto foi atingido).
_INTERVALO_TENTATIVA_S = 900
_ultima_tentativa = 0.0


def _tem_credenciais() -> bool:
    return bool((config.CONSUMER_KEY and config.CONSUMER_SECRET) or config.BASIC_PRONTO)


def _dados_atuais() -> dict | None:
    arq = config.DADOS_DIR / "latest.json"
    if not arq.exists():
        return None
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except Exception:
        return None


def _precisa_atualizar(dados: dict | None) -> bool:
    if dados is None or dados.get("exemplo"):
        return True
    ge = dados.get("gerado_em")
    if not ge:
        return True
    try:
        quando = datetime.fromisoformat(ge)
        return (datetime.now(quando.tzinfo) - quando) > timedelta(hours=_MAX_IDADE_H)
    except Exception:
        return False


def _atualizar_se_necessario() -> None:
    """Se houver chaves e os dados estiverem velhos/de exemplo, coleta a
    previsão real uma vez e regenera as páginas. Nunca derruba o request."""
    global _ultima_tentativa
    if not _tem_credenciais() or not _precisa_atualizar(_dados_atuais()):
        return
    agora = time.monotonic()
    if agora - _ultima_tentativa < _INTERVALO_TENTATIVA_S:
        return
    _ultima_tentativa = agora
    try:
        resultado = coleta.coletar(apenas_padrao=True)
        if resultado.get("cidades"):  # só salva se veio dado de verdade
            coleta.salvar(resultado)
    except Exception as e:  # não quebra a página se a API falhar
        app.logger.warning("Auto-atualização falhou: %s", e)


def _garante_paginas() -> None:
    """Gera index.html e panorama.html se ainda não existirem."""
    if (config.DOCS_DIR / "index.html").exists() and (config.DOCS_DIR / "panorama.html").exists():
        return
    base = config.DADOS_DIR / "latest.json"
    dados = json.loads(base.read_text(encoding="utf-8")) if base.exists() else coleta.gerar_exemplo()
    from . import dashboard
    dashboard.gerar(dados)


@app.get("/")
def index() -> Response:
    _atualizar_se_necessario()
    _garante_paginas()
    return Response((config.DOCS_DIR / "index.html").read_text(encoding="utf-8"), mimetype="text/html")


@app.get("/index.html")
def index_html() -> Response:
    return index()


@app.get("/panorama.html")
def panorama() -> Response:
    _garante_paginas()
    return Response((config.DOCS_DIR / "panorama.html").read_text(encoding="utf-8"), mimetype="text/html")


@app.get("/dados")
def dados() -> Response:
    _atualizar_se_necessario()
    arq = config.DADOS_DIR / "latest.json"
    if not arq.exists():
        return jsonify(coleta.gerar_exemplo())
    return Response(arq.read_text(encoding="utf-8"), mimetype="application/json")


@app.post("/api/atualizar")
def atualizar() -> Response:
    """Coleta ao vivo na Embrapa, salva e devolve o resultado."""
    try:
        resultado = coleta.coletar(apenas_padrao=True)
        coleta.salvar(resultado)
        return jsonify(resultado)
    except Exception as e:  # devolve o erro de forma legível para o painel
        return jsonify({"erro": f"{type(e).__name__}: {e}"}), 502


def main() -> None:
    import os
    porta = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=porta, debug=False)


if __name__ == "__main__":
    main()
