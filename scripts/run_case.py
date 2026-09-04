# -*- coding: utf-8 -*-
"""사례 하나를 FIReAct 연동 흐름(설계계획서 7.4)대로 끝까지 돌린다.

  판독(사진 층 사실만) → 가설 아홉을 50점에서 세움 → 변별 질의 선택 → 조사서로 응답
  → 재평가 → 확정 검사 → SHACL 검증 → PROV 경로로 '가설 교차검증' 보고서.

지금까지 이 흐름을 처음부터 끝까지 이어 붙여 돌린 적이 없었다. 평가(eval.py)는 조사서의
사실을 전부 한 번에 넣는다. 여기서는 **온톨로지가 고른 질의**에 조사서에 실제로 적힌 것으로만
답한다 — 질의 선택이 조사서에 있는 것을 묻는지, 몇 번 물어야 판정에 이르는지가 드러난다.
조사서에 없는 항목은 결측(Missing)으로 답한다. 결측은 부정 확인이 아니다 (P4).

  python scripts/run_case.py UIJEONGBU_2025_055        보고서 → build/run_<case>.md · .ttl
  python scripts/run_case.py --all                      150건 요약 (SHACL 은 생략)
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from efi_schema import (Session, Hypothesis, Fact, Ontology, Scenario, Mechanism, Status, Agent,
                        DEFAULT_MECHANISM, load_graph, ontology_text)
from rdflib import Graph, Namespace, RDF, URIRef

SESSIONS = ROOT / "cases" / "sessions.json"
E = Namespace("https://w3id.org/efi-onto#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
PROV = Namespace("http://www.w3.org/ns/prov#")
MAX_QUERIES = 8
ln = lambda u: str(u).split("#")[-1]


def labels():
    g = load_graph()
    return {ln(s): str(o) for s, o in g.subject_objects(SKOS.prefLabel) if getattr(o, "language", None) == "ko"}


def fresh(case):
    return Session(case_id=case["case_id"], query_count=0,
                   hypotheses=[Hypothesis(scenario=Scenario(k), mechanism=Mechanism(v)) for k, v in DEFAULT_MECHANISM.items()])


def fact(f):
    return Fact(cls=f["cls"], status=Status(f["status"]), agent=Agent(f["agent"]), note=f.get("src"))


def run(case, onto, ko, trace=True):
    """(세션, 자취) — 자취는 단계별 기록."""
    log = []
    photo = [f for f in case["facts"] if onto.is_damage(f["cls"])]
    scene = [f for f in case["facts"] if not onto.is_damage(f["cls"])]
    s = fresh(case)
    s.facts = [fact(f) for f in photo]
    s.apply(onto)
    log.append(("판독", [ko.get(f["cls"], f["cls"]) for f in photo], scores(s)))
    answered = set()
    while s.query_count < MAX_QUERIES:
        slots = [x for x in s.discriminating_slots(onto) if x[0] not in answered]
        # 확정 조건이 차도 세워 보지 않은 가설이 남았으면 계속 묻는다 — 대안 가설을 고려하지
        # 않는 것은 중대한 오류다(C-24, §4.3.7). 절연열화가 먼저 70점을 넘자 트래킹의 필요조건을
        # 묻지도 않고 멈춰 1,805자짜리 조사서를 오판한 사례가 있었다. 형성 질의(변별력 100 이상)만
        # 계속하고, 점수 차 질의는 확정 뒤에는 하지 않는다.
        if s.closure_met(onto):
            slots = [x for x in slots if x[2] >= 100]
        if not slots:
            pre = [c for c in s.prerequisite_slots(onto) if c not in answered]   # 확정 전제 (C-57 통전)
            if not pre:
                log.append(("질의 없음", "가르는 미확인 지표가 없다", scores(s))); break
            slots = [(pre[0], max(s.hypotheses, key=lambda h: h.support_score).scenario, 0)]
        ind, target, w = slots[0]
        answered.add(ind)
        hits = [f for f in scene if onto.matches(f["cls"], ind)]
        if hits:
            answer = [fact(f) for f in hits]
            said = "; ".join(f"{ko.get(f['cls'], f['cls'])}={f['status']} ({f.get('src','')})" for f in hits)
        else:
            answer = [Fact(cls=ind, status=Status.MISSING, agent=Agent.INVESTIGATOR)]
            said = "조사서에 없음 → 결측"
        s.facts += answer
        s.query_count += 1
        s.apply(onto)
        log.append((f"질의 {s.query_count}", f"{ko.get(ind, ind)}? (가르는 쪽: {ko.get(target.value, target.value)}, 변별력 {w}) → {said}", scores(s)))
    return s, log


def scores(s):
    return {h.scenario.value: (h.support_score, h.verdict.value, h.formed) for h in s.hypotheses}


def conclude(s, onto):
    out = s.outcome(onto)
    top = max(s.hypotheses, key=lambda h: h.support_score)
    problems = s.conclusion_check(top, onto)
    if not problems and out == top.scenario.value:
        s.proposed_conclusion = top.scenario
    return out, top, problems


def cross_validation(s):
    """CQ5 — SHACL 규칙을 돌린 그래프에서 지지·기각 경로를 증거 → 행위자로 읽는다."""
    from pyshacl import validate
    g = Graph().parse(data=ontology_text() + s.to_turtle(include_derived=False), format="turtle")
    validate(g, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    rows = []
    for h in s.hypotheses:
        n = URIRef(f"{E}{s.case_id}_{h.scenario.value}")
        for p, label in ((E.supportedBy, "지지"), (E.refutedBy, "기각")):
            for f in g.objects(n, p):
                who = ", ".join(ln(a) for a in g.objects(f, PROV.wasAttributedTo))
                rows.append((h.scenario.value, label, ln(next(g.objects(f, RDF.type))), ln(next(g.objects(f, E.confirmationStatus), "")), who))
    score = {h.scenario.value: next((int(x) for x in g.objects(URIRef(f"{E}{s.case_id}_{h.scenario.value}"), E.supportScore)), None)
             for h in s.hypotheses}
    return rows, score, g


def report(case, s, log, onto, ko):
    out, top, problems = conclude(s, onto)
    violations = s.validate() if s.proposed_conclusion else []
    rows, shacl_score, g = cross_validation(s)
    name = lambda k: ko.get(k, k)
    L = [f"# 연동 흐름 실행 — {case['case_id']}", "",
         f"조사관 판정: **{name(case['actual_scenario'])}** · 조사서 사실 {len(case['facts'])}건 · 원래 질의 수 {case.get('query_count')}", ""]
    L += ["## 1. 가설수립 — 사진 층 사실만으로", ""]
    for step, what, sc in log[:1]:
        L.append(f"판독된 손상 양상: {', '.join(what) or '(없음)'}"); L.append("")
        L += table(sc, name)
    L += ["", "## 2. 가설검증 — 온톨로지가 고른 질의와 조사서의 답", ""]
    for step, what, sc in log[1:]:
        L.append(f"**{step}.** {what}"); L.append("")
        L += table(sc, name); L.append("")
    L += ["## 3. 확정", "",
          f"- 판정: **{name(out)}**  (조사관: {name(case['actual_scenario'])}) → {'일치' if out == case['actual_scenario'] else '불일치'}",
          f"- 최상위 가설 {name(top.scenario.value)} {top.support_score}점 · 확정 조건: " + ("충족" if not problems else "; ".join(problems)),
          f"- 질의 {s.query_count}회 · 사실 {len(s.facts)}건 (결측 {sum(1 for f in s.facts if f.status is Status.MISSING)})"]
    if s.proposed_conclusion:
        L.append(f"- SHACL 결론 제약: " + ("위반 없음" if not violations else ""))
        L += [f"  - {v}" for v in violations]
    L += ["", "## 4. 가설 교차검증 (PROV 경로)", "", "| 가설 | 근거 | 사실 | 확인 상태 | 행위자 |", "|---|---|---|---|---|"]
    L += [f"| {name(a)} | {b} | {name(c)} | {d} | {e} |" for a, b, c, d, e in sorted(rows)]
    mism = {k: (v, shacl_score[k]) for k, v in scores(s).items() if shacl_score.get(k) is not None and shacl_score[k] != v[0]}
    L += ["", f"Python 점수와 SHACL F-4 점수 대조: " + ("일치" if not mism else f"**불일치** {mism}")]
    return "\n".join(L) + "\n", g


def table(sc, name):
    rows = sorted(sc.items(), key=lambda kv: -kv[1][0])
    return ["| 가설 | 점수 | 판정 | 형성 |", "|---|---:|---|---|"] + \
           [f"| {name(k)} | {v[0]} | {v[1]} | {'예' if v[2] else '아니오'} |" for k, v in rows]


def main():
    onto, ko = Ontology.load(), labels()
    cases = json.loads(SESSIONS.read_text(encoding="utf-8"))
    (ROOT / "build").mkdir(exist_ok=True)
    if "--all" in sys.argv:
        hit = held = wrong = 0; q = collections.Counter(); per = collections.defaultdict(lambda: [0, 0])
        for c in cases:
            s, _ = run(c, onto, ko); out, *_ = conclude(s, onto)
            q[s.query_count] += 1; per[c["actual_scenario"]][1] += 1
            if out == c["actual_scenario"]: hit += 1; per[c["actual_scenario"]][0] += 1
            elif out in ("Undetermined", "UnidentifiedShortCircuit"): held += 1
            else: wrong += 1
        n = len(cases)
        print(f"대화 루프 150건 — 일치 {hit} ({hit/n*100:.1f}%) · 판단보류 {held} · 오판 {wrong} · 최대 질의 {MAX_QUERIES}")
        print("질의 횟수 분포:", dict(sorted(q.items())))
        for k, (a, b) in per.items(): print(f"  {ko.get(k,k):6s} {a}/{b}")
        return
    ids = [a for a in sys.argv[1:] if not a.startswith("-")] or ["UIJEONGBU_2025_055"]
    for cid in ids:
        case = next(c for c in cases if c["case_id"] == cid)
        s, log = run(case, onto, ko)
        md, g = report(case, s, log, onto, ko)
        (ROOT / "build" / f"run_{cid}.md").write_text(md, encoding="utf-8", newline="\n")
        g.serialize(destination=ROOT / "build" / f"run_{cid}.ttl", format="turtle")
        print(md)


if __name__ == "__main__":
    main()
