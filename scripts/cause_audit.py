# -*- coding: utf-8 -*-
"""선행 조건 사슬의 체계적 편향 점검. 형태 축 audit.py 의 원인 축 짝.

왜 필요한가
  audit.py 는 형태 축에서 '화재도 이 흔적을 내는가'를 묻는다. 원인 축에는 같은
  장치가 없었고, 그래서 같은 종류의 오류가 반복해서 들어왔다.

    진동을 반단선 전용으로 두었다   — §9.11.4.3 은 반복 압력이 고저항 접촉을
                                    만든다고 한다. 접촉불량이다.
    플러그 접속부를 반단선 전용으로  — 교재 같은 쪽에 "플러그 부분에서의 불완전
    두었다                          접촉으로 출화"가 있다.

  둘 다 원문이 'A도 되고 B도 된다'고 적은 것을 A 쪽으로만 이은 것이다.
  형태 축의 편향과 같은 종류다 — 변별하는 방향으로 읽으려는 편향.

질문
  이 선행 조건은 정말 그 요인에서만 일어나는가?
  아니라면 사슬을 넓혀야 한다. 넓히면 변별력이 떨어지지만 그것이 정확한 값이다.

상태
  EXCL    그 요인에서만 일어난다 — 사슬이 하나여야 한다
  SHARED  다른 요인도 일으킨다  — 사슬이 둘 이상이어야 한다
  OPEN    원문 근거 없음 — 조사관 검토 또는 추가 대조 필요

  '가리키는 힘이 세다'와 '거기서만 일어난다'는 다르다. 전자는 가중치의 문제이고
  이 파일이 묻는 것은 후자다. 자주 같이 나온다는 이유로 EXCL 을 주지 않는다.
"""
import sys, pathlib, collections
from rdflib import Graph, Namespace, RDFS, URIRef

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
sys.path.insert(0, str(ROOT / "scripts"))
E = Namespace("https://w3id.org/efi-onto#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ln = lambda u: str(u).split("#")[-1]

EXCL, SHARED, OPEN = "전용", "공유", "미검토"

# (선행 조건, 판정, 근거). 근거가 원문인 것만 판정한다.
VERDICTS = {
    # ── 정의상 그 요인 자체인 것 ─────────────────────────────────────
    "LooseConnection":        (EXCL, "접속부 체결 불량이 곧 접촉불량이다. 공식 분류가 '접촉불량에 의한 단락'이라 적는 그 원인"),
    "CorrodedConnection":     (EXCL, "실무Ⅳ p.206 접점부의 산화·환경오염에 의한 접촉불량. 접속부 현상이다"),
    "ExternalCrushing":       (EXCL, "표 2-1 코드의 바닥 깔림이 단락 아래에 있다. 눌림은 도체를 직접 상하게 한다"),
    "RodentGnawing":          (EXCL, "실무Ⅳ p.253 피복을 갉아 도체가 드러나 단락에 이른다. 기계적 손상 경로"),
    "ConductiveSolutionInCrack": (EXCL, "§9.11.3 균열에 도전성 용액이 들어가야 누설이 흐른다. 트래킹의 필요조건"),
    "ContaminatedEnvironment": (EXCL, "실무Ⅳ p.147 이극 도체 사이 절연물 표면에 도전성 물질이 부착해야 트래킹이 시작된다"),

    # ── 원문이 둘 이상을 적는 것 ────────────────────────────────────
    "MoistureExposure":       (SHARED, "실무Ⅳ p.245 '먼지나 습기 등에 의해 절연열화로 이어지는 경우'. 트래킹 전용이 아니다"),
    "DustAccumulation":       (SHARED, "실무Ⅳ p.246 '먼지 또는 분진 등이 누적되어 통풍·냉각 저해로 발열'. 방열 저해 경로가 따로 있다"),
    "RepeatedFlexing":        (SHARED, "표 2-1 은 '코드의 접히거나 굽혀짐'을 단락 아래 둔다. 굽힘은 반단선도 되고 기계적 손상 단락도 된다"),
    "Vibration":              (SHARED, "§9.11.4.3 반복 압력이 시간이 지나 고저항 접촉을 만든다"),
    "AbnormalTemperatureOrVoltageDrop": (SHARED, "저항이 커지면 무엇이든 국부 과열·전압강하를 낸다. 소선이 줄어도 그렇다"),
    "FlickeringOrOdor":       (SHARED, "실무Ⅳ p.149 반단선은 접촉·단속을 반복한다. 깜박임은 접촉불량 전용 징후가 아니다"),
    "IntermittentRcdTripping": (SHARED, "누설전류가 흐르면 동작한다. 실무Ⅳ p.155 절연열화로도 누설이 생긴다"),
    "AgedInsulation":         (SHARED, "노후 절연은 절연파괴 아크와 누설전류 발열 양쪽을 가능하게 한다"),
    "ThermalDegradation":     (SHARED, "AgedInsulation 과 같다. 열화된 절연은 두 경로 모두에 열려 있다"),
    "InsulationDeterioration": (SHARED, "노후·열열화의 상위. 하위가 공유이므로 상위도 공유다"),
    "ReducedInsulationResistance": (SHARED, "절연저항 저하는 절연열화의 계측 증거이자 트래킹 진행의 결과이기도 하다"),
    "PlugJunctionArea":       (SHARED, "실무Ⅳ p.253 같은 쪽에 '플러그 인접부분에서의 반단선'과 '플러그 부분에서의 불완전 접촉으로 출화'가 함께 있다"),
    "ApplianceEntryPoint":    (SHARED, "실무Ⅳ p.204 관통부는 꺾임(반단선)과 마찰·눌림(기계적 손상)이 함께 일어나는 자리다"),
    "MisdrivenStaple":        (SHARED, "표 2-1 은 스테이플 찔림을 단락에 두고 실무Ⅳ p.245 는 같은 자리에서 반단선이 관찰된다고 한다"),
    "StressConcentrationPoint": (SHARED, "하위가 모두 공유다. 위치는 요인을 가르지 않는다"),

    # ── 아직 근거를 찾지 못한 것 ────────────────────────────────────
    # 지어내지 않는다. 원문을 더 받거나 조사관 검토로 닫는다.
}

def _subclasses(g, c, out=None):
    out = set() if out is None else out
    for s in g.subjects(RDFS.subClassOf, c):
        if isinstance(s, URIRef) and ln(s) not in out:
            out.add(ln(s)); _subclasses(g, s, out)
    return out


def reach(g=None):
    """선행 조건 → 닿는 가설 집합. 사슬을 그대로 따라간다."""
    import score
    g = g or Graph().parse(TTL, format="turtle")
    comp = score.compatibility(g)
    out = {}
    for a in sorted(_subclasses(g, E.AntecedentCondition)):
        v = {ln(x) for x in comp.get(a, set())}
        if v:                                   # 어디에도 안 닿는 것은 lint 의 몫
            out[a] = v
    return out


def unreviewed(g=None):
    return sorted(a for a in reach(g) if a not in VERDICTS)


def inconsistent(g=None):
    """판정과 사슬이 어긋난 것. 판정만 적고 사슬을 안 고치면 아무 일도 안 일어난다."""
    bad = []
    for a, scs in reach(g).items():
        v = VERDICTS.get(a)
        if not v:
            continue
        if v[0] == EXCL and len(scs) > 1:
            bad.append((a, "전용이라 했는데 사슬이 여럿에 닿는다", sorted(scs)))
        if v[0] == SHARED and len(scs) == 1:
            bad.append((a, "공유라 했는데 사슬이 하나뿐이다 — 넓혀야 한다", sorted(scs)))
    return bad


if __name__ == "__main__":
    g = Graph().parse(TTL, format="turtle")
    r = reach(g)
    lab = {a: str(g.value(E[a], SKOS.prefLabel) or a) for a in r}
    n = collections.Counter(VERDICTS.get(a, (OPEN,))[0] for a in r)
    print(f"선행 조건 {len(r)}개 — 전용 {n[EXCL]} / 공유 {n[SHARED]} / 미검토 {n[OPEN]}\n")
    for a in sorted(r, key=lambda x: (VERDICTS.get(x, (OPEN,))[0], x)):
        v, basis = VERDICTS.get(a, (OPEN, ""))
        mark = {EXCL: "■", SHARED: "△", OPEN: "?"}[v]
        scs = sorted(s.replace("Scenario", "") for s in r[a])
        print(f"  {mark} {v:4s} {lab[a][:22]:24s} {scs}")
        if basis:
            for i in range(0, len(basis), 70):
                print(f"           {basis[i:i+70]}")
    bad = inconsistent(g)
    print(f"\n판정과 사슬의 불일치: {len(bad)}건")
    for a, why, scs in bad:
        print(f"   {a:30s} {why} {scs}")
