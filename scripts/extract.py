
from rdflib import Graph, RDF, RDFS, OWL, URIRef, BNode, Namespace
from rdflib.collection import Collection
import json
EFI=Namespace("https://w3id.org/efi-onto#")
g=Graph().parse('ontology/efi_tbox.ttl',format='turtle')
def q(u): return str(u).split('#')[-1].split('/')[-1]
def ko(s):
    for o in g.objects(s,RDFS.label):
        if getattr(o,'language',None)=='ko': return str(o)
    return q(s)
cls=[s for s in set(g.subjects(RDF.type,OWL.Class)) if isinstance(s,URIRef) and str(s).startswith(str(EFI))]
names={q(c) for c in cls}
sup={q(c):[q(o) for o in g.objects(c,RDFS.subClassOf) if isinstance(o,URIRef) and q(o) in names] for c in cls}
AX={'HeatingMechanism':'mech','PhysicalEvidence':'evid','AntecedentCondition':'ante',
    'FirstFuelIgnited':'fuel','DamagePattern':'dmg','SceneEvidence':'scene',
    'IgnitionScenario':'scen','IndicatorRule':'meta','Conclusion':'meta',
    'VerificationQuery':'meta','InvestigationSession':'meta','ConfirmationStatus':'enum',
    'IndicatorRole':'enum','Verdict':'enum','Ignitability':'enum',
    'AIAgent':'agent','InvestigatorAgent':'agent','Instrument':'agent',
    'ArcEvent':'evt','FireExposureEvent':'evt','NormalInsulationResistance':'obs'}
def axis(n,seen=None):
    seen=seen or set()
    if n in AX: return AX[n]
    if n in seen: return 'other'
    seen.add(n)
    for p in sup.get(n,[]):
        a=axis(p,seen)
        if a!='other': return a
    return 'other'
shared={}
for s,o in g.subject_objects(EFI.canManifest): shared[q(o)]=shared.get(q(o),0)+1
nodes=[{"id":q(c),"ko":ko(c),"cm":(str(next(g.objects(c,RDFS.comment),'')) or '')[:180],
        "ax":axis(q(c)),"root":q(c) in AX,"sh":shared.get(q(c),0)} for c in cls]
edges=[{"s":c,"t":p,"k":"sub"} for c in sup for p in sup[c]]
def unwrap(b):
    if isinstance(b,URIRef): return [q(b)]
    u=g.value(b,OWL.unionOf)
    return [q(x) for x in Collection(g,u) if isinstance(x,URIRef)] if u is not None else []
for s,p,o in g:
    if isinstance(o,BNode) and p in (RDFS.subClassOf,OWL.equivalentClass) and isinstance(s,URIRef):
        items=[o]; inter=g.value(o,OWL.intersectionOf)
        if inter is not None: items=list(Collection(g,inter))
        for it in items:
            if not isinstance(it,BNode): continue
            pr=g.value(it,OWL.onProperty); vl=g.value(it,OWL.someValuesFrom) or g.value(it,OWL.allValuesFrom)
            if pr is None or vl is None: continue
            for t in unwrap(vl):
                if t in names: edges.append({"s":q(s),"t":t,"k":q(pr)})
rules=[]
for r in g.subjects(RDF.type,EFI.IndicatorRule):
    sc=[q(x) for x in g.objects(r,EFI.forScenario)]; ind=[q(x) for x in g.objects(r,EFI.indicates)]
    role=[q(x) for x in g.objects(r,EFI.hasRole)]; d=[int(x) for x in g.objects(r,EFI.scoreDelta)]
    if sc and ind: rules.append({"s":sc[0],"t":ind[0],"role":role[0] if role else "","d":d[0] if d else 0})
man=[{"s":q(s),"t":q(o)} for s,o in g.subject_objects(EFI.canManifest)]
for pr in ('enables','producesDamage','ignites','exhibits','attests'):
    for a,b in g.subject_objects(EFI[pr]):
        if q(a) in names and q(b) in names: edges.append({"s":q(a),"t":q(b),"k":pr})
print(json.dumps({"nodes":nodes,"edges":edges,"rules":rules,"manifest":man},ensure_ascii=False))
