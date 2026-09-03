# -*- coding: utf-8 -*-
"""efi_tbox.ttl → build/onto.json (구조도 build.py 입력)"""
from rdflib import Graph, RDF, RDFS, OWL, Namespace, URIRef
import json
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1] / "src"))
from efi_schema import load_graph

EFI = Namespace("https://w3id.org/efi-onto#")
g = load_graph()
q = lambda u: str(u).split('#')[-1].split('/')[-1]


def ko(s):
    for o in g.objects(s, RDFS.label):
        if getattr(o, 'language', None) == 'ko':
            return str(o)
    return ''


cls = [s for s in set(g.subjects(RDF.type, OWL.Class))
       if isinstance(s, URIRef) and str(s).startswith(str(EFI))]
names = {q(c) for c in cls}
node = {q(c): {"ko": ko(c),
               "cm": (str(next(g.objects(c, RDFS.comment), '')) or '')[:160],
               "sup": [q(o) for o in g.objects(c, RDFS.subClassOf)
                       if isinstance(o, URIRef) and q(o) in names],
               "eq": bool(list(g.objects(c, OWL.equivalentClass))),
               "dj": [q(o) for o in g.objects(c, OWL.disjointWith)]} for c in cls}


def props(t):
    return [{"n": q(p), "ko": ko(p),
             "d": [q(o) for o in g.objects(p, RDFS.domain) if isinstance(o, URIRef)],
             "r": [q(o) for o in g.objects(p, RDFS.range) if isinstance(o, URIRef)]}
            for p in sorted(set(g.subjects(RDF.type, t)), key=q)
            if str(p).startswith(str(EFI))]


rules = [{"n": q(s),
          "sc": [q(o) for o in g.objects(s, EFI.forScenario)],
          "ind": [q(o) for o in g.objects(s, EFI.indicates)],
          "role": [q(o) for o in g.objects(s, EFI.hasRole)],
          "st": [q(o) for o in g.objects(s, EFI.requiresStatus)],
          "d": [int(o) for o in g.objects(s, EFI.scoreDelta)]}
         for s in sorted(set(g.subjects(RDF.type, EFI.IndicatorRule)), key=q)]

man = {}
for s, o in g.subject_objects(EFI.canManifest):
    man.setdefault(q(s), []).append(q(o))
shared = {}
for v in man.values():
    for d in v:
        shared[d] = shared.get(d, 0) + 1
chain = {pr: [[q(a), q(b)] for a, b in g.subject_objects(EFI[pr])]
         for pr in ('enables', 'producesDamage', 'ignites', 'exhibits', 'attests')}

with open('build/onto.json', 'w', encoding='utf-8') as f:
    json.dump({"c": node, "op": props(OWL.ObjectProperty), "dp": props(OWL.DatatypeProperty),
               "rules": rules, "man": man, "shared": shared, "chain": chain},
              f, ensure_ascii=False)
print('build/onto.json', len(node), '클래스')
