# -*- coding: utf-8 -*-
"""현재 상태를 한 화면에 출력한다.

문서에 숫자를 손으로 적으면 반드시 낡는다. 실제로 낡았다 — SHACL 도형이 12개라고
적혀 있는 동안 55개가 됐다. 그래서 숫자는 여기서만 만들고 문서는 원칙만 적는다.
"""
import sys, json, pathlib, collections
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH, URIRef

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
TTL = ROOT / "ontology" / "efi_tbox.ttl"
E = Namespace("https://w3id.org/efi-onto#")
ln = lambda u: str(u).split("#")[-1]


def main():
    g = Graph().parse(TTL, format="turtle")
    named = lambda t: [s for s in g.subjects(RDF.type, t) if isinstance(s, URIRef)]
    shapes = named(SH.NodeShape)
    dp = [s for s in g.subjects(RDFS.subClassOf, E.DamagePattern)]

    print("── TBox " + "─" * 52)
    print(f"  트리플 {len(g)}   클래스 {len(named(OWL.Class))}")
    print(f"  객체 속성 {len(named(OWL.ObjectProperty))}   데이터 속성 {len(named(OWL.DatatypeProperty))}")
    print(f"  지표 규칙 {len(named(E.IndicatorRule))}   SHACL 도형 {len(shapes)}")

    import nfpa
    c = nfpa.counts()
    tot = len(nfpa.SECTIONS) - c[nfpa.OUT]
    print("\n── NFPA 921 (2024) 이식률 " + "─" * 35)
    print(f"  절 {len(nfpa.SECTIONS)}개 중 범위 내 {tot}개")
    print(f"  구현 {c[nfpa.DONE]}  일부 {c[nfpa.PART]}  없음 {c[nfpa.NONE]}  범위밖 {c[nfpa.OUT]}")
    print(f"  이식률 {c[nfpa.DONE]}/{tot} = {c[nfpa.DONE] / tot * 100:.0f}%")
    sub = collections.Counter(x[2] for x in nfpa.SUBSECTIONS)
    stot = len(nfpa.SUBSECTIONS) - sub[nfpa.PROC] - sub[nfpa.OUT]
    print(f"  하위 절까지 내려간 것 {len(nfpa.SUBSECTIONS)}개 중 대상 {stot}개, "
          f"{sub[nfpa.DONE]}/{stot} = {sub[nfpa.DONE] / stot * 100:.0f}%")

    import audit
    un = audit.unreviewed(g)
    import domestic
    dn, dins = domestic.counts()
    print("\n── 국내 공식 분류 (실무Ⅳ 표 2-1) 이식률 " + "─" * 21)
    print(f"  갈래 {len(domestic.BRANCHES)}개 중 범위 내 {dins}개")
    print(f"  구현 {dn[domestic.DONE]}  일부 {dn[domestic.PART]}  "
          f"없음 {dn[domestic.NONE]}  범위밖 {dn[domestic.OUT]}")
    print(f"  이식률 {dn[domestic.DONE]}/{dins} = {dn[domestic.DONE] / dins * 100:.0f}%")

    print("\n── 형태 발현 편향 점검 " + "─" * 38)
    print(f"  손상 양상 {len(dp)}개(직속) / 판정 {len(audit.VERDICTS)}건 / 미검토 {len(un)}건")
    print(f"  판정과 선언의 불일치 {len(audit.inconsistent(g))}건")

    sys.path.insert(0, str(ROOT / "tests"))
    import test_completeness as tc
    print("\n── 완성도 래칫 " + "─" * 45)
    if tc.BASELINE:
        for key, (limit, target) in tc.BASELINE.items():
            print(f"  {key:32s} {limit:>3d} → 목표 {target}")
    else:
        print("  남은 항목 없음. 세던 미완성 8개가 전부 불변식으로 옮겨졌다")

    base = ROOT / "cases" / "baseline.json"
    if base.exists():
        b = json.loads(base.read_text(encoding="utf-8"))
        print("\n── 정확도 (사례 %d건) " % b["cases"] + "─" * 38)
        print(f"  전체        {b['accuracy']*100:5.1f}%   "
              f"오판 {b['wrong']/b['cases']*100:.1f}%  미상 {b['undetermined']/b['cases']*100:.1f}%")
        print(f"  답한 것 중   {b.get('accuracy_when_answered',0)*100:5.1f}%   판단보류 제외")
        print(f"  상한        {b.get('ceiling',0)*100:5.1f}%   조사서에 자기 요인 단서가 있는 사례")
        for k, v in sorted(b["per_class"].items(), key=lambda x: -x[1]["correct"] / x[1]["n"]):
            gap = (v.get("ceiling", v["n"]) - v["correct"]) / v["n"] * 100
            print(f"    {k:8s} {v['correct']/v['n']*100:5.1f}%  상한 {v.get('ceiling',0)/v['n']*100:5.1f}%"
                  f"  남은거리 {gap:4.1f}%p")

    print("\n── 검증되지 않은 것 " + "─" * 41)
    print("  가감점은 검증만 했다. 보정하지 않았다 — make calibrate")
    print("  DL 일관성(V1)은 통과 — make reason")
    print("  조사관 검토표 회수 전")


if __name__ == "__main__":
    main()
