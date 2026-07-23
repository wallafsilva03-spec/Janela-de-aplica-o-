"""Notícias do agro / defensivos, atualizadas junto com a coleta (3x/dia).

Usa o RSS do Google Notícias (pt-BR), que é estável e sempre atual. Busca por
temas de defensivos e agricultura, remove duplicatas e devolve os itens mais
recentes. Tudo é best-effort: qualquer falha de rede devolve lista vazia sem
quebrar a publicação. Sem dependências externas (urllib + xml da stdlib).
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

_FUSO_BR = timezone(timedelta(hours=-3))
_FEED = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

# Consultas focadas em defensivos e no ramo agrícola (ordem de prioridade).
CONSULTAS = [
    "defensivos agrícolas",
    "herbicida pulverização",
    "agricultura safra Brasil",
]


def _fmt_data(pub: str) -> str:
    try:
        dt = parsedate_to_datetime(pub).astimezone(_FUSO_BR)
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return ""


def _buscar_feed(consulta: str, timeout: int) -> list[dict]:
    url = _FEED.format(q=urllib.parse.quote(consulta))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; GrupoMoreno/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raiz = ET.fromstring(resp.read())
    itens: list[dict] = []
    for item in raiz.iter("item"):
        titulo = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not titulo or not link:
            continue
        fonte = ""
        # O Google News costuma anexar " - Fonte" ao título.
        if " - " in titulo:
            titulo, fonte = titulo.rsplit(" - ", 1)
        itens.append({
            "titulo": titulo.strip(),
            "link": link,
            "fonte": fonte.strip(),
            "data": _fmt_data(item.findtext("pubDate") or ""),
            "tema": consulta,
        })
    return itens


def buscar(max_itens: int = 9, timeout: int = 20) -> list[dict]:
    """Devolve até ``max_itens`` notícias do agro/defensivos (best-effort)."""
    saida: list[dict] = []
    vistos: set[str] = set()
    for consulta in CONSULTAS:
        try:
            for it in _buscar_feed(consulta, timeout):
                chave = it["titulo"].lower()
                if chave in vistos:
                    continue
                vistos.add(chave)
                saida.append(it)
                if len(saida) >= max_itens:
                    return saida
        except Exception:
            continue
    return saida[:max_itens]


def exemplo() -> list[dict]:
    """Notícias de demonstração (usadas no modo --exemplo, sem rede)."""
    agora = datetime.now(_FUSO_BR).strftime("%d/%m %H:%M")
    base = [
        ("Boas práticas reduzem deriva na aplicação de herbicidas", "Embrapa"),
        ("Delta-T: entenda a janela ideal para pulverização", "Canal Rural"),
        ("Tecnologia de aplicação ganha espaço na safra do Sudeste", "Notícias Agrícolas"),
        ("Manejo de plantas daninhas exige atenção ao clima", "Agrolink"),
    ]
    return [{"titulo": t, "link": "https://news.google.com/?hl=pt-BR",
             "fonte": f, "data": agora, "tema": "exemplo"} for t, f in base]
