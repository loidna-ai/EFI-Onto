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
    (r"통전|전원.{0,3}(인가|투입|공급)|작동\s*(중|상태)|가동\s*(중|상태|을)|점등|사용\s*중|삽입되어", "EnergizedState"),
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
    (r"트립|떨어진|작동\s*확인|작동함|동작함|[Oo][Ff][Ff]|[Oo][Nn]\s*상태|내려감|차단됨|차단된|차단\s*상태|퓨즈\s*단선", "BreakerTripRecord"),
    (r"수동|임의로\s*차단", "BreakerTripRecord"),
 ],
 "slot_fastening_torque": [
    (r"꼬아|꼬여|꼬인|꼬임|비틀림|나선형|임의\s*접속|임의로\s*결합|수동\s*꼬임", "LooseConnection"),
    (r"느슨|헐거|결속력\s*약화|풀림|이완|이탈|불완전", "LooseConnection"),
    (r"절연테이프|전기테이프", "LooseConnection"),
 ],
 "slot_environmental_contamination": [
    # 트래킹의 자리 — 이극 도체 사이 절연물 표면 (실무Ⅳ p.147, 표 2-1 '각종 스위치류 양극간').
    # '스위치·콘센트'라는 낱말만으로는 읽지 않는다 — 다섯 요인에 고루 나온다.
    # 극 사이·기판 표면·버스바 사이처럼 자리가 명시될 때만 읽는다.
    (r"(양극|이극|극|전극|단자)\s*(간|사이)|기판\s*(표면|내부)|(버스바|부스바)[^.]{0,6}(사이|간)", "InterPoleInsulatingSurface"),
    # 기기 안의 오염도 이 자리다 — p.149 "관례적으로 전기기계·기구에 나타나는 경우를 트래킹".
    # 오염 어휘와 기기 어휘가 같은 절에 있을 때만 읽는다. '습도 90%' 만으로는 대상이 없다.
    (r"(분전반|배전반|분전함|차단기|기판|단자|버스바|부스바|릴레이|스위치|콘센트|제어기|기[기구]\s*내부)[^.,]{0,30}(먼지|분진|습기|수분|누수|물기|결로|빗물|이물질|오염)"
     r"|(먼지|분진|습기|수분|누수|물기|결로|빗물|이물질|오염)[^.,]{0,30}(분전반|배전반|분전함|차단기|기판|단자|버스바|부스바|릴레이|스위치|콘센트|제어기)", "InterPoleInsulatingSurface"),
    # 환경 슬롯에 적힌 트래킹 진행 서술 — p.148 1단계 "절연재료 표면의 침식 … 도전로 형성"
    (r"도전로|탄화된?\s*경로|트랙|침식", "CarbonizedConductivePath"),
    (r"먼지|분진|이물질|퇴적물|파지|섬유|실밥|무기질", "DustAccumulation"),
    (r"습기|습한|습도|결로|누수|물기|수분|빗물|우천|강수|침수|물청소", "MoistureExposure"),
    (r"기름|유증|염분|염해|화학|부식성", "SalineOrChemicalExposure"),
    (r"밀폐|방출되지\s*못|보온재|단열재\s*사이|감싸|덮인", "ThermalInsulationEnclosure"),
    (r"다발|묶음|여러\s*가닥.*묶", "BundledWiring"),
    # 슬롯은 환경이지만 진술이 명백히 기계적 응력·관통부인 경우
    (r"진동", "Vibration"),
    (r"관통|천공", "AbrasionAtPenetration"),
    (r"건조|청결|오염\s*없", None),                                     # 부재 확인
 ],
 "slot_pre_ignition_symptoms": [
    (r"불꽃|스파크|아크|섬광|번쩍|불빛|[\'\"‘’“”]?(퍽|펑|뻥)[\'\"‘’“”]?\s*(하는\s*)?소리|폭음|파열음", "PreFireArcObservation"),
    (r"타는\s*냄새|냄새|깜박|점멸|밝기|어둡", "FlickeringOrOdor"),
    (r"차단기.*(내려|떨어|작동)|누전\s*차단기.*이력", "IntermittentRcdTripping"),
    (r"온도|과열|뜨거|발열|연기|전압\s*강하|정전", "AbnormalTemperatureOrVoltageDrop"),
    (r"없었음|없음|발견되지\s*않", None),
 ],
 "slot_insulation_damage_history": [
    (r"압착|눌린|눌리|눌림|눌려|짓눌|뭉개|하중|중량물|적치|끼인|맞닿", "ExternalCrushing"),
    (r"꺾|굴곡|굴절|접힌|반복.*움직|굽힘|구부", "RepeatedFlexing"),
    (r"진동", "Vibration"),
    (r"당겨|장력|인장|늘어[남나]", "Tension"),
    (r"노후|경년|장기간|장시간|오래|\d+\s*년\s*(이상|전|간)?\s*(사용|경과|설치|된|가동)|\d{4}\s*년식|\d+\s*년식|상시\s*연결", "AgedInsulation"),
    (r"열화|경화|취성|딱딱|성상\s*변화|상태\s*변화|열\s*스트레스", "ThermalDegradation"),
    (r"마모|쓸림|긁힘|찢|벗겨|피복\s*손상|피복\s*훼손|박리|천공|날카로", "AbrasionAtPenetration"),
    (r"갈라|균열", "CrackedInsulation"),
    (r"나사|새들|스테이플|고정\s*부품|타카|못", "MisdrivenStaple"),
    # 이 슬롯에도 접속 불량 서술이 온다
    (r"꼬아|꼬여|꼬인|테이프", "LooseConnection"),
    (r"소선.*끊|일부\s*단선|가닥.*끊", "StrandFracture"),
 ],
 "slot_additional_visual_evidence": [
    # 이극 도체 사이의 탄화가 곧 트랙이다 — "절연물 표면의 일부가 분해되어
    # 탄화되거나 침식됨에 따라 도전성 물질이 생긴다 ... 다른 극의 전극 간에는
    # 도전성의 통로(Track)가 형성된다" (실무Ⅳ p.147). 일반 탄화와 갈라야 한다.
    (r"(양극|이극|극|전극|단자)\s*(간|사이)|(버스바|부스바)[^.]{0,6}(사이|간)|기판\s*표면", "InterPoleInsulatingSurface"),
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
    (r"눌린|눌려|압착|찍힘|변형|구부러", "MechanicalDeformation"),
    # 결선 형태는 접속 상태의 관찰이다 — 꼬임·비틀림·나선 접속
    (r"꼰\s*흔적|꼬임|꼬여|비틀림|나선", "LooseConnection"),
    # 반단선의 결정적 형태 — 단선부 양쪽 용흔 (실무Ⅳ p.150). 어휘만 있고 못 읽고 있었다
    (r"(끊어진|단선|파단)[^.]{0,10}양[측쪽][^.]{0,14}(용융|용흔|뭉친)|양[측쪽][^.]{0,10}(끊어진|단선|파단)[^.]{0,14}(용융|용흔)", "MeltMarkOnBothSidesOfBreak"),
    (r"스패터|비산|튄", "Spatter"),
    (r"광택\s*소실|무광", "LossOfLuster"),
    (r"아산화동", "CuprousOxideGrowth"),
    # 시각 슬롯에 적힌 환경 흔적 — 진술이 명백할 때만
    (r"누수\s*흔적|침수\s*흔적|물에\s*의해|수분\s*유입|결로\s*흔적", "MoistureExposure"),
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

UNVERIFIABLE = r"확인\s*불가|식별\s*불가|판단\s*불가|(?<!원인)불명|소실.*확인.*어려"   # 원인불명 누수는 누수가 확인된 것이다
ABSENT = r"없었음|없음|발견되지\s*않|미확인|아님|해당\s*없"


def status_of(text, mapped_none):
    if re.search(UNVERIFIABLE, text):
        return "Unverifiable"
    if mapped_none or re.search(ABSENT, text):
        return "ConfirmedAbsent"
    return "Confirmed"


CLAUSE = r"[,，.。;]|\s및\s|\s그리고\s|으나\s|지만\s|되며\s|되고\s|하며\s|하고\s"


def map_slot(slot, text):
    """(클래스, 상태) 목록과 매핑 실패 여부.

    확인 상태는 슬롯 전체가 아니라 그 표현이 든 절(節)에서 읽는다. "용융 흔적
    식별됨, 내부 부품은 특이점 없음"에서 '없음'은 뒤 절의 것이지 용융흔의
    것이 아니다. "노후 선로로 교체 이력 없음"의 '없음'도 노후의 부재가 아니다.
    슬롯 전체로 읽자 부재 확인 5건 중 3건이 이런 오독이었다.
    """
    out, none_hit = [], False
    clauses = [c for c in re.split(CLAUSE, text) if c and c.strip()]
    for pat, cls in RULES.get(slot, []):
        m = re.search(pat, text)
        if not m:
            continue
        if cls is None:
            none_hit = True
            continue
        if cls in [c for c, _ in out]:
            continue
        clause = next((c for c in clauses if re.search(pat, c)), text)
        out.append((cls, status_of(clause, False)))
    if none_hit and not out:
        return [], False
    return out, (not out and not none_hit)


# ── 대상 슬롯 — 전기적 특이점이 식별된 대상 ──────────────────────────────
# dataset.xlsx 에는 없다. 관찰 전문(cases/observed)에서 뽑는다.
# 대상 어휘는 다섯 요인에 고루 나오므로 '특이점이 붙은 문장'으로 좁힌다.
# 실무Ⅳ p.149 의 관례 — 전기기계·기구에 나타나면 트래킹 — 를 쓰려면 이 슬롯이 있어야 한다.
OBS = ROOT / "cases" / "observed"
SIGN = r"용융|단락흔|특이점|단선|아크|비드|도전로|탄화된?\s*경로|탄화흔|탄화\s*흔적|융착|소결|합선|멸실"
# 특이점 문장이 없으면 발화지점 문장으로 대상을 잡는다 — p.149 는 "전기기계·기구에 나타나는 경우"라 하고
# 조사관은 발화지점에서 그것을 안다. 근거 문장을 남기므로 되짚을 수 있다.
ORIGIN = r"발화지점|발화개소|출화|화재가\s*시작|연소\s*패턴|집중\s*소훼|소훼·탄화\s*강도|발화\s*부위"
NEG = r"식별되지\s*않|발견되지\s*않|발견할\s*수\s*없|관찰되지\s*않|특이점은?\s*인지하지"
OBJECT = [  # 구체적인 것부터. 같은 문장에 둘이면 앞이 이긴다
    # 접속단자·단자대는 양극이 나란한 절연 표면이라 트래킹의 자리다 — "1·2차접속단자나 몰드케이스의
    # 절연체에 먼지 또는 습기에 의한 트래킹" (p.201). 꼬임·결선은 한 극의 이음이라 다르다.
    ("단자",          r"접속단자|단자대|단자함|터미널|접속핀|연결\s*볼트|단자\s*(부|접속)"),
    ("접속부",        r"접속부|결선|꼬임|비틀림\s*접속|압착\s*단자|커넥터|칼받이|칼날받이"),
    ("기기 내부 절연부", r"차단기|분전반|배전반|분전함|기판|릴레이|제어기|버스바|부스바|전자개폐기|마그네트|인버터|장치\s*내부|기[기구]\s*내부"),
    ("배선기구",      r"콘센트|플러그|스위치|멀티탭|소켓|리셉터클"),
    ("권선·코일",     r"권선|코일|모터|컴프레서|압축기|안정기|트랜스|변압기"),
    ("콘덴서",        r"콘덴서|캐패시터|커패시터"),
    ("전선·코드",     r"전선|코드|케이블|열선|배선|전원선|인입선|리드선"),
]


OBJECT_CLASS = {"단자": "TerminalSite", "접속부": "ConnectionJointSite", "기기 내부 절연부": "DeviceInteriorSite",
                "배선기구": "WiringDeviceSite", "권선·코일": "WindingSite", "콘덴서": "CapacitorSite",
                "전선·코드": "CordMidspanSite"}


def origin_object(case_id):
    """(대상, 상태, 근거 문장). 관찰 전문이 없거나 특이점 문장이 없으면 미기재."""
    f = next((x for x in OBS.glob("*.txt") if x.stem.upper() == case_id.upper()), None)
    if not f:
        return None, "Missing", ""
    text = f.read_text(encoding="utf-8")
    sents = [x.strip() for x in re.split(r"[.\n]", text)
             if re.search(SIGN, x) and not re.search(NEG, x)]
    if not sents:
        sents = [x.strip() for x in re.split(r"[.]|" + chr(10), text) if re.search(ORIGIN, x)]
    if not sents:
        if re.search(UNVERIFIABLE, text):
            return None, "Unverifiable", ""
        return None, "Missing", ""
    votes = collections.Counter()
    src = {}
    for x in sents:
        # "콘센트 하부에 소락되어 있던 전원선의 단락흔" — 특이점은 전원선에 있다.
        # 특이점 낱말 바로 앞(40자)에서 가장 가까운 대상 낱말을 잡고, 없으면 문장 전체에서 잡는다.
        # 다만 기기·단자가 문장에 있으면 그것이 자리다 — 트래킹은 기기 절연 표면에서 일어나고
        # 녹는 것은 그 안의 전선이다 (p.201). '무엇이 녹았나'보다 '어디 안인가'가 먼저다.
        picked = next((name for name, pat in OBJECT if name in ("단자", "기기 내부 절연부") and re.search(pat, x)), None)
        for m in re.finditer(SIGN, x):
            if picked:
                break
            head = x[max(0, m.start() - 40):m.start()]
            best = max(((mm.end(), name) for name, pat in OBJECT for mm in re.finditer(pat, head)),
                       default=None)
            if best:
                picked = best[1]
                break
        if picked is None:
            picked = next((name for name, pat in OBJECT if re.search(pat, x)), None)
        if picked:
            votes[picked] += 1
            src.setdefault(picked, x)
    if not votes:
        return None, "Missing", sents[0]
    best = max(votes, key=lambda n: (votes[n], -[o[0] for o in OBJECT].index(n)))
    return best, "Confirmed", src[best]


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
        obj, ost, osrc = origin_object(str(rec["case_id"]))
        # 대상은 사실로 들어간다. 자리 도출은 온톨로지의 D-13 이 한다 — 판독기는 읽기만 한다.
        if obj:
            facts.append({"cls": OBJECT_CLASS[obj], "status": ost, "agent": "InvestigatorAgent",
                          "slot": "slot_origin_object", "src": osrc})
        sessions.append({
            "case_id": str(rec["case_id"]),
            "actual_scenario": LABEL[str(rec["gt_label"])],
            "origin_object": {"value": obj, "status": ost, "src": osrc},
            "facts": facts,
            "fuels": fuels,
            "query_count": sum(1 for s in slots if str(rec.get(s) or "").strip()) + (1 if obj else 0),
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
