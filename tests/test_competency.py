# -*- coding: utf-8 -*-
"""역량 질문 CQ1~CQ5 — 이 TBox 가 답하기로 한 질문에 실제로 답하는가 (설계계획서 1.2, 검증 계획 V2).

설계계획서가 온톨로지의 범위를 다섯 질문으로 정했다. 지금까지는 개별 규칙 시험이 이것을 암묵적으로
덮었을 뿐 질문 단위로 못 박은 적이 없었다. 여기서는 질문마다 하나씩, 설계 문서의 검증 방법 그대로 —
CQ1 F-2 실행 후 rdf:type, CQ2 필요조건과 세션 사실의 상태 조인, CQ3 discriminating_slots 와 SPARQL 스케치,
CQ4 F-3 → Weakened, CQ5 PROV 경로 질의.
"""
import sys, pathlib
from rdflib import Graph, Namespace, RDF
from pyshacl import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tests"))
from efi_schema import (Session, Hypothesis, Fact, Ontology, Scenario, Mechanism, Status, Agent, Verdict, Fuel,
                        DEFAULT_MECHANISM, ontology_text, load_graph)

EFI = Namespace("https://w3id.org/efi-onto#")
PROV = Namespace("http://www.w3.org/ns/prov#")
TIME = Namespace("http://www.w3.org/2006/time#")
q = lambda u: str(u).split("#")[-1]


def shacl(extra):
    g = Graph().parse(data=ontology_text() + extra, format="turtle")
    validate(g, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return g


# ── CQ1 ─────────────────────────────────────────────────────────────────────
def test_cq1_arc_mark_is_primary_or_secondary_by_time_and_unknown_when_time_is_missing():
    """CQ1 — 증거물의 아크 용융흔이 원인(1차)인지 결과(2차)인지는 아크 사건과 화염 노출의 선후로 판정한다.
    선후가 없으면 어느 쪽도 아니다 — 형태로 대신 판정하지 않는다(F-2, §9.10.2.1)."""
    base = """
    efi:arc a efi:ArcEvent . efi:fire a efi:FireExposureEvent .
    efi:m a efi:ArcMeltMark ; efi:formedBy efi:arc .
    """
    before = shacl(base + "efi:arc time:before efi:fire .")
    after = shacl(base + "efi:fire time:before efi:arc .")
    unknown = shacl(base)
    assert (EFI.m, RDF.type, EFI.PrimaryArcMark) in before and (EFI.m, RDF.type, EFI.SecondaryArcMark) not in before
    assert (EFI.m, RDF.type, EFI.SecondaryArcMark) in after and (EFI.m, RDF.type, EFI.PrimaryArcMark) not in after
    assert (EFI.m, RDF.type, EFI.PrimaryArcMark) not in unknown and (EFI.m, RDF.type, EFI.SecondaryArcMark) not in unknown, \
        "선후 없이 1차·2차를 판정했다"
    # 확보·미확보 목록 — 미확보인 것을 질의할 수 있어야 한다
    have = {q(p) for p, _ in unknown.predicate_objects(EFI.m)}
    assert "formedBy" in have and "locatedInOriginArea" not in have


# ── CQ2 ─────────────────────────────────────────────────────────────────────
def test_cq2_necessary_conditions_and_their_confirmation_status():
    """CQ2 — 가설 H 가 성립하려면 어떤 선행조건이 확인돼야 하며, 각각 확인/부정 확인/확인 불가/미확인 중 무엇인가."""
    onto = Ontology.load()
    need = onto.needs["PoorContactScenario"]
    assert need, "접촉불량의 필요조건이 선언돼 있지 않다"
    def status(facts):
        s = Session(case_id="cq2", hypotheses=[Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING)], facts=facts)
        s.apply(onto)
        return {n: s._slot_status(n, onto) for n in need}, s.hypotheses[0].formed
    st, formed = status([])
    assert set(st.values()) == {Status.MISSING} and not formed
    st, formed = status([Fact(cls="LooseConnection", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    assert Status.CONFIRMED in st.values() and formed, "하위(헐거움)의 확인이 상위 필요조건을 채우지 않았다"
    st, formed = status([Fact(cls="ConnectionCondition", status=Status.UNVERIFIABLE, agent=Agent.INVESTIGATOR)])
    assert Status.UNVERIFIABLE in st.values() and not formed, "확인 불가는 확인이 아니다 (P4)"
    st, formed = status([Fact(cls="ConnectionCondition", status=Status.CONFIRMED_ABSENT, agent=Agent.INVESTIGATOR)])
    assert Status.CONFIRMED_ABSENT in st.values() and not formed


# ── CQ3 ─────────────────────────────────────────────────────────────────────
def test_cq3_discriminating_indicators_between_two_competing_hypotheses():
    """CQ3 — 경합하는 두 가설에 대해 한쪽만 예측·반증하는 미확인 지표를 변별력 순으로 낸다.
    Python 의 discriminating_slots 와 설계계획서 1.3 의 SPARQL 스케치가 같은 지표를 가리켜야 한다."""
    onto = Ontology.load()
    s = Session(case_id="cq3", query_count=0,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING),
                            Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING)],
                facts=[Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM),
                       Fact(cls="LocalizedDiscoloration", status=Status.CONFIRMED, agent=Agent.AI_VLM)])
    s.apply(onto)
    slots = s.discriminating_slots(onto)
    assert slots, "변별 지표가 없다"
    assert {t for _, t, _ in slots} <= {Scenario.TRACKING, Scenario.POOR_CONTACT}
    weights = [w for _, _, w in slots]
    assert weights == sorted(weights, reverse=True), "변별력 순이 아니다"
    for ind, target, _ in slots:
        rules = [r for r in onto.rules if r.indicator == ind and r.scenario in (Scenario.TRACKING, Scenario.POOR_CONTACT)]
        assert rules and all(r.scenario == target for r in rules), f"{ind} 가 양쪽을 다 가리킨다"
    g = load_graph()
    rows = g.query("""
    PREFIX efi: <https://w3id.org/efi-onto#>
    SELECT DISTINCT ?indicator WHERE {
      VALUES (?h1 ?h2) { (efi:TrackingScenario efi:PoorContactScenario) }
      ?r a efi:IndicatorRule ; efi:forScenario ?favors ; efi:indicates ?indicator .
      FILTER ( ?favors IN (?h1, ?h2) )
      FILTER NOT EXISTS { ?r2 a efi:IndicatorRule ; efi:indicates ?indicator ; efi:forScenario ?other .
                          FILTER(?other IN (?h1, ?h2) && ?other != ?favors) }
    }""")
    sparql = {q(r.indicator) for r in rows}
    assert {i for i, _, _ in slots} <= sparql, "Python 이 고른 지표를 SPARQL 스케치가 변별 지표로 인정하지 않는다"


# ── CQ4 ─────────────────────────────────────────────────────────────────────
def test_cq4_ignition_competence_gap_weakens_in_both_engines():
    """CQ4 — 메커니즘의 최대 도달 온도가 착화물 발화 온도에 못 미치면 착화 역량 미달로 약화된다 (F-3).
    어느 요소가 부족한지(온도 차)가 드러나야 한다."""
    onto = Ontology.load()
    fuel = next(iter(Fuel))
    h = Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING,
                   first_fuel=fuel, mechanism_max_temp_c=300, fuel_ignition_temp_c=400)
    s = Session(case_id="cq4", hypotheses=[h]); s.apply(onto)
    assert h.verdict is Verdict.WEAKENED and any("착화 역량" in r for r in h.rationale)
    g = shacl(s.to_turtle(include_derived=False))
    n = EFI["cq4_PoorContactScenario"]
    assert (n, EFI.verdict, EFI.Weakened) in g and (n, EFI.ignitionCompetenceGap, None) in g
    ok = Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING,
                    first_fuel=fuel, mechanism_max_temp_c=500, fuel_ignition_temp_c=400)
    s2 = Session(case_id="cq4b", hypotheses=[ok]); s2.apply(onto)
    assert ok.verdict is Verdict.ACTIVE


# ── CQ5 ─────────────────────────────────────────────────────────────────────
def test_cq5_provenance_path_from_conclusion_to_evidence_and_agent():
    """CQ5 — 어떤 가설이 어떤 확인 사실로 결정적으로 기각됐고, 결론에 이르는 지지·기각 경로를
    증거 → 행위자 순으로 되짚을 수 있는가 (supportedBy·refutedBy ⊑ prov:wasDerivedFrom)."""
    onto = Ontology.load()
    s = Session(case_id="cq5", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM),
                       Fact(cls="DeEnergizedState", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    s.apply(onto)
    g = shacl(s.to_turtle(include_derived=False))
    tracking = EFI["cq5_TrackingScenario"]
    # 결정적 기각 — 비통전. 기각 근거 → 행위자 경로
    refuters = list(g.objects(tracking, EFI.refutedBy))
    assert refuters and (tracking, EFI.verdict, EFI.Refuted) in g, "비통전이 전기적 가설을 기각하지 않았다"
    kinds = {q(next(g.objects(f, RDF.type))) for f in refuters}
    assert "DeEnergizedState" in kinds
    agents = {q(next(g.objects(a, RDF.type))) for f in refuters for a in g.objects(f, PROV.wasAttributedTo)}
    assert "InvestigatorAgent" in agents, "기각 근거에서 행위자로 가는 경로가 없다"
    # 지지 경로도 PROV 로 읽힌다 — supportedBy·refutedBy ⊑ prov:wasDerivedFrom 이어야 경로 질의 하나로 되짚는다
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    assert (EFI.supportedBy, RDFS.subPropertyOf, PROV.wasDerivedFrom) in g
    assert (EFI.refutedBy, RDFS.subPropertyOf, PROV.wasDerivedFrom) in g
    supported_elsewhere = [h for h in s.hypotheses if h.supported_by]
    assert supported_elsewhere, "지지 근거가 하나도 안 남았다"
