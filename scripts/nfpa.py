# -*- coding: utf-8 -*-
"""NFPA 921 (2024) 절 대조표. 이식이 얼마나 남았는지의 분모를 만든다.

절 목록은 2024판 목차(절 수준)에서 옮긴 것이다. 하위 절 번호는 아직 없다.
상태는 '우리 그래프가 그 절의 내용을 다루는가'이며, 절 제목만으로 판정 가능한
것과 본문 확인이 필요한 것을 구분해 둔다.

주의 — 단서 규칙 25개(Table 2)는 NFPA 가 아니라 국내 실무·선행연구에서 왔다.
여기에 조항을 붙이면 출처가 왜곡된다. 조항은 방법론 층에만 붙인다.
"""
import sys, pathlib

DONE, PART, NONE, OUT, PROC = "구현", "일부", "없음", "범위밖", "현장절차"
# PROC = 이론에는 있으나 온톨로지가 표현할 대상이 아닌 것(도체 취급·촬영·표식 등
#        현장 작업 절차). 분모에서 뺀다. 빼지 않으면 100%는 도달 불가가 되고
#        그 순간 이 지표는 무시된다.

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
    ("9.1",  "Introduction",                         PART, "배경"),
    ("9.2",  "Basic Electricity",                    PART, "전기량 데이터 속성 일부"),
    ("9.3",  "Building Electrical Systems",          PART, "§9.3.4 인입구 무보호 구간을 구현. 전압·인입 방식·"
                                                           "계량기는 판정에 쓰이지 않아 넣지 않았다(판단)"),
    ("9.4",  "Service Equipment",                    PART, "ServiceEquipment 클래스. 세 기능 중 보호 기능만 판정에 연결"),
    ("9.5",  "Grounding",                            DONE, "본딩 경로와 중성선 단선. C-21 로 잘못된 추론을 막는다"),
    ("9.6",  "Overcurrent Protection",               PART, "BreakerTripRecord, D-1 과부하, GFCI·AFCI 클래스. 동작 특성은 없음"),
    ("9.7",  "Branch Circuits",                      PART, "Circuit·BranchCircuit 클래스는 생겼다. 계통 위상은 없음"),
    ("9.8",  "Outlets and Devices",                  PART, "PlugReceptacle, TerminalBlock"),
    ("9.9",  "Ignition by Electrical Energy",        DONE, "HeatingMechanism 축. 이 프로젝트의 중심"),
    ("9.10", "Interpreting Damage to Elec. Systems", DONE, "DamagePattern 축, M-1~M-3"),
    ("9.11", "Identification of Damaged Conductors", DONE, "1차/2차 단락흔, F-2"),
    ("9.12", "Electrical System Examination",        PART, "증거물 수거·관측은 있으나 검사 절차는 없음"),
    ("9.13", "Arc Surveys",                          DONE, "F-5, C-6~C-8, D-4~D-5 로 구현. 하위 절 표 참조"),
    ("9.14", "Static Electricity",                   OUT,  "5대 요인 밖. 범위 제외 (재검토 여지)"),
    ("9.15", "Batteries",                            OUT,  "5대 요인 밖. ESS·리튬 화재를 넣을지 결정 필요"),
    # ── Chapter 19 Fire Cause Determination ────────────────────────────────
    ("19.1", "Introduction",                         PART, "배경"),
    ("19.2", "Overall Methodology",                  DONE, "세션 절차"),
    ("19.3", "Data Collection",                      DONE, "Fact, ConfirmationStatus, PROV-O (C-4)"),
    ("19.4", "Analyze the Data",                     DONE, "M-1~M-3 변별력·혼동 쌍 산출"),
    ("19.5", "Developing Cause Hypotheses",          DONE, "IgnitionScenario 생성, P2"),
    ("19.6", "Testing the Hypothesis for Validity",  DONE, "F-1~F-4. 가장 강한 부분"),
    ("19.7", "Selecting the Final Hypothesis",       DONE, "Conclusion, C-2, 확정 조건"),
    ("19.8", "Fire Incident and Cause Classification", PART, "분류 구조는 구현(C-9~C-11). 범주 목록은 "
                                                             "이 온톨로지가 정하지 않고 외부 체계를 참조한다"),
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
    ("9.13.1.2", "조사 미완이면 결론은 조사 범위로 제한",   DONE, "C-7 ArcSurveyScopeShape"),
    ("9.13.1.3", "아크인지 다른 손상인지 금속조직 판정",     PART, "MaterialsAnalyst 행위자는 생겼다. 판정 규칙은 없음"),
    ("9.13.2.1", "회로 최하류 아크 지점 기록",             DONE, "D-5 FurthestDownstreamRuleShape"),
    ("9.13.2.2", "회로별 보호장치 종류와 상태 기록",        PART, "GFCI·AFCI 클래스와 circuitProtection. 상태 열거는 없음"),
    ("9.13.3.1", "아크 지점이 나타날 수 있는 위치",         PART, "도체·접속부는 있으나 전선관·접지면은 없다"),
    ("9.13.3.2", "전선관 내 도체 인출과 방향 유지",         PROC, "현장 작업 절차"),
    ("9.13.3.3", "전 둘레 육안·촉진 검사",                 PROC, "현장 작업 절차"),
    ("9.13.3.4", "원상 기록 후 피복 제거",                 PROC, "현장 작업 절차"),
    ("9.13.3.5", "현장 검사와 실험실 반출 선택",           PROC, "현장 작업 절차"),
    ("9.13.4.2", "전위가 다른 쪽 대응 손상 확인",           DONE, "D-4 CorrespondingDamageRuleShape"),
    ("9.13.4.3", "아크 지점 표식과 사진 기록",             PROC, "현장 작업 절차"),
    ("9.13.4.5", "아크 용융 부재도 기록 — 미조사와 구분",    DONE, "F-5 ArcSiteAbsenceRuleShape"),
    ("9.13.4.6", "용융이 아크 지점을 지웠을 가능성",         DONE, "F-5 + C-6 ObscuredArcSiteShape"),
    ("9.13.4.7", "아크 용융흔 단독은 통전 사실만 말한다",     DONE, "C-8 ArcMeltAloneShape"),
    ("4.1.0",    "발화 지점을 먼저, 그다음 원인",            OUT,  "발화 지점 특정은 이 프로젝트 범위 밖(설계계획서 1.1)"),
    ("4.3.1",    "문제 인식 — 무엇을 물을 것인가",           PART, "InvestigationSession 은 있으나 문제 진술 칸이 없다"),
    ("4.3.2",    "문제 정의 — 어떻게 풀 것인가",            PART, "질의·관측 경로는 있으나 조사 설계 표현은 없다"),
    ("4.3.3",    "자료 수집 — 검증 가능한 경험적 자료",       DONE, "Fact, ConfirmationStatus, SOSA·PROV (C-4)"),
    ("4.3.4",    "자료 분석 — 수집·목록화는 분석이 아니다",    DONE, "C-26 DataAnalyzedShape"),
    ("4.3.5",    "가설 수립(귀납) — 경험적 자료에서만",       DONE, "IgnitionScenario, P2"),
    ("4.3.6",    "가설 검증(연역) — 반증을 설계한다",         DONE, "F-1, C-25 UndeterminedOutcome, D-7"),
    ("4.3.6.1",  "시험 불가능한 가설은 무효다",              DONE, "C-23 UntestableHypothesisShape"),
    ("4.3.7",    "최종 가설 선택 — 대안 미고려는 중대 오류",   DONE, "C-24 AllHypothesesTestedShape, C-2"),
    ("4.3.8",    "예단 금지 — 자료 전에 가설 없다",          DONE, "C-27 NoPresumptionShape"),
    ("4.3.9",    "기대 편향",                            NONE, "편향을 표시하거나 검출할 자리가 없다"),
    ("4.3.10",   "확증 편향 — 같은 자료가 반대 가설도 지지",   PART, "M-2 혼동 쌍과 C-5 가 형태 쪽만 덮는다"),
    ("4.5.0",    "의견은 자료와 한계를 밝혀야 한다",          PART, "C-15 한계 명시. 과학적 방법 적용 서술은 §4.7 보고서 영역"),
    ("4.5.1.1",  "개연·가능 두 표현. 대등하면 가능까지",       DONE, "CertaintyLevel, C-12 EqualLikelihoodShape"),
    ("4.5.1.2",  "의심은 전문가 의견이 아니다",              DONE, "C-13 SuspectedNotOpinion, C-14 CertaintyStated"),
    ("4.5.2",    "유일하고 신뢰할 수 있는 최종 가설",         DONE, "C-16 UniqueFinalHypothesisShape"),
    ("4.6.1",    "행정 검토 — 절차와 서류 구비",             DONE, "AdministrativeReview"),
    ("4.6.1.1",  "행정 검토는 실질 비평을 못 한다",           DONE, "C-18 AdministrativeReviewScopeShape"),
    ("4.6.2",    "기술 검토 — 자격과 자료 접근이 전제",        PART, "C-19 자료 접근. 검토 범위별 자격 대조는 없음"),
    ("4.6.2.1",  "기술 검토의 확증 편향 위험",               NONE, "편향 위험을 표시할 자리가 없다"),
    ("4.6.3",    "동료 검토 — 독립성·객관성",               DONE, "C-17 PeerReviewIndependenceShape"),
    ("4.6.3.2",  "동료 검토는 자료 오류를 잡지 못한다",        DONE, "C-20 ReviewValidationShape"),
    ("19.8.1",   "통계 목적 사건 분류 — 외부 체계 참조",      DONE, "C-10 ClassificationSystemShape, ClassificationSystem 6종"),
    ("19.8.2",   "보고서용 원인 분류 — 판정 이후에 온다",     PART, "C-9 순서, C-11 분리는 구현. 범주 목록 미확보(원문 후속 필요)"),
]

# 방법론 층에만 붙인다. 단서 규칙(Table 2)은 국내 실무 출처이므로 제외.
SHAPE_REFS = {
    "FalsificationRuleShape":            ["4.3", "19.6"],
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
