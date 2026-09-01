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

OPEN 은 남지 않았다 (8 → 0)
  마지막 한 건이던 BurnCenterOnSurface 는 소방청 화재조사실무Ⅳ(2025) p.153 이
  답을 줬다. 표면 집중은 트래킹을 접속부 내부 발열과 가르지만, 외부 화염도
  절연물을 표면부터 태운다. 전용 단서가 아니다 — 화재도냄으로 판정했다.
  그 결과 트래킹에는 전용 형태 단서가 하나도 남지 않았고, 그래서 트래킹을
  세우려면 비시각적 현장 사실(오염 환경)이 있어야 한다. C-5 가 요구하는 그것이다.
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
    "BurnCenterOnSurface":         (FIRE, "실무Ⅳ p.153 표면 집중은 트래킹을 접속부 내부 발열과 가른다. 그러나 §9.10.1 외부 화염도 절연물을 표면부터 태우므로 전용 단서가 될 수 없다"),
    "CuprousOxideGrowth":          (ELEC, "§9.10.3 발광 접속부의 산화물 생성"),

    # 국내 실무 교재(화재조사실무Ⅳ 2025)에서 온 양상. NFPA 조항이 아니므로
    # 근거에 쪽수를 남긴다. 질문은 같다 — 화재도 이 흔적을 내는가?
    "FuseMeltPattern":             (FIRE, "실무Ⅳ p.203 퓨즈가 녹은 형태 일반은 외부 화염도 만든다. 갈래를 따져야 변별이 생긴다"),
    "FuseIrregularlyMelted":       (FIRE, "실무Ⅳ p.203 외부 화염에 의한 용융은 불규칙한 형태"),
    "FuseGloballyMeltedScattered": (FIRE, "실무Ⅳ p.203 단락 형태이나 §9.10.1 화재 유발 단락도 같은 형태를 낸다"),
    "FuseMeltedAtCenter":          (ELEC, "실무Ⅳ p.203 100~300% 과부하 구간이 중앙을 녹인다. §9.9.3 화재는 그 구간이 아니라 완전 단락을 만든다"),
    "FuseEndsDarkened":            (ELEC, "실무Ⅳ p.203 양단 흑변은 홀더 접촉부의 장기 발열 산물. 화재열은 퓨즈를 고르게 가열한다"),
    "MeltMarkOnBothSidesOfBreak":  (ELEC, "실무Ⅳ p.150 파단부 양쪽이라는 대응은 그 지점의 접촉·단속 반복이 만든다. §9.10.1 화재 유발 아크는 위치를 고르지 않는다"),
    "MeltMarkOnSupplySideOnly":    (ELEC, "실무Ⅳ p.150 전원측 편중은 방향성이다. §9.10.2.2 방향성은 전기적 현상의 표식이고 화재는 전원측을 가리지 않는다"),
    "StrandFractureOverTenPercent": (FIRE, "상위 StrandFracture 가 §9.10.2 로 화재도냄이다. 10% 라는 정도는 발화 전 상태를 뜻하지만 소손 후 형태만으로는 선후를 가릴 수 없다"),
    "LocalizedHeatWithSurroundingDamage": (ELEC, "실무Ⅳ p.210·211 주위까지 심하게 태운 국부 고열은 그 부품이 발화점이라는 표지다. 밖에서 온 화염은 이 대비를 만들지 않는다"),
    "IntactSurroundingsAroundComponent":  (FIRE, "실무Ⅳ p.210·211 부품과 주위가 모두 경미하면 외부 화염을 맞은 것으로 판정한다. 정의상 화재가 만드는 양상"),
    "DendriticTreePath":           (ELEC, "실무Ⅳ p.153·156 절연체 내부에서 전계 집중을 따라 자라는 경로다. 화재는 절연물 내부에 수지상 경로를 만들지 않는다"),
    "InternalDamageExceedingSurface": (ELEC, "실무Ⅳ p.254 내부 전극·유전체가 표면보다 강하게 탄화됐다면 안에서 시작된 것이다. §9.10.1 밖에서 온 화염은 표면부터 태운다"),
    # 용흔 외관·단면 (실무Ⅳ p.306~309). 1차/2차 판정은 F-2(시간 선후)가 하고
    # 이것들은 보강 근거다. 교재도 "본 결과물 단독으로 단정할 수 없다"고 한다.
    "WideMeltWithRoughSurface":    (FIRE, "실무Ⅳ p.309 열용흔의 대표 형태다. 전원이 차단된 상태에서 화재열로 녹은 것이므로 정의상 화재가 만든다"),
    "DrippingMeltFormation":       (FIRE, "실무Ⅳ p.309 전선 중간이 녹아 흘러내린 형태. 열용흔이다"),
    "StretchedThinnedEnd":         (FIRE, "실무Ⅳ p.309 외부 화염에 연화되어 장력 방향으로 늘어난 것. 열용흔이다"),
    "HemisphericalMeltShape":      (FIRE, "실무Ⅳ p.308 1차 용융흔에 반구형이 '많다'는 경향일 뿐 2차에도 나온다. 전용 단서가 아니다"),
    "SmoothLustrousMeltSurface":   (FIRE, "실무Ⅳ p.308 같은 경향 진술이다. 2차가 거친 것이 '많다'이지 항상은 아니다"),
    "ForeignMatterInclusion":      (FIRE, "실무Ⅳ p.309 2차 용융흔의 특징이다. 2차는 화재가 만든 것이므로 화재가 낸다"),
    "AlloyDiscoloration":          (FIRE, "실무Ⅳ p.318 알루미늄은 은색, 아연합금은 황동색으로 변한다. 아크가 아니라 합금 용융온도가 낮아진 결과일 수 있다"),
    "PostFireMechanicalDamage":    (FIRE, "실무Ⅳ p.318 진화·도괴·수습·조사관 절단으로 생긴다. 정의상 화재 이후의 것이다"),
    "CarbonizationFromInsideOut":  (ELEC, "실무Ⅳ p.312 도체가 발열하면 피복을 안쪽부터 태운다. §9.10.1 밖에서 온 화염은 반대 방향으로 태우므로 이 방향을 만들지 못한다"),
    "UniformDamageAlongConductor": (FIRE, "실무Ⅳ p.312 과전류는 도체 전 길이를 고르게 가열한다. 그러나 전선 전체가 화염에 잠겨도 같은 균일 손상이 나온다"),
    "ContactWelding":              (ELEC, "실무Ⅴ p.238 접촉·분리 시의 아크가 접점을 융착시킨다. 화재열은 접점을 녹일 수는 있어도 개폐 아크가 만드는 변형·융착 형태를 만들지 않는다"),
    "ToothMarkOnInsulation":       (ELEC, "실무Ⅳ p.253 설치류의 이빨 자국은 화재가 만들 수 있는 형태가 아니다. 잔존 피복에 남는다"),
    "RubyRedCrystal":              (ELEC, "실무Ⅳ p.153 적색 결정은 출화개소에 대응하는 접촉부에서 나온다. 상위 CuprousOxideGrowth 와 같이 §9.10.3 발광 접속부 산물"),
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
