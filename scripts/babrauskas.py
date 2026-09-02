# -*- coding: utf-8 -*-
"""Babrauskas, Ignition Handbook (2003) 전기 절 대조표. 국제 문헌 층의 분모.

왜 필요한가
  국내 교재는 요인별 서술이라 '어떤 흔적을 누가 내는가, 화재 자체도 내는가'의 행렬을
  주지 않는다. 그 빈 칸을 작성자가 채웠고 여섯 번을 잘못 채웠다(audit.py). Babrauskas 는
  그 행렬을 물리와 실험으로 쓴다. 그래서 이 표에는 nfpa·silmu 에 없는 열이 하나 있다 —
  **국내 교재(실무Ⅳ)와의 관계.** 일치하면 온톨로지의 근거가 둘이 되고, 상충하면 그
  사실을 드러내고 덮어쓰지 않는다(dcterms:references 로 둘 다 적는다).

절 목록은 PDF 표제 글꼴(11pt bold = A–Z 항목, Ch.11 은 절 제목)로 뽑았다.
인쇄 쪽수 = PDF 쪽 − 10. 전기는 두 곳 — Ch.11 'Electric phenomena'(p.534~553) 와
Ch.14 A–Z 의 Electric 항목군(p.737~806) + GFCI·히터(p.853~858).

상태
  DONE  온톨로지에 물화돼 판정에 쓰인다
  PART  어휘는 있으나 판정에 쓰이지 않거나 절의 일부만
  NONE  없다 — 원문이 판정 기준을 주는데 자리가 없다
  OUT   범위 밖 — 배경 물리·고압·통계·항공·차량·금속 연소
  PROC  현장 절차·시험 규격

관계 (국내 실무Ⅳ와)
  AGREE     같은 말을 한다 — 근거가 둘이 된다
  CONFLICT  다른 말을 한다 — 둘 다 적고 어느 쪽을 택했는지 밝힌다
  ADDS      실무Ⅳ에 없는 조건·수치를 준다
  NA        비교할 국내 서술이 없다

읽는 법
  CONFLICT 가 이 표의 값어치다. 특히 p.795~804 'Cause or victim?' — 국내 실무의
  1차/2차 용흔 형태 판별(p.308~310)이 통계적으로 서지 않는다는 결론. 그리고 p.762 —
  접점 융착을 화재 열도 만든다. 둘 다 온톨로지가 이미 그쪽으로 기울어 있었거나(전자)
  틀려 있었다(후자). CANDIDATES 에 모았다. 붙이기 전에 두 질문을 거친다.
"""
from collections import Counter

DONE, PART, NONE, OUT, PROC = "구현", "일부", "없음", "범위밖", "현장절차"
AGREE, CONFLICT, ADDS, NA = "일치", "상충", "보강", "—"

CH = {"11": "Ch.11 Characteristics of external ignition sources — Electric phenomena",
      "14": "Ch.14 The A–Z — Electric 항목군"}

# (절, 쪽, 제목, 상태, 관계, 근거)
SECTIONS = [
    # ── Ch.11 ────────────────────────────────────────────────────────────────
    ("11.1", 534, "Electric discharges — 파셴 법칙·절연파괴", OUT, NA,
     "방전 물리. 최소 340 V(7 μm 간극). 120 V 에서 직접 방전 불가 → 저압 아크는 접촉·탄화로만 시작한다는 뒤 절의 전제"),
    ("11.2", 537, "The electric spark", OUT, NA, "스파크 커널 성장. 가스 착화 이론"),
    ("11.3", 540, "The electric arc — 네 가지 생성 경로", PART, AGREE,
     "(1)고전압 파괴 (2)접점 분리 (3)탄화 경로 (4)글로→아크. ArcHeating·ShortCircuitArc·ArcTracking 이 그 셋. "
     "p.548 '진동으로 산화 다리 → 글로잉 접속' 은 Vibration → PoorContactHeating (실무Ⅳ p.194 와 일치)"),
    ("11.4", 548, "Electric current — 저전류 고장 넷", DONE, AGREE,
     "가스 아크·탄화 경로 아크·글로잉/과열·고온 입자 비산 = ArcHeating·ArcTracking·ResistiveHeating·Spatter. "
     "'저전류 회로에서는 증거가 더 심하게 손상된다'"),
    ("11.5", 549, "Overheating wires — 과전류 발화는 3~7배 필요", PART, ADDS,
     "OverloadHeating 확장 슬롯·OverloadIgnitionRarityShape(C-34). 정격의 3~7배라는 수치는 참조 지식(§9.9.2.4 와 같은 판정)"),
    ("11.6", 549, "Overheating electrical connections — 글로잉 접속부·아산화동 증식", DONE, AGREE,
     "GlowingConnection·CuprousOxideGrowth·RubyRedCrystal. 실무Ⅳ p.151~154 와 같은 현상(교류 양극·직류 +극 발열, 저항 부(負)온도계수). 하위 절 참조"),
    ("11.7", 553, "Ejection of hot particles", DONE, AGREE,
     "Spatter. audit 판정 '화재도 낸다'와 정합 — 단락·아크는 화재 중에도 입자를 던진다. 용융 알루미늄 방울이 더 위험하다는 것은 어휘 없음"),
    ("11.8", 553, "Dendrites — 직류 전용", OUT, AGREE,
     "Elliot 1965. 직류·수분·이온 → 덴드라이트. 실무Ⅳ p.154 은 이동과 같은 현상이고 같은 이유로 범위 밖(domestic.py)"),
    ("11.9", 553, "Adventitious batteries · Static electricity · Lightning", OUT, NA, "§9.14·§9.15·표 2-1 뇌 와 같은 판정"),
    # ── Ch.14 ────────────────────────────────────────────────────────────────
    ("14.1", 737, "Electric (general statistics)", OUT, NA,
     "통계. 노르웨이 '전기화재 1/3~1/2 이 접촉 불량' — 5요인 균등 표집인 사례 150건과 다른 분포임을 기억할 것"),
    ("14.2", 740, "Electric appliances and electronic equipment", PART, AGREE,
     "외함 난연 규격은 범위 밖. push-on 단자 이완(CPSC) → LooseConnection. 고온 제한 스위치 고장·접점 융착 계속 통전은 고장 갈래(domestic OUT)"),
    ("14.3", 742, "Electric batteries", OUT, NA, "§9.15 와 같은 판정"),
    ("14.4", 743, "Electric blankets and mattress pads", PART, AGREE,
     "접힘·덮음 열 축적 → CoveredHeatingDevice. 코드/접속부 31%·서모스탯 27%. PTC 도체 단선 → 아크"),
    ("14.5", 744, "Electric circuit interruption devices", DONE, AGREE,
     "차단기 미동작 원인 다섯(결함·정비·설정·정격 초과·전류 부족) → ProtectiveDeviceFailedToOperate. "
     "Franklin: 120 V 아크는 200~250 A 인데 대부분의 차단기가 그 전에 못 끊는다 — 실무Ⅳ p.285 및 옛 '트립 없음' 반증 삭제 결정과 일치. 하위 절 참조"),
    ("14.6", 746, "Electric fences", OUT, NA, ""),
    ("14.7", 746, "Electric lamps and lighting fixtures", PART, AGREE,
     "조명은 대부분 사용방법(가연물 접촉). 필라멘트 파단 판별(p.749 Allsop)은 실무Ⅳ p.214 와 같은 통전 입증 단서 — silmu 후보 ⑦(서식). "
     "안정기 층간단락 → InterTurnShortCircuit. 하위 절 참조"),
    ("14.8", 755, "Electric motors", PART, CONFLICT,
     "저전압 실속·단상 운전(3상)은 범위 밖. '밀폐형 컴프레서 모터의 내부 고장이 외부를 착화시킬 가능성은 극히 낮다'(p.755) — "
     "실무Ⅳ p.255·284 컴프레서 층간단락 출화 사례와 긴장. WindingSite 는 유지하되 주석에 적을 것"),
    ("14.9", 755, "Electric outlets, plugs and connections", DONE, AGREE,
     "가장 직접 닿는 절. 플러그 고장 4자리(p.756 Hagimoto) = 몸체 아크(트래킹)·소선 용단(반단선)·병렬 아크·볼트 단락. "
     "실무Ⅳ p.149·185·253 과 같은 자리. 하위 절 참조 — CONFLICT 둘(p.758 열적 트래킹, p.762 화재 융착)"),
    ("14.10", 766, "Electric switches", OUT, NA, "개폐 스파크의 가스 착화"),
    ("14.11", 766, "Electric transmission and distribution systems · Transformers", OUT, NA,
     "고압·변압기. 실무Ⅳ 3.3.10 과 같은 판정"),
    ("14.12", 773, "Electric wires and cables", DONE, AGREE,
     "발화 모드 셋(아크·저항 발열·외부 가열), 직렬/병렬 아크, 아크 원인 넷, 탄화 경로, 단락, 과부하, 방열 저해, 지락, 중성선 단선, "
     "기계적 손상, 쥐, 마지막 소선, 스테이플, 이음, 노후. 하위 절 참조 — CONFLICT 하나(p.778 최하류 가정)"),
    ("14.13", 793, "Appliance cords and extension cords", DONE, AGREE,
     "1500 W 이상 기기 화재의 74% 가 플러그 쪽. 고장 위치(코드 46·기기 접속 32·플러그 접속 10) → PlugJunctionArea·ApplianceEntryPoint. "
     "릴·카펫 밑 방열 저해 → CoveredByFloorCovering (실무Ⅳ p.245·253)"),
    ("14.14", 794, "Wires in steel conduits", DONE, AGREE,
     "전선관 내 아크 손상은 대개 외부 화재가 원인 — 탄화 → 저전류 아크 → 차단기 미동작. ArcMeltAloneShape(C-8)·CarbonizedConductivePath 화재 생성 판정과 정합"),
    ("14.15", 795, "Electric wiring: Cause or victim?", DONE, CONFLICT,
     "아크 비드 vs 화재 용융(경계 선명 vs 늘어짐)은 실무Ⅳ p.305·308 과 일치. 그러나 **'cause' 비드와 'victim' 비드는 광택·색·형상·평활도·크기로 가를 수 없고**, "
     "공극·수지상·산소 프로파일 등 제안된 방법 전부가 통계적으로 서지 않는다(65건 실화재에서 39% 일치). 실무Ⅳ p.308~310 의 경향 서술과 상충. "
     "온톨로지는 이미 F-2(시간 선후)·MetallographyAloneShape 로 Babrauskas 쪽에 서 있다. 하위 절 참조"),
    ("14.16", 804, "Electric wiring in motor vehicles · aircraft", OUT, NA, "12 V 차량·항공 Kapton 아크 트래킹"),
    ("14.17", 806, "Electronic components", OUT, AGREE, "기판 과전압 시험. domestic '반도체 전기적 파괴' OUT 과 같은 판정"),
    ("14.18", 853, "Ground fault circuit interrupters", DONE, AGREE,
     "물 튀김 부식 → GFCI 내부 과열, 트립 없이 연소. GroundFaultProtectiveDevice 가 DeviceInteriorSite 로 출화원이 되는 경우. 실무Ⅳ p.201 과 일치"),
    ("14.19", 854, "Heat tapes and heat cables", PART, ADDS,
     "동파방지 열선. 고장 모드 둘 — 번아웃(PVC 노후·과단열, 화재 드묾) / 열분해(아크가 전원 쪽으로 도약, 화재 다수). 자기제어형은 습기 침입 → 아크 트래킹 'wet fire'(40 밀리암페어로 지속). "
     "사례 150건의 열선 2건(절연열화 라벨)이 이 절이다. 열선 어휘 없음"),
    ("14.20", 856, "Heaters, electric", PART, AGREE,
     "고온 제한 스위치 고장·먼지 막힘·가연물 근접 → 사용방법·고장 갈래. 니크롬선 산화 처짐·파단 → 접지 접촉 → 아크 비산(p.858). 실무Ⅳ p.293 니크롬 용융 판별의 근거는 아님"),
    ("14.21", 870, "Metals — Aluminum · Copper", OUT, NA,
     "금속 연소(벌크 알루미늄 1750℃, 구리 1050℃ 산소 중). 용흔 판정과 무관. 합금은 p.793 'Alloying' 에서"),
]

# 하위 절. (절, 항, 제목, 상태, 관계, 근거)
SUBSECTIONS = [
    # 11.6 Overheating connections
    ("11.6", "a", "Aronstein — 접촉저항 10 mΩ 이 고장의 시작, 접촉력에 따라 급변, 비선형·이력", PART, ADDS,
     "계측값. 잔해에서 못 잰다. 참조 지식"),
    ("11.6", "b", "글로잉 온도 1100~1500℃, 10 mm 떨어진 곳 200~350℃", DONE, AGREE,
     "GlowingConnection. 실무Ⅳ p.152 아산화동 용융점 1232℃ 와 정합"),
    ("11.6", "c", "산화막 저항 — 구리 산화물은 반도체, 알루미늄 산화물은 부도체", PART, ADDS,
     "AlloyConductor 주석에 없는 물리. 알루미늄 접속은 글로잉이 아니라 금속간화합물 경로"),
    ("11.6", "d", "CEE 1961 — 글로잉 시작에 4~6 A 필요, 20 A 에서 35~50 W, 크기 무관 재료 의존", PART, ADDS,
     "발화 조건(전류·전력). 잔해에서 관측 불가. 가설 시험 시 참조"),
    ("11.6", "e", "Kawase — 청색 스파크 → 적색 → 아산화동 증식, 지렁이처럼 굽이치는 밝은 필라멘트", DONE, AGREE,
     "CuprousOxideGrowth. 실무Ⅳ p.151~152 '띠형·빨간 불' 서술의 원전. 발화 전 목격 진술(PreFireArcObservation)의 물리"),
    ("11.6", "f", "Hagimoto — 교류는 양단 백열, 직류는 +극만. 1 mm 선 16 W·2 mm 선 28 W 일정. 증식 6~18 mm/h. 연선은 끊어져 지속 못 함", DONE, AGREE,
     "실무Ⅳ p.153 '교류 양·음극측, 직류 양극측' 그대로. '연선은 발열점에서 끊어진다'는 접촉불량→반단선 이행의 근거 — ReducedContactArea 주석에 적을 것"),
    ("11.6", "g", "Suzuki — 2 V 이상 강하면 안정 글로잉. 구리-구리·구리-황동은 글로잉 안 됨(재현 실패)", PART, CONFLICT,
     "다른 연구와 반대. Babrauskas 자신이 '재현이 쉽지 않다'고 적는다. 판정 근거로 쓰지 않는다"),
    ("11.6", "h", "Aronstein — 50 W 접속부가 25분 뒤 목재 착화, 45~50 W 가 알루미늄 용융, 30 W 가 열경화 커버 착화", PART, ADDS,
     "IgnitionCompetenceRuleShape(F-3) 의 참조 수치. 값은 규칙에 박지 않는다(CLAUDE.md)"),
    ("11.6", "i", "Ettling — 못이 도체를 관통·절단하면 못과 두 단면 사이에 글로잉 접속", DONE, AGREE,
     "MisdrivenStaple → PoorContactHeating (R_PC_sup7). 실무Ⅳ p.185 스테이플과 §9.11.4.3 과 일치"),
    ("11.6", "j", "1 A 퓨즈가 안 끊어진 채 컴퓨터 글로잉 접속부에서 화재", DONE, AGREE,
     "직렬 고저항 발열은 보호장치를 안 건드린다. 옛 '트립 없음' 압착 반증 삭제·실무Ⅳ p.286 꼬아 접속 미트립과 같은 사실"),
    # 14.5 Circuit interruption
    ("14.5", "a", "퓨즈는 fail-safe, 차단기는 fail-unsafe. 반복 과부하로 약해진 퓨즈는 정격 이하에서 끊어진다", PART, ADDS,
     "FuseMeltPattern 4형(실무Ⅳ p.203)의 형태 기준은 여기 없다. 퓨즈 법의학은 Twibell & Christie 로 미룬다(자료_목록 후보)"),
    ("14.5", "b", "열동식 단독 구형 차단기는 대과부하에 접점이 융착돼 안 열린다", DONE, AGREE,
     "ContactWelding 이 차단기에도. 실무Ⅳ p.203 은 커버나이프 퓨즈만"),
    ("14.5", "c", "Franklin — 120 V 단락 아크 200~250 A, 대부분 브랜드가 순시 트립 전 착화 가능(표 55)", DONE, AGREE,
     "'외력 흔적 + 트립 없음'을 압착 반증으로 두었던 옛 규칙을 지운 근거가 셋이 됐다(실무Ⅳ p.285·286, Babrauskas p.745·774·778)"),
    ("14.5", "d", "저온 환경에서 차단기 동작 전류 상승 — −27℃ 에서 3.1배도 미트립", PART, ADDS, "옥외 분전반. 어휘 없음"),
    # 14.7 Lamps
    ("14.7", "a", "Allsop — 필라멘트 냉간 파단(날카롭고 산화 없음) / 점등 중 파단(밝은 용융 비드) / 유리 파손 후 연소(황색 산화텅스텐 침착)", NONE, AGREE,
     "실무Ⅳ p.214 '점등 중 파손이면 앵커 용착'과 같은 통전 입증 단서, 더 정밀. silmu 후보 ⑦ — 서식 우선"),
    ("14.7", "b", "형광등 안정기 — 권선 단락(shorted turn) 과열이 정상 고장 모드. 화재가 열 차단기를 손상시키므로 안정기를 열어 내부 과열 패턴을 봐야 원인/피해를 가른다", DONE, AGREE,
     "InterTurnShortCircuit(실무Ⅳ p.219~220). '내부를 열어 본다'는 InternalDamageExceedingSurface 와 같은 논리"),
    ("14.7", "c", "램프홀더 스프링 이완 → 접촉 없이 아크로 통전 → 글로잉 → 요소수지 갈변·흑변 → 훈소", DONE, AGREE,
     "IntermittentContactSeparation·GlowingConnection. 실무Ⅳ p.221 소켓 접촉불량"),
    ("14.7", "d", "페놀 램프홀더의 습기 아크 트래킹 — 저항은 정상이었는데 재통전 시 파열음", DONE, AGREE,
     "TrackingScenario·DeviceInteriorSite·MoistureExposure. **'절연저항 정상'이 트래킹을 반증하지 못한 사례** — R_TR_ref(NormalInsulationResistance −30)의 반례. CANDIDATES ⑥"),
    # 14.9 Outlets/plugs/connections
    ("14.9", "a", "일본 조사 28,112개 — 손상 27개: 칼날 주위 탄화 17, 칼날 변색 17, 칼날 굽음 11, 아크 흔적 8, **칼날 사이 탄화 5**, 녹청 6", DONE, AGREE,
     "'칼날 변색'=접촉불량 발열, '칼날 사이 탄화'=트래킹. 실무Ⅳ p.185 극별 용융 기준의 통계적 배경. silmu 후보 ①(서식)"),
    ("14.9", "b", "NIST — 기계 접속을 지키는 건 스프링 힘뿐. 열순환 → 미세 움직임 → 산화물 축적 → 저항 증가", DONE, AGREE,
     "InsufficientContactPressure·ContaminatedContactSurface(실무Ⅳ p.194)의 물리"),
    ("14.9", "c", "Hagimoto — 플러그 고장 4자리: 몸체 표면 아크(트래킹)·소선 용단(손상·산화)·병렬 아크·볼트 단락", DONE, AGREE,
     "WiringDeviceSite 가 다섯 요인 공유 자리라는 cause_audit 판정의 원전. 실무Ⅳ p.147·149·253 과 일치"),
    ("14.9", "d", "Blades — 1500 W 부하 활선 삽입·발거 10분 후 플러그/콘센트 계면 아크 지속, 절연물 탄화", DONE, AGREE, "IntermittentContactSeparation → 탄화 → 트래킹 이행"),
    ("14.9", "e", "코드 당김 → 소선 파단 → 과열. Shimizu ±70° 2000회, Katayama ±60°·0.5 kg — 접속부(R점) 소선 전부 파단 후 굽힘 30회/분으로 착화", DONE, AGREE,
     "PlugJunctionArea·RepeatedFlexing → PartialDisconnectionHeating. 실무Ⅳ p.149 '플러그 접속부 부근'의 실험 원전"),
    ("14.9", "f", "나사 한 바퀴 풀림 + 10 A → 1시간 내 200℃, 최대 400℃(Hagimoto). 무부하면 저항 증가 없음(Uchida)", DONE, AGREE,
     "LooseConnection. '무부하면 안 보인다'는 통전 필요조건(C-57)의 물리"),
    ("14.9", "g", "칼날 파지력 0.1~0.2 N 이면 20 A 에서 200℃, 15 A 면 무발열. 규격 10 N", DONE, ADDS,
     "InsufficientContactPressure. 파지력·전류 문턱은 참조 지식"),
    ("14.9", "h", "**Ashizawa — PVC 열적 열화 → 염화칼슘 생성(흡습) → 습기 흡수 → 섬광 → 탄화 경로 → 아크 → 착화. 절연저항 1 kΩ 까지 내려간 것만 착화**", DONE, CONFLICT,
     "과열 접속부의 열적 열화가 **오염 환경 없이** 트래킹을 만든다(수분은 열화 PVC 가 대기에서 흡수). 온톨로지는 트래킹의 필요조건을 ContaminatedEnvironment 로 둔다(C-5). "
     "실무Ⅳ p.196 '절연열화의 발화형태는 트래킹'은 이쪽 편이고, 3.1.5바 서모스탯도 같은 경로. CANDIDATES ③. 절연저항 1 kΩ/10 kΩ 문턱은 silmu 후보 ③의 값"),
    ("14.9", "i", "Okamoto — 베이클라이트는 PVC·요소수지보다 트래킹 취약. 열노화 1시간에 CTI 600 → 116(요소)·459(PVC), 5시간에 둘 다 ~113", DONE, AGREE,
     "LowTrackingResistanceInsulation(IEC 60112 CTI). 실무Ⅳ p.206 '페놀수지 가동편'. ADDS: 열노화가 CTI 를 무너뜨린다 — 재질 등급이 새것 기준이면 틀린다"),
    ("14.9", "j", "콘센트 — 나사 단자 불량이 최다. Meese — 0.3 A 에서도 가시 글로, 129시간 지속, 20 A 에서 20~40 W. **강철 나사가 황동보다 훨씬 취약(자석으로 식별)**", DONE, ADDS,
     "LooseConnection·GlowingConnection. '나사 재질(강철/황동, 자석 판별)'은 관측 가능한 새 선행 조건 — 어휘 없음. CANDIDATES ⑤"),
    ("14.9", "k", "NIST — 14 AWG 구리 나사 최소 토크 0.7 N·m. Hicks — 수명 ∝ 토크³, 권장 1.0~1.6 N·m", DONE, AGREE,
     "dataset 의 slot_fastening_torque 가 이 값의 자리. 온톨로지엔 토크 속성이 없다 — 어휘로는 InsufficientContactPressure. CANDIDATES ⑤"),
    ("14.9", "l", "back-wired(꽂음식) 콘센트 — 9년 뒤 저항 4배, 98~111℃ vs 나사식 27~28℃. 15%/년 고장", DONE, ADDS, "접속 방식이 선행 조건이라는 근거 — silmu 서식 항목 D(접속 방식)의 국제 근거"),
    ("14.9", "m", "아무것도 안 꽂힌 콘센트도 출화원이 된다 — 데이지체인 하류 부하 전류가 통과", DONE, AGREE,
     "실무Ⅳ p.188 ⑧ '기판 접속부'와 같은 자리. '플러그 없음'은 접촉불량 반증이 아니다 — 적을 것"),
    ("14.9", "n", "**Béland — 통전 없이 목재 화재에 노출만 해도 접점이 융착된다. 바이메탈 서모스탯·차단기 접점도. 외부 화재 융착은 부품의 심한 소손으로 가른다**", DONE, CONFLICT,
     "audit.py 가 ContactWelding 을 ELEC(화재 못 냄)으로 판정했고 R_PC_sup8(+10)이 그 위에 선다. 원문은 화재도 낸다고 한다 — 일곱 번째 형태 편향. "
     "가르는 기준은 IntactSurroundingsAroundComponent 의 역(부품 소손 정도). CANDIDATES ①"),
    ("14.9", "o", "트위스트 커넥터 불량 — 금속 손실이 커넥터가 아니라 '몇 인치 떨어진 곳'에서. 과열 → PVC 염화수소 → 구리 부식", DONE, ADDS,
     "CorrodedConnection 의 한 경로. **용흔·금속 손실 위치가 접속부에서 떨어져 있어도 접속부 원인일 수 있다** — 대상 슬롯 판독 시 주의"),
    ("14.9", "p", "진동(스파 버블러)으로 인접 벽 콘센트 접속 고장. 아연 15% 이상 황동은 탈아연 부식으로 접촉력 상실", DONE, AGREE, "Vibration → PoorContactHeating(R_PC_sup3). 실무Ⅳ p.194"),
    ("14.9", "q", "일본 사례 — XRD 로 붉은 유리질 물질이 아산화동, 부(負)온도계수 확인", DONE, AGREE, "RubyRedCrystal(실무Ⅳ p.153) + p.154 저항 판별의 원전"),
    ("14.9", "r", "알루미늄 배선 문제 (1964~72 미국)", PART, NA, "국내 저압 분기회로엔 드묾. AlloyConductor 로 어휘만. 강철 나사+알루미늄 조합 최악"),
    # 14.12 Wires and cables
    ("14.12", "a", "직렬 아크는 부하 없이 존재 못 하고 보호장치를 거의 안 건드린다. 분기회로 병렬 아크도 대개 못 끊는다(간헐·배선 저항·응답)", DONE, AGREE,
     "SeriesArc. 실무Ⅳ p.285·286 과 함께 옛 '트립 없음' 반증 삭제 근거. **BreakerTripRecord(트립 있음/없음)는 어느 가설의 표지도 아니다** — 화재도 83% 트립시킨다(p.786)"),
    ("14.12", "b", "아크 원인 넷 — 탄화(트래킹)·외부 이온화(화염·선행 아크)·금속 접촉 단락·접속 불량", DONE, AGREE, "네 메커니즘 클래스 모두 있음"),
    ("14.12", "c", "탄화 경로 생성 4경로(UL) — 반복 과전압·고압 트래킹·오염+습기·**열분해(고저항 직렬 고장, 개폐 아크, 기존 화재)**", DONE, CONFLICT,
     "NFPA 921(2001) '탄화 통과 아크는 항상 화재 결과'는 틀렸다고 명시. 우리 audit 는 CarbonizedConductivePath 를 '화재도 낸다'로 두어 정합. "
     "그러나 오염 없는 열분해 경로는 C-5 와 긴장 — CANDIDATES ③"),
    ("14.12", "d", "탄화 PVC 는 반도체 — 600℃ 에서 3 Ω, 180℃ 1000시간에 5×10⁵ Ω, 250℃ 10시간에 10⁵ Ω. 300℃ 부터 급락", DONE, ADDS,
     "silmu 후보 ③(탄화부 저항 측정)의 값 근거. 실무Ⅳ p.251 '수Ω~수십Ω'과 정합"),
    ("14.12", "e", "Nagata — 200~300℃ 예열된 PVC 는 상온~40℃ 에서 100 V 로 착화(열폭주)", DONE, ADDS, "ThermalDegradation → 절연파괴. '이전에 과열된 적 있는 배선'이 선행 조건"),
    ("14.12", "f", "Hagimoto — 병렬 아크는 반복적: 탄화층 소전류 → 국부 아크 → 용융 비산 → 전류 하락 → 반복. 아크 빈도 ∝ 1/피크 전류", DONE, AGREE,
     "MultipleArcBeads 의 물리. 한 자리에서도 여러 번 비산한다"),
    ("14.12", "g", "화염이 공기 절연강도를 3 MV/m → 0.1~0.2 MV/m 로 떨어뜨린다. **'화재에서 아크가 발견되는 압도적으로 흔한 상황은 진행 중인 화재가 아크를 만든 것'**", DONE, AGREE,
     "F-2·C-8·audit 의 대전제. SecondaryArcMark 가 기본이고 PrimaryArcMark 가 예외"),
    ("14.12", "h", "**Bernstein — 강한 화재에 노출된 회로는 전 구간에서 거의 동시에 아크가 생긴다. '가장 먼 곳이 최초'는 성립 안 함**", DONE, CONFLICT,
     "FurthestDownstreamRuleShape(D-5)·실무Ⅳ p.185 ⑦㉯·p.305 '부하측이 1차'와 상충. 조건부 규칙이다 — 강한 화재 노출이 아닐 때만. CANDIDATES ④"),
    ("14.12", "i", "Short circuits — 볼트 단락은 발열이 회로 전체에 분산, 아크 단락은 국부. **15~20 A 분기회로에서 단락으로 불 내기는 극히 어렵다**(트립 또는 금속 소실). 불쏘시개만 착화", DONE, AGREE,
     "ShortCircuitIgnitionShape(C-41, §9.11.5). Hagimoto: 열동전자식은 전부 트립·무착화, 열동식은 38/40 미트립·전부 착화. 아크 에너지 >100 J, I²t >1500 A²s"),
    ("14.12", "j", "일본 사례 — 볼트가 케이블 관통, 접지 불량으로 4.5 A 만 흘러 150 A 차단기 미동작, 0.4 m 화염", DONE, AGREE, "실무Ⅳ p.285 금속 개입 단락 미트립과 같은 사례. MisdrivenStaple 계열"),
    ("14.12", "k", "Gross overloads — 드묾. 3~7배 필요. 슬리빙(고무)은 과부하 표지, 열가소성은 구리가 연화 피복에서 '튀어나와' 단락", DONE, AGREE,
     "Sleeving·MeltOffset(§9.10.4.1). D-1 OverloadState. 정격 맞는 차단기면 과부하 발화 불가(C-34)"),
    ("14.12", "l", "Excessive thermal insulation — Béland 카펫 밑 코드 21.5 A 에서 밟으면 아크. Goodson 표 71: 인접 케이블 3~4가닥 + 우레탄폼이면 정격 100% 에서 294~417℃", DONE, AGREE,
     "ThermalInsulationEnclosure·BundledWiring·CoveredByFloorCovering. 실무Ⅳ p.245·253. **정격 이내에서도 발열 — 과부하 없이 절연열화 선행조건이 성립**"),
    ("14.12", "m", "Stray currents — Kinoshita: PVC 케이블이 아연도금 지붕에 닿으면 5 A 로 착화", DONE, AGREE, "LeakageCurrentHeating. 실무Ⅳ p.285 지락"),
    ("14.12", "n", "Overvoltage · floating neutral — 중성선 단선 시 120 V 부하에 0~240 V. 저전압에 발화하는 건 모터뿐", DONE, AGREE, "OpenNeutral·OpenNeutralOvervoltage(§9.5.2 확장 슬롯). 실무Ⅳ p.273 밥솥 사례"),
    ("14.12", "o", "Harmonic distortion — 3상 중성선 과부하", OUT, AGREE, "domestic '고조파' OUT 과 같은 판정"),
    ("14.12", "p", "External heating — PVC 215~250℃ 에서 도체 접촉 단락(5 kW/m² 면 충분). 화재 노출 코드 83% 가 차단기 트립, 절단부에 비드", DONE, AGREE,
     "SecondaryArcMark(R_EF_sup3). '트립 있음'도 화재가 만든다 — 14.12a 와 함께 BreakerTripRecord 의 한계"),
    ("14.12", "q", "Mechanical injury — 진동 덕트에 닿은 케이블 마모 → 화재", DONE, AGREE, "Vibration + AbrasionAtPenetration. 실무Ⅳ p.256·269"),
    ("14.12", "r", "**Rodents — '쥐가 갉음'은 부실 조사의 상징이었으나 실제로 일어난다. 몸과 배설물이 도전성. Hosaka 흐름도: 노출 도체 → (배설물 있음) 누설·아크 트래킹 / (없음) 볼트 단락·소선 파단 과열**", DONE, CONFLICT,
     "RodentGnawing 은 압착(단락)·반단선(오늘 추가)에 이어져 있다. 원문은 **배설물이 있으면 트래킹·누설**도 낸다 — 실무Ⅳ p.252 쥐 오줌 PTC 스파크와 같다. CANDIDATES ②"),
    ("14.12", "s", "Solid conductors — 망치·볼트 단락은 목재 못 태움(Béland). 못 절단 직렬 아크는 착화 가능하나 확률 낮음(Roberts/Béland 상반). 홈·니크만으론 과열 없음", DONE, AGREE,
     "MisconceptionShape(§9.11.2 니크·연신). ExternalCrushing 이 도체를 자르면 SeriesArc"),
    ("14.12", "t", "**Last-strand — 처음 10% 소선이 끊긴 뒤 파단이 급가속(Mitsuhashi). 착화는 10~20 A 창에서만: 벌크 구리 >100℃ 예열 + 마지막 소선 용단 >450℃ + 간극 ≥1 mm**", DONE, AGREE,
     "StrandFractureOverTenPercent(D-11, 실무Ⅳ p.149 '10% 넘으면 급격히 증가')의 실험 원전. ADDS: 전류 창·예열 조건은 참조 지식"),
    ("14.12", "u", "Creep — 눌린 케이블의 절연 냉간 유동 → 두께 감소 → 파괴 또는 소선 접촉 → 탄화 → 트래킹. 가구·문에 눌린 코드 화재는 '드물지 않다'. 실험은 없음", DONE, AGREE,
     "ExternalCrushing(표 2-1 바닥 깔림·접힘). 압착이 트래킹으로도 간다는 경로는 어휘상 CrushInducedArc 만 — 주석에 적을 것"),
    ("14.12", "v", "Overdriven staples — 4경로: 즉시 단락 / **절단+브리지 → 고저항 접속(접촉불량)** / 크리프 / 트래킹. 15시간~수년 지연", DONE, AGREE,
     "MisdrivenStaple 이 CD·PC·PD 공유(cause_audit SHARED)인 근거. 트래킹 경로는 없음 — CANDIDATES ②. 못에 녹아 붙은 구리 ≠ 아크(MetalTransferToFastener, §9.11.4.3)"),
    ("14.12", "w", "Poor splices — 손으로 꼬은 이음 20 A 에서 130~300℃", DONE, AGREE, "ConnectionJointSite. 실무Ⅳ p.286"),
    ("14.12", "x", "Aging — 산화·가수분해·열분해·가소제 손실 → 취화. 미국 전기화재 14%. **화재 사고와 노화를 실제로 연결한 현대 연구는 없다**", DONE, AGREE,
     "AgedInsulation·InsulationEmbrittlement·ThermalDegradation. Stricker: PVC 열선 71~77℃ 한 달에 가소제 손실. NIST 202℃ 65시간 → 취화·탈락·단락(실무Ⅳ p.305 절연열화 단락)"),
    ("14.12", "y", "Alloying — 용융 알루미늄이 구리에 닿으면 548℃ 합금으로 녹는다. 아크 손상과 혼동", DONE, AGREE, "AlloyConductor·AlloyDiscoloration(실무Ⅳ p.318)"),
    # 14.15 Cause or victim
    ("14.15", "a", "아크 비드 vs 화재 용융 — 구형과 도체의 경계가 선명 / 늘어짐(droopy). 불충분하면 현미경", DONE, AGREE,
     "hasSharpMeltBoundary·FireMeltMark·DrippingMeltFormation. 실무Ⅳ p.305·309 와 일치. NFPA 921 §9.11 도 같음"),
    ("14.15", "b", "결정 구조 — 300℃ 미만은 인발 줄무늬, 800℃ 이상 조대 결정. Takaki: 아크 비드는 3층(공극 표층·재결정 중간층·미변화 심층), 화재 용융은 균일 재결정", DONE, AGREE,
     "실무Ⅳ p.306~310 금속조직의 원전(Takaki). fineDendriticGrain 은 보강만"),
    ("14.15", "c", "**일본 연구 둘 — 'cause'/'victim' 은 광택·색·형상·평활도·크기로 가를 수 없다(1 mm 미만은 cause 경향, 3 mm 초과는 victim 경향뿐)**", DONE, CONFLICT,
     "실무Ⅳ p.308 '1차가 광택·평활·반구형이 많다'와 상충. 온톨로지: SmoothLustrousMeltSurface·HemisphericalMeltShape 는 어휘만, 규칙 없음, 주석에 '경향이지 기준 아님' — 이미 Babrauskas 쪽. 그대로 둔다"),
    ("14.15", "d", "공극 — Erlandsson(공기 아크만 공극) vs 도쿄소방청(과전류 용융도 공극). 크기·수·면적 모두 분포 겹침(Mitsuhashi·Oba·Miyoshi)", DONE, CONFLICT,
     "실무Ⅳ p.309~310 '1차 보이드 작고 전체 분포 / 2차 큰 보이드'의 원전이 바로 이 겹치는 연구들. voidFraction 주석('임계값 없음, 보강만')이 맞다. 주석에 이 절을 인용할 것"),
    ("14.15", "e", "수지상 결정 — 있고 없음은 산소 농도만 반영(cause 57%·victim 92% 가 무결정). 팔 간격은 주관적", DONE, CONFLICT,
     "실무Ⅳ p.305 '수지상조직 특징'. fineDendriticGrain 은 대부분의 비드에 적용 불가. 주석에 적을 것"),
    ("14.15", "f", "탄소·라만 — cause 비드의 27~60% 만 흑연 탄소. 산소 프로파일 AES/SIMS — 맥클리어리와 사토가 정반대 기준, 사토 65건 실화재 39% 일치. 앤더슨 방법 — 정량 기준 없음, 검증 실패", DONE, AGREE,
     "MetallographyAloneShape 의 국제 근거. 실무Ⅳ p.305·310 도 '단독 판정 불가'라 적는다 — 그 지점에서는 일치"),
    ("14.15", "g", "Levinson — 긴 구간이 균일 재결정이면 과전류(화재는 균일 가열 못 함). 단 원인 증명은 아님", DONE, AGREE, "UniformDamageAlongConductor(실무Ⅳ p.312)"),
    ("14.15", "h", "Reese — 주거 배선 화재는 대개 금속 접촉 단락이 아니라 탄화 통과 아크. Fitz — 복사열로 연화된 피복 접촉 단락은 연소 생성물 없이 생겨 '원인'으로 오판", DONE, AGREE,
     "1차/2차 판별의 논리적 한계 둘. F-2 가 형태가 아니라 시간 선후로 가르는 이유"),
    ("14.15", "i", "**결론 — 제안된 방법 전부 이론 없음·정성적·소표본·분포 겹침·미검증. 장차 신뢰할 방법이 나올 가능성도 의심**", DONE, CONFLICT,
     "실무Ⅳ 제4절 2 '금속조직관찰에 의한 전기용흔' 전체에 대한 국제 문헌의 판정. 온톨로지는 F-2·MetallographyAloneShape 로 이미 이쪽. 논문에서 이 상충을 한 절로 쓸 것"),
]

# CONFLICT 와 NONE 에서 나온 후보. 붙이기 전에 두 질문 — 화재도 내는가 / 그 요인에서만인가.
# (번호, 이름, 원문이 말하는 것, 출처 쪽, 온톨로지에서의 자리)
CANDIDATES = [
    ("①", "접점 융착은 화재도 낸다", "통전 없이 목재 화재 노출만으로 접점·바이메탈 서모스탯·차단기 접점이 융착. 부품의 심한 소손으로 외부 화재 융착을 가른다",
     "p.762 (Béland)", "audit.py ContactWelding ELEC → FIRE. ExternalFlameScenario canManifest ContactWelding 추가, R_PC_sup8 가감점 재유도(감쇠). "
     "실무Ⅴ p.238 은 '아크가 융착시킨다'지 '화재는 못 시킨다'가 아니었다 — 7장 ⑨ 와 같은 오독. 일곱 번째 형태 편향"),
    ("②", "쥐 갉음·스테이플은 트래킹도 낸다", "Hosaka 흐름도: 배설물이 있으면 누설·아크 트래킹. 스테이플 4경로 중 하나가 트래킹",
     "p.787·790", "RodentGnawing·MisdrivenStaple enables ArcTracking(오염 = 배설물). 실무Ⅳ p.252 쥐 오줌 PTC 와 일치. 사례에 쥐 0건이라 정확도 불변"),
    ("③", "열적 열화 → 트래킹 (오염 환경 없이)", "과열 접속부가 PVC 를 열화시켜 염화칼슘이 대기 습기를 흡수 → 탄화 경로 → 아크. UL 탄화 4경로 중 '열분해'",
     "p.758 (Ashizawa), p.774~775", "TrackingScenario 의 필요조건 ContaminatedEnvironment(C-5) 가 이 경로를 못 덮는다. 실무Ⅳ p.196 '절연열화 발화형태 = 트래킹'과 3.1.5바 서모스탯이 같은 편. "
     "**설계 결정 필요** — ThermalDegradation 을 트래킹 선행조건에 넣으면 트래킹·절연열화 경계(대상으로 가르는 관례, 인계 4.3)가 흔들린다. 사례로 먼저 센다"),
    ("④", "최하류 = 최초 아크 가정의 조건", "강한 화재에 노출된 회로는 전 구간 동시 아크. 부하측이 1차라는 추론은 그때 무효",
     "p.778 (Bernstein)", "FurthestDownstreamRuleShape(D-5) 주석과 실무Ⅳ p.185·305 인용에 조건을 단다. §9.13 아크 매핑도 같은 한계를 둔다. 규칙은 유지"),
    ("⑤", "나사 재질(강철/황동)과 체결 토크", "강철 나사가 황동보다 훨씬 글로잉 취약, 자석으로 식별. 14 AWG 최소 0.7 N·m, 수명 ∝ 토크³",
     "p.759·764 (Meese, NIST, Hicks)", "관측 가능한 접촉불량 선행조건 둘. 토크는 dataset 슬롯이 이미 있음(slot_fastening_torque) — 온톨로지 속성 없음. 나사 재질은 새 어휘. 서식 항목 D 에 '나사 재질' 추가 검토"),
    ("⑥", "절연저항 정상은 트래킹을 반증하지 못한다", "페놀 램프홀더 습기 트래킹 — 저항 정상, 재통전 시 파열. 고임피던스 전원에서 '빛나는 실이 핀에서 핀으로'",
     "p.753 (Cooper)", "R_TR_ref(NormalInsulationResistance → 트래킹 −30)의 반례. 탄화 경로는 건조하면 고저항, 통전·습윤 시 저저항. 사례 발동 0. make refute 후 역할 재검토"),
    ("⑦", "열선(동파방지)의 고장 모드", "번아웃(노후·과단열) / 열분해(도약 아크) / 자기제어형 습기 침입 wet fire 40 밀리암페어. 수명 3년",
     "p.854~856", "사례 150건의 열선 2건(절연열화)이 이 절. 열선은 CordMidspanSite 와 다른 자리 — 어휘 없음. 3건 미만이라 만들지 않는다"),
]


def counts():
    n = Counter(s[3] for s in SECTIONS)
    return n, len(SECTIONS) - n[OUT] - n[PROC]


def sub_counts():
    n = Counter(s[3] for s in SUBSECTIONS)
    return n, len(SUBSECTIONS) - n[OUT] - n[PROC]


def relations():
    return Counter(s[4] for s in SECTIONS + SUBSECTIONS if s[3] not in (OUT, PROC))


MARK = {DONE: "■", PART: "◐", NONE: "□", OUT: "·", PROC: "×"}
REL = {AGREE: "=", CONFLICT: "≠", ADDS: "+", NA: " "}


if __name__ == "__main__":
    n, ins = counts()
    print(f"Babrauskas, Ignition Handbook (2003) 전기 절 — {len(SECTIONS)}개, 범위 내 {ins}개\n")
    print(f"  구현 {n[DONE]}   일부 {n[PART]}   없음 {n[NONE]}   범위밖 {n[OUT]}   현장절차 {n[PROC]}")
    print(f"  이식률 {n[DONE]}/{ins} = {n[DONE] / ins * 100:.0f}%")
    sn, sins = sub_counts()
    print(f"\n  하위 절 {len(SUBSECTIONS)}개, 범위 내 {sins}개 — 구현 {sn[DONE]}  일부 {sn[PART]}  없음 {sn[NONE]}")
    print(f"  이식률 {sn[DONE]}/{sins} = {sn[DONE] / sins * 100:.0f}%")
    r = relations()
    print(f"\n  국내 실무Ⅳ와의 관계(범위 내 절+하위) — 일치 {r[AGREE]}  상충 {r[CONFLICT]}  보강 {r[ADDS]}  비교 없음 {r[NA]}\n")

    ch = None
    for sec, pg, title, st, rel, note in SECTIONS:
        c = sec.split(".")[0]
        if c != ch:
            ch = c
            print(f"\n── {CH[c]}")
        print(f"  {MARK[st]}{REL[rel]} {sec:6s} p.{pg:<3d} {title[:44]:44s} {st}")
        if st in (NONE, PART) or rel == CONFLICT:
            for i in range(0, len(note), 74):
                print(f"            {note[i:i + 74]}")

    print("\n\n── 하위 절까지 내려간 절 " + "─" * 44)
    order = [s[0] for s in SECTIONS]
    for p_ in sorted({x[0] for x in SUBSECTIONS}, key=order.index):
        rows = [x for x in SUBSECTIONS if x[0] == p_]
        k = Counter(x[3] for x in rows)
        m = len(rows) - k[PROC] - k[OUT]
        title = next(s[2] for s in SECTIONS if s[0] == p_)
        print(f"\n  §{p_} {title[:40]}  대상 {m}개 — 구현 {k[DONE]}  상충 {sum(1 for x in rows if x[4] == CONFLICT)}")
        for sec, sub, t, st, rel, note in rows:
            print(f"    {MARK[st]}{REL[rel]} {sub:2s} {t[:70]}")
            if st in (NONE, PART) or rel == CONFLICT:
                for i in range(0, len(note), 70):
                    print(f"           {note[i:i + 70]}")

    print("\n\n── 상충·없음에서 나온 후보 — 붙이기 전에 두 질문을 거친다 " + "─" * 12)
    for no, name, says, src, place in CANDIDATES:
        print(f"\n  {no} {name}  ({src})")
        print(f"     원문: {says}")
        print(f"     자리: {place}")
