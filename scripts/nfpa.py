# -*- coding: utf-8 -*-
"""NFPA 921 (2024) 절 대조표. 이식이 얼마나 남았는지의 분모를 만든다.

절 목록은 2024판 목차(절 수준)에서 옮긴 것이다. 하위 절 번호는 아직 없다.
상태는 '우리 그래프가 그 절의 내용을 다루는가'이며, 절 제목만으로 판정 가능한
것과 본문 확인이 필요한 것을 구분해 둔다.

주의 — 단서 규칙 25개(Table 2)는 NFPA 가 아니라 국내 실무·선행연구에서 왔다.
여기에 조항을 붙이면 출처가 왜곡된다. 조항은 방법론 층에만 붙인다.
"""
import sys, pathlib

DONE, PART, NONE, OUT = "구현", "일부", "없음", "범위밖"

# (절, 제목, 상태, 우리 쪽 대응 또는 빠진 내용)
SECTIONS = [
    # ── Chapter 4 Basic Methodology ────────────────────────────────────────
    ("4.1",  "Nature of Fire Investigations",        PART, "P1~P5 의 전제. 명시적 모형은 없음"),
    ("4.2",  "Systematic Approach",                  DONE, "InvestigationSession 절차"),
    ("4.3",  "Relating to the Scientific Method",    DONE, "P3 반증 우선, F-1, C-2"),
    ("4.4",  "Basic Method of a Fire Investigation", DONE, "가설수립 → 검증 → 확정 3단계"),
    ("4.5",  "Expert Opinions",                      NONE, "의견 확신도(probable/possible) 개념이 없다. "
                                                           "Conclusion 에 확신 수준 칸이 없고, 누가 낼 자격이 있는지도 없다"),
    ("4.6",  "Review Procedure",                     NONE, "동료 검토 절차가 모형에 없다. 검토표는 외부 문서일 뿐"),
    ("4.7",  "Reporting Procedure",                  NONE, "보고서 구조가 없다. PROV 경로는 있으나 보고서 자체는 미모형"),
    # ── Chapter 9 Electricity and Fire ─────────────────────────────────────
    ("9.1",  "Introduction",                         PART, "배경"),
    ("9.2",  "Basic Electricity",                    PART, "전기량 데이터 속성 일부"),
    ("9.3",  "Building Electrical Systems",          NONE, "배선 계통 구조가 없다"),
    ("9.4",  "Service Equipment",                    NONE, "인입 설비가 없다"),
    ("9.5",  "Grounding",                            NONE, "접지·지락 경로가 없다. 누전은 트래킹 쪽에만 걸쳐 있다"),
    ("9.6",  "Overcurrent Protection",               PART, "BreakerTripRecord, D-1 과부하. 보호기기 동작 특성은 없음"),
    ("9.7",  "Branch Circuits",                      NONE, "분기회로 개념이 없다"),
    ("9.8",  "Outlets and Devices",                  PART, "PlugReceptacle, TerminalBlock"),
    ("9.9",  "Ignition by Electrical Energy",        DONE, "HeatingMechanism 축. 이 프로젝트의 중심"),
    ("9.10", "Interpreting Damage to Elec. Systems", DONE, "DamagePattern 축, M-1~M-3"),
    ("9.11", "Identification of Damaged Conductors", DONE, "1차/2차 단락흔, F-2"),
    ("9.12", "Electrical System Examination",        PART, "증거물 수거·관측은 있으나 검사 절차는 없음"),
    ("9.13", "Arc Surveys",                          PART, "ArcMapPoint 클래스와 locatedInOriginArea 속성은 있으나 "
                                                           "이를 쓰는 규칙이 하나도 없다. 어휘만 있고 절차가 없다"),
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
    ("19.8", "Fire Incident and Cause Classification", NONE, "화재 분류(사고·방화·자연·원인미상)가 없다. "
                                                             "Withheld 는 가설 판정일 뿐 사건 분류가 아니다"),
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
}


def counts():
    from collections import Counter
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
