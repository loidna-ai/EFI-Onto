# -*- coding: utf-8 -*-
"""EFI-Onto 회귀 시험. TTL 을 고쳤으면 반드시 통과해야 한다."""
import sys, pathlib
import pytest
from rdflib import Graph, Namespace
from pyshacl import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
sys.path.insert(0, str(ROOT / "src"))
EFI = Namespace("https://w3id.org/efi-onto#")
PROV = Namespace("http://www.w3.org/ns/prov#")
q = lambda u: str(u).split("#")[-1]


@pytest.fixture(scope="module")
def g():
    return Graph().parse(TTL, format="turtle")


@pytest.fixture(scope="module")
def inferred():
    gr = Graph().parse(TTL, format="turtle")
    validate(gr, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return gr


@pytest.fixture(scope="module")
def onto():
    from efi_schema import Ontology
    return Ontology.load(str(TTL))


# ── 구조 ──────────────────────────────────────────────────────────────────
def test_parses(g):
    assert len(g) > 1500


def test_every_class_has_korean_label(g):
    from rdflib import RDF, RDFS, OWL, URIRef
    missing = []
    for c in g.subjects(RDF.type, OWL.Class):
        if not isinstance(c, URIRef) or not str(c).startswith(str(EFI)):
            continue
        if not any(getattr(o, "language", None) == "ko" for o in g.objects(c, RDFS.label)):
            missing.append(q(c))
    assert not missing, f"한글 라벨 없음: {missing}"


# ── M-3: 선언한 형태 발현이 메커니즘으로 설명되는가 ──────────────────────
def test_manifestation_has_mechanistic_basis(inferred):
    bad = {}
    for s in set(inferred.subjects(EFI.canManifest, None)):
        dec = {q(x) for x in inferred.objects(s, EFI.canManifest)}
        der = {q(x) for x in inferred.objects(s, EFI.derivedManifestation)}
        if dec - der:
            bad[q(s)] = sorted(dec - der)
    assert not bad, f"메커니즘 근거 없는 형태 발현: {bad}"


# ── M-2: 논문이 보고한 혼동 쌍이 도출되는가 ──────────────────────────────
@pytest.mark.parametrize("a,b", [
    ("InsulationDegradationScenario", "CrushDamageScenario"),      # 논문 64회
    ("TrackingScenario", "PoorContactScenario"),                   # 논문 66회
    ("InsulationDegradationScenario", "TrackingScenario"),         # 일괄주입에서도 17회 잔존
])
def test_known_confusion_pairs_derived(inferred, a, b):
    pairs = {tuple(sorted([q(s), q(o)]))
             for s, o in inferred.subject_objects(EFI.morphologicallyAmbiguousWith)}
    assert tuple(sorted([a, b])) in pairs


# ── F-2: 아크흔 선후 판정이 규칙 층까지 도달하는가 ───────────────────────
def test_arc_mark_sequence_reaches_rules(g):
    """1·2차 단락흔은 형태가 아니라 시간 선후로 가른다(F-2). 그 판정을 소비하는
    지표 규칙이 없으면 원칙이 SHACL 안에 갇혀 판정에 영향을 주지 못한다."""
    from rdflib import RDF
    used = {q(g.value(r, EFI.indicates)) for r in g.subjects(RDF.type, EFI.IndicatorRule)}
    assert used & {"PrimaryArcMark", "SecondaryArcMark"}, "아크흔 선후를 쓰는 규칙이 없다"


# ── 가감점은 손으로 고르지 않는다 ────────────────────────────────────────
def test_score_deltas_are_derived(g):
    """모든 scoreDelta 는 scripts/score.py 의 공식에서 재현돼야 한다.
    TTL 을 손으로 고치면 여기서 걸린다. 가중치의 단일 진실 원천은 공식이다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import score
    from rdflib import RDF
    calc = score.deltas(g)
    ttl = {q(r): int(g.value(r, EFI.scoreDelta)) for r in g.subjects(RDF.type, EFI.IndicatorRule)}
    bad = {k: (ttl[k], v) for k, v in calc.items() if ttl.get(k) != v}
    assert not bad, f"손으로 고친 가감점 (TTL, 계산값): {bad}"


def test_shared_morphology_scores_zero():
    """6개 가설 전부가 낼 수 있는 흔적은 가중치가 0 이어야 한다.
    C-5 를 제약이 아니라 계산 결과로 얻는다는 것이 공식의 요지다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import score, math
    assert round(score.SUPPORT_MAX * math.log2(score.N / score.N) / math.log2(score.N)) == 0


def test_core_is_the_strongest_clue(g):
    """핵심 단서는 그 가설의 보강 단서보다 약할 수 없다.
    약하다면 역할 선언이 틀렸거나 더 변별력 있는 단서를 놓친 것이다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import score, collections
    d = score.deltas(g)
    by = collections.defaultdict(lambda: {"Core": [], "Supporting": []})
    for name, sc, ind, role in score.rules(g):
        if role in ("Core", "Supporting"):
            by[sc][role].append((ind, d[name]))
    bad = {sc: r for sc, r in by.items() if r["Supporting"] and r["Core"]
           and min(v for _, v in r["Core"]) < max(v for _, v in r["Supporting"])}
    assert not bad, f"핵심이 보강보다 약하다: {bad}"


def test_core_indicators_are_not_morphology(g):
    """핵심 단서가 형태학적 특징이면 사진만으로 가설이 선다. P1·C-5 와 충돌한다."""
    from rdflib import RDF, RDFS, URIRef
    def anc(c, seen=None):
        seen = set() if seen is None else seen
        for p_ in g.objects(c, RDFS.subClassOf):
            if isinstance(p_, URIRef) and p_ not in seen:
                seen.add(p_); anc(p_, seen)
        return {q(x) for x in seen}
    bad = [q(g.value(r, EFI.indicates)) for r in g.subjects(RDF.type, EFI.IndicatorRule)
           if q(g.value(r, EFI.hasRole)) == "Core"
           and "DamagePattern" in anc(EFI[q(g.value(r, EFI.indicates))])]
    assert not bad, f"형태학적 핵심 단서: {bad}"


# ── 논문 Table 10 사례 A ─────────────────────────────────────────────────
CASE_A = """
efi:sesA a efi:InvestigationSession ; efi:queryCount 2 .
efi:invA a efi:InvestigatorAgent .  efi:aiA a efi:AIAgent .
efi:a1 a efi:MoistureExposure ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invA .
efi:a2 a efi:CarbonizedConductivePath ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:aiA .
efi:a3 a efi:LooseConnection ; efi:confirmationStatus efi:ConfirmedAbsent ; prov:wasAttributedTo efi:invA .
efi:a4 a efi:InsulationResistanceObservation ; efi:confirmationStatus efi:Unverifiable .
efi:sesA efi:hasFact efi:a1 , efi:a2 , efi:a3 , efi:a4 .
efi:hT a efi:TrackingScenario ; efi:inSession efi:sesA ; efi:supportedBy efi:a1 , efi:a2 .
efi:hP a efi:PoorContactScenario ; efi:inSession efi:sesA .
"""


def run(extra):
    gr = Graph().parse(data=TTL.read_text(encoding="utf-8") + extra, format="turtle")
    validate(gr, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return gr


def test_case_a_scores():
    gr = run(CASE_A)
    score = lambda n: int(next(gr.objects(EFI[n], EFI.supportScore)))
    assert score("hT") == 75, "트래킹 75점"
    assert score("hP") == 50, "접촉불량은 헐거움 부재에도 기각되지 않고 50점"


def test_unverifiable_is_not_refutation():
    """C-1 — 절연저항 '확인 불가'가 트래킹을 기각해서는 안 된다."""
    gr = run(CASE_A)
    assert not list(gr.objects(EFI.hT, EFI.refutedBy))


def test_deenergized_refutes_all_electrical():
    gr = run("""
    efi:sesD a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invD a efi:InvestigatorAgent .
    efi:d1 a efi:DeEnergizedState ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invD .
    efi:sesD efi:hasFact efi:d1 .
    efi:hD a efi:TrackingScenario ; efi:inSession efi:sesD .
    efi:hX a efi:ExternalFlameScenario ; efi:inSession efi:sesD .
    """)
    assert int(next(gr.objects(EFI.hD, EFI.supportScore))) == 0
    assert int(next(gr.objects(EFI.hX, EFI.supportScore))) == 50


def test_c5_blocks_shared_morphology_only():
    """C-5 — 피복 탄화 + 아크 비드처럼 공유 양상만으로는 확정 불가."""
    base = """
    efi:sesM a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invM a efi:InvestigatorAgent .
    efi:m1 a efi:InsulationCarbonization ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:m2 a efi:ArcBead ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:hM a efi:TrackingScenario ; efi:inSession efi:sesM ; efi:supportScore 75 ;
           efi:supportedBy efi:m1 , efi:m2 .
    efi:cM a efi:Conclusion ; efi:concludes efi:hM .
    """
    fires = lambda extra: "공유 형태" in validate(
        Graph().parse(data=TTL.read_text(encoding="utf-8") + extra, format="turtle"),
        advanced=True, allow_infos=True, allow_warnings=True)[2]
    assert fires(base), "공유 양상만인데 통과했다"
    assert not fires(base + """
    efi:m3 a efi:CarbonizedConductivePath ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:hM efi:supportedBy efi:m3 .
    """), "전용 양상을 넣었는데 막혔다"


# ── Pydantic 파이프라인이 SHACL 과 같은 답을 내는가 ──────────────────────
def test_python_matches_shacl(onto):
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(case_id="A", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING,
                                       antecedents=["ContaminatedEnvironment"])],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM)])
    s.apply(onto)
    assert s.hypotheses[0].support_score == 75


def test_subclass_matching(onto):
    """'결로'라고 답해도 오염 환경 규칙에 걸려야 한다."""
    for c in ("MoistureExposure", "DustAccumulation", "SalineOrChemicalExposure"):
        assert onto.matches(c, "ContaminatedEnvironment"), c


def test_shared_morphology_is_not_discriminating(onto):
    assert not onto.is_discriminating("InsulationCarbonization")   # 6개 가설 공통
    assert onto.is_discriminating("CarbonizedConductivePath")      # 트래킹 전용
    assert onto.is_discriminating("MoistureExposure")              # 형태학이 아님
