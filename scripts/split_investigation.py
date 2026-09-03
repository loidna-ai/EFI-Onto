# -*- coding: utf-8 -*-
"""조사 기록 어휘를 efi_investigation.ttl 로 옮긴다 (재편 1단계). 한 번만 쓴다.

기준은 하나다 — **점수·반증·형성(D-15)·결론(C-)에 닿는가.**
닿으면 추론이므로 tbox 에 남고, 기록의 완비만 검사하면 investigation 으로 간다.

옮기는 것은 50절부터 끝까지(T01~T16)이고 결론 제약 둘만 남긴다.
손으로 옮기지 않는다. 옮긴 뒤 `make iso` 가 동형이어야 한다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import pathlib
import ttlblocks as tb

ROOT = pathlib.Path(__file__).resolve().parents[1]
TBOX = ROOT / "ontology" / "efi_tbox.ttl"
INVEST = ROOT / "ontology" / "efi_investigation.ttl"

FIRST_SECTION = "# 50. 조사 계통"
STAY = {"efi:ConclusionFirstFuelEvidenceShape", "efi:ConclusionHeatTransferEvidenceShape"}

HEADER = """\
# ============================================================================
#  EFI-Onto : 조사 기록 층 (T01~T16)
#  출처가 있는 현장 기록의 어휘와 완비 검사. efi_tbox.ttl 과 한 그래프를 이룬다.
#
#  **이 파일의 자원은 점수·반증·형성·결론에 닿지 않는다.** 기록이 갖춰졌는지만
#  본다. 완비는 원인 판정이 아니다 — 연결이 확인돼도 통전이 아니고, 토크 기록이
#  있어도 체결 상태가 유지됐다는 뜻이 아니다. 판정에 닿는 도형은 efi_tbox.ttl 에
#  둔다(결론 제약 ConclusionFirstFuelEvidenceShape·ConclusionHeatTransferEvidenceShape).
#  경계는 tests/test_ontology.py 의 test_investigation_layer_never_touches_scoring 이 지킨다.
# ============================================================================
"""


def main():
    text = TBOX.read_text(encoding="utf-8")
    blocks = tb.cut(text)
    head_end = max(i for i, b in enumerate(blocks) if "@prefix" in b or "a owl:Ontology" in b) + 1
    start = next(i for i, b in enumerate(blocks) if FIRST_SECTION in b)

    head = "".join(blocks[:head_end])
    prefixes = "".join(l + chr(10) for l in head.split(chr(10)) if l.startswith("@prefix"))
    keep = blocks[:start] + [b for b in blocks[start:] if tb.subject(b) in STAY]
    move = [b for b in blocks[start:] if tb.subject(b) not in STAY]

    TBOX.write_text(tb.join(keep), encoding="utf-8", newline="\n")
    INVEST.write_text(HEADER + "\n" + prefixes + "\n" + tb.join(move), encoding="utf-8", newline="\n")
    print(f"tbox {len(keep)} 블록 · investigation {len(move)} 블록 → {INVEST.name}")


if __name__ == "__main__":
    main()
