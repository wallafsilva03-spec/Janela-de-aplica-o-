"""Gera o app HTML (2 páginas) autossuficiente, na identidade do Grupo Moreno.

Páginas (ambas em docs/, navegação no topo):
  - index.html    -> "Janelas de aplicação" (operacional): cidades, meu dia por
                     hora, janelas, visão geral, gráficos e editor de recomendações.
  - panorama.html -> "Panorama agrícola" (visão geral): notícias do agro/defensivos
                     (3x/dia), resumo, ranking das próximas janelas e mais gráficos.

Identidade visual: verde / verde-limão / azul do Grupo Moreno
(pilares FORTALECER · CONECTAR · CRESCER). Semáforo mantém verde/âmbar/vermelho
(significado), acessível para daltonismo.
"""
from __future__ import annotations

import json

from . import config

# ---------------------------------------------------------------------------
# Estilos (identidade Grupo Moreno)
# ---------------------------------------------------------------------------
_ESTILO = r"""
  :root{
    color-scheme:light dark;
    --verde:#1e9a44; --lima:#8bc53f; --lima-d:#5f9e2e; --azul:#1d3e95;
    --plane:#f4f6f3; --surface:#ffffff; --surface2:#f2f5ef;
    --ink:#12232e; --ink2:#4c5b63; --muted:#8a938f;
    --grid:#e6ebe4; --axis:#c7cfc4; --border:rgba(18,35,46,.10);
    --good:#1e9a44; --warn:#f5a623; --crit:#d23b3b;
    --band:rgba(29,62,149,.09);
    --shadow:0 1px 2px rgba(18,35,46,.05),0 10px 28px rgba(18,35,46,.07);
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --plane:#0c1114; --surface:#141b20; --surface2:#1b242a;
    --ink:#eef3f0; --ink2:#b7c2bd; --muted:#7f8a85;
    --grid:#243036; --axis:#33424a; --border:rgba(255,255,255,.10);
    --verde:#38b25e; --lima:#a6d84f; --lima-d:#a6d84f; --azul:#5b82e6;
    --band:rgba(91,130,230,.14);
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.45);
  }}
  :root[data-theme="dark"]{
    --plane:#0c1114; --surface:#141b20; --surface2:#1b242a;
    --ink:#eef3f0; --ink2:#b7c2bd; --muted:#7f8a85;
    --grid:#243036; --axis:#33424a; --border:rgba(255,255,255,.10);
    --verde:#38b25e; --lima:#a6d84f; --lima-d:#a6d84f; --azul:#5b82e6;
    --band:rgba(91,130,230,.14);
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.45);
  }
  /* tema claro explícito — vence o modo escuro do sistema quando escolhido */
  :root[data-theme="light"]{
    --plane:#f4f6f3; --surface:#ffffff; --surface2:#f2f5ef;
    --ink:#12232e; --ink2:#4c5b63; --muted:#8a938f;
    --grid:#e6ebe4; --axis:#c7cfc4; --border:rgba(18,35,46,.10);
    --verde:#1e9a44; --lima:#8bc53f; --lima-d:#5f9e2e; --azul:#1d3e95;
    --good:#1e9a44; --warn:#f5a623; --crit:#d23b3b;
    --band:rgba(29,62,149,.09);
    --shadow:0 1px 2px rgba(18,35,46,.05),0 10px 28px rgba(18,35,46,.07);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--plane);color:var(--ink);
    font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
  .wrap{max-width:1120px;margin:0 auto;padding:18px 18px 72px}
  a{color:var(--azul)}
  /* topo / marca */
  .head{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
    padding:6px 0 2px}
  .brand{display:flex;align-items:center;gap:14px}
  .logo{width:46px;height:52px;flex:none}
  .wm{font-family:Georgia,"Times New Roman",serif;font-style:italic;font-weight:700;
    font-size:26px;color:var(--azul);line-height:1;letter-spacing:.01em}
  .pillars{display:flex;gap:6px;margin-top:6px}
  .pillars span{font-size:10.5px;font-weight:700;letter-spacing:.06em;color:#fff;
    padding:3px 9px;border-radius:999px}
  .pf{background:var(--verde)} .pc{background:var(--lima)} .pk{background:var(--azul)}
  .tools{display:flex;gap:8px;align-items:center}
  .toggle,.btn,.linkbtn{font-size:12px;color:var(--ink2);cursor:pointer;border:1px solid var(--border);
    border-radius:999px;padding:7px 13px;background:var(--surface)}
  .btn{color:#fff;background:var(--azul);border-color:transparent;font-weight:600}
  .btn:disabled{opacity:.55;cursor:progress}
  /* navegação */
  .nav{display:flex;gap:4px;margin:14px 0 4px;border-bottom:1px solid var(--border)}
  .nav a{text-decoration:none;color:var(--ink2);font-weight:600;font-size:14.5px;
    padding:10px 16px;border-bottom:3px solid transparent;border-radius:8px 8px 0 0}
  .nav a.on{color:var(--azul);border-bottom-color:var(--azul);background:var(--surface)}
  #status{display:block;text-align:right;font-size:12px;color:var(--ink2);min-height:16px;padding-top:6px}
  #status.err{color:var(--crit)}
  h1{font-size:22px;margin:12px 0 4px;letter-spacing:-.01em}
  h2{font-size:16px;margin:0 0 14px;letter-spacing:-.01em}
  .sub{color:var(--muted);font-weight:400;font-size:13px}
  header p{margin:2px 0;color:var(--ink2);font-size:13px}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:16px;
    padding:18px 20px;margin:16px 0;box-shadow:var(--shadow)}
  .banner{background:color-mix(in srgb,var(--warn) 16%,var(--surface));
    border:1px solid var(--border);border-radius:12px;padding:10px 14px;margin:14px 0;font-size:13px}
  .row{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end}
  .field{display:flex;flex-direction:column;gap:6px}
  .field label{font-size:12px;color:var(--ink2);font-weight:600}
  .cidades{display:flex;flex-wrap:wrap;gap:8px}
  .chip{display:inline-flex;align-items:center;gap:8px;cursor:pointer;border:1px solid var(--border);
    border-radius:999px;padding:7px 14px;background:var(--surface);color:var(--ink);user-select:none;font-size:14px}
  .chip .dot{width:12px;height:12px;border-radius:50%;flex:none}
  .chip[aria-pressed="false"]{opacity:.4}
  input[type=date]{font:inherit;padding:7px 10px;border:1px solid var(--border);border-radius:10px;
    background:var(--surface);color:var(--ink)}
  .leg{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:var(--ink2);align-items:center}
  .leg span{display:inline-flex;align-items:center;gap:7px}
  .leg i{width:14px;height:14px;border-radius:4px;display:inline-block}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
  .kpi{border:1px solid var(--border);border-radius:14px;padding:14px 16px;background:var(--surface2)}
  .kpi .city{font-size:13px;display:inline-flex;align-items:center;gap:7px;margin-bottom:8px;font-weight:600}
  .kpi .city .dot{width:11px;height:11px;border-radius:50%}
  .kpi .big{display:flex;align-items:baseline;gap:8px}
  .kpi .n{font-size:30px;font-weight:680;letter-spacing:-.02em}
  .kpi .l{font-size:12px;color:var(--ink2)}
  .kpi .line{font-size:12.5px;color:var(--ink2);margin-top:8px;display:flex;justify-content:space-between;gap:8px}
  .kpi .line b{color:var(--ink)}
  .pill{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:700}
  .pill.f{background:color-mix(in srgb,var(--good) 20%,transparent);color:var(--good)}
  .pill.a{background:color-mix(in srgb,var(--warn) 26%,transparent);color:#8a5a00}
  .pill.d{background:color-mix(in srgb,var(--crit) 18%,transparent);color:var(--crit)}
  .diaCity{padding:14px 0;border-top:1px solid var(--border)}
  .diaCity:first-child{border-top:0}
  .diaCity .nome{display:flex;align-items:center;gap:8px;font-weight:600;margin-bottom:8px}
  .diaCity .nome .dot{width:11px;height:11px;border-radius:50%}
  .janelas{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
  .win{font-size:13px;padding:6px 12px;border-radius:10px;background:color-mix(in srgb,var(--good) 14%,var(--surface));
    border:1px solid color-mix(in srgb,var(--good) 30%,var(--border));display:inline-flex;gap:8px;align-items:center}
  .win b{font-variant-numeric:tabular-nums}
  .nowin{font-size:13px;color:var(--ink2)}
  .chuvinfo{font-size:13px;color:var(--ink2);margin-top:8px}
  svg{width:100%;height:auto;display:block}
  .tl-row{margin:12px 0}
  .tl-row .name{display:flex;align-items:center;gap:8px;font-size:14px;margin-bottom:4px}
  .tl-row .name .dot{width:11px;height:11px;border-radius:50%}
  .charts{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  @media (max-width:760px){.charts{grid-template-columns:1fr}}
  .chart h3{font-size:14px;margin:0 0 2px}
  .chart .u{font-size:12px;color:var(--muted);margin:0 0 6px}
  .rec[hidden]{display:none}
  .recgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:6px}
  .recbox{border:1px solid var(--border);border-radius:12px;padding:12px 14px;background:var(--surface2)}
  .recbox h4{margin:0 0 10px;font-size:13px}
  .recline{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:13px;color:var(--ink2)}
  .recline input{width:64px;font:inherit;padding:5px 8px;border:1px solid var(--border);border-radius:8px;
    background:var(--surface);color:var(--ink);text-align:right}
  .recact{display:flex;gap:10px;margin-top:14px}
  /* notícias */
  .news{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
  .na{display:flex;flex-direction:column;gap:6px;border:1px solid var(--border);border-radius:12px;
    padding:13px 15px;background:var(--surface2);text-decoration:none;color:var(--ink)}
  .na:hover{border-color:var(--azul)}
  .na .t{font-weight:600;font-size:14px;line-height:1.35}
  .na .m{font-size:11.5px;color:var(--muted);display:flex;gap:8px;justify-content:space-between}
  /* ranking */
  .rank{display:flex;flex-direction:column;gap:8px}
  .rk{display:flex;align-items:center;gap:12px;padding:10px 12px;border:1px solid var(--border);
    border-radius:10px;background:var(--surface2)}
  .rk .dot{width:11px;height:11px;border-radius:50%;flex:none}
  .rk .cidade{font-weight:600;min-width:130px}
  .rk .quando{font-variant-numeric:tabular-nums;color:var(--ink2)}
  .rk .dur{margin-left:auto;font-size:12px;color:var(--muted)}
  .agora{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
  .tip{position:fixed;pointer-events:none;z-index:20;background:var(--surface);border:1px solid var(--border);
    border-radius:10px;padding:8px 10px;font-size:12px;box-shadow:var(--shadow);opacity:0;transition:opacity .08s;max-width:250px}
  .tip b{display:block;margin-bottom:4px;color:var(--ink)}
  .tip .r{display:flex;align-items:center;gap:6px;color:var(--ink2)}
  .tip .r .dot{width:9px;height:9px;border-radius:50%}
  .foot{color:var(--muted);font-size:12px;margin-top:24px}
"""

# Logo em SVG (o "V" verde/lima + folha azul), inspirado na marca.
_LOGO = (
    '<svg class="logo" viewBox="0 0 46 52" aria-hidden="true">'
    '<path d="M4 2 L18 2 L24 40 L18 50 Q11 44 8 30 Z" fill="var(--verde)"/>'
    '<path d="M19 2 L31 2 L27 42 L21 46 Z" fill="var(--lima)"/>'
    '<path d="M35 8 Q43 22 33 44 Q29 34 31 20 Q32 12 35 8 Z" fill="var(--azul)"/>'
    '</svg>'
)


def _cabecalho(pagina: str) -> str:
    def on(p): return ' class="on"' if p == pagina else ""
    return f"""
  <div class="head">
    <div class="brand">{_LOGO}
      <div><div class="wm">Grupo Moreno</div>
        <div class="pillars"><span class="pf">FORTALECER</span><span class="pc">CONECTAR</span><span class="pk">CRESCER</span></div>
      </div>
    </div>
    <div class="tools">
      <button class="btn" id="atualizar">⟳ Atualizar agora</button>
      <button class="toggle" id="tema">☀︎ / ☾</button>
    </div>
  </div>
  <nav class="nav">
    <a href="index.html"{on('janelas')}>Janelas de aplicação</a>
    <a href="panorama.html"{on('panorama')}>Panorama agrícola</a>
  </nav>
  <span id="status"></span>
  <header>
    <h1 id="titulo"></h1>
    <p id="meta"></p>
    <p class="sub" id="fonte"></p>
  </header>
  <div id="banner"></div>"""


# ---------------------------------------------------------------------------
# Corpos das páginas
# ---------------------------------------------------------------------------
_BODY_JANELAS = """
  <div class="card">
    <div class="row">
      <div class="field" style="flex:1 1 320px">
        <label>Cidades <span class="sub">— clique para mostrar/ocultar</span></label>
        <div class="cidades" id="cidades"></div>
      </div>
      <div class="field"><label for="dia">Meu dia</label><input type="date" id="dia"></div>
      <div class="field"><label>&nbsp;</label><button class="linkbtn" id="abrirRec">⚙︎ Minhas recomendações</button></div>
    </div>
    <div class="rec" id="rec" hidden></div>
  </div>

  <div class="card">
    <h2>Resumo por cidade <span class="sub">— próximas horas na previsão</span></h2>
    <div class="kpis" id="kpis"></div>
  </div>

  <div class="card">
    <h2>Minhas janelas do dia <span class="sub" id="diaTitulo"></span></h2>
    <div class="leg" style="margin-bottom:6px">
      <span><i style="background:var(--good)"></i> Favorável</span>
      <span><i style="background:var(--warn)"></i> Atenção</span>
      <span><i style="background:var(--crit)"></i> Desfavorável</span>
      <span class="sub">• hora a hora, só do dia escolhido</span>
    </div>
    <div id="dia-view"></div>
  </div>

  <div class="card">
    <h2>Visão geral da previsão <span class="sub">— vários dias (passos da previsão)</span></h2>
    <div id="timelines"></div>
  </div>

  <div class="card">
    <h2>Condições previstas <span class="sub">— faixa sombreada = ideal para aplicação</span></h2>
    <div class="charts" id="charts"></div>
  </div>
"""

_BODY_PANORAMA = """
  <div class="card">
    <h2>Notícias do agro e defensivos <span class="sub">— atualiza 3x/dia junto com a previsão</span></h2>
    <div class="news" id="noticias"></div>
  </div>

  <div class="card">
    <h2>Resumo geral <span class="sub">— favorabilidade na previsão por cidade</span></h2>
    <div class="kpis" id="kpis"></div>
  </div>

  <div class="card">
    <h2>Próximas janelas favoráveis <span class="sub">— ranking por horário</span></h2>
    <div class="rank" id="ranking"></div>
  </div>

  <div class="card">
    <h2>Janelas favoráveis por dia <span class="sub">— quantidade de passos favoráveis</span></h2>
    <div class="leg" id="barras-leg" style="margin-bottom:8px"></div>
    <div id="barras-dia"></div>
  </div>

  <div class="card">
    <h2>Condições atuais <span class="sub">— primeiro instante da previsão</span></h2>
    <div class="agora" id="agora"></div>
  </div>
"""


def _documento(pagina: str, corpo: str, dados_json: str) -> str:
    return (
        '<!doctype html><html lang="pt-BR" data-theme="">\n<head>\n'
        '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Grupo Moreno — Janela de aplicação</title>\n<style>" + _ESTILO + "</style>\n</head>\n<body>\n"
        '<div class="wrap">' + _cabecalho(pagina) + corpo + '<p class="foot" id="foot"></p></div>\n'
        '<div class="tip" id="tip"></div>\n'
        '<script id="dados" type="application/json">' + dados_json + "</script>\n"
        '<script>const PAGINA="' + pagina + '";\n' + _SCRIPT + "\n</script>\n</body>\n</html>"
    )


# ---------------------------------------------------------------------------
# Script (compartilhado; cada render checa se os elementos existem)
# ---------------------------------------------------------------------------
_SCRIPT = r"""
const DADOS=JSON.parse(document.getElementById('dados').textContent);
const CORES=['var(--azul)','var(--verde)','var(--lima-d)','#eda100','#e87ba4'];
const STATUS={favoravel:'var(--good)',atencao:'var(--warn)',desfavoravel:'var(--crit)'};
const ROTULO={favoravel:'Favorável',atencao:'Atenção',desfavoravel:'Desfavorável'};
const tip=document.getElementById('tip');
let ativas=new Set(DADOS.cidades.map(c=>c.id));
const $=id=>document.getElementById(id);
// Resolve "var(--x)" para o valor concreto (vários navegadores não aceitam
// var() dentro de atributos fill/stroke de SVG). Reavaliado a cada render.
const RC=v=>(typeof v==='string'&&v.slice(0,4)==='var(')
  ?(getComputedStyle(document.documentElement).getPropertyValue(v.slice(4,-1)).trim()||v):v;
const COR=i=>RC(CORES[i]);
const ST=c=>RC(STATUS[c]);
const V=n=>RC('var('+n+')');

/* limiares editáveis */
function padraoLim(){return JSON.parse(JSON.stringify(DADOS.limiares));}
/* garante que o LIM salvo tenha SEMPRE o formato atual (dados antigos no
   navegador não quebram mais o editor de recomendações) */
function mesclarLim(base,ov){if(Array.isArray(base))return base.map((v,i)=>ov&&typeof ov[i]==='number'?ov[i]:v);
  if(base&&typeof base==='object'){const o={};for(const k in base)o[k]=mesclarLim(base[k],ov?ov[k]:undefined);return o;}
  return typeof ov==='number'?ov:base;}
let LIM;try{LIM=mesclarLim(padraoLim(),JSON.parse(localStorage.getItem('limiares_janela')));}catch(e){LIM=padraoLim();}
function salvarLim(){try{localStorage.setItem('limiares_janela',JSON.stringify(LIM));}catch(e){}}
function classificar(t,u,v,p,dt){const L=LIM;
  if(p>L.precip_mm_max)return'desfavoravel';
  if(v<L.vento_kmh.aceitavel[0]||v>L.vento_kmh.aceitavel[1])return'desfavoravel';
  if(t>L.temp_c.aceitavel_max)return'desfavoravel';
  if(u<L.umidade.aceitavel_min)return'desfavoravel';
  if(dt<L.delta_t.aceitavel[0]||dt>L.delta_t.aceitavel[1])return'desfavoravel';
  if(v>=L.vento_kmh.ideal[0]&&v<=L.vento_kmh.ideal[1]&&t<=L.temp_c.ideal_max&&u>=L.umidade.ideal_min&&
     dt>=L.delta_t.ideal[0]&&dt<=L.delta_t.ideal[1])return'favoravel';return'atencao';}
function reclassificar(){DADOS.cidades.forEach(c=>{c.serie.forEach(p=>{p.classe=classificar(p.temp_c,p.umidade,p.vento_kmh,p.precip_mm,p.delta_t);});c._hora=null;});}

const dois=n=>String(n).padStart(2,'0');
const diaISO=d=>d.getFullYear()+'-'+dois(d.getMonth()+1)+'-'+dois(d.getDate());
const fmtDia=s=>{const d=new Date(s+'T00:00');return d.toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'2-digit'});};
const fmtHora=s=>{const d=new Date(s);return d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+' '+dois(d.getHours())+'h';};
const idxCor=c=>DADOS.cidades.findIndex(x=>x.id===c.id);
const ativasLista=()=>DADOS.cidades.filter(c=>ativas.has(c.id));
const lt=(k,v)=>'<div class="r">'+k+': <b style="color:var(--ink)">'+v+'</b></div>';

function interpor(serie){if(serie.length<2)return serie.slice();
  const t=serie.map(p=>new Date(p.data).getTime());const out=[];let j=0;
  for(let ms=t[0];ms<=t[t.length-1];ms+=3600000){while(j<serie.length-2&&t[j+1]<=ms)j++;
    const a=serie[j],b=serie[j+1],f=t[j+1]>t[j]?(ms-t[j])/(t[j+1]-t[j]):0,L=k=>a[k]+(b[k]-a[k])*f;
    const temp=+L('temp_c').toFixed(1),umid=Math.round(L('umidade')),vento=+L('vento_kmh').toFixed(1),
      precip=+L('precip_mm').toFixed(2),dt=+L('delta_t').toFixed(2);
    out.push({data:new Date(ms).toISOString(),temp_c:temp,umidade:umid,vento_kmh:vento,precip_mm:precip,delta_t:dt,
      classe:classificar(temp,umid,vento,precip,dt)});}
  return out;}
function serieHora(c){if(!c._hora)c._hora=interpor(c.serie);return c._hora;}
function diasDisponiveis(){const s=new Set();DADOS.cidades.forEach(c=>c.serie.forEach(p=>s.add(diaISO(new Date(p.data)))));return[...s].sort();}
function resumo(serie){const fav=serie.filter(p=>p.classe==='favoravel');
  return{fav:fav.length,ate:serie.filter(p=>p.classe==='atencao').length,des:serie.filter(p=>p.classe==='desfavoravel').length,
    tot:serie.length,prox:fav.length?fav[0].data:null,chuva:+serie.reduce((s,p)=>s+(p.precip_mm>0?p.precip_mm:0),0).toFixed(1)};}
function janelasContiguas(pts){const out=[];let ini=null;
  for(let i=0;i<pts.length;i++){if(pts[i].classe==='favoravel'){if(ini===null)ini=pts[i];}
    else if(ini!==null){out.push([ini,pts[i-1]]);ini=null;}}
  if(ini!==null)out.push([ini,pts[pts.length-1]]);return out;}

/* cabeçalho */
function renderCabecalho(){
  $('titulo').textContent=PAGINA==='panorama'?'Panorama agrícola — Sudeste':'Janela de aplicação de herbicida — Sudeste';
  $('meta').textContent='Gerado em '+DADOS.gerado_em.replace('T',' ')+' • '+DADOS.regiao+
    ' • Atualiza 3x/dia (07h, 12h, 15h) • Requisições: '+DADOS.requisicoes_usadas+'/'+DADOS.limite_requisicoes;
  $('fonte').textContent='Fonte: '+DADOS.fonte;
  $('banner').innerHTML=DADOS.exemplo?'<div class="banner"><b>Dados de exemplo.</b> Configure as chaves da ClimAPI para ver a previsão real.</div>':'';
}

/* atualizar */
const btnAtu=$('atualizar'),elStatus=$('status');
try{if(sessionStorage.getItem('recarregado')){sessionStorage.removeItem('recarregado');
  elStatus.textContent='Mostrando a última publicação automática (atualiza sozinha às 07h, 12h e 15h).';}}catch(_){}
if(btnAtu)btnAtu.onclick=async()=>{btnAtu.disabled=true;elStatus.className='';elStatus.textContent='Atualizando…';
  let r=null,novo=null;
  try{r=await fetch('api/atualizar',{method:'POST'});try{novo=await r.json();}catch(_){}}catch(_){}
  if(novo&&novo.erro){elStatus.className='err';elStatus.textContent='A previsão ao vivo falhou: '+novo.erro;btnAtu.disabled=false;return;}
  if(novo&&r&&r.ok){ // backend disponível: atualização ao vivo
    Object.assign(DADOS,novo);ativas=new Set(DADOS.cidades.map(c=>c.id));
    reclassificar();if($('cidades'))montarCidades();renderCabecalho();render();
    elStatus.textContent='Atualizado ao vivo em '+DADOS.gerado_em.replace('T',' ');btnAtu.disabled=false;return;}
  // sem backend (GitHub Pages): recarrega a última publicação automática
  try{sessionStorage.setItem('recarregado','1');}catch(_){}
  location.reload();};

/* cidades / data / recomendações (página janelas) */
function montarCidades(){const el=$('cidades');if(!el)return;el.innerHTML='';
  DADOS.cidades.forEach((c,i)=>{const b=document.createElement('button');b.className='chip';
    b.setAttribute('aria-pressed',ativas.has(c.id)?'true':'false');
    b.innerHTML='<span class="dot" style="background:'+CORES[i]+'"></span>'+c.nome+'/'+c.uf;
    b.onclick=()=>{ativas.has(c.id)?ativas.delete(c.id):ativas.add(c.id);
      b.setAttribute('aria-pressed',ativas.has(c.id)?'true':'false');render();};el.appendChild(b);});}
const inpDia=$('dia');
function initData(){if(!inpDia)return;const dias=diasDisponiveis();inpDia.min='2026-07-01';
  if(dias.length)inpDia.max=dias[dias.length-1];const hoje=diaISO(new Date(DADOS.gerado_em));
  inpDia.value=dias.includes(hoje)?hoje:(dias[0]||hoje);inpDia.onchange=()=>renderDia();}

/* KPIs */
function renderKpis(){const el=$('kpis');if(!el)return;el.innerHTML='';
  const lst=$('cidades')?ativasLista():DADOS.cidades;
  lst.forEach(c=>{const r=resumo(c.serie),prox=r.prox?fmtHora(r.prox):'—';
    const d=document.createElement('div');d.className='kpi';
    d.innerHTML='<div class="city"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div>'+
      '<div class="big"><span class="n">'+r.fav+'</span><span class="l">passos favoráveis (de '+r.tot+')</span></div>'+
      '<div class="line"><span>Próxima janela</span><b>'+prox+'</b></div>'+
      '<div class="line"><span>Chuva prevista</span><b>'+r.chuva+' mm</b></div>'+
      '<div class="line"><span>Distribuição</span><span><span class="pill f">'+r.fav+'</span> <span class="pill a">'+r.ate+'</span> <span class="pill d">'+r.des+'</span></span></div>';
    el.appendChild(d);});}

/* Minhas janelas do dia */
function renderDia(){const host=$('dia-view');if(!host||!inpDia)return;const dia=inpDia.value;
  $('diaTitulo').textContent='— '+fmtDia(dia);host.innerHTML='';
  ativasLista().forEach(c=>{const pts=serieHora(c).filter(p=>diaISO(new Date(p.data))===dia);
    const box=document.createElement('div');box.className='diaCity';
    let html='<div class="nome"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div>';
    if(!pts.length){box.innerHTML=html+'<div class="nowin">Sem previsão para este dia (a previsão cobre os próximos dias a partir de hoje).</div>';host.appendChild(box);return;}
    box.innerHTML=html;box.appendChild(faixaDia(pts,c));
    const wins=janelasContiguas(pts),jd=document.createElement('div');jd.className='janelas';
    if(wins.length)wins.forEach(([a,b])=>{const j=document.createElement('span');j.className='win';
      const hb=new Date(b.data);hb.setHours(hb.getHours()+1);
      j.innerHTML='🟢 <b>'+dois(new Date(a.data).getHours())+'h–'+dois(hb.getHours()%24||24)+'h</b>';jd.appendChild(j);});
    else{const n=document.createElement('span');n.className='nowin';n.textContent='Sem janela favorável neste dia.';jd.appendChild(n);}
    box.appendChild(jd);
    const chuva=+pts.reduce((s,p)=>s+(p.precip_mm>0?p.precip_mm:0),0).toFixed(1);
    const pico=pts.reduce((m,p)=>p.precip_mm>m.precip_mm?p:m,pts[0]);
    const ci=document.createElement('div');ci.className='chuvinfo';
    ci.innerHTML=chuva>0?'🌧️ Chuva prevista no dia: <b>'+chuva+' mm</b> (pico ~'+dois(new Date(pico.data).getHours())+'h)':'☀️ Sem chuva relevante prevista neste dia.';
    box.appendChild(ci);host.appendChild(box);});}
function faixaDia(pts,c){const n=pts.length,W=1000,H=44,pl=4,pr=4,hb=26,iw=(W-pl-pr)/Math.max(1,n);let rects='',ticks='';
  const cm=V('--muted');
  pts.forEach((p,i)=>{const x=pl+i*iw;rects+='<rect x="'+(x+.5)+'" y="0" width="'+Math.max(.5,iw-1)+'" height="'+hb+'" rx="1.5" fill="'+ST(p.classe)+'" data-i="'+i+'"></rect>';
    const h=new Date(p.data).getHours();if(h%3===0)ticks+='<text x="'+(x+iw/2)+'" y="'+(H-4)+'" text-anchor="middle" fill="'+cm+'" font-size="10">'+dois(h)+'h</text>';});
  const wrap=document.createElement('div');wrap.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" style="height:44px">'+rects+ticks+'</svg>';
  const svg=wrap.firstChild;svg.addEventListener('mousemove',e=>{const t=e.target;if(t.tagName!=='rect'){hideTip();return;}
    const p=pts[+t.dataset.i];showTip(e,'<b>'+c.nome+' • '+dois(new Date(p.data).getHours())+'h</b><div class="r"><span class="dot" style="background:'+STATUS[p.classe]+'"></span>'+ROTULO[p.classe]+'</div>'+
      lt('Temperatura',p.temp_c+' °C')+lt('Umidade',p.umidade+' %')+lt('Vento',p.vento_kmh+' km/h')+lt('Delta-T',p.delta_t+' °C')+lt('Chuva',p.precip_mm+' mm'));});
  svg.addEventListener('mouseleave',hideTip);return svg;}

/* visão geral (nativa) */
function renderTimelines(){const host=$('timelines');if(!host)return;host.innerHTML='';
  const cm=V('--muted'),cs=V('--surface');
  ativasLista().forEach(c=>{const serie=c.serie,n=serie.length,W=1000,H=34,pl=4,pr=4,hb=24,iw=(W-pl-pr)/Math.max(1,n);let rects='',ticks='',ult='';
    serie.forEach((p,i)=>{const x=pl+i*iw;rects+='<rect x="'+(x+.5)+'" y="0" width="'+Math.max(.5,iw-1)+'" height="'+hb+'" rx="1.5" fill="'+ST(p.classe)+'" data-i="'+i+'"></rect>';});
    serie.forEach((p,i)=>{const d=new Date(p.data);if(d.toDateString()!==ult&&d.getHours()<3){const x=pl+i*iw;
      ticks+='<line x1="'+x+'" y1="0" x2="'+x+'" y2="'+hb+'" stroke="'+cs+'" stroke-width="2"/><text x="'+(x+3)+'" y="'+(H-2)+'" fill="'+cm+'" font-size="11">'+d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';ult=d.toDateString();}});
    const row=document.createElement('div');row.className='tl-row';
    row.innerHTML='<div class="name"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div><svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" style="height:34px">'+rects+ticks+'</svg>';
    const svg=row.querySelector('svg');svg.addEventListener('mousemove',e=>{const t=e.target;if(t.tagName!=='rect'){hideTip();return;}
      const p=serie[+t.dataset.i];showTip(e,'<b>'+c.nome+' • '+fmtHora(p.data)+'</b><div class="r"><span class="dot" style="background:'+STATUS[p.classe]+'"></span>'+ROTULO[p.classe]+'</div>'+
        lt('Temperatura',p.temp_c+' °C')+lt('Umidade',p.umidade+' %')+lt('Vento',p.vento_kmh+' km/h')+lt('Delta-T',p.delta_t+' °C')+lt('Chuva',p.precip_mm+' mm'));});
    svg.addEventListener('mouseleave',hideTip);host.appendChild(row);});}

/* gráficos de linha */
function metricas(){return[
  {key:'temp_c',titulo:'Temperatura',unidade:'°C',band:{max:LIM.temp_c.ideal_max},dec:0},
  {key:'umidade',titulo:'Umidade relativa',unidade:'%',band:{min:LIM.umidade.ideal_min},dec:0},
  {key:'vento_kmh',titulo:'Velocidade do vento',unidade:'km/h',band:{min:LIM.vento_kmh.ideal[0],max:LIM.vento_kmh.ideal[1]},dec:0},
  {key:'delta_t',titulo:'Delta-T (pulverização)',unidade:'°C',band:{min:LIM.delta_t.ideal[0],max:LIM.delta_t.ideal[1]},dec:1},
  {key:'precip_mm',titulo:'Previsão de chuva',unidade:'mm',band:{max:LIM.precip_mm_max},dec:1,fill:true},
];}
function renderCharts(){const host=$('charts');if(!host)return;host.innerHTML='';const cid=ativasLista();
  metricas().forEach(m=>{const box=document.createElement('div');box.className='chart';
    box.innerHTML='<h3>'+m.titulo+'</h3><p class="u">'+m.unidade+'</p>';box.appendChild(chartSVG(m,cid));host.appendChild(box);});}
function chartSVG(m,cidades){const W=500,H=250,pl=40,pr=12,pt=12,pb=26,iw=W-pl-pr,ih=H-pt-pb;
  const sc=cidades.map(c=>c.serie),ref=sc[0]||DADOS.cidades[0].serie,n=ref.length;let vals=[];
  sc.forEach(s=>s.forEach(p=>vals.push(p[m.key])));if(m.band.min!=null)vals.push(m.band.min);if(m.band.max!=null)vals.push(m.band.max);if(m.key==='precip_mm')vals.push(0);
  let ymin=Math.min(...vals),ymax=Math.max(...vals);const pad=(ymax-ymin)*.08||1;ymin-=pad;ymax+=pad;
  const X=i=>pl+(n<=1?0:i/(n-1)*iw),Y=v=>pt+(1-(v-ymin)/(ymax-ymin))*ih;
  const CB=V('--band'),CG=V('--grid'),CM=V('--muted'),CA=V('--axis');
  let s='<svg viewBox="0 0 '+W+' '+H+'" role="img">';
  const yTop=Y(m.band.max!=null?m.band.max:ymax),yBot=Y(m.band.min!=null?m.band.min:ymin);
  s+='<rect x="'+pl+'" y="'+yTop+'" width="'+iw+'" height="'+Math.max(0,yBot-yTop)+'" fill="'+CB+'"/>';
  if(m.band.min!=null)s+=lref(pl,iw,Y(m.band.min));if(m.band.max!=null)s+=lref(pl,iw,Y(m.band.max));
  for(let g=0;g<=4;g++){const v=ymin+(ymax-ymin)*g/4,y=Y(v);
    s+='<line x1="'+pl+'" y1="'+y+'" x2="'+(W-pr)+'" y2="'+y+'" stroke="'+CG+'" stroke-width="1"/><text x="'+(pl-6)+'" y="'+(y+4)+'" text-anchor="end" fill="'+CM+'" font-size="11">'+v.toFixed(m.dec)+'</text>';}
  let ult='';ref.forEach((p,i)=>{const d=new Date(p.data);if(d.toDateString()!==ult&&d.getHours()<3){s+='<text x="'+X(i)+'" y="'+(H-8)+'" fill="'+CM+'" font-size="11">'+d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';ult=d.toDateString();}});
  cidades.forEach((c,ci)=>{const cor=COR(idxCor(c));let d='';sc[ci].forEach((p,i)=>{d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(p[m.key]).toFixed(1)+' ';});
    if(m.fill){const yb=Y(ymin<0?0:ymin);s+='<path d="'+d+'L'+X(sc[ci].length-1).toFixed(1)+' '+yb+' L'+X(0).toFixed(1)+' '+yb+' Z" fill="'+cor+'" opacity="0.12"/>';}
    s+='<path d="'+d+'" fill="none" stroke="'+cor+'" stroke-width="2" stroke-linejoin="round"/>';});
  s+='<line id="cx" x1="0" y1="'+pt+'" x2="0" y2="'+(pt+ih)+'" stroke="'+CA+'" stroke-width="1" opacity="0"/><rect x="'+pl+'" y="'+pt+'" width="'+iw+'" height="'+ih+'" fill="transparent"/></svg>';
  const tpl=document.createElement('template');tpl.innerHTML=s.trim();const svg=tpl.content.firstChild;
  const cx=svg.querySelector('#cx'),ov=svg.querySelector('rect[fill="transparent"]');
  ov.addEventListener('mousemove',e=>{const r=svg.getBoundingClientRect(),ratio=W/r.width;let i=Math.round(((e.clientX-r.left)*ratio-pl)/iw*(n-1));i=Math.max(0,Math.min(n-1,i));
    cx.setAttribute('x1',X(i));cx.setAttribute('x2',X(i));cx.setAttribute('opacity','1');let html='<b>'+fmtHora(ref[i].data)+'</b>';
    cidades.forEach((c,ci)=>{const p=sc[ci][i];if(!p)return;html+='<div class="r"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+': <b style="color:var(--ink)">'+p[m.key].toFixed(m.dec)+' '+m.unidade+'</b></div>';});showTip(e,html);});
  ov.addEventListener('mouseleave',()=>{cx.setAttribute('opacity','0');hideTip();});return svg;}
const lref=(x,w,y)=>'<line x1="'+x+'" y1="'+y+'" x2="'+(x+w)+'" y2="'+y+'" stroke="'+V('--azul')+'" stroke-width="1" stroke-dasharray="4 3" opacity="0.45"/>';

/* editor de recomendações */
const REC=[
  {t:'Vento (km/h)',campos:[['vento_kmh.ideal.0','Ideal mín'],['vento_kmh.ideal.1','Ideal máx'],['vento_kmh.aceitavel.0','Aceit. mín'],['vento_kmh.aceitavel.1','Aceit. máx']]},
  {t:'Temperatura (°C)',campos:[['temp_c.ideal_max','Ideal até'],['temp_c.aceitavel_max','Aceit. até']]},
  {t:'Umidade relativa (%)',campos:[['umidade.ideal_min','Ideal a partir'],['umidade.aceitavel_min','Aceit. a partir']]},
  {t:'Delta-T (°C)',campos:[['delta_t.ideal.0','Ideal mín'],['delta_t.ideal.1','Ideal máx'],['delta_t.aceitavel.0','Aceit. mín'],['delta_t.aceitavel.1','Aceit. máx']]},
  {t:'Chuva (mm)',campos:[['precip_mm_max','Máx. sem chuva']]}];
const getP=(o,p)=>p.split('.').reduce((x,k)=>x==null?undefined:x[k],o);
function setP(o,p,v){const ks=p.split('.'),last=ks.pop();ks.reduce((x,k)=>x[k],o)[last]=v;}
function renderRec(){const el=$('rec');if(!el)return;let h='<div class="recgrid">';
  REC.forEach(g=>{h+='<div class="recbox"><h4>'+g.t+'</h4>';g.campos.forEach(([p,lab])=>{h+='<div class="recline"><span style="flex:1">'+lab+'</span><input type="text" inputmode="decimal" data-path="'+p+'" value="'+getP(LIM,p)+'"></div>';});h+='</div>';});
  h+='</div><div class="recact"><button class="btn" id="recSalvar">Aplicar</button><button class="linkbtn" id="recPadrao">Restaurar padrão</button><span class="sub" style="align-self:center">Recalcula as janelas e salva neste navegador.</span></div>';
  el.innerHTML=h;
  el.querySelector('#recSalvar').onclick=()=>{try{
    el.querySelectorAll('input[data-path]').forEach(i=>{const v=parseFloat(String(i.value).replace(',','.'));if(!isNaN(v))setP(LIM,i.dataset.path,v);});
    salvarLim();reclassificar();render();
    if(elStatus){elStatus.className='';elStatus.textContent='✓ Recomendações aplicadas — janelas recalculadas.';}
  }catch(err){if(elStatus){elStatus.className='err';elStatus.textContent='Não foi possível aplicar: '+err.message;}}};
  el.querySelector('#recPadrao').onclick=()=>{LIM=padraoLim();salvarLim();renderRec();reclassificar();render();
    if(elStatus){elStatus.className='';elStatus.textContent='↺ Recomendações restauradas para o padrão.';}};}
if($('abrirRec'))$('abrirRec').onclick=()=>{const r=$('rec');r.hidden=!r.hidden;if(!r.hidden)renderRec();};

/* ---------- PANORAMA ---------- */
function renderNoticias(){const el=$('noticias');if(!el)return;const ns=DADOS.noticias||[];
  if(!ns.length){el.innerHTML='<div class="nowin">Sem notícias no momento. Fonte: Google Notícias (agro/defensivos).</div>';return;}
  el.innerHTML=ns.map(n=>'<a class="na" href="'+n.link+'" target="_blank" rel="noopener"><span class="t">'+n.titulo+'</span>'+
    '<span class="m"><span>'+(n.fonte||'Google Notícias')+'</span><span>'+(n.data||'')+'</span></span></a>').join('');}

function renderRanking(){const el=$('ranking');if(!el)return;const agora=new Date(DADOS.gerado_em).getTime();const linhas=[];
  DADOS.cidades.forEach(c=>{janelasContiguas(c.serie).forEach(([a,b])=>{const fim=new Date(b.data);
    if(fim.getTime()>=agora)linhas.push({c,a,b});});});
  linhas.sort((x,y)=>new Date(x.a.data)-new Date(y.a.data));
  if(!linhas.length){el.innerHTML='<div class="nowin">Nenhuma janela favorável nos próximos dias com as recomendações atuais.</div>';return;}
  el.innerHTML=linhas.slice(0,10).map(({c,a,b})=>{const ha=new Date(a.data),hb=new Date(b.data);
    return '<div class="rk"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+
      '<span class="cidade">'+c.nome+'/'+c.uf+'</span>'+
      '<span class="quando">'+ha.toLocaleDateString('pt-BR',{weekday:'short',day:'2-digit',month:'2-digit'})+' • '+dois(ha.getHours())+'h–'+dois(hb.getHours())+'h</span>'+
      '</div>';}).join('');}

function renderBarrasDia(){const host=$('barras-dia');if(!host)return;const cid=DADOS.cidades;const dias=diasDisponiveis();
  const leg=$('barras-leg');if(leg)leg.innerHTML=cid.map(c=>'<span><i style="background:'+CORES[idxCor(c)]+'"></i>'+c.nome+'</span>').join('');
  const dados=dias.map(d=>cid.map(c=>c.serie.filter(p=>diaISO(new Date(p.data))===d&&p.classe==='favoravel').length));
  const maxV=Math.max(1,...dados.flat());
  const W=900,H=250,pl=30,pr=10,pt=10,pb=34,iw=W-pl-pr,ih=H-pt-pb;
  const gw=iw/Math.max(1,dias.length),bw=Math.min(26,(gw-10)/Math.max(1,cid.length));
  const CG=V('--grid'),CM=V('--muted');
  let s='<svg viewBox="0 0 '+W+' '+H+'" role="img">';
  for(let g=0;g<=4;g++){const v=maxV*g/4,y=pt+ih-(v/maxV)*ih;s+='<line x1="'+pl+'" y1="'+y+'" x2="'+(W-pr)+'" y2="'+y+'" stroke="'+CG+'"/><text x="'+(pl-6)+'" y="'+(y+4)+'" text-anchor="end" fill="'+CM+'" font-size="11">'+Math.round(v)+'</text>';}
  dias.forEach((d,gi)=>{const x0=pl+gi*gw+(gw-bw*cid.length)/2;
    cid.forEach((c,ci)=>{const v=dados[gi][ci],h=(v/maxV)*ih,x=x0+ci*bw,y=pt+ih-h;
      s+='<rect x="'+(x+1)+'" y="'+y+'" width="'+(bw-2)+'" height="'+h+'" rx="2" fill="'+COR(idxCor(c))+'"><title>'+c.nome+' • '+v+' favoráveis</title></rect>';});
    const dd=new Date(d+'T00:00');s+='<text x="'+(pl+gi*gw+gw/2)+'" y="'+(H-12)+'" text-anchor="middle" fill="'+CM+'" font-size="11">'+dd.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';});
  s+='</svg>';host.innerHTML=s;}

function renderAgora(){const el=$('agora');if(!el)return;el.innerHTML='';
  DADOS.cidades.forEach(c=>{const p=c.serie[0];if(!p)return;const cls=p.classe;
    const d=document.createElement('div');d.className='kpi';
    d.innerHTML='<div class="city"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+
      ' <span class="pill '+(cls==='favoravel'?'f':cls==='atencao'?'a':'d')+'" style="margin-left:auto">'+ROTULO[cls]+'</span></div>'+
      '<div class="line"><span>Temperatura</span><b>'+p.temp_c+' °C</b></div>'+
      '<div class="line"><span>Umidade</span><b>'+p.umidade+' %</b></div>'+
      '<div class="line"><span>Vento</span><b>'+p.vento_kmh+' km/h</b></div>'+
      '<div class="line"><span>Delta-T</span><b>'+p.delta_t+' °C</b></div>'+
      '<div class="line"><span>Chuva</span><b>'+p.precip_mm+' mm</b></div>';
    el.appendChild(d);});}

/* tooltip / tema */
function showTip(e,html){tip.innerHTML=html;tip.style.opacity='1';let x=e.clientX+14,y=e.clientY+14;const r=tip.getBoundingClientRect();
  if(x+r.width>innerWidth)x=e.clientX-r.width-14;if(y+r.height>innerHeight)y=e.clientY-r.height-14;tip.style.left=x+'px';tip.style.top=y+'px';}
function hideTip(){tip.style.opacity='0';}
function temaEfetivo(){const a=document.documentElement.getAttribute('data-theme');
  if(a==='dark'||a==='light')return a;
  return matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}
$('tema').onclick=()=>{document.documentElement.setAttribute('data-theme',temaEfetivo()==='dark'?'light':'dark');render();};

function render(){renderKpis();renderDia();renderTimelines();renderCharts();renderNoticias();renderRanking();renderBarrasDia();renderAgora();}
$('foot').innerHTML='Delta-T ideal 2–8 °C • vento 3–10 km/h • temperatura ≤ 28 °C • umidade ≥ 60 % (ajustáveis em “Minhas recomendações”). '+
  'Sempre confira a bula do produto. Grupo Moreno — Fortalecer · Conectar · Crescer. Previsão: Embrapa ClimAPI (NCEP/GFS); notícias: Google Notícias.';

reclassificar();montarCidades();initData();renderCabecalho();render();
"""


def gerar(resultado: dict) -> None:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    # Escapa "</" para não fechar o <script> caso um título de notícia contenha.
    dados_json = json.dumps(resultado, ensure_ascii=False).replace("</", "<\\/")
    (config.DOCS_DIR / "index.html").write_text(
        _documento("janelas", _BODY_JANELAS, dados_json), encoding="utf-8")
    (config.DOCS_DIR / "panorama.html").write_text(
        _documento("panorama", _BODY_PANORAMA, dados_json), encoding="utf-8")
