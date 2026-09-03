# -*- coding: utf-8 -*-
"""TBox 구조 점검. 기존 지표가 재지 않는 각도로 훑는다.

status.py 는 규모를, nfpa.py 는 이론 대비 이식률을, audit.py 는 형태 발현 편향을
잰다. 이 파일은 그 셋이 보지 않는 것을 본다 — 어휘가 사슬에 붙어 있는가,
선언해 놓고 쓰지 않는 것이 있는가, 축이 지켜지는가.

'어휘만 있고 절차가 없다'는 이 프로젝트가 반복해 겪은 실패다. ArcMapPoint 가
그랬고 downstreamIndex 가 그랬고 outcomeUndetermined 가 그랬다. 그래서 센다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import sys, pathlib, collections
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH, URIRef, Literal
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1] / "src"))
from efi_schema import load_graph, ontology_text

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
E = Namespace("https://w3id.org/efi-onto#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ln = lambda u: str(u).split("#")[-1]

AXES = ["HeatingMechanism", "PhysicalEvidence", "DamagePattern",
        "AntecedentCondition", "FirstFuelIgnited"]


def _subs(g, name):
    out = set()

    def walk(c):
        for s in g.subjects(RDFS.subClassOf, c):
            if isinstance(s, URIRef) and ln(s) not in out:
                out.add(ln(s))
                walk(s)
    walk(E[name])
    return out


def _named(g, t):
    return {ln(s) for s in g.subjects(RDF.type, t) if isinstance(s, URIRef)}


def _abstract(g, name):
    """하위 클래스가 있는 것은 추상 상위로 본다. 사슬은 잎에 붙으면 된다."""
    return bool(list(g.subjects(RDFS.subClassOf, E[name])))


def _ancestors(g, name):
    out = set()

    def walk(c):
        for o in g.objects(c, RDFS.subClassOf):
            if isinstance(o, URIRef) and ln(o) not in out:
                out.add(ln(o))
                walk(o)
    walk(E[name])
    return out


def _linked(g, name, pairs, side):
    """자신 또는 조상이 그 관계에 참여하면 연결된 것으로 본다."""
    fam = {name} | _ancestors(g, name)
    return any((a if side == 0 else b) in fam for a, b in pairs)


# 붙일 근거가 원문에 없다고 확인된 계측 속성. 임계값을 지어내 넣지 않는다.
# 확장 슬롯과 같이 결정이 끝났으므로 미완성 수에서 빼고 목록만 보여 준다.
# 근거가 생기면 여기서 빼고 사슬에 붙인다.
NO_CRITERION = {
    "beadDiameter_mm":        "비드 지름과 온도의 대응이 원문에 없다 (실무Ⅳ p.307 은 '추정할 수 있다'까지만)",
    "carbonizationDepth_mm":  "탄화 심도는 연소강약·발화개소 판정에 쓰이며 그 절차는 범위 밖이다",
    "conductorCrossSection_mm2": "반단선 판정은 소선 수로 한다 (D-11). 단면적을 쓰는 기준이 원문에 없다",
    "fineDendriticGrain":     "1차가 미세 공정조직이라는 것은 상대 비교이며 임계가 없다. 원문도 단독 단정을 금한다 (실무Ⅳ p.310)",
    "heatAffectedZoneWidth_mm": "열영향부 폭의 판정 기준이 원문에 없다",
    "minimumIgnitionEnergy_mJ": "견줄 아크 에너지 속성이 없다. F-3 은 온도로 착화 역량을 본다",
    "moistureExposureWithin_h": "은이행 조건은 '고온·다습'까지만이고 숫자가 없다",
    "relativeHumidity_pct":   "같은 이유로 숫자 기준이 없다",
    "tripDelayFromEvent_s":   "'외력 직후 즉시'의 시간 정의가 원문에 없다",
    "voidFraction":           "1차/2차를 가르는 기공률 임계는 확립된 표준이 없다 (선행연구도 EBSD+기계학습으로 판별)",
}


def checks(g):
    """(제목, 항목 목록, 설명) 의 목록."""
    out = []
    print_only = []
    mech = _subs(g, "HeatingMechanism")
    dmg = _subs(g, "DamagePattern")
    ante = _subs(g, "AntecedentCondition")
    fuel = _subs(g, "FirstFuelIgnited")
    scene = _subs(g, "SceneEvidence")

    rel = lambda p: {(ln(s), ln(o)) for s, o in g.subject_objects(E[p])}
    produces = rel("producesDamage")
    enables = rel("enables")
    ignites = rel("ignites")
    attests = rel("attests")
    declared = rel("hasDeclaredMechanism")

    out.append(("손상 양상을 만들지 않는 발열 메커니즘",
                sorted(m for m in mech if not _abstract(g, m) and not _linked(g, m, produces, 0)),
                "이 메커니즘이 일어나도 아무 흔적이 안 남는다는 뜻이 된다"))
    # 현행 9가설에서 독립 가설로 확장하지 않은 메커니즘이다.
    # OverloadHeating은 이미 OverloadScenario가 선언하므로 제외 목록에서 뺀다.
    # 새 독립 가설은 가설 집합·배타 공리·변별력 공식의 N을 함께 검토해야 한다.
    SLOTS = {"OpenNeutralOvervoltage", "SustainedFaulting"}
    out.append(("어떤 가설도 쓰지 않는 발열 메커니즘 (확장 슬롯 제외)",
                sorted(m for m in mech if not _abstract(g, m) and m not in SLOTS
                       and not _linked(g, m, declared, 1)),
                "가설로 세울 수 없어 판정에 등장하지 못한다"))
    # 구조 결함 검사에서만 제외한다. 원문 이식의 완료로 세지 않는다.
    print_only.append(("독립 가설 확장을 보류한 메커니즘", sorted(SLOTS),
                       "현재는 별도 가설이 아니다. 원문 이식 미완료 목록에서 보류 근거를 관리한다"))
    exhibits = rel("exhibits")
    out.append(("어디에도 붙지 않은 손상 양상",
                sorted(d for d in dmg if not _abstract(g, d)
                       and not _linked(g, d, produces, 1) and not _linked(g, d, exhibits, 1)),
                "메커니즘이 만들지도, 증거물이 나타내지도 않는다. "
                "기계적 손상처럼 발열이 원인이 아닌 것은 exhibits 로 붙는다"))
    out.append(("발열로 이어지지 않는 선행 조건",
                sorted(a for a in ante if not _abstract(g, a) and a != "DeEnergizedState"
                       and not _linked(g, a, enables, 0)),
                "확인해도 어떤 가설로도 연결되지 않는다. 비통전은 설계상 제외"))
    out.append(("어떤 메커니즘도 착화시키지 않는 착화물",
                sorted(f for f in fuel if not _abstract(g, f) and not _linked(g, f, ignites, 1)),
                "최초 착화물로 지목될 경로가 없다"))
    # 증언하지 않는 것이 정상인 것들. 이유를 적어 둔다.
    #   앞의 셋 — 원문이 '원인의 증거가 아니다'라고 못 박았다
    #   CorrespondingDamageArea — hasCorrespondingDamage 로 붙는다
    #   BurnPattern — 발화 지점 특정용. 그 절차는 범위 밖(설계계획서 1.1)
    #   NoArcOrSpatter — 외부화염의 핵심 단서(R_EF_core)로 직접 붙는다. 비통전을 증언하지는 않는다
    #   RcdHealthyNoTrip — 지락의 반증 단서(R_GF_ref2). 부재 증거라 아무 조건도 증언하지 않는다
    NOT_EVIDENCE = {"GroundingElectrodeDisconnection", "NickedOrStretchedConductor",
                    "UndersizedConductorFuel", "CorrespondingDamageArea", "BurnPattern", "NoArcOrSpatter",
                    "RcdHealthyNoTrip"}
    out.append(("아무것도 증언하지 않는 현장 사실",
                sorted(s for s in scene if not _abstract(g, s) and s not in NOT_EVIDENCE
                       and not _linked(g, s, attests, 0)),
                "수집해도 어떤 선행 조건도 뒷받침하지 못한다"))

    # 시나리오 완결성
    roles = collections.defaultdict(set)
    for r in g.subjects(RDF.type, E.IndicatorRule):
        roles[ln(g.value(r, E.forScenario))].add(ln(g.value(r, E.hasRole)))
    SC = [s for s in _subs(g, "IgnitionScenario") if s.endswith("Scenario")]
    out.append(("핵심 단서가 없는 가설",
                sorted(s for s in SC if not _abstract(g, s) and "Core" not in roles.get(s, ())),
                "무엇을 먼저 확인해야 하는지가 정해져 있지 않다"))

    # 미사용 어휘
    import re
    lines = ontology_text().split("\n")
    used = lambda n: any(re.search(rf"\befi:{n}\b", l) and not re.match(rf"\s*efi:{n}\s+a\s+owl:", l)
                         for l in lines)
    out.append(("선언만 되고 안 쓰이는 객체 속성",
                sorted(p for p in _named(g, OWL.ObjectProperty) if not used(p)), ""))
    unwired_dp = sorted(p for p in _named(g, OWL.DatatypeProperty) if not used(p))
    out.append(("선언만 되고 안 쓰이는 데이터 속성",
                [p for p in unwired_dp if p not in NO_CRITERION], ""))
    print_only.append(("계측 속성 — 붙일 근거가 없는 것으로 결정됨",
                       [p for p in unwired_dp if p in NO_CRITERION],
                       "임계값이나 견줄 짝이 원문에 없다. 지어내지 않는다"))

    # 이름이 겹치는 클래스 (라벨 중복)
    lab = collections.defaultdict(list)
    for s, o in g.subject_objects(SKOS.prefLabel):
        if isinstance(s, URIRef) and str(s).startswith(str(E)):
            lab[str(o)].append(ln(s))
    out.append(("같은 한글 라벨을 쓰는 클래스",
                sorted(f"{k}: {', '.join(v)}" for k, v in lab.items() if len(v) > 1),
                "용어가 갈리지 않으면 검토표에서 구별되지 않는다"))

    # 축을 두 개 이상 상속하는 클래스 (서로소라 DL 위반이 되어야 정상)
    multi = []
    for c in set().union(*[_subs(g, a) for a in AXES]):
        hit = [a for a in AXES if c in _subs(g, a)]
        if len(hit) > 1:
            multi.append(f"{c}: {', '.join(hit)}")
    out.append(("두 축에 동시에 속하는 클래스", sorted(multi),
                "축은 서로소다. 나오면 DL 일관성도 깨진다"))

    out.append(("판정에 닿은 기록 층 자원", sorted(_record_layer_touching_judgment(g)),
                "efi_investigation.ttl 은 기록의 완비만 본다. 점수·사슬·형성에 닿으면 "
                "추론이므로 efi_tbox.ttl 로 옮긴다"))
    print_only.append(("기록 전용 어휘 (efi_investigation.ttl)", sorted(_record_layer(g)),
                       "조사 기록의 어휘다. 사슬에 붙지 않는 것이 정상이며 구조 결함이 아니다. "
                       "다만 이 수가 자라면 추론이 아니라 서식이 자라는 것이다"))

    return out, print_only


# ── 기록 층 ──────────────────────────────────────────────────────────────
# 조사 기록 어휘는 사슬에 붙지 않는 것이 정상이라 위의 검사에 걸리면 안 된다.
# 그러나 자라는 것을 숨기지도 않는다 — 따로 세어 보인다.
JUDGMENT = ("scoreDelta", "canManifest", "enables", "producesDamage", "ignites",
            "exhibits", "attests", "hasDeclaredMechanism", "supportScore", "formed")


def _record_layer(g):
    """efi_investigation.ttl 이 선언한 이름들."""
    import re
    path = ROOT / "ontology" / "efi_investigation.ttl"
    if not path.exists():
        return set()
    return set(re.findall(r"^efi:(\w+)", path.read_text(encoding="utf-8"), re.M))


def _record_layer_touching_judgment(g):
    names = _record_layer(g)
    hit = set()
    for p in JUDGMENT:
        for s, o in g.subject_objects(E[p]):
            hit |= {ln(x) for x in (s, o) if ln(x) in names}
    return hit


def problems(g=None):
    g = g or load_graph()
    return [(t, items, why) for t, items, why in checks(g)[0] if items]


if __name__ == "__main__":
    g = load_graph()
    KO = {}
    for s, o in g.subject_objects(SKOS.prefLabel):
        KO.setdefault(ln(s), str(o))
    total = 0
    todo, noted = checks(g)
    for title, items, why in todo:
        print(f"\n■ {title}  {len(items)}건")
        if why:
            print(f"    {why}")
        for i in items[:20]:
            print(f"    - {KO.get(i, i)}" if i in KO else f"    - {i}")
        if len(items) > 20:
            print(f"    ... 외 {len(items) - 20}건")
        total += len(items)
    for title, items, why in noted:
        print(f"\n□ {title}  {len(items)}건  — 구조 결함 집계 제외, 원문 이식 완료와 별개")
        if why:
            print(f"    {why}")
        for i in items:
            print(f"    - {KO.get(i, i)}" if i in KO else f"    - {i}")
    print(f"\n합계 {total}건")
