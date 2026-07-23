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

from flask import Flask, Response, jsonify

from . import coleta, config

app = Flask(__name__)


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
