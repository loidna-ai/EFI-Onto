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
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
EFI = Namespace("https://w3id.org/efi-onto#")
q = lambda u: str(u).split("#")[-1]

# 자리표시자 점수. 실제 루브릭 값으로 교체되면 이 집합에서 벗어난다.
PLACEHOLDER_DELTAS = {15, 8, -25}

SCENARIOS = ["PoorContactScenario", "CrushDamageScenario", "PartialDisconnectionScenario",
             "InsulationDegradationScenario", "TrackingScenario", "ExternalFlameScenario"]

# 2026-08-31 측정값. 왼쪽이 현재 허용 한계, 오른쪽이 도달 목표.
BASELINE = {
    "placeholder_delta_rules":  (21, 0),    # 자리표시자 점수를 쓰는 규칙 수
    "min_refuting_per_scenario": (1, 2),    # 시나리오당 반증 규칙 최소 개수
    "unwired_data_properties":  (23, 0),    # 선언만 되고 아무데서도 안 쓰이는 데이터 속성
    "arc_sequence_rules":        (0, 1),    # 1차/2차 아크흔을 지목하는 규칙 수
    "morphological_core_rules":  (1, 0),    # core 단서가 형태학적 특징인 규칙 수
}


@pytest.fixture(scope="module")
def g():
    return Graph().parse(TTL, format="turtle")


def _rules(g):
    for r in g.subjects(RDF.type, EFI.IndicatorRule):
        yield (q(g.value(r, EFI.forScenario)), q(g.value(r, EFI.hasRole)),
               q(g.value(r, EFI.indicates)), int(g.value(r, EFI.scoreDelta)))


def _ancestors(g, c, seen=None):
    seen = set() if seen is None else seen
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, URIRef) and p not in seen:
            seen.add(p)
            _ancestors(g, p, seen)
    return {q(x) for x in seen}


def _is_damage(g, name):
    return "DamagePattern" in _ancestors(g, EFI[name])


# ── 지표 산출 ─────────────────────────────────────────────────────────────
def placeholder_delta_rules(g):
    return sum(1 for _, role, _, d in _rules(g)
               if role != "DecisiveRefuting" and d in PLACEHOLDER_DELTAS)


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


def arc_sequence_rules(g):
    """F-2 는 1차/2차 아크흔을 시간 선후로 가른다. 그 판정을 실제로 쓰는 규칙."""
    return [ind for _, _, ind, _ in _rules(g)
            if ind in ("PrimaryArcMark", "SecondaryArcMark")]


def morphological_core_rules(g):
    """core 단서가 형태학적 특징이면 사진만으로 가설이 성립한다. P1·C-5 와 충돌한다."""
    return [(sc, ind) for sc, role, ind, _ in _rules(g)
            if role == "Core" and _is_damage(g, ind)]


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


def test_score_delta_is_still_placeholder(g):
    """A-1 점수가 자리표시자다. 6개 시나리오가 15/8/-25 로 균일해
    supportScore 가 확인 항목 개수의 카운터 노릇밖에 못 한다."""
    _ratchet("placeholder_delta_rules", placeholder_delta_rules(g))


def test_refutation_rules_are_thin(g):
    """A-2 반증 우선(P3)을 선언했으나 가설당 반증 수단이 하나뿐이다."""
    _ratchet("min_refuting_per_scenario", min_refuting_per_scenario(g), better_is_lower=False)


def test_data_properties_are_wired(g):
    """A-3 측정값을 담을 그릇만 있고 판정에 쓰이지 않는다.
    공극률·결정립을 '보강 근거로 쓴다'고 했으나 어떤 규칙에도 붙어 있지 않다."""
    un = unwired_data_properties(g)
    _ratchet("unwired_data_properties", len(un))


def test_arc_mark_sequence_reaches_rules(g):
    """A-4 1·2차 단락흔을 시간 선후로 판정한다는 원칙이 규칙 층에 도달하지 않았다."""
    _ratchet("arc_sequence_rules", len(arc_sequence_rules(g)), better_is_lower=False)


def test_core_indicators_are_not_morphology(g):
    """A-5 core 가 형태면 사진만으로 가설이 선다."""
    _ratchet("morphological_core_rules", len(morphological_core_rules(g)))


if __name__ == "__main__":
    gr = Graph().parse(TTL, format="turtle")
    rows = [
        ("자리표시자 점수 규칙", placeholder_delta_rules(gr), "placeholder_delta_rules"),
        ("시나리오당 최소 반증 규칙", min_refuting_per_scenario(gr), "min_refuting_per_scenario"),
        ("미연결 데이터 속성", len(unwired_data_properties(gr)), "unwired_data_properties"),
        ("아크흔 선후 판정 규칙", len(arc_sequence_rules(gr)), "arc_sequence_rules"),
        ("형태학적 core 규칙", len(morphological_core_rules(gr)), "morphological_core_rules"),
    ]
    print(f"{'지표':26s} {'현재':>6s} {'한계':>6s} {'목표':>6s}")
    for label, now, key in rows:
        limit, target = BASELINE[key]
        print(f"{label:26s} {now:6d} {limit:6d} {target:6d}")
    print("\n미연결 데이터 속성:", ", ".join(unwired_data_properties(gr)))
    print("형태학적 core:", morphological_core_rules(gr))
