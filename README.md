# Janela de aplicação de herbicida — Sudeste

Monitor que consome a **Embrapa ClimAPI** (previsão do modelo NCEP/GFS) e mostra,
em gráficos, as **oportunidades de aplicação de herbicida** para cidades do Sudeste
— por padrão **Ribeirão Preto**, **São Carlos** e **Luís Antônio** (SP).

A coleta roda **uma vez por dia, às 07:00 (horário de Brasília)**, respeitando o
**limite de 500 requisições** da API (o gasto real é de ~16 requisições/dia).

## O que o painel mostra

Para cada instante da previsão, o sistema calcula e classifica a janela de aplicação:

- **Velocidade do vento** (km/h) — a partir das componentes U e V do GFS;
- **Temperatura do ar** (°C);
- **Umidade relativa** (%);
- **Delta-T** (°C) — o índice-padrão de pulverização (depressão do bulbo úmido, fórmula de Stull);
- **Chuva prevista** (mm).

Cada instante vira uma cor no semáforo:

| Classe | Critério (todos precisam valer para ser Favorável) |
|---|---|
| 🟢 **Favorável** | vento 3–10 km/h · temp ≤ 28 °C · umidade ≥ 60 % · Delta-T 2–8 °C · sem chuva |
| 🟡 **Atenção** | dentro do aceitável, mas fora do ideal |
| 🔴 **Desfavorável** | vento < 2 ou > 15 km/h · temp > 30 °C · umidade < 55 % · Delta-T fora de 2–10 · com chuva |

Os limiares ficam em [`src/config.py`](src/config.py) (`LIMIARES`) — ajuste conforme a bula do produto.

O painel (`docs/index.html`) é **autossuficiente** (sem CDN), tem **seletor de cidades**
(clique para mostrar/ocultar), tooltips e tema claro/escuro.

## Configuração das chaves

As chaves **não** ficam no código. Assine a ClimAPI na
[AgroAPI da Embrapa](https://www.agroapi.cnptia.embrapa.br) e gere o par
`consumer key` / `consumer secret`.

**Local:** copie `.env.example` para `.env` e preencha. Depois:

```bash
pip install -r requirements.txt
python -m src.coleta --apenas-padrao   # o .env é carregado automaticamente
```

**GitHub Actions + Pages (recomendado):** em *Settings → Secrets and variables →
Actions*, crie os secrets `EMBRAPA_CONSUMER_KEY` e `EMBRAPA_CONSUMER_SECRET`. O
workflow [`.github/workflows/publicar-painel.yml`](.github/workflows/publicar-painel.yml)
roda sozinho **3x/dia** às 10/15/18 UTC (07h, 12h e 15h BRT), gera o painel e publica no **GitHub Pages**.
Sem os secrets, ele publica com dados de exemplo até você cadastrá-los.

## Uso

```bash
python -m src.coleta --apenas-padrao   # coleta só as cidades padrão (real)
python -m src.coleta                    # coleta todas as cidades do config
python -m src.coleta --exemplo          # gera dados sintéticos p/ testar o painel
python -m src.coleta --listar-variaveis # imprime as variáveis da sua conta ClimAPI
```

Abra `docs/index.html` no navegador (ou publique via **GitHub Pages** apontando
para a pasta `docs/`).

## Botão "Atualizar agora" (dados ao vivo)

O painel tem um botão **⟳ Atualizar agora** que busca a previsão na hora. Ele
precisa de um pequeno backend rodando (as chaves ficam no servidor, nunca no
navegador):

```bash
pip install -r requirements.txt
python -m src.servidor               # sobe em http://127.0.0.1:8000 (lê o .env sozinho)
```

Abra <http://127.0.0.1:8000> e clique no botão — a página consulta a ClimAPI,
recalcula os indicadores e atualiza os gráficos ao vivo. Cada clique consome
~15 requisições (o limite da API é 500/dia).

Se você abrir apenas o `docs/index.html` (ou o GitHub Pages, que é estático), o
botão avisa que precisa do servidor — o Pages continua mostrando a última coleta
diária. Para o botão funcionar **online**, hospede o backend (veja abaixo).

### Deploy no Render (botão online)

O repositório já traz [`render.yaml`](render.yaml) e [`Procfile`](Procfile) prontos.

1. Faça push do repositório para o GitHub.
2. No [Render](https://render.com): **New + → Blueprint** e conecte este repositório.
   O Render lê o `render.yaml` e cria o serviço web (gunicorn).
3. Em **Environment**, cole as duas chaves (elas **não** ficam no código):
   - `EMBRAPA_CONSUMER_KEY`
   - `EMBRAPA_CONSUMER_SECRET`
4. Clique em **Deploy**. Abra a URL gerada e use o botão **Atualizar agora**.

Outras plataformas (Railway, Fly.io, uma VM) funcionam do mesmo jeito: comando de
start `gunicorn src.servidor:app --bind 0.0.0.0:$PORT` e as duas variáveis de ambiente.

> No plano grátis do Render o serviço "dorme" após um tempo ocioso; a primeira
> visita depois disso leva alguns segundos para acordar. Isso não afeta a coleta
> das 7h/12h/15h, que roda pelo GitHub Actions.

> **Segurança:** as chaves nunca vão para o HTML nem para o repositório (o `.env`
> está no `.gitignore`). Como as chaves que você enviou passaram pelo chat,
> gere um novo par na AgroAPI assim que possível.

## Selecionar / adicionar cidades

Edite [`config/cidades.json`](config/cidades.json). Cada cidade tem `nome`, `uf`,
`lat`, `lon` e `padrao` (se entra na coleta com `--apenas-padrao`). No painel, o
seletor no topo mostra/oculta cada cidade nos gráficos.

## Estrutura

```
config/cidades.json      cidades e coordenadas
src/config.py            credenciais, variáveis, limiares, teto de requisições
src/embrapa_client.py    cliente da ClimAPI (token + /ncep-gfs) com controle de teto
src/indicadores.py       Delta-T, vento, classificação da janela
src/coleta.py            orquestra a coleta e salva os dados
src/dashboard.py         gera o painel HTML
docs/index.html          painel (gerado)
dados/latest.json        último resultado (gerado)
.github/workflows/       agendamento diário
```

## Observações

- Os **códigos das variáveis** (`tmp2m`, `rh2m`, `apcpsfc`, `ugrd10m`, `vgrd10m`)
  seguem a convenção GFS. Se a sua conta retornar códigos diferentes, rode
  `--listar-variaveis` e ajuste em `src/config.py`.
- A ClimAPI atualiza os dados a cada 6 h e cobre o território nacional em
  resolução de ~25 km.
