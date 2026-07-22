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

    def serie(self, variavel: str, lon: float, lat: float) -> list[dict]:
        """Série de previsão de uma variável para o ponto (lon, lat).

        GET /ncep-gfs/{variavel}/{longitude}/{latitude}
        Devolve uma lista de {"data": ISO8601, "valor": float}.
        """
        bruto = self._get(f"/ncep-gfs/{variavel}/{lon}/{lat}")
        return _normalizar_serie(bruto)


# --------------------------------------------------------------------------
# Parsing tolerante das respostas
# --------------------------------------------------------------------------
_CHAVES_LISTA = ("response", "data", "result", "results", "features", "series", "valores")
_CHAVES_TEMPO = ("data", "date", "datetime", "horario", "timestamp", "instante", "dt")
_CHAVES_VALOR = ("valor", "value", "val", "measure", "medida")


def _extrair_lista(bruto: Any) -> list[dict]:
    if isinstance(bruto, list):
        return bruto
    if isinstance(bruto, dict):
        for chave in _CHAVES_LISTA:
            valor = bruto.get(chave)
            if isinstance(valor, list):
                return valor
        # Último recurso: primeira lista de dicionários encontrada.
        for valor in bruto.values():
            if isinstance(valor, list) and valor and isinstance(valor[0], dict):
                return valor
    raise ValueError(f"Formato de resposta inesperado da ClimAPI: {type(bruto)!r}")


def _primeira_chave(registro: dict, candidatas: tuple[str, ...]) -> str | None:
    for chave in candidatas:
        if chave in registro:
            return chave
    return None


def _normalizar_serie(bruto: Any) -> list[dict]:
    registros = _extrair_lista(bruto)
    saida: list[dict] = []
    for reg in registros:
        if not isinstance(reg, dict):
            continue
        ktempo = _primeira_chave(reg, _CHAVES_TEMPO)
        kvalor = _primeira_chave(reg, _CHAVES_VALOR)
        if ktempo is None or kvalor is None:
            continue
        try:
            valor = float(reg[kvalor])
        except (TypeError, ValueError):
            continue
        saida.append({"data": str(reg[ktempo]), "valor": valor})
    return saida
