# EFI-Onto

전기화재 발화 메커니즘 판정 온톨로지 (OWL 2 DL + SHACL).
FIReAct 논문의 NFPA 921 기반 감별 절차를 정형화한 것.

## 빠른 시작

```bash
make install
make test      # 13개 회귀 시험
make build     # 시각화·검토표 생성 → build/
```

## 산출물

| 파일 | 용도 |
|---|---|
| `build/EFI-Onto_그래프.html` | 인터랙티브 관계도 (형태 중첩 / 가설-증거 / 전체 클래스) |
| `build/EFI-Onto_TBox_구조도.html` | 설계 전체를 훑는 문서형 화면 |
| `build/EFI-Onto_검토표.xlsx` | 조사관 검토용. 판단 기준 301개를 한글 문장으로 |
| `build/EFI-Onto.graphml` | Cytoscape / Gephi / yEd 용 |
| `build/EFI-Onto_인과사슬.svg` | 논문 삽입용 벡터 도식 |

`ontology/efi_tbox.ttl` 은 Protégé, WebVOWL, GraphDB 에서 그대로 열린다.

## 설계와 주의사항

`CLAUDE.md` 참조. 특히 **검증되지 않은 것** 절을 먼저 읽을 것.

## 다음 과제

- [ ] `scoreDelta` 를 실제 감별 루브릭으로 교체
- [ ] NFPA 921 (2024) 조항 번호 대조
- [ ] 실무Ⅳ 목차 대조에서 나온 후보 7개 (`make silmu`) — 극별 용융 위치부터
- [ ] 조사관 검토표 회수 및 반영
- [ ] 조사서 사례 ABox 변환 (10건 → 150건)
- [ ] OWL / SHACL 파일 분리 (Protégé 편집 편의)
