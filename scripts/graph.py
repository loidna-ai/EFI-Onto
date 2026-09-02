import json
G = json.load(open('build/graph.json', encoding='utf-8'))
DATA = json.dumps(G, ensure_ascii=False, separators=(',', ':'))

HTML = '''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EFI-Onto 그래프</title>
<style>
:root{--ink:#141B21;--panel:#1B242B;--panel2:#222D35;--rule:#31404A;
 --fg:#DEE6EA;--mut:#8FA2AC;--dim:#65787F;
 --patina:#4FA894;--oxide:#C05A44;--amber:#D9963F;--slate:#6E8BA6;--copper:#B07A4A;--violet:#8A7BB5}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--ink);color:var(--fg);overflow:hidden;
 font-family:"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;
 font-size:14px;-webkit-font-smoothing:antialiased}
#app{display:flex;flex-direction:column;height:100%}
header{padding:12px 18px;border-bottom:1px solid var(--rule);display:flex;
 align-items:center;gap:18px;flex-wrap:wrap;background:var(--panel)}
h1{font-size:15px;margin:0;font-weight:700;letter-spacing:-.02em;white-space:nowrap}
h1 span{color:var(--patina);font-weight:500}
.tabs{display:flex;gap:2px}
.tabs button{background:transparent;border:1px solid var(--rule);color:var(--mut);
 padding:6px 13px;font:inherit;font-size:13px;cursor:pointer;border-radius:2px}
.tabs button[aria-selected=true]{background:var(--patina);border-color:var(--patina);color:#0F1519;font-weight:600}
.tabs button:focus-visible{outline:2px solid var(--amber);outline-offset:2px}
#search{background:var(--panel2);border:1px solid var(--rule);color:var(--fg);
 padding:6px 10px;border-radius:2px;font:inherit;font-size:13px;width:170px}
.hint{color:var(--dim);font-size:12px;margin-left:auto}
main{flex:1;position:relative;min-height:0}
svg{width:100%;height:100%;display:block;cursor:grab;touch-action:none}
svg.drag{cursor:grabbing}
.link{stroke:#3A4A55;fill:none}
.link.mech{stroke:var(--patina)} .link.ante{stroke:var(--amber)}
.link.core{stroke:var(--patina)} .link.sup{stroke:#37776B}
.link.shr{stroke:var(--oxide)} .link.exc{stroke:#3E6E63}
.link.enab{stroke:var(--amber)} .link.prod{stroke:var(--patina)}
.link.igni{stroke:var(--violet)} .link.exhi{stroke:var(--copper)} .link.atte{stroke:#7C99AE}
.link.ref{stroke:var(--oxide)} .link.dec{stroke:var(--amber)}
.link.faded{stroke-opacity:.07}
.link.hl{stroke-opacity:1}
.node circle{stroke:var(--ink);stroke-width:1.5px;cursor:pointer}
.node text{font-size:10.5px;fill:var(--mut);pointer-events:none;dominant-baseline:middle}
.node.big text{font-size:13px;fill:var(--fg);font-weight:700}
.node.faded{opacity:.16}
.node.hit circle{stroke:var(--amber);stroke-width:2.5px}
.legend{position:absolute;left:14px;bottom:14px;background:rgba(27,36,43,.94);
 border:1px solid var(--rule);border-radius:2px;padding:12px 14px;max-width:250px}
.legend h4{margin:0 0 8px;font-size:12px;color:var(--mut);font-weight:600}
.legend div{display:flex;align-items:center;gap:8px;font-size:12px;padding:2px 0;cursor:pointer}
.legend div.off{opacity:.35}
.legend i{width:10px;height:10px;border-radius:50%;flex:none}
.legend i.ln{width:16px;height:2px;border-radius:0}
#panel{position:absolute;right:14px;top:14px;width:290px;background:rgba(27,36,43,.96);
 border:1px solid var(--rule);border-radius:2px;padding:16px;display:none}
#panel.on{display:block}
#panel h3{margin:0 0 2px;font-size:16px}
#panel .id{font-family:ui-monospace,monospace;font-size:11px;color:var(--patina);word-break:break-all}
#panel p{margin:10px 0 0;font-size:12.5px;color:var(--mut);line-height:1.6}
#panel ul{margin:10px 0 0;padding:0;list-style:none;font-size:12.5px}
#panel li{padding:3px 0;border-top:1px solid var(--rule);color:var(--mut)}
#panel li b{color:var(--fg);font-weight:600}
#panel .close{position:absolute;right:10px;top:8px;background:none;border:0;
 color:var(--dim);font-size:18px;cursor:pointer;line-height:1}
.axhdr{font-size:12px;fill:var(--dim);font-weight:600;letter-spacing:.04em}
.deltag{font-size:9.5px;fill:var(--dim)}
@media(max-width:760px){#panel{left:14px;right:14px;width:auto;top:auto;bottom:14px}
 .legend{display:none}.hint{display:none}}
</style></head><body>
<div id="app">
<header>
  <h1>EFI-Onto <span>TBox 구조</span></h1>
  <div class="tabs" role="tablist">
    <button role="tab" aria-selected="true" data-v="0">형태학적 중첩</button>
    <button role="tab" aria-selected="false" data-v="1">가설과 증거</button>
    <button role="tab" aria-selected="false" data-v="2">전체 클래스</button>
  </div>
  <input id="search" placeholder="클래스 검색" autocomplete="off">
  <span class="hint">드래그로 이동 · 휠로 확대 · 노드를 누르면 연결만 남습니다</span>
</header>
<main>
  <svg id="svg"><g id="vp"></g></svg>
  <div class="legend" id="legend"></div>
  <div id="panel"><button class="close" aria-label="닫기">&times;</button><div id="pbody"></div></div>
</main>
</div>
<script>
const D=__DATA__;
const SVG=document.getElementById('svg'),VP=document.getElementById('vp');
const NS='http://www.w3.org/2000/svg';
const AXC={mech:'#4FA894',evid:'#B07A4A',ante:'#D9963F',fuel:'#8A7BB5',
 dmg:'#6E8BA6',scene:'#C05A44',scen:'#DEE6EA',meta:'#65787F',enum:'#4A5A64',shared:'#C05A44',excl:'#4FA894',
 agent:'#65787F',evt:'#8A7BB5',obs:'#6E8BA6',other:'#4A5A64'};
const AXN={mech:'발열 메커니즘',evid:'물리 증거물',ante:'선행 조건',fuel:'착화물',
 dmg:'손상 양상',scene:'현장 사실',scen:'가설·판정',evt:'사건',obs:'계측',
 meta:'절차 기록',enum:'열거값',agent:'행위자',other:'기타',
 shared:'여러 가설에 공통',excl:'한 가설에만 나타남'};
const SCK={PoorContactScenario:'접촉불량',CrushDamageScenario:'압착손상',
 PartialDisconnectionScenario:'반단선',InsulationDegradationScenario:'절연열화',
 TrackingScenario:'트래킹',ExternalFlameScenario:'외부화염',OverloadScenario:'과부하',GroundFaultScenario:'누전지락',InterTurnShortScenario:'층간단락',
 ElectricalIgnitionScenario:'전기적 발화 공통'};
const ROLEC={Core:'core',Supporting:'sup',Refuting:'ref',DecisiveRefuting:'dec'};
const ROLEN={Core:'핵심 단서',Supporting:'보강 단서',Refuting:'반증 단서',DecisiveRefuting:'결정적 반증'};
const byId={};D.nodes.forEach(n=>byId[n.id]=n);
const el=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;};

/* ---------- view 0 : 가설 ↔ 증거 ---------- */
function buildEvidence(){
  const order=['PoorContactScenario','CrushDamageScenario','PartialDisconnectionScenario',
   'InsulationDegradationScenario','TrackingScenario','OverloadScenario','GroundFaultScenario','InterTurnShortScenario','ExternalFlameScenario','ElectricalIgnitionScenario'];
  const rules=D.rules.filter(r=>order.includes(r.s));
  const N=[],L=[];
  const SX=0, GAP=132, TOP=70;
  order.forEach((s,i)=>N.push({id:s,ko:SCK[s]||s,x:SX,y:TOP+i*GAP,r:15,big:1,ax:'scen'}));
  const pos={};N.forEach(n=>pos[n.id]=n);
  // 증거는 좌(지지) / 우(반증)
  const side={left:[],right:[]};
  rules.forEach(r=>{ (r.d>=0?side.left:side.right).push(r); });
  [['left',-1],['right',1]].forEach(([k,sg])=>{
    const seen={};
    side[k].forEach(r=>{ if(!seen[r.t]) seen[r.t]=[]; seen[r.t].push(r); });
    const keys=Object.keys(seen).sort((a,b)=>{
      const ay=pos[seen[a][0].s].y, by=pos[seen[b][0].s].y; return ay-by;});
    keys.forEach((t,i)=>{
      const n=byId[t]||{id:t,ko:t,ax:'other',cm:''};
      N.push({id:t,ko:n.ko,x:sg*400,y:40+i*(760/Math.max(1,keys.length-1||1)),
              r:6,ax:n.ax,cm:n.cm});
    });
  });
  const P={};N.forEach(n=>{if(!P[n.id])P[n.id]=n;});
  rules.forEach(r=>{ if(P[r.s]&&P[r.t]) L.push({s:r.s,t:r.t,c:ROLEC[r.role]||'sup',d:r.d,role:r.role,st:r.st}); });
  return {N:Object.values(P),L,mode:'ev'};
}

/* ---------- view 0b : 형태학적 중첩 ---------- */
function buildMorph(){
  const SC=['PoorContactScenario','CrushDamageScenario','PartialDisconnectionScenario',
   'InsulationDegradationScenario','TrackingScenario','OverloadScenario','GroundFaultScenario','InterTurnShortScenario','ExternalFlameScenario'];
  const man={};D.manifest.forEach(m=>{(man[m.s]=man[m.s]||new Set()).add(m.t);});
  const N=[],L=[],P={};
  const R=300;
  SC.forEach((s,i)=>{
    const a=i*2*Math.PI/SC.length-Math.PI/2;
    const n={id:s,ko:SCK[s]||s,x:Math.cos(a)*R,y:Math.sin(a)*R,r:16,big:1,ax:'scen'};
    N.push(n);P[s]=n;
  });
  // 손상 양상: 공유 수가 클수록 중앙
  const dmg={};D.manifest.forEach(m=>{(dmg[m.t]=dmg[m.t]||[]).push(m.s);});
  const keys=Object.keys(dmg);
  keys.sort((a,b)=>dmg[b].length-dmg[a].length);
  keys.forEach(t=>{
    const owners=dmg[t],k=owners.length;
    let x=0,y=0;
    owners.forEach(o=>{x+=P[o].x;y+=P[o].y;});
    x/=k;y/=k;
    if(k===1){ x*=1.62; y*=1.62; }               // 전용 양상은 바깥으로
    else { const j=(keys.indexOf(t)%5-2)*17; x+=j; y+=(keys.indexOf(t)%3-1)*17; }
    const nd=byId[t]||{ko:t,cm:''};
    const n={id:t,ko:nd.ko,cm:nd.cm,ax:k>1?'shared':'excl',x,y,
             r:k>1?5+k*1.8:5,sh:k};
    N.push(n);P[t]=n;
  });
  D.manifest.forEach(m=>{
    const k=dmg[m.t].length;
    L.push({s:m.s,t:m.t,c:k>1?'shr':'exc',d:k>1?9:3,shared:k});
  });
  return {N,L,mode:'mo'};
}

/* ---------- view 1 : 전체 클래스 (축별 방사) ---------- */
function buildAll(){
  const axes=['mech','ante','dmg','scene','evid','fuel','scen','evt','obs','meta','agent','enum','other'];
  const groups={};D.nodes.forEach(n=>{(groups[n.ax]=groups[n.ax]||[]).push(n);});
  const use=axes.filter(a=>groups[a]&&groups[a].length);
  const N=[],P={};
  const R0=250, step=2*Math.PI/use.length;
  use.forEach((a,i)=>{
    const g=groups[a],ang=i*step-Math.PI/2;
    const cx=Math.cos(ang)*(R0+g.length*7), cy=Math.sin(ang)*(R0+g.length*7);
    // 축 내부는 부모-자식 깊이에 따른 동심 배치
    const depth={};
    const dep=n=>{let d=0,cur=n,guard=0;
      while(guard++<12){const p=D.edges.find(e=>e.k==='sub'&&e.s===cur);if(!p)break;cur=p.t;d++;}
      return d;};
    g.forEach(n=>{const d=dep(n.id);(depth[d]=depth[d]||[]).push(n);});
    Object.keys(depth).sort().forEach(d=>{
      const arr=depth[d],rr=28+(+d)*34;
      arr.forEach((n,j)=>{
        const a2=ang+(j-(arr.length-1)/2)*(Math.min(.42,2.0/Math.max(arr.length,4)));
        const nn={id:n.id,ko:n.ko,cm:n.cm,ax:n.ax,
          x:cx+Math.cos(a2)*rr*1.5,y:cy+Math.sin(a2)*rr*1.5,
          r:n.root?11:5.5,big:n.root?1:0,head:n.root?AXN[n.ax]:''};
        N.push(nn);P[n.id]=nn;
      });
    });
  });
  const L=[];
  const EC={sub:'sub',hasMechanism:'mech',hasAntecedent:'ante',enables:'enab',
            producesDamage:'prod',ignites:'igni',exhibits:'exhi',attests:'atte'};
  D.edges.forEach(e=>{ if(P[e.s]&&P[e.t])
    L.push({s:e.s,t:e.t,c:EC[e.k]||'sub',k:e.k}); });
  const cnt={};D.manifest.forEach(m=>cnt[m.t]=(cnt[m.t]||0)+1);
  D.manifest.forEach(m=>{ if(P[m.s]&&P[m.t])
    L.push({s:m.s,t:m.t,c:cnt[m.t]>1?'shr':'exc',k:'canManifest',shared:cnt[m.t]}); });
  // 손상 양상 노드: 공유하는 가설 수만큼 크게, 공유되면 테두리를 적갈로
  N.forEach(n=>{ const c=cnt[n.id]; if(c){ n.r=Math.max(n.r,4+c*1.6); n.sh=c;
    n.ring=c>1?'#C05A44':'#4FA894'; } });
  return {N,L,mode:'all'};
}

/* ---------- render ---------- */
let cur=null, sel=null;
function render(v){
  cur=v; VP.innerHTML='';
  const gl=el('g'),gn=el('g');VP.appendChild(gl);VP.appendChild(gn);
  const P={};v.N.forEach(n=>P[n.id]=n);
  v.L.forEach(l=>{
    const a=P[l.s],b=P[l.t];
    const mx=(a.x+b.x)/2, my=(a.y+b.y)/2, dx=b.x-a.x, dy=b.y-a.y;
    const cx=mx-dy*0.12, cy=my+dx*0.12;
    const p=el('path',{class:'link '+l.c,d:`M${a.x} ${a.y}Q${cx} ${cy} ${b.x} ${b.y}`,
      'stroke-width': v.mode==='ev'?Math.max(1,Math.min(4,Math.abs(l.d)/7)):(v.mode==='mo'?(l.shared>1?1.8:1):1),
      'stroke-opacity': v.mode==='ev'?.55:(v.mode==='mo'?(l.shared>1?.5:.28):(l.k==='sub'?.35:.3))});
    p.__l=l;gl.appendChild(p);
  });
  v.N.forEach(n=>{
    const g=el('g',{class:'node'+(n.big?' big':''),transform:`translate(${n.x},${n.y})`});
    const c=el('circle',{r:n.r,fill:AXC[n.ax]||'#4A5A64'});
    if(n.ring){c.setAttribute('stroke',n.ring);c.setAttribute('stroke-width','2');}
    g.appendChild(c);
    if(n.head){const h=el('text',{class:'axhdr',x:0,y:-n.r-13,'text-anchor':'middle'});
      h.textContent=n.head;g.appendChild(h);}
    const mid = (v.mode==='ev'||v.mode==='mo') && n.big;
    const anchor = mid ? 'middle' : (n.x<0?'end':'start');
    const off = mid ? 0 : (n.x<0?-10:10);
    const t=el('text',{x:off,y:mid?-n.r-11:0,'text-anchor':anchor});
    t.textContent=n.ko;g.appendChild(t);
    g.__n=n;g.addEventListener('click',ev=>{ev.stopPropagation();focus(n.id);});
    gn.appendChild(g);
  });
  fit();
}
function fit(){
  const b=VP.getBBox(),r=SVG.getBoundingClientRect();
  const k=Math.min(r.width/(b.width+150),r.height/(b.height+120));
  T.k=k;T.x=r.width/2-(b.x+b.width/2)*k;T.y=r.height/2-(b.y+b.height/2)*k;apply();
}
/* focus */
function focus(id){
  sel=(sel===id)?null:id;
  const nbr=new Set([id]);
  if(sel) cur.L.forEach(l=>{if(l.s===id)nbr.add(l.t);if(l.t===id)nbr.add(l.s);});
  VP.querySelectorAll('.node').forEach(g=>{
    const on=!sel||nbr.has(g.__n.id);
    g.classList.toggle('faded',!on);g.classList.toggle('hit',sel===g.__n.id);});
  VP.querySelectorAll('.link').forEach(p=>{
    const l=p.__l,on=!sel||l.s===id||l.t===id;
    p.classList.toggle('faded',!on);p.classList.toggle('hl',!!sel&&on);});
  sel?showPanel(id):hidePanel();
}
function showPanel(id){
  const n=byId[id]||cur.N.find(x=>x.id===id);
  const rs=D.rules.filter(r=>r.s===id||r.t===id);
  const par=D.edges.filter(e=>e.s===id);
  let h=`<h3>${n.ko||id}</h3><div class="id">${id}</div>`;
  if(n.cm)h+=`<p>${n.cm}</p>`;
  const owners=D.manifest.filter(m=>m.t===id).map(m=>SCK[m.s]||m.s);
  if(owners.length)h+=`<p style="color:${owners.length>1?'var(--oxide)':'var(--patina)'}">`+
    (owners.length>1?`${owners.length}개 가설에서 공통으로 나타납니다 — 이 양상만으로는 확정할 수 없습니다.<br>`
                    :`이 가설에서만 나타납니다 — 사진만으로 좁힐 수 있습니다.<br>`)+
    owners.join(' · ')+'</p>';
  const mine=D.manifest.filter(m=>m.s===id).map(m=>m.t);
  if(mine.length){const shc=mine.filter(t=>D.manifest.filter(m=>m.t===t).length>1);
    h+=`<p>남길 수 있는 손상 양상 ${mine.length}가지 중 <b style="color:var(--oxide)">${shc.length}가지</b>가 다른 가설과 겹칩니다.</p>`;}
  const KN={sub:'상위',hasMechanism:'정의 메커니즘',hasAntecedent:'필요 선행조건',
    enables:'성립시키는 메커니즘',producesDamage:'남기는 손상 양상',ignites:'착화시킬 수 있는 물질',
    exhibits:'지닐 수 있는 손상 양상',attests:'증언하는 선행조건'};
  const inc=D.edges.filter(e=>e.t===id&&e.k!=='sub');
  if(par.length)h+='<ul>'+par.map(e=>`<li>${KN[e.k]||e.k} <b>${(byId[e.t]||{}).ko||e.t}</b></li>`).join('')+'</ul>';
  if(inc.length)h+='<ul>'+inc.slice(0,10).map(e=>`<li style="color:var(--dim)">← <b>${(byId[e.s]||{}).ko||e.s}</b> 로부터</li>`).join('')+'</ul>';
  if(rs.length)h+='<ul>'+rs.map(r=>{
    const other=r.s===id?((byId[r.t]||{}).ko||r.t):(SCK[r.s]||r.s);
    return `<li>${ROLEN[r.role]||r.role} · <b>${other}</b> <span style="float:right;font-family:monospace">${r.d>0?'+':''}${r.d}</span></li>`;}).join('')+'</ul>';
  document.getElementById('pbody').innerHTML=h;
  document.getElementById('panel').classList.add('on');
}
function hidePanel(){document.getElementById('panel').classList.remove('on');}
document.querySelector('#panel .close').onclick=()=>{sel=null;focus('');hidePanel();};

/* pan / zoom */
const T={x:0,y:0,k:1};
const apply=()=>VP.setAttribute('transform',`translate(${T.x},${T.y}) scale(${T.k})`);
let dr=null;
SVG.addEventListener('pointerdown',e=>{dr={x:e.clientX,y:e.clientY,ox:T.x,oy:T.y};
  SVG.classList.add('drag');SVG.setPointerCapture(e.pointerId);});
SVG.addEventListener('pointermove',e=>{if(!dr)return;
  T.x=dr.ox+(e.clientX-dr.x);T.y=dr.oy+(e.clientY-dr.y);apply();});
SVG.addEventListener('pointerup',()=>{dr=null;SVG.classList.remove('drag');});
SVG.addEventListener('wheel',e=>{e.preventDefault();
  const r=SVG.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
  const f=Math.exp(-e.deltaY*0.0016),nk=Math.max(.15,Math.min(4,T.k*f));
  T.x=mx-(mx-T.x)*(nk/T.k);T.y=my-(my-T.y)*(nk/T.k);T.k=nk;apply();},{passive:false});
SVG.addEventListener('click',()=>{if(sel){sel=null;focus('');hidePanel();}});

/* legend */
function legend(mode){
  const L=document.getElementById('legend');
  if(mode==='mo'){
    L.innerHTML='<h4>손상 양상의 변별력</h4>'+
     '<div style="cursor:default"><i style="background:var(--oxide)"></i>여러 가설에 공통 — 사진만으로 못 가름</div>'+
     '<div style="cursor:default"><i style="background:var(--patina)"></i>한 가설에만 나타남 — 사진으로 좁혀짐</div>'+
     '<h4 style="margin-top:10px">배치</h4><div style="cursor:default">가운데로 갈수록 여러 가설이 공유합니다. 점 크기는 공유하는 가설 수입니다.</div>';
  }else if(mode==='ev'){
    L.innerHTML='<h4>단서의 역할</h4>'+
     [['core','핵심 단서'],['sup','보강 단서'],['ref','반증 단서'],['dec','결정적 반증 — 즉시 기각']]
     .map(([c,t])=>`<div><i class="ln" style="background:var(--${c==='core'?'patina':c==='sup'?'patina':c==='ref'?'oxide':'amber'});opacity:${c==='sup'?.6:1}"></i>${t}</div>`).join('')+
     '<h4 style="margin-top:10px">선의 굵기</h4><div style="cursor:default">가감점의 크기</div>';
  }else{
    L.innerHTML='<h4>축</h4>'+['mech','ante','dmg','scene','evid','fuel','scen']
     .map(a=>`<div style="cursor:default"><i style="background:${AXC[a]}"></i>${AXN[a]}</div>`).join('')+
     '<h4 style="margin-top:12px">연결 — 눌러서 켜고 끄기</h4>'+
     [['sub','상위 클래스 (계층)','#3A4A55'],
      ['enab','선행조건 → 메커니즘','#D9963F'],
      ['prod','메커니즘 → 손상 양상','#4FA894'],
      ['igni','메커니즘 → 착화물','#8A7BB5'],
      ['exhi','증거물 → 손상 양상','#B07A4A'],
      ['atte','현장사실 → 선행조건','#7C99AE'],
      ['mech','가설 정의: 메커니즘','#4FA894'],
      ['ante','가설 필요조건','#D9963F'],
      ['man','가설 → 형태 발현','#C05A44']]
     .map(([k,t,c])=>`<div data-f="${k}"><i class="ln" style="background:${c}"></i>${t}</div>`).join('')+
     '<h4 style="margin-top:12px">손상 양상 테두리</h4>'+
     '<div style="cursor:default"><i style="background:transparent;border:2px solid #C05A44"></i>여러 가설이 공유</div>'+
     '<div style="cursor:default"><i style="background:transparent;border:2px solid #4FA894"></i>한 가설 전용</div>';
    L.querySelectorAll('[data-f]').forEach(d=>d.onclick=()=>{
      d.classList.toggle('off');
      const k=d.dataset.f,off=d.classList.contains('off');
      VP.querySelectorAll('.link').forEach(p=>{
        const M={sub:'sub',man:'canManifest',mech:'hasMechanism',ante:'hasAntecedent',
                 enab:'enables',prod:'producesDamage',igni:'ignites',exhi:'exhibits',atte:'attests'};
        const l=p.__l,hit=(l.k===M[k]);
        if(hit)p.style.display=off?'none':'';});
    });
  }
}
/* tabs */
const views=[buildMorph(),buildEvidence(),buildAll()];
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));
  sel=null;hidePanel();const v=views[+b.dataset.v];render(v);legend(v.mode);});
/* search */
document.getElementById('search').addEventListener('input',e=>{
  const q=e.target.value.trim().toLowerCase();
  VP.querySelectorAll('.node').forEach(g=>{
    const n=g.__n,hit=q&&((n.ko||'').toLowerCase().includes(q)||n.id.toLowerCase().includes(q));
    g.classList.toggle('faded',!!q&&!hit);g.classList.toggle('hit',!!hit);});
  if(!q)VP.querySelectorAll('.node').forEach(g=>g.classList.remove('faded','hit'));
});
render(views[0]);legend('mo');
window.addEventListener('resize',()=>fit());
</script></body></html>'''

open('build/EFI-Onto_그래프.html', 'w', encoding='utf-8').write(HTML.replace('__DATA__', DATA))
print('ok')
