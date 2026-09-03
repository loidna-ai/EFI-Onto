# -*- coding: utf-8 -*-
"""절을 주제로 다시 묶는다 (재편 2단계). 한 번만 쓴다.

TTL 이 주제가 아니라 작업 순서로 쌓여 있었다. 같은 가설의 정의가 6절·33절·48절에
흩어져 있고, 절 제목이 '원인 축 편향 교정 2차'처럼 고친 기록인 곳이 여럿이다.

**의미를 바꾸지 않는다.** 블록을 옮기기만 하고 다시 쓰지 않는다. 끝나면
`make iso` 가 동형이어야 한다. 중복 선언과 어긋난 주석은 여기서 고치지 않고
목록만 낸다 — 옮기는 것과 고치는 것을 섞으면 무엇이 무엇을 바꿨는지 알 수 없다.

  python scripts/reorg.py            분류만 해서 보여준다 (파일을 안 건드린다)
  python scripts/reorg.py --write    실제로 옮긴다
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import pathlib, re, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import ttlblocks as tb
from efi_schema import load_graph
from rdflib import RDF, RDFS, OWL, URIRef, Namespace
from rdflib.collection import Collection

ROOT = pathlib.Path(__file__).resolve().parents[1]
TBOX = ROOT / "ontology" / "efi_tbox.ttl"
CHANGELOG = ROOT / "docs" / "TBox_절_이력.md"
E = Namespace("https://w3id.org/efi-onto#")
SH = Namespace("http://www.w3.org/ns/shacl#")
ln = lambda u: str(u).rsplit("#", 1)[-1].rsplit("/", 1)[-1]   # OBO·PROV 는 # 이 없다

# 절 제목 배너. 작업 순서의 흔적이라 옮길 때 버리고 이력 문서로 보낸다.
BANNER = re.compile(r"^[ \t]*#[ \t]*={10,}[ \t]*\n(?:^[ \t]*#.*\n)*?^[ \t]*#[ \t]*={10,}[ \t]*\n", re.M)

SCENARIOS = [
    ("PoorContactScenario", "접촉불량"), ("CrushDamageScenario", "압착손상"),
    ("PartialDisconnectionScenario", "반단선"), ("InsulationDegradationScenario", "절연열화"),
    ("TrackingScenario", "트래킹"), ("ExternalFlameScenario", "외부화염"),
    ("OverloadScenario", "과부하·과전류"), ("GroundFaultScenario", "누전·지락"),
    ("InterTurnShortScenario", "층간단락"),
]

SECTIONS = [
    ("0", "머리말 · 접두어", "접두어 선언과 owl:Ontology. 순서가 뜻을 갖는 유일한 자리다"),
    ("1", "바탕 — 상위 정렬과 보조 축", "BFO 2.0 정렬, 관측(SOSA)·출처(PROV-O)·시간(OWL-Time), "
                                    "조사 세션과 상태 열거. 네 축이 기대는 바닥이다"),
    ("2", "축 ① 발열 메커니즘", "무엇이 뜨거워지는 과정인가. 정의 메커니즘 열둘은 서로소다"),
    ("3", "축 ② 물리 증거물 · 손상 양상", "사진과 실물에서 읽는 것. 현장 사실과 섞이면 안 된다"),
    ("4", "축 ③ 선행 조건", "현장에서 확인하는 사실. 필요조건으로만 가설에 붙는다"),
    ("5", "축 ④ 최초 착화물", "무엇에 처음 불이 붙었는가"),
    ("6", "속성", "축 사이를 잇는 객체 속성과 물리 수치의 데이터 속성"),
    ("7", "가설 공통", "아홉 가설에 함께 걸리는 공리. 가설은 서로소다"),
    *[(f"7.{i+1}", f"가설 — {ko}", "정의(≡) · 필요조건(⊑) · 형태 발현 · 지표 규칙 · 전용 도출")
      for i, (_, ko) in enumerate(SCENARIOS)],
    ("8", "방법론 층 — 판정 절차", "NFPA 921 의 절차를 옮긴 어휘와 도형. M 변별력 · F 판정 · "
                                "C 결론 제약 · D 도출. 실행 순서는 파일 순서가 아니라 sh:order 가 정한다"),
    ("9", "미분류", "여기 남으면 분류표가 모자란 것이다. 비어 있어야 정상"),
]

AXIS = {"HeatingMechanism": "2", "PhysicalEvidence": "3", "DamagePattern": "3",
        "AntecedentCondition": "4", "FirstFuelIgnited": "5"}
# 네 축 밖의 바탕 어휘가 매달리는 상위. 관측·행위자·활동·사건·상태가 여기 온다.
BASE = {"Observation", "SceneEvidence", "Agent", "SoftwareAgent", "Sensor", "Activity",
        "InvestigationSession", "IgnitionScenario", "Conclusion", "IndicatorRule",
        "IndicatorRole", "ConfirmationStatus", "Verdict", "Instrument", "VerificationQuery",
        "Ignitability", "ArcMapPoint", "TemporalEntity", "BFO_0000015", "Entity",
        "ClassificationSystem", "InvestigationRecord", "ObservableProperty"}
# NFPA 절차가 쓰는 정보 산출물 — 분류·검토·보고서·추론 근거. 도형과 같은 층이다.
METHOD_BASE = {"IAO_0000030", "CertaintyLevel"}


class Classifier:
    def __init__(self):
        self.g = load_graph()
        self.sc_index = {s: f"7.{i+1}" for i, (s, _) in enumerate(SCENARIOS)}

    def _ancestors(self, u):
        """상위를 따라 올라간다. 부모를 owl:equivalentClass 의 교집합으로 다는 곳도 있다."""
        seen, stack = set(), [u]
        while stack:
            x = stack.pop()
            parents = list(self.g.objects(x, RDFS.subClassOf))
            for eq in self.g.objects(x, OWL.equivalentClass):
                for inter in self.g.objects(eq, OWL.intersectionOf):
                    parents += list(Collection(self.g, inter))
            for a in parents:
                if a not in seen:
                    seen.add(a)
                    stack.append(a)
        return {ln(a) for a in seen if isinstance(a, URIRef)}

    def _blob(self, u):
        """도형이 언급하는 이름 전부. 빈 노드 안의 SPARQL 까지 훑는다."""
        out, stack, seen = [], [u], set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            for p, o in self.g.predicate_objects(x):
                out.append(str(o))
                if not isinstance(o, URIRef) or o != u:
                    stack.append(o)
        return " ".join(out)

    def _shape_section(self, u):
        """한 가설만 언급하는 도형은 그 가설로, 나머지는 방법론 층으로."""
        blob = self._blob(u)
        hits = {s for s in self.sc_index if s in blob}
        return self.sc_index[next(iter(hits))] if len(hits) == 1 else "8"

    def _class_section(self, u):
        if ln(u) in self.sc_index:
            return self.sc_index[ln(u)]
        anc = self._ancestors(u) | {ln(u)}
        if anc & set(self.sc_index):
            return self.sc_index[next(iter(anc & set(self.sc_index)))]
        for k, v in AXIS.items():
            if k in anc:
                return v
        if anc & METHOD_BASE:
            return "8"
        if anc & BASE:
            return "1"
        return None

    def anonymous(self, block):
        """주어가 빈 노드인 블록(배타 공리)은 구성원이 사는 자리로 간다."""
        names = set(re.findall(r"efi:(\w+)", block))
        homes = {self._class_section(E[n]) for n in names} - {None}
        if not homes:
            return "1"
        if len(homes) == 1:
            return homes.pop()
        return "7" if all(h.startswith("7") for h in homes) else "1"

    def of(self, block):
        s = tb.subject(block)
        if s is None:
            if "@prefix" in block:
                return "0"
            return self.anonymous(block) if "owl:" in block or "efi:" in block else None
        u = E[s.split(":", 1)[1]] if s.startswith("efi:") else URIRef(s.strip("<>"))
        types = {ln(t) for t in self.g.objects(u, RDF.type)}
        if "Ontology" in types:
            return "0"
        if ln(u) in self.sc_index:
            return self.sc_index[ln(u)]
        if "IndicatorRule" in types:
            for sc in self.g.objects(u, E.forScenario):
                if ln(sc) in self.sc_index:
                    return self.sc_index[ln(sc)]
            return "8"
        if "NodeShape" in types:
            return self._shape_section(u)
        if types & {"ObjectProperty", "DatatypeProperty", "AnnotationProperty"}:
            return "6"
        if "NFPAClause" in types:
            return "8"
        if "NamedIndividual" in types or "Class" not in types:
            # 개체는 자기 타입 클래스가 가는 자리로 간다 (분류체계·확신도·검증수단…)
            for t2 in self.g.objects(u, RDF.type):
                if isinstance(t2, URIRef) and ln(t2) not in ("NamedIndividual",):
                    got = self._class_section(t2)
                    if got:
                        return got
        return self._class_section(u) or "9"


def strip_banner(block):
    """절 제목 배너를 떼고 (본문, 배너들) 로 낸다."""
    return BANNER.sub("", block), list(BANNER.finditer(block))


FENCE = "# " + "=" * 74


def banner(key, title, note):
    lines = [FENCE, f"# [{key}] {title}"]
    for i in range(0, len(note), 70):
        lines.append("#   " + note[i:i + 70].strip())
    lines.append(FENCE)
    return "\n".join(lines) + "\n"


HEAD = """# ==========================================================================
#  EFI-Onto : Electrical Fire Ignition Ontology — TBox
#  전기화재 발화 메커니즘 판정 온톨로지 (FIReAct 연계용)
#  표현 : OWL 2 DL (Turtle) + SHACL Advanced(규칙) + SKOS(용어 정렬)
#  방법론: Noy & McGuinness, Ontology Development 101 (Stanford KSL-01-05)
#  정렬  : BFO 2.0 · RO · SOSA/SSN · PROV-O · OWL-Time · QUDT
#  주의  : 지지점수(supportScore)는 확률이 아니며 퍼센트 기호 없이 0~100 정수다 (논문 3.2절)
#
#  절은 주제로 묶여 있고 번호는 순서가 아니라 자리다. 앵커는 `# [7.3]` 꼴이며
#  문서·backlog 가 이 문자열로 가리킨다. 재편 전의 절 제목은 docs/TBox_절_이력.md.
#  조사 기록 층은 efi_investigation.ttl 에 있고 둘이 한 그래프다.
#  **규칙의 실행 순서는 파일 순서가 아니라 sh:order 가 정한다** — 블록을 옮겨도
#  판정은 안 바뀐다(재편 0단계에서 증명). 옮겼으면 make iso 로 동형을 확인한다.
# ==========================================================================
"""


def run(write=False):
    blocks = tb.cut(TBOX.read_text(encoding="utf-8"))
    c = Classifier()
    buckets = collections.OrderedDict((k, []) for k, _, _ in SECTIONS)
    history = []
    for b in blocks:
        body, found = strip_banner(b)
        history += [m.group(0) for m in found]
        if not body.strip():
            continue
        buckets[c.of(body) or "0"].append(body)

    for k, _, _ in SECTIONS:
        print(f"  {k:5} {len(buckets[k]):4}")
    if buckets["9"]:
        print("\n미분류:")
        for b in buckets["9"]:
            print("   ", tb.subject(b))
        return buckets, history

    dup = collections.Counter(tb.subject(b) for bl in buckets.values() for b in bl if tb.subject(b))
    dup = {k: v for k, v in dup.items() if v > 1}
    print(f"\n같은 주어가 여러 블록에 흩어진 것 {len(dup)}개 (블록 {sum(dup.values())}). 3단계에서 합친다")

    if not write:
        print("\n(분류만 했다. 실제로 옮기려면 --write)")
        return buckets, history

    out = [HEAD] + list(buckets["0"])
    for k, title, note in SECTIONS:
        if k == "0" or not buckets[k]:
            continue
        out.append("\n" + banner(k, title, note))
        out += buckets[k]
    TBOX.write_text(tb.join(out), encoding="utf-8", newline="\n")
    _write_history(history, dup)
    print(f"\n{TBOX.name} 을 다시 썼다. make iso 로 확인할 것")
    return buckets, history


def _write_history(banners, dup):
    """버린 절 제목과 3단계로 넘길 중복 목록을 남긴다."""
    out = ["# TBox 절 이력 — 재편 전의 절 제목과 남은 정리거리", "",
           "재편 2단계에서 TTL 의 절 제목을 주제 기준으로 바꿨다. 이전 절 제목은 작업 순서와",
           "고친 기록이었다 — '원인 축 편향 교정 2차', '사슬에 안 붙어 있던 어휘 셋을 붙인다'",
           "같은 것들이다. TTL 에서는 사라졌지만 왜 그 어휘가 생겼는지는 남아야 하므로 옮겨 둔다.",
           "", "## 재편 전 절 제목", ""]
    for b in banners:
        for line in b.strip().split("\n"):
            s = line.lstrip("#").strip()
            if s and set(s) - set("= "):
                out.append(("- " if re.match(r"^\d+\.", s) else "  ") + s)
    out += ["", "## 같은 주어가 여러 블록에 흩어진 것 — 3단계에서 합친다", "",
            "재편으로 한자리에 모였다. 합치면서 서로 어긋난 주석이 드러날 수 있다.",
            "**2단계에서 고치지 않았다** — 옮기는 것과 고치는 것을 섞으면 무엇이 무엇을",
            "바꿨는지 알 수 없다. 2단계는 동형이어야 한다.", "",
            "| 주어 | 블록 수 |", "|---|---:|"]
    for k, v in sorted(dup.items(), key=lambda x: (-x[1], x[0])):
        out.append(f"| `{k}` | {v} |")
    CHANGELOG.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    run("--write" in sys.argv)
