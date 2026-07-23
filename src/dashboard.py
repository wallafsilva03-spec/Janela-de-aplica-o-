"""Gera o painel HTML autossuficiente (sem dependências externas / CDN).

Página completa com:
  - seletor de cidades;
  - seletor de data ("meu dia") a partir de 01/07;
  - "Minhas janelas do dia": semáforo hora a hora SÓ do dia escolhido, com a
    lista de faixas de horário favoráveis;
  - visão geral da previsão (passos nativos) em semáforo por cidade;
  - gráficos de temperatura, umidade, vento, Delta-T e CHUVA, com faixa ideal;
  - editor "Minhas recomendações": o usuário ajusta os limiares e tudo é
    reclassificado ao vivo (salvo no navegador).

Cores: paleta validada para daltonismo — status verde/amarelo/vermelho no
semáforo; azul/laranja/aqua para as cidades.
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
    --plane:#f6f7f4; --surface:#fcfcfb; --surface2:#f1f1ec;
    --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
    --grid:#e6e5df; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
    --good:#0ca30c; --warn:#fab219; --crit:#d03b3b;
    --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --rain:#256abf;
    --shadow:0 1px 2px rgba(11,11,11,.04),0 8px 24px rgba(11,11,11,.06);
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --plane:#0d0d0d; --surface:#1a1a19; --surface2:#232321;
    --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --rain:#3987e5;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.4);
  }}
  :root[data-theme="dark"]{
    --plane:#0d0d0d; --surface:#1a1a19; --surface2:#232321;
    --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --rain:#3987e5;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.4);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--plane);color:var(--ink);
    font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
  .wrap{max-width:1120px;margin:0 auto;padding:22px 18px 72px}
  h1{font-size:23px;margin:0 0 4px;letter-spacing:-.01em}
  h2{font-size:16px;margin:0 0 14px;letter-spacing:-.01em}
  .sub{color:var(--muted);font-weight:400;font-size:13px}
  header p{margin:2px 0;color:var(--ink2);font-size:13px}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:16px;
    padding:18px 20px;margin:16px 0;box-shadow:var(--shadow)}
  .banner{background:color-mix(in srgb,var(--warn) 16%,var(--surface));
    border:1px solid var(--border);border-radius:12px;padding:10px 14px;margin:14px 0;font-size:13px}
  .topbar{float:right;display:flex;gap:8px;align-items:center}
  .toggle,.btn,.linkbtn{font-size:12px;color:var(--ink2);cursor:pointer;border:1px solid var(--border);
    border-radius:999px;padding:7px 13px;background:var(--surface)}
  .btn{color:#fff;background:var(--c1);border-color:transparent;font-weight:600}
  .btn:disabled{opacity:.55;cursor:progress}
  #status{display:block;clear:both;text-align:right;font-size:12px;color:var(--ink2);min-height:16px;padding-top:6px}
  #status.err{color:var(--crit)}
  /* controles */
  .row{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end}
  .field{display:flex;flex-direction:column;gap:6px}
  .field label{font-size:12px;color:var(--ink2);font-weight:600}
  .cidades{display:flex;flex-wrap:wrap;gap:8px}
  .chip{display:inline-flex;align-items:center;gap:8px;cursor:pointer;border:1px solid var(--border);
    border-radius:999px;padding:7px 14px;background:var(--surface);user-select:none;font-size:14px}
  .chip .dot{width:12px;height:12px;border-radius:50%;flex:none}
  .chip[aria-pressed="false"]{opacity:.4}
  input[type=date]{font:inherit;padding:7px 10px;border:1px solid var(--border);border-radius:10px;
    background:var(--surface);color:var(--ink)}
  /* legenda */
  .leg{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:var(--ink2);align-items:center}
  .leg span{display:inline-flex;align-items:center;gap:7px}
  .leg i{width:14px;height:14px;border-radius:4px;display:inline-block}
  /* kpis */
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
  .kpi{border:1px solid var(--border);border-radius:14px;padding:14px 16px;background:var(--surface2)}
  .kpi .city{font-size:13px;display:inline-flex;align-items:center;gap:7px;margin-bottom:8px;font-weight:600}
  .kpi .city .dot{width:11px;height:11px;border-radius:50%}
  .kpi .big{display:flex;align-items:baseline;gap:8px}
  .kpi .n{font-size:30px;font-weight:680;letter-spacing:-.02em}
  .kpi .l{font-size:12px;color:var(--ink2)}
  .kpi .line{font-size:12.5px;color:var(--ink2);margin-top:8px;display:flex;justify-content:space-between;gap:8px}
  .kpi .line b{color:var(--ink)}
  .pill{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600}
  .pill.f{background:color-mix(in srgb,var(--good) 20%,transparent);color:var(--good)}
  .pill.a{background:color-mix(in srgb,var(--warn) 26%,transparent);color:#8a5a00}
  .pill.d{background:color-mix(in srgb,var(--crit) 18%,transparent);color:var(--crit)}
  /* dia */
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
  /* editor de recomendações */
  .rec{margin-top:6px}
  .rec[hidden]{display:none}
  .recgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:6px}
  .recbox{border:1px solid var(--border);border-radius:12px;padding:12px 14px;background:var(--surface2)}
  .recbox h4{margin:0 0 10px;font-size:13px}
  .recline{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:13px;color:var(--ink2)}
  .recline input{width:64px;font:inherit;padding:5px 8px;border:1px solid var(--border);border-radius:8px;
    background:var(--surface);color:var(--ink);text-align:right}
  .recact{display:flex;gap:10px;margin-top:14px}
  .tip{position:fixed;pointer-events:none;z-index:20;background:var(--surface);border:1px solid var(--border);
    border-radius:10px;padding:8px 10px;font-size:12px;box-shadow:var(--shadow);opacity:0;transition:opacity .08s;max-width:250px}
  .tip b{display:block;margin-bottom:4px;color:var(--ink)}
  .tip .r{display:flex;align-items:center;gap:6px;color:var(--ink2)}
  .tip .r .dot{width:9px;height:9px;border-radius:50%}
  .foot{color:var(--muted);font-size:12px;margin-top:24px}
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
    <div class="row">
      <div class="field" style="flex:1 1 320px">
        <label>Cidades <span class="sub">— clique para mostrar/ocultar</span></label>
        <div class="cidades" id="cidades"></div>
      </div>
      <div class="field">
        <label for="dia">Meu dia</label>
        <input type="date" id="dia">
      </div>
      <div class="field">
        <label>&nbsp;</label>
        <button class="linkbtn" id="abrirRec">⚙︎ Minhas recomendações</button>
      </div>
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
      <span class="sub">• detalhamento hora a hora só do dia escolhido</span>
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

  <p class="foot" id="foot"></p>
</div>
<div class="tip" id="tip"></div>

<script id="dados" type="application/json">__DADOS__</script>
<script>
const DADOS = JSON.parse(document.getElementById('dados').textContent);
const CORES=['var(--c1)','var(--c2)','var(--c3)','#eda100','#e87ba4'];
const STATUS={favoravel:'var(--good)',atencao:'var(--warn)',desfavoravel:'var(--crit)'};
const ROTULO={favoravel:'Favorável',atencao:'Atenção',desfavoravel:'Desfavorável'};
const tip=document.getElementById('tip');
let ativas=new Set(DADOS.cidades.map(c=>c.id));

/* ---------- limiares (recomendações), editáveis e persistidos ---------- */
function padraoLim(){return JSON.parse(JSON.stringify(DADOS.limiares));}
let LIM;
try{LIM=JSON.parse(localStorage.getItem('limiares_janela'))||padraoLim();}catch(e){LIM=padraoLim();}
function salvarLim(){try{localStorage.setItem('limiares_janela',JSON.stringify(LIM));}catch(e){}}

function classificar(t,u,v,p,dt){
  const L=LIM;
  if(p>L.precip_mm_max) return 'desfavoravel';
  if(v<L.vento_kmh.aceitavel[0]||v>L.vento_kmh.aceitavel[1]) return 'desfavoravel';
  if(t>L.temp_c.aceitavel_max) return 'desfavoravel';
  if(u<L.umidade.aceitavel_min) return 'desfavoravel';
  if(dt<L.delta_t.aceitavel[0]||dt>L.delta_t.aceitavel[1]) return 'desfavoravel';
  if(v>=L.vento_kmh.ideal[0]&&v<=L.vento_kmh.ideal[1]&&t<=L.temp_c.ideal_max&&
     u>=L.umidade.ideal_min&&dt>=L.delta_t.ideal[0]&&dt<=L.delta_t.ideal[1]) return 'favoravel';
  return 'atencao';
}
function reclassificar(){
  DADOS.cidades.forEach(c=>{
    c.serie.forEach(p=>{p.classe=classificar(p.temp_c,p.umidade,p.vento_kmh,p.precip_mm,p.delta_t);});
    c._hora=null; // invalida cache horário
  });
}

/* ---------- utilidades de tempo ---------- */
const dois=n=>String(n).padStart(2,'0');
const diaISO=d=>d.getFullYear()+'-'+dois(d.getMonth()+1)+'-'+dois(d.getDate());
const fmtDia=s=>{const d=new Date(s+'T00:00');return d.toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'2-digit'});};
const fmtHora=s=>{const d=new Date(s);return d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+' '+dois(d.getHours())+'h';};
const idxCor=c=>DADOS.cidades.findIndex(x=>x.id===c.id);
const ativasLista=()=>DADOS.cidades.filter(c=>ativas.has(c.id));

/* ---------- interpolação horária (para o dia selecionado) ---------- */
function interpor(serie){
  if(serie.length<2) return serie.slice();
  const t=serie.map(p=>new Date(p.data).getTime());
  const out=[];let j=0;
  for(let ms=t[0];ms<=t[t.length-1];ms+=3600000){
    while(j<serie.length-2&&t[j+1]<=ms) j++;
    const a=serie[j],b=serie[j+1],f=t[j+1]>t[j]?(ms-t[j])/(t[j+1]-t[j]):0;
    const L=k=>a[k]+(b[k]-a[k])*f;
    const temp=+L('temp_c').toFixed(1),umid=Math.round(L('umidade')),vento=+L('vento_kmh').toFixed(1),
      precip=+L('precip_mm').toFixed(2),dt=+L('delta_t').toFixed(2);
    out.push({data:new Date(ms).toISOString(),temp_c:temp,umidade:umid,vento_kmh:vento,precip_mm:precip,
      delta_t:dt,classe:classificar(temp,umid,vento,precip,dt)});
  }
  return out;
}
function serieHora(c){if(!c._hora)c._hora=interpor(c.serie);return c._hora;}

/* ---------- cabeçalho ---------- */
function renderCabecalho(){
  document.getElementById('meta').textContent=
    'Gerado em '+DADOS.gerado_em.replace('T',' ')+' • '+DADOS.regiao+
    ' • Atualiza 3x/dia (07h, 12h, 15h) • Requisições: '+DADOS.requisicoes_usadas+'/'+DADOS.limite_requisicoes;
  document.getElementById('fonte').textContent='Fonte: '+DADOS.fonte;
  document.getElementById('banner').innerHTML=DADOS.exemplo
    ?'<div class="banner"><b>Dados de exemplo.</b> Configure as chaves da ClimAPI para ver a previsão real.</div>':'';
}

/* ---------- botão atualizar ---------- */
const btnAtu=document.getElementById('atualizar'),elStatus=document.getElementById('status');
btnAtu.onclick=async()=>{
  btnAtu.disabled=true;elStatus.className='';elStatus.textContent='Consultando a Embrapa ClimAPI…';
  try{
    const r=await fetch('api/atualizar',{method:'POST'});const novo=await r.json();
    if(!r.ok||novo.erro) throw new Error(novo.erro||('HTTP '+r.status));
    Object.assign(DADOS,novo);
    ativas=new Set(DADOS.cidades.filter(c=>ativas.has(c.id)).map(c=>c.id));
    if(!ativas.size) ativas=new Set(DADOS.cidades.map(c=>c.id));
    reclassificar();montarCidades();renderCabecalho();render();
    elStatus.textContent='Atualizado ao vivo em '+DADOS.gerado_em.replace('T',' ');
  }catch(e){
    elStatus.className='err';
    elStatus.textContent='Não foi possível atualizar ao vivo ('+e.message+'). Precisa do servidor: python -m src.servidor';
  }finally{btnAtu.disabled=false;}
};

/* ---------- seletor de cidades ---------- */
function montarCidades(){
  const el=document.getElementById('cidades');el.innerHTML='';
  DADOS.cidades.forEach((c,i)=>{
    const b=document.createElement('button');b.className='chip';
    b.setAttribute('aria-pressed',ativas.has(c.id)?'true':'false');
    b.innerHTML='<span class="dot" style="background:'+CORES[i]+'"></span>'+c.nome+'/'+c.uf;
    b.onclick=()=>{ativas.has(c.id)?ativas.delete(c.id):ativas.add(c.id);
      b.setAttribute('aria-pressed',ativas.has(c.id)?'true':'false');render();};
    el.appendChild(b);
  });
}

/* ---------- seletor de data ---------- */
const inpDia=document.getElementById('dia');
function diasDisponiveis(){
  const s=new Set();
  DADOS.cidades.forEach(c=>c.serie.forEach(p=>s.add(diaISO(new Date(p.data)))));
  return [...s].filter(Boolean).sort();
}
function initData(){
  const dias=diasDisponiveis();
  inpDia.min='2026-07-01';
  if(dias.length) inpDia.max=dias[dias.length-1];
  const hoje=diaISO(new Date(DADOS.gerado_em));
  inpDia.value=dias.includes(hoje)?hoje:(dias[0]||hoje);
  inpDia.onchange=()=>renderDia();
}

/* ---------- KPIs ---------- */
function resumo(serie){
  const fav=serie.filter(p=>p.classe==='favoravel');
  return {fav:fav.length,ate:serie.filter(p=>p.classe==='atencao').length,
    des:serie.filter(p=>p.classe==='desfavoravel').length,tot:serie.length,
    prox:fav.length?fav[0].data:null,
    chuva:+serie.reduce((s,p)=>s+(p.precip_mm>0?p.precip_mm:0),0).toFixed(1)};
}
function renderKpis(){
  const el=document.getElementById('kpis');el.innerHTML='';
  ativasLista().forEach(c=>{
    const r=resumo(c.serie),prox=r.prox?fmtHora(r.prox):'—';
    const d=document.createElement('div');d.className='kpi';
    d.innerHTML='<div class="city"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div>'+
      '<div class="big"><span class="n">'+r.fav+'</span><span class="l">passos favoráveis (de '+r.tot+')</span></div>'+
      '<div class="line"><span>Próxima janela</span><b>'+prox+'</b></div>'+
      '<div class="line"><span>Chuva prevista</span><b>'+r.chuva+' mm</b></div>'+
      '<div class="line"><span>Distribuição</span><span>'+
        '<span class="pill f">'+r.fav+'</span> <span class="pill a">'+r.ate+'</span> <span class="pill d">'+r.des+'</span></span></div>';
    el.appendChild(d);
  });
}

/* ---------- Minhas janelas do dia ---------- */
function janelasContiguas(pts){
  const out=[];let ini=null;
  for(let i=0;i<pts.length;i++){
    if(pts[i].classe==='favoravel'){if(ini===null)ini=pts[i];}
    else if(ini!==null){out.push([ini,pts[i-1]]);ini=null;}
  }
  if(ini!==null)out.push([ini,pts[pts.length-1]]);
  return out;
}
function renderDia(){
  const dia=inpDia.value;
  document.getElementById('diaTitulo').textContent='— '+fmtDia(dia);
  const host=document.getElementById('dia-view');host.innerHTML='';
  ativasLista().forEach(c=>{
    const pts=serieHora(c).filter(p=>diaISO(new Date(p.data))===dia);
    const box=document.createElement('div');box.className='diaCity';
    let html='<div class="nome"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div>';
    if(!pts.length){
      html+='<div class="nowin">Sem dados de previsão para este dia (a previsão cobre os próximos dias a partir de hoje).</div>';
      box.innerHTML=html;host.appendChild(box);return;
    }
    box.innerHTML=html;
    box.appendChild(faixaDia(pts,c));
    const wins=janelasContiguas(pts);
    const jd=document.createElement('div');jd.className='janelas';
    if(wins.length){
      wins.forEach(([a,b])=>{const j=document.createElement('span');j.className='win';
        const hb=new Date(b.data);hb.setHours(hb.getHours()+1);
        j.innerHTML='🟢 <b>'+dois(new Date(a.data).getHours())+'h–'+dois(hb.getHours()%24||24)+'h</b>';
        jd.appendChild(j);});
    }else{
      const n=document.createElement('span');n.className='nowin';n.textContent='Sem janela favorável neste dia.';jd.appendChild(n);
    }
    box.appendChild(jd);
    const chuva=+pts.reduce((s,p)=>s+(p.precip_mm>0?p.precip_mm:0),0).toFixed(1);
    const pico=pts.reduce((m,p)=>p.precip_mm>m.precip_mm?p:m,pts[0]);
    const ci=document.createElement('div');ci.className='chuvinfo';
    ci.innerHTML=chuva>0?'🌧️ Chuva prevista no dia: <b>'+chuva+' mm</b> (pico ~'+dois(new Date(pico.data).getHours())+'h)':'☀️ Sem chuva relevante prevista neste dia.';
    box.appendChild(ci);
    host.appendChild(box);
  });
}
function faixaDia(pts,c){
  const n=pts.length,W=1000,H=44,pl=4,pr=4,hb=26,iw=(W-pl-pr)/Math.max(1,n);
  let rects='',ticks='';
  pts.forEach((p,i)=>{const x=pl+i*iw;
    rects+='<rect x="'+(x+.5)+'" y="0" width="'+Math.max(.5,iw-1)+'" height="'+hb+'" rx="1.5" fill="'+STATUS[p.classe]+'" data-i="'+i+'"></rect>';
    const h=new Date(p.data).getHours();
    if(h%3===0){ticks+='<text x="'+(x+iw/2)+'" y="'+(H-4)+'" text-anchor="middle" fill="var(--muted)" font-size="10">'+dois(h)+'h</text>';}
  });
  const wrap=document.createElement('div');
  wrap.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" style="height:44px">'+rects+ticks+'</svg>';
  const svg=wrap.firstChild;
  svg.addEventListener('mousemove',e=>{const t=e.target;if(t.tagName!=='rect'){hideTip();return;}
    const p=pts[+t.dataset.i];showTip(e,'<b>'+c.nome+' • '+dois(new Date(p.data).getHours())+'h</b>'+
      '<div class="r"><span class="dot" style="background:'+STATUS[p.classe]+'"></span>'+ROTULO[p.classe]+'</div>'+
      lt('Temperatura',p.temp_c+' °C')+lt('Umidade',p.umidade+' %')+lt('Vento',p.vento_kmh+' km/h')+
      lt('Delta-T',p.delta_t+' °C')+lt('Chuva',p.precip_mm+' mm'));});
  svg.addEventListener('mouseleave',hideTip);
  return wrap.firstChild;
}
const lt=(k,v)=>'<div class="r">'+k+': <b style="color:var(--ink)">'+v+'</b></div>';

/* ---------- visão geral (passos nativos) ---------- */
function renderTimelines(){
  const host=document.getElementById('timelines');host.innerHTML='';
  ativasLista().forEach(c=>{
    const serie=c.serie,n=serie.length,W=1000,H=34,pl=4,pr=4,hb=24,iw=(W-pl-pr)/Math.max(1,n);
    let rects='',ticks='',ult='';
    serie.forEach((p,i)=>{const x=pl+i*iw;
      rects+='<rect x="'+(x+.5)+'" y="0" width="'+Math.max(.5,iw-1)+'" height="'+hb+'" rx="1.5" fill="'+STATUS[p.classe]+'" data-i="'+i+'"></rect>';});
    serie.forEach((p,i)=>{const d=new Date(p.data);if(d.toDateString()!==ult&&d.getHours()<3){const x=pl+i*iw;
      ticks+='<line x1="'+x+'" y1="0" x2="'+x+'" y2="'+hb+'" stroke="var(--surface)" stroke-width="2"/>';
      ticks+='<text x="'+(x+3)+'" y="'+(H-2)+'" fill="var(--muted)" font-size="11">'+d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';ult=d.toDateString();}});
    const row=document.createElement('div');row.className='tl-row';
    row.innerHTML='<div class="name"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+'/'+c.uf+'</div>'+
      '<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" style="height:34px">'+rects+ticks+'</svg>';
    const svg=row.querySelector('svg');
    svg.addEventListener('mousemove',e=>{const t=e.target;if(t.tagName!=='rect'){hideTip();return;}
      const p=serie[+t.dataset.i];showTip(e,'<b>'+c.nome+' • '+fmtHora(p.data)+'</b>'+
        '<div class="r"><span class="dot" style="background:'+STATUS[p.classe]+'"></span>'+ROTULO[p.classe]+'</div>'+
        lt('Temperatura',p.temp_c+' °C')+lt('Umidade',p.umidade+' %')+lt('Vento',p.vento_kmh+' km/h')+lt('Delta-T',p.delta_t+' °C')+lt('Chuva',p.precip_mm+' mm'));});
    svg.addEventListener('mouseleave',hideTip);
    host.appendChild(row);
  });
}

/* ---------- gráficos ---------- */
function metricas(){return[
  {key:'temp_c',titulo:'Temperatura',unidade:'°C',band:{max:LIM.temp_c.ideal_max},dec:0},
  {key:'umidade',titulo:'Umidade relativa',unidade:'%',band:{min:LIM.umidade.ideal_min},dec:0},
  {key:'vento_kmh',titulo:'Velocidade do vento',unidade:'km/h',band:{min:LIM.vento_kmh.ideal[0],max:LIM.vento_kmh.ideal[1]},dec:0},
  {key:'delta_t',titulo:'Delta-T (índice de pulverização)',unidade:'°C',band:{min:LIM.delta_t.ideal[0],max:LIM.delta_t.ideal[1]},dec:1},
  {key:'precip_mm',titulo:'Previsão de chuva',unidade:'mm',band:{max:LIM.precip_mm_max},dec:1,fill:true},
];}
function renderCharts(){
  const host=document.getElementById('charts');host.innerHTML='';
  const cid=ativasLista();
  metricas().forEach(m=>{const box=document.createElement('div');box.className='chart';
    box.innerHTML='<h3>'+m.titulo+'</h3><p class="u">'+m.unidade+'</p>';
    box.appendChild(chartSVG(m,cid));host.appendChild(box);});
}
function chartSVG(m,cidades){
  const W=500,H=250,pl=40,pr=12,pt=12,pb=26,iw=W-pl-pr,ih=H-pt-pb;
  const sc=cidades.map(c=>c.serie);
  const ref=sc[0]||DADOS.cidades[0].serie,n=ref.length;
  let vals=[];sc.forEach(s=>s.forEach(p=>vals.push(p[m.key])));
  if(m.band.min!=null)vals.push(m.band.min);if(m.band.max!=null)vals.push(m.band.max);
  if(m.key==='precip_mm')vals.push(0);
  let ymin=Math.min(...vals),ymax=Math.max(...vals);const pad=(ymax-ymin)*.08||1;ymin-=pad;ymax+=pad;
  const X=i=>pl+(n<=1?0:i/(n-1)*iw),Y=v=>pt+(1-(v-ymin)/(ymax-ymin))*ih;
  let s='<svg viewBox="0 0 '+W+' '+H+'" role="img">';
  const yTop=Y(m.band.max!=null?m.band.max:ymax),yBot=Y(m.band.min!=null?m.band.min:ymin);
  s+='<rect x="'+pl+'" y="'+yTop+'" width="'+iw+'" height="'+Math.max(0,yBot-yTop)+'" fill="var(--good)" opacity="0.10"/>';
  if(m.band.min!=null)s+=lref(pl,iw,Y(m.band.min));if(m.band.max!=null)s+=lref(pl,iw,Y(m.band.max));
  for(let g=0;g<=4;g++){const v=ymin+(ymax-ymin)*g/4,y=Y(v);
    s+='<line x1="'+pl+'" y1="'+y+'" x2="'+(W-pr)+'" y2="'+y+'" stroke="var(--grid)" stroke-width="1"/>';
    s+='<text x="'+(pl-6)+'" y="'+(y+4)+'" text-anchor="end" fill="var(--muted)" font-size="11">'+v.toFixed(m.dec)+'</text>';}
  let ult='';ref.forEach((p,i)=>{const d=new Date(p.data);if(d.toDateString()!==ult&&d.getHours()<3){
    s+='<text x="'+X(i)+'" y="'+(H-8)+'" fill="var(--muted)" font-size="11">'+d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'})+'</text>';ult=d.toDateString();}});
  cidades.forEach((c,ci)=>{const cor=CORES[idxCor(c)];let d='';
    sc[ci].forEach((p,i)=>{d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(p[m.key]).toFixed(1)+' ';});
    if(m.fill){const area=d+'L'+X(sc[ci].length-1).toFixed(1)+' '+Y(ymin<0?0:ymin).toFixed(1)+' L'+X(0).toFixed(1)+' '+Y(ymin<0?0:ymin).toFixed(1)+' Z';
      s+='<path d="'+area+'" fill="'+cor+'" opacity="0.12"/>';}
    s+='<path d="'+d+'" fill="none" stroke="'+cor+'" stroke-width="2" stroke-linejoin="round"/>';});
  s+='<line id="cx" x1="0" y1="'+pt+'" x2="0" y2="'+(pt+ih)+'" stroke="var(--axis)" stroke-width="1" opacity="0"/>';
  s+='<rect x="'+pl+'" y="'+pt+'" width="'+iw+'" height="'+ih+'" fill="transparent"/></svg>';
  const tpl=document.createElement('template');tpl.innerHTML=s.trim();const svg=tpl.content.firstChild;
  const cx=svg.querySelector('#cx'),ov=svg.querySelector('rect[fill="transparent"]');
  ov.addEventListener('mousemove',e=>{const r=svg.getBoundingClientRect(),ratio=W/r.width;
    let i=Math.round(((e.clientX-r.left)*ratio-pl)/iw*(n-1));i=Math.max(0,Math.min(n-1,i));
    cx.setAttribute('x1',X(i));cx.setAttribute('x2',X(i));cx.setAttribute('opacity','1');
    let html='<b>'+fmtHora(ref[i].data)+'</b>';
    cidades.forEach((c,ci)=>{const p=sc[ci][i];if(!p)return;
      html+='<div class="r"><span class="dot" style="background:'+CORES[idxCor(c)]+'"></span>'+c.nome+': <b style="color:var(--ink)">'+p[m.key].toFixed(m.dec)+' '+m.unidade+'</b></div>';});
    showTip(e,html);});
  ov.addEventListener('mouseleave',()=>{cx.setAttribute('opacity','0');hideTip();});
  return svg;
}
const lref=(x,w,y)=>'<line x1="'+x+'" y1="'+y+'" x2="'+(x+w)+'" y2="'+y+'" stroke="var(--good)" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>';

/* ---------- editor de recomendações ---------- */
const REC=[
  {t:'Vento (km/h)',campos:[['vento_kmh.ideal.0','Ideal mín'],['vento_kmh.ideal.1','Ideal máx'],['vento_kmh.aceitavel.0','Aceit. mín'],['vento_kmh.aceitavel.1','Aceit. máx']]},
  {t:'Temperatura (°C)',campos:[['temp_c.ideal_max','Ideal até'],['temp_c.aceitavel_max','Aceit. até']]},
  {t:'Umidade relativa (%)',campos:[['umidade.ideal_min','Ideal a partir'],['umidade.aceitavel_min','Aceit. a partir']]},
  {t:'Delta-T (°C)',campos:[['delta_t.ideal.0','Ideal mín'],['delta_t.ideal.1','Ideal máx'],['delta_t.aceitavel.0','Aceit. mín'],['delta_t.aceitavel.1','Aceit. máx']]},
  {t:'Chuva (mm)',campos:[['precip_mm_max','Máx. sem chuva']]},
];
function getPath(o,p){return p.split('.').reduce((x,k)=>x[k],o);}
function setPath(o,p,v){const ks=p.split('.');const last=ks.pop();ks.reduce((x,k)=>x[k],o)[last]=v;}
function renderRec(){
  const el=document.getElementById('rec');
  let h='<div class="recgrid">';
  REC.forEach(g=>{h+='<div class="recbox"><h4>'+g.t+'</h4>';
    g.campos.forEach(([path,lab])=>{h+='<div class="recline"><span style="flex:1">'+lab+'</span>'+
      '<input type="number" step="any" data-path="'+path+'" value="'+getPath(LIM,path)+'"></div>';});
    h+='</div>';});
  h+='</div><div class="recact"><button class="btn" id="recSalvar">Aplicar</button>'+
     '<button class="linkbtn" id="recPadrao">Restaurar padrão</button>'+
     '<span class="sub" style="align-self:center">As mudanças recalculam todas as janelas e ficam salvas neste navegador.</span></div>';
  el.innerHTML=h;
  el.querySelector('#recSalvar').onclick=()=>{
    el.querySelectorAll('input[data-path]').forEach(inp=>{const v=parseFloat(inp.value);if(!isNaN(v))setPath(LIM,inp.dataset.path,v);});
    salvarLim();reclassificar();render();
  };
  el.querySelector('#recPadrao').onclick=()=>{LIM=padraoLim();salvarLim();renderRec();reclassificar();render();};
}
document.getElementById('abrirRec').onclick=()=>{const r=document.getElementById('rec');r.hidden=!r.hidden;if(!r.hidden)renderRec();};

/* ---------- tooltip / tema ---------- */
function showTip(e,html){tip.innerHTML=html;tip.style.opacity='1';
  let x=e.clientX+14,y=e.clientY+14;const r=tip.getBoundingClientRect();
  if(x+r.width>innerWidth)x=e.clientX-r.width-14;if(y+r.height>innerHeight)y=e.clientY-r.height-14;
  tip.style.left=x+'px';tip.style.top=y+'px';}
function hideTip(){tip.style.opacity='0';}
document.getElementById('tema').onclick=()=>{const cur=document.documentElement.getAttribute('data-theme');
  document.documentElement.setAttribute('data-theme',cur==='dark'?'light':'dark');render();};

/* ---------- render geral ---------- */
function render(){renderKpis();renderDia();renderTimelines();renderCharts();}
document.getElementById('foot').innerHTML=
  'Delta-T ideal 2–8 °C • vento 3–10 km/h • temperatura ≤ 28 °C • umidade ≥ 60 % (ajustáveis em “Minhas recomendações”). '+
  'Sempre confira a bula do produto. Painel gerado automaticamente a partir da Embrapa ClimAPI (modelo NCEP/GFS).';

reclassificar();montarCidades();initData();renderCabecalho();render();
</script>
</body>
</html>
"""


def gerar(resultado: dict) -> None:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dados_json = json.dumps(resultado, ensure_ascii=False)
    html = _HTML.replace("__DADOS__", dados_json)
    (config.DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
