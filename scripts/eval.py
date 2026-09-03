# -*- coding: utf-8 -*-
"""사례를 돌려 정확도를 잰다. 이 프로젝트에서 처음 재는 정확도다.

지금까지 잰 것은 전부 이식률이었다 — 이론을 얼마나 옮겼는가. 이 파일은 다른
것을 묻는다. 옮긴 것이 실제로 맞히는가.

판정 방식
  9개 가설 후보에 사실을 넣어 점수를 매긴다. 형성되고 기각되지 않은 것 중
  50점 초과의 유일한 최고점이 판정이다. 승자가 없으면 판단보류로 둔다 — §19.6.5.1 이
  둘 이상이 기각되지 않으면 원인미상이라고 한다. 억지로 하나를 고르면
  이론을 어기면서 정확도를 부풀리는 것이 된다.

두 가지 정확도를 함께 낸다
  전체 정확도  원인미상을 오답으로 세는 값. 논문에 쓸 단일 숫자다.
  답한 것 중   판단보류를 뺀 값. 답을 냈을 때 얼마나 맞는가.
  이 영역은 틀린 답보다 판단보류가 낫다(§19.6.5.1). 둘을 같이 보아야 한다.

한계 (숫자를 읽을 때 함께 읽을 것)
  외부화염·과부하·누전지락·층간단락 라벨 사례가 없다. 9개 중 5개만 나온다.
  절연저항 슬롯이 0건이라 트래킹 반증 규칙은 발동하지 않는다.
  조사관 최초 판단이 없어 사람과 비교할 수 없다.
"""
import json, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TTL = ROOT / "ontology" / "efi_tbox.ttl"

KO = {"PoorContactScenario": "접촉불량", "CrushDamageScenario": "압착손상",
      "PartialDisconnectionScenario": "반단선", "InsulationDegradationScenario": "절연열화",
      "TrackingScenario": "트래킹", "ExternalFlameScenario": "외부화염",
      "OverloadScenario": "과부하", "GroundFaultScenario": "누전지락", "InterTurnShortScenario": "층간단락",
      "Undetermined": "원인미상", "UnidentifiedShortCircuit": "미확인단락"}


HELD = {"Undetermined", "UnidentifiedShortCircuit"}     # 전체 정확도의 정답에는 제외하되, 오판과 별도 집계


def predict(sess, onto):
    from efi_schema import Session, Hypothesis, Fact, Scenario, Mechanism, Status, Agent, DEFAULT_MECHANISM
    s = Session(
        case_id=sess["case_id"],
        query_count=sess["query_count"],
        hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v))
                    for k, v in DEFAULT_MECHANISM.items()],
        facts=[Fact(cls=f["cls"], status=Status(f["status"]), agent=Agent(f["agent"]))
               for f in sess["facts"]],
    )
    s.apply(onto)
    # 가설 하나, 원인미상(§19.6.5.1), 또는 미확인 단락(원인미상 + 단락흔 + 통전). Session.outcome 이 정한다
    return s.outcome(onto), s


def main():
    from efi_schema import Ontology
    onto = Ontology.load(str(TTL))
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))

    conf = collections.Counter()
    per = collections.defaultdict(lambda: [0, 0])       # 실제 → [맞음, 전체]
    undet = collections.Counter()                       # 판단보류 전체 (원인미상 + 미확인 단락)
    unid = collections.Counter()                        # 그중 미확인 단락 (단락흔 + 통전)
    ties = []
    for sess in sessions:
        pred, s = predict(sess, onto)
        act = sess["actual_scenario"]
        conf[(act, pred)] += 1
        per[act][1] += 1
        if pred == act:
            per[act][0] += 1
        if pred == "UnidentifiedShortCircuit":
            unid[act] += 1
        if pred in HELD:
            undet[act] += 1
            live = [h for h in s.hypotheses if h.formed and h.verdict.value != "Refuted" and h.support_score > 50]
            top = max((h.support_score for h in live), default=0)
            ties.append((sess["case_id"], act,
                         [KO[h.scenario.value] for h in live if h.support_score == top]))

    # 천장 — 조사서에 자기 요인을 가리키는 사실이 하나도 없으면 어떤 온톨로지도
    # 못 맞힌다. 그런 사례를 뺀 것이 도달 가능한 상한이고, 남은 거리가 곧 할 일이다.
    # 거리가 0 이면 더 할 일은 온톨로지가 아니라 조사서 서식에 있다.
    ceil = collections.Counter()
    for sess in sessions:
        if any(any(onto.matches(f["cls"], r.indicator) for r in onto.rules
                   if r.scenario == sess["actual_scenario"] and r.role.value in ("Core", "Supporting"))
               for f in sess["facts"] if f["status"] == "Confirmed"):
            ceil[sess["actual_scenario"]] += 1

    n = len(sessions)
    ok = sum(v[0] for v in per.values())
    nd = sum(undet.values())
    print(f"사례 {n}건\n")
    print(f"  정확  {ok:3d}건  {ok / n * 100:5.1f}%")
    nu = sum(unid.values())
    print(f"  판단보류 {nd:3d}건  {nd / n * 100:5.1f}%   (동점 또는 판정 요건을 갖춘 가설 없음) — 그중 미확인 단락 {nu}건, 원인미상 {nd - nu}건")
    print(f"  오판  {n - ok - nd:3d}건  {(n - ok - nd) / n * 100:5.1f}%")
    ans = n - nd
    print(f"\n  답한 것 중 정확  {ok:3d}/{ans}  {ok / ans * 100:5.1f}%   (판단보류 제외)")
    cn = sum(ceil.values())
    print(f"  도달 가능한 상한 {cn:3d}/{n}  {cn / n * 100:5.1f}%   (조사서에 자기 요인 단서가 있는 사례)")

    print(f"\n{'실제':8s} {'건수':>4s} {'정확':>4s} {'보류':>4s} {'정확도':>7s} {'상한':>7s} {'남은거리':>8s}")
    for a in sorted(per, key=lambda x: -per[x][1]):
        c, t = per[a]
        cl = ceil.get(a, 0)
        print(f"{KO[a]:8s} {t:4d} {c:4d} {undet[a]:4d} {c / t * 100:6.1f}% {cl / t * 100:6.1f}% {(cl - c) / t * 100:7.1f}%p")

    print("\n혼동 행렬  (행=실제, 열=판정)")
    labels = sorted({a for a, _ in conf} | {p for _, p in conf if p not in HELD})
    print(f"{'':10s}" + "".join(f"{KO[l][:6]:>7s}" for l in labels) + f"{'미확인':>7s}{'미상':>7s}")
    for a in labels:
        row = "".join(f"{conf.get((a, p), 0):7d}" for p in labels)
        print(f"{KO[a]:10s}{row}{unid.get(a, 0):7d}{undet.get(a, 0) - unid.get(a, 0):7d}")

    # 기준선을 파일로 남긴다. 못 박아 두지 않으면 나중에 무엇 때문에 올랐는지
    # 말할 수 없다. 사건 정보는 담지 않고 집계만 남긴다.
    base = {"cases": n, "correct": ok, "undetermined": nd, "unidentified_short": nu, "wrong": n - ok - nd,
            "accuracy": round(ok / n, 4),
            "accuracy_when_answered": round(ok / ans, 4),
            "ceiling": round(cn / n, 4),
            "per_class": {KO[a]: {"n": per[a][1], "correct": per[a][0],
                                  "undetermined": undet.get(a, 0),
                                  "ceiling": ceil.get(a, 0)} for a in per}}
    (ROOT / "cases" / "baseline.json").write_text(
        json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n판단보류 {len(ties)}건 중 실제로 경합한 가설의 동점만 표시")
    pair = collections.Counter()
    for _, act, tied in ties:
        if len(tied) > 1:
            pair[" · ".join(sorted(tied))] += 1
    for k, v in pair.most_common(8):
        print(f"   {v:3d}건  {k}")

    # 동점이 왜 생기는지는 여기서 보인다. 한 사례가 여러 요인의 핵심 단서를
    # 함께 적고 있으면 점수로 갈리지 않는다. 대각선이 아닌 칸이 그 겹침이다.
    core = {r.scenario: r.indicator for r in onto.rules if r.role.value == "Core"}
    lab = [a for a in labels if a in core]
    print("\n핵심 단서 교차표  (행=실제, 열=그 요인의 핵심 단서를 적은 사례 수)")
    print(f"{'':10s}" + "".join(f"{KO[b][:6]:>7s}" for b in lab))
    for a in lab:
        row = ""
        for b in lab:
            n = sum(1 for s in sessions if s["actual_scenario"] == a
                    and any(onto.matches(f["cls"], core[b]) and f["status"] == "Confirmed"
                            for f in s["facts"]))
            row += f"{n:7d}"
        print(f"{KO[a]:10s}{row}")


if __name__ == "__main__":
    main()
