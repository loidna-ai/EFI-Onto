# -*- coding: utf-8 -*-
"""OWL 2 DL 일관성 검사 (설계계획서 V1). HermiT 로 불만족 클래스를 찾는다.

왜 필요한가
  pySHACL 은 OWL DL 일관성을 검사하지 않는다. 정의 클래스(owl:equivalentClass)와
  축 배타 공리(owl:AllDisjointClasses)가 계속 늘어난 동안 이 검사는 한 번도
  돌지 않았다. 불만족 클래스가 생겨도 회귀 시험은 전부 통과한다.

무엇을 잡는가
  불만족(unsatisfiable) 클래스 — 정의상 어떤 개체도 그 클래스의 인스턴스가 될 수
  없는 상태. 축이 서로소인데 두 축에 걸치는 제약을 걸면 이렇게 된다.

주의
  owl:imports 를 떼고 검사한다. BFO·SOSA·PROV-O 원본을 내려받지 않는다는 뜻이며,
  상위 온톨로지가 부과하는 공리는 이 검사에 반영되지 않는다. 우리가 쓴 공리끼리의
  모순만 본다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import sys, os, pathlib, tempfile, subprocess
from rdflib import Graph, Namespace, OWL, RDF

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
SH = Namespace("http://www.w3.org/ns/shacl#")


def _rdfxml_without_imports(ttl=None):
    """HermiT 은 Turtle 을 읽지 않는다. imports 를 떼고 RDF/XML 로 바꾼다."""
    g = Graph().parse(ttl or TTL, format="turtle")
    for s, p, o in list(g.triples((None, OWL.imports, None))):
        g.remove((s, p, o))
    # SHACL 삼중항은 DL 추론 대상이 아니다. 빼서 추론기 부담을 줄인다.
    for s in set(g.subjects(RDF.type, SH.NodeShape)):
        g.remove((s, None, None))
    f = tempfile.NamedTemporaryFile(suffix=".owl", delete=False, mode="wb")
    f.write(g.serialize(format="xml").encode("utf-8"))
    f.close()
    return f.name


def _hermit_cmd():
    import owlready2, shutil
    h = pathlib.Path(owlready2.__file__).parent / "hermit"
    java = shutil.which("java")
    if not java:
        raise RuntimeError("java 를 찾지 못했다. HermiT 은 Java 가 있어야 돈다.")
    return [java, "-cp", f"{h}{os.pathsep}{h / 'HermiT.jar'}",
            "org.semanticweb.HermiT.cli.CommandLine"]


def check(ttl=None):
    """(불만족 클래스 목록, 전역 모순 여부, 메시지).

    owlready2 0.51 의 sync_reasoner_hermit 은 내부 버그로 죽는다(_save 가
    commit 인자를 받지 않는다). 번들된 HermiT 을 직접 부른다.
    """
    iri = pathlib.Path(_rdfxml_without_imports(ttl)).as_uri()
    cmd = _hermit_cmd()
    k = subprocess.run(cmd + ["-k", iri], capture_output=True, text=True, timeout=900)
    out = ((k.stdout or "") + (k.stderr or "")).strip()
    low = out.lower()
    # HermiT 은 owl:Thing 의 충족 가능성으로 답한다. Thing 이 불충족이면 전역 모순이다.
    if "not satisfiable" in low or "unsatisfiable" in low:
        return [], True, out[:600]
    # 검사가 실제로 돌았는지 확인한다. 사용법만 출력하고 0 으로 끝나는 경우가 있었다.
    if k.returncode != 0 or "is satisfiable" not in low:
        raise RuntimeError("HermiT 이 일관성 판정을 내지 않았다:\n" + out[:600])
    u = subprocess.run(cmd + ["-U", iri], capture_output=True, text=True, timeout=900)
    # 출력은 머리글 한 줄 뒤에 들여쓴 클래스 이름이 이어진다.
    #   Classes equivalent to 'owl:Nothing':
    #       owl:Nothing
    #       :DeliberatelyBroken
    lines = (u.stdout or "").splitlines()
    if not any("owl:Nothing" in l for l in lines):
        raise RuntimeError("HermiT 이 불만족 클래스 목록을 내지 않았다:\n"
                           + ((u.stdout or "") + (u.stderr or ""))[:600])
    bad = []
    for line in lines:
        if not line[:1].isspace():
            continue
        name = line.strip().lstrip("<").rstrip(">").split("#")[-1].lstrip(":")
        if name and name != "owl:Nothing" and name != "Nothing":
            bad.append(name)
    return bad, False, (u.stderr or "").strip()[:400]


if __name__ == "__main__":
    bad, inconsistent, msg = check()
    if inconsistent:
        print("온톨로지 전체가 모순이다. 어떤 해석도 존재하지 않는다.")
        print(msg)
        sys.exit(1)
    if msg and not bad:
        print(msg)
    if bad:
        print(f"불만족 클래스 {len(bad)}개 — 어떤 개체도 이 클래스가 될 수 없다")
        for c in bad:
            print("  ", c)
        sys.exit(1)
    print("불만족 클래스 0개. DL 일관성 통과 (V1).")
