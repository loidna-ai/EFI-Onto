# TBox 절 이력 — 재편 전의 절 제목과 남은 정리거리

재편 2단계에서 TTL 의 절 제목을 주제 기준으로 바꿨다. 이전 절 제목은 작업 순서와
고친 기록이었다 — '원인 축 편향 교정 2차', '사슬에 안 붙어 있던 어휘 셋을 붙인다'
같은 것들이다. TTL 에서는 사라졌지만 왜 그 어휘가 생겼는지는 남아야 하므로 옮겨 둔다.

## 재편 전 절 제목

  EFI-Onto : Electrical Fire Ignition Ontology — TBox v0.1
  전기화재 발화 메커니즘 판정 온톨로지 (FIReAct 연계용)
  표현 : OWL 2 DL (Turtle) + SHACL Advanced(규칙) + SKOS(용어 정렬)
  방법론: Noy & McGuinness, Ontology Development 101 (Stanford KSL-01-05)
  정렬  : BFO 2.0 · RO · SOSA/SSN · PROV-O · OWL-Time · QUDT
  주의  : 지지점수(supportScore)는 확률이 아니며 퍼센트 기호 없이 0~100 정수로 표기 (논문 3.2절)
- 0. 상위 정렬 (BFO 2.0)
  BFO_0000015 process · BFO_0000040 material entity · BFO_0000019 quality
  BFO_0000016 disposition · IAO_0000030 information content entity
- 1. 축 ①  발열 메커니즘 (HeatingMechanism ⊑ bfo:process)
- 2. 축 ②  물리 증거물 (PhysicalEvidence ⊑ bfo:material entity) + 손상 양상(quality) + 현장 증거
- 3. 축 ③  선행 조건 (AntecedentCondition)
- 4. 축 ④  최초 착화물 (FirstFuelIgnited)
- 5. 보조 축  관측(SOSA) · 행위자/활동(PROV-O) · 상태 열거
- 6. 시나리오(가설) 클래스 — 논문 6개 감별 범주. 메커니즘으로 정의(≡), 선행조건은 필요조건(⊑)
  국내 분류의 나머지 셋(과부하·과전류, 누전·지락, 층간단락)은 48절에. 미확인 단락은 가설이 아니라 분류다.
- 7. 객체 속성 (인과·의존·증거·출처)
- 8. 데이터 속성 (물리 수치·상태)  — 단위는 이름 접미어 + QUDT 참조
- 9. 지표 규칙 인스턴스 (논문 Table 2). scoreDelta는 예시값 — 실제 루브릭 값으로 교체
- 10. SHACL 규칙·제약 (폐세계 검증 — 반증 및 소거법 오류 방지)
  [부가 모듈 A] 한글 라벨
  [부가 모듈 B] 형태학적 중첩 (morphological overlap)
  ---------------------------------------------------------------------------
  근거: 논문 4.2절 — 오분류는 무작위가 아니라 '비시각적 변별 축을 공유하는
  가설 쌍'에 구조적으로 집중된다 (절연열화↔압착손상 64회, 트래킹↔접촉불량 66회).
  모델링 원칙:
  - canManifest 는 '이 가설이 남길 수 있는 손상 양상'의 가능 집합이며,
  정의 조건(hasMechanism)이나 단서 규칙(IndicatorRule)과 층위가 다르다.
  - 두 가설의 canManifest 교집합이 곧 사진만으로는 갈리지 않는 지대다.
  - 따라서 변별력은 손상 양상 자체의 성질(sharedByCount)로 계산된다.
  [부가 모듈 C] 축 간 인과 연결
  ---------------------------------------------------------------------------
  선행조건 --enables--> 발열메커니즘 --producesDamage--> 손상양상
  └--ignites--> 착화물
  물리증거물 --exhibits--> 손상양상      현장사실 --attests--> 선행조건
  네 축을 분리한 이유는 섞이지 않게 하기 위해서지, 끊어 두기 위해서가 아니다.
  분리한 축은 명시적 관계로만 이어지며, 그 경로가 곧 감식 논리의 추적 경로가 된다.
- 11. 정의로 도출되는 사실 (D-1~D-3)
  임계값이 아니라 관계 비교다. 두 수치의 대소·동일 여부만으로 결정되므로
  감별 루브릭이 없어도 성립한다. OWL 은 두 데이터 속성을 비교하지 못하므로
  SHACL 로 쓴다.
  축을 넘지 않는다 — 물리 증거물에 대한 판정은 물리 증거물 쪽에만 남긴다.
  이 사실이 어느 선행 조건을 증언하는지는 루브릭 사항이며 여기서 정하지 않는다.
- 12. NFPA 921 (2024) 조항 대조
  방법론 층(SHACL 제약·규칙)에만 붙인다.
  지표 규칙 25개는 NFPA 가 아니라 논문 Table 2 · 국내 실무·선행연구에서 왔다.
  거기에 조항을 붙이면 출처가 왜곡되므로 붙이지 않는다.
  절 수준까지만 대조했다 — 하위 절 번호는 원문 확인 후 좁힌다.
- 13. 아크 조사 (NFPA 921 §9.13)
  회로의 아크 지점을 계통적으로 찾아 발화부 판정과 확산 경로 해석에 쓴다.
  어휘(ArcMapPoint, locatedInOriginArea)만 있고 절차가 없던 부분을 채운다.
- 14. 화재 분류 (NFPA 921 §19.8)
  분류는 원인 판정과 다른 일이며 원인 판정이 끝난 뒤에 온다 (§19.8.2).
  범주 목록은 이 온톨로지가 정하지 않는다 — 관할이 쓰는 외부 분류 체계를
  참조하도록만 한다 (§19.8.1). 범주를 여기서 열거하면 체계마다 다른 정의를
  하나로 뭉개게 된다.
- 15. 의견 확신도 (NFPA 921 §4.5)
  '개연(probable)'은 확률값이 아니라 경합 가설 대비 유일하게 앞선 상태로
  구현한다. supportScore 를 확률로 읽으면 논문 3.2절 원칙을 깨뜨린다.
- 16. 검토 절차 (NFPA 921 §4.6) · 보고 (§4.7)
  세 검토는 이름이 다른 게 아니라 보증하는 것이 다르다.
  행정 검토 = 절차·서류 구비 여부. 실질 비평을 하지 못한다 (§4.6.1.1)
  기술 검토 = 실질 비평. 자격과 자료 접근이 전제 (§4.6.2)
  동료 검토 = 독립성·객관성. 결과에 이해관계가 없어야 한다 (§4.6.3)
- 17. 인입 계통·접지 (NFPA 921 §9.3~§9.6)
  전압·인입 방식·계량기는 배경 지식이라 넣지 않는다. 넣어도 판정에 쓰이지 않아
  어휘만 남는다. 감식에 실제로 쓰이는 셋만 옮긴다.
  §9.3.4  인입구는 과전류 보호가 없어 고장이 지속된다
  §9.5.1.1 본딩은 저임피던스 경로로 보호장치를 제때 동작시킨다
  §9.5.2  중성선 단선은 과전압을 만들고, 접지극 제거가 그 원인이 아니다
- 18. 과학적 방법 (NFPA 921 §4.3)
  반증 우선(P3)은 §4.3.6 에서 이미 가져왔다. 여기서는 그 앞뒤 요건을 채운다.
  §4.3.4   수집한 자료는 최종 가설 형성 전에 전부 분석돼야 한다
  §4.3.6   모든 가설을 시험해 유일하게 정합적인 하나가 남을 때까지 계속한다
  하나도 견디지 못하면 원인미상으로 둔다
  §4.3.6.1 자료 부재 위에 세운 가설은 시험 불가능하므로 무효다
  반증되지 않았다는 것이 참이라는 뜻은 아니다
  §4.3.7   대안 가설을 고려하지 않는 것은 중대한 오류다
  §4.3.8   자료가 모이기 전에는 어떤 가설도 세우거나 시험할 수 없다
- 19. 원인 가설 수립·검증 (NFPA 921 §19.4~§19.7)
  소거법 금지(C-2)와 반증 우선은 이미 있다. 여기서는 그 위의 요건을 채운다.
  §19.5.1   발화부의 발열 기기는 쉽게 배제되더라도 반드시 목록에 올린다
  §19.6.3   가설 검증에서 답해야 할 질문 넷
  §19.6.5.1 둘 이상이 기각되지 않아도 원인미상이다
  §19.6.5.2 발화원과 최초 착화물을 짚은 것만으로는 원인이 아니다
- 20. 전기 에너지에 의한 발화 (NFPA 921 §9.9)
- 21. 방열 저해 조건 (NFPA 921 §9.9.1.2 · §9.9.2.2 · §9.9.3.2)
  원문의 물리 논의(와트·온도·지속 시간)는 가설을 시험할 때 참조하는 지식이지
  현장에서 관측하는 대상이 아니다. 관측 가능한 형태는 '열이 빠져나가지 못하는
  상태였는가'이고, 그것만 담는다.
  같은 전류가 흘러도 방열이 막히면 발화하고 아니면 하지 않는다.
- 22. 아크의 연료별 착화 역량 (NFPA 921 §9.9.4.1 · §9.9.4.4)
  아크 경로 안의 온도는 수천 도지만, 짧고 국부적이라 많은 연료를 착화시키지
  못한다. 목재 구조재 같은 벌크 고체는 통상 착화되지 않고, 표면적/질량비가
  큰 연료와 가스·증기·분진만 붙는다. F-3 은 온도만 보므로 이 축이 따로 필요하다.
- 23. 전기 계통 손상 해석 (NFPA 921 §9.10 · §9.11)
- 24. 손상 도체 식별의 통념들 (NFPA 921 §9.11.3~§9.11.6)
  원문이 "…라고 여겨져 왔으나" 로 시작해 부정하는 대목들이다.
  반증 근거는 지어내기 어려운데 원문이 직접 준다.
- 25. 전기 계통 검사 (NFPA 921 §9.12)
  대부분 현장 작업 절차다(안전 확보·LOTO·촬영). 온톨로지가 담을 것은
  검사 범위가 관심 영역에 전원을 공급하는 계통 전체를 포함했는가이다.
- 26. 발화 순서 기여 요인 (NFPA 921 §19.4.4.2.1)
  발화 순서 설명에 반드시 포함돼야 할 일곱 가지. 원문이 열거해 준 체크리스트라
  지어낼 것이 없다. 어느 하나라도 답하지 않으면 발화 순서를 설명한 것이 아니다.
- 27. 발화원 미발견 시 추론 (NFPA 921 §19.4.4.3)
  원인 판정은 증거에 근거해야지 증거의 부재에 근거해서는 안 된다. 다만 발화원을
  찾지 못했어도 발화 순서를 논리적으로 추론할 수 있는 제한적 상황이 있다.
  그 상황에 해당하지 않으면 추론해서는 안 된다.
- 28. 확증 편향과 가설 검증 수단 (NFPA 921 §4.3.10 · §4.6.2.1 · §19.6.4)
- 29. 구조 점검으로 드러난 끊긴 사슬 (scripts/lint.py)
  선언만 하고 사슬에 붙이지 않은 어휘들이다. 확인해도 어떤 가설로도
  이어지지 않으므로 판정에 기여하지 못한다.
- 30. 발화 전 아크·불꽃 목격
  사례 실측에서 드러난 빈 곳이다. PreFireAnomaly 아래에 조명 깜박임·누전차단기
  동작·온도 이상은 있었으나 '배선에서 불꽃을 봤다'가 없었다.
  축은 현장 사실이다. 선행 조건이 아니라 관측이며, 통전 사실을 증언한다.
  발화 전 아크를 목격했다면 그 시점에 회로가 살아 있었다는 뜻이다.
- 31. 반단선의 사슬을 단락까지 잇는다
  공식 발화요인 분류는 '반단선에 의한 단락'이라고 적는다. 압착손상·절연열화도
  마찬가지로 '~에 의한 단락'이다. 즉 셋 다 단락으로 귀결되고, 변별은 그 단락을
  부른 원인에서 나온다.
  우리는 반단선을 저항 발열과 직렬 아크에서 끝내 두어 단락까지 가지 않았다.
  문헌이 그 사이를 메운다 — 반단선부의 접촉저항으로 국부 발열이 일어나
  피복이 절연 파괴되고 선간 단락에 이른다.
  반복 굴곡·진동 → 소선 파단 → 접촉저항 발열 → 피복 절연파괴 → 선간 단락
  (여기까지만 모형화돼 있었다)
  이 사슬이 이어지면 단락흔이 세 가설 모두에서 나온다는 것이 구조로 설명된다.
  사례 실측에서 단락흔의 변별력이 27% 에 그친 것과 일치한다.

## 같은 주어가 여러 블록에 흩어진 것 — 3단계에서 합친다

재편으로 한자리에 모였다. 합치면서 서로 어긋난 주석이 드러날 수 있다.
**2단계에서 고치지 않았다** — 옮기는 것과 고치는 것을 섞으면 무엇이 무엇을
바꿨는지 알 수 없다. 2단계는 동형이어야 한다.

| 주어 | 블록 수 |
|---|---:|
| `efi:ExternalFlameExposure` | 24 |
| `efi:ExternalFlameScenario` | 24 |
| `efi:PoorContactScenario` | 13 |
| `efi:PartialDisconnectionScenario` | 11 |
| `efi:PoorContactHeating` | 10 |
| `efi:GlowingConnection` | 9 |
| `efi:InsulationBreakdownArc` | 9 |
| `efi:PartialDisconnectionHeating` | 9 |
| `efi:Conductor` | 8 |
| `efi:CrushDamageScenario` | 8 |
| `efi:CrushInducedArc` | 8 |
| `efi:InsulationDegradationScenario` | 8 |
| `efi:OverloadHeating` | 8 |
| `efi:TrackingScenario` | 8 |
| `efi:ArcTracking` | 7 |
| `efi:ConnectionPoint` | 7 |
| `efi:ElectricalHeatingMechanism` | 6 |
| `efi:FlickeringOrOdor` | 6 |
| `efi:Insulation` | 6 |
| `efi:InterTurnShortCircuit` | 6 |
| `efi:LeakageCurrentHeating` | 6 |
| `efi:PartialDisconnectionInducedArc` | 6 |
| `efi:SeriesArc` | 6 |
| `efi:Vibration` | 6 |
| `efi:AgedInsulation` | 5 |
| `efi:DustAccumulation` | 5 |
| `efi:ExternalCrushing` | 5 |
| `efi:InsulationDeterioration` | 5 |
| `efi:IntermittentContactSeparation` | 5 |
| `efi:IntermittentRcdTripping` | 5 |
| `efi:MisdrivenStaple` | 5 |
| `efi:MoistureExposure` | 5 |
| `efi:ResistiveHeating` | 5 |
| `efi:ShortCircuitArc` | 5 |
| `efi:AbnormalTemperatureOrVoltageDrop` | 4 |
| `efi:AbrasionAtPenetration` | 4 |
| `efi:AccumulatedDustFuel` | 4 |
| `efi:EnergizedState` | 4 |
| `efi:HammerMisHitDamage` | 4 |
| `efi:LooseConnection` | 4 |
| `efi:OverloadState` | 4 |
| `efi:ProtectiveDevice` | 4 |
| `efi:RepeatedFlexing` | 4 |
| `efi:SalineOrChemicalExposure` | 4 |
| `efi:StrandedConductor` | 4 |
| `efi:ArcMapPoint` | 3 |
| `efi:BreakerTripRecord` | 3 |
| `efi:BurnPattern` | 3 |
| `efi:ContaminatedEnvironment` | 3 |
| `efi:ContaminationDeposit` | 3 |
| `efi:CorrodedConnection` | 3 |
| `efi:ElectricalArtifact` | 3 |
| `efi:Enclosure` | 3 |
| `efi:EnclosureMaterialFuel` | 3 |
| `efi:ExternalForceTrace` | 3 |
| `efi:FlammableVaporFuel` | 3 |
| `efi:FlexingHistoryWithStrandFracture` | 3 |
| `efi:GroundFaultHeating` | 3 |
| `efi:GroundFaultScenario` | 3 |
| `efi:HeatDissipationImpairment` | 3 |
| `efi:ImmediateTripAfterExternalForce` | 3 |
| `efi:InsufficientContactPressure` | 3 |
| `efi:InsulationMaterialFuel` | 3 |
| `efi:InterTurnShortScenario` | 3 |
| `efi:LongTermRepeatedStress` | 3 |
| `efi:MoistureTrace` | 3 |
| `efi:MultipleArcBeadsAtOrigin` | 3 |
| `efi:OrganicInsulationPresent` | 3 |
| `efi:OverloadScenario` | 3 |
| `efi:PaperTextileFuel` | 3 |
| `efi:PlugReceptacle` | 3 |
| `efi:PrimaryArcMark` | 3 |
| `efi:ReducedContactArea` | 3 |
| `efi:ReducedInsulationResistance` | 3 |
| `efi:RodentGnawing` | 3 |
| `efi:SolidConductor` | 3 |
| `efi:Tension` | 3 |
| `efi:TerminalBlock` | 3 |
| `efi:ThermalDegradation` | 3 |
| `efi:ThermalInsulationFuel` | 3 |
| `efi:WoodStructuralFuel` | 3 |
| `efi:AIAgent` | 2 |
| `efi:AbnormalLampBrightnessReport` | 2 |
| `efi:AdjacentCombustible` | 2 |
| `efi:AlloyConductor` | 2 |
| `efi:AlloyConductorArcMarkShape` | 2 |
| `efi:AntecedentCondition` | 2 |
| `efi:ApplianceEntryPoint` | 2 |
| `efi:ArcBead` | 2 |
| `efi:ArcEvent` | 2 |
| `efi:ArcHeating` | 2 |
| `efi:ArcMarkAwayFromOriginShape` | 2 |
| `efi:ArcMarkSequenceRuleShape` | 2 |
| `efi:ArcMeltMark` | 2 |
| `efi:ArcOriginIndicationRuleShape` | 2 |
| `efi:BundledWiringTrace` | 2 |
| `efi:BurnCenterOnSurface` | 2 |
| `efi:CapacitorSite` | 2 |
| `efi:CarbonizedConductivePath` | 2 |
| `efi:CelluloseFuel` | 2 |
| `efi:Conclusion` | 2 |
| `efi:ConclusionShape` | 2 |
| `efi:ConductiveSolutionInCrack` | 2 |
| `efi:ConfirmationStatus` | 2 |
| `efi:ConnectionCondition` | 2 |
| `efi:ConnectionJointSite` | 2 |
| `efi:ContaminatedContactSurface` | 2 |
| `efi:CordMidspanSite` | 2 |
| `efi:CuprousOxideDerivationRuleShape` | 2 |
| `efi:CuprousOxideGrowth` | 2 |
| `efi:DamagePattern` | 2 |
| `efi:DeEnergizedState` | 2 |
| `efi:DeformedPlugOrSwitch` | 2 |
| `efi:DerivedManifestationRuleShape` | 2 |
| `efi:DeviceInteriorSite` | 2 |
| `efi:ElectricalIgnitionScenario` | 2 |
| `efi:ElectricalState` | 2 |
| `efi:EnvironmentalCondition` | 2 |
| `efi:FactShape` | 2 |
| `efi:FalsificationRuleShape` | 2 |
| `efi:FireExposureEvent` | 2 |
| `efi:FireMeltMark` | 2 |
| `efi:FirstFuelIgnited` | 2 |
| `efi:ForeignMatterInclusion` | 2 |
| `efi:Fuse` | 2 |
| `efi:GeneralMelting` | 2 |
| `efi:GroundFaultProtectionRuleShape` | 2 |
| `efi:GroundPath` | 2 |
| `efi:GroundedMetalwork` | 2 |
| `efi:HeatingMechanism` | 2 |
| `efi:HemisphericalMeltShape` | 2 |
| `efi:Ignitability` | 2 |
| `efi:IgnitionCompetenceRuleShape` | 2 |
| `efi:IgnitionScenario` | 2 |
| `efi:IndicatorRole` | 2 |
| `efi:IndicatorRule` | 2 |
| `efi:Instrument` | 2 |
| `efi:InsulationCarbonization` | 2 |
| `efi:InsulationCondition` | 2 |
| `efi:InsulationEmbrittlement` | 2 |
| `efi:InsulationResistanceDerivationRuleShape` | 2 |
| `efi:InsulationResistanceObservation` | 2 |
| `efi:InterPoleInsulatingSurface` | 2 |
| `efi:InvestigationSession` | 2 |
| `efi:InvestigatorAgent` | 2 |
| `efi:LargeMeltMark` | 2 |
| `efi:LocalizedDiscoloration` | 2 |
| `efi:LongTermTerminalHeating` | 2 |
| `efi:LossOfLuster` | 2 |
| `efi:LowGroundResistanceAtFaultPath` | 2 |
| `efi:LusterAbsenceShape` | 2 |
| `efi:MechanicalDeformation` | 2 |
| `efi:MechanicalStressHistory` | 2 |
| `efi:MeltBoundaryRuleShape` | 2 |
| `efi:MeltMark` | 2 |
| `efi:MetallographyAloneShape` | 2 |
| `efi:MorphologicalAmbiguityRuleShape` | 2 |
| `efi:MorphologyDiscriminationRuleShape` | 2 |
| `efi:MorphologyOnlyConclusionShape` | 2 |
| `efi:MultipleApplianceMalfunction` | 2 |
| `efi:MultipleArcBeads` | 2 |
| `efi:NoArcOrSpatter` | 2 |
| `efi:NonElectricalHeatingMechanism` | 2 |
| `efi:NormalInsulationResistance` | 2 |
| `efi:Observation` | 2 |
| `efi:OpenNeutral` | 2 |
| `efi:OpenNeutralOvervoltage` | 2 |
| `efi:OverloadDerivationRuleShape` | 2 |
| `efi:PartialDisconnectionDerivationRuleShape` | 2 |
| `efi:PhysicalEvidence` | 2 |
| `efi:PlugJunctionArea` | 2 |
| `efi:PostFireDamageShape` | 2 |
| `efi:PreFireAnomaly` | 2 |
| `efi:PreFireArcObservation` | 2 |
| `efi:ProtectiveDeviceFailedToOperate` | 2 |
| `efi:ProtectiveDeviceOperationRuleShape` | 2 |
| `efi:PureAluminumConductor` | 2 |
| `efi:QueryDerivationRuleShape` | 2 |
| `efi:RefutationEvidenceShape` | 2 |
| `efi:Sagging` | 2 |
| `efi:ScenarioShape` | 2 |
| `efi:SceneEvidence` | 2 |
| `efi:SecondaryArcMark` | 2 |
| `efi:SelfFuel` | 2 |
| `efi:SmallMeltBallOnStrandEnd` | 2 |
| `efi:SmoothLustrousMeltSurface` | 2 |
| `efi:Spatter` | 2 |
| `efi:StrandFracture` | 2 |
| `efi:StrandFractureAtStressPoint` | 2 |
| `efi:StrandFractureDerivationRuleShape` | 2 |
| `efi:StressConcentrationPoint` | 2 |
| `efi:SupportScoreRuleShape` | 2 |
| `efi:SustainedFaulting` | 2 |
| `efi:TerminalSite` | 2 |
| `efi:ThermalGradientFlow` | 2 |
| `efi:ThermalInsulationTrace` | 2 |
| `efi:Verdict` | 2 |
| `efi:VerificationQuery` | 2 |
| `efi:WholeConductorCrushedOrCut` | 2 |
| `efi:Winding` | 2 |
| `efi:WindingSite` | 2 |
| `efi:WiringDeviceSite` | 2 |
| `efi:furthestDownstream` | 2 |
