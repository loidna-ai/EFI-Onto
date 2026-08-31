# EFI-Onto

전기화재 발화 메커니즘 판정 온톨로지. FIReAct 논문(NFPA 921 절차 기반 전기화재 감식 지원 AI 에이전트)의
감별 절차를 OWL 2 DL + SHACL 로 정형화한 것.

## 이 프로젝트가 하는 일

사진에서 읽은 형태학적 특징과 현장에서 확인한 사실을 **서로 다른 존재론 범주에 두고**, 둘이 섞이지 않은 채로
대조되게 한다. 그래서 "사진만으로는 못 가르는 지대"가 구조적으로 드러난다.

## 명령

```bash
make install     # 의존성 설치
make test        # 온톨로지 정합성 검사 (SHACL + Pydantic 양쪽)
make build       # 시각화·검토표 전부 생성 → build/
make review      # 조사관 검토용 xlsx 만 생성
make clean
```

## 구조

```
ontology/efi_tbox.ttl    TBox 본체. 클래스 125, 속성 27+33, 단서 규칙 25, SHACL 11
src/efi_schema.py        Pydantic v2 추론 파이프라인. TTL 을 읽어 세션 단위로 실행
scripts/score.py         가감점 산출. 가중치의 단일 진실 원천
scripts/                 시각화·내보내기 (그래프 HTML, GraphML, SVG, 검토표 xlsx)
tests/test_ontology.py   회귀 시험. TTL 을 고치면 반드시 통과해야 함
docs/                    설계계획서 (Noy & McGuinness 7단계)
build/                   생성물. git 에 넣지 않음
```

## 설계 원칙 — 고치기 전에 읽을 것

| | 원칙 | 이유 |
|---|---|---|
| P1 | 4축(발열 메커니즘·물리 증거물·선행 조건·착화물)을 BFO 최상위 범주로 분리 | 형태학적 특징과 현장 지표가 한 칸에 섞이면 추론이 무너진다 |
| P2 | 판독 결과는 결론(Conclusion)이 아니라 가설(IgnitionScenario) | 논문의 핵심 명제 |
| P3 | 반증을 점수보다 먼저 실행 (sh:order) | 점수를 먼저 매기면 기각됐어야 할 가설이 점수를 갖는다 |
| P4 | '확인 불가'는 반증 근거가 될 수 없다 | 결측과 부정 응답의 구분 (논문 3.2) |
| P5 | 모든 사실에 확인 상태 + 출처(PROV-O) | 추적 가능성 |

**가설은 메커니즘으로 정의(owl:equivalentClass), 선행 조건은 필요조건(rdfs:subClassOf)으로만 붙인다.**
오염 환경이 있다고 트래킹인 것은 아니지만, 오염 환경 없이 트래킹일 수는 없다.

**1차·2차 단락흔은 형태가 아니라 시간 선후로 판정한다** (OWL-Time, `ArcEvent time:before FireExposureEvent`).
공극률·결정립은 보강 근거로만 쓴다.

**단서(Table 2)는 클래스 정의가 아니라 `IndicatorRule` 인스턴스로 물화한다.**
루브릭이 바뀌면 규칙 인스턴스만 갈아 끼우고 클래스 정의는 건드리지 않는다.

## SHACL 규칙과 제약

| | 이름 | 하는 일 |
|---|---|---|
| M-1 | MorphologyDiscriminationRuleShape | 손상 양상별 변별력 산출 (몇 개 가설이 남기는가) |
| M-2 | MorphologicalAmbiguityRuleShape | 양상 2개 이상 공유하는 가설 쌍 = 형태학적 혼동 쌍 |
| M-3 | DerivedManifestationRuleShape | 선언된 canManifest 를 메커니즘의 producesDamage 와 대조 |
| F-1 | FalsificationRuleShape | 반증 우선. 비통전 확인은 −100 즉시 기각 |
| F-2 | ArcMarkSequenceRuleShape | 1차/2차 아크흔 판정 |
| F-3 | IgnitionCompetenceRuleShape | 착화 역량 (도달 온도 < 발화 온도 → 약화) |
| F-4 | SupportScoreRuleShape | 50 + Σ가감점, 0~100 클램프 |
| C-1 | RefutationEvidenceShape | 반증은 Confirmed/ConfirmedAbsent 만 |
| C-2 | ConclusionShape | 소거만으로 확정 불가 (negative corpus 배제) |
| C-3 | ScenarioShape | 가설 하나에 메커니즘 하나 |
| C-4 | FactShape | 모든 사실에 상태 + 출처 |
| C-5 | MorphologyOnlyConclusionShape | 공유 형태만으로 확정 불가 (논문 4.2) |

## 코딩 규칙

- 미사여구·불필요한 주석 없이 간결하게. `/mnt/skills/user/terse-coder` 스타일.
- `supportScore` 는 xsd:integer, **퍼센트 기호를 붙이지 않는다** (논문 3.2). 확률이 아니다.
- **`scoreDelta` 를 TTL 에서 직접 고치지 않는다.** `python scripts/score.py --write` 로 다시 만든다.
  손으로 고치면 `test_score_deltas_are_derived` 가 잡는다.
- TTL 을 고치면 `make test` 를 돌린다. M-3 불일치가 0이 아니면 커밋하지 않는다.
- 한 줄에 한 주어만 쓴다 (Turtle 다중 주어는 파싱 사고의 원인이었다).
- SPARQL 에서 `owl:unionOf` 는 순회되지 않는다. 하위 클래스는 `rdfs:subClassOf` 로 명시할 것.

## 검증되지 않은 것 — 건드릴 때 주의

1. **`scoreDelta` 는 손으로 고치지 않는다.** `scripts/score.py` 가 변별력에서 유도한다.
   척도(지지 15 / 반증 30)는 확정 조건에서 풀려나온 값이고, 형태학적 감쇠 0.7 만 판단이다.
   **아직 사례로 보정되지 않았다** — ABox 150건이 들어오면 조건부 빈도로 검증해야 한다.
2. **NFPA 921 조항 번호 미대조.** 현재 장(Ch.4/9/19) 수준 표기. 2024판 원문 확인 필요.
3. **`canManifest` / `enables` / `producesDamage` / `ignites` / `exhibits` / `attests` 는 작성자 구성이다.**
   Table 1·2 와 선행연구를 근거로 했으나 실무 검증 전. `build/EFI-Onto_검토표.xlsx` 로 조사관 검토 진행 중.
4. **ABox 없음.** 조사서 사례가 하나도 들어 있지 않다. 150건 변환이 다음 과제.

## 출처 구분 — 논문·발표에서 뭉뚱그리지 말 것

| 부분 | 근거 |
|---|---|
| 가설수립→검증→확정 3단계, 반증 우선, negative corpus 배제, 판단보류 허용 | NFPA 921 |
| 5대 발화 요인 구분, Table 2 단서 | 국내 실무·선행연구 + FIReAct 논문 |
| 형태 발현 프로파일, 축 간 인과 연결 | 작성자 구성 (검증 필요) |
| 가감점 | 변별력에서 유도 (`scripts/score.py`). 사례 보정 전 |
