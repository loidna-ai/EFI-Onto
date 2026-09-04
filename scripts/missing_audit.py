# -*- coding: utf-8 -*-
"""대화 루프의 결측을 가른다 — 원문에 답이 있는데 못 뽑은 것인가, 원문에도 없는 것인가.

run_case.py 의 150건 대화 루프에서 질의가 결측(Missing)으로 끝난 것이 1,003건이었다.
그 결측이 판독기의 한계인지 조사서(서식)의 한계인지가 다음 일을 정한다 —
판독기를 고칠 것인가, 서식에 항목을 넣을 것인가. 그리고 조사관과 재검토할 사건을 고를 근거다.

결측 하나마다 세 신호를 본다.
  LLM   cases/llm_reading.json 이 그 사실을 읽었는가 (사전이 놓친 것을 LLM 이 읽은 기록)
  사전  scripts/slots.py 의 규칙이 원문에 걸리는가 (걸리는데 세션에 없으면 판독 파이프라인 문제)
  낱말  온톨로지의 한글 이름(prefLabel·altLabel)이 원문에 그대로 있는가 (사전에 규칙이 없는 것)

  python scripts/missing_audit.py
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import json, re, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import run_case as rc
import slots
from efi_schema import Status, load_graph
from rdflib import Namespace, RDFS, URIRef

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
E = Namespace("https://w3id.org/efi-onto#")
OBS = ROOT / "cases" / "observed"
ln = lambda u: str(u).split("#")[-1]


def vocabulary():
    g = load_graph()
    desc = collections.defaultdict(set)
    for s, o in g.subject_objects(RDFS.subClassOf):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            desc[ln(o)].add(ln(s))
    def below(c, seen=None):
        seen = seen or set()
        for d in desc.get(c, ()):
            if d not in seen:
                seen.add(d); below(d, seen)
        return seen
    names = collections.defaultdict(set)
    for p in (SKOS.prefLabel, SKOS.altLabel):
        for s, o in g.subject_objects(p):
            if getattr(o, "language", None) == "ko":
                for part in re.split(r"[·(),/]", str(o)):
                    part = part.strip()
                    if len(part) >= 2:
                        names[ln(s)].add(part)
    return below, names


def raw_text(case_id):
    for p in OBS.glob("*.txt"):
        if p.stem.lower() == case_id.lower():
            return p.read_text(encoding="utf-8")
    return ""


def main():
    onto, ko = rc.Ontology.load(), rc.labels()
    below, names = vocabulary()
    cases = json.loads(rc.SESSIONS.read_text(encoding="utf-8"))
    llm = json.loads((ROOT / "cases" / "llm_reading.json").read_text(encoding="utf-8"))
    llm_by = collections.defaultdict(set)
    for r in llm["readings"]:
        llm_by[r["case"]].update(r["classes"])
    rules = [(re.compile(pat), cls) for pats in slots.RULES.values() for pat, cls in pats]

    rows, picks = [], []
    for c in cases:
        s, log = rc.run(c, onto, ko)
        out, top, _ = rc.conclude(s, onto)
        text = raw_text(c["case_id"])
        actual = next(h for h in s.hypotheses if h.scenario.value == c["actual_scenario"])
        for f in s.facts:
            if f.status is not Status.MISSING:
                continue
            fam = {f.cls} | below(f.cls)
            llm_hit = bool(llm_by[c["case_id"]] & fam)
            dict_hit = any(cls in fam and rx.search(text) for rx, cls in rules)
            words = {w for n in fam for w in names.get(n, ())}
            word_hit = next((w for w in words if w in text), None)
            cat = ("LLM 이 읽음" if llm_hit else "사전 규칙이 원문에 걸림" if dict_hit
                   else "원문에 낱말 있음" if word_hit else "원문에 없음")
            need = onto.needs.get(c["actual_scenario"], set())
            forms_actual = any(onto.matches(f.cls, n) or onto.matches(n, f.cls) for n in need)
            rows.append((c["case_id"], c["actual_scenario"], f.cls, cat, word_hit, forms_actual, out == c["actual_scenario"], actual.formed))

    n = len(rows)
    cat = collections.Counter(r[3] for r in rows)
    print(f"결측 {n}건")
    for k, v in cat.most_common():
        print(f"  {k:14s} {v:5d}  ({v / n * 100:.0f}%)")

    print("\n결측이 많은 지표 (건수 · 원문에 답이 있는 비율)")
    by_ind = collections.defaultdict(list)
    for r in rows:
        by_ind[r[2]].append(r[3])
    for ind, cats in sorted(by_ind.items(), key=lambda kv: -len(kv[1]))[:12]:
        have = sum(1 for x in cats if x != "원문에 없음")
        print(f"  {ko.get(ind, ind):22s} {len(cats):4d}   원문에 있음 {have:3d} ({have / len(cats) * 100:.0f}%)")

    # 정답 가설의 필요조건이 결측으로 끝난 사례 — 판독 문제인가 서식 문제인가
    print("\n정답이 형성되지 못한 사례 — 그 필요조건의 결측이 어디서 왔나")
    crit = [r for r in rows if r[5] and not r[7]]
    src = collections.Counter(r[3] for r in crit)
    for k, v in src.most_common():
        print(f"  {k:14s} {v}")

    print("\n조사관 재검토 후보 5건")
    reading = [r for r in crit if r[3] != "원문에 없음"]
    form = [r for r in crit if r[3] == "원문에 없음"]
    seen = set()
    for label, pool, k in (("판독 문제 — 원문에 답이 있다", reading, 3), ("서식 문제 — 원문에도 없다", form, 2)):
        print(f"  [{label}]")
        for r in pool:
            if r[0] in seen or k == 0:
                continue
            seen.add(r[0]); k -= 1
            snippet = ""
            if r[4]:
                t = raw_text(r[0]); i = t.find(r[4])
                snippet = t[max(0, i - 25): i + 35].replace("\n", " ")
            print(f"    {r[0]:20s} 조사관 {ko.get(r[1], r[1]):6s} 결측 {ko.get(r[2], r[2])} · {r[3]}"
                  + (f' · "{snippet}"' if snippet else ""))


if __name__ == "__main__":
    main()
