# -*- coding: utf-8 -*-
"""TTL 을 주어 블록으로 자른다. 재편의 도구이며 손으로 옮기지 않기 위한 것이다.

블록 = 앞선 주석·빈 줄 + 주어 첫 줄부터 문장을 닫는 '.' 까지.

**줄 단위로 자르면 안 된다.** SPARQL 규칙이 전부 삼중 따옴표 안에 있고
문자열을 닫는 따옴표와 문장의 마침표가 한 줄에 같이 온다. 줄 단위 파서는 이 마침표를
놓쳐 블록 여럿을 하나로 뭉친다 — 실제로 D-15 가 50절의 기록 클래스에 붙어
있었고 왕복 검사도 섞기 검사도 그것을 잡지 못했다(뭉친 채로 함께 움직이므로).
그래서 문자 단위로 훑는다. 소수점(0.7)은 뒤에 숫자가 오므로 문장 끝이 아니다.

  python scripts/ttlblocks.py    왕복·블록 수를 확인한다
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import pathlib, re


def cut(text):
    """[블록…] 으로 자른다. 이어 붙이면 원본과 바이트 단위로 같다."""
    blocks, start, i, n, depth = [], 0, 0, len(text), 0
    while i < n:
        c = text[i]
        if c == "#":                                    # 주석은 줄 끝까지
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith('"""', i):                 # 삼중 따옴표 문자열
            j = text.find('"""', i + 3)
            i = n if j < 0 else j + 3
        elif c == '"':                                  # 한 줄 문자열
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif c == "<" and 0 <= text.find(">", i) and "\n" not in text[i:text.find(">", i)]:
            i = text.find(">", i) + 1                   # IRI
        elif c in "[(":
            depth += 1; i += 1
        elif c in "])":
            depth -= 1; i += 1
        elif c == "." and depth == 0 and (i + 1 >= n or text[i + 1] in " \t\r\n"):
            j = text.find("\n", i)
            end = n if j < 0 else j + 1
            blocks.append(text[start:end])
            start = i = end
        else:
            i += 1
    if start < n:
        blocks.append(text[start:])
    return blocks


def subject(block):
    """블록의 주어를 낸다. 접두어 선언이나 빈 노드로 시작하면 None."""
    for line in block.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("@"):
            continue
        m = re.match(r"^(<[^>]+>|[A-Za-z][\w.-]*:[^\s;,]*)", s)
        return m.group(1) if m else None
    return None


def join(blocks):
    return "".join(blocks)


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parents[1]
    for p in sorted((root / "ontology").glob("*.ttl")):
        text = p.read_text(encoding="utf-8")
        bs = cut(text)
        named = sum(1 for b in bs if subject(b))
        print(f"{p.name}: 블록 {len(bs)} (주어 있음 {named}) "
              f"왕복 {'같다' if join(bs) == text else '다르다'}")
        if join(bs) != text:
            raise SystemExit("왕복 실패 — 파서를 고치기 전에는 쓰지 않는다")
