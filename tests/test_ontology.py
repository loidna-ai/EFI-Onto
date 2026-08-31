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


# ── NFPA 921 조항 근거 ───────────────────────────────────────────────────
def test_every_shape_cites_nfpa(g):
    """방법론 층의 모든 제약·규칙은 NFPA 921 조항에 닿아야 한다.
    닿지 않는 규칙은 우리가 지어낸 절차라는 뜻이므로 그 사실이 드러나야 한다."""
    from rdflib import RDF, SH, URIRef
    from rdflib.namespace import DCTERMS
    bad = [q(sh) for sh in g.subjects(RDF.type, SH.NodeShape)
           if isinstance(sh, URIRef) and not any(
               "NFPA 921" in str(o) for o in g.objects(sh, DCTERMS.references))]
    assert not bad, f"조항 근거 없는 도형: {bad}"


def test_indicator_rules_do_not_cite_nfpa(g):
    """지표 규칙은 Table 2 · 국내 실무·선행연구에서 왔다. NFPA 조항을 붙이면
    출처가 왜곡된다. 출처 구분은 논문에서 뭉뚱그리지 않기 위한 것이다."""
    from rdflib import RDF
    from rdflib.namespace import DCTERMS
    bad = [q(r) for r in g.subjects(RDF.type, EFI.IndicatorRule)
           if any("NFPA" in str(o) for o in g.objects(r, DCTERMS.references))]
    assert not bad, f"지표 규칙에 NFPA 조항이 붙었다: {bad}"


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
    assert score("hT") == 71, "트래킹 71점 (탄화 도전로는 외부화염도 낸다 — §9.9.4.5)"
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
    efi:m3 a efi:BurnCenterOnSurface ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:hM efi:supportedBy efi:m3 .
    """), "전용 양상을 넣었는데 막혔다"


# ── §19.8 분류는 판정이 아니다 ───────────────────────────────────────────
def _msg(extra):
    return validate(Graph().parse(data=TTL.read_text(encoding="utf-8") + extra, format="turtle"),
                    advanced=True, allow_infos=True, allow_warnings=True)[2]


def test_classification_requires_a_determination():
    """C-9 — 원인 분류는 확정된 감별 의견을 가리켜야 한다. 분류가 판정을 대신할 수 없다."""
    assert "확정된 감별 의견" in _msg("""
    efi:kA a efi:FireCauseClassification ; efi:usesClassificationSystem efi:NFIRS ;
           efi:classificationCategory "예시 범주" .
    """)


def test_classification_must_name_its_system():
    """C-10 — 체계마다 범주 정의가 다르므로 어느 체계를 쓴 것인지 밝혀야 한다."""
    assert "분류 체계" in _msg("""
    efi:kB a efi:IncidentClassification ; efi:classificationCategory "예시 범주" .
    """)


def test_conclusion_cannot_carry_a_category():
    """C-11 — 감별 의견에 분류 범주를 직접 달면 통계 라벨이 원인 판정으로 읽힌다."""
    assert "분류 범주를 직접" in _msg("""
    efi:hK a efi:TrackingScenario ; efi:supportScore 75 .
    efi:cK a efi:Conclusion ; efi:concludes efi:hK ; efi:classificationCategory "예시 범주" .
    """)


# ── §4.5 확신도 ──────────────────────────────────────────────────────────
def test_tied_hypotheses_cannot_be_probable():
    """C-12 — 대등한 가설이 남아 있으면 개연이 아니라 가능이다 (§4.5.1.1(2)).
    점수를 확률로 읽지 않고 '유일하게 앞서는가'만 본다."""
    tie = """
    efi:sT a efi:InvestigationSession ; efi:queryCount 2 .
    efi:h1 a efi:TrackingScenario ; efi:inSession efi:sT ; efi:supportScore 75 .
    efi:h2 a efi:PoorContactScenario ; efi:inSession efi:sT ; efi:supportScore 75 .
    efi:cT a efi:Conclusion ; efi:concludes efi:h1 ; efi:certaintyLevel efi:Probable .
    """
    assert "개연이 아니라 가능" in _msg(tie)
    # 기각된 가설은 대등 경합으로 치지 않는다.
    assert "개연이 아니라 가능" not in _msg(tie + "efi:h2 efi:verdict efi:Refuted .")


def test_suspected_is_not_an_expert_opinion():
    """C-13 — 의심 수준은 전문가 의견이 아니다 (§4.5.1.2)."""
    assert "전문가 의견의 요건" in _msg("""
    efi:hS a efi:TrackingScenario ; efi:supportScore 55 .
    efi:cS a efi:Conclusion ; efi:concludes efi:hS ; efi:certaintyLevel efi:Suspected .
    """)


def test_unverifiable_fact_forces_limitation_disclosure():
    """C-15 — 확인 불가 사실이 있으면 그 한계를 밝혀야 한다 (§4.5).
    밝히지 않으면 그 사실이 없었던 것처럼 읽힌다."""
    base = CASE_A + """
    efi:hT efi:supportScore 75 .
    efi:cU a efi:Conclusion ; efi:concludes efi:hT ; efi:certaintyLevel efi:Possible .
    """
    assert "한계를 명시" in _msg(base)
    assert "한계를 명시" not in _msg(
        base + 'efi:cU efi:statedLimitation "절연저항 계측 불가" .')


# ── §4.6 검토 절차 ───────────────────────────────────────────────────────
def test_insider_review_is_not_peer_review():
    """C-17 — 같은 조사에 참여한 사람의 검토는 동료 검토가 아니다 (§4.6.3).
    이름을 잘못 붙이면 독립성 없는 검토가 독립 검토로 인용된다."""
    inside = """
    efi:sR a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invR a efi:InvestigatorAgent ; efi:participatedIn efi:sR .
    efi:rvR a efi:PeerReview ; efi:reviews efi:sR ; efi:reviewer efi:invR .
    """
    assert "동료 검토가 아니라 기술 검토" in _msg(inside)
    assert "동료 검토가 아니라 기술 검토" not in _msg(
        inside.replace("efi:invR a efi:InvestigatorAgent ; efi:participatedIn efi:sR .",
                       "efi:invR a efi:InvestigatorAgent ."))


def test_author_selected_reviewer_is_not_peer_review():
    """C-17 — 저자가 검토자를 고르면 동료 검토가 아니다 (§4.6.3)."""
    assert "동료 검토가 아니라 기술 검토" in _msg("""
    efi:sR2 a efi:InvestigationSession ; efi:queryCount 2 .
    efi:rvR2 a efi:PeerReview ; efi:reviews efi:sR2 ; efi:reviewerSelectedByAuthor true .
    """)


def test_peer_review_alone_cannot_validate_results():
    """C-20 — 동료 검토자는 논리 결함은 잡아도 자료 오류를 잡을 근거가 없다 (§4.6.3.2).
    잘못된 자료 위의 결론은 잘못될 수밖에 없다."""
    only_peer = """
    efi:sV a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hV a efi:TrackingScenario ; efi:inSession efi:sV ; efi:supportScore 75 .
    efi:rvV a efi:PeerReview ; efi:reviews efi:sV .
    efi:cV a efi:Conclusion ; efi:concludes efi:hV ;
           efi:certaintyLevel efi:Probable ; efi:reviewValidated true .
    """
    assert "기술 검토가 있어야" in _msg(only_peer)
    assert "기술 검토가 있어야" not in _msg(only_peer + """
    efi:rvT a efi:TechnicalReview ; efi:reviews efi:sV ; efi:hasDocumentationAccess true .
    """)


# ── §9.5.2 원문이 경고한 잘못된 추론 ─────────────────────────────────────
def test_grounding_removal_does_not_imply_open_neutral():
    """C-21 — 접지극 연결 제거는 중성선 단선의 원인이 아니다 (§9.5.2).
    원문이 명시적으로 경고하는 추론이라 구조로 막는다."""
    assert "접지 상태와 무관" in _msg("""
    efi:gE a efi:GroundingElectrodeDisconnection ; efi:attests efi:OpenNeutral .
    """)
    # 정당한 단서로 증언하는 것은 막지 않는다.
    assert "접지 상태와 무관" not in _msg("""
    efi:lB a efi:AbnormalLampBrightnessReport ; efi:attests efi:OpenNeutral .
    """)


def test_service_entrance_allows_sustained_faulting():
    """D-6 — 인입구는 과전류 보호가 없어 고장이 지속될 수 있다 (§9.3.4)."""
    gr = run("efi:seA a efi:ServiceEntrance .")
    assert list(gr.objects(EFI.seA, EFI.sustainedFaultingPossible))


# ── §4.3 과학적 방법 ─────────────────────────────────────────────────────
def test_hypothesis_built_on_absence_is_invalid():
    """C-23 — 부재만으로 지지된 가설은 시험할 수 없어 무효다 (§4.3.6.1).
    반증되지 않았다는 것은 참이라는 뜻이 아니다."""
    absent = """
    efi:sN a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invN a efi:InvestigatorAgent .
    efi:n1 a efi:LooseConnection ; efi:confirmationStatus efi:ConfirmedAbsent ;
           prov:wasAttributedTo efi:invN ; efi:analyzed true .
    efi:sN efi:hasFact efi:n1 .
    efi:hN a efi:TrackingScenario ; efi:inSession efi:sN ; efi:verdict efi:Supported ;
           efi:supportedBy efi:n1 .
    efi:cN a efi:Conclusion ; efi:concludes efi:hN ; efi:certaintyLevel efi:Probable .
    """
    assert "부재 위에 세운 가설" in _msg(absent)
    assert "부재 위에 세운 가설" not in _msg(
        absent.replace("efi:confirmationStatus efi:ConfirmedAbsent",
                       "efi:confirmationStatus efi:Confirmed"))


def test_untested_alternate_hypothesis_blocks_conclusion():
    """C-24 — 대안 가설을 고려하지 않는 것은 중대한 오류다 (§4.3.7)."""
    assert "대안 가설을 고려하지 않는 것" in _msg("""
    efi:sX a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hX1 a efi:TrackingScenario ; efi:inSession efi:sX ; efi:verdict efi:Supported .
    efi:hX2 a efi:PoorContactScenario ; efi:inSession efi:sX .
    efi:cX a efi:Conclusion ; efi:concludes efi:hX1 ; efi:certaintyLevel efi:Possible .
    """)


def test_all_refuted_becomes_undetermined():
    """C-25·D-7 — 어느 가설도 견디지 못하면 결론이 아니라 원인미상이다 (§4.3.6)."""
    gr = run("""
    efi:sZ a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hZ1 a efi:TrackingScenario ; efi:inSession efi:sZ ; efi:verdict efi:Refuted .
    efi:hZ2 a efi:PoorContactScenario ; efi:inSession efi:sZ ; efi:verdict efi:Refuted .
    """)
    assert list(gr.objects(EFI.sZ, EFI.outcomeUndetermined)), "원인미상 판정이 도출되지 않았다"


# ── §19.5~19.6 원인 가설 ─────────────────────────────────────────────────
def test_heat_producing_device_must_be_listed():
    """C-29 — 발화부의 발열 기기는 쉽게 배제되더라도 목록에 올려야 한다 (§19.5.1).
    뻔해 보인다는 이유로 빠지면 그 가설은 시험조차 되지 않는다."""
    base = """
    efi:sH a efi:InvestigationSession ; efi:queryCount 2 .
    efi:dH a efi:HeatProducingDevice ; efi:atOriginArea true .
    efi:sH efi:hasFact efi:dH .
    """
    assert "가설 목록에 없다" in _msg(base)
    assert "가설 목록에 없다" not in _msg(base + "efi:sH efi:hasCandidateSource efi:dH .")


def test_source_and_fuel_alone_are_not_a_cause():
    """C-30 — 발화원과 착화물을 짚은 것만으로는 원인이 아니다 (§19.6.5.2).
    둘을 한자리에 모은 정황이 있어야 원인이 된다."""
    base = """
    efi:hC a efi:TrackingScenario ; efi:hasMechanism [ a efi:ArcTracking ] .
    efi:cC a efi:Conclusion ; efi:concludes efi:hC .
    """
    assert "둘을 모은 정황이 없다" in _msg(base)
    assert "둘을 모은 정황이 없다" not in _msg(
        base + "efi:hC efi:hasAntecedent [ a efi:ContaminatedEnvironment ] .")


def test_two_surviving_hypotheses_are_undetermined():
    """D-8 — 둘 이상이 기각되지 않아도 원인미상이다 (§19.6.5.1).
    모두 기각된 경우만 잡던 D-7 의 반대편이다."""
    gr = run("""
    efi:sQ a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hQ1 a efi:TrackingScenario ; efi:inSession efi:sQ ; efi:supportScore 65 .
    efi:hQ2 a efi:PoorContactScenario ; efi:inSession efi:sQ ; efi:supportScore 65 .
    """)
    assert list(gr.objects(EFI.sQ, EFI.outcomeUndetermined)), "원인미상 판정이 도출되지 않았다"


# ── §9.9.1.2 방열 저해 ───────────────────────────────────────────────────
def test_heat_dissipation_impairment_justifies_overload():
    """C-34 — 과부하 발화는 보호가 정상이면 드물다. 예외는 도체 축소이거나
    열이 빠져나가지 못하는 상태다 (§9.9.3.2). 방열 저해가 그 근거가 된다."""
    base = """
    efi:hO a efi:IgnitionScenario ; efi:hasMechanism [ a efi:OverloadHeating ] .
    efi:cO a efi:Conclusion ; efi:concludes efi:hO .
    """
    assert "과부하 발화는 보호가 정상이면 드물다" in _msg(base)
    assert "과부하 발화는 보호가 정상이면 드물다" not in _msg(
        base + "efi:hO efi:hasAntecedent [ a efi:BundledWiring ] .")


def test_brief_arc_cannot_ignite_bulk_solid():
    """C-36 — 짧고 국부적인 아크로는 목재 구조재가 착화되지 않는다 (§9.9.4.1).
    F-3 은 온도만 본다. 연료의 형상·표면적은 다른 축이다."""
    wood = """
    efi:hW a efi:IgnitionScenario ; efi:hasMechanism [ a efi:ShortCircuitArc ] ;
           efi:hasFirstFuel [ a efi:WoodStructuralFuel ] .
    efi:cW a efi:Conclusion ; efi:concludes efi:hW .
    """
    assert "이 연료가 착화되지 않는다" in _msg(wood)
    assert "이 연료가 착화되지 않는다" not in _msg(
        wood.replace("efi:WoodStructuralFuel", "efi:PaperTextileFuel"))


# ── §9.11 원문이 명시적으로 부정하는 통념 ────────────────────────────────
def test_undersized_conductor_is_not_evidence_of_cause():
    """C-37 — 언더사이즈 도체·과대 보호기는 화재 원인의 증거가 아니다 (§9.11.1).
    허용 전류에는 큰 안전율이 있어 추가 발열만으로 피복이 벗겨지지 않는다."""
    assert "허용 전류에는 큰 안전율" in _msg("""
    efi:fU a efi:UndersizedConductorFuel ; efi:confirmationStatus efi:Confirmed .
    efi:hU a efi:IgnitionScenario ; efi:supportedBy efi:fU .
    efi:cU2 a efi:Conclusion ; efi:concludes efi:hU .
    """)


def test_nicked_conductor_is_not_a_heating_basis():
    """C-37 — 니크·연신에 의한 단면 감소는 발열 근거가 못 된다 (§9.11.2)."""
    assert "무시할 수준" in _msg("""
    efi:fN a efi:NickedOrStretchedConductor ; efi:confirmationStatus efi:Confirmed .
    efi:hN2 a efi:IgnitionScenario ; efi:supportedBy efi:fN .
    efi:cN2 a efi:Conclusion ; efi:concludes efi:hN2 .
    """)


def test_multiple_arc_beads_are_no_longer_exclusive(onto):
    """§9.10.2 — 화재 열로 탄화된 피복을 통한 아크는 여러 지점에서 일어난다.
    다발성 아크 비드를 반단선 전용으로 둔 것은 과대평가였다."""
    assert not onto.is_discriminating("MultipleArcBeads")


def test_fire_producibility_declarations_agree(g):
    """화재가 낼 수 있다고 판정한 양상은 외부화염 선언에 있어야 하고,
    낼 수 없다고 판정한 양상은 없어야 한다 (scripts/audit.py).

    이 온톨로지는 '이 가설이 이 흔적을 낸다'는 방향으로만 지어져, 화재 자체가
    만드는 흔적을 전기적 원인의 전용 단서로 오인하는 편향이 있었다. 원문 대조로
    다섯 건이 드러났고 이 시험이 재발을 막는다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit
    bad = audit.inconsistent(g)
    assert not bad, f"판정과 선언의 불일치: {bad}"


# ── V1: OWL 2 DL 일관성 ──────────────────────────────────────────────────
def _hermit_available():
    import shutil, importlib.util
    return shutil.which("java") and importlib.util.find_spec("owlready2")


@pytest.mark.skipif(not _hermit_available(), reason="HermiT 은 Java 와 owlready2 가 있어야 돈다")
def test_no_unsatisfiable_classes():
    """불만족 클래스가 없어야 한다. pySHACL 은 DL 일관성을 보지 않으므로
    정의 클래스와 축 배타 공리가 어긋나도 다른 시험은 전부 통과한다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import consistency
    bad, inconsistent, msg = consistency.check()
    assert not inconsistent, f"온톨로지 전체가 모순이다: {msg}"
    assert not bad, f"불만족 클래스: {bad}"


@pytest.mark.skipif(not _hermit_available(), reason="HermiT 은 Java 와 owlready2 가 있어야 돈다")
def test_consistency_checker_actually_detects(tmp_path):
    """검사기 자체의 반증 대조. 서로소인 두 축에 동시에 속하는 클래스를 넣으면
    반드시 잡혀야 한다. 한 번 거짓 통과를 낸 적이 있어 이 시험을 둔다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import consistency
    poison = tmp_path / "poison.ttl"
    poison.write_text(TTL.read_text(encoding="utf-8") + """
efi:DeliberatelyBroken a owl:Class ;
    rdfs:subClassOf efi:HeatingMechanism , efi:DamagePattern ;
    rdfs:label "고의로 깨뜨린 클래스"@ko .
""", encoding="utf-8")
    bad, _, _ = consistency.check(str(poison))
    assert "DeliberatelyBroken" in bad, f"검사기가 고의 결함을 놓쳤다: {bad}"


# ── Pydantic 파이프라인이 SHACL 과 같은 답을 내는가 ──────────────────────
def test_python_matches_shacl(onto):
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(case_id="A", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING,
                                       antecedents=["ContaminatedEnvironment"])],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM)])
    s.apply(onto)
    assert s.hypotheses[0].support_score == 71


def test_python_delegates_conclusion_checks_to_shacl():
    """Python 은 결론 제약을 옮겨 적지 않고 pySHACL 에 위임한다.

    제약을 두 곳에 적으면 갈라진다. 실제로 갈라졌었다 — SHACL 에 수십 개가
    쌓이는 동안 Python 은 초기 다섯 가지만 알고 있었다. 이 시험은 Python 이
    스스로 구현하지 않은 제약(C-3 선행 조건)을 실제로 보고하는지 확인한다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(case_id="V", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    msgs = s.validate(str(TTL))
    assert any("hasAntecedent" in m for m in msgs), f"SHACL 제약이 전달되지 않았다: {msgs}"


def test_serialization_does_not_duplicate_derived_values():
    """supportScore 는 owl:FunctionalProperty 다. Python 이 쓴 값과 F-4 가 계산한
    값이 겹치면 값이 둘이 되어 모순이다. 검증 입력에는 도출값을 넣지 않는다."""
    from efi_schema import Session, Hypothesis, Scenario, Mechanism
    s = Session(case_id="W",
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)])
    assert "supportScore" in s.to_turtle()
    assert "supportScore" not in s.to_turtle(include_derived=False)


def test_subclass_matching(onto):
    """'결로'라고 답해도 오염 환경 규칙에 걸려야 한다."""
    for c in ("MoistureExposure", "DustAccumulation", "SalineOrChemicalExposure"):
        assert onto.matches(c, "ContaminatedEnvironment"), c


def test_shared_morphology_is_not_discriminating(onto):
    assert not onto.is_discriminating("InsulationCarbonization")   # 6개 가설 공통
    assert not onto.is_discriminating("CarbonizedConductivePath")  # 화재 열로도 생긴다 (§9.9.4.5)
    assert onto.is_discriminating("BurnCenterOnSurface")           # 트래킹 전용
    assert onto.is_discriminating("MoistureExposure")              # 형태학이 아님
