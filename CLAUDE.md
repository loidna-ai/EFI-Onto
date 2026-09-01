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
make status      # 현재 규모·이식률·래칫을 한 화면에
make reason      # OWL 2 DL 일관성 검사 (HermiT). Java 필요
make lint        # 구조 점검 — 사슬에 붙지 않은 어휘 찾기
make review      # 조사관 검토용 xlsx 만 생성
make clean
```

## 구조

```
ontology/efi_tbox.ttl        TBox 본체 (규모는 make status)
src/efi_schema.py            Pydantic 파이프라인. 점수 산출과 질의 선택
scripts/score.py             가감점 산출. 가중치의 단일 진실 원천
scripts/nfpa.py              NFPA 921 절 대조표. 이식률의 분모
scripts/audit.py             형태 발현 편향 점검. '화재도 이 흔적을 내는가'
scripts/cause_audit.py       선행 조건 편향 점검. '정말 그 요인에서만 일어나는가'
scripts/lint.py              구조 점검. 어휘가 사슬에 붙어 있는가
scripts/status.py            현재 상태 요약
scripts/consistency.py       OWL 2 DL 일관성 검사 (HermiT 직접 호출)
scripts/{extract,build,graph,review,export}.py   시각화·검토표
tests/test_ontology.py       정합성 불변식. 깨지면 안 되는 것
tests/test_completeness.py   완성도 래칫. 얼마나 남았는가
docs/                        설계계획서 + 변경 이력
build/                       생성물. git 에 넣지 않음
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

접두어가 종류를 뜻한다. **개별 목록은 `make status` 와 TTL 의 절 주석을 보라 — 여기 적으면 낡는다.**

| 접두어 | 하는 일 | 예 |
|---|---|---|
| M | 형태 발현에서 변별력·혼동 쌍을 산출 | M-1 변별력, M-2 혼동 쌍, M-3 메커니즘 근거 대조 |
| F | 판정 규칙. 반증이 점수보다 먼저 (`sh:order`) | F-1 반증 우선, F-2 아크흔 선후, F-3 착화 역량, F-4 점수, F-5 아크흔 부재 |
| C | 결론이 서지 못하게 막는 제약 | C-2 소거법 금지, C-5 공유 형태 금지, C-23 부재 위 가설 금지 |
| D | 정의로 도출되는 사실. 임계값이 아니라 관계 비교 | D-1 과부하, D-4 대응 손상, D-7 원인미상 |

**모든 명명 도형은 NFPA 921 조항에 닿아야 한다** (`test_every_shape_cites_nfpa`).
닿지 않으면 우리가 지어낸 절차라는 뜻이므로 그 사실이 드러나야 한다.
반대로 **지표 규칙에는 조항을 붙이지 않는다** — Table 2 는 국내 실무 출처다.

## 어디까지가 SHACL 이고 어디까지가 Python 인가

| | 맡는 것 | 이유 |
|---|---|---|
| `src/efi_schema.py` | 가감점 산출, 변별 질의 선택, 세션 상태 | 대화 루프에서 매 턴 돌아야 해서 가볍다 |
| SHACL (`pySHACL`) | 결론 검증 전체 | 확정 시점에 한 번만 돌면 되고 규칙이 많다 |

**결론 제약을 Python 으로 옮겨 적지 않는다.** 두 번 적으면 반드시 갈라진다 —
실제로 갈라졌었다. `Session.validate()` 가 pySHACL 을 호출해 위임한다.

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
2. **NFPA 921 조항 대조 진행 중.** `scripts/nfpa.py` 가 절별 상태를 들고 있다.
   원문을 받은 절만 하위 절까지 내려가 있고 나머지는 절 제목 수준의 근사치다.
   **내려갈 때마다 이식률은 대체로 낮아진다** — 제목으로는 덮인 듯 보이던 요건이 드러나기 때문이다.
   낮아진 숫자가 정확한 숫자다.
3. **인과 사슬(`canManifest`·`enables`·`producesDamage`·`ignites`·`exhibits`·`attests`)은 작성자 구성이다.**
   일부는 원문 대조로 교정됐다. `build/EFI-Onto_검토표.xlsx` 로 조사관 검토 진행 중.

   **알려진 편향** — 이 온톨로지는 '이 가설이 이 흔적을 낸다'는 방향으로만 지어져,
   화재 자체가 만드는 흔적을 전기적 원인의 전용 단서로 오인했다. 원문 대조에서 여섯 건이 나왔다
   (탄화 도전로, 다발성 아크 비드, 아크흔·비드, 국부 변색, 광택 소실, 소손 중심 표면 집중).
   미검토는 0건이 됐고 `test_every_morphology_answers_the_fire_question` 이 불변식으로 못을 박는다.
   `scripts/audit.py` 가 세고 `test_fire_producibility_declarations_agree` 가 선언과의 어긋남을 막는다.

   마지막 한 건이 닫히면서 **트래킹에는 전용 형태 단서가 하나도 남지 않았다.** 그래서 트래킹을
   세우려면 비시각적 현장 사실(오염 환경)이 반드시 있어야 한다 — C-5 가 요구하던 그것이다.

   **새 형태 발현을 선언할 때 반드시 물을 것: 이 흔적을 화재 자체가 낼 수 있는가?**

   같은 편향이 **원인 축에도 있었다.** 원문이 'A도 되고 B도 된다'고 적은 것을 A 쪽으로만 이었다
   (진동을 반단선 전용으로, 플러그 접속부를 반단선 전용으로, 먼지·습기를 트래킹 전용으로).
   `scripts/cause_audit.py` 가 한 가설에만 연결된 선행 조건을 세고
   `test_cause_chain_declarations_agree` 가 판정과 사슬의 어긋남을 막는다.

   **새 선행 조건을 한 가설에만 이을 때 반드시 물을 것: 정말 그 요인에서만 일어나는가?**

   **어휘만 만들고 사슬에 붙이지 않는 실패가 반복됐다.** ArcMapPoint, downstreamIndex,
   outcomeUndetermined 가 그랬다. 선언만 하면 확인해도 판정에 기여하지 못한다.
   `make lint` 가 센다. 새 클래스·속성을 만들면 그 자리에서 사슬에 붙인다.
4. **ABox 없음.** 조사서 사례가 하나도 들어 있지 않다. 150건 변환이 다음 과제.
   지금까지 잰 것은 전부 **이식률**이다. **정확도는 한 번도 재지 않았다.**
5. **DL 일관성(V1)은 통과했다.** `make reason` 으로 HermiT 을 돌린다. Java 와 owlready2 가 필요하다.
   pySHACL 은 DL 일관성을 보지 않으므로 이 검사 없이는 불만족 클래스가 생겨도 다른 시험이 전부 통과한다.
   검사기 자체의 반증 대조 시험(`test_consistency_checker_actually_detects`)을 함께 둔다 —
   한 번 거짓 통과를 냈던 적이 있다.

## 출처 구분 — 논문·발표에서 뭉뚱그리지 말 것

| 부분 | 근거 |
|---|---|
| 가설수립→검증→확정 3단계, 반증 우선, negative corpus 배제, 판단보류 허용 | NFPA 921 |
| 5대 발화 요인 구분, Table 2 단서 | 국내 실무·선행연구 + FIReAct 논문 |
| 형태 발현 프로파일, 축 간 인과 연결 | 작성자 구성. 일부 원문 대조로 교정됨 |
| 퓨즈 용단 형태, 용흔 위치, 반단선 10% 정의, 아산화동 감식, 자체 발화 판정 | 소방청 화재조사실무Ⅳ(2025) 제2편. TTL 32·33절, 클래스 주석에 쪽수 |
| 방법론 층 제약 (M·F·C·D 도형) | NFPA 921 조항에 대조됨 (`dcterms:references`) |
| 가감점 | 변별력에서 유도 (`scripts/score.py`). 사례 보정 전 |
