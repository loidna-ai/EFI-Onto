# 조사서 사례 (ABox)

지금까지 잰 것은 전부 **이식률**이다. 이론을 얼마나 옮겼는지만 안다.
**정확도는 한 번도 재지 않았다.** 그것을 재려면 여기에 사례가 들어와야 한다.

```
cases/
  raw/    조사서 원본. git 에 넣지 않는다 (사건 정보·개인정보)
  abox/   변환된 TTL. 재생성물이라 git 에 넣지 않는다
```

## 먼저 10건

150건을 다 변환한 뒤에 필드 명세가 틀린 것을 알면 전부 다시 해야 한다.
**10건으로 파이프라인을 검증하고 명세를 확정한 다음 넓힌다.**

## 사례 하나에 필요한 것

### 필수 — 이것만 있으면 점수 산출과 변별 질의가 돈다

| 항목 | 설명 |
|---|---|
| `case_id` | 사례 식별자 |
| `facts[]` | 조사에서 확인한 사실 목록 |
| `facts[].cls` | 아래 어휘 중 하나 |
| `facts[].status` | `Confirmed` 확인 / `ConfirmedAbsent` 부재 확인 / `Unverifiable` 확인 불가 / `Missing` 미확인 |
| `facts[].agent` | `InvestigatorAgent` 조사관 / `Instrument` 계측기 / `AIAgent` 판독 |
| `hypotheses[]` | 검토한 가설 (없으면 9개 전부로 시작) |
| `query_count` | 확인 질의 횟수. 모르면 실제 확인 항목 수로 |

**`status` 를 뭉개지 말 것.** 확인 불가와 미확인을 같은 칸에 넣으면 이 온톨로지의
핵심 원칙(P4)이 무너진다. 조사서에 "확인 불가"라고 적혀 있으면 `Unverifiable`,
아예 언급이 없으면 `Missing` 이다.

### 정답 라벨 — 정확도를 재려면 필요하다

| 항목 | 설명 |
|---|---|
| `actual_scenario` | 그 사례의 실제 판정 (9개 가설 중 하나, 또는 `Undetermined`) |

### 비교군 — "조사관보다 낫다"를 말하려면 필요하다

| 항목 | 설명 |
|---|---|
| `investigator_initial` | 조사관이 **처음** 지목한 가설 |

최종 결론만 남아 있고 초기 판단이 기록되지 않은 경우가 많다.
없으면 목표의 후반부는 검증 대상이 사라진다. 확인이 필요하다.

## 어휘

`facts[].cls` 에는 TTL 클래스의 로컬명을 쓴다. 목록은 이렇게 뽑는다.

```bash
python -c "import sys;sys.path.insert(0,'src');import efi_schema as E;[print(m.value) for m in E.Antecedent]"
```

| 갈래 | 개수 | 예 |
|---|---|---|
| 선행 조건 `Antecedent` | 18 | `LooseConnection`, `ContaminatedEnvironment`, `ThermalDegradation` |
| 손상 양상 `Damage` | 24 | `CarbonizedConductivePath`, `ArcBead`, `MoltenOxideMass` |
| 현장 사실 `SceneEvidence` | 9 | `ImmediateTripAfterExternalForce`, `NoArcOrSpatter` |
| 착화물 `Fuel` | 6 | `InsulationMaterialFuel`, `PaperTextileFuel` |

가설은 아홉이다. 앞의 다섯이 사례 라벨에 있는 5대 요인이고, 뒤의 셋은 화재조사 보고규정의
나머지 전기적 요인이다(라벨 0건 — 온톨로지는 갖되 사례로는 아직 못 잰다).
`PoorContactScenario` 접촉불량 · `CrushDamageScenario` 압착손상 ·
`PartialDisconnectionScenario` 반단선 · `InsulationDegradationScenario` 절연열화 ·
`TrackingScenario` 트래킹 · `ExternalFlameScenario` 외부화염 ·
`OverloadScenario` 과부하·과전류 · `GroundFaultScenario` 누전·지락 · `InterTurnShortScenario` 층간단락

판정은 가설 하나이거나 판단보류다. 판단보류는 둘로 갈린다 — 단락흔이 확인됐고 비통전이
아니면 **미확인 단락**(국내 분류, D-14), 아니면 **원인미상**. `scripts/eval.py` 가 둘 다 오답으로 센다.

**조사서 표현이 이 어휘에 없으면 억지로 끼워 맞추지 말고 그대로 두라.**
매핑되지 않는 표현이 무엇인지가 어휘의 빈 곳을 알려준다.

## 형식

무엇이든 좋다 — CSV, 엑셀, JSON, 한글 표. 변환기는 형식을 보고 만든다.
가장 단순한 형태는 이렇다.

```json
{
  "case_id": "2023-0417",
  "query_count": 4,
  "facts": [
    {"cls": "MoistureExposure", "status": "Confirmed", "agent": "InvestigatorAgent"},
    {"cls": "CarbonizedConductivePath", "status": "Confirmed", "agent": "InvestigatorAgent"},
    {"cls": "LooseConnection", "status": "ConfirmedAbsent", "agent": "InvestigatorAgent"},
    {"cls": "InsulationResistanceObservation", "status": "Unverifiable", "agent": "Instrument"}
  ],
  "actual_scenario": "TrackingScenario",
  "investigator_initial": "PoorContactScenario"
}
```

## 첫 결과는 정확도가 아닐 것이다

결론 검증까지 통과하려면 발화 순서 기여 요인 일곱, 열전달 경로, 아크 개시 경위,
착화 역량·시간선·접촉 정황, 이격 거리, 의견 확신도가 모두 있어야 한다
(`make test` 의 `test_a_complete_conclusion_can_pass` 참조).

실제 조사서에 이 항목들이 다 적혀 있을 가능성은 낮다. **그래서 첫 측정은
"150건 중 몇 건이 NFPA 921 의 결론 요건을 충족하는가"가 될 것이다.**

이것 자체가 결과다. 둘 중 하나를 뜻한다 —
조사서가 이론이 요구하는 것을 기록하지 않고 있거나, 우리 제약이 과도하거나.
어느 쪽인지는 실패한 조항을 보면 갈린다. C-3 이 과대 제약이었던 것을 그렇게 찾았다.
