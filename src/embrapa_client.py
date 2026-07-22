"""Cliente da ClimAPI (Embrapa AgroAPI) com controle de teto de requisições.

Responsável por:
  - obter o token OAuth2 (client_credentials);
  - listar as variáveis disponíveis no recurso /ncep-gfs;
  - baixar a série temporal de previsão de uma variável para um ponto;
  - contar as requisições e parar antes de estourar o limite diário.

O parser das respostas é tolerante: a ClimAPI pode devolver a lista de
registros direto no topo ou aninhada em uma chave; cada registro pode nomear
o instante e o valor de formas diferentes. Tratamos os casos comuns.
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from . import config


class LimiteRequisicoesError(RuntimeError):
    """Disparada quando o teto de requisições seria ultrapassado."""


class EmbrapaClimAPI:
    def __init__(self, timeout: int = 60) -> None:
        self._token: str | None = None
        self._sessao = requests.Session()
        self._timeout = timeout
        self.requisicoes = 0
        self.limite = config.LIMITE_REQUISICOES

    # ------------------------------------------------------------------ token
    def _cabecalho_basic(self) -> str:
        if config.BASIC_PRONTO:
            return config.BASIC_PRONTO
        if not (config.CONSUMER_KEY and config.CONSUMER_SECRET):
            raise RuntimeError(
                "Credenciais da ClimAPI ausentes. Defina EMBRAPA_CONSUMER_KEY e "
                "EMBRAPA_CONSUMER_SECRET (ou EMBRAPA_BASIC) no ambiente/.env."
            )
        cru = f"{config.CONSUMER_KEY}:{config.CONSUMER_SECRET}".encode("utf-8")
        return base64.b64encode(cru).decode("ascii")

    def autenticar(self) -> str:
        """Obtém (e memoriza) o access_token."""
        if self._token:
            return self._token
        self._contar()
        resp = self._sessao.post(
            config.TOKEN_URL,
            headers={
                "Authorization": f"Basic {self._cabecalho_basic()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError(f"Token não retornado pela API: {resp.text[:200]}")
        self._token = token
        return token

    # ---------------------------------------------------------------- helpers
    def _contar(self) -> None:
        if self.requisicoes >= self.limite:
            raise LimiteRequisicoesError(
                f"Teto de {self.limite} requisições atingido; coleta interrompida."
            )
        self.requisicoes += 1

    def _get(self, caminho: str) -> Any:
        self._contar()
        url = f"{config.BASE_URL}{caminho}"
        resp = self._sessao.get(
            url,
            headers={"Authorization": f"Bearer {self.autenticar()}"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------- endpoints
    def listar_variaveis(self) -> Any:
        """GET /ncep-gfs — lista as variáveis disponíveis na sua conta."""
        return self._get("/ncep-gfs")

    def datas(self, variavel: str) -> list[str]:
        """GET /ncep-gfs/{variavel} — datas das rodadas disponíveis (mais recente primeiro)."""
        bruto = self._get(f"/ncep-gfs/{variavel}")
        return [str(d) for d in bruto] if isinstance(bruto, list) else []

    def serie(self, variavel: str, lon: float, lat: float, data: str) -> list[dict]:
        """Série de previsão de uma variável para o ponto (lon, lat) numa rodada.

        GET /ncep-gfs/{variavel}/{data}/{longitude}/{latitude}
        A resposta é uma lista de {"horas": N, "valor": X}, onde N é o número de
        horas após 00:00 UTC da data base. Convertemos para instantes no fuso de
        Brasília e devolvemos {"data": ISO8601, "valor": float}.
        Em caso de 404 (variável sem essa data), devolve lista vazia.
        """
        try:
            bruto = self._get(f"/ncep-gfs/{variavel}/{data}/{lon}/{lat}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return []
            raise
        return _serie_horas(bruto, data)


# --------------------------------------------------------------------------
# Parsing da resposta (registros {"horas": N, "valor": X})
# --------------------------------------------------------------------------
_FUSO_BR = timezone(timedelta(hours=-3))  # America/Sao_Paulo


def _serie_horas(bruto: Any, data: str) -> list[dict]:
    if not isinstance(bruto, list):
        return []
    try:
        base = datetime.strptime(data, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return []
    saida: list[dict] = []
    for reg in bruto:
        if not isinstance(reg, dict):
            continue
        horas, valor = reg.get("horas"), reg.get("valor")
        if horas is None or valor is None:
            continue
        try:
            instante = (base + timedelta(hours=int(horas))).astimezone(_FUSO_BR)
            saida.append({"data": instante.isoformat(timespec="minutes"), "valor": float(valor)})
        except (TypeError, ValueError):
            continue
    return saida
