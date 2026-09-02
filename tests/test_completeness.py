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
             "InsulationDegradationScenario", "TrackingScenario", "ExternalFlameScenario",
             "OverloadScenario", "GroundFaultScenario", "InterTurnShortScenario"]

# 왼쪽이 현재 허용 한계, 오른쪽이 도달 목표.
BASELINE = {}
# 비었다 — 세던 미완성이 전부 닫혔다. 새 항목이 생기면 여기 적는다.
# 이관 완료: arc_sequence_rules(0→3), role_rank_mismatch(4→0),
#           morphological_core_rules(1→0), unreviewed_fire_producibility(8→0),
#           unreviewed_cause_exclusivity(11→0), min_refuting_per_scenario(1→2),
#           unwired_data_properties(23→0), dangling_vocabulary(23→0).
#           모두 test_ontology.py 의 불변식이 됐다.


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
    # 붙일 근거가 원문에 없다고 확인된 것은 lint 가 따로 관리한다. 임계값을
    # 지어내 넣지 않기로 한 결정이며 그것을 미완성으로 세면 결정이 지워진다.
    sys.path.insert(0, str(ROOT / "scripts"))
    import lint
    out = [x for x in out if x not in lint.NO_CRITERION]
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
