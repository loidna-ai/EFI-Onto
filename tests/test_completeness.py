# -*- coding: utf-8 -*-
"""TBox 완성도 래칫. 미완성 부분을 수치로 고정한다.

test_ontology.py 가 '정합성이 깨졌는가'를 묻는다면 이 파일은 '얼마나 남았는가'를 묻는다.
전부 통과하는 것이 정상 상태다. 실패하면 둘 중 하나다.
  · 나빠졌다  → TTL 수정이 미완성 영역을 늘렸다. 되돌린다.
  · 좋아졌다  → BASELINE 을 측정값으로 조인다. 되돌아가지 못하게 못을 박는다.

TARGET 에 도달하면 그 항목은 test_ontology.py 로 옮기고 여기서 지운다.
"""
import sys, pathlib, warnings, collections
import pytest
from rdflib import Graph, Namespace, RDF, OWL

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
EFI = Namespace("https://w3id.org/efi-onto#")
q = lambda u: str(u).split("#")[-1]

SCENARIOS = ["PoorContactScenario", "CrushDamageScenario", "PartialDisconnectionScenario",
             "InsulationDegradationScenario", "TrackingScenario", "ExternalFlameScenario"]

# 왼쪽이 현재 허용 한계, 오른쪽이 도달 목표.
BASELINE = {
    "min_refuting_per_scenario": (1, 2),    # 시나리오당 반증 규칙 최소 개수
    # 23 → 18 → 13 → 12. 남은 12개는 임계값·설계 결정이 있어야 풀린다.
    # 그중 5개는 임계값이 존재하지 않는 것이 확인됐다(기공률 등). 목표 0 은
    # 도달하지 못할 수 있다 — 확인되면 그때 목표를 고친다.
    "unwired_data_properties":  (12, 0),    # 선언만 되고 아무데서도 안 쓰이는 데이터 속성
    # 화재 자체가 낼 수 있는지 원문 근거로 판정되지 않은 손상 양상.
    # 판정되지 않은 채로 전용 단서 노릇을 하면 변별력이 과대평가된다.
    # 8 → 7 → 1. 원문 근거로 판정 가능한 것은 모두 판정했다.
    # 남은 1건(BurnCenterOnSurface)은 화재가 같은 양상을 못 낸다는 근거를 찾지 못했다.
    # 지어내지 않고 검토표 7번 시트로 조사관에게 보냈다.
    "unreviewed_fire_producibility": (1, 0),
    # 사슬에 붙지 않은 어휘. 선언만 하고 쓰지 않으면 판정에 기여하지 못한다.
    # 확장 슬롯 3건과 미사용 속성 15건. scripts/lint.py 참조.
    "dangling_vocabulary": (18, 0),
}
# 이관 완료: arc_sequence_rules(0→3), role_rank_mismatch(4→0),
#           morphological_core_rules(1→0). 모두 test_ontology.py 의 불변식이 됐다.


@pytest.fixture(scope="module")
def g():
    return Graph().parse(TTL, format="turtle")


def _rules(g):
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        yield (q(g.value(r, EFI.forScenario)), q(g.value(r, EFI.hasRole)),
               q(g.value(r, EFI.indicates)), int(g.value(r, EFI.scoreDelta)))


# ── 지표 산출 ─────────────────────────────────────────────────────────────
def unreviewed_fire_producibility(g):
    """'화재 자체가 이 흔적을 낼 수 있는가'에 원문 근거로 답하지 않은 양상."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
    import audit
    return audit.unreviewed(g)


def dangling_vocabulary(g):
    """사슬에 붙지 않은 어휘. 어휘만 있고 절차가 없는 것은 이 프로젝트의 반복된 실패다."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
    import lint
    return [i for _, items, _ in lint.problems(g) for i in items]


def min_refuting_per_scenario(g):
    """결정적 반증(비통전)은 제외한다. 전기 가설 전체에 걸리는 단일 규칙이라
    시나리오별 반증 수단을 갖췄다는 근거가 되지 못한다."""
    cnt = collections.Counter()
    for sc, role, _, _ in _rules(g):
        if role == "Refuting":
            cnt[sc] += 1
    return min(cnt[s] for s in SCENARIOS)


def unwired_data_properties(g):
    """선언 줄 바깥에서 한 번도 참조되지 않는 데이터 속성.
    클래스 정의·규칙·SHACL 어디에도 연결되지 않아 판정에 기여할 수 없다."""
    import re
    lines = TTL.read_text(encoding="utf-8").split("\n")
    out = []
    for p in sorted(q(s) for s in g.subjects(RDF.type, OWL.DatatypeProperty)):
        used = any(re.search(rf"\befi:{p}\b", l) and not re.match(rf"\s*efi:{p}\s+a\s+owl:", l)
                   for l in lines)
        if not used:
            out.append(p)
    return out


# ── 래칫 ──────────────────────────────────────────────────────────────────
def _ratchet(key, now, better_is_lower=True):
    limit, target = BASELINE[key]
    if now == target:
        warnings.warn(f"[달성] {key}: {now} — test_ontology.py 로 옮기고 여기서 지울 것")
        return
    improved = now < limit if better_is_lower else now > limit
    if improved:
        pytest.fail(f"{key} 가 개선됐다 ({limit} → {now}). "
                    f"BASELINE 을 {now} 로 조여서 되돌아가지 못하게 할 것. 목표 {target}")
    worse = now > limit if better_is_lower else now < limit
    assert not worse, f"{key} 가 나빠졌다 ({limit} → {now}). 목표 {target}"
    warnings.warn(f"[잔여] {key}: {now} (목표 {target})")


def test_refutation_rules_are_thin(g):
    """A-2 반증 우선(P3)을 선언했으나 가설당 반증 수단이 하나뿐이다."""
    _ratchet("min_refuting_per_scenario", min_refuting_per_scenario(g), better_is_lower=False)


def test_fire_producibility_is_reviewed(g):
    """원문 근거로 판정되지 않은 양상이 남아 있다. 판정되지 않은 채 전용 단서
    노릇을 하면 변별력이 과대평가된다 — 이미 다섯 건이 그랬다."""
    _ratchet("unreviewed_fire_producibility", len(unreviewed_fire_producibility(g)))


def test_vocabulary_is_wired(g):
    """선언만 하고 사슬에 붙이지 않은 어휘가 남아 있다. ArcMapPoint 가 그랬고
    downstreamIndex 가 그랬다 — 어휘만 있고 절차가 없으면 판정에 기여하지 못한다."""
    _ratchet("dangling_vocabulary", len(dangling_vocabulary(g)))


def test_data_properties_are_wired(g):
    """A-3 측정값을 담을 그릇만 있고 판정에 쓰이지 않는다.
    공극률·결정립을 '보강 근거로 쓴다'고 했으나 어떤 규칙에도 붙어 있지 않다."""
    un = unwired_data_properties(g)
    _ratchet("unwired_data_properties", len(un))


if __name__ == "__main__":
    gr = Graph().parse(TTL, format="turtle")
    rows = [
        ("시나리오당 최소 반증 규칙", min_refuting_per_scenario(gr), "min_refuting_per_scenario"),
        ("미연결 데이터 속성", len(unwired_data_properties(gr)), "unwired_data_properties"),
        ("화재 생성 가능성 미검토", len(unreviewed_fire_producibility(gr)), "unreviewed_fire_producibility"),
        ("사슬에 안 붙은 어휘", len(dangling_vocabulary(gr)), "dangling_vocabulary"),
    ]
    print(f"{'지표':26s} {'현재':>6s} {'한계':>6s} {'목표':>6s}")
    for label, now, key in rows:
        limit, target = BASELINE[key]
        print(f"{label:26s} {now:6d} {limit:6d} {target:6d}")
    print("\n미연결 데이터 속성:", ", ".join(unwired_data_properties(gr)))
