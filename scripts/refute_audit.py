# -*- coding: utf-8 -*-
"""반증 규칙을 사례로 검증한다. 사람에게 묻지 않는다.

왜 필요한가
  검토표 시트 6 은 조사관에게 "X 가 확인되면 A 를 약화시켜도 되는가"를 물었다.
  그 답은 의견이 아니라 사실이다 — 'A 요인의 화재에서도 X 가 나오는가'.
  사실이면 두 곳에서 확인할 수 있다. 원문, 그리고 사례.

  이 파일은 사례 쪽이다. 반증 규칙 하나가 정답 라벨의 사례에서 발동하면
  그 규칙은 맞는 답을 깎는다. 그것이 반례다. 반례가 있는 규칙은 결정적
  반증이 될 수 없고, 반례가 많으면 약화 규칙으로도 틀렸다.

무엇을 세는가
  기존 반증 규칙마다:  발동 건수 / 그중 정답 라벨에서 발동한 반례 건수
  시트 6 후보마다:      같은 것 + 후보를 넣었을 때의 정확도 변화

한계
  라벨은 조사관 판정이다. 반례 1건은 라벨 오류일 수도 있다.
  관측 0건인 규칙은 이 파일이 검증하지 못한다. 원문만이 근거다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import sys, json, pathlib, collections
from rdflib import Graph

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import score
from efi_schema import load_graph

TTL = ROOT / "ontology" / "efi_tbox.ttl"
KO = {"PoorContactScenario": "접촉불량", "CrushDamageScenario": "압착손상",
      "PartialDisconnectionScenario": "반단선", "InsulationDegradationScenario": "절연열화",
      "TrackingScenario": "트래킹", "ExternalFlameScenario": "외부화염",
      "OverloadScenario": "과부하", "GroundFaultScenario": "누전지락", "InterTurnShortScenario": "층간단락",
      "ElectricalIgnitionScenario": "전기 전체"}


def _targets(scenario):
    return set(score.ELECTRICAL) if scenario == "ElectricalIgnitionScenario" else {scenario}


def fires(onto, sessions, indicator, status):
    """지표가 그 확인 상태로 발동하는 사례의 라벨 분포."""
    hit = onto.matches_absent if status == "ConfirmedAbsent" else onto.matches
    return collections.Counter(
        s["actual_scenario"] for s in sessions
        if any(hit(f["cls"], indicator) and f["status"] == status for f in s["facts"]))


def existing(onto, sessions):
    """기존 반증 규칙 → (발동 건수, 반례 건수, 반례 라벨)."""
    out = []
    for r in onto.rules:
        if r.role.value not in ("Refuting", "DecisiveRefuting"):
            continue
        d = fires(onto, sessions, r.indicator, r.required_status.value)
        bad = {k: v for k, v in d.items() if k in _targets(r.scenario)}
        out.append((r.id, r.scenario, r.indicator, r.required_status.value, r.delta,
                    sum(d.values()), sum(bad.values()), bad))
    return out


def candidates(g):
    """검토표 시트 6 과 같은 후보. (약화되는 가설, 전용 가설, 지표, 형태 여부).

    혼동 쌍마다 하나 — 사슬상 한 가설에만 양립하는 지표 중 그 가설의 규칙이 아직
    쓰지 않는 것을 대표로 뽑는다. review.py 가 이 함수를 쓴다.
    """
    from rdflib import Namespace
    E = Namespace("https://w3id.org/efi-onto#")
    ln = score.ln
    man = {sc: {ln(d) for d in g.objects(E[sc], E.canManifest)} for sc in score.SCENARIOS}
    conf = {(a, b): len(man[a] & man[b]) for a in score.SCENARIOS for b in score.SCENARIOS
            if a != b and len(man[a] & man[b]) >= 2}
    excl = {i: next(iter(v)) for i, v in score.compatibility(g).items() if len(v) == 1}
    cov = {}
    for _, sc, ind, _ in score.rules(g):
        for x in _targets(sc):
            cov.setdefault(x, set()).add(ind)
    morph = lambda i: "DamagePattern" in score._ancestors(g, E[i])
    out = []
    for (sc, own), n in conf.items():
        pool = [i for i, o in excl.items() if o == own and i not in cov.get(sc, set())]
        anc = {i: score._ancestors(g, E[i]) for i in pool}
        pool = [i for i in pool if not (anc[i] & set(pool))]
        if not pool:
            continue
        pool.sort(key=lambda i: (morph(i), len(anc[i]), i))
        out.append((sc, own, pool[0], n, morph(pool[0])))
    return sorted(out, key=lambda r: (r[2], r[0]))


def _accuracy(onto, sessions):
    import eval as ev
    ok = und = 0
    for s in sessions:
        p, _ = ev.predict(s, onto)
        ok += p == s["actual_scenario"]
        und += p in ev.HELD
    n = len(sessions)
    return ok / n, und / n, (n - ok - und) / n


def simulate(onto, sessions, rules):
    """규칙을 더한 온톨로지로 정확도를 다시 잰다. 원본은 건드리지 않는다."""
    from efi_schema import IndicatorRule, Role, Status
    o = onto.model_copy(deep=True)
    for i, (sc, ind, delta) in enumerate(rules):
        o.rules.append(IndicatorRule(id=f"cand{i}", scenario=sc, indicator=ind,
                                     role=Role.REFUTING, required_status=Status.CONFIRMED,
                                     delta=delta, basis="후보"))
    return _accuracy(o, sessions)


if __name__ == "__main__":
    from efi_schema import Ontology
    g = load_graph()
    onto = Ontology.load()
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))
    lab = {}
    for s, o in g.subject_objects(score.SKOS.prefLabel):
        lab.setdefault(score.ln(s), str(o))
    K = lambda x: lab.get(x, x)[:20]

    print("■ 기존 반증 규칙 — 정답 라벨에서 발동하면 반례다\n")
    print(f"{'규칙':20s}{'가설':10s}{'지표':22s}{'상태':16s}{'점':>4s}{'발동':>5s}{'반례':>5s}  반례 라벨")
    ex = existing(onto, sessions)
    for rid, sc, ind, st, d, n, bad, lbl in sorted(ex, key=lambda r: (-r[6], -r[5])):
        who = " ".join(f"{KO[k]}{v}" for k, v in lbl.items())
        print(f"{rid:20s}{KO[sc]:10s}{K(ind):22s}{st:16s}{d:4d}{n:5d}{bad:5d}  {who}")
    print(f"\n  규칙 {len(ex)}개 · 사례에서 한 번이라도 발동한 것 {sum(1 for r in ex if r[5])}개 "
          f"· 반례 있는 것 {sum(1 for r in ex if r[6])}개")

    base = _accuracy(onto, sessions)
    print(f"\n■ 검토표 시트 6 후보 — 넣으면 어떻게 되는가   (지금 정확 {base[0]*100:.1f}% "
          f"미상 {base[1]*100:.1f}% 오판 {base[2]*100:.1f}%)\n")
    print(f"{'약화 가설':10s}{'전용 가설':10s}{'지표':22s}{'점':>4s}{'발동':>5s}{'반례':>5s}"
          f"{'정확':>8s}{'미상':>7s}{'오판':>7s}")
    cands = candidates(g)
    by_ind = collections.defaultdict(list)
    for sc, own, ind, n, morph in cands:
        by_ind[ind].append((sc, own, morph))
    all_rules = []
    for ind, rows in by_ind.items():
        d = fires(onto, sessions, ind, "Confirmed")
        delta = -21 if rows[0][2] else -30                       # k=1 이므로 최대치
        rules = [(sc, ind, delta) for sc, _, _ in rows]
        all_rules += rules
        acc = simulate(onto, sessions, rules)
        bad = sum(v for k, v in d.items() if k != rows[0][1])
        print(f"{'(전부)':10s}{KO[rows[0][1]]:10s}{K(ind):22s}{delta:4d}{sum(d.values()):5d}{bad:5d}"
              f"{(acc[0]-base[0])*100:+7.1f}p{(acc[1]-base[1])*100:+6.1f}p{(acc[2]-base[2])*100:+6.1f}p"
              f"   {' '.join(f'{KO[k]}{v}' for k, v in d.items()) or '관측 0건'}")
    acc = simulate(onto, sessions, all_rules)
    print(f"\n  후보 {len(all_rules)}개 전부 넣으면  정확 {(acc[0]-base[0])*100:+.1f}%p  "
          f"미상 {(acc[1]-base[1])*100:+.1f}%p  오판 {(acc[2]-base[2])*100:+.1f}%p")
    print("\n  읽는 법: 반례가 있으면 그 지표는 다른 요인에서도 나온다 — 반증이 아니다.")
    print("          관측 0건이면 사례로는 검증할 수 없다. 원문만이 근거다.")
    print("          정확도가 올라도 원문 없이 넣지 않는다. 정확도는 계기다.")
