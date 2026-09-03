# EFI-Onto

전기화재 발화 메커니즘 판정 온톨로지 (OWL 2 DL + SHACL).
FIReAct 논문의 NFPA 921 기반 감별 절차를 정형화한 것.

## 빠른 시작

```bash
make install
make test      # 회귀 시험 및 OWL/SHACL 정합성 검사
make build     # 시각화·검토표 생성 → build/
make backlog   # 원문 이식 미완료 목록·근거·누락 검사
```

## 산출물

| 파일 | 용도 |
|---|---|
| `build/EFI-Onto_그래프.html` | 인터랙티브 관계도 (형태 중첩 / 가설-증거 / 전체 클래스) |
| `build/EFI-Onto_TBox_구조도.html` | 설계 전체를 훑는 문서형 화면 |
| `build/EFI-Onto_검토표.xlsx` | 현재 온톨로지의 판단 기준을 한글 문장으로 정리한 조사관 검토표 |
| `build/EFI-Onto.graphml` | Cytoscape / Gephi / yEd 용 |
| `build/EFI-Onto_인과사슬.svg` | 논문 삽입용 벡터 도식 |

`ontology/` 의 TTL 둘은 Protégé, WebVOWL, GraphDB 에서 그대로 열린다. `efi_tbox.ttl` 이 추론 어휘, `efi_investigation.ttl` 이 조사 기록 층이며 함께 읽으면 한 그래프다.

전원·보호장치·시간선·최초 착화물 입력은 [T01~T04 구현 안내](docs/T01_T04_구현.md)를 참조한다.
합성 입력을 실행하려면 `python scripts/investigate.py examples/investigation_t01_t04.json`.

비교 관찰·조사 계획·검토 범위·금속분 부착은 [T05·T06·T12 구현 안내](docs/T05_T06_T12_구현.md)를 참조한다.
`python scripts/investigate.py examples/investigation_t05_t06_t12.json`으로 완료 주장과 추가 확인 질문을 확인할 수 있다.

접속 구조·나사 재질·제품별 토크 대조는 [T07 구현 안내](docs/T07_구현.md)와
`python scripts/investigate.py examples/investigation_t07.json`에서 확인할 수 있다.

절연 재질·충전재와 가열·표면 수분 이력은 [T14 구현 안내](docs/T14_구현.md)와
`python scripts/investigate.py examples/investigation_t14.json`에서 확인할 수 있다.

도체·접점의 모재·도금과 문헌 적용 범위 대조는 [T15 구현 안내](docs/T15_구현.md)와
`python scripts/investigate.py examples/investigation_t15.json`에서 확인할 수 있다.

허용전류·도체 크기·절연·다발·보호장치 정격의 출처별 대조는 [T16 구현 안내](docs/T16_구현.md)와
`python scripts/investigate.py examples/investigation_t16.json`에서 확인할 수 있다.

## 설계와 주의사항

`CLAUDE.md` 참조. 특히 **검증되지 않은 것** 절을 먼저 읽을 것.

## 다음 과제

원문 이식의 현재 작업 목록은 [TBox 미완료 목록](docs/TBox_미완료_목록.md)에서 관리한다.
원문별 ‘일부·없음’ 행을 작업에 연결하고 구현대기·설계검토·기존보류·자료대기·범위제외를 구분했다.
테스트 통과나 과거 후보의 반영 완료를 원문 전체 이식 완료로 세지 않는다.

- [x] 가감점 유도 및 150건 평가: 일치 126·오판 8·판단보류 16 (84.0%). 라벨에 맞춰 가중치를 보정하지 않음
- [x] NFPA §9.4·9.7·9.8·9.12 본문 대조, 재질·산화·부식 입력 구분, TIA 24-1 반영
- [x] 원문 대조표의 미완료 행 감사와 중복 작업 정리 (`make backlog`)
- [x] T01 관련 전원·회로·단자·부하 연결 → T02 보호장치 상태·조작 → T03 공급원별 시간선
- [x] T04 최초 착화물·열전달 근거 (후보의 미확인은 허용, 결론에서는 근거 요구)
- [x] T05 비교 관찰 → T06 조사 문제·검토 범위 → T12 비산 금속의 후속 절연 오염
- [x] T07 접속 방식·나사 재질·체결값의 적용 조건과 측정 시점 검증
- [x] T14 습윤 PVC의 재질·충전재·가열·수분 이력과 발화 전 선후 검증
- [x] T15 도체·접점 금속·도금과 산화 특성 문헌의 설치 조건별 적용 범위 검증
- [x] T16 허용전류·도체 크기·절연·다발 조건과 외부 적용 기준의 관할·판본별 대조
- [ ] T17 본딩 경로와 임피던스 근거 설계검토
- [ ] 조사서 서식 제안 회수 (반례 사건번호 형식)
- [ ] 조사관 검토표 회수 및 반영
- [ ] 외부화염·과부하·누전지락·층간단락의 신규 라벨 사례와 시간·재질 기록 확보
- [ ] 조사서 사례 ABox 변환 (10건 → 150건)
- [ ] OWL / SHACL 파일 분리 (Protégé 편집 편의)
