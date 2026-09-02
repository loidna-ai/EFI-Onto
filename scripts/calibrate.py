# -*- coding: utf-8 -*-
"""유도한 가감점을 사례로 검증한다. 대체하는 것이 아니다.

무엇을 묻는가
  scripts/score.py 는 가중치를 구조에서 유도한다 — 6개 가설 중 k개와 양립하는
  단서는 log2(6/k)/log2(6) 만큼 좁힌다. 이때 k 는 '가능한가'를 센다.

  사례 150건은 다른 것을 안다 — '실제로 어느 요인에서 나오는가'. 같은 공식에
  k 대신 유효 가설 수 k̂ 를 넣으면 두 값을 같은 자에 놓고 볼 수 있다.

    k̂ = 2^H,  H = 조건부 분포 P(요인 | 단서 확인)의 엔트로피
  단서가 한 요인에만 나오면 k̂=1, 다섯에 고르게 나오면 k̂=5.

왜 대체하지 않는가
  · 라벨이 조사관 판정이다. 정답이 아니라 사람의 판단이고, 이 프로젝트는
    사람의 판단을 가중치 원천으로 쓰지 않기로 했다.
  · 5요인 30건씩 균등 표집이다. 실제 발생 분포가 아니다.
  · 150건은 조건부 확률을 재기에 적다. 단서 대부분이 한 자릿수로 나온다.

  그러므로 이 파일은 순위가 어긋나는 지점을 찾는 데 쓴다. 어긋나면 둘 중
  하나가 틀린 것이고, 사슬을 다시 보는 것이 먼저다 — 실제로 그렇게 여섯 건을
  고쳤다.
"""
import sys, json, math, pathlib, collections
from rdflib import Graph

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import score

KO = {"PoorContactScenario": "접촉불량", "CrushDamageScenario": "기계손상",
      "PartialDisconnectionScenario": "반단선", "InsulationDegradationScenario": "절연열화",
      "TrackingScenario": "트래킹", "ExternalFlameScenario": "외부화염",
      "OverloadScenario": "과부하", "GroundFaultScenario": "누전지락", "InterTurnShortScenario": "층간단락"}


def empirical(onto, sessions):
    """지표 → (확인 건수, 조건부 분포). subsumption 을 반영해 센다."""
    out = {}
    inds = {r.indicator for r in onto.rules}
    for i in inds:
        d = collections.Counter(
            s["actual_scenario"] for s in sessions
            if any(onto.matches(f["cls"], i) and f["status"] == "Confirmed" for f in s["facts"]))
        if d:
            out[i] = (sum(d.values()), d)
    return out


def eff_count(dist):
    """유효 가설 수 k̂ = 2^H. 한 요인에만 나오면 1."""
    n = sum(dist.values())
    h = -sum((v / n) * math.log2(v / n) for v in dist.values() if v)
    return 2 ** h


def weight(k, morph):
    w = score.SUPPORT_MAX * math.log2(score.N / k) / math.log2(score.N)
    return int(round(w * (score.MORPHOLOGY_FACTOR if morph else 1.0)))


if __name__ == "__main__":
    from efi_schema import Ontology
    g = Graph().parse(ROOT / "ontology" / "efi_tbox.ttl", format="turtle")
    onto = Ontology.load(str(ROOT / "ontology" / "efi_tbox.ttl"))
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))
    emp = empirical(onto, sessions)
    comp = score.compatibility(g)

    rows = []
    for r in onto.rules:
        if r.role.value not in ("Core", "Supporting") or r.indicator not in emp:
            continue
        n, dist = emp[r.indicator]
        k = max(1, len(comp.get(r.indicator, set())))
        kh = eff_count(dist)
        morph = onto.is_damage(r.indicator)
        rows.append((r.indicator, KO.get(r.scenario, r.scenario), n, k, kh,
                     weight(k, morph), weight(max(1.0, kh), morph),
                     dist.most_common(1)[0]))
    rows.sort(key=lambda x: -abs(x[5] - x[6]))

    print(f"규칙이 쓰는 지표 중 사례에 나타난 것 {len(rows)}개\n")
    print(f"{'지표':30s}{'가설':8s}{'건수':>4s}{'k':>4s}{'k̂':>6s}{'유도':>5s}{'실측':>5s}{'차':>5s}  최다")
    for i, sc, n, k, kh, wd, we, top in rows:
        print(f"{i[:28]:30s}{sc:8s}{n:4d}{k:4d}{kh:6.1f}{wd:5d}{we:5d}{we-wd:+5d}  "
              f"{KO.get(top[0],'?')} {top[1]}/{n}")

    gap = [r for r in rows if abs(r[5] - r[6]) >= 5]
    print(f"\n5점 이상 어긋난 지표 {len(gap)}/{len(rows)}개")
    over = [r for r in rows if r[5] - r[6] >= 5]
    under = [r for r in rows if r[6] - r[5] >= 5]
    print(f"  유도가 높게 본 것 {len(over)}개 — 사슬이 좁게 적혀 있을 수 있다")
    for r in over:
        print(f"     {r[0]:30s} 유도 {r[5]:2d} vs 실측 {r[6]:2d}  ({r[7][1]}/{r[2]} {KO.get(r[7][0],'?')})")
    print(f"  유도가 낮게 본 것 {len(under)}개 — 사슬이 넓게 적혀 있을 수 있다")
    for r in under:
        print(f"     {r[0]:30s} 유도 {r[5]:2d} vs 실측 {r[6]:2d}  ({r[7][1]}/{r[2]} {KO.get(r[7][0],'?')})")
