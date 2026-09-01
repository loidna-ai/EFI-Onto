# -*- coding: utf-8 -*-
"""형태 발현 선언의 체계적 편향 점검.

왜 필요한가
  이 온톨로지는 '이 가설이 이 흔적을 낸다'는 방향으로만 지어졌다. 반대 방향,
  곧 '화재 자체가 이 흔적을 낸다'는 거의 담기지 않았다. 그 결과 전용 단서가
  실제보다 많아 보였고 변별력이 과대평가됐다.

  NFPA 921 원문 대조로 세 건이 드러났다 — 탄화 도전로(§9.9.4.5), 다발성 아크
  비드(§9.10.2), 종이·목재 묶음(§9.9.4.1). 셋 다 같은 오류다. 남은 선언에도
  같은 오류가 있을 것으로 보고 전부에 같은 질문을 던진다.

질문
  이 손상 양상을 화재 자체가 만들 수 있는가?
  그렇다면 그 양상은 전기적 가설의 전용 단서가 될 수 없다.

상태
  FIRE   화재도 낸다 — 외부화염 시나리오에 포함돼 있어야 한다
  ELEC   화재는 내지 못한다 — 전기적 가설의 단서로 유지
  OPEN   원문 근거 없음 — 조사관 검토 또는 추가 조항 필요

남은 OPEN
  BurnCenterOnSurface — 절연물 표면에 소손이 집중되는 양상. 트래킹 특유로 보이나
  화재가 같은 양상을 못 낸다는 원문 근거를 찾지 못했다. 지어내지 않고 남긴다.
  검토표 7번 시트로 조사관에게 나가 있다.
"""
import sys, pathlib, collections
from rdflib import Graph, Namespace, RDFS, URIRef

ROOT = pathlib.Path(__file__).resolve().parents[1]
TTL = ROOT / "ontology" / "efi_tbox.ttl"
E = Namespace("https://w3id.org/efi-onto#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ln = lambda u: str(u).split("#")[-1]

FIRE, ELEC, OPEN = "화재도냄", "전기전용", "미검토"

# (양상, 판정, 근거). 근거가 원문 조항인 것만 판정한다.
VERDICTS = {
    # 화재가 만드는 것 — 원문 근거 있음
    "InsulationCarbonization":     (FIRE, "§9.10.2 화재 열이 피복을 탄화시킨다"),
    "CarbonizedConductivePath":    (FIRE, "§9.9.4.5 비전기적 열로도 탄화된다"),
    "MultipleArcBeads":            (FIRE, "§9.10.2 탄화를 통한 아크는 여러 지점에 남는다"),
    "ArcMeltMark":                 (FIRE, "§9.10.1 화재로 연화된 피복이 단락 파팅 아크를 만든다"),
    "ArcBead":                     (FIRE, "§9.10.1·§9.10.2 화재 유발 아크도 비드를 남긴다"),
    "SecondaryArcMark":            (FIRE, "정의상 화재 이후 형성"),
    "LargeMeltMark":               (FIRE, "이미 외부화염 포함"),
    "GeneralMelting":              (FIRE, "외부화염 고유"),
    "Sagging":                     (FIRE, "외부화염 고유"),
    "ThermalGradientFlow":         (FIRE, "외부화염 고유"),
    "FireMeltMark":                (FIRE, "외부화염 고유"),
    "LocalizedDiscoloration":      (FIRE, "§9.10.3.1(1) 화재 노출만으로도 금속이 산화된다"),
    "LossOfLuster":                (FIRE, "§9.10.3.1(1) 화재 산화로 표면 광택이 사라진다"),
    "InsulationEmbrittlement":     (FIRE, "§9.11.3 절연은 노후와 가열로 취화된다. 화재 열도 가열이다"),
    "CrackedInsulation":           (FIRE, "§9.11.3 취화된 절연은 갈라진다"),
    "MetalTransferToFastener":     (FIRE, "§9.11.4.3 진행 중인 화재의 결과일 수 있다"),
    "MeltMark":                    (FIRE, "FireMeltMark 가 하위 클래스다. 화재 용융흔이 여기 속한다"),
    "Spatter":                     (FIRE, "§9.9.5 스패터는 아크가 던진 입자다. §9.10.1 화재도 아크를 만든다"),
    "StrandFracture":              (FIRE, "§9.10.2 화재 탄화를 통한 아크가 도체를 여러 토막으로 끊는다"),
    "SmallMeltBallOnStrandEnd":    (FIRE, "§9.10.2·§9.10.4.1 용융으로 끊긴 끝단에 생긴다"),
    # 화재가 만들지 못하는 것 — 원문 근거 있음
    "MechanicalDeformation":       (ELEC, "§9.10.5 기계적 손상은 아크·열손상과 구별된다"),
    "WholeConductorCrushedOrCut":  (ELEC, "§9.10.5 기계적 손상"),
    "MechanicalGouge":             (ELEC, "§9.10.5 긁힘 자국과 변형, 융착면 부재"),
    "MoltenOxideMass":             (ELEC, "§9.10.3.3 외부 화재 노출과 외관상 구별된다"),
    "EnlargedScrewHeadOxidation":  (ELEC, "§9.10.3.3 외부 화재 노출과 외관상 구별된다"),
    "OxideBanding":                (ELEC, "§9.10.3.1(12) 필라멘트 이동 흔적"),
    "CuprousOxideGrowth":          (ELEC, "§9.10.3 발광 접속부의 산화물 생성"),
    "PrimaryArcMark":              (ELEC, "정의상 화재 이전 형성"),
    "Sleeving":                    (ELEC, "§9.10.4.1 과부하 구간 전 길이의 내부 발열"),
    "MeltOffset":                  (ELEC, "§9.10.4.1 회로가 열리는 순간 굳은 형태"),
    "StrandFractureAtStressPoint": (ELEC, "§9.10.5 변별점은 파단 자체가 아니라 기계적 응력 부위와의 "
                                          "위치 일치다. 화재는 응력 부위를 골라 끊지 않는다"),
    "LongTermTerminalHeating":     (ELEC, "§9.10.3.1(12)·§9.10.3.3 여러 시간에 걸쳐 형성되며 "
                                          "외부 화재 노출로 인한 용융·아크와 외관상 구별된다"),
}


def patterns(g):
    """DamagePattern 의 모든 하위 클래스."""
    out = set()

    def walk(c):
        for s in g.subjects(RDFS.subClassOf, c):
            if isinstance(s, URIRef) and ln(s) not in out:
                out.add(ln(s))
                walk(s)
    walk(E.DamagePattern)
    return sorted(out)


def owners(g):
    m = collections.defaultdict(set)
    for s, o in g.subject_objects(E.canManifest):
        m[ln(o)].add(ln(s))
    return m


def unreviewed(g=None):
    """원문 근거 없이 판정되지 않은 양상. 조사관 검토 또는 추가 조항이 필요하다."""
    g = g or Graph().parse(TTL, format="turtle")
    return [p for p in patterns(g) if p not in VERDICTS]


def inconsistent(g=None):
    """판정과 선언이 어긋난 것. 화재도 낸다고 판정했는데 외부화염에 없거나 그 반대."""
    g = g or Graph().parse(TTL, format="turtle")
    own, bad = owners(g), []
    for p, (v, _) in VERDICTS.items():
        scs = own.get(p, set())
        if not scs:
            continue
        has_fire = "ExternalFlameScenario" in scs
        if v == FIRE and not has_fire:
            bad.append((p, "화재도 낸다고 판정했으나 외부화염 선언에 없다"))
        if v == ELEC and has_fire:
            bad.append((p, "화재는 못 낸다고 판정했으나 외부화염 선언에 있다"))
    return bad


if __name__ == "__main__":
    g = Graph().parse(TTL, format="turtle")
    KO = {}
    for s, o in g.subject_objects(SKOS.prefLabel):
        KO.setdefault(ln(s), str(o))
    own, ps = owners(g), patterns(g)
    print(f"손상 양상 {len(ps)}개 — 판정 {len(ps) - len(unreviewed(g))} / 미검토 {len(unreviewed(g))}\n")
    for p in ps:
        v, why = VERDICTS.get(p, (OPEN, ""))
        scs = sorted(x.replace("Scenario", "") for x in own.get(p, ()))
        mark = {FIRE: "△", ELEC: "■", OPEN: "?"}[v]
        print(f"  {mark} {v:5s} {KO.get(p, p)[:22]:22s} {scs}")
        if why:
            print(f"           {why}")
    bad = inconsistent(g)
    print(f"\n판정과 선언의 불일치: {len(bad)}건")
    for p, why in bad:
        print(f"  {KO.get(p, p)} — {why}")
