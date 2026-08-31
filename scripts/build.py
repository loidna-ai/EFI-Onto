import json
D = json.load(open('build/onto.json', encoding='utf-8'))

AXES = [
    ("발열 메커니즘", "HeatingMechanism", "BFO 과정 (process)", "열이 발생하는 물리 현상 그 자체. 증거물도 조건도 아니다."),
    ("물리 증거물", "PhysicalEvidence", "BFO 물질 실체 (material entity)", "현장에서 수거되는 물건. 전선, 단자대, 절연물."),
    ("선행 조건", "AntecedentCondition", "BFO 성향 (disposition)", "발화 이전부터 존재하던 상태. 헐거운 접속, 오염 환경, 노후화."),
    ("착화물", "FirstFuelIgnited", "BFO 물질 실체 (material entity)", "최초로 불이 붙은 대상. 피복 자체인가, 주변 가연물인가."),
]
AUX = [
    ("손상 양상", "DamagePattern", "BFO 성질 (quality)", "증거물 표면에 남은 형태학적 특징. 사진으로 보이는 것."),
    ("현장 사실", "SceneEvidence", "정보 실체 (IAO ICE)", "조사관이 확인해 보고하는 사실. 사진 밖에 있는 것."),
    ("가설과 판정", "IgnitionScenario", "정보 실체 (IAO ICE)", "판독 결과는 결론이 아니라 가설이다."),
]
SCEN = {
    "PoorContactScenario": "접촉불량", "CrushDamageScenario": "압착손상",
    "PartialDisconnectionScenario": "반단선", "InsulationDegradationScenario": "절연열화",
    "TrackingScenario": "트래킹", "ExternalFlameScenario": "외부화염",
    "ElectricalIgnitionScenario": "전기적 발화(상위)",
}
ROLE = {"CoreIndicator": ("핵심", "core"), "SupportingIndicator": ("보강", "sup"),
        "RefutingIndicator": ("반증", "ref"), "DecisiveRefutingIndicator": ("결정적 반증", "dec")}

PIPE = [
    ("M-1", "손상 양상별 변별력 산출", "MorphologyDiscriminationRuleShape",
     "각 손상 양상을 몇 개의 가설이 남길 수 있는지 센다. 한 가설에서만 나오면 사진으로 좁힐 수 있는 양상이고, 여럿에 걸치면 변별력이 없다."),
    ("M-2", "형태학적 혼동 쌍 도출", "MorphologicalAmbiguityRuleShape",
     "손상 양상을 두 가지 이상 공유하는 가설 쌍을 자동으로 묶는다. 이 쌍은 사진만으로 갈리지 않으므로 현장 사실을 물어야 한다."),
    ("M-3", "형태 발현을 메커니즘에서 유도해 대조", "DerivedManifestationRuleShape",
     "가설이 남길 수 있다고 선언한 손상 양상과, 그 가설의 발열 메커니즘이 실제로 남기는 양상을 대조한다. 어긋나면 근거 없는 선언이므로 잡아낸다."),
    ("F-1", "반증 우선", "FalsificationRuleShape",
     "확인된 반증 사실이 있으면 해당 가설을 먼저 기각한다. 비통전 확인처럼 물리적으로 결정적인 사실은 즉시 기각 수준으로 내린다."),
    ("F-2", "1차·2차 단락흔 판정", "ArcMarkSequenceRuleShape",
     "아크 사건이 화염 노출보다 앞서면 1차 아크흔, 뒤면 2차 수열흔. 공극률이나 결정립 같은 형태학은 보강 근거로만 쓴다."),
    ("F-3", "착화 역량 검토", "IgnitionCompetenceRuleShape",
     "메커니즘의 최고 도달 온도가 착화물의 발화 온도에 못 미치면 가설을 약화시킨다."),
    ("F-4", "지지점수 산출", "SupportScoreRuleShape",
     "50점에서 출발해 확인된 단서의 가감점을 누적한다. 0~100으로 자르고, 확률이 아니므로 퍼센트 기호를 쓰지 않는다."),
]
CONS = [
    ("C-1", "'확인 불가'는 반증이 아니다", "RefutationEvidenceShape",
     "반증 근거로 인정되는 상태는 '확인됨'과 '없음이 확인됨' 둘뿐이다. 확인하지 못한 것을 없는 것으로 취급하지 않는다."),
    ("C-2", "소거만으로 확정할 수 없다", "ConclusionShape",
     "확정하려면 긍정 지지 사실 2건 이상, 그중 조사관이 확인한 것 1건 이상, 지지점수 70 이상, 질의 2회 이상을 모두 만족해야 한다. NFPA 921의 negative corpus 배제를 그대로 옮긴 것."),
    ("C-3", "가설은 하나의 메커니즘에 대응", "ScenarioShape",
     "한 시나리오가 둘 이상의 발열 메커니즘을 동시에 주장할 수 없다."),
    ("C-5", "공유 형태만으로는 확정할 수 없다", "MorphologyOnlyConclusionShape",
     "여러 가설에 공통으로 나타나는 손상 양상만 모아서는 결론이 서지 않는다. 그 가설에서만 나타나는 양상이거나, 손상 양상이 아닌 현장 사실이 최소 한 건 필요하다. 논문 4.2절의 구조적 혼동을 제약으로 고정한 것."),
    ("C-4", "모든 사실에 출처와 상태", "FactShape",
     "사실 하나마다 확인 상태와 누가 확인했는지(조사관인지 AI인지)를 반드시 남긴다."),
]


def tree(root, depth=0, seen=None):
    seen = seen or set()
    if root in seen:
        return []
    seen.add(root)
    kids = sorted([k for k, v in D['c'].items() if root in v['sup']])
    out = []
    for k in kids:
        out.append((k, depth))
        out += tree(k, depth + 1, seen)
    return out


def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def li(n, d):
    c = D['c'][n]
    ko = c['ko'] or n
    eq = '<i class="eq" title="필요충분조건으로 정의된 클래스">\u2261</i>' if c['eq'] else ''
    dj = f'<i class="dj" title="상호배타: {esc(", ".join(c["dj"]))}">\u22a5</i>' if c['dj'] else ''
    return (f'<li style="--d:{d}"><span class="ko">{esc(ko)}</span>'
            f'<span class="id">{esc(n)}</span>{eq}{dj}'
            + (f'<span class="cm">{esc(c["cm"])}</span>' if c['cm'] else '') + '</li>')


def axis_block(title, root, bfo, note):
    rows = ''.join(li(n, d) for n, d in tree(root))
    rc = D['c'][root]
    return f'''<section class="axis">
<header><h3>{esc(title)}</h3><p class="bfo">{esc(bfo)}</p><p class="note">{esc(note)}</p></header>
<ul class="tree"><li style="--d:0" class="root"><span class="ko">{esc(rc["ko"] or root)}</span><span class="id">{esc(root)}</span></li>{rows}</ul>
</section>'''


# 단서 규칙 매트릭스
by_sc = {}
for r in D['rules']:
    for s in r['sc']:
        by_sc.setdefault(s, []).append(r)
order = ["PoorContactScenario", "CrushDamageScenario", "PartialDisconnectionScenario",
         "InsulationDegradationScenario", "TrackingScenario", "ExternalFlameScenario",
         "ElectricalIgnitionScenario"]
rule_html = ''
for s in order:
    rs = by_sc.get(s, [])
    if not rs:
        continue
    cells = ''
    for r in sorted(rs, key=lambda x: -abs(x['d'][0] if x['d'] else 0)):
        rl, cl = ROLE.get(r['role'][0] if r['role'] else '', ('', 'sup'))
        ind = r['ind'][0] if r['ind'] else ''
        ko = D['c'].get(ind, {}).get('ko') or ind
        dv = r['d'][0] if r['d'] else 0
        st = r['st'][0] if r['st'] else ''
        stk = '없음 확인' if st == 'ConfirmedAbsent' else '확인됨'
        cells += (f'<div class="rule r-{cl}"><b>{esc(ko)}</b>'
                  f'<span class="delta">{dv:+d}</span>'
                  f'<span class="meta">{rl} · {stk}</span></div>')
    rule_html += f'<div class="scen"><h4>{esc(SCEN.get(s, s))}</h4><div class="rules">{cells}</div></div>'

# ── 형태학적 중첩 절
MAN = D['man']; SHARED = D['shared']
def kko(n): return D['c'].get(n, {}).get('ko') or n
pairs = []
ks = sorted(MAN)
for i, a in enumerate(ks):
    for b in ks[i+1:]:
        sh = sorted(set(MAN[a]) & set(MAN[b]))
        if len(sh) >= 2:
            pairs.append((a, b, sh))
pairs.sort(key=lambda x: -len(x[2]))
pair_rows = ''.join(
    f'<tr><td><b>{esc(SCEN.get(a,a))}</b> &harr; <b>{esc(SCEN.get(b,b))}</b></td>'
    f'<td style="text-align:center;color:var(--oxide);font-weight:700">{len(sh)}</td>'
    f'<td>{esc(" · ".join(kko(x) for x in sh))}</td></tr>' for a, b, sh in pairs)

sh_sorted = sorted(SHARED.items(), key=lambda x: (-x[1], x[0]))
morph_cells = ''.join(
    f'<div class="mcell {"m-shared" if n>1 else "m-excl"}">'
    f'<b>{esc(kko(k))}</b><span class="mn">{n}</span>'
    f'<span class="meta">{"가설 " + str(n) + "개 공통" if n>1 else "전용 · 사진으로 좁혀짐"}</span></div>'
    for k, n in sh_sorted)

prof_rows = ''
for scn in ["PoorContactScenario","CrushDamageScenario","PartialDisconnectionScenario",
            "InsulationDegradationScenario","TrackingScenario","ExternalFlameScenario"]:
    ds = MAN.get(scn, [])
    cells = ''.join(
        f'<span class="chip {"c-shared" if SHARED.get(d,1)>1 else "c-excl"}">{esc(kko(d))}</span>'
        for d in sorted(ds, key=lambda x: -SHARED.get(x, 1)))
    nsh = sum(1 for d in ds if SHARED.get(d, 1) > 1)
    prof_rows += (f'<div class="prof"><h4>{esc(SCEN.get(scn,scn))}'
                  f'<small>{len(ds)}가지 중 {nsh}가지가 다른 가설과 겹침</small></h4>'
                  f'<div class="chips">{cells}</div></div>')

# ── 축 간 인과 사슬
CH = D['chain']
def kko2(n): return D['c'].get(n, {}).get('ko') or n
def chain_table(key, lhs, rhs):
    m = {}
    for a, b in CH[key]:
        m.setdefault(a, []).append(b)
    return ''.join(
        f'<tr><td><b>{esc(kko2(a))}</b></td><td>{esc(" · ".join(kko2(x) for x in sorted(bs)))}</td></tr>'
        for a, bs in sorted(m.items(), key=lambda x: kko2(x[0])))

chain_enables = chain_table('enables', '선행 조건', '메커니즘')
chain_prod = chain_table('producesDamage', '메커니즘', '손상 양상')
chain_ign = chain_table('ignites', '메커니즘', '착화물')
chain_exh = chain_table('exhibits', '증거물', '손상 양상')
chain_att = chain_table('attests', '현장 사실', '선행 조건')
n_chain = sum(len(v) for v in CH.values())

op_rows = ''.join(
    f'<tr><td class="id">{esc(p["n"])}</td><td>{esc(p["ko"])}</td>'
    f'<td class="dm">{esc(" ∪ ".join(p["d"]) or "—")}</td>'
    f'<td class="dm">{esc(" ∪ ".join(p["r"]) or "—")}</td></tr>' for p in D['op'])
dp_rows = ''.join(
    f'<tr><td class="id">{esc(p["n"])}</td><td>{esc(p["ko"])}</td>'
    f'<td class="dm">{esc(" ∪ ".join(p["d"]) or "—")}</td>'
    f'<td class="dm">{esc(" ".join(p["r"]) or "—")}</td></tr>' for p in D['dp'])

pipe_html = ''.join(
    f'<li><div class="tag">{k}</div><div><h4>{esc(t)}</h4>'
    f'<p>{esc(desc)}</p><code>{esc(shape)}</code></div></li>' for k, t, shape, desc in PIPE)
cons_html = ''.join(
    f'<li><div class="tag c">{k}</div><div><h4>{esc(t)}</h4>'
    f'<p>{esc(desc)}</p><code>{esc(shape)}</code></div></li>' for k, t, shape, desc in CONS)

axes_html = ''.join(axis_block(*a) for a in AXES)
aux_html = ''.join(axis_block(*a) for a in AUX)

N = dict(c=len(D['c']), op=len(D['op']), dp=len(D['dp']),
         r=len(D['rules']), s=11)

HTML = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EFI-Onto TBox</title>
<style>
:root{{
  --ink:#151C22; --panel:#1C252C; --panel2:#222C34; --rule:#31404A;
  --fg:#DDE5E8; --mut:#8FA2AC; --dim:#6C808B;
  --patina:#4FA894; --patina-d:#2E6C60;
  --oxide:#C05A44; --oxide-d:#7E3628;
  --amber:#D9963F; --copper:#A9713F;
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--ink);color:var(--fg);
 font-family:"Pretendard Variable",Pretendard,-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;
 font-size:15px;line-height:1.65;letter-spacing:-.01em}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 24px}}
code,.id,.dm,.delta{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace}}

/* hero */
.hero{{padding:88px 0 56px;border-bottom:1px solid var(--rule)}}
.hero h1{{font-size:clamp(30px,5.2vw,52px);line-height:1.15;margin:0 0 18px;font-weight:800;letter-spacing:-.035em}}
.hero h1 small{{display:block;font-size:.38em;font-weight:500;color:var(--patina);letter-spacing:.02em;margin-bottom:14px}}
.hero p{{max-width:62ch;color:var(--mut);margin:0 0 8px}}
.counts{{display:flex;flex-wrap:wrap;gap:0;margin-top:36px;border:1px solid var(--rule);border-radius:2px;overflow:hidden}}
.counts div{{flex:1 1 120px;padding:16px 18px;border-right:1px solid var(--rule);background:var(--panel)}}
.counts div:last-child{{border-right:0}}
.counts b{{display:block;font-size:26px;font-weight:700;color:var(--fg)}}
.counts span{{font-size:12.5px;color:var(--dim)}}

/* section */
section.blk{{padding:60px 0;border-bottom:1px solid var(--rule)}}
h2{{font-size:24px;font-weight:700;margin:0 0 6px;letter-spacing:-.02em}}
.lead{{color:var(--mut);max-width:66ch;margin:0 0 32px}}

/* axes */
.axis{{border:1px solid var(--rule);border-radius:2px;background:var(--panel);margin-bottom:14px;overflow:hidden}}
.axis header{{padding:16px 20px;background:var(--panel2);border-bottom:1px solid var(--rule)}}
.axis h3{{margin:0;font-size:17px;font-weight:700}}
.axis .bfo{{margin:2px 0 0;font-size:12px;color:var(--patina);font-family:ui-monospace,monospace}}
.axis .note{{margin:6px 0 0;font-size:13.5px;color:var(--mut)}}
ul.tree{{list-style:none;margin:0;padding:10px 0}}
ul.tree li{{padding:3px 20px 3px calc(20px + var(--d)*20px);position:relative;font-size:14px}}
ul.tree li:not(.root)::before{{content:"";position:absolute;left:calc(11px + var(--d)*20px);top:0;bottom:0;border-left:1px solid var(--rule)}}
ul.tree li.root{{font-weight:700}}
.ko{{margin-right:8px}}
.id{{font-size:11.5px;color:var(--dim)}}
.cm{{display:block;font-size:12.5px;color:var(--dim);max-width:70ch}}
.eq,.dj{{font-style:normal;margin-left:7px;font-size:12px;padding:1px 5px;border-radius:2px}}
.eq{{color:var(--patina);border:1px solid var(--patina-d)}}
.dj{{color:var(--oxide);border:1px solid var(--oxide-d)}}

/* scenario definition */
.def{{border:1px solid var(--rule);background:var(--panel);padding:22px;border-radius:2px}}
.def p{{margin:0 0 14px;color:var(--mut)}}
.formula{{font-family:ui-monospace,monospace;font-size:13.5px;line-height:2.1;color:var(--fg);overflow-x:auto}}
.formula .k{{color:var(--patina)}}
.formula .n{{color:var(--amber)}}

/* rules */
.scen{{margin-bottom:22px}}
.scen h4{{margin:0 0 10px;font-size:15px;font-weight:700;padding-bottom:6px;border-bottom:1px solid var(--rule)}}
.rules{{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:8px}}
.rule{{padding:10px 12px;border-radius:2px;background:var(--panel);border-left:3px solid var(--dim);position:relative}}
.rule b{{display:block;font-size:13.5px;font-weight:600;padding-right:44px}}
.rule .meta{{font-size:11.5px;color:var(--dim)}}
.rule .delta{{position:absolute;right:12px;top:10px;font-size:13px;font-weight:700}}
.r-core{{border-left-color:var(--patina)}} .r-core .delta{{color:var(--patina)}}
.r-sup{{border-left-color:var(--patina-d)}} .r-sup .delta{{color:var(--patina-d)}}
.r-ref{{border-left-color:var(--oxide)}} .r-ref .delta{{color:var(--oxide)}}
.r-dec{{border-left-color:var(--amber);background:linear-gradient(90deg,rgba(217,150,63,.10),var(--panel) 60%)}}
.r-dec .delta{{color:var(--amber)}}
.legend{{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:22px;font-size:12.5px;color:var(--mut)}}
.legend i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:6px}}

/* morphology */
.mgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px}}
.mcell{{padding:10px 12px;border-radius:2px;background:var(--panel);border-left:3px solid var(--patina);position:relative}}
.mcell b{{display:block;font-size:13.5px;font-weight:600;padding-right:30px}}
.mcell .mn{{position:absolute;right:12px;top:9px;font-family:ui-monospace,monospace;font-size:14px;font-weight:700;color:var(--patina)}}
.mcell .meta{{font-size:11.5px;color:var(--dim)}}
.m-shared{{border-left-color:var(--oxide);background:linear-gradient(90deg,rgba(192,90,68,.10),var(--panel) 55%)}}
.m-shared .mn{{color:var(--oxide)}}
.prof{{margin-bottom:16px}}
.prof h4{{margin:0 0 8px;font-size:14.5px;font-weight:700;display:flex;justify-content:space-between;
 align-items:baseline;border-bottom:1px solid var(--rule);padding-bottom:6px;gap:12px}}
.prof h4 small{{font-size:12px;font-weight:400;color:var(--dim)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{font-size:12.5px;padding:4px 9px;border-radius:2px;border:1px solid var(--rule);color:var(--mut)}}
.c-shared{{border-color:var(--oxide-d);color:var(--oxide);background:rgba(192,90,68,.07)}}
.c-excl{{border-color:var(--patina-d);color:var(--patina)}}

/* pipeline */
ol.pipe{{list-style:none;margin:0;padding:0}}
ol.pipe li{{display:flex;gap:18px;padding:18px 0;border-bottom:1px solid var(--rule)}}
ol.pipe li:last-child{{border-bottom:0}}
.tag{{flex:0 0 52px;height:52px;display:grid;place-items:center;border:1px solid var(--patina-d);
 color:var(--patina);font-family:ui-monospace,monospace;font-size:14px;font-weight:700;border-radius:2px}}
.tag.c{{border-color:var(--oxide-d);color:var(--oxide)}}
ol.pipe h4{{margin:0 0 4px;font-size:16px}}
ol.pipe p{{margin:0 0 6px;color:var(--mut);max-width:70ch}}
ol.pipe code{{font-size:11.5px;color:var(--dim)}}

/* tables */
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font-weight:600;color:var(--mut);padding:8px 10px;border-bottom:1px solid var(--rule);font-size:12px}}
td{{padding:7px 10px;border-bottom:1px solid rgba(49,64,74,.5);vertical-align:top}}
td.id{{color:var(--patina);font-size:12px;white-space:nowrap}}
td.dm{{color:var(--dim);font-size:11.5px}}
.two{{display:grid;grid-template-columns:1fr;gap:34px}}
@media(min-width:900px){{.two{{grid-template-columns:1fr 1fr}}}}

/* case */
.case{{border:1px solid var(--rule);background:var(--panel);border-radius:2px;overflow:hidden}}
.case .hd{{padding:14px 20px;background:var(--panel2);border-bottom:1px solid var(--rule);font-size:14px;font-weight:600}}
.case .bd{{padding:20px;font-size:13.5px}}
.facts{{display:grid;gap:6px;margin:0 0 18px;padding:0;list-style:none}}
.facts li{{display:flex;gap:10px;align-items:baseline}}
.facts em{{font-style:normal;font-size:11.5px;padding:1px 6px;border-radius:2px;border:1px solid var(--rule);color:var(--mut);white-space:nowrap}}
.res{{display:grid;gap:10px}}
.bar{{display:grid;grid-template-columns:120px 1fr 66px;gap:12px;align-items:center}}
.bar .track{{height:8px;background:var(--panel2);border-radius:1px;overflow:hidden}}
.bar .fill{{height:100%;background:var(--patina)}}
.bar.low .fill{{background:var(--dim)}}
.bar .v{{font-family:ui-monospace,monospace;font-size:12.5px;color:var(--mut)}}
.why{{margin:14px 0 0;padding:12px 14px;border-left:3px solid var(--oxide);background:rgba(192,90,68,.07);font-size:13px;color:var(--mut)}}
.next{{margin-top:16px;font-size:13px;color:var(--mut)}}
.next b{{color:var(--amber);font-weight:600}}

footer{{padding:44px 0 70px;color:var(--dim);font-size:12.5px}}
footer p{{max-width:70ch;margin:0 0 6px}}
</style></head><body>

<div class="wrap">
<div class="hero">
  <h1><small>EFI-Onto · 전기화재 발화 메커니즘 온톨로지</small>판독 결과는 결론이 아니라<br>검증해야 할 가설이다</h1>
  <p>FIReAct 프레임워크의 감별 절차를 OWL 2 DL과 SHACL로 정형화한 TBox입니다. 사진에서 읽은 형태학적 특징과 현장에서 확인한 사실을 서로 다른 존재론 범주에 두어, 둘이 섞이지 않은 채로 대조되도록 만들었습니다.</p>
  <div class="counts">
    <div><b>{N['c']}</b><span>클래스</span></div>
    <div><b>{N['op']}</b><span>객체 속성</span></div>
    <div><b>{N['dp']}</b><span>데이터 속성</span></div>
    <div><b>{N['r']}</b><span>단서 규칙</span></div>
    <div><b>{N['s']}</b><span>SHACL 규칙·제약</span></div>
  </div>
</div>

<section class="blk">
  <h2>네 개의 축</h2>
  <p class="lead">Table 1의 '형태학적 특징'과 '현장 추론 지표'가 한 칸에 섞여 있으면 추론이 무너집니다. 그래서 네 축을 BFO의 서로 다른 최상위 범주에 배정해, 존재론 층위에서 애초에 섞일 수 없게 했습니다.</p>
  {axes_html}
</section>

<section class="blk">
  <h2>보조 축</h2>
  <p class="lead">손상 양상은 증거물이 가진 성질이고, 현장 사실과 가설은 사람이 만든 정보 실체입니다. 사진으로 보이는 것과 사진 밖에 있는 것의 경계가 여기서 갈립니다.</p>
  {aux_html}
</section>

<section class="blk">
  <h2>가설은 어떻게 정의되는가</h2>
  <p class="lead">5대 요인은 발열 메커니즘으로 <span style="color:var(--patina)">정의</span>하고, 선행 조건은 <span style="color:var(--amber)">필요조건</span>으로만 붙였습니다. 오염 환경이 있다고 해서 트래킹이 되는 것은 아니지만, 오염 환경 없이 트래킹일 수는 없다는 뜻입니다.</p>
  <div class="def"><div class="formula">
<span class="k">TrackingScenario</span> &#8801; IgnitionScenario &#8851; &#8707;hasMechanism.<span class="k">SurfaceTracking</span><br>
<span class="k">TrackingScenario</span> &#8849; &#8707;requiresAntecedent.<span class="n">ContaminatedEnvironment</span><br>
<span class="k">TrackingScenario</span> &#8849; &#8707;manifestsAs.<span class="n">CarbonizedConductivePath</span><br><br>
<span class="k">PoorContactScenario</span> &#8801; IgnitionScenario &#8851; &#8707;hasMechanism.<span class="k">HighResistanceHeating</span><br>
<span class="k">PoorContactScenario</span> &#8849; &#8707;requiresAntecedent.<span class="n">LooseConnection</span><br><br>
<span class="k">PrimaryArcMark</span> &#8801; ArcMeltMark &#8851; &#8707;precedes.<span class="n">FireExposureEvent</span><br>
<span class="k">SecondaryArcMark</span> &#8801; ArcMeltMark &#8851; &#8707;precededBy.<span class="n">FireExposureEvent</span>
  </div></div>
  <p class="lead" style="margin-top:18px">1차·2차 단락흔을 가르는 기준을 형태가 아니라 <b>시간 선후</b>로 둔 것이 핵심입니다. 공극률이나 결정립 방위는 보강 근거로만 들어갑니다.</p>
</section>

<section class="blk">
  <h2>단서 규칙 {N['r']}개</h2>
  <p class="lead">논문 Table 2의 핵심·보강·반증 단서를 클래스가 아니라 규칙 인스턴스로 물화했습니다. 루브릭이 바뀌면 가중치만 갈아 끼우면 되고, 클래스 정의는 건드리지 않습니다.</p>
  <div class="legend">
    <span><i style="background:var(--patina)"></i>핵심 단서</span>
    <span><i style="background:var(--patina-d)"></i>보강 단서</span>
    <span><i style="background:var(--oxide)"></i>반증 단서</span>
    <span><i style="background:var(--amber)"></i>결정적 반증 — 즉시 기각</span>
    <span style="color:var(--dim)">가감점은 예시값. 실제 루브릭으로 교체 필요</span>
  </div>
  {rule_html}
</section>

<section class="blk">
  <h2>축을 가로지르는 연결</h2>
  <p class="lead">네 축을 나눈 것은 섞이지 않게 하기 위해서지 끊어 두기 위해서가 아닙니다. 축과 축은 명시적인 관계로만 이어지고, 그 경로가 곧 감식 논리의 추적 경로가 됩니다. 지금 {n_chain}개의 연결이 걸려 있습니다.</p>
  <div class="def" style="margin-bottom:26px"><div class="formula">
현장 사실 <span class="k">&mdash;증언&rarr;</span> 선행 조건 <span class="k">&mdash;성립&rarr;</span> 발열 메커니즘 <span class="k">&mdash;발현&rarr;</span> 손상 양상<br>
<span style="padding-left:23.5em">└<span class="n">&mdash;착화&rarr;</span> 최초 착화물</span><br>
물리 증거물 <span class="k">&mdash;보유&rarr;</span> 손상 양상
  </div></div>
  <p class="lead">읽는 법은 이렇습니다. 조사관이 "전날 비가 왔다"고 답하면 그것이 <b>누수·결로 노출</b>을 증언하고, 그 조건이 <b>트래킹 아크</b>를 성립시키며, 그 메커니즘이 <b>수지상 탄화 도전로</b>를 남기고 <b>피복</b>에 불을 붙입니다. 결론에 이르는 경로가 문장이 아니라 연결로 남습니다.</p>
  <div class="two" style="margin-bottom:26px">
    <div><h3 style="font-size:15px;margin:0 0 10px">현장 사실 → 선행 조건</h3>
      <table><tbody>{chain_att}</tbody></table></div>
    <div><h3 style="font-size:15px;margin:0 0 10px">선행 조건 → 발열 메커니즘</h3>
      <table><tbody>{chain_enables}</tbody></table></div>
  </div>
  <div class="two">
    <div><h3 style="font-size:15px;margin:0 0 10px">발열 메커니즘 → 손상 양상</h3>
      <table><tbody>{chain_prod}</tbody></table>
      <h3 style="font-size:15px;margin:24px 0 10px">발열 메커니즘 → 최초 착화물</h3>
      <table><tbody>{chain_ign}</tbody></table></div>
    <div><h3 style="font-size:15px;margin:0 0 10px">물리 증거물 → 지닐 수 있는 손상 양상</h3>
      <table><tbody>{chain_exh}</tbody></table></div>
  </div>
</section>

<section class="blk">
  <h2>형태학적으로 겹치는 지대</h2>
  <p class="lead">사진에 남는 흔적은 발화 요인마다 깔끔하게 나뉘지 않습니다. 각 가설이 남길 수 있는 손상 양상을 <code style="color:var(--patina)">canManifest</code>로 적어 두면, 두 가설의 교집합이 곧 사진만으로는 갈리지 않는 지대가 됩니다. 아래 혼동 쌍은 손으로 지정한 것이 아니라 그 교집합에서 자동으로 도출된 것입니다.</p>
  <table style="margin-bottom:30px"><thead><tr><th>가설 쌍</th><th style="text-align:center">공유</th><th>겹치는 손상 양상</th></tr></thead><tbody>{pair_rows}</tbody></table>

  <h3 style="font-size:15px;margin:0 0 4px">양상별 변별력</h3>
  <p class="lead" style="margin-bottom:16px">숫자는 그 흔적을 남길 수 있는 가설의 수입니다. 사진에서 가장 잘 보이는 피복 탄화와 아크 비드가 정작 변별력이 가장 낮습니다.</p>
  <div class="mgrid">{morph_cells}</div>

  <h3 style="font-size:15px;margin:32px 0 14px">가설별 발현 프로파일</h3>
  {prof_rows}
</section>

<section class="blk">
  <h2>추론은 반증부터 돌린다</h2>
  <p class="lead">순서가 설계의 일부입니다. 점수를 먼저 매기면 이미 기각됐어야 할 가설이 점수를 갖게 됩니다. 그래서 반증을 1번에 두었습니다.</p>
  <ol class="pipe">{pipe_html}</ol>
</section>

<section class="blk">
  <h2>소거법 오류를 막는 제약</h2>
  <p class="lead">"다른 게 다 아니니까 이거다"는 NFPA 921이 negative corpus로 경계하는 추론입니다. 온톨로지가 그 결론을 아예 통과시키지 않도록 제약으로 박아 넣었습니다.</p>
  <ol class="pipe">{cons_html}</ol>
</section>

<section class="blk">
  <h2>논문 사례 A를 실제로 돌리면</h2>
  <p class="lead">Table 10의 사례 A입니다. 사진 단독 판독은 접촉불량이었고, 질의 두 번으로 트래킹으로 교정된 사례입니다. 아래는 이 TBox에 사실을 넣고 SHACL과 Pydantic으로 각각 추론시킨 결과이며, 두 경로가 같은 값을 냈습니다.</p>
  <div class="case">
    <div class="hd">입력된 현장 사실 네 건</div>
    <div class="bd">
      <ul class="facts">
        <li><em>확인됨 · 조사관</em><span>우천 노출 — 사고 전날 강우, 옥외 단자함</span></li>
        <li><em>확인됨 · AI 판독</em><span>절연체 표면 탄화 도전로</span></li>
        <li><em>없음이 확인됨 · 조사관</em><span>접속부 헐거움 없음</span></li>
        <li><em>확인 불가</em><span>절연저항 — 측정값 없음</span></li>
      </ul>
      <div class="res">
        <div class="bar"><span>트래킹</span><span class="track"><span class="fill" style="width:75%"></span></span><span class="v">75 · 유효</span></div>
        <div class="bar low"><span>접촉불량</span><span class="track"><span class="fill" style="width:50%"></span></span><span class="v">50 · 유효</span></div>
      </div>
      <div class="why">접촉불량은 헐거움이 없다는 확인에도 <b>기각되지 않고 50점에 남습니다.</b> 확인 불가인 절연저항을 반증으로 쓰지 않기 때문입니다(C-1). 대신 확정 조건을 이렇게 막습니다 — 긍정 지지 사실 0건, 조사관 확인 사실 0건, 지지점수 50 미만 70. 소거만으로는 어떤 가설도 확정되지 않습니다.</div>
      <p class="next">다음에 물어야 할 것을 시스템이 고릅니다 &mdash; <b>소손 중심이 표면에 집중되어 있습니까?</b> 두 가설의 점수 차를 가장 크게 벌리는 항목이라 1순위입니다. 그다음은 단자 장기 발열 흔적, 비정상 온도·전압강하 순.</p>
    </div>
  </div>
</section>

<section class="blk">
  <h2>속성</h2>
  <div class="two">
    <div>
      <h3 style="font-size:15px;margin:0 0 10px">객체 속성 {N['op']}개</h3>
      <table><thead><tr><th>이름</th><th>뜻</th><th>정의역</th><th>치역</th></tr></thead><tbody>{op_rows}</tbody></table>
    </div>
    <div>
      <h3 style="font-size:15px;margin:0 0 10px">데이터 속성 {N['dp']}개</h3>
      <table><thead><tr><th>이름</th><th>뜻</th><th>정의역</th><th>자료형</th></tr></thead><tbody>{dp_rows}</tbody></table>
    </div>
  </div>
</section>

<footer>
  <p>이 화면은 efi_tbox.ttl 파일을 직접 읽어 생성했습니다. 손으로 그린 그림이 아니라 실제 온톨로지의 내용입니다.</p>
  <p>확인이 필요한 두 곳 — 단서 가감점은 예시값이라 실제 감별 루브릭으로 교체해야 하고, NFPA 921 조항 번호는 2024판 원문 대조 전이라 장 수준으로만 표기했습니다.</p>
</footer>
</div>
</body></html>'''

open('build/EFI-Onto_TBox_구조도.html', 'w', encoding='utf-8').write(HTML)
print('ok', len(HTML))
