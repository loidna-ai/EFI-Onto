# -*- coding: utf-8 -*-
"""화재조사실무Ⅳ(2025) 제2편 전기화재감식 절 대조표. 국내 실무 층의 두 번째 분모.

왜 필요한가
  domestic.py 는 표 2-1 의 갈래 24개를 분모로 든다. 그러나 표 2-1 은 '발생 경로'의
  분류이지 감식 기준의 목록이 아니다. 실무Ⅳ 제2편(p.126~342, 217쪽)에 흩어진 감식
  기준 — 용흔 판정, 기기별 감식 포인트, 절연열화 원인 목록 — 은 낱말 검색으로만
  찾아 옮겼고(TTL 인용 22쪽) 목차 단위로 '무엇을 안 담았는가'를 세어 본 적이 없었다.
  nfpa.py 가 NFPA 921 에 하는 일을 이 파일이 실무Ⅳ에 한다.

절 목록은 PDF 본문의 표제 글꼴 크기로 뽑았다(12.1pt = 'N.', 10.8pt = '가.').
인쇄 쪽수 = PDF 쪽 − 13. 제3장 제3절의 감식사례는 기기마다 항목 단위로 내려갔다 —
그것이 국내 실무가 판정 기준을 적는 자리이기 때문이다.

상태
  DONE  가설·메커니즘·선행조건·손상 양상·규칙·도형 중 하나로 물화됐고 판정에 쓰인다
  PART  어휘는 있으나 판정에 쓰이지 않거나, 절의 일부만 담았다
  NONE  없다 — 원문이 감식 기준을 주는데 온톨로지에 자리가 없다
  OUT   범위 밖으로 결정함 — 5대 요인 밖·배경 이론·발화지점 특정. 이유를 적는다
  PROC  현장·감정 작업 절차. 온톨로지가 표현할 대상이 아니다. 분모에서 뺀다

읽는 법
  NONE 이 이 파일의 값어치다. nfpa.py 와 domestic.py 는 NONE 이 0 이었다 — 못 담은
  것을 전부 OUT 으로 돌렸기 때문이다. 여기서는 원문이 감식 기준을 주는데 어휘가
  없으면 NONE 으로 남긴다. 그 목록이 CANDIDATES 이고 다음 작업이다.
  CANDIDATES 는 후보다. 붙이기 전에 CLAUDE.md 의 질문 둘을 거친다 — 이 흔적을
  화재 자체가 낼 수 있는가, 정말 그 요인에서만 일어나는가.
"""
from collections import Counter

DONE, PART, NONE, OUT, PROC = "구현", "일부", "없음", "범위밖", "현장절차"

CH = {"1": "제1장 전기화재", "2": "제2장 전기화재 감식",
      "3.1": "제3장 제1절 배선기구", "3.2": "제3장 제2절 조명기구",
      "3.3": "제3장 제3절 가전 및 주방기기", "3.4": "제3장 제4절 용흔의 판정과 소손흔",
      "4": "제4장 전기화재 조사장비"}

# (절, 쪽, 제목, 상태, 우리 쪽 대응 또는 빠진 내용)
SECTIONS = [
    # ── 제1장 전기화재 ──────────────────────────────────────────────────────
    ("1.1", 127, "전기화재 발생 과정 · 표 2-1", DONE,
     "표 2-1 은 domestic.py 가 갈래 24개로 판정한다. 발열 종류(줄열·아크)는 ResistiveHeating·ArcHeating"),
    ("1.2", 129, "전기란?", OUT, "용어의 유래. 판정 요건이 없다"),
    ("1.3", 129, "전류·전압·저항 등 전기이론의 기초", OUT,
     "배경 이론. §9.2 와 같은 판정. 차.소선 용단특성·카.금속 용융점은 하위 절 참조"),
    ("1.4", 136, "옴의 법칙, 줄의 법칙", OUT, "배경 이론"),
    ("1.5", 138, "교류와 직류", OUT, "배경 이론. 직류 조건은 은 이동(범위밖)에만 쓰인다"),
    ("1.6", 140, "전기재료·부품 — 절연재료, 저항기, 콘덴서, 코일", PART,
     "라.콘덴서 5) 관찰 포인트만 판정에 쓴다(p.145~146). 나머지는 부품 이론. 하위 절 참조"),
    ("1.7", 148, "절연물 표면 도체 부착·도체로의 변질", DONE,
     "트래킹·반단선·아산화동 셋이 5대 요인의 핵심 절. 하위 절 참조"),
    ("1.8", 156, "지락·누전 및 고압부 누설방전", PART,
     "가.지락·누전은 LeakageCurrentHeating·GroundFaultProtectiveDevice. 나.고압부는 범위밖"),
    ("1.9", 157, "정전기 방전에 의한 발화", OUT, "5대 요인 밖. §9.14 와 같은 판정"),
    ("1.10", 166, "뇌(雷)", OUT, "자연 요인. 표 2-1 에서도 별도 항목"),
    # ── 제2장 전기화재 감식 ──────────────────────────────────────────────────
    ("2.1", 178, "통전입증", PART,
     "EnergizedState 는 있으나 지지 규칙이 없다(gaps.py 137건). 칼날 광택·칼날받이 열림 같은 "
     "통전 판별 단서는 어휘가 없다. 하위 절 참조"),
    ("2.2", 181, "수거 등 현장처치", PART,
     "대부분 현장 절차. 사.4) 각 부품의 감식 포인트가 판정 기준이며 그중 극별 용융 위치가 빠져 있다. 하위 절 참조"),
    ("2.3", 189, "감식종료 후의 처리", OUT, "처분·조서·자료관리. §4.7 보고 절차와 같은 판정"),
    # ── 제3장 제1절 배선기구 ─────────────────────────────────────────────────
    ("3.1.1", 191, "배선용차단기", DONE,
     "표 2-18 동작시간(D-12), 접속부 과열 요인(p.194), 절연열화 원인 목록(p.196). 구조·감식 절차는 제외. 하위 절 참조"),
    ("3.1.2", 198, "누전차단기", DONE,
     "표 2-19 정격감도전류(GroundFaultProtectionRuleShape), 절연열화 원인 ①(p.201 → TerminalSite·DeviceInteriorSite). 구조는 제외"),
    ("3.1.3", 203, "커버나이프스위치", DONE,
     "퓨즈 용단 4형태 FuseMeltPattern(p.203), 접속터미널 변색흔 LongTermTerminalHeating. 개폐 판정은 현장 절차"),
    ("3.1.4", 205, "케이블과 주변 구조물", DONE,
     "샌드위치 패널 절단면 마찰 → AbrasionAtPenetration. 입증 요건 ③ 부하측 무이상은 SupplyPathCoverageShape(C-43)"),
    ("3.1.5", 206, "스위치, 전자접촉기, 커넥터", DONE,
     "접점 용착 ContactWelding(p.211), 부품 국부 고열/주위 손상 경미(p.210·211), 터미널 접촉불량+아산화동. 하위 절 참조"),
    # ── 제3장 제2절 조명기구 ─────────────────────────────────────────────────
    ("3.2.1", 213, "백열전구", PART,
     "가연물 접촉·전구 이동은 사용방법(범위밖). 마)기구 배선 진동 접촉불량은 Vibration→접촉불량. "
     "나)점등 중 파손 필라멘트 용착은 통전 판별 단서인데 어휘 없음"),
    ("3.2.2", 217, "형광등", DONE,
     "안정기 층간단락 진행과정(p.219~220 InterTurnShortCircuit), 점등관 소켓 접촉불량, 기판 트래킹, 기구 내 배선 끼임·진동. 하위 절 참조"),
    ("3.2.3", 223, "네온등", OUT,
     "고압 방전 설비. 표 2-1 고압부 누설방전과 같은 판정. ㉵ 점멸기 단자 구리가루 트래킹은 SalineOrChemicalExposure·DustAccumulation 으로 덮인다"),
    ("3.2.4", 227, "HID램프", OUT, "고압 방전램프. ⑧ 안정기 층간단락은 InterTurnShortCircuit"),
    # ── 제3장 제3절 가전 및 주방기기 ──────────────────────────────────────────
    ("3.3.1", 230, "텔레비전과 컴퓨터모니터", PART,
     "고압 누설방전(1)·반도체 고장(6)은 범위밖. 층간단락(2), 기판 트래킹(3·4), 코드 눌림(7), 플러그 트래킹(8)은 구현. "
     "납땜 크랙(5)은 어휘 없음. 하위 절 참조"),
    ("3.3.2", 240, "전자레인지", PART,
     "식품 과열·금속 방전(1~3)은 범위밖. 기판 오염 트래킹(4), 래치스위치 접점 마모(5), 모터·트랜스 층간단락(6·8), "
     "코드 눌림·스테이플·카펫(7)은 구현. 하위 절 참조"),
    ("3.3.3", 248, "냉장고", DONE,
     "기동기 결로+먼지 트래킹(1), 커넥터·플러그·삽입구(3), 층간단락(5), 콘덴서 내부 탄화(6, p.254), 진동 마찰(7). 하위 절 참조"),
    ("3.3.4", 257, "세탁기", DONE,
     "채터링 IntermittentContactSeparation(1·2), 콘덴서 결로 부식·흡습 절연열화(3), 진동 마찰(다). 클러치 슬립 마찰열은 비전기(범위밖)"),
    ("3.3.5", 262, "냉·온수기, 전기밥솥, 전기히터, 토스터", PART,
     "냉온수기 서모스탯 트래킹·밥솥 기판 밥물 트래킹·코드 반단선은 구현. 히터·토스터는 사용방법·고장(범위밖). 하위 절 참조"),
    ("3.3.6", 281, "에어컨", DONE,
     "층간단락(1·2), 프레임 마찰 단락(3·4), 쥐 갉음 반단선(5), 꼬아 접속 과열(6), 기판-단자 진동 접촉불량(나). "
     "하위 절 참조 — 4)·5)에 사슬 검토 항목"),
    ("3.3.7", 288, "선풍기", DONE,
     "도금 고화 배선의 좌우회전 반복 굴곡 반단선(RepeatedFlexing), 콘덴서 습기 절연열화(p.289 CapacitorSite), 모터 층간단락 링회로"),
    ("3.3.8", 292, "전기스토브와 세라믹히터", PART,
     "가연물 접촉·오조작은 사용방법. 세라믹히터 S자 스프링(InsufficientContactPressure)·공통단자 헐거움(LooseConnection)은 구현. "
     "니크롬선 용융 판별(p.293)은 어휘 없음"),
    ("3.3.9", 297, "전기장판, 카펫", PART,
     "컨트롤러 내 릴레이 스파크 → 케이스 흑연화 → 트래킹(p.299)은 DeviceInteriorSite·OrganicInsulationPresent. "
     "다.감식사례 본문은 HID램프 절의 오식(원문 결함)"),
    ("3.3.10", 300, "특별고압수전설비", OUT,
     "고압 설비. 8)적산전력계 단자 느슨·빗물은 접촉불량 어휘로 덮이나 계량기는 §9.3.3 과 같이 범위밖"),
    # ── 제3장 제4절 용흔의 판정과 소손흔 ────────────────────────────────────
    ("3.4.1", 304, "용흔의 판정 방법", DONE,
     "1차·2차·열용흔 → PrimaryArcMark·SecondaryArcMark·FireMeltMark, F-2 시간 선후. 여러 개소면 부하측(D-5). 하위 절 참조"),
    ("3.4.2", 306, "금속조직관찰에 의한 전기용흔", DONE,
     "광택·평활도·반구형(p.308), 열용흔 3형(p.309), 이물 혼입·공극(voidFraction·fineDendriticGrain). "
     "단독 판정 불가는 MetallographyAloneShape"),
    ("3.4.3", 311, "과전류와 화염에 의한 전선피복의 소손흔", DONE,
     "UniformDamageAlongConductor·CarbonizationFromInsideOut(p.312). 200~300% 온도·시간 단계는 실험값이라 담지 않는다"),
    ("3.4.4", 313, "과전류에 의한 전선 용단흔의 특징", PART,
     "OverloadMeltingNotProofShape·Sleeving·MeltOffset 은 NFPA 쪽. '망울이 정상 표면을 감싼다'·'미용융 표면 산화 박리'는 어휘 없음"),
    ("3.4.5", 315, "외부화염에 의한 전선피복의 표면형태", DONE,
     "경계 명확·밖→안 탄화 → CarbonizationFromInsideOut 부정, 2차 합선 → SecondaryArcMark. 하위 절 참조"),
    ("3.4.6", 318, "소화 후에 나타나는 손상형태", DONE,
     "StretchedThinnedEnd, AlloyDiscoloration·AlloyConductor(AlloyConductorArcMarkShape), PostFireMechanicalDamage(PostFireDamageShape). 전부 p.318 인용"),
    # ── 제4장 전기화재 조사장비 ───────────────────────────────────────────────
    ("4.1", 320, "검전기", PROC, "안전 확보 장비. §9.12.3 과 같은 판정"),
    ("4.2", 323, "회로시험기", PROC, "장비 조작. 도통시험 결과는 Instrument 관측으로 들어온다"),
    ("4.3", 331, "절연저항계", PART,
     "표 2-22 저압전로 절연저항 기준은 D-9 InsulationResistanceDerivationRuleShape 가 대상 속성으로 든다. 장비 조작은 현장 절차"),
    ("4.4", 334, "클램프미터", PROC, "누설전류 측정 절차. 기준값(표 2-19)은 3.1.2 에서 구현"),
    ("4.5", 336, "접지저항계", PROC, "접지저항 측정 절차. 판정에 쓰이지 않는다"),
]

# 하위 절. (절, 항, 제목, 상태, 근거)
SUBSECTIONS = [
    # 1.3
    ("1.3", "차", "소선의 용단특성(Preece 실험식)", OUT,
     "용단 전류 공식. 가설 시험 시 참조하는 공학 지식이지 감식 대상이 아니다(§9.9.2.4 와 같은 판정)"),
    ("1.3", "카", "금속의 용융점", PART,
     "F-3 IgnitionCompetenceRuleShape 가 온도를 견주지만 금속별 용융점 표는 값으로 들고 있지 않다"),
    # 1.6
    ("1.6", "나", "절연재료 내열 구분(표 2-4)", OUT, "재료 규격. 판정에 쓰이지 않는다"),
    ("1.6", "라5", "콘덴서 관찰·조사 포인트", DONE,
     "자체 출화면 알루미늄이 갈라져 부풀고 외부화염이면 원형 유지 탄화(p.146) → InternalDamageExceedingSurface. 습기 → 트래킹은 CapacitorSite"),
    # 1.7
    ("1.7", "가1", "트래킹현상 — 정의", DONE,
     "이극 도체 사이 고체절연물 표면 → InterPoleInsulatingSurface. 유기 절연물 → OrganicInsulationPresent. TrackingScenario 의 필요조건"),
    ("1.7", "가2", "트래킹 진행과정 3단계", DONE,
     "1단계 오염(습기·염분·무기질·섬유질·도전성물질) → MoistureExposure·SalineOrChemicalExposure·DustAccumulation. 2·3단계는 CarbonizedConductivePath 로 귀결"),
    ("1.7", "나", "그라파이트 현상", PART,
     "경계는 '관례적'(p.149)이라 클래스로 가르지 않고 주석만. domestic.py 표 2-1 도 같은 판정"),
    ("1.7", "다", "반단선 — 10% 정의·발생 개소·용흔 위치", DONE,
     "StrandFractureOverTenPercent(D-11), 플러그 접속부 부근 StressConcentrationPoint·PlugJunctionArea, "
     "양측 용흔 MeltMarkOnBothSidesOfBreak vs 전원측 편중 MeltMarkOnSupplySideOnly(p.150). '통전 단면적 감소 = 과부하'는 D-1"),
    ("1.7", "라1", "아산화동 — 발화원인 경향", DONE,
     "접속기구 체결 불량·느슨함 → 국부 과열 → 아산화동. PoorContactHeating 의 하위 GlowingConnection, CuprousOxideGrowth"),
    ("1.7", "라3", "아산화동 외관 — 적색 결정", DONE,
     "RubyRedCrystal(p.153). 현미경 없을 때 저항이 0도 ∞도 아니고 가열 시 감소하는 판별(p.154 다)은 클래스 주석에"),
    ("1.7", "라5", "아산화동 없으면 접촉저항 발열", DONE,
     "CuprousOxideDerivationRuleShape 가 접촉불량 안에서 가른다. ReducedContactArea·IntermittentContactSeparation 이 나머지 갈래"),
    ("1.7", "마", "보이드에 의한 절연파괴", PART,
     "DendriticTreePath 로 전기 트리만. 보이드 어휘 없음. 고압 설비라 5대 요인 밖"),
    ("1.7", "바", "은 이동", OUT, "직류기기 현상. domestic.py 와 같은 판정"),
    # 1.8
    ("1.8", "가", "지락과 누전의 차이", DONE, "LeakageCurrentHeating. 지락/누전은 용어 차이라 한 클래스로 둔다"),
    ("1.8", "나", "고압부 누설방전 · 수 트리", OUT,
     "고압 트랜스·네온. 수 트리는 DendriticTreePath 어휘만 있고 CV케이블 고압이라 판정에 쓰지 않는다"),
    # 2.1
    ("2.1", "가", "플러그의 칼날 — 광택·변색 경계로 통전 판별", NONE,
     "칼날 접촉면 광택 잔존·그을음 경계라는 통전 입증 단서에 어휘가 없다. "
     "같은 절의 '칼날 사이 습기 → 탄화도전로'는 WiringDeviceSite 트래킹으로 구현. CANDIDATES ⑦"),
    ("2.1", "나", "칼날받이 — 열린 채 고착·용흔 정합", NONE, "통전 입증 단서. 어휘 없음. CANDIDATES ⑦"),
    ("2.1", "다", "중간스위치·기구스위치 ON/OFF 판별", PROC,
     "X선·도통시험 절차. 결과(통전 여부)만 EnergizedState 로 들어온다"),
    ("2.1", "라", "배선 — 스테이플·급굽힘·인출부 눌림+진동", DONE,
     "MisdrivenStaple, ExternalCrushing, ApplianceEntryPoint, Vibration. 1)케이블 다회선 포설 온도상승 → BundledWiring"),
    ("2.1", "라b", "용흔 일부·변색 부분 상이 → 장력", PART,
     "Tension 은 있으나 '변색이 부분적으로 다르다'는 관측에서 장력을 도출하는 규칙은 없다"),
    # 2.2
    ("2.2", "가", "출화지점 판정 — 기기 내 용흔이 있어도 발화원 단정 금지", DONE,
     "ArcMeltAloneShape(C-8): 용흔은 통전만 증언한다. 연소·수열 방향 판정 자체는 발화지점(범위밖)"),
    ("2.2", "나~바", "출화 가능성 검토·수속·채취·설명·협조", PROC, "현장 절차"),
    ("2.2", "사1", "사전준비 — 리콜·수리이력·평상시 사용", PROC,
     "자료 입수 절차. 출화 전 이상 상황 청취는 PreFireAnomaly 로 들어온다"),
    ("2.2", "사2", "감식요령 공통 — 6면 관찰·촬영·분해", PROC, "§9.12.6.2 와 같은 판정"),
    ("2.2", "사3", "결론 도출 — 연소방향성과 용흔 위치의 정합", DONE,
     "ArcMarkAwayFromOriginShape: 연소 중심과 이격된 단락흔은 발화원 근거가 못 된다"),
    ("2.2", "사4①", "콘센트·플러그 — 한 극만 용융이면 접촉부 과열, 양극이면 트래킹", NONE,
     "극별 용융 위치가 접촉불량과 트래킹을 가르는 단서인데 어휘가 없다. ⑦㉰·⑧ 에서 같은 기준이 세 번 나온다. CANDIDATES ①"),
    ("2.2", "사4②", "스위치 접점 용착", DONE, "ContactWelding. 용착 → 전원 차단 기능 상실 → 히터 과열은 고장(범위밖)"),
    ("2.2", "사4③", "퓨즈 4형태 — 단락·과부하·접촉불량·외부화염", DONE,
     "FuseGloballyMeltedScattered·FuseMeltedAtCenter·FuseEndsDarkened(R_PC_sup4)·FuseIrregularlyMelted(R_EF_sup4). "
     "단락·과부하 형은 가설이 아니라 어휘만. 온도퓨즈는 범위밖"),
    ("2.2", "사4④", "반도체", OUT, "부품 내부 파괴. domestic.py 와 같은 판정"),
    ("2.2", "사4⑤", "콘덴서 — 소자 중심부 소손이면 자체 출화", DONE, "InternalDamageExceedingSurface"),
    ("2.2", "사4⑥", "코일 — 층간단락·과부하운전·고주파", PART,
     "InterTurnShortCircuit·WindingSite. 과부하운전은 OverloadState 확장 슬롯, 고조파는 범위밖"),
    ("2.2", "사4⑦㉮", "코드에만 용흔·부품 무이상 → 코드 단락", PART,
     "SupplyPathCoverageShape 가 부하측 검사 범위를 요구한다. '다른 데 없으니 코드'는 C-2 소거법 경계라 규칙으로 두지 않는다"),
    ("2.2", "사4⑦㉯", "여러 개소 용흔 → 가장 부하측이 화원", DONE, "FurthestDownstreamRuleShape(D-5)"),
    ("2.2", "사4⑦㉰", "한쪽 소선에만 용흔 → 반단선·접촉불량·지락", NONE,
     "①과 같은 기준. 부근 금속 용흔이면 지락 → CorrespondingDamageArea 로 일부. CANDIDATES ①"),
    ("2.2", "사4⑧", "기판 접속부 — 한 극 용융 접촉불량·납땜불량, 양극 트래킹", NONE,
     "①과 같은 기준. 납땜 불량은 어휘 없음(3.3.1 다5 와 같다). CANDIDATES ①·②"),
    # 3.1.1
    ("3.1.1", "나라", "표 2-18 과전류차단기 동작시간특성", DONE, "ProtectiveDeviceOperationRuleShape(D-12). 기준값은 대상 속성"),
    ("3.1.1", "다", "접속부 과열 — 요철 집중저항·기름 경계저항·압력 부족·진동 이완·부식·변형", DONE,
     "ContaminatedContactSurface·InsufficientContactPressure(p.194), Vibration, CorrodedConnection, DeformedPlugOrSwitch"),
    ("3.1.1", "다가", "접속부 과열 발화요인 7 — 이물·마모·용착·전이·채터링·과전압·가동부", DONE,
     "①ContaminatedContactSurface ③④ContactWelding ⑤IntermittentContactSeparation. ⑥허용량 이상 전압·전류는 OverloadState 확장 슬롯"),
    ("3.1.1", "라", "절연열화 원인 5 — 먼지·습기, 취급 손상, 이상전압, 과전류 열적열화, 결로 / 발화형태 = 트래킹·흑연화", DONE,
     "①R_ID_sup7·R_ID_sup8 ④ThermalDegradation ⑤MoistureExposure. ②취급 손상은 MechanicalDamageAntecedent. "
     "③이상전압은 어휘 없음 — 5대 요인 밖 원인이라 두지 않았다(판단). 발화형태 문장이 트래킹·절연열화 경계의 근거(CLAUDE.md)"),
    ("3.1.1", "마", "외형 감식 — 저항·X선·동작편 위치", PROC, "동작편 중립 → 부하측 과부하·단락은 BreakerTripRecord 로 들어온다"),
    # 3.1.2
    ("3.1.2", "다", "표 2-19 정격감도전류·동작시간", DONE, "GroundFaultProtectionRuleShape. 기준값은 대상 속성"),
    ("3.1.2", "라", "절연열화 원인 — ①단자·몰드케이스 먼지·습기 트래킹", DONE,
     "TerminalSite·DeviceInteriorSite + 오염 확인 → TrackingSiteDerivationRuleShape(D-13)"),
    ("3.1.2", "나다③", "과전압 트립 — 중성선 결상 시 과전압", PART, "OpenNeutral·OpenNeutralOvervoltage 확장 슬롯"),
    # 3.1.5
    ("3.1.5", "가", "스위치류 — 접점 접촉불량 용착·가동부 동작불량", DONE,
     "ContactWelding. 부하기기 장시간 통전 과열은 고장 갈래(범위밖)"),
    ("3.1.5", "나다", "텀블러스위치 절연열화 — 오물·부식·마모가루, 릴레이 접점 소모", DONE,
     "ContaminatedEnvironment·CorrodedConnection(p.206, cause_audit). 접점 소모 → IntermittentContactSeparation"),
    ("3.1.5", "다마", "전자접촉기 터미널 접촉불량 + 아산화동 상승작용", DONE,
     "PoorContactHeating → CuprousOxideGrowth. 온도측정(14℃ 차)은 현장 절차"),
    ("3.1.5", "다사", "전자접촉기 감식 ①주위 손상 적으면 외부화염 ②코어 고열·내부 손상 심하면 자체 ③조작코일 층간단락", DONE,
     "IntactSurroundingsAroundComponent(R_ANY_Intact·R_EF_sup5), LocalizedHeatWithSurroundingDamage(R_ANY_LocalHeat), InterTurnShortCircuit"),
    ("3.1.5", "라", "커넥터 — 같은 기준", DONE, "위와 같다"),
    ("3.1.5", "마", "릴레이 접점 융착 — 아크 → 변형 → 접촉저항 상승 → 융착 → 계속 통전", DONE, "ContactWelding(p.211)"),
    ("3.1.5", "바", "바이메탈 서모스탯 — 접점 아크가 주변 절연재를 열화시켜 트래킹", PART,
     "결과(DeviceInteriorSite 트래킹)는 구현. '접점 아크가 오염원'이라는 사슬 — 아크 비산 금속분 → ContaminatedEnvironment — 은 없다"),
    # 3.2.1
    ("3.2.1", "나", "점등 중 파손 — 필라멘트 산화 소실·앵커 용착 → 점등 상태 입증", NONE,
     "통전 입증 단서. 2.1 과 같은 자리. CANDIDATES ⑦"),
    ("3.2.1", "마", "기구 배선 접속부 진동 접촉불량", DONE, "Vibration → PoorContactScenario(R_PC_sup3)"),
    ("3.2.1", "바", "전구 변형으로 연소 진행방향", OUT, "발화지점 특정"),
    # 3.2.2
    ("3.2.2", "가", "안정기 층간단락 진행 — 절연열화 → 층간단락 → 이상발열 → 확대", DONE,
     "InterTurnShortCircuit(p.219~220 되먹임 고리), WindingSite. ㉯ 이음·이취는 FlickeringOrOdor(규칙 없음, gaps.py)"),
    ("3.2.2", "나", "점등관 — 바이메탈 아크 용융 과전류 / 소켓 접촉불량", PART,
     "소켓 접촉불량은 ConnectionCondition. 바이메탈 용융 → 지속 과전류는 어휘 없음(고장 갈래)"),
    ("3.2.2", "다", "전자회로 부품 — 절연파괴·트래킹·납땜부 접촉저항", PART,
     "트래킹은 구현. 부품 절연파괴는 범위밖. 납땜 균열·이완은 어휘 없음. CANDIDATES ②"),
    ("3.2.2", "라", "인입선·기구 내 배선 — 접속불량, 끼임·찍힘, 간접단락·지락, 진동 외함 접촉", DONE,
     "ConnectionCondition, ExternalCrushing, LeakageCurrentHeating, Vibration+AbrasionAtPenetration. "
     "'외부 화염이면 기구 내 단락 전에 전원이 끊긴다'는 F-2 와 정합"),
    # 3.3.1
    ("3.3.1", "다1", "고압회로 누설방전 — 플라이백·브라운관 균열", OUT, "고압부. 1.8나 와 같은 판정"),
    ("3.3.1", "다2", "플라이백트랜스 층간단락", DONE, "InterTurnShortCircuit. 충전수지 크랙 분출은 InternalDamageExceedingSurface 와 같은 꼴"),
    ("3.3.1", "다3", "기판 핀-접지패턴 먼지 트래킹 · 재질이 흑연화 가능한가", DONE,
     "DeviceInteriorSite+DustAccumulation → D-13. 재질 → OrganicInsulationPresent"),
    ("3.3.1", "다4", "포지스터 단자 먼지·수분 트래킹 — 대기전압 상태", DONE, "같은 사슬. 대기전압은 EnergizedState 로 들어온다"),
    ("3.3.1", "다5", "납땜 크랙 방전 발열", NONE,
     "납땜 불량·균열은 접촉불량의 한 갈래인데 어휘가 없다. 2.2사4⑧·3.2.2다 와 같다. CANDIDATES ②"),
    ("3.3.1", "다6", "반도체 고장 — 트랜지스터 내부 단락 과전류", OUT, "부품 내부 파괴"),
    ("3.3.1", "다7", "전원코드 눌림 단락", DONE, "ExternalCrushing"),
    ("3.3.1", "다8", "플러그 트래킹 — 장기간 꽂아 둠·먼지", DONE, "WiringDeviceSite+DustAccumulation"),
    # 3.3.2
    ("3.3.2", "나1~3", "식품 과열·금속 방전·찌꺼기", OUT, "마이크로파 가열. 사용방법 갈래"),
    ("3.3.2", "나4", "기판 기름·먼지·바퀴벌레 배설물 → 이극 단자 트래킹", DONE,
     "ContaminatedEnvironment(배설물은 오염물의 하나). (바) 절연기판 스파크·아크 흔적 → CarbonizedConductivePath"),
    ("3.3.2", "나5", "래치스위치 접점 마모 접촉불량 · 접점간 저항 수Ω~수십Ω", PART,
     "ReducedContactArea·IntermittentContactSeparation. 접점 저항 측정값은 어휘 없음 — CANDIDATES ③ 과 같은 계측"),
    ("3.3.2", "나6", "모터 배선·코일 — 층간단락, 통풍 저해, 진동 단락, 먼지·습기 열화", DONE,
     "InterTurnShortCircuit, HeatDissipationImpairment, Vibration, R_ID_sup7·R_ID_sup8"),
    ("3.3.2", "나7", "전원코드 — 눌림 1차용흔, 스테이플 반단선, 카펫 아래 방열 악화", DONE,
     "ExternalCrushing, MisdrivenStaple(R_PD_sup10), CoveredByFloorCovering(p.245)"),
    ("3.3.2", "나8", "트랜스·부품 — 층간단락, 단자 접촉불량, 통풍 저해, 고압콘덴서·다이오드, 고조파", PART,
     "앞 셋은 구현. 고압 부품·고조파·50/60Hz 오사용은 범위밖(domestic.py)"),
    # 3.3.3
    ("3.3.3", "가", "개요 — 기동 릴레이 스파크로 누설 가스 착화", OUT, "가스 착화. 전기적 발화 메커니즘이 아니라 착화물 문제"),
    ("3.3.3", "다1", "기동기 — 결로+먼지 → 단자·접점 트래킹, 페놀수지 경년열화 · 탄화부 저항 수Ω~수십Ω", PART,
     "MoistureExposure·DustAccumulation·DeviceInteriorSite·AgedInsulation 은 구현. "
     "(5) 탄화도전로 저항 측정은 어휘 없음 — 네 기기에서 반복되는 관측. CANDIDATES ③"),
    ("3.3.3", "다2", "PTC 릴레이 은 이동 · 쥐 배설물 스파크", OUT,
     "은 이동 범위밖. 쥐 배설물은 ContaminatedEnvironment 로 들어오나 PTC 단자는 직류"),
    ("3.3.3", "다3", "코드·커넥터 접속부 — 헐거움, 다발 배선, 방열부 눌림·카펫, 플러그 불완전 접촉, 삽입구 반단선, 결로 접점 트래킹, 히터선 가늘어짐, 쥐 갉음", DONE,
     "LooseConnection, BundledWiring, CoveredByFloorCovering(p.253), PlugJunctionArea·ApplianceEntryPoint, MoistureExposure, "
     "RodentGnawing·ToothMarkOnInsulation(p.253). (7)히터선 가늘어짐 적열은 통전 단면적 감소라 반단선과 같은 물리인데 어휘 없음"),
    ("3.3.3", "다4", "안전장치 제거 팬모터 과열 → 층간단락", PART, "층간단락은 구현. 온도퓨즈 제거는 개조불량(domestic.py PART)"),
    ("3.3.3", "다5", "컴프레서 코일 층간단락", DONE, "InterTurnShortCircuit·WindingSite"),
    ("3.3.3", "다6", "콘덴서 — 단자 느슨 / 소자 내부 절연열화 → 케이스 구멍·쪼개짐·내부 탄화", DONE,
     "LooseConnection / InternalDamageExceedingSurface(p.254). 고조파는 범위밖"),
    ("3.3.3", "다7", "진동 — 외함 날카로운 절단면과 내부 배선 마찰", DONE, "Vibration+AbrasionAtPenetration"),
    # 3.3.5
    ("3.3.5", "가1", "냉온수기 개요 — 서모스탯 접점 아크 용융 변형·비산 금속분이 절연물에 도포되어 절연파괴", PART,
     "접점 변형 → 접촉저항은 IntermittentContactSeparation. 아크 비산 금속분 → 오염 사슬은 3.1.5바 와 같이 없음"),
    ("3.3.5", "가3", "감식요령 — 층간단락, 피복 손상 단락, 쥐, 전자접촉기 단자 먼지·습기 트래킹, 결로 접점 트래킹, 서모스탯 단자 오염 트래킹·그래파이트", DONE,
     "전부 기존 사슬. 기동장치 스파크 가스 착화는 범위밖"),
    ("3.3.5", "가4", "입증 요건 — 연소형상·퓨즈/차단기 상태·전기적 특이점", PART,
     "특이점은 사실(Fact)로 들어온다. 퓨즈·차단기 상태는 BreakerTripRecord 어휘만(gaps.py RULE). 연소형상은 발화지점"),
    ("3.3.5", "나다", "전기밥솥 조사포인트 — 코드 반복 작동 반단선, 커넥터·나사 이완, 기판 밥물 트래킹, 코일 층간단락", DONE,
     "RepeatedFlexing, LooseConnection, MoistureExposure+DeviceInteriorSite, InterTurnShortCircuit. (5)~(9)는 부품·과전압·용도 외 사용(범위밖)"),
    ("3.3.5", "나2가", "기판 그래파이트 도통시험 · 수분 침투 경로 특정", PART,
     "도통 확인은 CANDIDATES ③. 경로 특정은 현장 절차. 트랜지스터 단락은 범위밖"),
    ("3.3.5", "나2나", "중성선 결손 과전압으로 취사히터 출화", PART, "OpenNeutralOvervoltage 확장 슬롯. §9.5.2 와 같은 자리"),
    ("3.3.5", "나2라", "기구 코드 반단선 — 부하전류 전제(보온 상태), 사용년수·설치환경", DONE,
     "EnergizedState 전제(규칙 없음), StressConcentrationPoint"),
    ("3.3.5", "다2", "전기히터 — 복사열·가연물 접촉·오조작", OUT, "사용방법 갈래"),
    ("3.3.5", "다2라", "전원코드 꺾음·물건 올림·방열 악화 단락, 비틀어 꼬아 접속, 가장 가까운 용흔이 화원", DONE,
     "ExternalCrushing, HeatDissipationImpairment, ConnectionJointSite, D-5"),
    ("3.3.5", "다2마", "시스히터 과밀 권선·과전압 과열", OUT, "제조 결함·과전압"),
    ("3.3.5", "라", "토스터 — 통전 방치·접점 용착·승강기구 고장", OUT, "사용방법·고장 갈래. 접점 용착만 ContactWelding"),
    # 3.3.6
    ("3.3.6", "나1", "컴프레서 모터 층간단락 — 환경 부적격·덕트 과부하운전·제조", PART, "층간단락은 구현. 과부하운전은 OverloadState 확장 슬롯"),
    ("3.3.6", "나2", "배수모터 층간단락 — 먼지 퇴적 과부하", PART, "같다"),
    ("3.3.6", "나3", "전원선 프레임 지락 → 누전차단기 강제 재투입 → 발열 → 단락", PART,
     "AbrasionAtPenetration 은 구현. 누전차단기 작동 여부·고장검사·프레임 용흔·접지저항은 BreakerTripRecord·CorrespondingDamageArea 어휘만"),
    ("3.3.6", "나4", "전원선 진동 프레임 접촉 단락 · 가장 부하측 용흔 2차측 무이상 · 금속 개입 단락은 차단기가 순간 작동 안 함", PART,
     "AbrasionAtPenetration+Vibration, D-5 는 구현. (3) '접촉저항이 커서 즉시 트립하지 않는다'는 R_CD_ref(NoTripDespiteExternalForce −30)와 "
     "긴장한다 — 사례 반례 여부를 make refute 로 볼 것. CANDIDATES ⑤"),
    ("3.3.6", "나5", "쥐가 갉아 히터선 반단선", PART,
     "RodentGnawing 은 압착손상에만 이어져 있다(cause_audit EXCL, p.253). p.286 은 갉음이 반단선도 만든다고 적는다 — 사슬 재검토. CANDIDATES ④"),
    ("3.3.6", "나6", "손으로 비틀어 꼬아 접속 → 접촉부 과열 · 차단기 일시 미동작", DONE, "ConnectionJointSite. 미동작 문장은 나4 와 같은 항목"),
    ("3.3.6", "나7", "배선 오접속 히터 과열", OUT, "인적 요인"),
    ("3.3.6", "나나", "기판-단자 진동 접촉불량 — 반복 단속·접촉저항 증가", DONE, "Vibration(R_PC_sup3)·IntermittentContactSeparation"),
    # 3.3.8
    ("3.3.8", "가2라", "니크롬선 용융(1,425℃)은 화재열(약 1,200℃)로 설명되지 않는다", NONE,
     "외부화염 가설의 반증 후보. 원인(과밀 권선·과전압)은 범위밖이지만 판별 기준 자체는 IgnitionCompetenceRuleShape(F-3) 자리다. CANDIDATES ⑥"),
    ("3.3.8", "나2", "세라믹히터 — S자 스프링 접촉압 상실, 공통단자 헐거움", DONE,
     "InsufficientContactPressure, LooseConnection. 다)회로설계 불량은 범위밖"),
    # 3.3.9
    ("3.3.9", "나", "컨트롤러 내 트래킹 — 전원 OFF·플러그만 꽂힘, 릴레이 스파크로 케이스 흑연화", DONE,
     "DeviceInteriorSite, OrganicInsulationPresent(재질), InterPoleInsulatingSurface(양극간 전위차). 탄화물 도통은 CANDIDATES ③"),
    # 3.4.1
    ("3.4.1", "가", "1차용흔 — 광택·치밀, 탄화물 미포함, 여러 개소면 부하측, 연선 선단 용착·반대측 무변화, 화재열로 표면 재융해 주의", DONE,
     "PrimaryArcMark, SmoothLustrousMeltSurface, D-5, SmallMeltBallOnStrandEnd. 재융해 주의는 F-2 가 형태가 아니라 선후로 가르는 이유"),
    ("3.4.1", "나", "2차용흔 — 광택 없음·망울 늘어짐·연선 용착 범위 큼", DONE,
     "SecondaryArcMark, WideMeltWithRoughSurface, DrippingMeltFormation"),
    ("3.4.1", "다", "열용흔 — 융해 범위 넓고 거칠고 광택 없음, 굵기 불균일", DONE, "FireMeltMark 3종(p.309)"),
    ("3.4.1", "라", "차단기 미차단이면 전원측으로 여러 개소", DONE, "VinylCord 주석(실무Ⅱ p.90)과 같은 사실"),
    ("3.4.1", "서", "주상조직·수지상조직 — 실험 단계, 단독 판정 불가", DONE, "MetallographyAloneShape. fineDendriticGrain 은 보강만"),
    # 3.4.2
    ("3.4.2", "가", "1차용흔 정의 — 피복 노후·손상 심선 접촉 / 굽힘 코드 소선 끊김 반단선 → 발열 → 피복 열화 → 단락", DONE,
     "CordMidspanSite(p.305), PartialDisconnectionInducedArc"),
    ("3.4.2", "라1", "외관관찰 — 아크가 생기는 세 경우(3상 선간·상-중성·지락)", OUT, "3상은 범위밖. 나머지는 ShortCircuitArc 의 정의"),
    ("3.4.2", "라라~바", "광택·평활도·형상(반구형)", DONE, "SmoothLustrousMeltSurface, HemisphericalMeltShape(p.308). 경향이지 기준이 아님을 주석에"),
    ("3.4.2", "라사", "열용흔 3 — 넓고 거침, 흘러내림·물방울, 장력 방향 신장", DONE,
     "WideMeltWithRoughSurface, DrippingMeltFormation, StretchedThinnedEnd(p.309)"),
    ("3.4.2", "라아", "단면 관찰 — 보이드·블로우홀은 1차에 많고, 2차는 이물 혼입", DONE, "voidFraction, ForeignMatterInclusion(p.309)"),
    ("3.4.2", "라자", "단면조직 — 1차 미세 공정조직, 2차 큰 보이드·산화제일구리 초기결정·그을음", PART,
     "fineDendriticGrain·voidFraction 은 보강 근거로만(CLAUDE.md). 산화구리 결정·그을음 혼입은 어휘 없음"),
    # 3.4.5
    ("3.4.5", "가", "외부화염 — 경계 명확, 밖→안 탄화, 2차 합선", DONE,
     "CarbonizationFromInsideOut 의 부정(R_EF_ref4), SecondaryArcMark(R_EF_sup3)"),
    ("3.4.5", "나", "동전선 온도별 표면 변화(300~1,100℃)", OUT,
     "주변 온도 추정용 사진 자료. 온도 이력을 담을 자리가 없다(§9.9.4.5.1 과 같은 판정)"),
    ("3.4.5", "다", "용흔을 찾는 목적 — 출화부 축소", OUT, "발화지점 특정(설계계획서 1.1)"),
]

# NONE 에서 나온 후보. 붙이기 전에 CLAUDE.md 의 질문 둘을 거친다.
# (번호, 이름, 원문이 말하는 것, 출처 쪽, 온톨로지에서의 자리)
CANDIDATES = [
    ("①", "극별 용융 위치", "한 극만 용융 → 접촉부 과열(접촉불량)·반단선·지락, 양극 용융 → 트래킹",
     "p.185 ①·⑦㉰·⑧", "DamagePattern 두 클래스와 규칙. 대상 슬롯(플러그·기판)과 결합. 화재 자체가 한 극만 녹이는가를 먼저 묻는다"),
    ("②", "납땜 불량·균열", "기판 납땜부 접촉저항 증가·크랙 방전",
     "p.185 ⑧, p.222 다㉱, p.237 5)", "ConnectionCondition 하위. 접촉불량의 자리가 기판이면 이것"),
    ("③", "탄화도전로 도통·저항(수Ω~수십Ω)", "트래킹 탄화부를 회로시험기로 재면 도통한다",
     "p.243 (바), p.251 (5), p.272 ③, p.299 (3)", "CarbonizedConductivePath 의 계측 확인. InsulationResistanceObservation 과 같은 꼴"),
    ("④", "쥐 갉음 → 반단선", "히터선을 갉아 반단선",
     "p.286 5)", "RodentGnawing 을 PartialDisconnectionScenario 에도 잇는다. cause_audit EXCL → SHARED. 정확도는 내려갈 수 있다"),
    ("⑤", "금속 개입 단락·꼬아 접속의 차단기 미동작", "접촉저항이 커서 순간 트립하지 않는다",
     "p.285 (3), p.286 (3)", "R_CD_ref(NoTripDespiteExternalForce)가 이 경우를 반증으로 오독할 수 있다. make refute 로 반례를 센 뒤 결정"),
    ("⑥", "니크롬선 용융", "1,425℃ 는 화재열로 닿지 않는다",
     "p.293 라)", "외부화염 반증 또는 F-3 착화 역량. 히터가 있는 사례에서만"),
    ("⑦", "통전 입증 단서", "칼날 광택·변색 경계, 칼날받이 열림, 필라멘트 앵커 용착",
     "p.178~179, p.214", "EnergizedState 지지 규칙이 먼저(gaps.py). 그다음 이 단서들이 그것을 세운다"),
]


def counts():
    n = Counter(s[3] for s in SECTIONS)
    inscope = len(SECTIONS) - n[OUT] - n[PROC]
    return n, inscope


def sub_counts():
    n = Counter(s[3] for s in SUBSECTIONS)
    inscope = len(SUBSECTIONS) - n[OUT] - n[PROC]
    return n, inscope


def gaps():
    return [s for s in SECTIONS if s[3] in (NONE, PART)] + [s for s in SUBSECTIONS if s[3] in (NONE, PART)]


MARK = {DONE: "■", PART: "◐", NONE: "□", OUT: "·", PROC: "×"}


def _chapter(sec):
    return sec if sec.startswith("3.") and sec[:3] in CH else sec.split(".")[0]


if __name__ == "__main__":
    n, ins = counts()
    print(f"화재조사실무Ⅳ(2025) 제2편 전기화재감식 — 절 {len(SECTIONS)}개, 범위 내 {ins}개\n")
    print(f"  구현 {n[DONE]}   일부 {n[PART]}   없음 {n[NONE]}   범위밖 {n[OUT]}   현장절차 {n[PROC]}")
    print(f"  이식률 {n[DONE]}/{ins} = {n[DONE] / ins * 100:.0f}%")
    sn, sins = sub_counts()
    print(f"\n  하위 절 {len(SUBSECTIONS)}개, 범위 내 {sins}개 — 구현 {sn[DONE]}  일부 {sn[PART]}  없음 {sn[NONE]}"
          f"  범위밖 {sn[OUT]}  현장절차 {sn[PROC]}")
    print(f"  이식률 {sn[DONE]}/{sins} = {sn[DONE] / sins * 100:.0f}%\n")

    ch = None
    for sec, pg, title, st, note in SECTIONS:
        c = _chapter(sec)[:3] if sec.startswith("3.") else sec.split(".")[0]
        if c != ch:
            ch = c
            print(f"\n── {CH[c]} " + "─" * max(0, 52 - len(CH[c])))
        print(f"  {MARK[st]} {sec:6s} p.{pg:<3d} {title[:36]:36s} {st}")
        if st in (NONE, PART):
            for i in range(0, len(note), 74):
                print(f"           {note[i:i + 74]}")

    print("\n\n── 하위 절까지 내려간 절 " + "─" * 44)
    order = [s[0] for s in SECTIONS]
    for p_ in sorted({x[0] for x in SUBSECTIONS}, key=order.index):
        rows = [x for x in SUBSECTIONS if x[0] == p_]
        k = Counter(x[3] for x in rows)
        m = len(rows) - k[PROC] - k[OUT]
        rate = f"{k[DONE]}/{m} = {k[DONE] / m * 100:.0f}%" if m else "대상 없음"
        title = next(s[2] for s in SECTIONS if s[0] == p_)
        print(f"\n  §{p_} {title[:28]}  온톨로지 대상 {m}개 / 현장 절차 {k[PROC]}개 / 범위밖 {k[OUT]}개 — 이식률 {rate}")
        for sec, sub, t, st, note in rows:
            print(f"    {MARK[st]} {sub:7s} {t[:44]:44s} {st}")
            if st in (NONE, PART):
                for i in range(0, len(note), 70):
                    print(f"              {note[i:i + 70]}")

    print("\n\n── 없음에서 나온 후보 — 붙이기 전에 두 질문을 거친다 " + "─" * 16)
    for no, name, says, src, place in CANDIDATES:
        print(f"\n  {no} {name}  ({src})")
        print(f"     원문: {says}")
        print(f"     자리: {place}")
