# -*- coding: utf-8 -*-
"""가감점을 온톨로지 구조에서 유도한다. 사람이 값을 고르지 않는다.

왜 유도하는가
  조사관마다 중요도 판단이 갈린다. 순위를 모아 평균을 내면 아무도 동의하지 않는 값이
  남는다. 그래서 개별 값을 정하지 않고 값을 만드는 규칙을 정한다. 규칙이 틀렸다는
  반론은 가능하지만 취향 다툼은 생기지 않는다.

무엇에서 유도하는가 — 변별력
  단서의 가치는 가설 공간을 얼마나 좁히느냐다. 6개 가설 중 k개와 양립하는 단서를
  관측하면 log2(6/k) 만큼 좁혀진다. k=1 이면 최대, k=6 이면 0 이다.
  피복 탄화처럼 6개 전부가 낼 수 있는 흔적은 가중치가 0 이 된다 —
  C-5(공유 형태만으로 확정 불가)가 제약이 아니라 계산 결과로 나온다.

척도는 어디서 오는가 — 확정 조건에서
  확정선은 70점, 기준선은 50점, 확정에는 최소 2건의 긍정 사실이 필요하다(3.2절).
    · 단서 하나로 확정되면 안 된다      50 + x < 70   →  x < 20
    · 단서 둘이면 확정에 닿아야 한다    50 + 2x >= 70  →  x >= 10
  10 <= x < 20 에서 최대 지지점을 15로 둔다.
    · 최대 반증 하나는 확정 요건을 갖춘 가설(50+15+15=80)을 기준선으로 되돌려야 한다
      80 - y = 50  →  y = 30
  즉 15와 30은 고른 값이 아니라 확정 조건에서 풀려나온 값이다.

형태학적 특징에 붙는 감쇠 0.7
  이것만은 유도가 아니라 판단이다. 사진 판독은 오독이 가능하고 현장 확인 사실과
  같은 무게를 줄 수 없다는 P1·논문 4.2의 취지를 계수로 옮긴 것이다.
  근거를 바꾸려면 이 상수만 바꾼다.
"""
import math, sys, io, re, collections, pathlib
from rdflib import Graph, Namespace, RDF, RDFS, URIRef

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
E = Namespace("https://w3id.org/efi-onto#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ln = lambda u: str(u).split("#")[-1]

SUPPORT_MAX = 15      # 확정 조건에서 유도 (10 <= x < 20)
REFUTE_MAX = 30       # 확정 요건을 갖춘 가설을 기준선으로 되돌리는 값
MORPHOLOGY_FACTOR = 0.7   # 판단. 사진 판독은 현장 확인과 같은 무게가 아니다
DECISIVE = -100       # 비통전. 점수가 아니라 차단기다

def _scenarios():
    """가설 목록을 TTL 에서 읽는다. 손으로 들고 있으면 시나리오가 늘 때 어긋나고,
    변별력 공식의 N 이 조용히 틀린 값이 된다."""
    g = Graph().parse(TTL, format="turtle")
    out = set()

    def walk(c):
        for s in g.subjects(RDFS.subClassOf, c):
            if isinstance(s, URIRef):
                n = ln(s)
                if n not in out:
                    if not list(g.subjects(RDFS.subClassOf, s)):   # 추상 상위는 뺀다
                        out.add(n)
                    walk(s)
    walk(E.IgnitionScenario)
    return sorted(out)


SCENARIOS = _scenarios()
ELECTRICAL = [s for s in SCENARIOS if s != "ExternalFlameScenario"]
N = len(SCENARIOS)


def _subclasses(g, name):
    out = {name}
    for s in g.subjects(RDFS.subClassOf, E[name]):
        if isinstance(s, URIRef):
            out |= _subclasses(g, ln(s))
    return out


def _ancestors(g, c, seen=None):
    seen = set() if seen is None else seen
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, URIRef) and p not in seen:
            seen.add(p)
            _ancestors(g, p, seen)
    return {ln(x) for x in seen}


def compatibility(g):
    """지표 → 양립 가능한 가설 집합. 선언된 인과 사슬만 따라간다."""
    mech = collections.defaultdict(set)
    for s, o in g.subject_objects(E.hasDeclaredMechanism):
        mech[ln(s)].add(ln(o))
    enables = collections.defaultdict(set)
    for s, o in g.subject_objects(E.enables):
        enables[ln(s)].add(ln(o))

    compat = collections.defaultdict(set)
    for sc in SCENARIOS:
        for d in g.objects(E[sc], E.canManifest):           # 가설 → 손상 양상
            compat[ln(d)].add(sc)
        for ante, ms in enables.items():                    # 선행조건 → 발열 → 가설
            if ms & mech.get(sc, set()):
                for a in _subclasses(g, ante):
                    compat[a].add(sc)
    for ev, ants in ((ln(s), {ln(o) for o in g.objects(s, E.attests)})
                     for s in set(g.subjects(E.attests, None))):
        for a in ants:                                      # 현장사실 → 선행조건 → 가설
            compat[ev] |= compat.get(a, set())

    # 지표가 상위 클래스이면 하위 어느 것이 관측돼도 그 지표에 걸린다(subsumption).
    # 그러므로 지표의 양립 범위는 하위 전체의 합집합이다. 자기 선언만 읽으면
    # 오염 환경처럼 하위가 넓어진 상위가 계속 전용으로 남아 과대평가된다.
    # 선언(enables)은 여전히 상위→하위 상속이다 — 방향이 반대인 두 읽기다.
    for c in list(compat):
        for k in _subclasses(g, c):
            compat[c] |= compat.get(k, set())
    return compat


def rules(g):
    for r in sorted(g.subjects(RDF.type, E.IndicatorRule), key=str):
        yield (ln(r), ln(g.value(r, E.forScenario)), ln(g.value(r, E.indicates)),
               ln(g.value(r, E.hasRole)))


def deltas(g=None):
    """규칙 이름 → 가감점. TTL 이 아니라 이 함수가 가중치의 단일 진실 원천이다."""
    g = g or Graph().parse(TTL, format="turtle")
    compat = compatibility(g)
    # 대체 근거. 인과 사슬이 없는 지표는 규칙 자체에서 k 를 얻는다. 부재 증거
    # (아크·스패터 부재, 트립 이력 없음, 절연저항 정상)는 어떤 가설과도 양립하지
    # 않는 것이 정상이라 사슬이 없는 편이 맞다. 다만 긍정 단서가 여기 걸리면
    # 가중치 근거가 구조가 아니라 규칙 집합이 되므로 약하다.
    # 현재 이 경로를 쓰는 긍정 단서: 비정상 온도·전압강하, 누전차단기 간헐 동작,
    # 1차 단락흔, 아크·스패터 부재.
    positive = collections.defaultdict(set)
    for _, sc, ind, role in rules(g):
        if role in ("Core", "Supporting"):
            positive[ind] |= set(ELECTRICAL if sc == "ElectricalIgnitionScenario" else [sc])

    out = {}
    for name, sc, ind, role in rules(g):
        if role == "DecisiveRefuting":
            out[name] = DECISIVE
            continue
        k = len(compat.get(ind, set())) or len(positive.get(ind, set())) or 1
        rel = math.log2(N / k) / math.log2(N)               # k=1 → 1.0, k=6 → 0.0
        axis = MORPHOLOGY_FACTOR if "DamagePattern" in _ancestors(g, E[ind]) else 1.0
        mx = -REFUTE_MAX if role == "Refuting" else SUPPORT_MAX
        out[name] = int(round(mx * rel * axis))
    return out


def write(g=None):
    """TTL 의 scoreDelta 를 계산값으로 덮어쓴다."""
    g = g or Graph().parse(TTL, format="turtle")
    d = deltas(g)
    s = io.open(TTL, encoding="utf-8").read()
    n = 0
    for name, v in d.items():
        pat = re.compile(rf"(efi:{name}\b(?:[^.]|\.\d)*?efi:scoreDelta\s+)(-?\d+)", re.S)
        s, c = pat.subn(lambda m: m.group(1) + str(v), s, count=1)
        n += c
    io.open(TTL, "w", encoding="utf-8", newline="\n").write(s)
    return n, len(d)


if __name__ == "__main__":
    g = Graph().parse(TTL, format="turtle")
    KO = {}
    for s, o in g.subject_objects(SKOS.prefLabel):
        KO.setdefault(ln(s), str(o))
    compat, d = compatibility(g), deltas(g)
    if "--write" in sys.argv:
        print("scoreDelta %d/%d 갱신" % write(g))
    else:
        print(f"{'규칙':18s} {'가설':10s} {'지표':26s} {'역할':10s} {'k':>2s} {'형태':>4s} {'점':>4s}")
        for name, sc, ind, role in sorted(rules(g), key=lambda r: (r[1], -abs(d[r[0]]))):
            k = len(compat.get(ind, set())) or "·"
            m = "예" if "DamagePattern" in _ancestors(g, E[ind]) else "-"
            print(f"{name:18s} {KO.get(sc,sc)[:10]:10s} {KO.get(ind,ind)[:26]:26s} "
                  f"{role:10s} {str(k):>2s} {m:>4s} {d[name]:>4d}")
