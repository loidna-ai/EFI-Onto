# -*- coding: utf-8 -*-
"""TTL 을 주어 블록으로 자른다. 재편의 도구이며 손으로 옮기지 않기 위한 것이다.

블록 = 앞선 주석·빈 줄 + 주어 첫 줄부터 문장을 닫는 '.' 까지.
파일이 '한 줄에 한 주어' 규칙을 지키므로 가능하다. 삼중 따옴표 안의 마침표는
문장 끝이 아니다 — SPARQL 규칙이 전부 그 안에 있다.

왕복(cut → join)이 원본과 바이트 단위로 같아야 한다. 아니면 쓰지 않는다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import pathlib, re

def cut(text):
    """(머리말, [블록…]) 로 자른다. 머리말은 접두어 선언과 owl:Ontology 까지."""
    lines = text.split("\n")
    blocks, cur, in_str, depth = [], [], False, 0
    for line in lines:
        cur.append(line)
        # 삼중 따옴표는 한 줄에 여러 번 나올 수 있다. 홀수면 상태가 바뀐다.
        if line.count('"""') % 2:
            in_str = not in_str
        if in_str:
            continue
        stripped = _strip_literals(line).rstrip()
        if stripped.endswith(".") and not stripped.endswith("..") and depth == 0:
            if not stripped.lstrip().startswith("#"):
                blocks.append("\n".join(cur))
                cur = []
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _strip_literals(line):
    """문자열 리터럴 안의 마침표를 문장 끝으로 오인하지 않도록 지운다."""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "#" and not out[-1:] == ["\\"]:
            break
        if c == '"':
            i += 1
            while i < n and line[i] != '"':
                i += 2 if line[i] == "\\" else 1
        elif c == "<":
            while i < n and line[i] != ">":
                i += 1
        else:
            out.append(c)
        i += 1
    return "".join(out)


def subject(block):
    """블록의 주어를 낸다. 빈 노드로 시작하면 None."""
    for line in block.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(<[^>]+>|[A-Za-z][\w.-]*:[^\s]*|\[)", s)
        return None if not m or m.group(1) == "[" else m.group(1)
    return None


def join(blocks):
    return "\n".join(blocks)


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parents[1]
    for p in sorted((root / "ontology").glob("*.ttl")):
        text = p.read_text(encoding="utf-8")
        bs = cut(text)
        ok = join(bs) == text
        named = sum(1 for b in bs if subject(b))
        print(f"{p.name}: 블록 {len(bs)} (주어 있음 {named}) 왕복 {'같다' if ok else '다르다'}")
        if not ok:
            raise SystemExit("왕복 실패 — 파서를 고치기 전에는 쓰지 않는다")
