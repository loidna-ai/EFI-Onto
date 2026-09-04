"""EFI-Onto ↔ FIReAct 연동 스키마 (Pydantic v2).

TBox(efi_tbox.ttl)의 클래스·속성을 파이썬 타입으로 미러링하고,
세션 레지스트리(논문 3.2절) → 반증 규칙 → 지지점수 → 변별 질의 선택 → 확정 조건 검사를 제공한다.
지지점수는 확률이 아닌 0~100 정수이며 퍼센트 기호를 붙이지 않는다.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from investigation import InvestigationData

EFI = "https://w3id.org/efi-onto#"

# ───────────────────── 온톨로지 적재 (파일이 몇 개든 그래프는 하나) ─────────────────────
# 추론 어휘(efi_tbox.ttl)와 조사 기록 층(efi_investigation.ttl)이 나뉘어 있다.
# 목록을 여기서만 만든다 — 파일 이름을 손으로 든 곳이 열아홉이었고 하나를 빠뜨리면
# 그 층이 통째로 사라진 채 시험이 전부 통과한다.
import pathlib as _pathlib

ONTOLOGY_DIR = _pathlib.Path(__file__).resolve().parents[1] / "ontology"


def ontology_files() -> list[_pathlib.Path]:
    return sorted(ONTOLOGY_DIR.glob("*.ttl"))


def ontology_text() -> str:
    """전체를 이어 붙인 Turtle 원문. 접두어가 겹쳐도 무방하다."""
    return chr(10).join(p.read_text(encoding="utf-8") for p in ontology_files())


def load_graph(paths=None):
    from rdflib import Graph
    g = Graph()
    for p in (paths or ontology_files()):
        g.parse(p, format="turtle")
    return g


# ───────────────────── 열거형 = TBox 클래스 로컬명 ─────────────────────
class Scenario(StrEnum):
    POOR_CONTACT = "PoorContactScenario"
    CRUSH_DAMAGE = "CrushDamageScenario"
    PARTIAL_DISCONNECTION = "PartialDisconnectionScenario"
    INSULATION_DEGRADATION = "InsulationDegradationScenario"
    TRACKING = "TrackingScenario"
    EXTERNAL_FLAME = "ExternalFlameScenario"
    # 국내 분류(화재조사 및 보고규정)의 나머지 셋. TTL 48절
    OVERLOAD = "OverloadScenario"
    GROUND_FAULT = "GroundFaultScenario"
    INTER_TURN_SHORT = "InterTurnShortScenario"


ELECTRICAL: frozenset[Scenario] = frozenset(Scenario) - {Scenario.EXTERNAL_FLAME}
ELECTRICAL_SUPER = "ElectricalIgnitionScenario"  # 규칙이 전기적 시나리오 전체를 겨냥할 때


class Mechanism(StrEnum):
    POOR_CONTACT_HEATING = "PoorContactHeating"
    GLOWING_CONNECTION = "GlowingConnection"
    PARTIAL_DISCONNECTION_HEATING = "PartialDisconnectionHeating"
    SERIES_ARC = "SeriesArc"
    CRUSH_INDUCED_ARC = "CrushInducedArc"
    INSULATION_BREAKDOWN_ARC = "InsulationBreakdownArc"
    ARC_TRACKING = "ArcTracking"
    EXTERNAL_FLAME_EXPOSURE = "ExternalFlameExposure"
    OVERLOAD_HEATING = "OverloadHeating"
    GROUND_FAULT_HEATING = "GroundFaultHeating"
    INTER_TURN_SHORT_CIRCUIT = "InterTurnShortCircuit"


# 가설 → 정의 메커니즘. 6개 가설 전부로 시작할 때 쓴다 (eval.py·calibrate.py 가 같은 표를 읽는다)
DEFAULT_MECHANISM: dict[str, str] = {
    "PoorContactScenario": "PoorContactHeating",
    "CrushDamageScenario": "CrushInducedArc",
    "PartialDisconnectionScenario": "PartialDisconnectionHeating",
    "InsulationDegradationScenario": "InsulationBreakdownArc",
    "TrackingScenario": "ArcTracking",
    "ExternalFlameScenario": "ExternalFlameExposure",
    "OverloadScenario": "OverloadHeating",
    "GroundFaultScenario": "GroundFaultHeating",
    "InterTurnShortScenario": "InterTurnShortCircuit",
}


class Antecedent(StrEnum):
    ENERGIZED = "EnergizedState"
    DE_ENERGIZED = "DeEnergizedState"
    LOOSE_CONNECTION = "LooseConnection"
    CORRODED_CONNECTION = "CorrodedConnection"
    REPEATED_FLEXING = "RepeatedFlexing"
    VIBRATION = "Vibration"
    TENSION = "Tension"
    EXTERNAL_CRUSHING = "ExternalCrushing"
    LONG_TERM_REPEATED_STRESS = "LongTermRepeatedStress"
    AGED_INSULATION = "AgedInsulation"
    REDUCED_INSULATION_RESISTANCE = "ReducedInsulationResistance"
    THERMAL_DEGRADATION = "ThermalDegradation"
    MOISTURE_EXPOSURE = "MoistureExposure"
    DUST_ACCUMULATION = "DustAccumulation"
    SALINE_OR_CHEMICAL = "SalineOrChemicalExposure"
    CONTAMINATED_ENVIRONMENT = "ContaminatedEnvironment"  # 상기 세 클래스의 합집합(정의 클래스)
    INTERMITTENT_RCD_TRIPPING = "IntermittentRcdTripping"
    ABNORMAL_TEMP_OR_VDROP = "AbnormalTemperatureOrVoltageDrop"


class Damage(StrEnum):
    PRIMARY_ARC_MARK = "PrimaryArcMark"
    SECONDARY_ARC_MARK = "SecondaryArcMark"
    ARC_MELT_MARK = "ArcMeltMark"
    FIRE_MELT_MARK = "FireMeltMark"
    LARGE_MELT_MARK = "LargeMeltMark"
    SMALL_MELT_BALL_ON_STRAND_END = "SmallMeltBallOnStrandEnd"
    GENERAL_MELTING = "GeneralMelting"
    SPATTER = "Spatter"
    LOCALIZED_DISCOLORATION = "LocalizedDiscoloration"
    CUPROUS_OXIDE_GROWTH = "CuprousOxideGrowth"
    LONG_TERM_TERMINAL_HEATING = "LongTermTerminalHeating"
    STRAND_FRACTURE = "StrandFracture"
    STRAND_FRACTURE_AT_STRESS_POINT = "StrandFractureAtStressPoint"
    INSULATION_CARBONIZATION = "InsulationCarbonization"
    INSULATION_EMBRITTLEMENT = "InsulationEmbrittlement"
    CARBONIZED_CONDUCTIVE_PATH = "CarbonizedConductivePath"
    MECHANICAL_DEFORMATION = "MechanicalDeformation"
    WHOLE_CONDUCTOR_CRUSHED_OR_CUT = "WholeConductorCrushedOrCut"
    SAGGING = "Sagging"
    BURN_CENTER_ON_SURFACE = "BurnCenterOnSurface"
    THERMAL_GRADIENT_FLOW = "ThermalGradientFlow"
    ARC_BEAD = "ArcBead"
    MULTIPLE_ARC_BEADS = "MultipleArcBeads"
    LOSS_OF_LUSTER = "LossOfLuster"


class SceneEvidence(StrEnum):
    BREAKER_TRIP_RECORD = "BreakerTripRecord"
    IMMEDIATE_TRIP_AFTER_EXTERNAL_FORCE = "ImmediateTripAfterExternalForce"
    EXTERNAL_FORCE_TRACE = "ExternalForceTrace"
    NO_ARC_OR_SPATTER = "NoArcOrSpatter"
    MULTIPLE_ARC_BEADS_AT_ORIGIN = "MultipleArcBeadsAtOrigin"
    FLEXING_HISTORY_WITH_STRAND_FRACTURE = "FlexingHistoryWithStrandFracture"
    NORMAL_INSULATION_RESISTANCE = "NormalInsulationResistance"
    ARC_MAP_POINT = "ArcMapPoint"


class Fuel(StrEnum):
    INSULATION_MATERIAL = "InsulationMaterialFuel"
    ENCLOSURE_MATERIAL = "EnclosureMaterialFuel"
    ACCUMULATED_DUST = "AccumulatedDustFuel"
    CELLULOSE = "CelluloseFuel"
    THERMAL_INSULATION = "ThermalInsulationFuel"
    FLAMMABLE_VAPOR = "FlammableVaporFuel"


class Status(StrEnum):  # 논문 3.2절: 결측 ≠ 확인 불가 ≠ 부정 확인
    CONFIRMED = "Confirmed"
    CONFIRMED_ABSENT = "ConfirmedAbsent"
    UNVERIFIABLE = "Unverifiable"
    MISSING = "Missing"


class Agent(StrEnum):
    INVESTIGATOR = "InvestigatorAgent"
    AI_VLM = "AIAgent"
    INSTRUMENT = "Instrument"


class Verdict(StrEnum):
    ACTIVE = "Active"
    WEAKENED = "Weakened"
    REFUTED = "Refuted"
    SUPPORTED = "Supported"
    WITHHELD = "Withheld"


class Role(StrEnum):
    CORE = "Core"
    SUPPORTING = "Supporting"
    REFUTING = "Refuting"
    DECISIVE = "DecisiveRefuting"


FactClass = Antecedent | Damage | SceneEvidence
def _fact_names() -> set[str]:
    """사실이 될 수 있는 클래스 이름. TTL 에서 읽는다.

    열거형을 손으로 들고 있으면 TTL 에 클래스를 더할 때마다 어긋난다. 실제로
    어긋났다 — 사례 평가를 돌리자 새로 넣은 어휘가 전부 거부됐다.
    열거형은 자주 쓰는 값의 별칭으로 남기고, 유효성은 TTL 이 정한다.
    """
    try:
        from rdflib import Namespace, RDFS, URIRef
        g = load_graph()
        E = Namespace(EFI)
        out = set()

        def walk(c):
            for x in g.subjects(RDFS.subClassOf, c):
                if isinstance(x, URIRef):
                    n = str(x).split("#")[-1]
                    if n not in out:
                        out.add(n)
                        walk(x)
        for root in ("AntecedentCondition", "DamagePattern", "SceneEvidence", "Observation"):
            walk(E[root])
        return out or {m.value for e in (Antecedent, Damage, SceneEvidence) for m in e}
    except Exception:
        return {m.value for e in (Antecedent, Damage, SceneEvidence) for m in e}


_FACT_NAMES = _fact_names()


# ───────────────────── 관측 · 사실 (SOSA + PROV) ─────────────────────
class Observation(BaseModel):
    """sosa:Observation. 계측기·조사관·VLM의 판독을 동일 구조로 기록."""
    id: str
    feature_of_interest: str                      # 증거물 ID (sosa:hasFeatureOfInterest)
    observed_property: str                        # efi 데이터 속성 로컬명 (예: insulationResistance_MOhm)
    value: float | int | bool | str | None = None  # sosa:hasSimpleResult
    unit: str | None = None                       # QUDT unit 로컬명 (MegaOHM, DEG_C, A, MilliM)
    agent: Agent
    observed_at: datetime | None = None
    measured_pre_fire: bool | None = None         # 절연저항은 발화 전/비손상 구간 계측만 반증에 사용


class Fact(BaseModel):
    """세션 레지스트리 1행 = 정규화된 감식 항목. 추론으로 생성 금지, 출처 필수."""
    cls: str = Field(description="TBox 클래스 로컬명")
    status: Status
    agent: Agent
    observation: Observation | None = None
    note: str | None = None
    derived_types: list[str] = []                 # D- 규칙이 덧붙인 유형. 직렬화하지 않는다

    @field_validator("cls")
    @classmethod
    def _known(cls, v: str) -> str:
        if v not in _FACT_NAMES:
            raise ValueError(f"unknown TBox class: {v}")
        return v

    @model_validator(mode="after")
    def _missing_has_no_data(self):
        if self.status is Status.MISSING and (self.observation or self.note):
            raise ValueError("MISSING 상태 사실은 값·비고를 가질 수 없다 (결측 보존)")
        return self


class IndicatorRule(BaseModel):
    """논문 Table 2 한 칸 = efi:IndicatorRule 인스턴스."""
    id: str
    scenario: Scenario | Literal["ElectricalIgnitionScenario"]
    indicator: str
    role: Role
    required_status: Status = Status.CONFIRMED
    delta: int = Field(description="지지점수 가감 (0~100 눈금, 확률 아님)")
    basis: str = ""

    def targets(self, s: Scenario) -> bool:
        return self.scenario == s or (self.scenario == ELECTRICAL_SUPER and s in ELECTRICAL)


class Ontology(BaseModel):
    """TTL에서 적재한 규칙 + 클래스 상위 계층 (사실↔지표 매칭에 subClassOf* 반영)."""
    rules: list[IndicatorRule]
    ancestors: dict[str, set[str]]
    needs: dict[str, set[str]] = {}         # 가설 → 선언된 필요조건 (hasAntecedent 제한). 없으면 항상 형성
    manifest: dict[str, set[str]] = {}      # 가설 → 남길 수 있는 손상 양상
    shared_by: dict[str, int] = {}          # 손상 양상 → 이 양상을 남기는 가설 수
    damage_cls: set[str] = set()            # DamagePattern 하위 전체

    def matches(self, fact_cls: str, indicator: str) -> bool:
        return indicator in self.ancestors.get(fact_cls, {fact_cls})

    def matches_absent(self, fact_cls: str, indicator: str) -> bool:
        """부재 확인은 포섭 방향이 반대다.

        관측이 '헐거움'이면 상위인 '접속 상태'도 관측된 것이다 — 위로 올라간다.
        그러나 '헐거움 없음'은 '접속 상태 이상 없음'을 뜻하지 않는다. 부식이
        있을 수 있다. 부재는 위에서 아래로만 함의한다 — '오염 환경 없음'이
        확인되면 그 하위인 '습기 노출 없음'도 따라온다.
        """
        return fact_cls in self.ancestors.get(indicator, {indicator})

    def is_damage(self, fact_cls: str) -> bool:
        return fact_cls in self.damage_cls

    def is_discriminating(self, fact_cls: str) -> bool:
        """그 가설에서만 나타나는 양상인가. 비형태학적 사실은 항상 True."""
        if not self.is_damage(fact_cls):
            return True
        return self.shared_by.get(fact_cls, 0) == 1

    def ambiguous_pairs(self, min_shared: int = 2) -> list[tuple[str, str, list[str]]]:
        """손상 양상을 min_shared개 이상 공유하는 가설 쌍 (M-2 대응)."""
        ks, out = sorted(self.manifest), []
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                sh = sorted(self.manifest[a] & self.manifest[b])
                if len(sh) >= min_shared:
                    out.append((a, b, sh))
        return sorted(out, key=lambda x: -len(x[2]))

    @classmethod
    def load(cls, ttl_path: str | None = None) -> Ontology:
        """온톨로지 전체를 읽는다. 경로를 주면 그 파일만 — 조각을 시험할 때만 쓴다."""
        from rdflib import RDFS, URIRef, Namespace
        EFI = Namespace("https://w3id.org/efi-onto#")
        g = load_graph([ttl_path] if ttl_path else None)
        loc = lambda u: str(u).split("#")[-1]
        anc: dict[str, set[str]] = {}
        for c in {x for x in g.subjects(RDFS.subClassOf, None) if isinstance(x, URIRef)}:
            anc[loc(c)] = {loc(a) for a in g.transitive_objects(c, RDFS.subClassOf) if isinstance(a, URIRef)}
        from rdflib import OWL
        import rdflib.collection as rc
        needs: dict[str, set[str]] = {}
        for sc in g.subjects(RDFS.subClassOf, EFI.IgnitionScenario):
            for sub in [sc] + list(g.subjects(RDFS.subClassOf, sc)):
                if loc(sub) == "ElectricalIgnitionScenario":
                    continue          # 통전은 모든 전기 가설의 공통 필요조건이라 형성 기준이 아니다 (C-57 이 결론에서 요구)
                for r in g.objects(sub, RDFS.subClassOf):
                    if (r, OWL.onProperty, EFI.hasAntecedent) not in g:
                        continue
                    v = g.value(r, OWL.someValuesFrom)
                    if isinstance(v, URIRef):
                        needs.setdefault(loc(sub), set()).add(loc(v))
                    else:
                        for u in g.objects(v, OWL.unionOf):
                            needs.setdefault(loc(sub), set()).update(loc(x) for x in rc.Collection(g, u))
        man: dict[str, set[str]] = {}
        for s, o in g.subject_objects(EFI.canManifest):
            man.setdefault(loc(s), set()).add(loc(o))
        shared: dict[str, int] = {}
        for ds in man.values():
            for d in ds:
                shared[d] = shared.get(d, 0) + 1
        dmg = {k for k, v in anc.items() if "DamagePattern" in v} | {"DamagePattern"}
        return cls(rules=load_rules(ttl_path), ancestors=anc, needs=needs,
                   manifest=man, shared_by=shared, damage_cls=dmg)


# ───────────────────── 가설 · 세션 ─────────────────────
class Hypothesis(BaseModel):
    scenario: Scenario
    mechanism: Mechanism
    antecedents: list[str] = []
    first_fuel: Fuel | None = None                # 미확인 허용 → 판단보류 경로
    mechanism_max_temp_c: float | None = None
    fuel_ignition_temp_c: float | None = None
    support_score: int = Field(50, ge=0, le=100)  # 이미지 단독 ≈ 50 출발 (논문 3.2절)
    verdict: Verdict = Verdict.ACTIVE
    formed: bool = True                           # D-15: 필요조건이 자료에 있는가. 없으면 세워지지 않은 가설
    supported_by: list[str] = []                  # Fact.cls
    refuted_by: list[str] = []
    rationale: list[str] = []


class Session(BaseModel):
    """efi:InvestigationSession (세션 레지스트리)."""
    case_id: str
    artifacts: list[str] = []
    facts: list[Fact] = []
    hypotheses: list[Hypothesis] = []
    investigation: InvestigationData | None = None
    proposed_conclusion: Scenario | None = None
    query_count: int = 0
    closure_min_facts: int = 2       # 확정 조건 (논문 3.2절)
    closure_min_queries: int = 2
    closure_min_score: int = 70

    @model_validator(mode="after")
    def _investigation_references(self):
        names = {h.scenario.value: h for h in self.hypotheses}
        if len(names) != len(self.hypotheses):
            raise ValueError("duplicate hypothesis scenario")
        if self.proposed_conclusion is not None and self.proposed_conclusion.value not in names:
            raise ValueError("proposed conclusion must refer to a registered hypothesis")
        if self.investigation:
            known_fuels = {name: h.first_fuel.value for name, h in names.items() if h.first_fuel is not None}
            for record in [*self.investigation.first_fuels, *self.investigation.heat_transfers]:
                if record.scenario not in names:
                    raise ValueError("investigation record must refer to a registered hypothesis")
            for record in self.investigation.first_fuels:
                if record.scenario in known_fuels and known_fuels[record.scenario] != record.fuel_class:
                    raise ValueError("conflicting first fuel classes for the same hypothesis")
                known_fuels[record.scenario] = record.fuel_class
            if any(r.scenario not in known_fuels for r in self.investigation.heat_transfers):
                raise ValueError("heat transfer record requires an identified candidate fuel")
        return self

    # ---- 조회 ----
    def status_of(self, cls: str) -> Status:
        return next((f.status for f in self.facts if f.cls == cls), Status.MISSING)

    def _facts_matching(self, r: IndicatorRule, o: Ontology) -> list[Fact]:
        hit = o.matches_absent if r.required_status is Status.CONFIRMED_ABSENT else o.matches
        return [f for f in self.facts if f.status == r.required_status
                and (hit(f.cls, r.indicator) or any(o.matches(t, r.indicator) for t in f.derived_types))]

    def _slot_status(self, indicator: str, o: Ontology) -> Status:
        sts = [f.status for f in self.facts
               if o.matches(f.cls, indicator) or any(o.matches(t, indicator) for t in f.derived_types)]
        return next((st for st in (Status.CONFIRMED, Status.CONFIRMED_ABSENT, Status.UNVERIFIABLE) if st in sts), Status.MISSING)

    # ---- 규칙 실행: 반증 우선 → 점수 → 착화 역량 ----
    # ---- D-13 기기 내부·단자 + 오염 확인 → 그 대상은 이극 도체 간 절연물 표면 ----
    #  새 사실을 만들지 않는다(C-4). 대상 사실에 유형을 덧붙인다. SHACL 의
    #  TrackingSiteDerivationRuleShape 와 같은 규칙이며 두 곳이 갈리면 안 된다.
    SITE_BASES: ClassVar[tuple[str, ...]] = ("DeviceInteriorSite", "TerminalSite")

    def derive(self, o: Ontology) -> Session:
        for f in self.facts:
            f.derived_types = []
        if any(o.matches(f.cls, "ContaminatedEnvironment") and f.status is Status.CONFIRMED for f in self.facts):
            for f in self.facts:
                if f.status is Status.CONFIRMED and any(o.matches(f.cls, b) for b in self.SITE_BASES):
                    f.derived_types.append("InterPoleInsulatingSurface")
        return self

    def apply(self, o: Ontology) -> Session:
        self.derive(o)
        for h in self.hypotheses:
            h.support_score, h.verdict = 50, Verdict.ACTIVE
            h.supported_by, h.refuted_by, h.rationale = [], [], []
            # [D-15] 가설 형성 — 선언된 필요조건 중 하나라도 확인돼야 세워진다 (§19.4.1).
            #  형성되지 않아도 점수는 매긴다(질의 후보를 고르는 데 쓴다). 판정에서만 빠진다.
            #  세우는 길은 둘 — 필요조건이 확인됐거나, 특이 흔적(양립 가설 둘 이하)이 확인됐거나.
            #  공유 흔적은 세우지 못한다. SHACL D-15 와 같아야 한다.
            need = o.needs.get(h.scenario.value)
            specific = [d for d in o.manifest.get(h.scenario.value, ()) if o.shared_by.get(d, 0) <= 2]
            h.formed = not need or any(
                f.status is Status.CONFIRMED and (
                    any(o.matches(c, n) for n in need for c in [f.cls] + f.derived_types)
                    or any(o.matches(f.cls, d) for d in specific))
                for f in self.facts)
            # 더 구체적인 규칙이 함께 발동하면 상위 규칙은 세지 않는다.
            #   굴곡 하나로 '장기 반복 응력'(6)과 '반복 굴곡'(9)이 함께 발동해
            #   15점이 되던 이중 계상을 막는다. 같은 관측을 두 해상도로 두 번
            #   세는 것이므로 좁힌 쪽만 남긴다.
            # 형제(습기·분진)는 서로 다른 관측이므로 각각 센다 — 교재 p.147 이
            # '수분을 많이 함유한 먼지'를 트래킹의 조건으로 드는 그 겹침이다.
            # F-4 SHACL 규칙에 같은 것이 적혀 있다. 두 곳이 갈리면 안 된다.
            fired = [r for r in o.rules
                     if r.targets(h.scenario) and r.role in (Role.CORE, Role.SUPPORTING)
                     and self._facts_matching(r, o)]
            keep = {id(r) for r in fired
                    if not any(s is not r and r.indicator in o.ancestors.get(s.indicator, set())
                               for s in fired)}
            for r in (r for r in o.rules if r.targets(h.scenario)):
                hits = self._facts_matching(r, o)
                if not hits:
                    continue
                if r.role in (Role.CORE, Role.SUPPORTING) and id(r) not in keep:
                    continue
                if r.role is Role.DECISIVE:                       # [F-1] 결정적 기각 (예: 비통전)
                    h.verdict, h.support_score = Verdict.REFUTED, 0
                    h.refuted_by += [f.cls for f in hits]
                    h.rationale.append(f"{r.id}: 결정적 반증 — {r.basis}")
                    break
                h.support_score = max(0, min(100, h.support_score + r.delta))
                (h.refuted_by if r.role is Role.REFUTING else h.supported_by).extend(f.cls for f in hits)
                h.rationale.append(f"{r.id}: {r.role} {r.delta:+d} — {r.basis}")
            if h.verdict is Verdict.REFUTED:
                continue
            if h.refuted_by and h.support_score < 40:            # 반증단서 누적 → 약화
                h.verdict = Verdict.WEAKENED
            if (h.mechanism_max_temp_c is not None and h.fuel_ignition_temp_c is not None
                    and h.mechanism_max_temp_c < h.fuel_ignition_temp_c):   # [F-3] 착화 역량 미달
                h.verdict = Verdict.WEAKENED
                h.rationale.append("착화 역량 미달: 메커니즘 최대 온도 < 착화물 발화 온도")
        return self

    # ---- 판정 결과: 가설 하나, 원인미상, 또는 미확인 단락 ----
    #  §19.6.5.1 — 전부 기각되거나(D-7) 최고점이 동점이면(D-8) 원인미상이다.
    #  세워지지 않은 가설(D-15, formed=False)은 이기지도 동점을 만들지도 못한다.
    #  자료가 지지하지 않는 가설(50점 이하)도 판정이 못 된다(D-16) — 외부화염이 빈 조사서에서 홀로 남는 것.
    #  그 원인미상 중 단락흔과 통전이 확인됐으면 국내 분류의 '미확인 단락'(D-14). 통전 미확인은 원인미상.
    #  분류지 결론이 아니다(§19.8.2). SHACL D-14 와 같아야 한다.
    UNDETERMINED: ClassVar[str] = "Undetermined"
    UNIDENTIFIED_SHORT: ClassVar[str] = "UnidentifiedShortCircuit"

    def outcome(self, o: Ontology) -> str:
        # 승자 후보: 형성됐고(D-15) 기각되지 않았고 자료가 지지하는(D-16, 50점 초과) 가설
        live = [h for h in self.hypotheses if h.verdict is not Verdict.REFUTED and h.formed and h.support_score > 50]
        if live:
            top = max(h.support_score for h in live)
            best = [h for h in live if h.support_score == top]
            if len(best) == 1:
                return best[0].scenario.value
        arc = any(f.status is Status.CONFIRMED and o.matches(f.cls, "ArcMeltMark") for f in self.facts)
        live_ = any(f.status is Status.CONFIRMED and o.matches(f.cls, "EnergizedState") for f in self.facts)
        return self.UNIDENTIFIED_SHORT if arc and live_ else self.UNDETERMINED     # 통전 기준은 C-57 과 같다

    # ---- CQ3: 상위 두 가설을 가르는 미확인 지표 (동적 질의 후보) ----
    def discriminating_slots(self, o: Ontology) -> list[tuple[str, Scenario, int]]:
        """상위 가설들을 가르는 미확인 지표, 변별력 순.

        **동점이면 동점 전부가 후보다.** 사진만으로 아홉이 50점이면 '상위 둘'은 목록 순서상
        앞의 둘(접촉불량·압착손상)이라, 접속 상태·아산화동을 147회 묻고 대부분 결측으로
        끝났다 — 150건 대화 루프에서 정답 가설이 형성조차 안 된 것이 74건. 연동 흐름을
        처음 끝까지 돌렸을 때 드러났다.

        **형성되지 않은 가설의 필요조건을 먼저 묻는다.** D-15 는 필요조건이 자료에 있어야
        가설을 세운다(§19.4.1). 세워지지 않은 가설은 이기지도 동점을 만들지도 못하므로
        그것을 세울지 가를 질문이 점수 차보다 먼저다.
        """
        live = sorted((h for h in self.hypotheses if h.verdict is not Verdict.REFUTED),
                      key=lambda h: h.support_score, reverse=True)
        if len(live) < 2:
            return []
        top = live[0].support_score
        tied = [h for h in live if h.support_score == top]
        cands = tied if len(tied) >= 2 else live[:2]
        unformed = {h.scenario for h in cands if not h.formed}
        # 형성 질의는 필요조건이 선언된 수준에서 한 번에 묻는다. 반단선의 필요조건은
        # 굴곡|진동|인장의 합집합인데 잎마다 따로 물으면 세 번이고, 조사서가 '반복 굴곡'을
        # 적어도 "인장?" 에는 결측으로 답한다. 공통 상위(장기 반복 응력)를 물으면 어떤 하위로
        # 답해도 포섭으로 잡힌다. 150건에서 24건이 '물었는데도 미형성'이던 이유다.
        formation: dict[str, tuple[Scenario, int]] = {}
        for h in cands:
            if h.scenario not in unformed:
                continue
            need = o.needs.get(h.scenario.value, set())
            if not need:
                continue
            ask = self._common_need(need, o)
            if self._slot_status(ask, o) is Status.MISSING:
                cur = formation.get(ask)
                formation[ask] = (h.scenario, (cur[1] if cur else 0) + 1)   # 여러 가설을 세우는 조건이 앞
        out: list[tuple[str, Scenario, int, int]] = [(k, s, n * 100, 1) for k, (s, n) in formation.items()]
        for r in o.rules:
            if r.scenario == ELECTRICAL_SUPER or self._slot_status(r.indicator, o) is not Status.MISSING:
                continue
            hit = [h for h in cands if r.targets(h.scenario)]
            if not hit or len(hit) == len(cands):                 # 전부 또는 아무도 가리키지 않으면 못 가른다
                continue
            w = abs(r.delta)
            if o.is_damage(r.indicator):                          # 형태학적 지표는 변별력으로 감쇠
                w = int(round(w / max(1, o.shared_by.get(r.indicator, 1))))
            target = hit[0].scenario
            out.append((r.indicator, target, w, 0))
        out.sort(key=lambda x: (x[3], x[2]), reverse=True)
        seen: set[str] = set()
        return [(i, s, w) for i, s, w, _ in out if not (i in seen or seen.add(i))]

    @staticmethod
    def _common_need(need: set[str], o: Ontology) -> str:
        """필요조건 합집합의 가장 구체적인 공통 상위. 하나면 그 자신, 공통이 없으면 첫째."""
        members = sorted(need)
        if len(members) == 1:
            return members[0]
        common = set.intersection(*[o.ancestors.get(m, set()) | {m} for m in members])
        common -= {"AntecedentCondition", "EnvironmentalCondition", "InsulationCondition", "ElectricalState", "SceneEvidence"}
        if not common:
            return members[0]
        return max(common, key=lambda c: len(o.ancestors.get(c, set())))   # 조상이 많을수록 구체적

    # ---- 확정의 전제: 변별력이 0 이라 질의 후보에 오르지 않지만 없으면 결론이 서지 않는 것 ----
    #  C-57 통전 확인. 대화 루프 150건에서 조사서에 있는데도 70건을 끝내 안 물었다 —
    #  모든 전기적 가설이 같이 요구하므로 어떤 가설도 가르지 않기 때문이다.
    CLOSURE_PREREQUISITES: ClassVar[tuple[str, ...]] = ("EnergizedState",)

    def prerequisite_slots(self, o: Ontology) -> list[str]:
        return [c for c in self.CLOSURE_PREREQUISITES if self._slot_status(c, o) is Status.MISSING]

    # ---- 확정 조건 / negative corpus 방지 ----
    def conclusion_check(self, h: Hypothesis, o: Ontology | None = None) -> list[str]:
        confirmed = [f for f in self.facts if f.cls in h.supported_by and f.status is Status.CONFIRMED]
        problems = []
        if o is not None and confirmed and not any(o.is_discriminating(f.cls) for f in confirmed):
            problems.append("공유 형태학적 단서만으로 구성 — 전용 양상 또는 비시각적 현장 사실 필요 (C-5)")
        if h.verdict is Verdict.REFUTED:
            problems.append("기각된 가설")
        if len(confirmed) < self.closure_min_facts:
            problems.append(f"긍정 지지 사실 {len(confirmed)}건 < {self.closure_min_facts} (타 가설 소거만으로 확정 불가)")
        if not any(f.agent is Agent.INVESTIGATOR for f in confirmed):
            problems.append("조사관 확인 사실 0건 (AI 판독 단독 확정 불가)")
        if h.support_score < self.closure_min_score:
            problems.append(f"지지점수 {h.support_score} < {self.closure_min_score}")
        if self.query_count < self.closure_min_queries:
            problems.append(f"질의 {self.query_count}회 < {self.closure_min_queries}")
        return problems

    def closure_met(self, o: Ontology | None = None) -> bool:
        return any(not self.conclusion_check(h, o) for h in self.hypotheses)

    # ---- 결론 검증은 SHACL 에 위임한다 ----
    def validate(self, ttl_path: str | None = None) -> list[str]:
        """결론 제약 위반 메시지. 규칙을 여기 옮겨 적지 않고 pySHACL 을 부른다.

        제약을 두 곳에 적으면 반드시 갈라진다. 실제로 갈라졌었다 — SHACL 에만
        수십 개가 쌓이는 동안 이 파일은 초기 다섯 가지만 알고 있었다.
        점수 산출과 질의 선택은 여기서, 결론 검증은 저기서 한다.
        """
        from rdflib import Graph
        from pyshacl import validate as shacl_validate
        text = open(ttl_path, encoding="utf-8").read() if ttl_path else ontology_text()
        g = Graph().parse(data=text + self.to_turtle(include_derived=False), format="turtle")
        _, _, text = shacl_validate(g, advanced=True, allow_infos=True, allow_warnings=True)
        return [l.strip()[len("Message: "):] for l in text.splitlines()
                if l.strip().startswith("Message: ")]

    # ---- ABox 직렬화 (rdflib 선택 의존) ----
    def to_turtle(self, include_derived: bool = True) -> str:
        """include_derived=False 면 점수·판정을 빼고 쓴다.

        supportScore 는 owl:FunctionalProperty 인데 F-4 가 다시 계산해 넣는다.
        둘 다 쓰면 값이 둘이 되어 모순이다. 검증할 때는 입력만 넘기고
        도출은 SHACL 에 맡긴다."""
        from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
        from decimal import Decimal
        E, PROV = Namespace(EFI), Namespace("http://www.w3.org/ns/prov#")
        g, s = Graph(), URIRef(f"{EFI}session_{self.case_id}")
        g.bind("efi", E); g.bind("prov", PROV)
        g.add((s, RDF.type, E.InvestigationSession)); g.add((s, E.queryCount, Literal(self.query_count)))
        for i, f in enumerate(self.facts):
            n = URIRef(f"{EFI}{self.case_id}_fact{i}")
            g.add((s, E.hasFact, n)); g.add((n, RDF.type, E[f.cls]))
            g.add((n, E.confirmationStatus, E[f.status])); g.add((n, PROV.wasAttributedTo, E[f"{self.case_id}_{f.agent}"]))
            g.add((E[f"{self.case_id}_{f.agent}"], RDF.type, E[f.agent]))
        nodes = {}
        for h in self.hypotheses:
            n, m = URIRef(f"{EFI}{self.case_id}_{h.scenario}"), BNode()
            fuel = URIRef(f"{n}/first_fuel")
            nodes[h.scenario.value] = (n, m, fuel)
            g.add((n, RDF.type, E[h.scenario])); g.add((n, E.inSession, s))
            g.add((n, E.hasMechanism, m)); g.add((m, RDF.type, E[h.mechanism]))
            if h.first_fuel is not None:
                g.add((n, E.hasFirstFuel, fuel)); g.add((fuel, RDF.type, E[h.first_fuel]))
            if h.mechanism_max_temp_c is not None:
                g.add((m, E.maxAttainableTemperature_C, Literal(Decimal(str(h.mechanism_max_temp_c)))))
            if h.fuel_ignition_temp_c is not None and (h.first_fuel is not None or (
                    self.investigation is not None and any(r.scenario == h.scenario.value for r in self.investigation.first_fuels))):
                g.add((fuel, E.ignitionTemperature_C, Literal(Decimal(str(h.fuel_ignition_temp_c)))))
            if include_derived:
                g.add((n, E.supportScore, Literal(h.support_score)))
                g.add((n, E.verdict, E[h.verdict]))
        if self.investigation is not None:
            self.investigation.add_to_graph(g, s, nodes)
        if self.proposed_conclusion is not None:
            conclusion = URIRef(f"{s}/proposed_conclusion")
            g.add((conclusion, RDF.type, E.Conclusion))
            g.add((conclusion, E.concludes, nodes[self.proposed_conclusion.value][0]))
        return g.serialize(format="turtle")


# ───────────────────── 규칙 로더 (TTL이 단일 진실 원천) ─────────────────────
def load_rules(ttl_path: str | None = None) -> list[IndicatorRule]:
    from rdflib import Namespace
    E = Namespace(EFI)
    g = load_graph([ttl_path] if ttl_path else None)
    q = """PREFIX efi: <https://w3id.org/efi-onto#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?r ?sc ?ind ?role ?st ?d ?c WHERE {
      ?r a efi:IndicatorRule ; efi:forScenario ?sc ; efi:indicates ?ind ; efi:hasRole ?role ;
         efi:requiresStatus ?st ; efi:scoreDelta ?d . OPTIONAL { ?r rdfs:comment ?c } }"""
    loc = lambda u: str(u).split("#")[-1]
    return [IndicatorRule(id=loc(r.r), scenario=loc(r.sc), indicator=loc(r.ind), role=Role(loc(r.role)),
                          required_status=Status(loc(r.st)), delta=int(r.d), basis=str(r.c or ""))
            for r in g.query(q)]


# ───────────────────── 사용 예 ─────────────────────
if __name__ == "__main__":
    onto = Ontology.load()
    s = Session(case_id="A", query_count=2, facts=[
        Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR, note="옥외 단자함, 전날 우천"),
        Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM),
        Fact(cls="LooseConnection", status=Status.CONFIRMED_ABSENT, agent=Agent.INVESTIGATOR),
        Fact(cls="NormalInsulationResistance", status=Status.UNVERIFIABLE, agent=Agent.INVESTIGATOR),
    ], hypotheses=[
        Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING),
        Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING),
    ]).apply(onto)
    for h in s.hypotheses:
        print(h.scenario, h.support_score, h.verdict, s.conclusion_check(h))
    print("next queries:", s.discriminating_slots(onto)[:3])
    print("closure:", s.closure_met())
