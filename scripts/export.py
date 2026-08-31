# -*- coding: utf-8 -*-
"""efi_tbox.ttl → (1) GraphML (Cytoscape/Gephi/yEd) (2) Graphviz SVG (논문 삽입용)"""
import json, subprocess, xml.sax.saxutils as sx

G = json.load(open('build/graph.json', encoding='utf-8'))
KO = {n['id']: n['ko'] for n in G['nodes']}
AX = {n['id']: n['ax'] for n in G['nodes']}
AXN = {'mech': '발열 메커니즘', 'evid': '물리 증거물', 'ante': '선행 조건', 'fuel': '착화물',
       'dmg': '손상 양상', 'scene': '현장 사실', 'scen': '가설·판정', 'evt': '사건',
       'obs': '계측', 'meta': '절차 기록', 'enum': '열거값', 'agent': '행위자', 'other': '기타'}
AXC = {'mech': '#4FA894', 'evid': '#B07A4A', 'ante': '#D9963F', 'fuel': '#8A7BB5',
       'dmg': '#6E8BA6', 'scene': '#C05A44', 'scen': '#3F4C55', 'evt': '#8A7BB5',
       'obs': '#6E8BA6', 'meta': '#7A8A93', 'enum': '#8A959B', 'agent': '#7A8A93', 'other': '#8A959B'}
EK = {'sub': '상위', 'hasMechanism': '정의', 'hasAntecedent': '필요조건',
      'enables': '성립', 'producesDamage': '발현', 'ignites': '착화',
      'exhibits': '보유', 'attests': '증언', 'canManifest': '발현가능'}
EDGES = G['edges'] + [{'s': m['s'], 't': m['t'], 'k': 'canManifest'} for m in G['manifest']]
SHARED = {}
for m in G['manifest']:
    SHARED[m['t']] = SHARED.get(m['t'], 0) + 1

# ── GraphML ───────────────────────────────────────────────────────────────
q = sx.escape
gm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
      '<key id="label" for="node" attr.name="label" attr.type="string"/>',
      '<key id="uri" for="node" attr.name="uri" attr.type="string"/>',
      '<key id="axis" for="node" attr.name="axis" attr.type="string"/>',
      '<key id="color" for="node" attr.name="color" attr.type="string"/>',
      '<key id="shared" for="node" attr.name="sharedByScenarios" attr.type="int"/>',
      '<key id="rel" for="edge" attr.name="relation" attr.type="string"/>',
      '<key id="relko" for="edge" attr.name="relationKo" attr.type="string"/>',
      '<graph id="EFI-Onto" edgedefault="directed">']
for n in G['nodes']:
    gm.append(
        f'<node id="{q(n["id"])}">'
        f'<data key="label">{q(n["ko"])}</data>'
        f'<data key="uri">https://w3id.org/efi-onto#{q(n["id"])}</data>'
        f'<data key="axis">{q(AXN.get(n["ax"], n["ax"]))}</data>'
        f'<data key="color">{AXC.get(n["ax"], "#888888")}</data>'
        f'<data key="shared">{SHARED.get(n["id"], 0)}</data></node>')
for i, e in enumerate(EDGES):
    gm.append(f'<edge id="e{i}" source="{q(e["s"])}" target="{q(e["t"])}">'
              f'<data key="rel">{q(e["k"])}</data>'
              f'<data key="relko">{q(EK.get(e["k"], e["k"]))}</data></edge>')
gm += ['</graph>', '</graphml>']
open('build/EFI-Onto.graphml', 'w', encoding='utf-8').write('\n'.join(gm))

# ── Graphviz: 인과 사슬 도식 (논문 삽입용) ────────────────────────────────
CHAIN = ['attests', 'enables', 'producesDamage', 'ignites', 'exhibits']
keep = set()
for e in EDGES:
    if e['k'] in CHAIN:
        keep |= {e['s'], e['t']}
COL = {'attests': '#7C99AE', 'enables': '#D9963F', 'producesDamage': '#4FA894',
       'ignites': '#8A7BB5', 'exhibits': '#B07A4A'}
RANK = {'scene': 0, 'ante': 1, 'mech': 2, 'dmg': 3, 'fuel': 4, 'evid': 3}

d = ['digraph EFI {',
     '  rankdir=LR; bgcolor="#FFFFFF"; splines=spline; overlap=false;',
     '  nodesep=0.16; ranksep=1.5; pad=0.3;',
     '  node [shape=box style="rounded,filled" fontname="NanumGothic" fontsize=10 '
     'penwidth=0 fontcolor="#FFFFFF" margin="0.10,0.05" height=0.28];',
     '  edge [arrowsize=0.5 penwidth=0.8 fontname="NanumGothic" fontsize=8];']
groups = {}
for n in keep:
    groups.setdefault(AX.get(n, 'other'), []).append(n)
for ax in sorted(groups, key=lambda a: RANK.get(a, 9)):
    d.append(f'  subgraph cluster_{ax} {{ label="{AXN.get(ax, ax)}"; '
             f'fontname="NanumGothic" fontsize=11 fontcolor="#555555"; '
             f'color="#DDDDDD"; style=rounded;')
    for n in sorted(groups[ax], key=lambda x: KO.get(x, x)):
        d.append(f'    "{n}" [label="{KO.get(n, n)}" fillcolor="{AXC.get(ax, "#888")}"];')
    d.append('  }')
for e in EDGES:
    if e['k'] in CHAIN:
        d.append(f'  "{e["s"]}" -> "{e["t"]}" [color="{COL[e["k"]]}" '
                 f'tooltip="{EK[e["k"]]}"];')
d.append('}')
open('build/chain.dot', 'w', encoding='utf-8').write('\n'.join(d))
subprocess.run(['dot', '-Tsvg', 'build/chain.dot',
                '-o', 'build/EFI-Onto_인과사슬.svg'], check=True)
print('graphml nodes', len(G['nodes']), 'edges', len(EDGES))
print('dot nodes', len(keep))
