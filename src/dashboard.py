"""Gera o painel HTML autossuficiente (sem dependências externas / CDN).

Recebe o dicionário de resultado da coleta e escreve docs/index.html com os
dados embutidos. O painel tem:
  - seletor de cidades (mostra/esconde cada cidade nos gráficos);
  - linha do tempo "semáforo" da janela de aplicação por cidade;
  - gráficos por métrica (temperatura, umidade, vento, Delta-T) com a faixa
    ideal sombreada e tooltip ao passar o mouse.

Cores seguem uma paleta validada para daltonismo: status verde/amarelo/vermelho
para o semáforo; azul/laranja/aqua para as cidades.
"""
from __future__ import annotations

import json

from . import config

_HTML = r"""<!doctype html>
<html lang="pt-BR" data-theme="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Janela de aplicação de herbicida — Sudeste</title>
<style>
  :root {
    color-scheme: light dark;
    --plane: #f9f9f7; --surface: #fcfcfb;
    --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
    --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,.10);
    --good: #0ca30c; --warn: #fab219; --crit: #d03b3b;
    --c1: #2a78d6; --c2: #eb6834; --c3: #1baf7a;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --plane: #0d0d0d; --surface: #1a1a19;
      --ink: #fff; --ink2: #c3c2b7; --muted: #898781;
      --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10);
      --c1: #3987e5; --c2: #d95926; --c3: #199e70;
    }
  }
  :root[data-theme="dark"] {
    --plane: #0d0d0d; --surface: #1a1a19;
    --ink: #fff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10);
    --c1: #3987e5; --c2: #d95926; --c3: #199e70;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--plane); color: var(--ink);
    font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 24px 18px 64px; }
  header h1 { font-size: 22px; margin: 0 0 4px; }
  header p { margin: 2px 0; color: var(--ink2); font-size: 13px; }
  .banner { background: color-mix(in srgb, var(--warn) 18%, var(--surface));
    border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px;
    margin: 14px 0; font-size: 13px; }
  .card { background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 18px; margin: 16px 0; }
  h2 { font-size: 16px; margin: 0 0 12px; }
  .sub { color: var(--muted); font-weight: 400; font-size: 13px; }
  /* seletor de cidades */
  .cidades { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
    border: 1px solid var(--border); border-radius: 999px; padding: 7px 14px;
    background: var(--surface); user-select: none; font-size: 14px; }
  .chip input { display: none; }
  .chip .dot { width: 12px; height: 12px; border-radius: 50%; flex: none; }
  .chip[aria-pressed="false"] { opacity: .42; }
  /* legenda */
  .leg { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--ink2); }
  .leg span { display: inline-flex; align-items: center; gap: 7px; }
  .leg i { width: 14px; height: 14px; border-radius: 4px; display: inline-block; }
  /* kpis */
  .kpis { display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 12px; }
  .kpi { border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; }
  .kpi .n { font-size: 26px; font-weight: 650; }
  .kpi .l { font-size: 12px; color: var(--ink2); }
  .kpi .city { font-size: 12px; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 6px; }
  .kpi .city .dot { width: 10px; height: 10px; border-radius: 50%; }
  /* timeline */
  .tl-row { margin: 12px 0; }
  .tl-row .name { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 4px; }
  .tl-row .name .dot { width: 11px; height: 11px; border-radius: 50%; }
  svg { width: 100%; height: auto; display: block; }
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 720px) { .charts { grid-template-columns: 1fr; } }
  .chart h3 { font-size: 14px; margin: 0 0 2px; }
  .chart .u { font-size: 12px; color: var(--muted); margin: 0 0 6px; }
  .tip { position: fixed; pointer-events: none; z-index: 20; background: var(--surface);
    border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px; font-size: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,.18); opacity: 0; transition: opacity .08s; max-width: 240px; }
  .tip b { display: block; margin-bottom: 4px; color: var(--ink); }
  .tip .r { display: flex; align-items: center; gap: 6px; color: var(--ink2); }
  .tip .r .dot { width: 9px; height: 9px; border-radius: 50%; }
  .foot { color: var(--muted); font-size: 12px; margin-top: 24px; }
  .topbar { float: right; display: flex; gap: 8px; align-items: center; }
  .toggle, .btn { font-size: 12px; color: var(--ink2); cursor: pointer;
    border: 1px solid var(--border); border-radius: 999px; padding: 6px 12px; background: var(--surface); }
  .btn { color: #fff; background: var(--c1); border-color: transparent; font-weight: 600; }
  .btn:disabled { opacity: .55; cursor: progress; }
  #status { display: block; clear: both; text-align: right; font-size: 12px; color: var(--ink2); min-height: 18px; padding-top: 6px; }
  #status.err { color: var(--crit); }
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <button class="btn" id="atualizar">⟳ Atualizar agora</button>
    <button class="toggle" id="tema">☀︎ / ☾</button>
  </div>
  <span id="status"></span>
  <header>
    <h1>Janela de aplicação de herbicida — Sudeste</h1>
    <p id="meta"></p>
    <p class="sub" id="fonte"></p>
  </header>
  <div id="banner"></div>

  <div class="card">
    <h2>Cidades <span class="sub">— clique para mostrar/ocultar</span></h2>
    <div class="cidades" id="cidades"></div>
  </div>

  <div class="card">
    <h2>Resumo — próximas horas</h2>
    <div class="kpis" id="kpis"></div>
  </div>

  <div class="card">
    <h2>Linha do tempo da janela <span class="sub">— quando aplicar</span></h2>
    <div class="leg" style="margin-bottom:12px">
      <span><i style="background:var(--good)"></i> Favorável</span>
      <span><i style="background:var(--warn)"></i> Atenção</span>
      <span><i style="background:var(--crit)"></i> Desfavorável</span>
    </div>
    <div id="timelines"></div>
  </div>

  <div class="card">
    <h2>Condições previstas <span class="sub">— faixa sombreada = ideal para aplicação</span></h2>
    <div class="charts" id="charts"></div>
  </div>

  <p class="foot" id="foot"></p>
</div>
<div class="tip" id="tip"></div>

<script id="dados" type="application/json">__DADOS__</script>
<script>
let DADOS = JSON.parse(document.getElementById('dados').textContent);
const CORES = ['var(--c1)','var(--c2)','var(--c3)','#eda100','#e87ba4'];
const STATUS = {favoravel:'var(--good)', atencao:'var(--warn)', desfavoravel:'var(--crit)'};
const ROTULO = {favoravel:'Favorável', atencao:'Atenção', desfavoravel:'Desfavorável'};
const tip = document.getElementById('tip');
let ativas = new Set(DADOS.cidades.map(c => c.id));

// ---- cabeçalho ----
function renderCabecalho() {
  document.getElementById('meta').textContent =
    'Gerado em ' + DADOS.gerado_em.replace('T',' ') + ' • Região: ' + DADOS.regiao +
    ' • Requisições: ' + DADOS.requisicoes_usadas + '/' + DADOS.limite_requisicoes;
  document.getElementById('fonte').textContent = 'Fonte: ' + DADOS.fonte;
  document.getElementById('banner').innerHTML = DADOS.exemplo
    ? '<div class="banner"><b>Dados de exemplo.</b> Clique em <b>Atualizar agora</b> ' +
      '(com o servidor rodando) ou configure as chaves da ClimAPI para ver a previsão real.</div>'
    : '';
}

// ---- botão "Atualizar agora" (busca dados ao vivo no backend) ----
const btnAtu = document.getElementById('atualizar');
const elStatus = document.getElementById('status');
btnAtu.onclick = async () => {
  btnAtu.disabled = true; elStatus.className = '';
  elStatus.textContent = 'Consultando a Embrapa ClimAPI…';
  try {
    const r = await fetch('api/atualizar', { method: 'POST' });
    const novo = await r.json();
    if (!r.ok || novo.erro) throw new Error(novo.erro || ('HTTP ' + r.status));
    DADOS = novo;
    ativas = new Set(DADOS.cidades.filter(c => ativas.has(c.id)).map(c => c.id));
    if (!ativas.size) ativas = new Set(DADOS.cidades.map(c => c.id));
    renderCabecalho(); render();
    elStatus.className = '';
    elStatus.textContent = 'Atualizado ao vivo em ' + DADOS.gerado_em.replace('T',' ');
  } catch (e) {
    elStatus.className = 'err';
    elStatus.textContent = 'Não foi possível atualizar ao vivo (' + e.message +
      '). O botão precisa do servidor rodando: python -m src.servidor';
  } finally {
    btnAtu.disabled = false;
  }
};

// ---- seletor de cidades ----
const elCid = document.getElementById('cidades');
DADOS.cidades.forEach((c, i) => {
  const b = document.createElement('button');
  b.className = 'chip'; b.setAttribute('aria-pressed','true');
  b.innerHTML = '<span class="dot" style="background:'+CORES[i]+'"></span>' + c.nome + '/' + c.uf;
  b.onclick = () => {
    if (ativas.has(c.id)) { ativas.delete(c.id); b.setAttribute('aria-pressed','false'); }
    else { ativas.add(c.id); b.setAttribute('aria-pressed','true'); }
    render();
  };
  elCid.appendChild(b);
});

// ---- utilidades ----
const fmtHora = s => { const d = new Date(s);
  return d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'}) + ' ' +
         String(d.getHours()).padStart(2,'0') + 'h'; };
const idxCor = c => DADOS.cidades.findIndex(x => x.id === c.id);

function ativasLista() { return DADOS.cidades.filter(c => ativas.has(c.id)); }

// ---- KPIs ----
function renderKpis() {
  const el = document.getElementById('kpis'); el.innerHTML = '';
  ativasLista().forEach(c => {
    const r = c.resumo;
    const prox = r.proxima_janela ? fmtHora(r.proxima_janela) : '—';
    const d = document.createElement('div'); d.className = 'kpi';
    d.innerHTML =
      '<div class="city"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'</div>'+
      '<div class="n">'+r.horas_favoraveis+'</div>'+
      '<div class="l">instantes favoráveis (de '+r.total_instantes+')</div>'+
      '<div class="l" style="margin-top:8px">Próxima janela: <b>'+prox+'</b></div>';
    el.appendChild(d);
  });
}

// ---- linha do tempo (semáforo) ----
function renderTimelines() {
  const host = document.getElementById('timelines'); host.innerHTML = '';
  ativasLista().forEach(c => {
    const serie = c.serie; const n = serie.length;
    const W = 1000, H = 34, pl = 4, pr = 4, top = 0, hb = 24;
    const iw = (W - pl - pr) / Math.max(1, n);
    let rects = '', ticks = '';
    serie.forEach((p, i) => {
      const x = pl + i * iw;
      rects += '<rect x="'+(x+0.5)+'" y="'+top+'" width="'+Math.max(0.5,iw-1)+'" height="'+hb+
        '" rx="1.5" fill="'+STATUS[p.classe]+'" data-i="'+i+'"></rect>';
    });
    // marca de dia
    let ultimoDia = '';
    serie.forEach((p, i) => {
      const d = new Date(p.data); const dia = d.toDateString();
      if (dia !== ultimoDia && d.getHours() < 3) {
        const x = pl + i * iw;
        ticks += '<line x1="'+x+'" y1="0" x2="'+x+'" y2="'+hb+'" stroke="var(--surface)" stroke-width="2"/>';
        ticks += '<text x="'+(x+3)+'" y="'+(H-2)+'" fill="var(--muted)" font-size="11">'+
          d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';
        ultimoDia = dia;
      }
    });
    const row = document.createElement('div'); row.className = 'tl-row';
    row.innerHTML = '<div class="name"><span class="dot" style="background:'+CORES[idxCor(c)]+
      '"></span>'+c.nome+'/'+c.uf+'</div>'+
      '<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" style="height:34px">'+
      rects+ticks+'</svg>';
    const svg = row.querySelector('svg');
    svg.addEventListener('mousemove', e => {
      const t = e.target; if (t.tagName !== 'rect') { hideTip(); return; }
      const p = serie[+t.dataset.i];
      showTip(e, '<b>'+c.nome+' • '+fmtHora(p.data)+'</b>'+
        '<div class="r"><span class="dot" style="background:'+STATUS[p.classe]+'"></span>'+ROTULO[p.classe]+'</div>'+
        linhaTip('Temperatura', p.temp_c+' °C')+
        linhaTip('Umidade', p.umidade+' %')+
        linhaTip('Vento', p.vento_kmh+' km/h')+
        linhaTip('Delta-T', p.delta_t+' °C')+
        linhaTip('Chuva', p.precip_mm+' mm'));
    });
    svg.addEventListener('mouseleave', hideTip);
    host.appendChild(row);
  });
}
const linhaTip = (k,v) => '<div class="r">'+k+': <b style="color:var(--ink)">'+v+'</b></div>';

// ---- gráficos de linha por métrica ----
const METRICAS = [
  {key:'temp_c',    titulo:'Temperatura', unidade:'°C',   band:{max:28}, dec:0},
  {key:'umidade',   titulo:'Umidade relativa', unidade:'%', band:{min:60}, dec:0},
  {key:'vento_kmh', titulo:'Velocidade do vento', unidade:'km/h', band:{min:3,max:10}, dec:0},
  {key:'delta_t',   titulo:'Delta-T (índice de pulverização)', unidade:'°C', band:{min:2,max:8}, dec:1},
];

function renderCharts() {
  const host = document.getElementById('charts'); host.innerHTML = '';
  const cid = ativasLista();
  METRICAS.forEach(m => {
    const box = document.createElement('div'); box.className = 'chart';
    box.innerHTML = '<h3>'+m.titulo+'</h3><p class="u">'+m.unidade+'</p>';
    box.appendChild(chartSVG(m, cid));
    host.appendChild(box);
  });
}

function chartSVG(m, cidades) {
  const W = 500, H = 260, pl = 40, pr = 12, pt = 12, pb = 26;
  const iw = W - pl - pr, ih = H - pt - pb;
  // eixo de tempo pela primeira cidade ativa (todas compartilham a grade GFS)
  const ref = cidades[0] ? cidades[0].serie : (DADOS.cidades[0].serie);
  const n = ref.length;
  let vals = [];
  cidades.forEach(c => c.serie.forEach(p => vals.push(p[m.key])));
  if (m.band.min != null) vals.push(m.band.min);
  if (m.band.max != null) vals.push(m.band.max);
  let ymin = Math.min(...vals), ymax = Math.max(...vals);
  const pad = (ymax - ymin) * 0.08 || 1; ymin -= pad; ymax += pad;
  const X = i => pl + (n <= 1 ? 0 : i/(n-1)*iw);
  const Y = v => pt + (1 - (v - ymin)/(ymax - ymin)) * ih;

  let s = '<svg viewBox="0 0 '+W+' '+H+'" role="img">';
  // faixa ideal sombreada
  const yTop = Y(m.band.max != null ? m.band.max : ymax);
  const yBot = Y(m.band.min != null ? m.band.min : ymin);
  s += '<rect x="'+pl+'" y="'+yTop+'" width="'+iw+'" height="'+Math.max(0,(yBot-yTop))+
       '" fill="var(--good)" opacity="0.10"/>';
  if (m.band.min != null) s += linhaRef(pl, iw, Y(m.band.min));
  if (m.band.max != null) s += linhaRef(pl, iw, Y(m.band.max));
  // grade + rótulos Y
  for (let g=0; g<=4; g++) {
    const v = ymin + (ymax-ymin)*g/4, y = Y(v);
    s += '<line x1="'+pl+'" y1="'+y+'" x2="'+(W-pr)+'" y2="'+y+'" stroke="var(--grid)" stroke-width="1"/>';
    s += '<text x="'+(pl-6)+'" y="'+(y+4)+'" text-anchor="end" fill="var(--muted)" font-size="11">'+
         v.toFixed(m.dec)+'</text>';
  }
  // rótulos de dia no eixo X
  let ultimo='';
  ref.forEach((p,i) => { const d=new Date(p.data);
    if (d.toDateString()!==ultimo && d.getHours()<3) {
      s += '<text x="'+X(i)+'" y="'+(H-8)+'" fill="var(--muted)" font-size="11">'+
           d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';
      ultimo=d.toDateString();
    }});
  // linhas por cidade
  cidades.forEach(c => {
    const cor = CORES[idxCor(c)];
    let d = '';
    c.serie.forEach((p,i) => { d += (i?'L':'M') + X(i).toFixed(1) + ' ' + Y(p[m.key]).toFixed(1) + ' '; });
    s += '<path d="'+d+'" fill="none" stroke="'+cor+'" stroke-width="2" stroke-linejoin="round"/>';
  });
  // camada de hover
  s += '<line id="cx" x1="0" y1="'+pt+'" x2="0" y2="'+(pt+ih)+'" stroke="var(--axis)" stroke-width="1" opacity="0"/>';
  s += '<rect x="'+pl+'" y="'+pt+'" width="'+iw+'" height="'+ih+'" fill="transparent"/>';
  s += '</svg>';

  const tpl = document.createElement('template'); tpl.innerHTML = s.trim();
  const svg = tpl.content.firstChild;
  const cx = svg.querySelector('#cx');
  const overlay = svg.querySelector('rect[fill="transparent"]');
  overlay.addEventListener('mousemove', e => {
    const r = svg.getBoundingClientRect(); const ratio = W / r.width;
    const sx = (e.clientX - r.left) * ratio;
    let i = Math.round((sx - pl)/iw*(n-1)); i = Math.max(0, Math.min(n-1, i));
    cx.setAttribute('x1', X(i)); cx.setAttribute('x2', X(i)); cx.setAttribute('opacity','1');
    let html = '<b>'+fmtHora(ref[i].data)+'</b>';
    cidades.forEach(c => { const p = c.serie[i]; if (!p) return;
      html += '<div class="r"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+
              c.nome+': <b style="color:var(--ink)">'+p[m.key].toFixed(m.dec)+' '+m.unidade+'</b></div>'; });
    showTip(e, html);
  });
  overlay.addEventListener('mouseleave', () => { cx.setAttribute('opacity','0'); hideTip(); });
  return svg;
}
const linhaRef = (x,w,y) => '<line x1="'+x+'" y1="'+y+'" x2="'+(x+w)+'" y2="'+y+
  '" stroke="var(--good)" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>';

// ---- tooltip ----
function showTip(e, html) {
  tip.innerHTML = html; tip.style.opacity = '1';
  let x = e.clientX + 14, y = e.clientY + 14;
  const r = tip.getBoundingClientRect();
  if (x + r.width > innerWidth) x = e.clientX - r.width - 14;
  if (y + r.height > innerHeight) y = e.clientY - r.height - 14;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function hideTip() { tip.style.opacity = '0'; }

// ---- tema ----
document.getElementById('tema').onclick = () => {
  const cur = document.documentElement.getAttribute('data-theme');
  document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
  render();
};

function render() { renderKpis(); renderTimelines(); renderCharts(); }
renderCabecalho();
document.getElementById('foot').textContent =
  'Delta-T ideal 2–8 °C • vento 3–10 km/h • temperatura ≤ 28 °C • umidade ≥ 60 %. ' +
  'Sempre confira a bula do produto. Painel gerado automaticamente a partir da Embrapa ClimAPI.';
render();
</script>
</body>
</html>
"""


def gerar(resultado: dict) -> None:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dados_json = json.dumps(resultado, ensure_ascii=False)
    html = _HTML.replace("__DADOS__", dados_json)
    (config.DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
