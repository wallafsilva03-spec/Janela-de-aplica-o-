"""Configurações centrais do monitor de janela de aplicação de herbicida.

Aqui ficam:
  - credenciais/endereços da ClimAPI (lidos de variáveis de ambiente);
  - os códigos das variáveis meteorológicas usadas;
  - os limiares agronômicos que definem uma boa janela de aplicação;
  - o teto de requisições diárias.

Nada de segredo é escrito no código: as chaves vêm do ambiente
(.env local ou secrets do GitHub Actions).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
CONFIG_DIR = RAIZ / "config"
DADOS_DIR = RAIZ / "dados"
DOCS_DIR = RAIZ / "docs"

# Carrega o arquivo .env automaticamente (se existir e se python-dotenv estiver
# instalado), para não precisar exportar variáveis de ambiente na mão.
try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ModuleNotFoundError:
    pass

# ---------------------------------------------------------------------------
# Credenciais e endpoints da ClimAPI (Embrapa AgroAPI)
# ---------------------------------------------------------------------------
# Fluxo OAuth2 client_credentials:
#   1. POST em TOKEN_URL com Authorization: Basic base64(chave:segredo)
#      e corpo grant_type=client_credentials  ->  devolve access_token
#   2. Chamadas ao recurso usam Authorization: Bearer <access_token>
#
# Preencha via ambiente:
#   EMBRAPA_CONSUMER_KEY / EMBRAPA_CONSUMER_SECRET   (par de chaves da AgroAPI)
#   ou, se preferir, EMBRAPA_BASIC (o base64 já pronto de "chave:segredo").
CONSUMER_KEY = os.getenv("EMBRAPA_CONSUMER_KEY", "").strip()
CONSUMER_SECRET = os.getenv("EMBRAPA_CONSUMER_SECRET", "").strip()
BASIC_PRONTO = os.getenv("EMBRAPA_BASIC", "").strip()

TOKEN_URL = os.getenv("EMBRAPA_TOKEN_URL", "https://api.cnptia.embrapa.br/token").strip()
BASE_URL = os.getenv("EMBRAPA_BASE_URL", "https://api.cnptia.embrapa.br/climapi/v1").strip()

# ---------------------------------------------------------------------------
# Variáveis meteorológicas (recurso /ncep-gfs)
# ---------------------------------------------------------------------------
# Estes são os códigos usados na chamada:
#   GET {BASE_URL}/ncep-gfs/{variavel}/{longitude}/{latitude}
#
# Os códigos abaixo seguem a convenção GFS/NOAA usada pela ClimAPI. Caso a
# Embrapa altere algum identificador, rode `python -m src.coleta --listar-variaveis`
# para ver a lista exata que a sua conta retorna e ajuste aqui.
VARIAVEIS = {
    "temperatura": os.getenv("VAR_TEMPERATURA", "tmpsfc"),     # temperatura da superfície (°C)
    "umidade": os.getenv("VAR_UMIDADE", "rh2m"),               # umidade relativa a 2 m (%)
    "precipitacao": os.getenv("VAR_PRECIPITACAO", "apcpsfc"),  # precipitação acumulada (mm)
    "vento_u": os.getenv("VAR_VENTO_U", "ugrd10m"),            # vento componente U a 10 m (m/s)
    "vento_v": os.getenv("VAR_VENTO_V", "vgrd10m"),            # vento componente V a 10 m (m/s)
}

# ---------------------------------------------------------------------------
# Teto de requisições
# ---------------------------------------------------------------------------
# A API tem limite de 500 requisições. Como coletamos 5 variáveis por cidade
# (temperatura, umidade, precipitação e as duas componentes do vento) mais 1
# requisição de token, o gasto diário é pequeno. Mesmo assim há um teto de
# segurança que interrompe a coleta antes de estourar o limite.
LIMITE_REQUISICOES = int(os.getenv("EMBRAPA_LIMITE_REQUISICOES", "500"))

# ---------------------------------------------------------------------------
# Limiares agronômicos da janela de aplicação
# ---------------------------------------------------------------------------
# Referências usuais de pulverização/aplicação de defensivos no Brasil.
# Ajuste conforme a recomendação do produto/bula que você usa.
LIMIARES = {
    # Velocidade do vento (km/h): ideal evita deriva sem risco de inversão térmica.
    "vento_kmh": {"ideal": (3.0, 10.0), "aceitavel": (2.0, 15.0)},
    # Temperatura do ar (°C): acima disso a evaporação de gotas cresce muito.
    "temp_c": {"ideal_max": 28.0, "aceitavel_max": 30.0},
    # Umidade relativa (%): abaixo disso aumenta evaporação e deriva.
    "umidade": {"ideal_min": 60.0, "aceitavel_min": 55.0},
    # Delta-T (°C): índice-padrão de pulverização (depressão do bulbo úmido).
    "delta_t": {"ideal": (2.0, 8.0), "aceitavel": (2.0, 10.0)},
    # Precipitação no passo de tempo (mm): praticamente sem chuva prevista.
    "precip_mm_max": 0.2,
}


def carregar_cidades(apenas_padrao: bool = False) -> list[dict]:
    """Lê config/cidades.json e devolve a lista de cidades.

    Se ``apenas_padrao`` for True, retorna só as marcadas com "padrao": true.
    """
    dados = json.loads((CONFIG_DIR / "cidades.json").read_text(encoding="utf-8"))
    cidades = dados.get("cidades", [])
    if apenas_padrao:
        cidades = [c for c in cidades if c.get("padrao")]
    return cidades
