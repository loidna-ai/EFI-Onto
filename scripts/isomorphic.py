# -*- coding: utf-8 -*-
"""재편이 의미를 바꾸지 않았음을 증명한다.

절을 옮기고 파일을 나누는 작업의 유일한 완료 조건은 '그래프가 같다'이다.
줄 수도 파일 수도 아니다.

**rdflib 의 to_isomorphic 은 이 그래프에 쓰지 않는다.** 빈 노드가 932개이고
`sh:property [ sh:path …; sh:minCount 1 ]` 처럼 구조가 닮은 것이 많아
정규화가 수렴하지 못한다 — 블록 순서만 바꿔도 동형이 아니라고 답한다
(접지 트리플 4716개가 전부 같은데도). 그래서 여기서는 빈 노드마다
재귀 서명을 만들어 다중집합으로 비교한다. 이 그래프의 빈 노드는 명명 주어에
매달린 나무(owl:Restriction, sh:property, sh:rule, rdf 목록)라서 가능하다.

  python scripts/isomorphic.py --freeze    현재 그래프를 기준선으로 굳힌다
  python scripts/isomorphic.py             기준선과 비교한다. 다르면 어디가 다른지 낸다
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import json, pathlib, collections
from rdflib import Graph, BNode

ROOT = pathlib.Path(__file__).resolve().parents[1]
ONTO = ROOT / "ontology"
BASELINE = ROOT / "build" / "baseline.json"


def load(paths=None):
    """온톨로지 전체를 한 그래프로 읽는다. 파일이 몇 개든 그래프는 하나다."""
    g = Graph()
    for p in sorted(paths or ONTO.glob("*.ttl")):
        g.parse(p, format="turtle")
    return g


def _sig(g, node, seen=()):
    """빈 노드의 재귀 서명. 순서에 의존하지 않게 술어·목적어를 정렬한다."""
    if not isinstance(node, BNode):
        return node.n3()
    if node in seen:
        return "*"          # 순환. 이 온톨로지에는 없지만 방어한다
    seen = seen + (node,)
    parts = sorted(f"{p.n3()} {_sig(g, o, seen)}" for p, o in g.predicate_objects(node))
    return "[ " + " ; ".join(parts) + " ]"


def signature(g):
    """그래프의 순서 무관 서명. 트리플마다 한 문자열."""
    referenced = {o for _, _, o in g if isinstance(o, BNode)}
    out = collections.Counter()
    for s, p, o in g:
        if isinstance(s, BNode) and s in referenced:
            continue        # 부모 쪽 서명에 이미 들어간다
        out[f"{_sig(g, s)} {p.n3()} {_sig(g, o)}"] += 1
    return out


def freeze(g=None):
    g = g if g is not None else load()
    sig = signature(g)
    BASELINE.parent.mkdir(exist_ok=True)
    BASELINE.write_text(json.dumps(dict(sig), ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"기준선 트리플 {len(g)} · 서명 {sum(sig.values())} → {BASELINE.relative_to(ROOT).as_posix()}")


def compare(g=None, quiet=False):
    if not BASELINE.exists():
        print("기준선이 없다. --freeze 를 먼저 돌린다.")
        return 2
    a = collections.Counter(json.loads(BASELINE.read_text(encoding="utf-8")))
    g = g if g is not None else load()
    b = signature(g)
    if a == b:
        if not quiet:
            print(f"동형 — 트리플 {len(g)} · 서명 {sum(b.values())}")
        return 0
    lost, added = a - b, b - a
    print(f"동형 아님 — 기준선 서명 {sum(a.values())} 현재 {sum(b.values())}")
    print(f"  사라짐 {sum(lost.values())}   새로 생김 {sum(added.values())}")
    for label, part in (("사라짐", lost), ("새로 생김", added)):
        for line, n in list(part.items())[:12]:
            print(f"  [{label}] {line[:180]}")
    return 1


if __name__ == "__main__":
    sys.exit(freeze() or 0 if "--freeze" in sys.argv else compare())
