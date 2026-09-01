# -*- coding: utf-8 -*-
"""사례를 돌려 정확도를 잰다. 이 프로젝트에서 처음 재는 정확도다.

지금까지 잰 것은 전부 이식률이었다 — 이론을 얼마나 옮겼는가. 이 파일은 다른
것을 묻는다. 옮긴 것이 실제로 맞히는가.

판정 방식
  6개 가설을 전부 세우고 사실을 넣어 점수를 매긴다. 기각되지 않은 것 중
  최고점이 판정이다. 최고점이 동점이면 원인미상으로 둔다 — §19.6.5.1 이
  둘 이상이 기각되지 않으면 원인미상이라고 한다. 억지로 하나를 고르면
  이론을 어기면서 정확도를 부풀리는 것이 된다.

한계 (숫자를 읽을 때 함께 읽을 것)
  외부화염 사례가 0건이다. 6개 중 5개만 나온다.
  절연저항 슬롯이 0건이라 트래킹 반증 규칙은 발동하지 않는다.
  조사관 최초 판단이 없어 사람과 비교할 수 없다.
"""
import json, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TTL = ROOT / "ontology" / "efi_tbox.ttl"

MECH = {
    "PoorContactScenario": "PoorContactHeating",
    "CrushDamageScenario": "CrushInducedArc",
    "PartialDisconnectionScenario": "PartialDisconnectionHeating",
    "InsulationDegradationScenario": "InsulationBreakdownArc",
    "TrackingScenario": "ArcTracking",
    "ExternalFlameScenario": "ExternalFlameExposure",
}
KO = {"PoorContactScenario": "접촉불량", "CrushDamageScenario": "압착손상",
      "PartialDisconnectionScenario": "반단선", "InsulationDegradationScenario": "절연열화",
      "TrackingScenario": "트래킹", "ExternalFlameScenario": "외부화염",
      "Undetermined": "원인미상"}


def predict(sess, onto):
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent
    s = Session(
        case_id=sess["case_id"],
        query_count=sess["query_count"],
        hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v))
                    for k, v in MECH.items()],
        facts=[Fact(cls=f["cls"], status=Status(f["status"]), agent=Agent(f["agent"]))
               for f in sess["facts"]],
    )
    s.apply(onto)
    live = [h for h in s.hypotheses if h.verdict.value != "Refuted"]
    if not live:
        return "Undetermined", s
    top = max(h.support_score for h in live)
    best = [h for h in live if h.support_score == top]
    if len(best) > 1:
        return "Undetermined", s          # §19.6.5.1 둘 이상 남으면 원인미상
    return best[0].scenario.value, s


def main():
    from efi_schema import Ontology
    onto = Ontology.load(str(TTL))
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))

    conf = collections.Counter()
    per = collections.defaultdict(lambda: [0, 0])       # 실제 → [맞음, 전체]
    undet = collections.Counter()
    ties = []
    for sess in sessions:
        pred, s = predict(sess, onto)
        act = sess["actual_scenario"]
        conf[(act, pred)] += 1
        per[act][1] += 1
        if pred == act:
            per[act][0] += 1
        if pred == "Undetermined":
            undet[act] += 1
            live = [h for h in s.hypotheses if h.verdict.value != "Refuted"]
            top = max((h.support_score for h in live), default=0)
            ties.append((sess["case_id"], act,
                         [KO[h.scenario.value] for h in live if h.support_score == top]))

    n = len(sessions)
    ok = sum(v[0] for v in per.values())
    nd = sum(undet.values())
    print(f"사례 {n}건\n")
    print(f"  정확  {ok:3d}건  {ok / n * 100:5.1f}%")
    print(f"  원인미상 {nd:3d}건  {nd / n * 100:5.1f}%   (동점 또는 전부 기각)")
    print(f"  오판  {n - ok - nd:3d}건  {(n - ok - nd) / n * 100:5.1f}%")

    print(f"\n{'실제':8s} {'건수':>4s} {'정확':>4s} {'미상':>4s} {'정확도':>7s}")
    for a in sorted(per, key=lambda x: -per[x][1]):
        c, t = per[a]
        print(f"{KO[a]:8s} {t:4d} {c:4d} {undet[a]:4d} {c / t * 100:6.1f}%")

    print("\n혼동 행렬  (행=실제, 열=판정)")
    labels = sorted({a for a, _ in conf} | {p for _, p in conf if p != "Undetermined"})
    print(f"{'':10s}" + "".join(f"{KO[l][:6]:>7s}" for l in labels) + f"{'미상':>7s}")
    for a in labels:
        row = "".join(f"{conf.get((a, p), 0):7d}" for p in labels)
        print(f"{KO[a]:10s}{row}{undet.get(a, 0):7d}")

    # 기준선을 파일로 남긴다. 못 박아 두지 않으면 나중에 무엇 때문에 올랐는지
    # 말할 수 없다. 사건 정보는 담지 않고 집계만 남긴다.
    base = {"cases": n, "correct": ok, "undetermined": nd, "wrong": n - ok - nd,
            "accuracy": round(ok / n, 4),
            "per_class": {KO[a]: {"n": per[a][1], "correct": per[a][0],
                                  "undetermined": undet.get(a, 0)} for a in per}}
    (ROOT / "cases" / "baseline.json").write_text(
        json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n동점으로 갈리지 않은 사례 {len(ties)}건 — 어느 가설끼리 붙었나")
    pair = collections.Counter()
    for _, act, tied in ties:
        if len(tied) > 1:
            pair[" · ".join(sorted(tied))] += 1
    for k, v in pair.most_common(8):
        print(f"   {v:3d}건  {k}")


if __name__ == "__main__":
    main()
