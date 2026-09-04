# -*- coding: utf-8 -*-
"""EFI-Onto 회귀 시험. TTL 을 고쳤으면 반드시 통과해야 한다."""
import re, sys, pathlib
import pytest
from rdflib import Graph, Namespace, RDF, RDFS
from pyshacl import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
sys.path.insert(0, str(ROOT / "src"))
from efi_schema import load_graph, ontology_text
EFI = Namespace("https://w3id.org/efi-onto#")
PROV = Namespace("http://www.w3.org/ns/prov#")
q = lambda u: str(u).split("#")[-1]


@pytest.fixture(scope="module")
def g():
    return load_graph()


@pytest.fixture(scope="module")
def inferred():
    gr = load_graph()
    validate(gr, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return gr


@pytest.fixture(scope="module")
def onto():
    from efi_schema import Ontology
    return Ontology.load()


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


def test_core_is_a_declared_necessary_condition(g):
    """핵심 단서는 그 가설의 필요조건으로 선언돼 있어야 한다.

    이 온톨로지에서 핵심 단서란 '가장 변별력 있는 것'이 아니라 '없으면 성립하지
    않는 것'이다. CLAUDE.md 가 적어 둔 그대로 — 오염 환경이 있다고 트래킹인 것은
    아니지만 오염 환경 없이 트래킹일 수는 없다.

    전에는 가중치 순서(핵심 >= 보강)로 이것을 대신 쟀다. 대리 지표였고 실제로
    두 번 옳게 걸렸다(접촉불량의 징후, 압착손상의 결과). 그러나 사슬이 정확해져
    필요조건이 여러 요인과 양립하게 되자 대리 지표가 무너졌다 — 필요조건은
    좁히는 것이 아니라 거르는 것이라 양립 가설 수로 값을 매길 대상이 아니다.
    그래서 대리 지표를 버리고 재려던 것을 바로 잰다.
    """
    from rdflib import RDF, RDFS, OWL, URIRef
    import rdflib.collection as rc

    def declared(sc):
        out = set()
        for r in g.objects(EFI[sc], RDFS.subClassOf):
            if (r, OWL.onProperty, EFI.hasAntecedent) not in g:
                continue
            v = g.value(r, OWL.someValuesFrom)
            if isinstance(v, URIRef):
                out.add(q(v))
            elif v is not None:
                for u in g.objects(v, OWL.unionOf):
                    out |= {q(x) for x in rc.Collection(g, u)}
        return out

    def subs(c, acc=None):
        acc = set() if acc is None else acc
        for s in g.subjects(RDFS.subClassOf, c):
            if isinstance(s, URIRef) and q(s) not in acc:
                acc.add(q(s)); subs(s, acc)
        return acc

    bad = []
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        if q(g.value(r, EFI.hasRole)) != "Core":
            continue
        sc, ind = q(g.value(r, EFI.forScenario)), q(g.value(r, EFI.indicates))
        need = declared(sc)
        if not need:
            continue                      # 외부화염은 부재 근거로 서는 가설이다
        kids = subs(EFI[ind])
        if ind in need:
            continue
        if kids and kids <= need:
            continue                      # 필요조건들을 묶은 상위여도 된다
        bad.append((sc, ind, sorted(need)))
    assert not bad, f"핵심 단서가 필요조건이 아니다: {bad}"


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


def test_source_tables_name_existing_vocabulary(g):
    """원문 대조표(scripts/silmu.py, scripts/babrauskas.py)의 근거 칸이 부르는 클래스·규칙·도형·속성은
    TTL 에 있어야 한다. 이름이 바뀌거나 지워지면 대조표가 조용히 낡는다 —
    nfpa.py 의 SHAPE_REFS 가 test_every_shape_cites_nfpa 로 묶여 있는 것과 같다."""
    import re
    from rdflib import URIRef
    sys.path.insert(0, str(ROOT / "scripts"))
    import silmu, babrauskas
    names = {q(s) for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(str(EFI))}
    pat = re.compile(r"(?<![A-Za-z_])(?:[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+|[a-z]+(?:[A-Z][a-z0-9]*)+|R_[A-Z]{2,3}_[A-Za-z0-9]+)")
    rows = []
    for mod in (silmu, babrauskas):
        rows += ([(mod.__name__ + r[0], r[-1]) for r in mod.SECTIONS]
                 + [(mod.__name__ + r[0] + r[1], r[-1]) for r in mod.SUBSECTIONS]
                 + [(mod.__name__ + c[0], c[-1]) for c in mod.CANDIDATES])
    bad = sorted({(sec, tok) for sec, note in rows for tok in pat.findall(note) if tok not in names})
    assert not bad, f"대조표가 부르는 이름이 TTL 에 없다: {bad}"


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
    gr = Graph().parse(data=ontology_text() + extra, format="turtle")
    validate(gr, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return gr


def test_case_a_scores():
    gr = run(CASE_A)
    score = lambda n: int(next(gr.objects(EFI[n], EFI.supportScore)))
    # 71 → 62 → 65. 오염 환경이 트래킹 전용이 아니게 되면서 상위 지표는 6 이
    # 됐지만(습기는 절연열화로도, 염해는 접촉불량으로도 간다), 관측이 '습기'로
    # 구체적이면 그만큼 좁혀진 것이라 9 를 쓴다. 상위 규칙은 세지 않는다 —
    # 같은 관측을 두 해상도로 두 번 세는 것이기 때문이다.
    assert score("hT") == 65, "트래킹 65점 (습기 8 + 탄화 도전로 7 — 가설 9개 기준 유도값)"
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
    """C-5 — 피복 탄화 + 아크 비드처럼 공유 양상만으로는 확정 불가.

    트래킹으로 세운다. 편향 점검에서 소손 중심 표면 집중이 화재도냄으로 바뀐 뒤
    트래킹에는 전용 형태 단서가 하나도 남지 않았다. 그래서 이 가설을 세우려면
    비시각적 현장 사실(오염 환경)이 있어야 한다 — C-5 가 요구하는 바로 그것이다.
    """
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
        Graph().parse(data=ontology_text() + extra, format="turtle"),
        advanced=True, allow_infos=True, allow_warnings=True)[2]
    assert fires(base), "공유 양상만인데 통과했다"
    assert not fires(base + """
    efi:m3 a efi:MoistureExposure ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:hM efi:supportedBy efi:m3 .
    """), "비시각적 현장 사실을 넣었는데 막혔다"


def test_conclusion_requires_energized_state():
    """C-57 — 통전 확인 없이 전기적 발화를 확정할 수 없다 (§9.9.1, 실무Ⅳ p.178).
    지지 규칙이 아니라 문턱이다: 여섯 가설 전부와 양립하므로 점수로는 0 이지만
    필요조건이다. 확인 불가는 반증이 아니므로 가설을 기각하지는 않는다 — 결론만 막는다."""
    base = """
    efi:sesE a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invE a efi:InvestigatorAgent .
    efi:e1 a efi:MoistureExposure ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invE .
    efi:e2 a efi:InterPoleInsulatingSurface ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invE .
    efi:sesE efi:hasFact efi:e1 , efi:e2 .
    efi:hE a efi:TrackingScenario ; efi:inSession efi:sesE ; efi:supportScore 75 ; efi:supportedBy efi:e1 , efi:e2 .
    efi:cE a efi:Conclusion ; efi:concludes efi:hE .
    """
    fires = lambda extra: "통전 확인 없이" in validate(
        Graph().parse(data=ontology_text() + extra, format="turtle"),
        advanced=True, allow_infos=True, allow_warnings=True)[2]
    assert fires(base), "통전 확인이 없는데 확정이 통과했다"
    assert not fires(base + """
    efi:e3 a efi:EnergizedState ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invE .
    efi:sesE efi:hasFact efi:e3 .
    """), "통전을 확인했는데 막혔다"
    # 확인 불가는 확인이 아니다 — 여전히 막힌다. 그러나 가설을 기각하지는 않는다(C-1).
    assert fires(base + """
    efi:e4 a efi:EnergizedState ; efi:confirmationStatus efi:Unverifiable .
    efi:sesE efi:hasFact efi:e4 .
    """), "확인 불가를 확인으로 쳤다"
    # 외부화염은 전기적 가설이 아니므로 통전을 요구하지 않는다.
    assert not fires("""
    efi:sesX a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hX a efi:ExternalFlameScenario ; efi:inSession efi:sesX ; efi:supportScore 75 .
    efi:cX a efi:Conclusion ; efi:concludes efi:hX .
    """), "외부화염 결론에 통전을 요구했다"


# ── §19.8 분류는 판정이 아니다 ───────────────────────────────────────────
def _msg(extra):
    return validate(Graph().parse(data=ontology_text() + extra, format="turtle"),
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
    base = """
    efi:sQ a efi:InvestigationSession ; efi:queryCount 2 .
    efi:hQ1 a efi:TrackingScenario ; efi:inSession efi:sQ ; efi:supportScore 65 .
    efi:hQ2 a efi:PoorContactScenario ; efi:inSession efi:sQ ; efi:supportScore 65 .
    efi:q1 a efi:MoistureExposure ; efi:confirmationStatus efi:Confirmed .
    efi:q2 a efi:LooseConnection ; efi:confirmationStatus efi:Confirmed .
    """
    gr = run(base + "efi:sQ efi:hasFact efi:q1 , efi:q2 .")
    assert list(gr.objects(EFI.sQ, EFI.outcomeUndetermined)), "원인미상 판정이 도출되지 않았다"
    # D-15 — 접촉 상태가 자료에 없으면 접촉불량은 세워진 가설이 아니라 동점을 만들지 못한다
    gr = run(base + "efi:sQ efi:hasFact efi:q1 .")
    assert not list(gr.objects(EFI.sQ, EFI.outcomeUndetermined)), "형성되지 않은 가설이 동점을 만들었다"
    assert (EFI.hQ1, EFI.formed, None) in gr and (EFI.hQ2, EFI.formed, None) not in gr


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
    poison.write_text(ontology_text() + """
efi:DeliberatelyBroken a owl:Class ;
    rdfs:subClassOf efi:HeatingMechanism , efi:DamagePattern ;
    rdfs:label "고의로 깨뜨린 클래스"@ko .
""", encoding="utf-8")
    bad, _, _ = consistency.check(str(poison))
    assert "DeliberatelyBroken" in bad, f"검사기가 고의 결함을 놓쳤다: {bad}"


# ── 논리적 정합 ──────────────────────────────────────────────────────────
def test_a_complete_conclusion_can_pass():
    """제약을 40개 넘게 쌓았다. 통과 가능한 결론이 실제로 존재해야 한다.
    존재하지 않으면 이 시스템은 영원히 결론을 내지 못한다."""
    gold = """
    efi:sG a efi:InvestigationSession ; efi:queryCount 3 ; efi:hasCandidateSource efi:dG .
    efi:invG a efi:InvestigatorAgent .
    efi:dG a efi:HeatProducingDevice ; efi:atOriginArea true ;
           efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invG ; efi:analyzed true .
    efi:f1 a efi:ContaminatedEnvironment ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    efi:f2 a efi:CarbonizedConductivePath ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    efi:f3 a efi:BurnCenterOnSurface ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    # 오염 환경이 공유가 된 뒤로 트래킹은 단서 넷이 모여야 확정선에 닿는다.
    # 전에는 둘이면 됐다. 늘어난 요구가 정확한 요구다.
    efi:f4 a efi:OrganicInsulationPresent ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    efi:f5 a efi:IntermittentRcdTripping ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    # C-57 — 통전 확인은 점수에 들어가지 않지만 없으면 결론이 서지 않는다.
    efi:f6 a efi:EnergizedState ; efi:confirmationStatus efi:Confirmed ;
           prov:wasAttributedTo efi:invG ; efi:analyzed true .
    efi:sG efi:hasFact efi:dG , efi:f1 , efi:f2 , efi:f3 , efi:f4 , efi:f5 , efi:f6 .
    efi:fuelG a efi:InsulationMaterialFuel ; efi:distanceToHeatSource_mm 2 .
    efi:mechanismG a efi:ArcTracking .
    efi:hG a efi:TrackingScenario ; efi:inSession efi:sG ;
           efi:hasMechanism efi:mechanismG ; efi:hasFirstFuel efi:fuelG ;
           efi:hasAntecedent [ a efi:ContaminatedEnvironment ] ; efi:verdict efi:Supported ;
           efi:supportedBy efi:f1 , efi:f2 , efi:f3 , efi:f4 , efi:f5 ;
           efi:sourceCompetentForFuel true ; efi:timelineConsistent true ;
           efi:contactCircumstance "오염 표면 누설 전류로 탄화 경로 형성" ;
           efi:heatTransferPath "탄화 경로에서 접촉 피복으로 직접 전도" ;
           efi:arcInitiationMode "오염층 누설 전류가 표면을 탄화시켜 개시" ;
           efi:testedBy efi:TestByScientificPrinciple ;
           efi:addressesFactor efi:FactorFuelPresence , efi:FactorOxidantPresence ,
               efi:FactorSourcePresence , efi:FactorHeatTransfer , efi:FactorSafetyDevice ,
               efi:FactorBringingTogether , efi:FactorFireSpread .
    efi:hG2 a efi:PoorContactScenario ; efi:inSession efi:sG ; efi:verdict efi:Refuted ;
            efi:hasMechanism [ a efi:PoorContactHeating ] .
    efi:cG a efi:Conclusion ; efi:concludes efi:hG ; efi:certaintyLevel efi:Probable ;
           efi:statedLimitation "절연저항 계측 불가 구간 있음" .
    efi:fuelRecordG a efi:FirstFuelAssessment ; efi:recordSession efi:sG ;
           efi:assessedScenario efi:hG ; efi:assessedFuel efi:fuelG ;
           efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invG ;
           efi:recordSource "합성 사례 G의 현장 사진·잔존물 기록" ;
           efi:fuelPresenceBasis "발화 당시 접속부 피복의 존재를 사진과 잔존물로 확인" .
    efi:heatRecordG a efi:HeatTransferAssessment ; efi:recordSession efi:sG ;
           efi:assessedScenario efi:hG ; efi:assessedFuel efi:fuelG ; efi:assessedMechanism efi:mechanismG ;
           efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invG ;
           efi:recordSource "합성 사례 G의 열전달 검토·재현 기록" ;
           efi:transferDescription "탄화 경로에서 접촉 피복으로 직접 전도" ;
           efi:heatAdequacyBasis "동일 조건 재현으로 가열·열손실·착화를 확인" ;
           efi:durationBasis "사건 영상과 재현 시험의 가열 지속 구간 대조" ;
           efi:fuelConditionBasis "피복 두께·형상·위치 및 탄화 경로 접촉 확인" .
    """
    msgs = _msg(gold)
    assert "Message:" not in msgs and "Conforms: True" in msgs, "완전한 사례가 막혔다:\n" + msgs[:900]


def test_causal_chain_stays_class_level(g):
    """인과 사슬은 클래스끼리 잇는다. 개체 수준 진술이 섞이면 M-1 의 변별력 계산과
    M-2 의 혼동 쌍 판정이 개체까지 세어 틀어진다. ABox 가 들어올 때 위험하다."""
    from rdflib import RDF, OWL, URIRef
    CHAIN = ["canManifest", "producesDamage", "enables", "ignites", "attests",
             "exhibits", "hasDeclaredMechanism"]
    bad = []
    for p_ in CHAIN:
        for s_, o_ in g.subject_objects(EFI[p_]):
            for n in (s_, o_):
                if isinstance(n, URIRef) and str(n).startswith(str(EFI))                         and (n, RDF.type, OWL.Class) not in g:
                    bad.append(f"{p_}: {q(n)}")
    assert not bad, f"인과 사슬에 클래스가 아닌 것이 섞였다: {sorted(set(bad))}"


def test_scenario_list_comes_from_the_ontology():
    """변별력 공식의 N 은 TTL 의 가설 수여야 한다. 손으로 들고 있으면 시나리오가
    늘어도 N 이 그대로여서 모든 가중치가 조용히 틀린 값이 된다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import score
    from rdflib import Graph as G2
    gg = G2().parse(TTL, format="turtle")
    ttl = {q(s) for s in gg.subjects(RDFS.subClassOf, EFI.IgnitionScenario)} |           {q(s) for s in gg.subjects(RDFS.subClassOf, EFI.ElectricalIgnitionScenario)}
    ttl = {t for t in ttl if not list(gg.subjects(RDFS.subClassOf, EFI[t]))}
    assert set(score.SCENARIOS) == ttl, f"TTL {sorted(ttl)} vs score.py {sorted(score.SCENARIOS)}"
    assert score.N == len(ttl)


# ── Pydantic 파이프라인이 SHACL 과 같은 답을 내는가 ──────────────────────
def test_python_matches_shacl(onto):
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(case_id="A", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING,
                                       antecedents=["ContaminatedEnvironment"])],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM)])
    s.apply(onto)
    assert s.hypotheses[0].support_score == 65      # CASE_A 와 같은 값이어야 한다


def test_absence_direction_matches_in_both_engines():
    """부재 확인의 포섭 방향이 Python 과 SHACL 에서 같아야 한다.

    '헐거움 없음'은 상위인 '접속 상태 이상 없음'을 뜻하지 않는다. 반대로
    '접속 상태 이상 없음'은 하위인 '헐거움 없음'을 함의한다. 방향이 하나뿐이며
    두 엔진이 갈리면 점수와 검증이 어긋난다. 실제로 SHACL 쪽만 고쳤을 때
    골든 케이스가 깨졌다.
    """
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, Ontology
    onto = Ontology.load()

    def both(cls):
        s = Session(case_id="N", query_count=2,
                    hypotheses=[Hypothesis(scenario=Scenario.POOR_CONTACT,
                                           mechanism=Mechanism.POOR_CONTACT_HEATING)],
                    facts=[Fact(cls=cls, status=Status.CONFIRMED_ABSENT,
                                agent=Agent.INVESTIGATOR)])
        s.apply(onto)
        gr = run(f"""
        efi:sN a efi:InvestigationSession ; efi:queryCount 2 .
        efi:invN a efi:InvestigatorAgent .
        efi:n1 a efi:{cls} ; efi:confirmationStatus efi:ConfirmedAbsent ; prov:wasAttributedTo efi:invN .
        efi:sN efi:hasFact efi:n1 .
        efi:hN a efi:PoorContactScenario ; efi:inSession efi:sN .
        """)
        return s.hypotheses[0].support_score, int(next(gr.objects(EFI.hN, EFI.supportScore)))

    # 하위의 부재 — 상위 필요조건을 기각하지 못한다
    py, sh = both("LooseConnection")
    assert py == sh == 50, f"하위 부재가 기각시켰다: python {py}, shacl {sh}"
    # 상위의 부재 — 기각한다
    py, sh = both("ConnectionCondition")
    assert py == sh, f"두 엔진이 갈렸다: python {py}, shacl {sh}"
    assert py < 50, f"상위 필요조건 부재인데 기각되지 않았다: {py}"


def test_python_delegates_conclusion_checks_to_shacl():
    """Python 은 결론 제약을 옮겨 적지 않고 pySHACL 에 위임한다.

    제약을 두 곳에 적으면 갈라진다. 실제로 갈라졌었다 — SHACL 에 수십 개가
    쌓이는 동안 Python 은 초기 다섯 가지만 알고 있었다. 이 시험은 Python 이
    스스로 구현하지 않은 제약(C-3 선행 조건)을 실제로 보고하는지 확인한다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(case_id="V", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    # 같은 ABox 를 pySHACL 로 직접 돌린 결과와 일치해야 한다. 특정 제약에 기대면
    # 그 제약이 바뀔 때 시험이 깨지고, 정작 위임이 끊겨도 모른다.
    direct = _msg(s.to_turtle(include_derived=False))
    got = s.validate()
    assert all(m in direct for m in got), f"위임 결과가 직접 실행과 다르다: {got}"
    assert ("Conforms: True" in direct) == (not got)


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


def test_every_scenario_can_be_refuted_two_ways(g):
    """가설마다 반증 경로가 둘 이상 있어야 한다.

    P3 는 반증을 점수보다 먼저 실행하라 하는데, 정작 다섯 요인이 반증 규칙을
    하나씩만 갖고 그 다섯 지표가 사례 150건에서 전부 0건이었다. 반증이 한 번도
    발동하지 않는 채로 '반증 우선'을 구현했다고 적고 있었던 셈이다.
    필요조건의 부재 확인을 반증 경로로 물화해 채웠다.
    """
    from rdflib import RDF
    import collections
    n = collections.Counter()
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        if q(g.value(r, EFI.hasRole)) in ("Refuting", "DecisiveRefuting"):
            n[q(g.value(r, EFI.forScenario))] += 1
    scen = {q(s) for s in g.subjects(RDFS.subClassOf, EFI.ElectricalIgnitionScenario)}
    scen.add("ExternalFlameScenario")
    bad = {s: n[s] for s in scen if n[s] < 2}
    assert not bad, f"반증 경로가 둘 미만인 가설: {bad}"


def test_each_indicator_rule_says_one_thing(g):
    """규칙 하나는 가설 하나·지표 하나·역할 하나·점수 하나여야 한다.

    같은 id 를 두 번 쓰면 RDF 는 둘을 한 자원으로 합친다. 오류가 아니라
    조용한 병합이라 파싱도 통과하고 DL 일관성도 통과한다. 실제로 세 건이
    그렇게 합쳐져 있었고, 지표 셋이 사라진 채로 시험이 전부 녹색이었다.
    """
    from rdflib import RDF
    bad = []
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        for prop in (EFI.forScenario, EFI.indicates, EFI.hasRole, EFI.scoreDelta,
                     EFI.requiresStatus):
            n = len(set(g.objects(r, prop)))
            if n != 1:
                bad.append((q(r), q(prop), n))
    assert not bad, f"규칙이 여러 값을 갖는다(id 중복 의심): {bad}"


def test_vocabulary_is_wired(g):
    """선언만 하고 사슬에 붙이지 않은 어휘가 없어야 한다.

    ArcMapPoint 가 그랬고 downstreamIndex 가 그랬고 outcomeUndetermined 가
    그랬다. 어휘만 있고 절차가 없으면 확인해도 판정에 기여하지 못한다.
    23 → 0 으로 닫고 래칫에서 이관했다.

    범위 밖으로 결정한 것(확장 슬롯 셋)과 붙일 근거가 원문에 없다고 확인한 것
    (계측 속성 열)은 lint 가 따로 관리한다. 결정을 미완성으로 세면 결정이 지워진다.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import lint
    bad = lint.problems(g)
    assert not bad, f"사슬에 붙지 않은 어휘: {[(t_, i) for t_, i, _ in bad]}"


def test_constraint_numbers_are_unique(g):
    """C-번호를 두 번 쓰지 않는다.

    번호는 문서와 발표에서 제약을 가리키는 이름이다. 겹치면 어느 것을 말하는지
    갈리지 않는다. 실제로 새 절을 붙이며 C-48~50 을 다시 썼다.
    도형 id 와 달리 주석이라 RDF 도 시험도 잡지 못한다 — 여기서 센다.
    """
    import re, collections
    text = ontology_text()
    n = collections.Counter(re.findall(r"\[([CMFD]-\d+)\]", text))
    dup = {k: v for k, v in n.items() if v > 1}
    assert not dup, f"번호가 겹친다: {dup}"


def test_cause_chain_declarations_agree(g):
    """원인 축 판정과 사슬이 어긋나면 안 된다.

    '이 조건은 다른 요인도 일으킨다'고 적어 놓고 사슬을 하나로 두면 아무 일도
    일어나지 않는다. 판정만 적고 사슬을 안 고치는 실수를 막는다.
    형태 축의 test_fire_producibility_declarations_agree 와 같은 짝이다.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import cause_audit
    bad = cause_audit.inconsistent(g)
    assert not bad, f"판정과 사슬 불일치: {bad}"


def test_every_cause_answers_the_exclusivity_question(g):
    """모든 선행 조건은 '정말 그 요인에서만 일어나는가'에 답이 있어야 한다.

    답이 없는 채로 한 가설에만 이어 두면 변별력이 과대평가된다. 실제로 그렇게
    좁혀 둔 것이 열한 건 나왔다. 11 → 0 으로 닫고 래칫에서 이관했다.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import cause_audit
    assert not cause_audit.unreviewed(g), f"전용성 미검토: {cause_audit.unreviewed(g)}"


def test_every_morphology_answers_the_fire_question(onto):
    """모든 손상 양상은 '화재 자체도 이 흔적을 내는가'에 답이 있어야 한다.

    답이 없는 채로 전용 단서 노릇을 하면 변별력이 과대평가된다. 실제로 그렇게
    과대평가된 것이 여섯 건 나왔다. 8 → 0 으로 닫고 래칫에서 이관했다.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit
    assert not audit.unreviewed(), f"화재 발현 미검토: {audit.unreviewed()}"


def test_shared_morphology_is_not_discriminating(onto):
    assert not onto.is_discriminating("InsulationCarbonization")   # 6개 가설 공통
    assert not onto.is_discriminating("CarbonizedConductivePath")  # 화재 열로도 생긴다 (§9.9.4.5)
    assert not onto.is_discriminating("BurnCenterOnSurface")       # 외부 화염도 표면부터 태운다 (실무Ⅳ p.153)
    assert onto.is_discriminating("MoltenOxideMass")               # 접촉불량 전용 (§9.10.3.3)
    assert onto.is_discriminating("MoistureExposure")              # 형태학이 아님


def test_refuting_rules_have_no_counterexamples(onto):
    """반증 규칙은 정답 라벨의 사례에서 발동하면 안 된다.

    반증 후보를 조사관에게 "맞습니까?"로 묻는 대신 사례로 센다. 정답 라벨에서
    발동하는 반증은 맞는 답을 깎는 규칙이며, 그 지표가 다른 요인에서도 나온다는
    뜻이다. 검토표 시트 6 의 후보 하나(관통부 마모)가 그렇게 걸러졌다.
    사례 파일은 git 밖이므로 없으면 건너뛴다.
    """
    import json
    path = ROOT / "cases" / "sessions.json"
    if not path.exists():
        pytest.skip("cases/sessions.json 없음 — python scripts/slots.py 로 만든다")
    sys.path.insert(0, str(ROOT / "scripts"))
    import refute_audit
    sessions = json.loads(path.read_text(encoding="utf-8"))
    bad = [(rid, lbl) for rid, *_, n, cnt, lbl in refute_audit.existing(onto, sessions) if cnt]
    assert not bad, f"정답 라벨에서 발동하는 반증 규칙: {bad}"


def test_verdicts_match_in_both_engines(onto):
    """반증의 판정이 Python 과 SHACL 에서 같아야 한다.

    SHACL F-1 은 반증 단서 하나로 곧바로 기각하고 Python 은 감점 후 40 미만이면
    약화였다. test_python_matches_shacl 이 점수만 견주어 못 잡았다. 논문 3.2 는
    결정적 사실만 기각 수준이고 나머지는 가감점 누적이므로 Python 쪽에 맞췄다.
    """
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    cases = {
        # 반증 단서 하나: 접촉불량 -13 → 37 → 약화. 기각이 아니다
        "weak": (Scenario.POOR_CONTACT, Mechanism.POOR_CONTACT_HEATING, "BurnCenterOnSurface"),
        # 결정적 반증: 비통전 → 기각
        "dead": (Scenario.TRACKING, Mechanism.ARC_TRACKING, "DeEnergizedState"),
    }
    for name, (sc, mech, fact) in cases.items():
        s = Session(case_id=name, query_count=2,
                    hypotheses=[Hypothesis(scenario=sc, mechanism=mech)],
                    facts=[Fact(cls=fact, status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
        s.apply(onto)
        py = s.hypotheses[0].verdict.value
        gr = run(s.to_turtle(include_derived=False))
        h = next(gr.subjects(EFI.inSession, None))
        sh = sorted(q(v) for v in gr.objects(h, EFI.verdict))
        assert sh == [py], f"{name}: Python {py} vs SHACL {sh}"
        assert int(next(gr.objects(h, EFI.supportScore))) == s.hypotheses[0].support_score


def test_rule_shapes_declare_execution_order(g):
    """규칙을 가진 도형은 도형 수준 sh:order 를 가져야 한다.

    P3 는 '반증이 점수보다 먼저'를 규칙의 sh:order 1→4 로 구현했다고 적었지만,
    pySHACL 은 규칙 순서를 도형 안에서만 지키고 도형끼리는 도형의 sh:order 로
    정렬한다. 도형에 값이 없으면 전부 0 이라 사전 순서로 돌았고, 실제로 F-4 가
    F-1 보다 먼저 돌았다. F-4 가 판정을 읽지 않아 드러나지 않았을 뿐이다.
    도형의 sh:order 는 그 도형 규칙의 최소 sh:order 와 같아야 한다.
    """
    from rdflib import SH
    bad = []
    for sh in set(g.subjects(SH.rule, None)):
        want = min(int(g.value(r, SH.order) or 0) for r in g.objects(sh, SH.rule))
        got = g.value(sh, SH.order)
        if got is None or int(got) != want:
            bad.append((q(sh), got and int(got), want))
    assert not bad, f"도형 sh:order 가 없거나 규칙과 어긋남 (도형, 지금, 필요): {bad}"


def test_tracking_site_is_derived_in_both_engines(onto):
    """D-13 — 기기 내부·단자 + 오염 확인 → 그 대상은 이극 도체 간 절연물 표면.

    새 사실을 만들지 않고(C-4) 대상 사실에 유형을 덧붙인다. Python derive() 와
    SHACL TrackingSiteDerivationRuleShape 가 같은 점수를 내야 한다. 오염이 없으면
    대상만으로는 아무 점수도 없다 — 대상 어휘는 다섯 요인에 고루 나온다.
    """
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    d = {r.id: r.delta for r in onto.rules}          # 가감점은 유도값이라 숫자를 박지 않는다
    for facts, want in ((["DeviceInteriorSite", "MoistureExposure"], 50 + d["R_TR_sup4"] + d["R_TR_sup7"]),
                        (["TerminalSite", "DustAccumulation"], 50 + d["R_TR_sup5"] + d["R_TR_sup7"]),
                        (["DeviceInteriorSite"], 50),
                        (["CordMidspanSite", "MoistureExposure"], 50 + d["R_TR_sup4"])):
        s = Session(case_id="d13", query_count=2,
                    hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)],
                    facts=[Fact(cls=c, status=Status.CONFIRMED, agent=Agent.INVESTIGATOR) for c in facts])
        s.apply(onto)
        assert s.hypotheses[0].support_score == want, f"Python {facts}"
        gr = run(s.to_turtle(include_derived=False))
        h = next(gr.subjects(EFI.inSession, None))
        assert int(next(gr.objects(h, EFI.supportScore))) == want, f"SHACL {facts}"


def test_formation_matches_in_both_engines(onto):
    """D-15 — 가설 형성이 Python 과 SHACL 에서 같아야 한다.

    노후 절연만 적힌 조사서에서 절연열화는 세워지고 누전·지락·층간단락은 세워지지
    않는다 — 지락 경로도 권선도 자료에 없다. 외부화염은 제한이 없어 언제나 세워진다.
    """
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, DEFAULT_MECHANISM
    s = Session(case_id="F", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                facts=[Fact(cls="AgedInsulation", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="ArcMeltMark", status=Status.CONFIRMED, agent=Agent.AI_VLM),
                       Fact(cls="EnergizedState", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    s.apply(onto)
    py = {h.scenario.value: h.formed for h in s.hypotheses}
    assert py["InsulationDegradationScenario"] and py["ExternalFlameScenario"]
    assert not py["GroundFaultScenario"] and not py["InterTurnShortScenario"] and not py["OverloadScenario"]
    assert s.outcome(onto) == "InsulationDegradationScenario"
    gr = run(s.to_turtle(include_derived=False))
    sh = {q(h).split("_", 1)[1]: (h, EFI.formed, None) in gr for h in gr.subjects(EFI.inSession, None)}
    assert sh == py, f"Python {py} vs SHACL {sh}"


def test_unidentified_short_circuit_matches_in_both_engines(onto):
    """D-14 — 원인미상 + 단락흔 + 통전 확인이면 미확인 단락. 두 엔진이 같아야 한다.

    단락흔이 없으면 원인미상이고, 통전이 확인되지 않았으면(비통전이든 미확인이든) 전기적 요인이라
    분류할 수 없어 원인미상이다 — C-57 과 같은 기준.
    """
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, DEFAULT_MECHANISM
    def sess(facts):
        s = Session(case_id="U", query_count=2,
                    hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                    facts=[Fact(cls=c, status=Status.CONFIRMED, agent=Agent.INVESTIGATOR) for c in facts])
        return s.apply(onto)
    s = sess(["ArcMeltMark", "EnergizedState"])          # 세워지는 가설이 외부화염뿐, 지지 없음 → 판단보류, 단락흔 있음
    assert s.outcome(onto) == "UnidentifiedShortCircuit"
    gr = run(s.to_turtle(include_derived=False))
    assert (EFI.session_U, EFI.outcomeUndetermined, None) in gr
    assert (EFI.session_U, EFI.outcomeUnidentifiedShortCircuit, None) in gr
    s = sess(["EnergizedState"])                         # 단락흔 없음 → 원인미상
    assert s.outcome(onto) == "Undetermined"
    gr = run(s.to_turtle(include_derived=False))
    assert (EFI.session_U, EFI.outcomeUndetermined, None) in gr
    assert (EFI.session_U, EFI.outcomeUnidentifiedShortCircuit, None) not in gr
    s = sess(["ArcMeltMark", "DeEnergizedState"])        # 비통전 → 전기 요인 아님 → 원인미상
    assert s.outcome(onto) == "Undetermined"
    assert (EFI.session_U, EFI.outcomeUnidentifiedShortCircuit, None) not in run(s.to_turtle(include_derived=False))
    s = sess(["ArcMeltMark"])                            # 통전 미확인 → 모르는 것은 통전이 아니다(P4, C-57) → 원인미상
    assert s.outcome(onto) == "Undetermined"
    assert (EFI.session_U, EFI.outcomeUnidentifiedShortCircuit, None) not in run(s.to_turtle(include_derived=False))


def test_measurement_derivations_reach_scores():
    """계측에서 도출한 사실(D-1·D-2·D-3·D-9·D-11·보호장치 부동작)이 점수까지 닿아야 한다.

    전에는 도출 결과를 증거물에 붙여서 F-4 가 못 보았다 — 조사서에 계측값이 0건이라 아무도
    몰랐다. 이제 도출은 세션의 사실이 되고, 형성(D-15)과 점수(F-4)가 그것을 읽는다.
    """
    gr = run("""
    efi:sM a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invM a efi:InvestigatorAgent .
    efi:wire a efi:StrandedConductor ; efi:strandCount 30 ; efi:fracturedStrandCount 6 ; efi:partialDisconnectionRatio 0.1 ;
        efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:cord a efi:ElectricalArtifact ; efi:loadCurrent_A 20 ; efi:ratedCurrent_A 15 ;
        efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:cb a efi:ProtectiveDevice ; efi:overcurrentMultiple 2 ; efi:overcurrentDuration_min 10 ; efi:ratedTripTime_min 4 ;
        efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:ins a efi:Insulation ; efi:insulationResistance_MOhm 0.05 ; efi:requiredInsulationResistance_MOhm 0.2 ;
        efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:cp a efi:ConnectionPoint ; efi:cuprousOxidePresent true ; efi:oxideMassGrowthConfirmed true ;
        efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invM .
    efi:sM efi:hasFact efi:wire , efi:cord , efi:cb , efi:ins , efi:cp .
    efi:hPD a efi:PartialDisconnectionScenario ; efi:inSession efi:sM .
    efi:hOL a efi:OverloadScenario ; efi:inSession efi:sM .
    efi:hID a efi:InsulationDegradationScenario ; efi:inSession efi:sM .
    efi:hPC a efi:PoorContactScenario ; efi:inSession efi:sM .
    """)
    facts = {q(t) for f in gr.objects(EFI.sM, EFI.hasFact) for t in gr.objects(f, RDF.type)}
    for want in ("StrandFracture", "StrandFractureOverTenPercent", "OverloadState",
                 "ProtectiveDeviceFailedToOperate", "ReducedInsulationResistance", "CuprousOxideGrowth"):
        assert want in facts, f"{want} 가 세션의 사실로 도출되지 않았다"
    score = lambda n: int(next(gr.objects(EFI[n], EFI.supportScore)))
    for h in ("hPD", "hOL", "hID", "hPC"):
        assert (EFI[h], EFI.formed, None) in gr, f"{h} 가 도출 사실로 세워지지 않았다"
        assert score(h) > 50, f"{h} 점수가 도출 사실로 오르지 않았다"
    # 도출 사실은 C-4 를 지킨다 — 출처가 있다
    from rdflib.namespace import Namespace
    PROV = Namespace("http://www.w3.org/ns/prov#")
    for f in gr.objects(EFI.sM, EFI.hasFact):
        assert (f, PROV.wasAttributedTo, None) in gr


def test_conclusion_requires_a_formed_hypothesis():
    """C-58 — 세워지지 않은 가설로는 결론을 낼 수 없다 (§19.4.1). D-15 의 뒷문을 닫는다."""
    base = """
    efi:sF a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invF a efi:InvestigatorAgent .
    efi:g1 a efi:ArcMeltMark ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invF .
    efi:g2 a efi:EnergizedState ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invF .
    efi:hF a efi:GroundFaultScenario ; efi:inSession efi:sF ; efi:supportedBy efi:g1 , efi:g2 .
    efi:cF a efi:Conclusion ; efi:concludes efi:hF .
    """
    fired = lambda extra: "Message: 세워지지 않은 가설" in _msg(extra)   # 보고서는 도형 정의도 찍으므로 Message 줄만 본다
    assert fired(base + "efi:sF efi:hasFact efi:g1 , efi:g2 .")
    # 지락 경로가 확인되면 세워진다
    ok = base + """
    efi:g3 a efi:GroundPath ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invF .
    efi:sF efi:hasFact efi:g1 , efi:g2 , efi:g3 .
    """
    assert not fired(ok)


def test_declared_manifestations_cover_mechanisms(g):
    """가설의 정의 메커니즘이 내는 흔적은 가설의 canManifest 에도 있어야 한다.

    M-3 은 반대 방향(선언한 것이 유도되는가)만 본다. 이 방향이 비면 그 흔적의 공유 가설 수가
    적게 세어져 가감점이 부푼다 — 접촉불량의 아크 용융흔이 그랬다.
    """
    import collections
    mech = collections.defaultdict(set); prod = collections.defaultdict(set); man = collections.defaultdict(set)
    for s, o in g.subject_objects(EFI.hasDeclaredMechanism): mech[q(s)].add(q(o))
    for s, o in g.subject_objects(EFI.producesDamage): prod[q(s)].add(q(o))
    for s, o in g.subject_objects(EFI.canManifest): man[q(s)].add(q(o))
    bad = {sc: sorted(set().union(*(prod[m] for m in ms)) - man[sc]) for sc, ms in mech.items()}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"메커니즘은 내는데 가설이 선언하지 않은 흔적: {bad}"


def test_secondary_arc_refutation_is_recorded():
    """F-2 가 F-1 앞에 돌아야 2차 단락흔 반증이 refutedBy 에 적힌다 (순서 구멍)."""
    gr = run("""
    efi:sS a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invS a efi:InvestigatorAgent .
    efi:arcS a efi:ArcEvent .  efi:fireS a efi:FireExposureEvent .
    efi:fireS time:before efi:arcS .
    efi:mS a efi:ArcMeltMark ; efi:formedBy efi:arcS ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invS .
    efi:sS efi:hasFact efi:mS .
    efi:hS a efi:CrushDamageScenario ; efi:inSession efi:sS .
    """)
    assert (EFI.mS, RDF.type, EFI.SecondaryArcMark) in gr
    assert (EFI.hS, EFI.refutedBy, EFI.mS) in gr, "2차 단락흔 반증이 기록되지 않았다"


@pytest.mark.skipif(not _hermit_available(), reason="HermiT 은 Java 와 owlready2 가 있어야 돈다")
def test_mechanism_subsumption_is_caught(tmp_path):
    """정의 메커니즘이 서로소여야 정의의 겹침이 불만족 클래스로 드러난다.

    가설 클래스만 배타면 "층간 순환전류 발열 ⊑ 절연파괴 단락 아크" 같은 실수를 HermiT 가 못 잡는다 —
    이름 있는 클래스는 여전히 만족 가능하기 때문이다. 메커니즘에 배타 공리를 두면 그 포섭이
    층간단락 가설을 절연열화 가설 안으로 넣어 두 배타 가설의 교집합, 즉 불만족 클래스가 된다.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import consistency
    poison = tmp_path / "subsume.ttl"
    poison.write_text(ontology_text() +
                      "\nefi:InterTurnShortCircuit rdfs:subClassOf efi:InsulationBreakdownArc .\n", encoding="utf-8")
    bad, inconsistent, _ = consistency.check(poison)
    assert inconsistent or bad, "메커니즘 포섭 실수를 DL 검사가 잡지 못했다"


# ── 층 경계 (재편 1단계) ────────────────────────────────────────────────
INVESTIGATION = ROOT / "ontology" / "efi_investigation.ttl"
JUDGMENT_PROPS = ("scoreDelta", "canManifest", "enables", "producesDamage",
                  "ignites", "exhibits", "attests", "hasDeclaredMechanism",
                  "supportScore", "formed")


def _investigation_names():
    import re
    return set(re.findall(r"^efi:(\w+)", INVESTIGATION.read_text(encoding="utf-8"), re.M))


def test_investigation_layer_never_touches_scoring(g):
    """조사 기록 층은 점수·사슬·형성에 닿지 않는다.

    기록의 완비는 원인 판정이 아니다 — 연결이 확인돼도 통전이 아니고, 토크 기록이
    있어도 체결 상태가 유지됐다는 뜻이 아니다. 이 경계가 무너지면 서식을 채운 것이
    가점이 되고, 그것은 이 온톨로지가 막으려는 바로 그 일이다.
    판정에 닿아야 하는 도형은 efi_tbox.ttl 에 둔다.
    """
    names, bad = _investigation_names(), {}
    for p in JUDGMENT_PROPS:
        for s, o in g.subject_objects(EFI[p]):
            for x in (s, o):
                if q(x) in names:
                    bad.setdefault(p, set()).add(q(x))
    assert not bad, f"기록 층이 판정에 닿았다: {bad}"


def test_every_ontology_file_is_loaded(g):
    """온톨로지 파일 목록의 단일 진실 원천이 실제 파일과 같다.

    파일 이름을 손으로 든 곳이 열아홉이었다. 하나를 빠뜨리면 그 층이 통째로
    사라진 채 시험이 전부 통과한다 — 없는 것을 검사하는 시험은 없기 때문이다.
    """
    from efi_schema import ontology_files
    assert {p.name for p in ontology_files()} == {p.name for p in (ROOT / "ontology").glob("*.ttl")}
    assert len(g) == len(load_graph()), "적재 경로가 갈렸다"


# ── 절 배치 (재편 2단계) ────────────────────────────────────────────────
SECTION_OF = {"PoorContactScenario": "7.1", "CrushDamageScenario": "7.2",
              "PartialDisconnectionScenario": "7.3", "InsulationDegradationScenario": "7.4",
              "TrackingScenario": "7.5", "ExternalFlameScenario": "7.6",
              "OverloadScenario": "7.7", "GroundFaultScenario": "7.8",
              "InterTurnShortScenario": "7.9"}
ANCHOR = re.compile(r"^# \[([\d.]+)\][^\n]*\n(?:#[^\n]*\n)*# ={10,}\n", re.M)


def _sections():
    parts = ANCHOR.split(TTL.read_text(encoding="utf-8"))
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def test_indicator_rule_lives_in_its_hypothesis_section(g):
    """지표 규칙은 자기 가설의 절 안에 있다.

    한 가설을 이해하려면 한 자리만 읽으면 되게 하려고 재편했다. 새 규칙을 파일
    끝에 덧붙이면 다시 흩어진다 — 그것이 재편 전의 상태였다.
    """
    secs, stray = _sections(), []
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        sc = next((q(x) for x in g.objects(r, EFI.forScenario)), None)
        want = SECTION_OF.get(sc)
        if want and f"efi:{q(r)} " not in secs.get(want, ""):
            stray.append((q(r), want))
    assert not stray, f"자기 가설 절 밖에 있는 지표 규칙: {stray}"


def test_every_section_anchor_is_present():
    """절 앵커가 다 있어야 문서·backlog 가 가리킬 자리가 있다."""
    assert set(_sections()) == {"1", "2", "3", "4", "5", "6", "7", "8"} | set(SECTION_OF.values())


def test_one_korean_pref_label_per_resource(g):
    """자원마다 한글 prefLabel 은 하나다. rdfs:label 이 있으면 그것과 같다.

    라벨을 나중에 한 번 더 붙이는 통에 58개 자원이 이름을 둘씩 가졌고, 검토표는
    그중 둘째를 보여 줬다. '2차 단락흔'이 '2차 수열흔'으로 나갔다 — 표 4-9 에서
    열흔은 통전 없는 흔적이라 다른 것이다. 둘째 이름은 altLabel 로 내리거나 지웠다.
    """
    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
    ko = lambda s, p: {str(o) for o in g.objects(s, p) if getattr(o, "language", None) == "ko"}
    bad = []
    for s in set(g.subjects(SKOS.prefLabel, None)):
        if not str(s).startswith(str(EFI)):
            continue
        pref, lab = ko(s, SKOS.prefLabel), ko(s, RDFS.label)
        if len(pref) > 1 or (lab and lab != pref):
            bad.append((q(s), sorted(pref), sorted(lab)))
    assert not bad, f"한글 이름이 갈린 자원: {bad[:10]}"


def test_no_redundant_named_superclass(g):
    """명명 부모 둘 중 하나가 다른 하나에 포섭되면 넓은 쪽은 군더더기다.

    정의 줄에 넓은 부모를 적어 두고 나중에 좁은 부모를 한 줄 덧붙이는 식으로
    22개가 생겼다. 상위 정렬(BFO·SOSA·PROV)처럼 서로 포섭하지 않는 다중 부모는 둔다.
    """
    from rdflib import OWL
    bad = []
    for c in g.subjects(RDF.type, OWL.Class):
        if not isinstance(c, type(EFI.x)) or not str(c).startswith(str(EFI)):
            continue
        ps = [p for p in g.objects(c, RDFS.subClassOf) if isinstance(p, type(c))]
        for p in ps:
            for r in ps:
                if p != r and p in set(g.transitive_objects(r, RDFS.subClassOf)):
                    bad.append((q(c), q(p), q(r)))
    assert not bad, f"군더더기 부모: {sorted(set(bad))[:10]}"



# ── 아크 매핑 — 최하류·절연전선 지시력의 조건 (D-5·D-10·D-18·C-58) ──────────
ARC_MAP = """
efi:invO a efi:InvestigatorAgent .
efi:sesO a efi:InvestigationSession ; efi:queryCount 2 .
efi:circO a efi:BranchCircuit ; efi:overcurrentProtected true .
efi:wireO a efi:InsulatedWire ; efi:exhibits efi:mkO .
efi:pO1 a efi:ArcMapPoint ; efi:onCircuit efi:circO ; efi:downstreamIndex 1 .
efi:pO2 a efi:ArcMapPoint ; efi:onCircuit efi:circO ; efi:downstreamIndex 2 .
efi:mkO a efi:ArcMeltMark ; efi:locatedInOriginArea efi:pO2 ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invO .
efi:sesO efi:hasFact efi:mkO .
efi:hO a efi:PoorContactScenario ; efi:inSession efi:sesO ; efi:supportScore 75 .
efi:cO a efi:Conclusion ; efi:concludes efi:hO ; efi:originEvidence efi:mkO .
"""
LOCALIZED = """
efi:xO a efi:FireExposureExtentObservation ; efi:observedCircuit efi:circO ; efi:exposureExtent efi:LocalizedExposure ;
       efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invO .
efi:sesO efi:hasFact efi:xO .
"""
NO_INDICATION = "지시력을 갖지 못한다"
BERNSTEIN = "전반 화재 노출이 확인됐다"


def test_downstream_mark_indicates_origin_when_exposure_localized_and_protected():
    """D-5 → D-10 → C-58. 최하류 지점의 단락흔은 노출 국부·과전류 보호가 확인될 때 지시력을 갖는다."""
    gr = run(ARC_MAP + LOCALIZED)
    assert (EFI.pO2, EFI.furthestDownstream, None) in gr, "D-5 가 최하류를 표시하지 않았다"
    assert (EFI.mkO, EFI.originIndicativeArcMark, None) in gr, "D-10 이 지시력을 세우지 않았다"
    assert NO_INDICATION not in _msg(ARC_MAP + LOCALIZED)


def test_origin_indication_needs_exposure_record():
    """노출 기록이 없으면 지시력이 서지 않는다 — 미확인은 국부가 아니다 (P4). D-10 이 전에는 무조건이었다."""
    gr = run(ARC_MAP)
    assert (EFI.mkO, EFI.originIndicativeArcMark, None) not in gr
    assert NO_INDICATION in _msg(ARC_MAP)


def test_general_exposure_defeats_downstream_inference():
    """Babrauskas p.778 (Bernstein) — 전반 노출이면 전 구간 동시 아크. D-18 이 표시하고 C-58 이 그 이유로 막는다."""
    general = LOCALIZED.replace("efi:LocalizedExposure", "efi:GeneralExposure")
    gr = run(ARC_MAP + general)
    assert (EFI.pO2, EFI.arcSequenceIndeterminate, None) in gr
    assert (EFI.mkO, EFI.originIndicativeArcMark, None) not in gr
    msgs = _msg(ARC_MAP + general)
    assert BERNSTEIN in msgs and NO_INDICATION in msgs


def test_origin_indication_needs_overcurrent_protection():
    """'첫 단락에서 보호장치가 동작한다'는 전제가 없으면 최하류 추론이 서지 않는다 (§9.13.2.2, D-6)."""
    unprotected = ARC_MAP.replace("efi:overcurrentProtected true", "efi:overcurrentProtected false")
    gr = run(unprotected + LOCALIZED)
    assert (EFI.mkO, EFI.originIndicativeArcMark, None) not in gr
    assert NO_INDICATION in _msg(unprotected + LOCALIZED)


def test_unverifiable_exposure_is_not_localized():
    """확인 불가는 확인이 아니다 (P4)."""
    unv = LOCALIZED.replace("efi:Confirmed", "efi:Unverifiable")
    assert (EFI.mkO, EFI.originIndicativeArcMark, None) not in run(ARC_MAP + unv)


def test_supported_by_mark_is_not_an_origin_claim():
    """지지 근거로 쓴 단락흔은 발화지점 주장이 아니다 — originEvidence 를 들지 않으면 C-58 은 침묵한다."""
    quiet = ARC_MAP.replace("; efi:originEvidence efi:mkO", "").replace(
        "efi:hO a efi:PoorContactScenario ; efi:inSession efi:sesO ; efi:supportScore 75 .",
        "efi:hO a efi:PoorContactScenario ; efi:inSession efi:sesO ; efi:supportScore 75 ; efi:supportedBy efi:mkO .")
    assert NO_INDICATION not in _msg(quiet)



# ── 밀폐형 컴프레서 — 용기 밖 경로 (C-60, T30) ─────────────────────────────
SEALED = """
efi:invS a efi:InvestigatorAgent .
efi:sesS a efi:InvestigationSession ; efi:queryCount 2 .
efi:siteS a efi:HermeticCompressorWindingSite ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invS .
efi:sesS efi:hasFact efi:siteS .
efi:hS a efi:InterTurnShortScenario ; efi:inSession efi:sesS ; efi:supportScore 75 ; efi:supportedBy efi:siteS .
efi:cS a efi:Conclusion ; efi:concludes efi:hS .
"""
EXIT_PATH = """
efi:htS a efi:HeatTransferAssessment ; efi:assessedScenario efi:hS ; efi:confirmationStatus efi:Confirmed ;
        prov:wasAttributedTo efi:invS ; efi:enclosureExitBasis "단자 관통부 유리 절연 파손과 냉동유 유출 흔적 (현장 사진 12·14)" .
"""
NO_EXIT = "밀폐 용기 밖으로 열·가연물이 나온 경로"


def test_hermetic_compressor_conclusion_needs_exit_path():
    """C-60 — 밀폐형 권선의 층간단락 결론은 용기 밖 경로 근거가 있어야 선다. 없으면 기각이 아니라 미확정."""
    assert NO_EXIT in _msg(SEALED)
    assert NO_EXIT not in _msg(SEALED + EXIT_PATH)
    assert (EFI.hS, EFI.formed, None) in run(SEALED), "밀폐형 권선 자리도 WindingSite 하위라 가설은 선다(D-15)"


def test_plain_winding_site_is_not_asked_for_exit_path():
    """일반 권선(개방형 모터·변압기)에는 요구하지 않는다."""
    plain = SEALED.replace("efi:HermeticCompressorWindingSite", "efi:WindingSite")
    assert NO_EXIT not in _msg(plain)


def test_unverifiable_exit_path_is_not_a_path():
    """확인 불가는 확인이 아니다 (P4)."""
    unv = EXIT_PATH.replace("efi:Confirmed", "efi:Unverifiable")
    assert NO_EXIT in _msg(SEALED + unv)



# ── 연동 흐름을 처음 끝까지 돌렸을 때 드러난 두 엔진의 갈림 ─────────────────────
def test_duplicate_facts_count_once_in_both_engines():
    """같은 클래스의 사실이 둘이어도 규칙은 한 번만 센다. F-4 가 (규칙, 사실) 쌍마다 더해
    Python 과 15점씩 갈렸다 — 실제 사례 19건에 그런 중복(헐거움 13건)이 있다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, Ontology
    onto = Ontology.load()
    s = Session(case_id="D", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING)],
                facts=[Fact(cls="LooseConnection", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="LooseConnection", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    s.apply(onto)
    gr = run("""
    efi:sD a efi:InvestigationSession ; efi:queryCount 2 .
    efi:invD a efi:InvestigatorAgent .
    efi:d1 a efi:LooseConnection ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invD .
    efi:d2 a efi:LooseConnection ; efi:confirmationStatus efi:Confirmed ; prov:wasAttributedTo efi:invD .
    efi:sD efi:hasFact efi:d1 , efi:d2 .
    efi:hD a efi:PoorContactScenario ; efi:inSession efi:sD .
    """)
    py, sh = s.hypotheses[0].support_score, int(next(gr.objects(EFI.hD, EFI.supportScore)))
    assert py == sh, f"두 엔진이 갈렸다: python {py}, shacl {sh}"
    assert {q(f) for f in gr.objects(EFI.hD, EFI.supportedBy)} == {"d1", "d2"}, "F-4 가 지지 근거를 남기지 않았다"


def test_shacl_derives_supported_by_like_python():
    """결론 제약 열 개가 supportedBy 를 읽는데 아무 규칙도 만들지 않았다 — 실제 세션에서는
    전부 빈 목록을 봤다. F-4 가 Python 의 supported_by 와 같은 사실을 남겨야 한다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, Ontology
    from rdflib import Graph
    from pyshacl import validate
    onto = Ontology.load()
    s = Session(case_id="S", query_count=2,
                hypotheses=[Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)],
                facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
                       Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM),
                       Fact(cls="LooseConnection", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
    s.apply(onto)
    gr = Graph().parse(data=ontology_text() + s.to_turtle(include_derived=False), format="turtle")
    validate(gr, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    got = {q(next(gr.objects(f, RDF.type))) for f in gr.objects(EFI.S_TrackingScenario, EFI.supportedBy)}
    assert got == set(s.hypotheses[0].supported_by), f"python {sorted(set(s.hypotheses[0].supported_by))} vs shacl {sorted(got)}"



def test_query_selection_forms_hypotheses_before_scoring_them():
    """아홉이 50점 동점이면 동점 전부가 후보이고, 세워지지 않은 가설의 필요조건을 먼저 묻는다.
    전에는 목록 순서상 앞의 둘(접촉불량·압착손상)만 가르려 들어 150건에서 정답이 형성조차 안 된 것이 74건이었다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, Ontology, DEFAULT_MECHANISM
    onto = Ontology.load()
    s = Session(case_id="Q", query_count=0,
                hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                facts=[Fact(cls="ArcMeltMark", status=Status.CONFIRMED, agent=Agent.AI_VLM)])
    s.apply(onto)
    slots = s.discriminating_slots(onto)
    assert slots, "동점인데 질의 후보가 없다"
    first, target, _ = slots[0]
    need = onto.needs.get(target.value, set())
    assert any(onto.matches(first, n) or onto.matches(n, first) for n in need),         f"첫 질의 {first} 가 {target} 의 필요조건이 아니다 — 형성보다 점수를 먼저 물었다"
    targets = {t for _, t, _ in slots}
    assert len(targets) > 2, f"동점 전부가 아니라 둘만 가르려 든다: {targets}"
    assert s.prerequisite_slots(onto) == ["EnergizedState"]


def test_dialogue_policy_interleaves_forming_and_confirming():
    """형성된 가설끼리 경합 중이면 형성 질의와 변별 질의를 번갈아 낸다.

    형성만 먼저 하면 선두 확인이 굶고(8회를 미형성 가설 일곱의 필요조건에 다 쓴다),
    변별만 먼저 하면 대안을 세우지 않아 이긴 것이 섞인다. 150건에서 번갈아 묻기가
    일치 122·오판 10 으로 둘보다 낫다 — 세부는 docs/연동_흐름_실행.md.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_case as rc
    from efi_schema import Ontology
    onto, ko = Ontology.load(), rc.labels()
    case = {"case_id": "P", "actual_scenario": "TrackingScenario", "facts": [
        {"cls": "CarbonizedConductivePath", "status": "Confirmed", "agent": "AIAgent"},
        {"cls": "InterPoleInsulatingSurface", "status": "Confirmed", "agent": "InvestigatorAgent"},
        {"cls": "AgedInsulation", "status": "Confirmed", "agent": "InvestigatorAgent"},
        {"cls": "EnergizedState", "status": "Confirmed", "agent": "InvestigatorAgent"}]}
    rc.POLICY, rc.MAX_QUERIES = "interleave", 8
    s, log = rc.run(case, onto, ko)
    asked = [what.split("?")[0] for step, what, _ in log[1:] if step.startswith("질의")]
    kinds = ["형성" if "변별력 100" in what or "변별력 200" in what else "변별"
             for step, what, _ in log[1:] if step.startswith("질의")]
    assert "변별" in kinds[:3], f"형성 질의만 앞에 몰렸다: {kinds}"
    assert "형성" in kinds[:3], f"변별 질의만 앞에 몰렸다: {kinds}"
    assert rc.conclude(s, onto)[0] == "TrackingScenario", asked



# ── 이론적 연결의 정합 — TBox 안에서 끊긴 곳이 없는가 ──────────────────────────
def _definition_mechanisms(g, sc):
    from rdflib import OWL, URIRef
    from rdflib.collection import Collection
    out = set()
    for eq in g.objects(sc, OWL.equivalentClass):
        for lst in g.objects(eq, OWL.intersectionOf):
            for m in Collection(g, lst):
                if (m, OWL.onProperty, EFI.hasMechanism) in g:
                    v = g.value(m, OWL.someValuesFrom)
                    if isinstance(v, URIRef):
                        out.add(q(v))
                    else:
                        for u in g.objects(v, OWL.unionOf):
                            out |= {q(x) for x in Collection(g, u)}
    return out


def _below(g, c):
    out, st = {c}, [EFI[c]]
    while st:
        for s in g.subjects(RDFS.subClassOf, st.pop()):
            if q(s) not in out:
                out.add(q(s)); st.append(s)
    return out


def test_declared_mechanisms_are_defined(g, onto):
    """hasDeclaredMechanism 은 정의(equivalentClass)의 메커니즘 합집합 안에 있어야 한다.

    반단선 유발 단락 아크와 누설전류 발열이 선언되고 배타 공리에 있으면서 정의에서 빠져 있었다 —
    그 메커니즘을 가진 시나리오가 정의상 그 가설이 아니면서 점수·발현은 그 가설로 다루는 모순.
    """
    bad = []
    for sc in g.subjects(RDFS.subClassOf, EFI.ElectricalIgnitionScenario):
        defn = _definition_mechanisms(g, sc)
        for m in g.objects(sc, EFI.hasDeclaredMechanism):
            if q(m) not in defn and not (onto.ancestors.get(q(m), set()) & defn):
                bad.append((q(sc), q(m), sorted(defn)))
    assert not bad, f"선언이 정의 밖: {bad}"


def test_every_need_enables_a_definition_mechanism(g, onto):
    """가설의 필요조건은 그 가설의 정의 메커니즘(또는 그 하위)을 enables 해야 한다. 아니면 사슬이 끊긴 것."""
    enables = {}
    for a, m in g.subject_objects(EFI.enables):
        enables.setdefault(q(a), set()).add(q(m))
    bad = []
    for sc, need in onto.needs.items():
        mechs = set().union(*[_below(g, m) for m in _definition_mechanisms(g, EFI[sc])] or [set()])
        for n in need:
            fam = onto.ancestors.get(n, set()) | _below(g, n)
            if not any(x in mechs for c in fam for x in enables.get(c, ())):
                bad.append((sc, n))
    assert not bad, f"필요조건이 정의 메커니즘으로 이어지지 않는다: {bad}"


# 부재를 확인하는 복합 단서. 사슬(발현·원인·증언)에 붙지 않는 것이 정의다 — 외부화염의 핵심 단서로만 쓴다.
CHAIN_EXCEPTIONS = {"NoArcOrSpatter"}


def test_supporting_indicators_are_in_their_scenario_chain(g, onto):
    """핵심·지지 단서는 그 가설의 사슬 안에 있어야 한다 — 가설이 낼 수 있는 흔적(canManifest)이거나,
    정의 메커니즘을 가능케 하는 선행 조건(enables)이거나, 그런 조건을 증언하는 현장 사실(attests).
    반증 단서는 다른 가설의 흔적으로 반박하므로 사슬 밖이 정상이다."""
    enables, manifest, attests = {}, {}, {}
    for a, m in g.subject_objects(EFI.enables): enables.setdefault(q(a), set()).add(q(m))
    for s, d in g.subject_objects(EFI.canManifest): manifest.setdefault(q(s), set()).add(q(d))
    for s, d in g.subject_objects(EFI.attests): attests.setdefault(q(s), set()).add(q(d))
    fam = lambda c: onto.ancestors.get(c, set()) | _below(g, c)
    loose = []
    for r in onto.rules:
        sc = r.scenario if isinstance(r.scenario, str) else r.scenario.value
        if sc == "ElectricalIgnitionScenario" or r.role.value not in ("Core", "Supporting") or r.indicator in CHAIN_EXCEPTIONS:
            continue
        mechs = set().union(*[_below(g, m) for m in _definition_mechanisms(g, EFI[sc])] or [set()])
        shown = set().union(*[_below(g, d) for d in manifest.get(sc, ())] or [set()])
        causes = lambda c: any(x in mechs for c2 in fam(c) for x in enables.get(c2, ()))
        ok = bool(fam(r.indicator) & shown) or causes(r.indicator) \
            or any(causes(t) or (fam(t) & shown) for c in fam(r.indicator) for t in attests.get(c, ()))
        if not ok:
            loose.append((r.id, sc, r.indicator))
    assert not loose, f"사슬 밖 지지 단서: {loose}"


def test_no_dangling_references(g):
    """SPARQL 문자열·sh:path·sh:class·domain·range·사슬이 가리키는 efi: 이름은 전부 선언돼 있어야 한다.
    오타 하나면 그 규칙은 조용히 영원히 발동하지 않는다. 파서도 다른 시험도 잡지 않는다."""
    from rdflib import URIRef
    SH = Namespace("http://www.w3.org/ns/shacl#")
    declared = {q(s) for s in g.subjects(RDF.type, None) if isinstance(s, URIRef) and str(s).startswith(str(EFI))}
    declared |= {q(s) for s in g.subjects(RDFS.subClassOf, None) if isinstance(s, URIRef) and str(s).startswith(str(EFI))}
    bad = set()
    for pred in (SH.select, SH.construct):
        for _, text in g.subject_objects(pred):
            bad |= {n for n in re.findall(r"\befi:([A-Za-z_]\w*)", str(text)) if n not in declared}
    for p in (SH.path, SH["class"], SH.targetClass, RDFS.domain, RDFS.range, SH.targetObjectsOf, SH.targetSubjectsOf,
              EFI.indicates, EFI.forScenario, EFI.canManifest, EFI.enables, EFI.producesDamage, EFI.ignites,
              EFI.attests, EFI.exhibits, EFI.hasDeclaredMechanism):
        for _, o in g.subject_objects(p):
            if isinstance(o, URIRef) and str(o).startswith(str(EFI)) and q(o) not in declared:
                bad.add(q(o))
    assert not bad, f"선언되지 않은 이름을 가리킨다: {sorted(bad)}"


def test_python_enums_exist_in_ttl(g):
    """파이썬 열거형의 값은 전부 TTL 에 있어야 한다. 갈리면 사례 평가가 새 어휘를 통째로 거부한다."""
    from rdflib import URIRef
    from efi_schema import Scenario, Mechanism, Antecedent, Damage, SceneEvidence, Fuel
    names = {q(s) for s in g.subjects(None, None) if isinstance(s, URIRef)}
    missing = [(e.__name__, v.value) for e in (Scenario, Mechanism, Antecedent, Damage, SceneEvidence, Fuel) for v in e if v.value not in names]
    assert not missing, missing



def test_arc_site_corroboration_is_a_warning_not_a_bar():
    """C-61 — 발화지점 근거 단락흔의 지점에 대응 손상 확인이 없으면 권고한다. D-4 가 둘 이상을 세우면 침묵.
    원문(§9.13.4.2)이 '확률이 오른다'는 서술이라 위반이 아니라 권고다."""
    corroborate = "대응 손상이 둘 이상 확인되지 않았다"
    assert corroborate in _msg(ARC_MAP + LOCALIZED)
    two = ARC_MAP + LOCALIZED + """
    efi:cdA a efi:CorrespondingDamageArea . efi:cdB a efi:CorrespondingDamageArea .
    efi:pO2 efi:hasCorrespondingDamage efi:cdA , efi:cdB .
    """
    gr = run(two)
    assert (EFI.pO2, EFI.trueArcSiteLikely, None) in gr, "D-4 가 발동하지 않았다"
    assert corroborate not in _msg(two)
    one = ARC_MAP + LOCALIZED + "efi:cdA a efi:CorrespondingDamageArea . efi:pO2 efi:hasCorrespondingDamage efi:cdA ."
    assert corroborate in _msg(one), "하나로는 확률이 오르지 않는다 (둘 이상)"



def test_foreign_conductor_intrusion_matches_in_both_engines(onto):
    """D-19 — 원인미상 + 단락흔 + 통전 + 기기 내 도전물 혼입 확인이면 국내 분류 '이물 혼입'. 두 엔진이 같아야 한다.
    가설이 아니라 분류다 — 혼입이 확인돼도 어떤 가설도 서거나 점수를 받지 않는다. 확인 불가는 확인이 아니다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, DEFAULT_MECHANISM
    def sess(facts, status=Status.CONFIRMED):
        s = Session(case_id="FC", query_count=2,
                    hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                    facts=[Fact(cls=c, status=(status if c == "ForeignConductorInEquipment" else Status.CONFIRMED),
                                agent=Agent.INVESTIGATOR) for c in facts])
        return s.apply(onto)
    s = sess(["ArcMeltMark", "EnergizedState", "ForeignConductorInEquipment"])
    assert s.outcome(onto) == "ForeignConductorIntrusion"
    assert all(h.support_score <= 50 for h in s.hypotheses), "혼입이 어떤 가설에 점수를 줬다"
    assert not any(h.formed for h in s.hypotheses if h.scenario is not Scenario.EXTERNAL_FLAME), "혼입이 가설을 세웠다"
    gr = run(s.to_turtle(include_derived=False))
    assert (EFI.session_FC, EFI.outcomeForeignConductorIntrusion, None) in gr
    assert (EFI.session_FC, EFI.outcomeUnidentifiedShortCircuit, None) in gr, "이물 혼입은 미확인 단락 안의 분류다"
    s = sess(["ArcMeltMark", "EnergizedState"])
    assert s.outcome(onto) == "UnidentifiedShortCircuit"
    assert (EFI.session_FC, EFI.outcomeForeignConductorIntrusion, None) not in run(s.to_turtle(include_derived=False))
    s = sess(["ArcMeltMark", "EnergizedState", "ForeignConductorInEquipment"], status=Status.UNVERIFIABLE)
    assert s.outcome(onto) == "UnidentifiedShortCircuit", "확인 불가 혼입을 확인으로 읽었다"
    assert (EFI.session_FC, EFI.outcomeForeignConductorIntrusion, None) not in run(s.to_turtle(include_derived=False))



def test_liquid_ingress_forms_tracking_but_metal_object_forms_nothing(onto):
    """표 2-1 '이물 혼입'의 세 갈래 — 도전성 액체는 트래킹으로 가고(오염 환경의 하위), 금속 물체는 즉시 단락이라
    어떤 가설도 세우지 않는다. 물체를 트래킹에 이으면 오염 환경 없이 트래킹이 서서 C-5 가 뒤집힌다."""
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, DEFAULT_MECHANISM
    def one(cls):
        s = Session(case_id="IN", query_count=2,
                    hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()],
                    facts=[Fact(cls=cls, status=Status.CONFIRMED, agent=Agent.INVESTIGATOR)])
        s.apply(onto)
        return {h.scenario: h for h in s.hypotheses}
    liquid = one("ConductiveLiquidIngress")
    assert liquid[Scenario.TRACKING].formed and liquid[Scenario.TRACKING].support_score > 50, "도전성 액체가 트래킹을 세우지 않는다"
    metal = one("ForeignConductorInEquipment")
    assert not metal[Scenario.TRACKING].formed and metal[Scenario.TRACKING].support_score == 50, "금속 물체가 트래킹을 세웠다"
    assert all(h.support_score == 50 for h in metal.values()), "금속 물체가 어떤 가설에 점수를 줬다"


# ── §19.8.2 보고용 원인 분류 (T20) ─────────────────────────────────────
def test_every_electrical_scenario_reports_to_one_korean_category(g):
    """T20 — 전기 가설 여덟은 화재조사 및 보고규정 세부분류의 항목 하나에 대응한다. 외부화염은 전기적 요인이
    아니라 대응이 없다. 항목은 채택 체계(KoreaFireReportClassification)의 것이어야 한다."""
    from rdflib.namespace import SKOS, DCTERMS
    sys.path.insert(0, str(ROOT / "scripts"))
    import score
    for sc in score._scenarios():
        cats = list(g.objects(EFI[sc], EFI.reportedAs))
        if sc == "ExternalFlameScenario":
            assert not cats, "외부화염이 전기적 요인 항목에 대응됐다"
            continue
        assert len(cats) == 1, f"{sc}: 대응 항목 {len(cats)}개"
        scheme = g.value(cats[0], SKOS.inScheme)
        assert (scheme, DCTERMS.isPartOf, EFI.KoreaFireReportClassification) in g, f"{sc}: 채택 체계 밖의 항목"


def test_conclusion_derives_report_classification():
    """D-20 — 결론이 서면 보고용 분류 개체가 판정 뒤에 만들어지고 C-9·C-10·C-62 를 통과한다.
    결론이 외부화염이면 만들지 않는다. 분류가 결론에 범주를 직접 달지 않는다(C-11)."""
    from rdflib.namespace import SKOS
    gr = run("""
    efi:hT a efi:TrackingScenario ; efi:supportScore 75 .
    efi:cT a efi:Conclusion ; efi:concludes efi:hT .
    """)
    k = gr.value(None, EFI.classifiesCause, EFI.cT)
    assert k is not None, "결론에서 분류 개체가 나오지 않았다"
    assert (k, EFI.usesClassificationSystem, EFI.KoreaFireReportClassification) in gr
    assert str(gr.value(k, EFI.classificationCategory)) == "트래킹에 의한 단락"
    assert (EFI.cT, EFI.classificationCategory, None) not in gr, "결론에 범주가 직접 붙었다 (C-11)"
    assert "분류" not in _msg("""
    efi:hT a efi:TrackingScenario ; efi:supportScore 75 .
    efi:cT a efi:Conclusion ; efi:concludes efi:hT .
    """)
    gr = run("""
    efi:hX a efi:ExternalFlameScenario ; efi:supportScore 75 .
    efi:cX a efi:Conclusion ; efi:concludes efi:hX .
    """)
    assert gr.value(None, EFI.classifiesCause, EFI.cX) is None, "외부화염 결론에 전기 분류가 붙었다"


def test_report_category_must_belong_to_declared_system():
    """C-62 — 항목은 분류가 밝힌 체계의 것이어야 한다. 다른 체계의 항목을 빌리면 라벨만 같고 뜻이 다르다."""
    assert "체계의 것이 아니다" in _msg("""
    efi:hN a efi:TrackingScenario ; efi:supportScore 75 .
    efi:cN a efi:Conclusion ; efi:concludes efi:hN .
    efi:kN a efi:FireCauseClassification ; efi:classifiesCause efi:cN ;
           efi:usesClassificationSystem efi:NFIRS ; efi:hasReportCategory kfc:Factor-Electrical-07 ;
           efi:classificationCategory "트래킹에 의한 단락" .
    """)


def test_report_categories_carry_manual_codes_one_to_ten(g):
    """T20 — 채택 체계의 열 항목은 국가화재분류체계 매뉴얼(2019) p.37 의 코드 1~10 을 하나씩, 중복 없이 갖는다."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS
    KFC = Namespace("https://w3id.org/efi-onto/kfc#")
    cats = list(g.subjects(SKOS.broader, KFC["Factor-Electrical"]))
    codes = sorted(int(g.value(c, SKOS.notation)) for c in cats)
    assert codes == list(range(1, 11)), codes
    assert str(g.value(KFC["Factor-Electrical-02"], SKOS.prefLabel)) == "접촉불량에 의한 단락", "접촉불량은 2 다 — 제2편 예시의 5 는 오식"
    assert str(g.value(KFC["Factor-Electrical-09"], SKOS.prefLabel)) == "미확인 단락"


def test_classification_layer_is_reference_only():
    """efi_classification.ttl 은 공식 분류표(SKOS)만 담는다 — 도형·규칙·efi: 어휘 선언이 없어야 한다.
    판정 어휘와 섞이면 보고 분류가 판정에 스며든다. 발화요인은 대분류 11·소분류 43 이다(매뉴얼 p.33~51 + 별지 4)."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS
    g = Graph().parse(ROOT / "ontology" / "efi_classification.ttl", format="turtle")
    KFC = Namespace("https://w3id.org/efi-onto/kfc#")
    SH = Namespace("http://www.w3.org/ns/shacl#")
    assert not list(g.subjects(RDF.type, SH.NodeShape)), "분류 층에 도형이 있다"
    assert not [s for s in g.subjects(RDF.type, None) if str(s).startswith(str(EFI))], "분류 층이 efi: 어휘를 선언한다"
    tops = list(g.subjects(SKOS.topConceptOf, KFC.Factor))
    leaves = [s for s in g.subjects(SKOS.inScheme, KFC.Factor) if (s, SKOS.broader, None) in g]
    assert len(tops) == 11 and len(leaves) == 43, (len(tops), len(leaves))
    for s in g.subjects(SKOS.inScheme, KFC.Factor):
        assert (s, SKOS.prefLabel, None) in g and (s, DCTERMS_source(), None) in g, s
    # 같은 대분류 안에서 코드는 하나씩
    for top in tops:
        codes = [str(g.value(c, SKOS.notation)) for c in g.subjects(SKOS.broader, top)]
        assert len(codes) == len(set(codes)), top


def DCTERMS_source():
    from rdflib.namespace import DCTERMS
    return DCTERMS.source


def test_every_electrical_mechanism_has_a_heat_source_match(g):
    """K2 — 잎 메커니즘마다 발화열원 짝이 있다. 아크 계열은 작동기기-01 과 정확히 같고, 저항 발열 계열은
    01·03 에 '관련 있다'로 걸린다(매뉴얼에 저항 발열 소분류가 없다). 외부화염 수열은 짝이 없다. 정확·관련을 둘 다 갖지 않는다."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS, OWL
    KFC = Namespace("https://w3id.org/efi-onto/kfc#")
    leaves = [m for m in g.subjects(RDF.type, OWL.Class)
              if (m, RDFS.subClassOf * "+", EFI.ElectricalHeatingMechanism) in g and not list(g.subjects(RDFS.subClassOf, m))]
    assert leaves, "잎 메커니즘이 없다"
    def inherited(m, p):
        fam = [m] + [a for a in g.transitive_objects(m, RDFS.subClassOf) if a != m]
        for c in fam:
            v = list(g.objects(c, p))
            if v:
                return v
        return []
    for m in leaves:
        exact = inherited(m, EFI.mappedHeatSourceExact); rel = inherited(m, EFI.mappedHeatSourceRelated)
        assert bool(exact) != bool(rel), f"{q(m)}: 정확 {len(exact)} 관련 {len(rel)}"
        for c in exact + rel:
            assert (c, SKOS.inScheme, KFC.HeatSource) in g, f"{q(m)} → {c}: 발화열원 축 밖"
        if exact:
            assert exact == [KFC["HeatSource-OperatingEquipment-01"]], q(m)
    assert not list(g.objects(EFI.ExternalFlameExposure, EFI.mappedHeatSourceExact | EFI.mappedHeatSourceRelated))
    leaves26 = [s for s in g.subjects(SKOS.inScheme, KFC.HeatSource) if (s, SKOS.broader, None) in g]
    assert len(leaves26) == 26 and len(list(g.subjects(SKOS.topConceptOf, KFC.HeatSource))) == 9


def test_every_first_fuel_class_has_a_first_item_match(g):
    """K3 — 잎 착화물마다 최초착화물 짝이 있다(상속 포함). 정확히 같은 것은 둘(피복재→전선피복, 분진→분진)이고 나머지는
    '넓게 포함된다'다. 대분류 11·소분류 89 — 다른 문서의 57 은 오류."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS
    KFC = Namespace("https://w3id.org/efi-onto/kfc#")
    leaves = [c for c in g.transitive_subjects(RDFS.subClassOf, EFI.FirstFuelIgnited)
              if c != EFI.FirstFuelIgnited and not list(g.subjects(RDFS.subClassOf, c))]
    assert leaves
    def inherited(m, p):
        for c in [m] + [a for a in g.transitive_objects(m, RDFS.subClassOf) if a != m]:
            v = list(g.objects(c, p))
            if v:
                return v
        return []
    exact_owners = set()
    for f in leaves:
        exact = inherited(f, EFI.mappedFirstItemExact); broad = inherited(f, EFI.mappedFirstItemBroad)
        assert exact or broad, q(f)
        for c in exact + broad:
            assert (c, SKOS.inScheme, KFC.FirstItem) in g, f"{q(f)} → {c}"
        if exact:
            exact_owners.add(q(f))
    assert exact_owners == {"InsulationMaterialFuel", "AccumulatedDustFuel"}, exact_owners
    leaves89 = [s for s in g.subjects(SKOS.inScheme, KFC.FirstItem) if (s, SKOS.broader, None) in g]
    assert len(leaves89) == 89 and len(list(g.subjects(SKOS.topConceptOf, KFC.FirstItem))) == 11
