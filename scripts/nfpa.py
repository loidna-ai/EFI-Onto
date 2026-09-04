# -*- coding: utf-8 -*-
"""NFPA 921 (2024) 절 대조표. 이식이 얼마나 남았는지의 분모를 만든다.

절 목록은 2024판 목차에서 옮긴 것이다. 원문을 받은 절만 하위 절까지 내려가 있고
나머지는 절 제목 수준의 근사치다. 내려갈 때마다 이식률은 대체로 낮아진다 —
제목으로는 덮인 듯 보이던 요건이 드러나기 때문이다. 낮아진 숫자가 정확한 숫자다.

2026-09-03 제공 이미지로 §9.4·9.7·9.8·9.12 본문 전체를 대조했다.
자료 수신 범위와 판정 근거는 docs/NFPA_추가자료_대조.md. 원문 확인과 구현 완료는 다르다.

주의 — 단서 규칙(Table 2)은 NFPA 가 아니라 국내 실무·선행연구에서 왔다.
여기에 조항을 붙이면 출처가 왜곡된다. 조항은 방법론 층에만 붙인다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import sys, pathlib

DONE, PART, NONE, OUT, PROC = "구현", "일부", "없음", "범위밖", "현장절차"
# PROC = 이론에는 있으나 온톨로지가 표현할 대상이 아닌 것(도체 취급·촬영·표식 등
#        현장 작업 절차). 분모에서 뺀다. 빼지 않으면 100%는 도달 불가가 되고
#        그 순간 이 지표는 무시된다.

# (절, 제공 파일, 이번에 직접 확인한 범위, 추가로 필요한 범위)
SOURCE_REVIEW = [
    ("9.4", "9.4.png", "본문 전체", "없음"),
    ("9.7", "9.7_A.png + 9.7_B.png", "본문 전체 (§9.7~9.7.5.4)", "A.9.7.4 미확보·보류 (사용자 보유 자료에 없음; 후속 작업의 선행 조건 아님)"),
    ("9.8", "9.7_B.png + 9.8.png", "본문 전체 (§9.8~9.8.3.2)", "없음"),
    ("9.12", "9.11.png + 9.12.png", "본문 전체 (§9.12~9.12.7.2)", "없음"),
    ("TIA 24-1", "NFPA 공식 TIA_921_24_1.pdf (2025-04-30 발효)", "신설 §9.10.2.1·A.9.10.2.1 및 후속 조항 번호 변경", "없음"),
]

# (절, 제목, 상태, 우리 쪽 대응 또는 빠진 내용)
SECTIONS = [
    # ── Chapter 4 Basic Methodology ────────────────────────────────────────
    ("4.1",  "Nature of Fire Investigations",        PART, "P1~P5 의 전제. 명시적 모형은 없음"),
    ("4.2",  "Systematic Approach",                  DONE, "InvestigationSession 절차"),
    ("4.3",  "Relating to the Scientific Method",    DONE, "P3 반증 우선, F-1, C-2"),
    ("4.4",  "Basic Method of a Fire Investigation", DONE, "가설수립 → 검증 → 확정 3단계"),
    ("4.5",  "Expert Opinions",                      DONE, "CertaintyLevel 과 C-12~C-16. 하위 절 표 참조"),
    ("4.6",  "Review Procedure",                     DONE, "검토 3종과 각각의 한계. C-17~C-20. 하위 절 표 참조"),
    ("4.7",  "Reporting Procedure",                  PART, "InvestigationReport 와 reportsConclusion. "
                                                           "형식·전달 경로는 소관에 따라 달라져 열거하지 않는다"),
    # ── Chapter 9 Electricity and Fire ─────────────────────────────────────
    ("9.1",  "Introduction",                         OUT,  "장 개요. 요건이 없다(판단)"),
    ("9.2",  "Basic Electricity",                    OUT,  "전기 기초 이론. 배경 지식이라 판정에 쓰이지 않는다(판단)"),
    ('9.3', 'Building Electrical Systems', DONE, '인입구 무보호 구간과 관심 영역의 공급망. ElectricalSystemModel·PowerSource·ElectricMeter 및 확인된 연결. 전압·인입 방식의 상세 계측은 기존 범위 결정 유지'),
    ('9.4', 'Service Equipment', DONE, 'ServiceEquipment와 계량기·주차단·분기·부하를 ConnectionRecord로 연결. Supply·Protection·SwitchControl 기능을 구분하고 확인된 공급 경로를 조회한다'),
    ("9.5",  "Grounding",                            DONE, "본딩 경로와 중성선 단선. C-21 로 잘못된 추론을 막는다"),
    ("9.6",  "Overcurrent Protection",               DONE, "BreakerTripRecord, D-1 과부하, GFCI·AFCI. 동작 특성을 표 2-18·2-19 로 물화 — 규정 동작시간을 넘겨도 동작하지 않으면 보호장치 부동작"),
    ('9.7', 'Branch Circuits', PART, '계통·도체 역할(T01), 접속 금속·도금(T15), 출처 범위를 갖춘 허용전류·절연·다발·정격 대조(T16)를 구현했다. 고압 공기 절연의 잔여는 T25 범위제외에 연결한다'),
    ('9.8', 'Outlets and Devices', DONE, '스위치·극별 연결·내장 보호장치·단자 접속(T01·T07)과 출처 범위를 갖춘 도체·보호장치·연결 기기 정격 대조(T16)를 구현했다'),
    ('9.9', 'Ignition by Electrical Energy', PART, '최초 착화물·열전달 근거(T04)와 절연재의 재질·충전재·가열·수분 이력(T14)을 연결했다. 실험 수치의 보편 임계값 이식은 T24 범위제외로 남긴다'),
    ("9.10", "Interpreting Damage to Elec. Systems", DONE, "DamagePattern 축, M-1~M-3, C-37~C-39. 하위 절 표 참조"),
    ("9.11", "Identification of Damaged Conductors", DONE, "1차/2차 단락흔 F-2, 통념 부정 C-37. 하위 절 표 참조"),
    ('9.12', 'Electrical System Examination', DONE, '관련 계통·검사 범위와 공급원별 사건·AMI 수집 범위·사후 취급을 구조화(T01~T03). 외부 전력사 연동과 현장 안전 수행은 별도'),
    ("9.13", "Arc Surveys",                          DONE, "F-5, C-6~C-8, D-4~D-5 로 구현. 하위 절 표 참조"),
    ("9.14", "Static Electricity",                   OUT,  "5대 요인 밖. 범위 제외 (재검토 여지)"),
    ("9.15", "Batteries",                            OUT,  "5대 요인 밖. ESS·리튬 화재를 넣을지 결정 필요"),
    # ── Chapter 19 Fire Cause Determination ────────────────────────────────
    ("19.1", "Introduction",                         OUT,  "장 개요. 요건이 없다(판단)"),
    ("19.2", "Overall Methodology",                  DONE, "세션 절차"),
    ("19.3", "Data Collection",                      DONE, "Fact, ConfirmationStatus, PROV-O (C-4)"),
    ("19.4", "Analyze the Data",                     DONE, "M-1~M-4, C-44·C-45 발화 순서 요인과 추론 근거. D-15 가설 형성 — 필요조건 또는 특이 흔적이 자료에 있어야 세운다(§19.4.1)"),
    ("19.5", "Developing Cause Hypotheses",          DONE, "C-29 발열 기기 목록, C-46 경합 발화원 미특정 공개"),
    ("19.6", "Testing the Hypothesis for Validity",  DONE, "F-1~F-4, C-28·C-30·C-31, D-7·D-8. 하위 절 표 참조"),
    ("19.7", "Selecting the Final Hypothesis",       DONE, "Conclusion, C-2, 확정 조건"),
    ("19.8", "Fire Incident and Cause Classification", DONE, "분류 구조는 구현(C-9~C-11·C-62). 보고용 원인 분류의 채택 체계는 "
                                                             "국내 보고규정 세부분류 하나이며 가설 대응과 도출은 D-20(T20). NFPA 참조 체계 여섯은 코드 목록 없이 참조 개체로만"),
]

# 9.13 하위 절. 원문 확인 후 좁힌 것. 나머지 절도 이 수준까지 내려가야 한다.
SUBSECTIONS = [
    ("9.3.2",    "단상·삼상 인입 전압과 결선",              OUT,  "배경 지식. 판정에 쓰이지 않는다(판단)"),
    ("9.3.2.1.2", "hot·neutral·ground 표준 용어 정렬",      DONE, "UngroundedConductor 등 SKOS altLabel"),
    ("9.3.3",    "계량기와 계량기함",                      OUT,  "배경 지식. 판정에 쓰이지 않는다(판단)"),
    ("9.3.4",    "인입구는 과전류 보호가 없어 고장이 지속된다", DONE, "D-6 SustainedFaultingRuleShape, ServiceEntrance"),
    ("9.5.1.1",  "본딩은 저임피던스 귀로를 만든다",           PART, "BondingPath 클래스. 임피던스 판정은 없음"),
    ("9.5.2",    "중성선 단선 과전압과 거주자 진술",          DONE, "OpenNeutral, OpenNeutralOvervoltage, 진술 2종"),
    ("9.5.2b",   "접지극 제거는 중성선 단선의 원인이 아니다",   DONE, "C-21 OpenNeutralInferenceShape"),
    ("9.6.1",    "보호장치는 자동 동작이 요건이다",           DONE, "C-22 ProtectedSustainedFaultShape"),
    ('9.6.4.1', '분전반 아크 손상만으로 발화원을 단정할 수 없다', DONE, 'DamageComparison의 내부·외부 위치·손상·노출 근거를 대조(T05). 분전반 아크·단독 산화를 원인 또는 hasFact로 자동 승격하지 않는다'),
    ("9.6.4.2",  "화재 후 분전반 보존·회수·실험실 검사",       PROC, "9.7_A.png. 가능하면 현장에서 분해하지 않고 소부품·잔해를 보존한다"),
    ('9.6.4.3', '분전반 안팎 아크와 최초 아크 도체의 비교', DONE, '계통·함체 연결과 PanelInsideOutside 비교(T05). 외부 위치는 명시적으로 확인하며 함체 미기록을 외부라고 읽지 않는다'),
    ("9.7.1",    "배선 도체의 주재료는 구리·알루미늄",          OUT, "재료 기초. 재질별 손상 판정은 §9.7.3.2·9.7.4.1에서 별도로 센다"),
    ("9.7.2",    "AWG 도체 크기와 분기회로 허용전류 표",        DONE, "T16: AWG·mm² 크기 체계와 값, 재질, 표의 허용전류 범위·용도를 출처 기록으로 표현한다. 표 9.7.2는 ContextOnly로 저장하여 국내 보편 임계값으로 쓰지 않는다"),
    ("9.7.2.1",  "알루미늄 분기배선의 접속부 과열 문제",         DONE, "T15: 도체 재질·등급·크기·단선/연선, 접점 모재·도금, 접속 방식·용도·지역·연도·기기 적합 표시·승인 확인을 문헌 범위와 대조한다. "
                                                          "소구경 분기배선 설명을 대형 인입선이나 모든 지역·시기의 알루미늄 접속에 일반화하지 않는다"),
    ("9.7.2.2",  "도체 허용전류는 크기·절연·다발 조건에 따른다",  DONE, "T16: 관할·문서·판본과 재질·크기·절연·포설·다발 수·용도가 명시된 외부 기준만 실제 부하·보호장치 정격과 대조한다. 초과 결과에서 과부하 원인을 자동 생성하지 않는다"),
    ("9.7.3.1",  "순동의 조직·연성·융점",                   OUT, "재료 기초. 융점만으로 발화 원인을 판정하지 않는다"),
    ("9.7.3.2",  "화재 노출 구리의 산화·환원과 표면색",        DONE, "화재가 만드는 CuprousOxideDeposit를 증식과 분리. D-3은 확인 상태·성분·증식 형태를 함께 요구한다"),
    ("9.7.4.1",  "순알루미늄 산화막의 용융 형상 보존",          DONE, "PureAluminumConductor·OxideRetainedAluminumMelt. C-53 재질별 아크 판별 근거 확인. A.9.7.4는 미확보·보류"),
    ("9.7.4.2",  "동피복 알루미늄의 허용전류·물성",           OUT, "재료 기초. 구리 피복이 있어도 허용전류와 물성은 알루미늄과 유사하다는 설명"),
    ("9.7.5.1",  "절연의 기능과 공기 절연 파괴",              PART, "Insulation·균열 내 도전성 용액은 있으나 고전압·오염에 따른 공기 절연 파괴는 표현하지 않는다"),
    ("9.7.5.1.1", "절연 종류·정격·제조 정보의 표기",           OUT, "식별을 위한 기초 정보. 참조된 NFPA 70 표 310.4(1)은 이번 자료에 없다"),
    ("9.7.5.1.2", "도체 역할에 따른 피복 색상",               OUT, "미국 배선의 식별 관례. 색상만으로 국내 설비의 도체 역할을 확정하지 않는다"),
    ("9.7.5.2",  "PVC 분해와 염화수소·수분에 의한 금속 부식",   DONE, "ContactCorrosion는 화재도 가능한 관찰 양상. D-17은 발화 전 존재가 확인될 때만 CorrodedConnection을 도출"),
    ('9.7.5.3', '고무 절연의 취화와 화재 후 취급 균열', DONE, 'ComponentExamination의 절연 재질과 Bending/TensionHandling/Disassembly 사건·관찰 시각을 분리. 사후 관찰을 형성 시각으로 대체하지 않는다'),
    ("9.7.5.4",  "기타 절연재의 용도와 열적 특성",             OUT, "폴리에틸렌·나일론·실리콘·플루오로폴리머의 재료 기초"),
    ('9.8.1', '스위치는 비접지 도체를 개폐한다', DONE, 'ElectricalSwitch·componentRole·SwitchControl 연결로 스위치와 개폐 도체·조명의 관계를 기록. 연결 구조에서 통전 상태를 추정하지 않는다'),
    ('9.8.2', '콘센트의 정격·접지형·극성', DONE, '극별 연결·단자 표시·접속 방식(T01·T07)과 연결 기기의 실제 표시 정격 및 출처가 요구하는 최소 정격의 조건부 대조(T16)를 구현'),
    ('9.8.2.1', '콘센트 내장 GFCI', DONE, 'GroundFaultProtectiveDevice를 componentContainer로 콘센트에 연결하여 내장 보호장치와 독립 보호장치를 구분'),
    ('9.8.2.2', '콘센트 단자·나사·꽂음식 접속', DONE, 'TerminationRecord로 도체·단자·기기·연결 기록·단자 표시를 연결. ScrewTerminal·PushInSpring·PushInScrewClamp·WireWrapPin 등을 구분하고 구조 식별·토크 비교 완료 주장을 검증(T07)'),
    ('9.8.3', '고정 조명과 상시 연결 발열기기', DONE, '고정 배선은 Supply, 스위치·조광기 등의 제어 관계는 SwitchControl로 구분한다. 플러그 존재는 공급 경로의 전제가 아니다'),
    ('9.8.3.1', '산업 설비의 직접 배선과 접촉기 제어', DONE, '부하의 직접 공급 연결과 별도 제어 관계를 Supply·SwitchControl로 분리하여 같은 계통 모델에 기록'),
    ("9.8.3.2",  "폭발성 분위기에서의 방폭 기구",              OUT, "방폭 설비의 설치·격리 기능은 현재 전기 발화 메커니즘 감별 범위 밖"),
    ('9.9.1', '발화 성립의 두 조건 — 통전과 충분한 열', DONE, 'C-57 통전 필요조건과 FirstFuelAssessment·HeatTransferAssessment. 온도만으로 충분성을 확정하지 않고 지속 시간·연료 상태·열전달 근거를 요구'),
    ("9.9.1.1",  "열전달이 충분히 오래 유지돼야 한다",         OUT,  "지속 시간은 잔해에서 관측되지 않는다. 가설 시험 시 "
                                                          "참조하는 공학 지식이지 감식 대상이 아니다(판단)"),
    ("9.9.1.2",  "에너지가 충분해도 착화가 보장되지 않는다",     DONE, "HeatDissipationImpairment 갈래. 와트 계산이 아니라 "
                                                          "관측 가능한 형태(단열 매입·다발·적치)로 담았다"),
    ('9.9.1.3', '온도와 지속 시간이 초기 연료에 맞아야 한다', DONE, 'HeatTransferAssessment에 지속 시간·연료 상태·열 충분성 근거. 공통 온도/시간 문턱을 지어내지 않고 최종 결론의 근거 유무를 검증'),
    ("9.9.1.4",  "발열원·충분성·열전달 경로 셋을 식별",        DONE, "C-32 HeatTransferPathShape"),
    ("9.9.2.4",  "접속 불량 — 산화막 발열 30~40 W",          DONE, "PoorContactHeating·GlowingConnection 사슬. 수치는 "
                                                          "가설 시험 시 참조하는 지식이라 규칙으로 두지 않는다(판단)"),
    ("9.9.3.2",  "과부하 발화는 보호가 정상이면 드물다",        DONE, "C-34 OverloadIgnitionRarityShape"),
    ("9.9.4.1",  "350 V 미만 자발 아크 없음. 고체 착화 어려움",  DONE, "C-33 개시 경위, C-36 연료별 착화 역량"),
    ("9.9.4.4",  "통상 파팅 아크는 가스·증기·분진만 착화",      DONE, "ignitableByBriefArc, C-36 ArcFuelCompetenceShape"),
    ("9.9.4.5",  "탄화는 화재 열로도 생긴다 — 통전만이 아니다",  DONE, "ExternalFlame 도 CarbonizedConductivePath 를 낸다"),
    ('9.9.4.5.1', '탄산칼슘 함유 PVC의 자체 습윤 — 가열·대기 수분 조건', DONE, 'T14: 재질·충전재 식별, 가열 온도·발생 범위, 표면 수분 존재·유래를 독립 기록으로 연결한다. 110°C는 본문 설명 조건으로 보존하며 충분·필요 판정 문턱으로 쓰지 않는다. 자료 완비·발화 전 선후와 메커니즘 성립을 구분한다. T13 인과 경로 보류는 유지'),
    ("9.9.5.2",  "알루미늄 스파크·분기회로 스파크의 효율",       OUT,  "입자 재질·크기는 잔해에서 판별되지 않는다(판단)"),
    ("9.9.6",    "고저항 고장은 화재 후 발견이 어렵다",         OUT,  "발견 난이도는 조사 여건이지 판정 대상이 아니다(판단)"),
    ("9.10.1",   "단락·지락 파팅 아크 — 화재로도 생긴다",     DONE, "F-2 시간 선후 판정"),
    ("9.10.2",   "화재 탄화를 통한 아크 — 여러 지점에 남는다",   DONE, "MultipleArcBeads 를 외부화염도 내도록 정정"),
    ("9.10.2.1", "TIA 24-1: 화재열·저산소·피복·전압별 탄화 아크 연구", DONE, "F-2·C-8 외관만으로 원인 판정 금지. F-5는 미발견을 사건 부재로 도출하지 않는다. 30/60 V 시험 결과를 보편 임계값으로 쓰지 않는다"),
    ("9.10.2.2", "인입 도체 지속 고장과 용융·소실",           DONE, "D-6·SustainedFaulting. TIA 24-1로 인쇄본 §9.10.2.1에서 이동"),
    ("9.10.2.3", "버스바 아크는 전원 반대쪽으로 이동한다",      DONE, "C-39 BusBarArcTravelShape. TIA 24-1로 인쇄본 §9.10.2.2에서 이동"),
    ('9.10.3.1', '과열 접속부의 형태 특징 열세 가지', DONE, 'HeatingCharacteristic01~13 항목별 관찰·출처 및 기존 어휘 대응. 동종 금속·동등 노출 비교를 연결한다. 원문의 하나 이상을 유지하며 전항목 충족이나 단독 원인 규칙으로 쓰지 않는다'),
    ("9.10.3.3", "발광 접속부 증거는 외부 화재와 구별된다",      DONE, "MoltenOxideMass 등 3종을 접촉불량 전용으로"),
    ("9.10.4.1", "슬리빙과 오프셋. 용융은 발화의 증거가 아니다",  DONE, "Sleeving, MeltOffset, C-38"),
    ("9.10.5",   "기계적 홈·눌림은 아크흔과 구별된다",          PART, "MechanicalGouge 클래스. 미세 판별 규칙은 없음"),
    ("9.10.6.1", "설치 시 망치 오타격 — 시간이 지나 발현",      DONE, "HammerMisHitDamage 선행 조건"),
    ("9.11.1",   "언더사이즈 도체는 원인의 증거가 아니다",       DONE, "C-37 MisconceptionShape"),
    ("9.11.3",   "균열만으로는 누설 전류가 흐르지 않는다",       DONE, "C-40 CrackedInsulationLeakageShape"),
    ("9.11.4.3", "못·스테이플로의 금속 전이는 화재 결과일 수 있다", DONE, "MetalTransferToFastener, MisdrivenStaple"),
    ("9.11.5",   "분기회로 단락은 통상 피복을 착화시키지 않는다",   DONE, "C-41 ShortCircuitIgnitionShape"),
    ("9.11.6",   "도체 끝 비드 자체는 원인을 지시하지 않는다",     DONE, "C-8 ArcMeltAloneShape 에 포섭"),
    ('9.12.1', '전기적 위험·피해 범위·발화원·아크 조사', DONE, 'ComponentExamination에 계통별 손상·미접근·아크 지점 관찰 상태를 기록. 전선관·접지면도 대상이며 안전 절차의 실제 수행은 별도'),
    ("9.12.2",   "예비 관찰로 해당 건물의 전기 계통 파악",      PROC, "손상 해석에 필요한 계통 이해. 규모·복잡도에 따라 구조물 일부로 조사 범위를 제한할 수 있다"),
    ("9.12.3",   "전원 격리·재통전 방지·무전원 확인",          PROC, "주공급 외 태양광·발전기·UPS 등 복수 전원을 확인하는 현장 안전 절차. "
                                                          "조사 전 무전원 확보는 발화 당시 DeEnergizedState의 근거가 아니다"),
    ("9.12.4",   "관심 영역에 전원을 공급하는 관련 계통 검사",   DONE, "C-43 SupplyPathCoverageShape의 범위와 일치. 통상 전원부터 시작하며 "
                                                          "전원은 건물 밖이나 내부 밀폐 공간에도 있을 수 있다. 건물 전체 무조건 검사가 아니다"),
    ("9.12.5",   "사건별로 인입 설비의 조사 항목 결정",        PROC, "필요 항목·검사 깊이는 사건에 따라 다르며, condition은 일반적으로 외관 관찰을 뜻한다"),
    ("9.12.5.1", "배전 변압기의 상태·명판·배선·정격 기록",      PROC, "9.11.png의 마지막 문장이 9.12.png 첫 문단으로 이어진다. "
                                                          "전압·상수·용량·배선·접지 상태와 공급자 정보를 확인하는 조사 절차"),
    ("9.12.5.2", "인입 도체의 가공·지중 상태 기록",           PROC, "공급 도체의 외관과 상태를 문서화"),
    ('9.12.5.3', '차단 시각과 아크 발생 선후', DONE, 'ElectricalEventRecord의 공급원·사건 시간 범위를 비교. 복전 이력의 범위가 확인된 때만 동일 공급원의 차단 후 아크 모순을 검출'),
    ("9.12.5.4", "인입 구성요소와 접속·스위치 상태 기록",       PROC, "인입선·기둥·개폐장치·접속부·차단기·퓨즈 등 현장 문서화"),
    ("9.12.5.5", "계량기 보존·분리 후 검사",                 PROC, "사진·상태 기록 및 전력 공급자에 의한 분리 후 부품 검사"),
    ('9.12.5.5.1', '스마트미터 AMI의 사용량·정전 기록', DONE, 'PowerRecordCoverage에 실제 확보 여부·수집 종류·기간·복전 이력 완전성을 기록. 미확보를 정전/복전 부재로 읽지 않는다. 전력사 API 연동은 별도'),
    ("9.12.6",   "구내 배선 계통과 검사 깊이",                PROC, "현장 상황에 따른 외관 검사·추가 상세 검사"),
    ("9.12.6.1", "목격·영상·손상 범위로 조사 영역 결정",        PROC, "원인 조사에 필요한 구내 배선 조사 범위를 정하는 현장 절차"),
    ("9.12.6.2", "분전반 검사 열한 항목",                    PROC, "외관·차단기 위치·회로표·화재 후 조작 여부·내부·도체 접속·본딩·개조·아크 등을 기록. "
                                                          "차단기 현재 위치와 화재 이후 조작 이력을 구별한다"),
    ("9.12.6.3", "벽 내부 배선 접근과 잔해 속 전기기구 조사",    PROC, "손상 벽 내부와 잔해에서 배선·기구를 찾아 조사하는 현장 절차"),
    ("9.12.7.1", "코드·플러그·기타 이동형 배선 검사",          PROC, "코드 세트·연장선·이동식 전원탭 등의 아크 지점 검사"),
    ("9.12.7.2", "분해 전후 아크 조사와 증거 훼손 고려",        PROC, "부속품을 떼기 전 조사하고 분해 중 내부 도체를 확인한다. 전문 인력에 의한 반출 검사 가능"),
    ("9.11.2",   "니크·연신의 추가 발열은 무시할 수준이다",      DONE, "C-37 MisconceptionShape"),
    ("9.13.1.2", "조사 미완이면 결론은 조사 범위로 제한",   DONE, "C-7 ArcSurveyScopeShape"),
    ("9.13.1.3", "아크인지 다른 손상인지 금속조직 판정",     PART, "MaterialsAnalyst 행위자는 생겼다. 판정 규칙은 없음"),
    ("9.13.2.1", "회로 최하류 아크 지점 기록",             DONE, "D-5 FurthestDownstreamRuleShape. D-10 이 노출 국부·과전류 보호 확인 아래서만 지시력을 세우고 C-59 이 결론에서 읽는다"),
    ('9.13.2.2', '회로별 보호장치 종류와 상태 기록', DONE, '회로·보호 연결과 DeviceStateRecord의 On/Off/Tripped/FuseOpen/Unknown. 발견 상태와 자동 동작·수동 조작 사건은 별도'),
    ('9.13.3.1', '아크 지점이 나타날 수 있는 위치', DONE, 'Conduit·GroundedSurface 및 구성요소 검사 기록. 아크 지점 미발견은 사건 부재나 비통전으로 도출하지 않는다'),
    ("9.13.3.2", "전선관 내 도체 인출과 방향 유지",         PROC, "현장 작업 절차"),
    ("9.13.3.3", "전 둘레 육안·촉진 검사",                 PROC, "현장 작업 절차"),
    ("9.13.3.4", "원상 기록 후 피복 제거",                 PROC, "현장 작업 절차"),
    ("9.13.3.5", "현장 검사와 실험실 반출 선택",           PROC, "현장 작업 절차"),
    ("9.13.4.2", "전위가 다른 쪽 대응 손상 확인",           DONE, "D-4 CorrespondingDamageRuleShape. C-61 이 발화지점 근거 단락흔에 권고로 읽는다 — 원문이 확률 서술이라 위반이 아니다"),
    ("9.13.4.3", "아크 지점 표식과 사진 기록",             PROC, "현장 작업 절차"),
    ("9.13.4.5", "아크 용융 부재도 기록 — 미조사와 구분",    DONE, "F-5 ArcSiteAbsenceRuleShape"),
    ("9.13.4.6", "용융이 아크 지점을 지웠을 가능성",         DONE, "F-5 + C-6 ObscuredArcSiteShape"),
    ("9.13.4.7", "아크 용융흔 단독은 통전 사실만 말한다",     DONE, "C-8 ArcMeltAloneShape"),
    ("4.1.0",    "발화 지점을 먼저, 그다음 원인",            OUT,  "발화 지점 특정은 이 프로젝트 범위 밖(설계계획서 1.1)"),
    ('4.3.1', '문제 인식 — 무엇을 물을 것인가', DONE, 'InvestigationProblemRecord의 확인 상태·질문 진술·출처와 해결 계획을 연결(T06)'),
    ('4.3.2', '문제 정의 — 어떻게 풀 것인가', DONE, 'InvestigationPlanRecord의 범위·방법·필요 전문성과 VerificationRecord의 실제 결과·관측 근거를 연결. 완료 주장과 미확인을 검증(T06)'),
    ("4.3.3",    "자료 수집 — 검증 가능한 경험적 자료",       DONE, "Fact, ConfirmationStatus, SOSA·PROV (C-4)"),
    ("4.3.4",    "자료 분석 — 수집·목록화는 분석이 아니다",    DONE, "C-26 DataAnalyzedShape"),
    ("4.3.5",    "가설 수립(귀납) — 경험적 자료에서만",       DONE, "IgnitionScenario, P2"),
    ("4.3.6",    "가설 검증(연역) — 반증을 설계한다",         DONE, "F-1, C-25 UndeterminedOutcome, D-7"),
    ("4.3.6.1",  "시험 불가능한 가설은 무효다",              DONE, "C-23 UntestableHypothesisShape"),
    ("4.3.7",    "최종 가설 선택 — 대안 미고려는 중대 오류",   DONE, "C-24 AllHypothesesTestedShape, C-2"),
    ("4.3.8",    "예단 금지 — 자료 전에 가설 없다",          DONE, "C-27 NoPresumptionShape"),
    ("4.3.9",    "기대 편향",                            OUT,  "성급한 가설이 질의를 유도했는지는 조사 과정의 기록이지 "
                                                          "잔해에서 판정되지 않는다(판단)"),
    ("4.3.10",   "확증 편향 — 같은 자료가 반대 가설도 지지",   DONE, "M-4 EvidentialAmbiguityRule 로 형태 밖까지 넓혔다"),
    ("4.5.0",    "의견은 자료와 한계를 밝혀야 한다",          PART, "C-15 한계 명시. 과학적 방법 적용 서술은 §4.7 보고서 영역"),
    ("4.5.1.1",  "개연·가능 두 표현. 대등하면 가능까지",       DONE, "CertaintyLevel, C-12 EqualLikelihoodShape"),
    ("4.5.1.2",  "의심은 전문가 의견이 아니다",              DONE, "C-13 SuspectedNotOpinion, C-14 CertaintyStated"),
    ("4.5.2",    "유일하고 신뢰할 수 있는 최종 가설",         DONE, "C-16 UniqueFinalHypothesisShape"),
    ("4.6.1",    "행정 검토 — 절차와 서류 구비",             DONE, "AdministrativeReview"),
    ("4.6.1.1",  "행정 검토는 실질 비평을 못 한다",           DONE, "C-18 AdministrativeReviewScopeShape"),
    ('4.6.2', '기술 검토 — 자격과 자료 접근이 전제', DONE, 'TechnicalReviewRecord가 전체/선택 요청 범위와 범위별 전문성·자료 접근·실질 비평을 대조. 특정 자격 제도를 보편 기준으로 쓰지 않는다(T06)'),
    ("4.6.2.1",  "기술 검토의 확증 편향 위험",               DONE, "C-48 TechnicalReviewBiasShape 검토자 관계 공개"),
    ("4.6.3",    "동료 검토 — 독립성·객관성",               DONE, "C-17 PeerReviewIndependenceShape"),
    ("4.6.3.2",  "동료 검토는 자료 오류를 잡지 못한다",        DONE, "C-20 ReviewValidationShape"),
    ('19.4.4.2', '발화 순서 — 사건과 조건의 선후', DONE, '사건별 시간 범위와 출처를 비교하여 recordPrecedes를 도출. 같은 구성요소의 아크·화염 도달 선후만 실제 사건의 time:before로 연결'),
    ("19.4.4.2.1", "발화 기여 요인 일곱 가지",              DONE, "IgnitionSequenceFactor 7종, C-44"),
    ("19.4.4.3", "발화원 미발견 시 순서 추론의 조건",         DONE, "InferenceWarrant 5종, C-45"),
    ("19.5.0",   "증거가 없다는 이유로 배제하지 말라",         DONE, "C-1 반증은 확인·부정 확인만. 확인 불가는 반증이 못 된다"),
    ("19.5.1",   "발화부 발열 기기는 반드시 목록에",          DONE, "C-29 HeatProducingDeviceListedShape"),
    ("19.5.2",   "회수 불가 발화원 — 라이터·정전기·낙뢰",      PART, "NonRecoverableIgnitionSource 클래스. 존재 판정 규칙은 없음"),
    ('19.5.3', '각 발화원에 대해 연료 존재를 세워야 한다', DONE, '후보의 미확인은 허용하되 ConclusionFirstFuelEvidenceShape가 최종 결론의 연료 존재·확인·출처 및 상충 기록을 검사'),
    ("19.5.4",   "복수 경합 발화원 — 특정 못 해도 가설은 선다", DONE, "sourceUnspecified, C-46 한계 명시 요구"),
    ("19.6.3",   "가설 검증에서 답해야 할 질문 넷",           DONE, "C-28 TestingQuestionsShape"),
    ("19.6.4",   "확인이 아니라 반증을 시도한다",             DONE, "F-1, P3"),
    ("19.6.4.1", "과학 문헌을 검증 수단으로 쓴다",            DONE, "HypothesisTestMethod, C-47 인용 요구"),
    ("19.6.4.2", "물리·열역학 법칙에 어긋나면 반증된 것",      DONE, "C-31 CompetenceRequiredShape, F-3"),
    ('19.6.4.5', '시간선은 변별 수단이 된다', DONE, 'SupplyTimelineConflictShape·EventTimeRangeShape로 전원별 선후 모순·시간 범위 역전을 검증. 겹침·미확인은 보류'),
    ("19.6.4.6", "고장 수목으로 가설을 시험한다",             DONE, "TestByFaultTree"),
    ("19.6.5",   "negative corpus 는 과학적 방법이 아니다",   DONE, "C-2 ConclusionShape"),
    ("19.6.5.1", "모두 기각되거나 둘 이상 남으면 원인미상",    DONE, "D-7, D-8 UndeterminedByTieRuleShape(최고점 동점), D-16 지지 없는 가설뿐이면 원인미상. D-14 는 그 안에서 단락흔+통전이면 국내 분류 미확인 단락"),
    ("19.6.5.2", "발화원과 착화물을 짚은 것은 원인이 아니다",   DONE, "C-30 CauseNotJustSourceShape"),
    ("19.8.1",   "통계 목적 사건 분류 — 외부 체계 참조",      DONE, "C-10 ClassificationSystemShape, ClassificationSystem 6종"),
    ("19.8.2",   "보고서용 원인 분류 — 판정 이후에 온다",     DONE, "C-9 순서, C-11 분리. 채택 체계는 국내 보고규정 세부분류(KoreaFireReportClassification) 하나 — 전기 가설 여덟이 항목에 대응하고 D-20 이 결론 뒤에 분류 개체를 만든다(sh:order 7). 미확인 단락은 D-14 세션 표지. NFPA 921 자체에는 범주 목록이 없다(T20)"),
]

# 방법론 층에만 붙인다. 단서 규칙(Table 2)은 국내 실무 출처이므로 제외.
SHAPE_REFS = {
    "FalsificationRuleShape":            ["4.3", "19.6"],
    "HypothesisFormationRuleShape":      ["19.4"],
    "NoSupportedHypothesisRuleShape":    ["19.6", "19.7"],
    "UnidentifiedShortCircuitDerivationRuleShape": ["19.6", "19.8"],
    "ArcMarkSequenceRuleShape":          ["9.11"],
    "IgnitionCompetenceRuleShape":       ["9.9", "19.6"],
    "SupportScoreRuleShape":             ["19.6"],
    "RefutationEvidenceShape":           ["19.6"],
    "ConclusionShape":                   ["19.7"],
    "ScenarioShape":                     ["19.5"],
    "FactShape":                         ["19.3"],
    "MorphologyDiscriminationRuleShape": ["9.10", "19.4"],
    "MorphologicalAmbiguityRuleShape":   ["9.10", "19.4"],
    "MorphologyOnlyConclusionShape":     ["9.10", "19.7"],
    "DerivedManifestationRuleShape":     ["9.9", "19.4"],
    "OverloadDerivationRuleShape":       ["9.6"],
    "StrandFractureDerivationRuleShape": ["9.11"],
    "CuprousOxideDerivationRuleShape":   ["9.10"],
    "TrackingSiteDerivationRuleShape":   ["9.11"],
    # 아래 다섯은 TTL 안에 하위 절까지 직접 부착돼 있다 (§9.13.x).
    "ArcSiteAbsenceRuleShape":           ["9.13"],
    "ObscuredArcSiteShape":              ["9.13"],
    "ArcSurveyScopeShape":               ["9.13"],
    "ArcMeltAloneShape":                 ["9.13"],
    "CorrespondingDamageRuleShape":      ["9.13"],
    "FurthestDownstreamRuleShape":       ["9.13"],
    "CauseClassificationOrderShape":     ["19.8"],
    "ClassificationSystemShape":         ["19.8"],
    "ConclusionNotClassifiedShape":      ["19.8"],
    "ReportClassificationDerivationRuleShape": ["19.8"],
    "ReportCategoryBelongsToSystemShape": ["19.8"],
    "EqualLikelihoodShape":              ["4.5"],
    "SuspectedNotOpinionShape":          ["4.5"],
    "CertaintyStatedShape":              ["4.5"],
    "LimitationDisclosureShape":         ["4.5"],
    "UniqueFinalHypothesisShape":        ["4.5"],
    "PeerReviewIndependenceShape":       ["4.6"],
    "AdministrativeReviewScopeShape":    ["4.6"],
    "TechnicalReviewAccessShape":        ["4.6"],
    "ReviewValidationShape":             ["4.6"],
    "SustainedFaultingRuleShape":        ["9.3"],
    "OpenNeutralInferenceShape":         ["9.5"],
    "ProtectedSustainedFaultShape":      ["9.6"],
    "UntestableHypothesisShape":         ["4.3"],
    "AllHypothesesTestedShape":          ["4.3"],
    "UndeterminedOutcomeShape":          ["4.3"],
    "DataAnalyzedShape":                 ["4.3"],
    "NoPresumptionShape":                ["4.3"],
    "UndeterminedDerivationRuleShape":   ["4.3"],
    "TestingQuestionsShape":             ["19.6"],
    "HeatProducingDeviceListedShape":    ["19.5"],
    "CauseNotJustSourceShape":           ["19.6"],
    "CompetenceRequiredShape":           ["19.6"],
    "UndeterminedByTieRuleShape":        ["19.6"],
    "HeatTransferPathShape":             ["9.9"],
    "EnergizedRequiredShape":            ["9.9"],
    "ArcInitiationShape":                ["9.9"],
    "OverloadIgnitionRarityShape":       ["9.9"],
    "FuelProximityShape":                ["9.9"],
    "ArcFuelCompetenceShape":            ["9.9"],
    "MisconceptionShape":                ["9.11"],
    "OverloadMeltingNotProofShape":      ["9.10"],
    "BusBarArcTravelShape":              ["9.10"],
    "CrackedInsulationLeakageShape":     ["9.11"],
    "MetallographyAloneShape":           ["9.11"],
    "ArcOriginIndicationRuleShape":      ["9.12"],
    "PartialDisconnectionDerivationRuleShape": ["9.11"],
    "ProtectiveDeviceOperationRuleShape": ["9.6", "9.9"],
    "GroundFaultProtectionRuleShape":    ["9.6"],
    "MeltBoundaryRuleShape":             ["9.10"],
    "AlloyConductorArcMarkShape":        ["9.10"],
    "PostFireDamageShape":               ["9.10"],
    "LusterAbsenceShape":                ["9.10"],
    "ArcMarkAwayFromOriginShape":        ["9.10"],
    "QueryDerivationRuleShape":          ["19.6"],
    "InsulationResistanceDerivationRuleShape": ["9.11"],
    "ShortCircuitIgnitionShape":         ["9.11"],
    "SupplyPathCoverageShape":           ["9.12"],
    "IgnitionSequenceShape":             ["19.4"],
    "UnrecoveredSourceShape":            ["19.4"],
    "UnspecifiedSourceDisclosureShape":  ["19.5"],
    "EvidentialAmbiguityRuleShape":      ["4.3"],
    "LiteratureCitationShape":           ["19.6"],
    "TechnicalReviewBiasShape":          ["4.6"],
}


from collections import Counter


def counts():
    return Counter(s[2] for s in SECTIONS)


def gaps():
    return [s for s in SECTIONS if s[2] in (NONE, PART)]


if __name__ == "__main__":
    c = counts()
    tot = len(SECTIONS) - c[OUT]
    print(f"NFPA 921 (2024) 절 {len(SECTIONS)}개 — 범위 내 {tot}개\n")
    print(f"  구현 {c[DONE]}   일부 {c[PART]}   없음 {c[NONE]}   범위밖 {c[OUT]}")
    print(f"  이식률 {c[DONE]}/{tot} = {c[DONE]/tot*100:.0f}%\n")
    print("── 2026-09-03 제공 이미지 원문 대조 (구현 상태와 별개) ──")
    for sec, files, covered, missing in SOURCE_REVIEW:
        print(f"  §{sec}: {covered} — {files}")
        if missing != "없음":
            print(f"    추가 원문: {missing}")
    print("  상세: docs/NFPA_추가자료_대조.md\n")
    ch = None
    for sec, title, st, note in SECTIONS:
        h = sec.split(".")[0]
        if h != ch:
            ch = h
            print(f"\n── Chapter {h} " + "─" * 52)
        mark = {DONE: "■", PART: "◐", NONE: "□", OUT: "·"}[st]
        print(f"  {mark} {sec:5s} {title[:38]:38s} {st}")
        if st in (NONE, PART):
            print(f"          {note}")
    par = lambda x: ".".join(x.split(".")[:2])
    print("\n\n── 하위 절까지 내려간 절 " + "─" * 44)
    for p_ in sorted({par(x[0]) for x in SUBSECTIONS}, key=lambda v: [int(t) for t in v.split(".")]):
        rows = [x for x in SUBSECTIONS if par(x[0]) == p_]
        k = Counter(x[2] for x in rows)
        n = len(rows) - k[PROC] - k[OUT]
        rate = f"{k[DONE]}/{n} = {k[DONE]/n*100:.0f}%" if n else "대상 없음"
        print(f"\n  §{p_}  온톨로지 대상 {n}개 / 현장 절차 {k[PROC]}개 / 범위밖 {k[OUT]}개"
              f" — 이식률 {rate}")
        for sec, title, st, note in rows:
            mark = {DONE: "■", PART: "◐", NONE: "□", PROC: "·", OUT: "×"}[st]
            print(f"    {mark} {sec:9s} {title[:30]:30s} {st:5s} {note}")
