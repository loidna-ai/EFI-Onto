# 전기화재 발화 메커니즘 판정 온톨로지 (EFI-Onto) — TBox 설계 계획서 및 스키마 명세

**Stanford 『Ontology Development 101』(Noy & McGuinness, KSL-01-05) 7단계 준수 · FIReAct 6.1절(지식 그래프 + RAG) 후속 과제 연계**

---

## 0. 설계 개요

### 0.1 문서 목적

FIReAct 논문 6.1절은 NFPA 921과 국내 실무 기준을 **온톨로지 기반 지식 그래프**로 정형화하고 RAG와 결합해 감별 추론의 일관성·근거성을 강화할 것을 제언한다. 본 문서는 그 첫 단계인 **TBox(스키마 층)** 설계를 다룬다. 실험에서 확인된 두 구조적 혼동 쌍(절연열화↔압착손상, 트래킹↔접촉불량)을 가르는 비시각적 변별 축을 클래스·속성·공리로 고정하고, 소거법 오류를 막는 반증 규칙을 기계 가독 형태로 남기는 것이 목표다.

### 0.2 온톨로지 프로파일

| 항목 | 내용 |
|---|---|
| 명칭 · 접두어 | EFI-Onto (Electrical Fire Ignition Ontology) · `efi:` |
| 네임스페이스 | `https://w3id.org/efi-onto#` (제안; w3id 영구 식별자 등록 전제) |
| 표현 언어 | OWL 2 DL (Turtle 직렬화) + SHACL Advanced Features(규칙·검증) + SKOS(용어 정렬) |
| 추론기 | HermiT/Pellet (DL 일관성·분류) · pySHACL `advanced=True` (반증 규칙·확정 조건) |
| 상위 온톨로지 | BFO 2.0 (ISO/IEC 21838-2) · RO · SOSA/SSN · PROV-O · OWL-Time · QUDT |
| 연계 대상 | FIReAct 세션 레지스트리(3.2절) · 절차적 지지점수 루브릭 · RAG 검색 키 · 폐쇄망 SLM 지식 증류 데이터 스키마(6.2절) |
| 범위 판정 대상 | 접촉불량 · 압착손상 · 반단선 · 절연열화 · 트래킹 (+ 외부화염 반증 범주) 및 1차·2차 단락흔 구분 |

### 0.3 방법론 단계 대응

| Stanford 101 원 단계 | 본 계획서 적용 | 산출물 |
|---|---|---|
| 1. Determine domain and scope | Step 1 범위 · 역량 질문 5개 | CQ 표, 포함/제외 표 |
| 2. Consider reusing existing ontologies | Step 2 표준 온톨로지 재사용 포인트 | 정렬 표 |
| 3. Enumerate important terms | Step 3 핵심 용어 목록 | 축별 용어 표 |
| 4. Define classes and class hierarchy | Step 4 Middle-out 계층 (4대 축 + 보조 축) | 텍스트 트리 |
| 5. Define properties of classes (slots) | Step 5 객체·데이터 속성 | Domain/Range/Datatype 표 |
| 6. Define facets of slots | Step 6 제약·공리 (반증 규칙 포함) | DL 공리 · SHACL 규칙 표 |
| 7. Create instances | Step 7 코드 산출 (TBox Turtle + Pydantic; 인스턴스는 세션 레지스트리가 생성) | `efi_tbox.ttl`, `efi_schema.py` |

### 0.4 설계 원칙

| ID | 원칙 | 논문 근거 | 온톨로지에서의 구현 |
|---|---|---|---|
| P1 | **4축 분리** — 발열메커니즘 / 물리증거물 / 선행조건 / 착화물을 서로 배타적인 상위 클래스로 둔다 | Table 1의 '형태학적 특징'(시각)과 '현장 추론 지표'(비시각)를 섞지 않음 | `owl:AllDisjointClasses` |
| P2 | **판독 결과 = 가설** — VLM 판독은 `IgnitionScenario` 인스턴스(가설)로 등록되며, `Conclusion`은 별도 클래스 | 1.2절, 7절 | `efi:IgnitionScenario` ≠ `efi:Conclusion` |
| P3 | **반증 우선(Falsification-first)** — 지지점수 합산보다 기각 규칙이 먼저 실행 | 3.2절 "물리적으로 결정적인 사실은 기각 수준으로 조정" | SHACL 규칙 `sh:order` 1 → 4 |
| P4 | **결측 ≠ 확인 불가 ≠ 부정 확인** — 세 상태를 열거형으로 구분하고, '확인 불가'는 반증 근거로 쓰지 않는다 | 3.2절 "'확인 불가'로 보존하여 결측과 부정 응답을 구분" | `efi:ConfirmationStatus` (4값) + 제약 C-1 |
| P5 | **출처 추적** — 모든 사실·판정은 행위자(조사관/AI/계측기)와 활동에 귀속 | 7절 "결론 도출 경로를 추적 가능하게" | PROV-O 정렬, 제약 C-4 |

### 0.5 산출물

| 파일 | 내용 | 검증 |
|---|---|---|
| `EFI-Onto_TBox_설계계획서.md` | 본 문서 | — |
| `efi_tbox.ttl` | OWL 2 DL TBox + 지표 규칙 인스턴스 + SHACL 규칙·제약 (약 1,160 트리플) | rdflib 파싱 · pySHACL 규칙 실행 통과 |
| `efi_schema.py` | Pydantic v2 스키마 + 규칙 로더 + 세션 엔진 (TTL을 단일 진실 원천으로 적재) | 실행 예제 통과 |

---

## Step 1. 범위 결정과 역량 질문 (Scope)

### 1.1 도메인과 범위

| 구분 | 내용 |
|---|---|
| **도메인** | 화재조사관이 최초 발화 구역을 특정한 이후, 그 구역에서 수거된 전기 증거물의 훼손 양상과 현장 사실을 대조해 전기적 발화 요인을 감별하는 절차 (논문 1.3절과 동일) |
| **포함** | ① 5대 전기적 발화 요인 + 외부화염의 시나리오 정의 ② 1차·2차 단락흔의 시공간적·형태학적 구분 근거 ③ 선행조건–메커니즘–착화물의 인과 사슬 ④ 증거의 확인 상태와 출처 ⑤ 가설 지지·기각의 규칙과 확정 조건 |
| **제외** | 발화 지점 특정 절차, 비전기적 원인, 법적 책임, 화학 성분 분석, 건축·설비 온톨로지, 개별 제품 결함 데이터베이스 |
| **사용 주체** | FIReAct 대화 엔진(변별 질의 선택·지지점수 산출), 세션 레지스트리(사실 정규화), RAG 검색기(용어 정렬), 보고서 생성기(추론 경로 재구성) |

### 1.2 역량 질문 (Competency Questions)

| ID | 역량 질문 | 답하기 위해 필요한 온톨로지 요소 | FIReAct 대응 | 검증 방법 |
|---|---|---|---|---|
| **CQ1** | 증거물 E에 관찰된 아크 용융흔이 **화재의 원인(1차)인지 결과(2차)인지** 판정하려면 어떤 시공간적 근거(발화 구역 내 위치, 아크 매핑, 통전 시점과 연소 도달 시점의 선후)와 형태학적 지표가 필요하며, 현재 확보된 것과 미확보된 것은 무엇인가? | `PrimaryArcMark`/`SecondaryArcMark`, `ArcEvent`, `FireExposureEvent`, `time:before`, `locatedInOriginArea`, `voidFraction` 등 | 가설수립(3.1) | 규칙 F-2 실행 후 `rdf:type` 추론 확인 |
| **CQ2** | 가설 H(예: 접촉불량)가 성립하려면 **어떤 선행조건이 반드시 확인**되어야 하며, 그중 현재 '확인 / 부정 확인 / 확인 불가 / 미확인' 상태인 항목은 각각 무엇인가? | 시나리오 클래스의 필요조건 공리(`hasAntecedent ⊑`), `ConfirmationStatus` | 가설검증(3.2) 감식 항목 등록 | SPARQL: 필요조건 클래스와 세션 사실의 상태 조인 |
| **CQ3** | 경합하는 두 가설 H1·H2(예: 트래킹 vs 접촉불량)에 대해, **한쪽만 예측하거나 반증하는 증거 항목**은 무엇이며, 그중 아직 확인되지 않은 항목 중 변별력이 가장 큰 것은 무엇인가? | `IndicatorRule`(forScenario, indicates, hasRole, scoreDelta) | 동적 질의 선택(3.2, 4.4) | `Session.discriminating_slots()` 출력이 Table 10 사례와 일치 |
| **CQ4** | 가설 H의 발열 메커니즘이 생성하는 열적 조건(최대 도달 온도)이 후보 착화물 F의 **발화 요건과 근접 조건**을 충족하는가? 충족하지 못하면 어느 요소가 부족한가? | `maxAttainableTemperature_C`, `ignitionTemperature_C`, `distanceToHeatSource_mm`, `ignites` | 결론확정(3.3) 보수적 판단 | 규칙 F-3 → `Weakened` 판정 |
| **CQ5** | 현재 세션에서 **어떤 가설이 어떤 확인 사실에 의해 결정적으로 기각**되었으며(예: 비통전), 최종 결론에 이르는 지지·기각 경로를 증거 → 행위자 → 활동 순으로 재구성할 수 있는가? | `refutedBy`/`supportedBy`(⊑ `prov:wasDerivedFrom`), `prov:wasAttributedTo`, `InvestigationSession` | 보고서 5개 절 중 '가설 교차검증' | PROV 경로 질의 |

### 1.3 CQ3 검증용 SPARQL 스케치

```sparql
# 두 경합 가설 ?h1 ?h2 를 가르는 미확인 지표를 변별력(|scoreDelta|) 순으로
PREFIX efi: <https://w3id.org/efi-onto#>
SELECT ?indicator ?favors (ABS(?d) AS ?power) WHERE {
  VALUES (?h1 ?h2) { (efi:TrackingScenario efi:PoorContactScenario) }
  ?r a efi:IndicatorRule ; efi:forScenario ?favors ; efi:indicates ?indicator ; efi:scoreDelta ?d .
  FILTER ( ?favors IN (?h1, ?h2) )
  FILTER NOT EXISTS { ?r2 a efi:IndicatorRule ; efi:indicates ?indicator ;
                      efi:forScenario ?other . FILTER(?other IN (?h1,?h2) && ?other != ?favors) }
  FILTER NOT EXISTS { ?s efi:hasFact ?f . ?f rdf:type/rdfs:subClassOf* ?indicator ;
                      efi:confirmationStatus ?st . FILTER(?st != efi:Missing) }
} ORDER BY DESC(?power)
```

---

## Step 2. 기존 온톨로지 재사용 (Reuse)

### 2.1 재사용 포인트

| 표준 | 재사용 요소 | EFI-Onto 매핑 | 재사용 이유 |
|---|---|---|---|
| **BFO 2.0** (ISO/IEC 21838-2) | `process`, `material entity`, `quality`, `disposition`, IAO `information content entity` | `HeatingMechanism ⊑ process` · `PhysicalEvidence ⊑ material entity` · `DamagePattern ⊑ quality` · `Ignitability ⊑ disposition` · `IgnitionScenario ⊑ ICE` | 4축을 존재론적으로 다른 범주에 두어 혼입을 원천 차단; 향후 재료·안전 온톨로지와 정렬 가능 |
| **RO** (Relations Ontology) | `inheres_in`(RO_0000052), `causally upstream of`(RO_0002411) | `exhibits ≡ inverse(inheres_in)` · `enables ⊑ causally upstream of` | 인과·의존 관계 어휘를 새로 만들지 않음 |
| **SOSA/SSN** (W3C) | `Observation`, `Sensor`, `ObservableProperty`, `FeatureOfInterest`, `hasSimpleResult` | 절연저항·온도·전류 계측과 **VLM 판독을 동일한 `Observation` 구조**로 기록; 증거물 = `FeatureOfInterest`; 조사관·AI·계측기 = `Sensor` | 계측값과 판독값의 출처·시각·단위를 같은 틀로 남겨 교차 대조(3.3절) 가능 |
| **PROV-O** (W3C) | `Entity`, `Activity`, `Agent`, `SoftwareAgent`, `wasGeneratedBy`, `wasAttributedTo`, `wasDerivedFrom` | 가설·결론·사실 = `Entity`; 세션·변별 질의 = `Activity`; 조사관 = `Agent`, AI = `SoftwareAgent`; `supportedBy`/`refutedBy ⊑ wasDerivedFrom` | 결론 도출 경로의 감사 가능성(7절) |
| **OWL-Time** | `TemporalEntity`, `before`/`after` | `ArcEvent`, `FireExposureEvent`의 선후 관계 | 1차·2차 단락흔 판정의 1차 근거를 시간 관계로 표현 |
| **QUDT** | `Unit`, `QuantityKind`, `hasQuantityKind` | MΩ · °C · A · mm² 단위 명시 | 지지점수에 %가 붙는 오류(3.2절 위반) 같은 단위 혼동 예방 |
| **SKOS** | `prefLabel`, `altLabel`, `definition`, `closeMatch` | 국문·영문·NFPA 921 용어를 한 클래스에 병기 | RAG 검색 키 및 보고서 용어 통일 |
| **SHACL** (W3C) | `NodeShape`, `SPARQLRule`, `qualifiedValueShape` | 반증 규칙 F-1~F-4, 확정 조건 C-1~C-4 | OWL의 개방세계 가정으로는 "트립 이력 **없음**" 같은 부재 사실을 처리할 수 없으므로 폐세계 검증 층이 필요 |
| SEPIO / ECO (선택) | `Assertion`, `EvidenceLine`, `supports`/`refutes` | `supportedBy`/`refutedBy`를 `skos:closeMatch`로 정렬 | 증거–주장 관계의 생의학 표준과 호환 |

### 2.2 정렬 원칙

| 원칙 | 내용 |
|---|---|
| BFO에는 `rdfs:subClassOf`만 사용 | `owl:equivalentClass`로 상위 온톨로지에 묶으면 BFO 개정 시 본 온톨로지가 함께 깨진다 |
| SOSA·PROV·Time은 직접 상속 | 도구 지원이 넓고 안정적이므로 그대로 사용 |
| SEPIO/ECO는 `skos:closeMatch` | 강제 의존을 피하고 호환만 확보 |
| 시나리오 클래스의 개체 참조는 **OWL 2 punning** | `IndicatorRule → forScenario → efi:TrackingScenario`처럼 클래스를 개체로도 참조 (OWL 2 DL 허용) |

### 2.3 미재사용 결정

| 후보 | 결정 | 사유 |
|---|---|---|
| 화재조사 전용 공개 온톨로지 | 자체 설계 | NFPA 921은 문서 표준이며 공식 온톨로지가 공개되어 있지 않음 |
| EMMO 등 재료 온톨로지 | 범위 외 | 용융흔 미세조직(EBSD)은 데이터 속성 수준으로만 반영 |
| IFC/건축 온톨로지 | 범위 외 | 발화 구역 특정 이후 단계만 다룸 |

---

## Step 3. 핵심 용어 목록 (Term List)

논문 Table 1·2, 3.2절 감식 항목, NFPA 921 Ch.9(Electricity and Fire)·Ch.19(Fire Cause Determination)에서 추출. **굵은 글씨**는 실험에서 확인된 두 혼동 쌍을 가르는 핵심 변별 용어.

### 3.1 축 ① 발열 메커니즘

| 국문 | 영문 | 근거 |
|---|---|---|
| 줄열(저항 발열) | Joule / resistive heating | NFPA 921 Ch.9 |
| **접촉불량(고저항 접속) 발열** | high-resistance connection heating | Table 1·2 |
| 아산화동 증식(글로잉) | glowing connection, Cu₂O growth | Table 1 |
| 반단선 단면적 감소 과열 | reduced cross-section overheating | Table 1 |
| 직렬 아크 | series arc | NFPA 921 Ch.9 |
| 단락(병렬) 아크 | short-circuit (parallel) arc | NFPA 921 Ch.9 |
| 압착손상 유발 아크 | crush-induced arc | Table 1 |
| 절연파괴 단락 | dielectric breakdown short | Table 1 |
| **트래킹(표면 도전로 아크)** | arc tracking | Table 1·2 |
| 누설전류 발열 | leakage current heating | Table 2 (누전차단기 간헐 동작) |
| 과부하 발열 | overload heating | 확장 슬롯 |
| 외부화염 수열 | external flame exposure | 1.3절 반증 판정 범주 |

### 3.2 축 ② 물리 증거물 · 손상 양상 · 현장 증거

| 국문 | 영문 | 근거 |
|---|---|---|
| 도체(단선/연선), 소선 | conductor (solid/stranded), strand | Table 1 |
| 피복·절연물 | insulation | Table 1 |
| 접속부, 단자대, 콘센트 | connection point, terminal block, receptacle | Table 2 |
| 차단기, 누전차단기 | circuit breaker, RCD/ELCB | Table 2 |
| 단자함, 분전반 | junction box, distribution panel | Table 10 사례 A |
| 용융흔 / 아크 용융흔(단락흔) / 아크 비드 | melt mark / arc melt mark / arc bead | NFPA 921 Ch.9 |
| **1차 단락흔(원인) / 2차 단락흔(피해)** | cause bead / victim bead | NFPA 921 Ch.9, 참고문헌 [5][6] |
| 수열 용융흔(열흔) | fire melt mark | [5] |
| 스패터, 다발성 아크 비드 | spatter, multiple arc beads | Table 2 |
| 국부 변색·산화, 광택 소실 | localized discoloration, loss of luster | Table 1 |
| 단자 장기 발열 흔적 | long-term terminal heating trace | Table 2 |
| 소선 파단, 소선 끝단 소형 용융구 | strand fracture, small melt ball on strand end | Table 2 |
| 피복 경화·균열·취성·변색, 탄화 | embrittlement, cracking, carbonization | Table 2 |
| **수지상 탄화 도전로** | dendritic carbonized conductive path | Table 1 |
| 압착·찍힘·절단 변형 | crush / dent / cut deformation | Table 2 |
| 자중 연화·처짐, 열 구배 유동 | sagging, thermal-gradient flow | Table 1·2 |
| 소손 중심 표면 집중 | burn center concentrated on surface | Table 2 (접촉불량 반증) |
| 외력 흔적 | external force trace | Table 2 |
| 차단기 트립 이력 | breaker trip record | 3.2절 맥락 정보 |
| 누수·결로 흔적, 분진 퇴적 | moisture trace, dust deposit | Table 2 |
| 아크 매핑 지점 | arc mapping point | NFPA 921 Ch.9 |

### 3.3 축 ③ 선행 조건

| 국문 | 영문 | 근거 |
|---|---|---|
| **통전 / 비통전** | energized / de-energized | 3.2절 (기각 수준 조정) |
| 과부하 상태 | overload state | 확장 |
| **접속부 체결 불량·헐거움** | loose connection | Table 2 핵심 단서 |
| 접속부 부식 | corroded connection | 보강 |
| 반복 굴곡, 진동, 인장 | repeated flexing, vibration, tension | Table 2 |
| 외력 압착·찍힘 | external crushing | Table 2 |
| 장기 반복 응력 정황 | long-term repeated stress | Table 2 |
| 노후화·장기 사용 | aged insulation | Table 2 |
| **절연저항 저하 / 정상** | reduced / normal insulation resistance | Table 2 (절연열화 핵심 · 트래킹 반증) |
| 열적 절연 열화 | thermal degradation | Table 1 |
| **누수·결로·우천 노출** | moisture exposure | Table 10 사례 A |
| 분진 퇴적, 염분·화학물질 노출 | dust accumulation, saline/chemical exposure | Table 2 |
| 오염 환경 (위 셋의 합집합) | contaminated environment | Table 2 트래킹 핵심 단서 |
| 발화 전 이상 징후 | pre-fire anomaly | 3.2절 |
| 누전차단기 간헐 동작 | intermittent RCD tripping | Table 2 |
| 비정상 온도·전압강하 | abnormal temperature / voltage drop | Table 2 |

### 3.4 축 ④ 최초 착화물

| 국문 | 영문 | 근거 |
|---|---|---|
| 최초 착화물 | first fuel ignited | NFPA 921 Ch.19 발화 순서 |
| 피복재(PVC·XLPE·고무) | insulation material fuel | 증거물 자체 |
| 함체·몰드 수지 | enclosure / molding resin | 증거물 자체 |
| 퇴적 분진, 종이·목재·섬유, 단열재, 인화성 증기 | accumulated dust, cellulose, thermal insulation, flammable vapor | 3.2절 '주변 가연물' |
| 발화 온도, 최소 착화 에너지, 열원 거리 | ignition temperature, MIE, distance to heat source | NFPA 921 경합 가능 발화원 |

### 3.5 절차·판정 용어 (보조 축)

| 국문 | 영문 | 근거 |
|---|---|---|
| 발화 시나리오(가설), 최종 감별 의견 | ignition scenario (hypothesis), conclusion | 1.2절 |
| 핵심 확인 단서 / 보강 단서 / 반증 단서 | core / supporting / refuting indicator | Table 2 열 제목 |
| 결정적 반증 | decisive refutation | 3.2절 |
| 확인 / 부정 확인 / 확인 불가 / 미확인 | confirmed / confirmed-absent / unverifiable / missing | 3.2절 |
| 절차적 지지점수 (0~100, 확률 아님) | procedural support score | 3.2절 |
| 확정 조건 | closure condition | 3.2절 (항목 ≥2, 질의 ≥2, 점수 ≥70) |
| 변별 질의, 세션 레지스트리 | discriminating query, session registry | 3.2절 |
| 판단보류 | withheld | 3.1절 |
| 조사관 / AI 에이전트 / 계측기 | investigator / AI agent / instrument | 2.2절 HITL |

---

## Step 4. 클래스 계층 (Class Hierarchy)

### 4.1 구축 방식: Middle-Out

| 방식 | 채택 여부 | 이유 |
|---|---|---|
| Top-down | 부분 | BFO 상위 범주는 이미 주어져 있어 4축의 부모만 정하면 됨 |
| Bottom-up | 부분 | Table 2의 18개 단서(6가설 × 3열)와 3.2절 감식 항목이 구체 수준 출발점 |
| **Middle-out** | **채택** | 논문의 6개 감별 범주와 Table 2 단서라는 **중간 수준 개념이 가장 안정적**이며, 위로는 BFO 정렬, 아래로는 세부 손상 형태로 확장 |

### 4.2 상위 정렬 (BFO 2.0)

```
bfo:entity
├── bfo:continuant
│   ├── bfo:independent continuant ─ bfo:material entity
│   │   ├── efi:PhysicalEvidence            (축 ②)
│   │   └── efi:FirstFuelIgnited            (축 ④)
│   ├── bfo:specifically dependent continuant
│   │   ├── bfo:quality
│   │   │   ├── efi:DamagePattern           (축 ② 손상 양상 — 증거물에 inheres_in)
│   │   │   └── efi:AntecedentCondition (상태형)   (축 ③)
│   │   └── bfo:disposition ─ efi:Ignitability
│   └── bfo:generically dependent continuant ─ iao:information content entity
│       ├── efi:IgnitionScenario / efi:Conclusion / efi:IndicatorRule
│       └── efi:SceneEvidence  (조사관 진술·기록 형태의 현장 사실)
└── bfo:occurrent ─ bfo:process
    ├── efi:HeatingMechanism                (축 ①)
    ├── efi:AntecedentCondition (이력형: 반복 굴곡 등)   (축 ③)
    └── efi:ArcEvent · efi:FireExposureEvent  (⊓ time:TemporalEntity)
```

### 4.3 축 ① 발열 메커니즘

```
efi:HeatingMechanism  ⊑ bfo:process
├── efi:ElectricalHeatingMechanism
│   ├── efi:ResistiveHeating                       줄열
│   │   ├── efi:PoorContactHeating                 접촉불량(고저항 접속)
│   │   │   └── efi:GlowingConnection              아산화동 증식 글로잉
│   │   ├── efi:PartialDisconnectionHeating        반단선 단면적 감소 과열
│   │   └── efi:OverloadHeating                    과부하 (확장 슬롯)
│   ├── efi:ArcHeating
│   │   ├── efi:ShortCircuitArc                    단락(병렬) 아크
│   │   │   ├── efi:CrushInducedArc                압착손상 유발
│   │   │   └── efi:InsulationBreakdownArc         절연파괴 유발
│   │   ├── efi:SeriesArc                          직렬 아크 (반단선 파단부)
│   │   └── efi:ArcTracking                        트래킹
│   └── efi:LeakageCurrentHeating                  누설전류
└── efi:NonElectricalHeatingMechanism
    └── efi:ExternalFlameExposure                  외부화염 (반증 판정 범주)
```

### 4.4 축 ② 물리 증거물 · 손상 양상 · 현장 증거

```
efi:PhysicalEvidence  ⊑ bfo:material entity, sosa:FeatureOfInterest
└── efi:ElectricalArtifact
    ├── efi:Conductor ─ efi:SolidConductor | efi:StrandedConductor
    ├── efi:Insulation
    ├── efi:ConnectionPoint ─ efi:TerminalBlock | efi:PlugReceptacle
    ├── efi:ProtectiveDevice
    └── efi:Enclosure

efi:DamagePattern  ⊑ bfo:quality   (증거물이 exhibits)
├── efi:MeltMark
│   ├── efi:ArcMeltMark (단락흔)
│   │   ├── efi:PrimaryArcMark      1차 (원인)   ┐ owl:disjointWith
│   │   ├── efi:SecondaryArcMark    2차 (피해)   ┘
│   │   └── efi:ArcBead
│   ├── efi:FireMeltMark (열흔) ─ efi:GeneralMelting
│   ├── efi:LargeMeltMark
│   └── efi:SmallMeltBallOnStrandEnd
├── efi:Spatter · efi:MultipleArcBeads
├── efi:LocalizedDiscoloration · efi:CuprousOxideGrowth · efi:LossOfLuster · efi:LongTermTerminalHeating
├── efi:StrandFracture ─ efi:StrandFractureAtStressPoint
├── efi:InsulationCarbonization · efi:InsulationEmbrittlement · efi:CarbonizedConductivePath
├── efi:MechanicalDeformation ─ efi:WholeConductorCrushedOrCut
├── efi:Sagging · efi:ThermalGradientFlow
└── efi:BurnCenterOnSurface

efi:SceneEvidence  ⊑ iao:ICE, prov:Entity   (조사관이 확인하는 비증거물 사실)
├── efi:BreakerTripRecord ─ efi:ImmediateTripAfterExternalForce
├── efi:NoTripDespiteExternalForce        (복합: 외력 흔적 확인 ∧ 트립 이력 부정 확인)
├── efi:ExternalForceTrace
├── efi:MoistureTrace · efi:ContaminationDeposit
├── efi:BurnPattern · efi:ArcMapPoint
├── efi:NoArcOrSpatter                    (복합: 아크 용융흔 부정 확인 ∧ 스패터 부정 확인)
├── efi:MultipleArcBeadsAtOrigin
└── efi:FlexingHistoryWithStrandFracture  (복합: 반복 굴곡 이력 ∧ 소선 부분단선)
```

> 복합 사실(composite fact)은 Table 2의 반증단서가 두 사실의 결합으로 정의되어 있어 두었다. 세션 레지스트리의 정규화기가 구성 사실이 모두 등록될 때 인스턴스화하며, OWL 정의는 `rdfs:comment`로 남기고 판정은 SHACL 층에서 수행한다.

### 4.5 축 ③ 선행 조건

```
efi:AntecedentCondition  ⊑ bfo:quality ⊔ bfo:process
├── efi:ElectricalState
│   ├── efi:EnergizedState      통전    ┐ owl:disjointWith
│   ├── efi:DeEnergizedState    비통전  ┘  → 전기적 시나리오 결정적 기각
│   └── efi:OverloadState
├── efi:ConnectionCondition
│   ├── efi:LooseConnection     체결 불량·헐거움  (접촉불량 핵심)
│   └── efi:CorrodedConnection
├── efi:MechanicalStressHistory
│   ├── efi:RepeatedFlexing · efi:Vibration · efi:Tension   (반단선 필요조건)
│   ├── efi:ExternalCrushing                                (압착손상 필요조건)
│   └── efi:LongTermRepeatedStress
├── efi:InsulationCondition
│   ├── efi:AgedInsulation · efi:ReducedInsulationResistance · efi:ThermalDegradation   (절연열화 필요조건)
├── efi:EnvironmentalCondition
│   └── efi:ContaminatedEnvironment ≡ MoistureExposure ⊔ DustAccumulation ⊔ SalineOrChemicalExposure   (트래킹 필요조건)
└── efi:PreFireAnomaly
    ├── efi:IntermittentRcdTripping
    ├── efi:AbnormalTemperatureOrVoltageDrop
    └── efi:FlickeringOrOdor
```

### 4.6 축 ④ 최초 착화물

```
efi:FirstFuelIgnited  ⊑ bfo:material entity   (hasIgnitability → efi:Ignitability ⊑ bfo:disposition)
├── efi:SelfFuel                      증거물 자체 가연부
│   ├── efi:InsulationMaterialFuel    PVC · XLPE · 고무
│   └── efi:EnclosureMaterialFuel     함체·몰드 수지
└── efi:AdjacentCombustible           주변 가연물
    ├── efi:AccumulatedDustFuel
    ├── efi:CelluloseFuel             종이·목재·섬유
    ├── efi:ThermalInsulationFuel
    └── efi:FlammableVaporFuel
```

### 4.7 보조 축 — 시나리오 · 관측 · 행위자 · 상태

```
efi:IgnitionScenario  ⊑ iao:ICE, prov:Entity          (가설; 판독 결과는 여기에 등록)
├── efi:ElectricalIgnitionScenario  ⊑ ∃hasMechanism.ElectricalHeatingMechanism ⊓ ∃hasAntecedent.EnergizedState
│   ├── efi:PoorContactScenario             접촉불량
│   ├── efi:CrushDamageScenario             압착손상
│   ├── efi:PartialDisconnectionScenario    반단선
│   ├── efi:InsulationDegradationScenario   절연열화
│   └── efi:TrackingScenario                트래킹
└── efi:ExternalFlameScenario               외부화염
      (6개 상호 배타: owl:AllDisjointClasses)

efi:Conclusion  ⊑ iao:ICE, prov:Entity      (concludes → IgnitionScenario; 제약 C-2 통과 시에만 유효)
efi:IndicatorRule  ⊑ iao:ICE                (Table 2 한 칸 = 1 인스턴스)

efi:Observation ⊑ sosa:Observation, prov:Entity
└── efi:InsulationResistanceObservation ⊑ ∃sosa:observedProperty.{efi:InsulationResistance}
    └── efi:NormalInsulationResistance ≡ … ⊓ measuredPreFire=true ⊓ resultValue ≥ 1.0 (MΩ, KEC 132 저압 참조)

prov:Agent ─ efi:InvestigatorAgent | efi:AIAgent(⊑ prov:SoftwareAgent) | efi:Instrument   (모두 ⊑ sosa:Sensor)
prov:Activity ─ efi:InvestigationSession | efi:VerificationQuery

열거형(owl:oneOf)
├── efi:ConfirmationStatus = {Confirmed, ConfirmedAbsent, Unverifiable, Missing}
├── efi:Verdict            = {Active, Weakened, Refuted, Supported, Withheld}
└── efi:IndicatorRole      = {Core, Supporting, Refuting, DecisiveRefuting}
```

### 4.8 시나리오 클래스 정의 원칙

| 요소 | 공리 유형 | 이유 |
|---|---|---|
| 발열 메커니즘 | **정의(≡)** — `TrackingScenario ≡ IgnitionScenario ⊓ ∃hasMechanism.ArcTracking` | 메커니즘이 곧 범주를 결정하므로 추론기가 자동 분류 가능 |
| 선행 조건 | **필요조건(⊑)** — `TrackingScenario ⊑ ∃hasAntecedent.ContaminatedEnvironment` | 선행조건이 없으면 시나리오가 성립하지 않지만, 선행조건만으로 범주가 확정되지는 않음 |
| 증거 단서 | **규칙(IndicatorRule 인스턴스)** | 단서는 가중 합산·기각 대상이지 클래스 정의 요소가 아님 (3.2절 루브릭과 분리) |

---

## Step 5. 속성 (Properties)

### 5.1 객체 속성 — 인과 · 의존 · 증거 · 출처

| 속성 | Domain | Range | 특성 | 의미 · 상위 속성 |
|---|---|---|---|---|
| `efi:hasAntecedent` | IgnitionScenario | AntecedentCondition | — | 시나리오가 전제하는 선행조건 |
| `efi:hasMechanism` | IgnitionScenario | HeatingMechanism | SHACL로 정확히 1 | 시나리오의 발열 메커니즘 |
| `efi:hasFirstFuel` | IgnitionScenario | FirstFuelIgnited | 최대 1 | 최초 착화물 (미확인 허용 → 판단보류) |
| `efi:enables` | AntecedentCondition | HeatingMechanism | ⊑ `ro:causally upstream of` | 선행조건 → 메커니즘 인과 |
| `efi:producesDamage` | HeatingMechanism | DamagePattern | — | 메커니즘 → 손상 양상 |
| `efi:ignites` | HeatingMechanism | FirstFuelIgnited | — | 메커니즘 → 착화물 |
| `efi:exhibits` | PhysicalEvidence | DamagePattern | `owl:inverseOf ro:inheres_in` | 증거물이 나타내는 손상 |
| `efi:locatedInOriginArea` | PhysicalEvidence | ArcMapPoint | — | 발화 구역 내 위치(아크 매핑) |
| `efi:formedBy` | ArcMeltMark | ArcEvent | — | 용융흔을 형성한 아크 사건 (→ `time:before` FireExposureEvent) |
| `efi:hasIgnitability` | FirstFuelIgnited | Ignitability | — | 착화 성향(disposition) |
| `efi:inSession` | IgnitionScenario | InvestigationSession | — | 가설이 속한 세션 |
| `efi:hasFact` | InvestigationSession | Antecedent ⊔ Damage ⊔ SceneEvidence ⊔ Observation | — | 정규화된 감식 항목 |
| `efi:supportedBy` | IgnitionScenario | (사실) | ⊑ `prov:wasDerivedFrom` | 지지 근거 |
| `efi:refutedBy` | IgnitionScenario | (사실) | ⊑ `prov:wasDerivedFrom` | 기각 근거 |
| `efi:verdict` | IgnitionScenario | Verdict | Functional | 현재 판정 |
| `efi:confirmationStatus` | (사실) | ConfirmationStatus | Functional | 확인 상태 |
| `efi:discriminates` | VerificationQuery | IgnitionScenario | — | 질의가 가르는 경합 가설 |
| `efi:concludes` | Conclusion | IgnitionScenario | ⊑ `prov:wasDerivedFrom` | 결론이 채택한 가설 |
| `efi:forScenario` / `efi:indicates` / `efi:hasRole` / `efi:requiresStatus` | IndicatorRule | 시나리오 클래스(punning) / 지표 클래스 / IndicatorRole / ConfirmationStatus | 뒤 둘 Functional | Table 2 한 칸의 구조 |
| `prov:wasAttributedTo` (재사용) | 사실·관측 | Agent | — | 출처 행위자 (제약 C-4 필수) |

### 5.2 데이터 속성 — 물리 수치 · 상태

단위는 속성명 접미어로 명시하고 QUDT 단위를 병기한다. **지지점수에는 % 기호를 붙이지 않는다.**

| 속성 | Domain | Datatype | 단위 | 용도 |
|---|---|---|---|---|
| `resultValue` | Observation | `xsd:decimal` | 관측 속성에 따름 | ⊑ `sosa:hasSimpleResult` |
| `measuredPreFire` | Observation | `xsd:boolean` | — | 절연저항 반증은 발화 전·비손상 구간 계측만 인정 |
| `insulationResistance_MOhm` | Insulation | `xsd:decimal` | MΩ | 절연열화 핵심 / 트래킹 반증 |
| `comparativeTrackingIndex_V` | Insulation | `xsd:decimal` | V (IEC 60112 CTI) | 절연재의 트래킹 내성 |
| `serviceYears` | ElectricalArtifact | `xsd:decimal` | 년 | 노후화 |
| `conductorCrossSection_mm2` | Conductor | `xsd:decimal` | mm² | 반단선 단면적 감소 계산 |
| `strandCount` / `fracturedStrandCount` | StrandedConductor | `xsd:nonNegativeInteger` | 가닥 | 반단선 정도 |
| `ratedCurrent_A` / `loadCurrent_A` | ElectricalArtifact | `xsd:decimal` | A | 과부하 판정 |
| `beadDiameter_mm` | ArcMeltMark | `xsd:decimal` | mm | 1·2차 보조 지표 |
| `voidFraction` | ArcMeltMark | `xsd:decimal` (0~1) | — | 기공률 (1·2차 보조 지표) |
| `hasSharpMeltBoundary` | MeltMark | `xsd:boolean` | — | 용융 경계 명확성 |
| `heatAffectedZoneWidth_mm` | MeltMark | `xsd:decimal` | mm | 열영향부 폭 |
| `fineDendriticGrain` | ArcMeltMark | `xsd:boolean` | — | EBSD·금속조직 [6] |
| `cuprousOxidePresent` | ConnectionPoint | `xsd:boolean` | — | 아산화동 증식 |
| `carbonizationDepth_mm` | Insulation | `xsd:decimal` | mm | 탄화 깊이 |
| `isEnergized` | ElectricalState | `xsd:boolean` | — | 통전 여부 |
| `breakerTripped` / `tripDelayFromEvent_s` | BreakerTripRecord | `xsd:boolean` / `xsd:decimal` | — / s | 압착손상 핵심·반증 |
| `moistureExposureWithin_h` | MoistureExposure | `xsd:nonNegativeInteger` | h | 사례 A "전날 비" |
| `relativeHumidity_pct` | EnvironmentalCondition | `xsd:decimal` | % | 환경 |
| `ignitionTemperature_C` / `minimumIgnitionEnergy_mJ` / `distanceToHeatSource_mm` | FirstFuelIgnited | `xsd:decimal` | °C / mJ / mm | 착화 역량 검사 |
| `maxAttainableTemperature_C` | HeatingMechanism | `xsd:decimal` | °C | 착화 역량 검사 |
| `supportScore` | IgnitionScenario | `xsd:integer` [0,100] | **없음(확률 아님)** | 절차적 지지점수 |
| `scoreDelta` | IndicatorRule | `xsd:integer` | — | 루브릭 가감점 |
| `queryCount` | InvestigationSession | `xsd:nonNegativeInteger` | 회 | 확정 조건 |
| `ignitionCompetenceGap` | IgnitionScenario | `xsd:boolean` | — | 규칙 F-3 플래그 |

### 5.3 인과 사슬 인스턴스 예 — 논문 Table 10 사례 A

```
sessA : InvestigationSession  (queryCount 2)
 ├─ hasFact  f1 : MoistureExposure        status=Confirmed        wasAttributedTo inv1 : InvestigatorAgent   "옥외 단자함, 전날 우천"
 ├─ hasFact  f2 : CarbonizedConductivePath status=Confirmed       wasAttributedTo ai1  : AIAgent
 ├─ hasFact  f3 : LooseConnection         status=ConfirmedAbsent  wasAttributedTo inv1
 └─ hasFact  f4 : NormalInsulationResistance status=Unverifiable  wasAttributedTo inv1   (반증 근거로 사용 금지)

H_pc : PoorContactScenario  hasMechanism m1:PoorContactHeating  hasAntecedent f3   → supportScore 50, Active (핵심 단서 부정 확인 → 지지 없음)
H_tr : TrackingScenario     hasMechanism m2:ArcTracking         hasAntecedent f1
        f1 --enables--> m2 --producesDamage--> f2 --(exhibits⁻¹)--> artifact_A : TerminalBlock
        m2 --ignites--> fuel : EnclosureMaterialFuel
        supportedBy f1, f2  → supportScore 75 (=50+15+10), Active
C_A : Conclusion  concludes H_tr   ← 제약 C-2 통과 (확인 사실 2, 조사관 귀속 1, 점수 ≥70, 질의 ≥2)
```

---

## Step 6. 제약과 공리 (Constraints & Axioms)

### 6.1 공리 층위

| 층 | 언어 | 담당 | 세계 가정 |
|---|---|---|---|
| L1 구조 공리 | OWL 2 DL | 클래스 정의, 상호 배타, 도메인/레인지, 데이터 범위 | 개방세계 — "없다"를 말할 수 없음 |
| L2 반증 규칙 | SHACL SPARQLRule (`sh:order` 1~4) | 결정적 기각 → 1·2차 판정 → 착화 역량 → 지지점수 | 폐세계 — 세션 사실만으로 판단 |
| L3 확정 제약 | SHACL NodeShape | negative corpus 금지, 확인 상태 제약, 출처 필수 | 폐세계 |
| L4 운용 규칙 | Pydantic (`Session.apply`) | L2·L3의 실행 미러 + 변별 질의 선택 | — (TTL을 단일 진실 원천으로 적재) |

### 6.2 서술논리 공리 (Manchester 구문)

```manchester
# 시나리오 정의 (메커니즘 = 정의, 선행조건 = 필요조건)
Class: efi:ElectricalIgnitionScenario
  SubClassOf: efi:IgnitionScenario,
              efi:hasMechanism some efi:ElectricalHeatingMechanism,
              efi:hasAntecedent some efi:EnergizedState

Class: efi:PoorContactScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some efi:PoorContactHeating)
  SubClassOf:   efi:hasAntecedent some efi:LooseConnection

Class: efi:CrushDamageScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some efi:CrushInducedArc)
  SubClassOf:   efi:hasAntecedent some efi:ExternalCrushing

Class: efi:PartialDisconnectionScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some (efi:PartialDisconnectionHeating or efi:SeriesArc))
  SubClassOf:   efi:hasAntecedent some (efi:RepeatedFlexing or efi:Vibration or efi:Tension)

Class: efi:InsulationDegradationScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some efi:InsulationBreakdownArc)
  SubClassOf:   efi:hasAntecedent some (efi:AgedInsulation or efi:ReducedInsulationResistance or efi:ThermalDegradation)

Class: efi:TrackingScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some efi:ArcTracking)
  SubClassOf:   efi:hasAntecedent some efi:ContaminatedEnvironment

Class: efi:ExternalFlameScenario
  EquivalentTo: efi:IgnitionScenario and (efi:hasMechanism some efi:ExternalFlameExposure)

# 상호 배타
DisjointClasses: efi:PoorContactScenario, efi:CrushDamageScenario, efi:PartialDisconnectionScenario,
                 efi:InsulationDegradationScenario, efi:TrackingScenario, efi:ExternalFlameScenario
DisjointClasses: efi:HeatingMechanism, efi:PhysicalEvidence, efi:DamagePattern, efi:AntecedentCondition, efi:FirstFuelIgnited
DisjointClasses: efi:PrimaryArcMark, efi:SecondaryArcMark
DisjointClasses: efi:EnergizedState, efi:DeEnergizedState

# 정의 클래스 (데이터 범위 포함)
Class: efi:ContaminatedEnvironment
  EquivalentTo: efi:MoistureExposure or efi:DustAccumulation or efi:SalineOrChemicalExposure
Class: efi:NormalInsulationResistance
  EquivalentTo: efi:InsulationResistanceObservation and (efi:measuredPreFire value true)
                and (efi:resultValue some xsd:decimal[>= 1.0])

# 데이터 범위
DataProperty: efi:supportScore  Characteristics: Functional  Range: xsd:integer[>= 0, <= 100]
```

**추론 결과(HermiT 기준 기대치)**: 비통전(`DeEnergizedState`)을 `hasAntecedent`로 가지면서 `ElectricalIgnitionScenario`로 선언된 개체는 `EnergizedState` 필요조건과의 배타 공리로 **모순(inconsistent)** 이 된다. 즉 L1만으로도 "비통전 전기화재"는 논리적으로 표현 불가능하며, L2 규칙은 이를 세션 단위 기각 판정으로 바꿔 기록한다.

### 6.3 반증 규칙 (SHACL SPARQLRule)

| ID | 규칙 | 트리거 (세션 사실) | 효과 | 근거 | 순서 |
|---|---|---|---|---|---|
| **F-1** 일반 반증 | 가설의 상위 클래스를 `forScenario`로 갖는 `IndicatorRule` 중 역할이 `Refuting`/`DecisiveRefuting`인 지표 클래스(및 하위 클래스)의 사실이 `requiresStatus`(기본 `Confirmed`)로 존재 | `verdict Refuted`, `refutedBy 사실` | Table 2 반증단서 열 전체 + 3.2절 비통전 기각 | 1 |
| **F-2** 1·2차 단락흔 | `ArcMeltMark formedBy ArcEvent` ∧ `ArcEvent time:before FireExposureEvent` / 그 역 | `rdf:type PrimaryArcMark` / `SecondaryArcMark` | NFPA 921 Ch.9 — 원인/피해 아크 판정은 형태학 단독이 아니라 발화 순서·아크 매핑으로 | 2 |
| **F-3** 착화 역량 | `hasMechanism m`, `hasFirstFuel fuel`, `m.maxAttainableTemperature_C < fuel.ignitionTemperature_C` | `verdict Weakened`, `ignitionCompetenceGap true` | NFPA 921 경합 가능 발화원(competent ignition source) 요건 | 3 |
| **F-4** 지지점수 | 50 + Σ(발화한 IndicatorRule의 `scoreDelta`), [0,100] 클램프 | `supportScore` | 3.2절 "약 50점에서 출발, 사전 정의된 가감점 누적" | 4 |

F-1이 실행하는 Table 2 반증단서의 지표 클래스 매핑:

| 가설 | 결정적 반증 (공통) | 반증 단서 → 지표 클래스 |
|---|---|---|
| 5개 전기적 시나리오 | `DeEnergizedState` 확인 | — |
| 접촉불량 | ↑ | `BurnCenterOnSurface` |
| 압착손상 | ↑ | `NoTripDespiteExternalForce` |
| 반단선 | ↑ | `WholeConductorCrushedOrCut` |
| 절연열화 | ↑ | `FlexingHistoryWithStrandFracture` |
| 트래킹 | ↑ | `NormalInsulationResistance` (발화 전 계측, ≥1.0 MΩ) |
| 외부화염 | — | `MultipleArcBeadsAtOrigin` |

### 6.4 소거법 오류 방지 제약 (SHACL NodeShape)

| ID | 제약 | 방지하는 오류 | 근거 |
|---|---|---|---|
| **C-1** 기각 근거 상태 | `refutedBy`의 대상은 `confirmationStatus ∈ {Confirmed, ConfirmedAbsent}` | "확인 불가"를 "없음"으로 오독해 가설을 기각 | 3.2절 |
| **C-2** 결론 요건 | `Conclusion → concludes` 대상이 ① `Confirmed` 지지 사실 ≥ 2 ② 그중 `InvestigatorAgent` 귀속 ≥ 1 ③ `supportScore ≥ 70` ④ `verdict ≠ Refuted` ⑤ 세션 `queryCount ≥ 2` | **negative corpus** — 다른 가설이 다 기각됐다는 이유만으로 남은 가설을 확정; AI 판독 단독 확정 | NFPA 921 Ch.19 소거법 조항(부정적 증거만으로의 결론 배제), 3.2절 확정 조건, 3.3절 독립 교차 대조 |
| **C-3** 시나리오 구조 | `hasMechanism` 정확히 1, `hasAntecedent` ≥ 1, `hasFirstFuel` ≤ 1, `supportScore` ≤ 1 | 메커니즘 없는 가설, 선행조건 없는 가설 | 4.8 정의 원칙 |
| **C-4** 사실 출처 | `hasFact` 대상은 `confirmationStatus` 정확히 1 + `prov:wasAttributedTo` ≥ 1 | 명시되지 않은 정황을 추론으로 생성 | 3.2절 "등록된 감식 항목에 해당하는 값만 반영" |

### 6.5 추론 파이프라인

```
세션 레지스트리 (조사관 응답 정규화)
   │  Fact{cls, status, agent}  — C-4 검증
   ▼
[L2-1] F-1 결정적 기각 · 반증단서     → Refuted 가설 제외
   ▼
[L2-2] F-2 1·2차 단락흔 재분류        → 외부화염 vs 전기 가설 경계 확정
   ▼
[L2-3] F-3 착화 역량                  → Weakened
   ▼
[L2-4] F-4 지지점수 = 50 + Σ delta    → 상위 두 가설 결정
   ▼
CQ3: 상위 두 가설을 가르는 미확인 지표 중 |delta| 최대 → 다음 변별 질의  (Session.discriminating_slots)
   ▼
확정 조건 (C-2) 충족?  ─예→ Conclusion 생성 → 보고서 '가설 교차검증' 절에 PROV 경로 출력
                      ─아니오→ 변별 질의가 남아 있으면 반복, 없으면 Withheld(판단보류)
```

### 6.6 실행 검증 결과 (pySHACL · Pydantic 동일 결과)

| 테스트 ABox | 기대 | 결과 |
|---|---|---|
| 사례 A: `MoistureExposure`(조사관·확인) + `CarbonizedConductivePath`(AI·확인) + `LooseConnection`(부정 확인) + `NormalInsulationResistance`(확인 불가) | 트래킹 75 · 접촉불량 50 · 확인 불가는 반증에 불사용 · 확정 조건 충족 | ✔ TrackingScenario 75 Active / PoorContactScenario 50 / closure = True |
| 비통전 확인 세션 | 전기적 가설 전부 `Refuted`, 외부화염만 잔존 | ✔ TrackingScenario 0 Refuted(refutedBy DeEnergizedState) / ExternalFlameScenario 50 Active |
| `ArcEvent time:before FireExposureEvent` | `PrimaryArcMark` 추론 | ✔ |
| 지지점수 60 가설을 `Conclusion`이 채택 | C-2 위반 보고 | ✔ "지지점수 70 미만" 위반 메시지 |
| 다음 변별 질의 (트래킹 vs 접촉불량) | 한쪽만 겨냥하는 미확인 지표 우선 | ✔ `BurnCenterOnSurface`(25) → `LongTermTerminalHeating`(8) … |

---

## Step 7. 코드 산출 (Code Export)

### 7.1 파일 구성과 의존성

| 파일 | 역할 | 의존성 |
|---|---|---|
| `efi_tbox.ttl` | TBox(클래스·속성·공리) + 지표 규칙 인스턴스 25개 + SHACL 규칙 F-1~F-4 · 제약 C-1~C-4 | 없음 (검증: `rdflib`, `pyshacl`) |
| `efi_schema.py` | Pydantic v2 열거형·모델, `Ontology.load(ttl)`로 규칙·계층 적재, `Session.apply / discriminating_slots / conclusion_check / to_turtle` | `pydantic>=2`, `rdflib`(선택) |

### 7.2 Turtle 핵심 발췌

**헤더 · 상위 정렬**

```turtle
@prefix efi:  <https://w3id.org/efi-onto#> .
@prefix obo:  <http://purl.obolibrary.org/obo/> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix time: <http://www.w3.org/2006/time#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
# … owl rdf rdfs xsd skos qudt unit dcterms

<https://w3id.org/efi-onto> a owl:Ontology ;
    owl:imports <http://purl.obolibrary.org/obo/bfo.owl> , <http://www.w3.org/ns/sosa/> ,
                <http://www.w3.org/ns/prov-o#> , <http://www.w3.org/2006/time#> ;
    sh:declare [ sh:prefix "efi" ; sh:namespace "https://w3id.org/efi-onto#"^^xsd:anyURI ] .

efi:HeatingMechanism    a owl:Class ; rdfs:subClassOf obo:BFO_0000015 .   # process
efi:PhysicalEvidence    a owl:Class ; rdfs:subClassOf obo:BFO_0000040 , sosa:FeatureOfInterest .  # material entity
efi:DamagePattern       a owl:Class ; rdfs:subClassOf obo:BFO_0000019 .   # quality
efi:FirstFuelIgnited    a owl:Class ; rdfs:subClassOf obo:BFO_0000040 .
efi:IgnitionScenario    a owl:Class ; rdfs:subClassOf obo:IAO_0000030 , prov:Entity .
```

**시나리오 정의와 상호 배타**

```turtle
efi:TrackingScenario a owl:Class ; rdfs:subClassOf efi:ElectricalIgnitionScenario ; skos:prefLabel "트래킹"@ko ;
    owl:equivalentClass [ a owl:Class ; owl:intersectionOf ( efi:IgnitionScenario
        [ a owl:Restriction ; owl:onProperty efi:hasMechanism ; owl:someValuesFrom efi:ArcTracking ] ) ] ;
    rdfs:subClassOf [ a owl:Restriction ; owl:onProperty efi:hasAntecedent ; owl:someValuesFrom efi:ContaminatedEnvironment ] .

[] a owl:AllDisjointClasses ; owl:members ( efi:PoorContactScenario efi:CrushDamageScenario efi:PartialDisconnectionScenario
                                            efi:InsulationDegradationScenario efi:TrackingScenario efi:ExternalFlameScenario ) .
efi:PrimaryArcMark owl:disjointWith efi:SecondaryArcMark .
efi:EnergizedState owl:disjointWith efi:DeEnergizedState .
```

**절연저항 정상 — 데이터 범위 정의 클래스**

```turtle
efi:NormalInsulationResistance a owl:Class ;
    owl:equivalentClass [ a owl:Class ; owl:intersectionOf (
        efi:InsulationResistanceObservation
        [ a owl:Restriction ; owl:onProperty efi:measuredPreFire ; owl:hasValue true ]
        [ a owl:Restriction ; owl:onProperty efi:resultValue ;
          owl:someValuesFrom [ a rdfs:Datatype ; owl:onDatatype xsd:decimal ;
                               owl:withRestrictions ( [ xsd:minInclusive "1.0"^^xsd:decimal ] ) ] ] ) ] .
```

**지표 규칙 인스턴스 (Table 2 → 기계 가독)**

```turtle
efi:R_ANY_DeEnergized a efi:IndicatorRule ; efi:forScenario efi:ElectricalIgnitionScenario ;
    efi:indicates efi:DeEnergizedState ; efi:hasRole efi:DecisiveRefuting ; efi:requiresStatus efi:Confirmed ; efi:scoreDelta -100 .
efi:R_TR_core a efi:IndicatorRule ; efi:forScenario efi:TrackingScenario ;
    efi:indicates efi:ContaminatedEnvironment ; efi:hasRole efi:Core ; efi:requiresStatus efi:Confirmed ; efi:scoreDelta 15 .
efi:R_TR_ref  a efi:IndicatorRule ; efi:forScenario efi:TrackingScenario ;
    efi:indicates efi:NormalInsulationResistance ; efi:hasRole efi:Refuting ; efi:requiresStatus efi:Confirmed ; efi:scoreDelta -25 .
# … 시나리오별 핵심·보강·반증 규칙 25개 (scoreDelta는 예시값 — 실제 루브릭으로 교체)
```

**SHACL 반증 규칙 F-1 (일반형 · 상속 포함)**

```turtle
efi:FalsificationRuleShape a sh:NodeShape ; sh:targetClass efi:IgnitionScenario ;
    sh:rule [ a sh:SPARQLRule ; sh:prefixes <https://w3id.org/efi-onto> ; sh:order 1 ;
        sh:construct """
        CONSTRUCT { $this efi:verdict efi:Refuted ; efi:refutedBy ?f . }
        WHERE {
          $this rdf:type/rdfs:subClassOf* ?cat .
          ?r a efi:IndicatorRule ; efi:forScenario ?cat ; efi:indicates ?C ; efi:hasRole ?role ; efi:requiresStatus ?st .
          FILTER ( ?role IN ( efi:Refuting , efi:DecisiveRefuting ) )
          $this efi:inSession ?s . ?s efi:hasFact ?f .
          ?f rdf:type/rdfs:subClassOf* ?C ; efi:confirmationStatus ?st .
        }""" ] .
```

**결론 제약 C-2 (negative corpus 금지)**

```turtle
efi:ConclusionShape a sh:NodeShape ; sh:targetClass efi:Conclusion ;
    sh:property [ sh:path efi:concludes ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:node [ a sh:NodeShape ;
            sh:property [ sh:path efi:supportedBy ; sh:qualifiedMinCount 2 ;
                sh:qualifiedValueShape [ sh:property [ sh:path efi:confirmationStatus ; sh:hasValue efi:Confirmed ] ] ;
                sh:message "긍정 지지 근거가 2건 미만 — 타 가설 소거만으로 확정할 수 없다"@ko ] ;
            sh:property [ sh:path efi:supportedBy ; sh:qualifiedMinCount 1 ;
                sh:qualifiedValueShape [ sh:property [ sh:path prov:wasAttributedTo ; sh:class efi:InvestigatorAgent ; sh:minCount 1 ] ] ;
                sh:message "조사관이 확인한 현장 사실이 최소 1건 필요 — AI 판독만으로 확정 불가"@ko ] ;
            sh:property [ sh:path efi:supportScore ; sh:minInclusive 70 ; sh:minCount 1 ] ;
            sh:property [ sh:path efi:verdict ; sh:not [ sh:hasValue efi:Refuted ] ] ;
            sh:property [ sh:path ( efi:inSession efi:queryCount ) ; sh:minInclusive 2 ] ] ] .
```

### 7.3 Pydantic 스키마 핵심 발췌

```python
class Status(StrEnum):            # 논문 3.2절: 결측 ≠ 확인 불가 ≠ 부정 확인
    CONFIRMED = "Confirmed"; CONFIRMED_ABSENT = "ConfirmedAbsent"; UNVERIFIABLE = "Unverifiable"; MISSING = "Missing"

class Fact(BaseModel):            # 세션 레지스트리 1행 = 정규화된 감식 항목
    cls: str                      # TBox 클래스 로컬명 (검증기로 존재 확인)
    status: Status
    agent: Agent                  # InvestigatorAgent | AIAgent | Instrument  (PROV 귀속)
    observation: Observation | None = None

class IndicatorRule(BaseModel):   # Table 2 한 칸 = efi:IndicatorRule
    scenario: Scenario | Literal["ElectricalIgnitionScenario"]
    indicator: str; role: Role; required_status: Status = Status.CONFIRMED; delta: int

class Hypothesis(BaseModel):
    scenario: Scenario; mechanism: Mechanism
    support_score: int = Field(50, ge=0, le=100)   # % 기호 없음
    verdict: Verdict = Verdict.ACTIVE
    supported_by: list[str] = []; refuted_by: list[str] = []

class Ontology(BaseModel):        # TTL이 단일 진실 원천: 규칙 + subClassOf* 계층
    rules: list[IndicatorRule]; ancestors: dict[str, set[str]]
    @classmethod
    def load(cls, ttl_path: str) -> Ontology: ...

class Session(BaseModel):
    def apply(self, o: Ontology) -> Session: ...                 # F-1 → F-3 → F-4 미러
    def discriminating_slots(self, o: Ontology) -> list[tuple[str, Scenario, int]]: ...   # CQ3
    def conclusion_check(self, h: Hypothesis) -> list[str]: ... # C-2 미러 (위반 사유 목록)
    def to_turtle(self) -> str: ...                              # ABox 직렬화 → pySHACL 교차 검증
```

```python
# 실행 예 (사례 A)
onto = Ontology.load("efi_tbox.ttl")
s = Session(case_id="A", query_count=2,
    facts=[Fact(cls="MoistureExposure", status=Status.CONFIRMED, agent=Agent.INVESTIGATOR),
           Fact(cls="CarbonizedConductivePath", status=Status.CONFIRMED, agent=Agent.AI_VLM),
           Fact(cls="LooseConnection", status=Status.CONFIRMED_ABSENT, agent=Agent.INVESTIGATOR)],
    hypotheses=[Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING),
                Hypothesis(scenario=Scenario.TRACKING, mechanism=Mechanism.ARC_TRACKING)]).apply(onto)
# → TrackingScenario 75 Active [] / PoorContactScenario 50 Active [...]
# → discriminating_slots: [('BurnCenterOnSurface', POOR_CONTACT, 25), ...]
```

### 7.4 FIReAct 연동 흐름

| FIReAct 단계 (논문) | 온톨로지 호출 | 입력 → 출력 |
|---|---|---|
| 가설수립 (3.1) | VLM 판독 → `Hypothesis` 인스턴스 생성 (`support_score=50`) | 이미지 → `IgnitionScenario` 후보 (Conclusion 아님) |
| 가설검증 (3.2) 질의 선택 | `Session.discriminating_slots(onto)` | 상위 두 가설 → 미확인 지표 순위 → 질의문 생성 (SKOS 라벨 사용) |
| 가설검증 (3.2) 응답 정규화 | `Fact(cls, status, agent)` 등록 · C-4 검증 | 자연어 응답 → 4-상태 사실 |
| 가설검증 (3.2) 재평가 | `Session.apply(onto)` | F-1 → F-4 실행, 지지점수 갱신 |
| 결론확정 (3.3) | `Session.conclusion_check(h)` → 비어 있으면 `Conclusion` 생성 | 확정 조건·negative corpus 검사 |
| 보고서 생성 (3.3) | `Session.to_turtle()` → PROV 경로 질의 | '가설 교차검증' 절: 지지·기각 사실과 출처 나열 |
| RAG (6.1) | `skos:prefLabel/altLabel/definition` + NFPA 921 조항 링크(`dcterms:references`, 후속) | 검색 키 → 조항 근거 인용 |
| 폐쇄망 SLM 증류 (6.2) | `Session.model_json_schema()` | 세션 로그 → 정형 학습 데이터 |

---

## 8. 검증 · 후속 계획

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| V1 DL 일관성 | Protégé + HermiT로 `efi_tbox.ttl` 분류·일관성 검사 | unsatisfiable 클래스 0 |
| V2 CQ 단위 테스트 | CQ1~CQ5 각각에 SPARQL/pySHACL 테스트 ABox 작성 (6.6 표 확장) | 5/5 통과 |
| V3 루브릭 이식 | `scoreDelta` 예시값을 논문 3.2절 실제 가중 루브릭으로 교체, 750회 실행 로그로 회귀 검증 | Table 5 동적 질의 정확도 재현 |
| V4 조항 링크 | 각 `IndicatorRule`에 NFPA 921 (2024) 조항 번호를 `dcterms:references`로 부착 — 조항 번호는 2024판 원문 대조 후 확정 | 규칙 25개 전부 |
| V5 절연저항 슬롯 | `InsulationResistanceObservation`을 필수 질의 슬롯으로 승격 (12번 슬라이드 실무 숙제) | 절연열화 정확도 개선 확인 |
| V6 ABox 확장 | 150건 데이터셋을 `Session.to_turtle()`로 변환해 지식 그래프 구축, 혼동 쌍 질의로 CQ3 재검증 | 그래프 적재 완료 |

---

## 부록 A. 논문 Table 1·2 ↔ 온톨로지 요소 대응

| 가설 | 형태학적 특징 (Table 1 → DamagePattern) | 현장 추론 지표 (Table 1 → Antecedent/SceneEvidence) | 핵심 확인 단서 (Table 2 → Core) | 보강 단서 (→ Supporting) | 반증 단서 (→ Refuting) |
|---|---|---|---|---|---|
| 접촉불량 | LocalizedDiscoloration | LongTermTerminalHeating, CuprousOxideGrowth, LossOfLuster | LooseConnection | LongTermTerminalHeating, AbnormalTemperatureOrVoltageDrop | BurnCenterOnSurface |
| 압착손상 | ArcBead, MeltMark(용융 경계) | ExternalForceTrace, BreakerTripRecord, EnergizedState | ImmediateTripAfterExternalForce | MechanicalDeformation, LargeMeltMark | NoTripDespiteExternalForce |
| 반단선 | StrandFracture, MeltMark(국부) | RepeatedFlexing, 단면적 감소(`conductorCrossSection_mm2`) | StrandFractureAtStressPoint | SmallMeltBallOnStrandEnd, LongTermRepeatedStress | WholeConductorCrushedOrCut |
| 절연열화 | InsulationEmbrittlement, InsulationCarbonization | ThermalDegradation, InsulationBreakdownArc | AgedInsulation, ReducedInsulationResistance | InsulationEmbrittlement | FlexingHistoryWithStrandFracture |
| 트래킹 | CarbonizedConductivePath | LeakageCurrentHeating(표면 미세 전류), 흑연화 | ContaminatedEnvironment | CarbonizedConductivePath, IntermittentRcdTripping | NormalInsulationResistance |
| 외부화염 | Sagging, GeneralMelting | ThermalGradientFlow, 아크 흔적 부재 | NoArcOrSpatter | GeneralMelting, Sagging | MultipleArcBeadsAtOrigin |

## 부록 B. 참고 표준

| 표준 | 용도 |
|---|---|
| NFPA 921 (2024) Ch.4 Basic Methodology · Ch.9 Electricity and Fire · Ch.19 Fire Cause Determination | 과학적 방법, 아크 판정, 발화 순서, 소거법 조항 (조항 번호는 원문 대조 후 부착) |
| Noy & McGuinness, *Ontology Development 101*, Stanford KSL-01-05 (2001) | 7단계 방법론 |
| ISO/IEC 21838-2 (BFO 2.0) · OBO RO | 상위 온톨로지·관계 |
| W3C SOSA/SSN · PROV-O · OWL-Time · SHACL · SKOS | 관측·출처·시간·제약·용어 |
| QUDT · IEC 60112 (CTI) · KEC 132 (저압 절연저항 기준) | 단위·절연재 트래킹 지수·절연저항 임계값 |

---

## 부록 C. 원안과 달라진 지점 (변경 이력)

이 계획서는 초기 설계를 담은 문서다. 이후 NFPA 921 (2024) 원문 대조를 진행하며
원안과 달라진 결정들이 있다. 계획서 본문은 그대로 두고 차이만 여기 적는다.
현재 수치는 `make status` 로 확인한다.

### C.1 V3 (루브릭 이식) — 대체함

원안은 `scoreDelta` 를 논문 3.2절의 실제 가중 루브릭으로 교체하고 750회 실행 로그로
회귀 검증하는 것이었다. 조사관마다 중요도 판단이 갈려 순위를 모아도 수렴하지 않는다는
판단에 따라, 개별 값을 정하는 대신 **값을 만드는 공식**을 정했다.

- 가중치는 변별력에서 유도한다. 6개 가설 중 k개와 양립하는 단서는 `log2(6/k)` 만큼
  가설 공간을 좁힌다. k=6 이면 0 이 되어 C-5(공유 형태 확정 불가)가 계산 결과로 나온다.
- 척도(지지 15 / 반증 30)는 확정 조건(70점, 최소 2건)에서 풀려나왔다.
- 판단이 들어간 상수는 형태학적 감쇠 0.7 하나뿐이다.
- 구현은 `scripts/score.py`. TTL 의 값을 손으로 고치면 시험이 잡는다.

**미충족 사항**: 원안의 완료 기준(Table 5 동적 질의 정확도 재현)은 그대로 남아 있다.
공식이 옳은지는 ABox 150건으로만 판정된다.

### C.2 V4 (조항 링크) — 방침을 바꿈

원안은 각 `IndicatorRule` 에 NFPA 921 조항 번호를 붙이는 것이었다. 그대로 하면
출처가 왜곡된다 — 지표 규칙은 Table 2 와 국내 실무·선행연구에서 왔고 NFPA 가 아니다.
조항은 **방법론 층(SHACL 도형)에만** 붙였고, 지표 규칙에 붙는 것을 시험으로 막았다.

### C.3 원문 대조가 잡아낸 오류 다섯 건

| 대상 | 원안 | 정정 | 근거 |
|---|---|---|---|
| 수지상 탄화 도전로 | 트래킹 전용 | 외부화염도 냄 | §9.9.4.5 비전기적 열로도 탄화된다 |
| 다발성 아크 비드 | 반단선 전용 | 외부화염도 냄 | §9.10.2 탄화를 통한 아크는 여러 지점에 |
| 아크 용융흔·비드 | 전기적 가설만 | 외부화염도 냄 | §9.10.1 화재로 연화된 피복이 파팅 아크를 만든다 |
| 국부 변색·광택 소실 | 전기적 가설만 | 외부화염도 냄 | §9.10.3.1(1) 화재 노출만으로도 금속이 산화된다 |
| 종이·목재·섬유 | 한 클래스 | 종이·섬유 / 목재 구조재로 분리 | §9.9.4.1 아크 착화성이 정반대다 |

다섯 건이 모두 같은 오류다. 이 온톨로지는 '이 가설이 이 흔적을 낸다'는 방향으로만
지어졌고 '화재 자체가 낸다'는 반대 방향을 담지 않았다. 그 결과 전용 단서가 실제보다
많아 보였고 변별력이 과대평가됐다. `scripts/audit.py` 가 남은 것을 점검한다.

### C.4 범위 판정 — 이론에 있으나 담지 않은 것

담을 수 없는 것을 분모에 두면 이식률 100% 는 도달 불가가 되고, 그 순간 지표가
무시된다. 그래서 판정하고 기록한다. 판정 기준은 **잔해에서 관측되는가**이다.

| 조항 | 판정 | 이유 |
|---|---|---|
| §9.13.3.2~3.5, §9.13.4.3 | 현장 절차 | 도체 취급·촬영·표식은 작업 절차다 |
| §9.3.2, §9.3.3 | 범위밖 | 전압·인입 방식·계량기는 배경 지식이다 |
| §9.9.1.1 | 범위밖 | 열전달 지속 시간은 잔해에서 관측되지 않는다 |
| §9.9.5.2 | 범위밖 | 스파크 입자의 재질·크기는 판별되지 않는다 |
| §9.9.6 | 범위밖 | 발견 난이도는 조사 여건이지 판정 대상이 아니다 |
| §4.1 발화 지점 특정 | 범위밖 | 1.1 의 도메인 경계. 이 프로젝트는 그 이후를 다룬다 |
| §9.14 정전기, §9.15 배터리 | 범위밖 | 5대 요인 밖. ESS·리튬 화재를 넣을지는 재검토 여지 |

원문의 물리 논의(와트·온도·지속 시간)는 §19.6.4 의 가설 검증 수단이지 §9.10 의
손상 해석이 아니다. 관측 가능한 형태로 바꿔 담는다 —
"열전달 계수"가 아니라 "전선이 단열재에 묻혀 있었나"(`HeatDissipationImpairment`).

### C.5 Python 과 SHACL 의 경계

결론 제약이 SHACL 에만 쌓이는 동안 Python 파이프라인은 초기 다섯 가지만 알고 있었다.
두 곳에 적으면 반드시 갈라진다. 역할을 나누고 위임하기로 했다.

- `src/efi_schema.py` — 가감점 산출, 변별 질의 선택, 세션 상태. 대화 루프용이라 가볍다.
- SHACL — 결론 검증 전체. 확정 시점에 한 번 돌면 된다.
- `Session.validate()` 가 pySHACL 을 호출해 위임한다. 제약을 Python 으로 옮겨 적지 않는다.
