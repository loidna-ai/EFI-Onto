# -*- coding: utf-8 -*-
"""dataset.xlsx 의 슬롯 텍스트를 온톨로지 어휘로 매핑한다.

왜 사전인가
  LLM 판독을 쓰면 유연하지만, 틀렸을 때 온톨로지가 틀린 것인지 판독기가 틀린
  것인지 갈리지 않는다. 사전은 투명하고 재현되며, 매핑되지 않는 표현이 무엇인지가
  곧 어휘의 빈 곳을 알려준다. 그 빈 곳 자체가 결과다.

왜 슬롯별로 나누는가
  슬롯이 축을 정해 준다. '먼지 적체'가 slot_environmental_contamination 에
  있으면 후보는 환경 조건뿐이다. 축을 모르고 매핑하면 같은 낱말이 여러 축으로
  흩어지지만, 축을 알면 후보가 좁아 오탐이 준다.

확인 상태
  '확인 불가'는 Unverifiable, '없음·특이사항 없음'은 ConfirmedAbsent,
  나머지는 Confirmed. 이 셋을 뭉개면 P4 가 무너진다.
"""
import openpyxl, re, json, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
XLSX = pathlib.Path("V:/Dataset/dataset.xlsx")
OUT = ROOT / "cases" / "sessions"

LABEL = {"기계적 손상 단락": "CrushDamageScenario", "반단선": "PartialDisconnectionScenario",
         "절연열화 단락": "InsulationDegradationScenario", "접촉불량": "PoorContactScenario",
         "트래킹": "TrackingScenario"}

# 슬롯 → (표현 패턴, 온톨로지 클래스). 위에서부터 먼저 맞는 것을 쓴다.
RULES = {
 "slot_energized_status": [
    (r"통전|전원\s*인가|전원\s*투입|작동\s*중|가동\s*중|점등|사용\s*중", "EnergizedState"),
    # '정전'만으로 비통전이라 읽지 않는다. 비통전은 결정적 기각(-100)이라
    # 전기 가설 전부를 죽인다. 그런데 '부분 정전'은 회로 일부가 나갔다는 뜻이고
    # 오히려 전기적 이상의 징후다 — 발화 지점이 비통전이었다는 뜻이 아니다.
    # 실제로 "매장 내 부분 정전 현상"이 압착손상 사례를 통째로 기각시키고 있었다.
    (r"비통전|전원\s*없|단전|전원\s*차단\s*상태|미통전", "DeEnergizedState"),
 ],
 "slot_breaker_trip_status": [
    (r"확인\s*불가|식별\s*불가|판단\s*불가", "BreakerTripRecord"),      # 상태는 Unverifiable
    # '외력 직후 즉시 트립'은 트립 사실과 외력 사실이 함께 서야 하는 복합 사실이고
    # 외력은 다른 슬롯에 있다. 한 슬롯에서 판정할 수 없으므로 단순 기록으로 둔다.
    # 실측이 이를 뒷받침한다 — 32건 중 기계적 손상은 12건뿐이다(37%). 차단기는
    # 어떤 단락에서도 동작한다.
    (r"트립|떨어진|작동\s*확인|작동함|OFF|내려감", "BreakerTripRecord"),
    (r"수동|임의로\s*차단", "BreakerTripRecord"),
 ],
 "slot_fastening_torque": [
    (r"꼬아|꼬임|비틀림|나선형|임의\s*접속|임의로\s*결합|수동\s*꼬임", "LooseConnection"),
    (r"느슨|헐거|결속력\s*약화|풀림|이완", "LooseConnection"),
    (r"절연테이프|전기테이프", "LooseConnection"),
 ],
 "slot_environmental_contamination": [
    (r"먼지|분진|이물질|퇴적물|파지", "DustAccumulation"),
    (r"습기|습한|습도|결로|누수|물기|빗물|강수|침수", "MoistureExposure"),
    (r"기름|유증|염분|염해|화학|부식성", "SalineOrChemicalExposure"),
    (r"밀폐|방출되지\s*못|보온재|단열재\s*사이|감싸|덮인", "ThermalInsulationEnclosure"),
    (r"다발|묶음|여러\s*가닥.*묶", "BundledWiring"),
    (r"건조|청결|오염\s*없", None),                                     # 부재 확인
 ],
 "slot_pre_ignition_symptoms": [
    (r"불꽃|스파크|아크|섬광|번쩍|불빛|퍽\s*소리|펑\s*소리|파열음", "PreFireArcObservation"),
    (r"타는\s*냄새|냄새|깜박|점멸|밝기|어둡", "FlickeringOrOdor"),
    (r"차단기.*(내려|떨어|작동)|누전\s*차단기.*이력", "IntermittentRcdTripping"),
    (r"온도|과열|뜨거|전압\s*강하|정전", "AbnormalTemperatureOrVoltageDrop"),
    (r"없었음|없음|발견되지\s*않", None),
 ],
 "slot_insulation_damage_history": [
    (r"압착|눌린|눌리|눌림|눌려|짓눌|뭉개|하중|중량물|적치|끼인|맞닿", "ExternalCrushing"),
    (r"꺾|굴곡|굴절|접힌|반복.*움직|굽힘|구부", "RepeatedFlexing"),
    (r"진동", "Vibration"),
    (r"당겨|장력|인장", "Tension"),
    (r"노후|경년|장기간\s*사용|장시간\s*사용|오래", "AgedInsulation"),
    (r"열화|경화|취성|딱딱", "ThermalDegradation"),
    (r"마모|쓸림|긁힘|찢|벗겨|피복\s*손상|피복\s*훼손|박리|천공|날카로", "AbrasionAtPenetration"),
    (r"갈라|균열", "CrackedInsulation"),
    (r"나사|새들|스테이플|고정\s*부품|타카|못", "MisdrivenStaple"),
    (r"소선.*끊|일부\s*단선|가닥.*끊", "StrandFracture"),
 ],
 "slot_additional_visual_evidence": [
    # 이극 도체 사이의 탄화가 곧 트랙이다 — "절연물 표면의 일부가 분해되어
    # 탄화되거나 침식됨에 따라 도전성 물질이 생긴다 ... 다른 극의 전극 간에는
    # 도전성의 통로(Track)가 형성된다" (실무Ⅳ p.147). 일반 탄화와 갈라야 한다.
    (r"탄화된?\s*경로|도전로|트랙", "CarbonizedConductivePath"),
    (r"(단자|전극|극|접점|접속부)\s*(사이|간)[^.]{0,16}탄화|탄화[^.]{0,16}(단자|전극|극)\s*(사이|간)", "CarbonizedConductivePath"),
    # 소선(素線) 끝단의 용융구와 전선 말단의 일반 비드는 다른 것이다.
    # 전자는 반단선 표지지만(실측 4건 중 3건) 후자는 아니다(19건 중 3건, 절연열화가
    # 9건으로 최다). §9.11.6 이 "도체 끝의 비드 자체는 원인을 지시하지 않는다"고
    # 못박은 그것을 매퍼가 우회하고 있었다. 소선·가닥·연선이 명시될 때만 쓴다.
    (r"(소선|가닥|연선)[^.]{0,20}(구슬|구형|용융구|소구|망울)|(구슬|구형|용융구|소구|망울)[^.]{0,20}(소선|가닥|연선)", "SmallMeltBallOnStrandEnd"),
    (r"구슬|구형|소구|망울|끝단[^.]{0,8}용융|말단[^.]{0,8}용융", "ArcBead"),
    (r"소선.*단선|연선.*단선|소선.*끊|일부\s*단선", "StrandFracture"),
    (r"다수의?\s*용융|다수의?\s*용단|여러\s*(곳|개소|군데).{0,10}용융|복수.*용융흔", "MultipleArcBeads"),
    (r"단락흔|용융흔|용융된|녹은|녹아|녹음|융착|유착|용단|전기적\s*특이점|용융물", "ArcMeltMark"),
    (r"비드", "ArcBead"),
    (r"탄화|그을|숯", "InsulationCarbonization"),
    (r"변색|산화|검게", "LocalizedDiscoloration"),
    (r"눌린|압착|찍힘|변형|구부러", "MechanicalDeformation"),
    (r"스패터|비산|튄", "Spatter"),
    (r"광택\s*소실|무광", "LossOfLuster"),
    (r"아산화동", "CuprousOxideGrowth"),
    # 절연물 '내부' 현상 — 화재가 만들 수 없는 절연열화 전용 형태 (실무Ⅳ p.153·254)
    (r"수지상|전기\s*트리|워터\s*트리|트리잉", "DendriticTreePath"),
    (r"외함\s*파열|케이스.{0,4}(구멍|쪼개|파열)|내부.{0,4}탄화|내부.{0,6}유전체", "InternalDamageExceedingSurface"),
    (r"성상\s*변화|경화|취성|딱딱|부풀|팽창", "InsulationEmbrittlement"),
 ],
 "slot_surrounding_combustibles": [
    (r"피복|절연물|전선\s*피복", "InsulationMaterialFuel"),
    (r"샌드위치|단열재|보온재|스티로폼|우레탄", "ThermalInsulationFuel"),
    (r"분진|먼지", "AccumulatedDustFuel"),
    (r"플라스틱|수지|외함|커버|케이스", "EnclosureMaterialFuel"),
    (r"목재|합판|각재|구조재", "WoodStructuralFuel"),
    (r"종이|박스|섬유|의류|천", "PaperTextileFuel"),
    (r"이불|의류|커튼|침구|천막", "PaperTextileFuel"),
    (r"책상|수납장|가구|합판|판넬\s*심재|심재", "WoodStructuralFuel"),
    (r"냉장고|에어컨|기기|가전|멀티탭|콘센트|배전반|분전반", "EnclosureMaterialFuel"),
    (r"가연물|집기|가재도구|적치물|주변", "AdjacentCombustible"),
 ],
}

UNVERIFIABLE = r"확인\s*불가|식별\s*불가|판단\s*불가|불명|소실.*확인.*어려"
ABSENT = r"없었음|없음|발견되지\s*않|미확인|아님|해당\s*없"


def status_of(text, mapped_none):
    if re.search(UNVERIFIABLE, text):
        return "Unverifiable"
    if mapped_none or re.search(ABSENT, text):
        return "ConfirmedAbsent"
    return "Confirmed"


def map_slot(slot, text):
    """(클래스, 상태) 목록과 매핑 실패 여부."""
    out, none_hit = [], False
    for pat, cls in RULES.get(slot, []):
        if re.search(pat, text):
            if cls is None:
                none_hit = True
            elif cls not in [c for c, _ in out]:
                out.append((cls, None))
    st = status_of(text, none_hit)
    return [(c, st) for c, _ in out], (not out and not none_hit)


def load():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    rows = list(wb["Sheet1"].iter_rows(values_only=True))
    hdr = [str(c) if c else "" for c in rows[0]]
    return hdr, [r for r in rows[1:] if any(r)]


def build():
    hdr, data = load()
    slots = [h for h in hdr if h.startswith("slot_")]
    sessions, miss = [], collections.defaultdict(list)
    cov = collections.Counter()
    tot = collections.Counter()
    for r in data:
        rec = dict(zip(hdr, r))
        facts, fuels = [], []
        for s in slots:
            v = str(rec.get(s) or "").strip()
            if not v:
                continue
            tot[s] += 1
            got, failed = map_slot(s, v)
            if failed:
                miss[s].append(v)
            else:
                cov[s] += 1
            for cls, st in got:
                # 착화물은 세션 사실이 아니라 가설의 속성(hasFirstFuel)이다.
                # 착화물을 지목하는 지표 규칙도 없어 점수에 기여하지 않는다.
                # 매핑 커버리지에는 세되 사실 목록에는 넣지 않는다.
                (fuels if s == "slot_surrounding_combustibles" else facts).append(
                    {"cls": cls, "status": st, "agent": "InvestigatorAgent",
                     "slot": s, "src": v})
        sessions.append({
            "case_id": str(rec["case_id"]),
            "actual_scenario": LABEL[str(rec["gt_label"])],
            "facts": facts,
            "fuels": fuels,
            "query_count": sum(1 for s in slots if str(rec.get(s) or "").strip()),
        })
    return sessions, cov, tot, miss


if __name__ == "__main__":
    sessions, cov, tot, miss = build()
    OUT.mkdir(exist_ok=True)
    (ROOT / "cases" / "sessions.json").write_text(
        json.dumps(sessions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'슬롯':36s} {'값':>4s} {'매핑':>5s} {'커버리지':>7s}")
    for s in sorted(tot, key=lambda x: -tot[x]):
        print(f"{s:36s} {tot[s]:4d} {cov[s]:5d} {cov[s]/tot[s]*100:6.0f}%")
    n = sum(len(x["facts"]) for x in sessions)
    print(f"\n사례 {len(sessions)}건, 사실 {n}개 (사례당 {n/len(sessions):.1f})")
    print(f"매핑 실패 {sum(len(v) for v in miss.values())}건 — 어휘의 빈 곳")
    for s, v in sorted(miss.items(), key=lambda x: -len(x[1])):
        if not v:
            continue
        print(f"\n  ■ {s}  {len(v)}건")
        for t in v[:6]:
            print(f"      {t[:72]}")
