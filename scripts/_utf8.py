# -*- coding: utf-8 -*-
"""출력이 한글이므로 stdout 을 utf-8 로 고정한다.

Makefile 은 PYTHONIOENCODING 을 넘기지만 스크립트를 직접 부르면 Windows 는
cp949 로 쓰다가 em-dash 하나에 죽는다. 실제로 status.py 가 그랬다.
불러오는 것만으로 효과가 있다 — 부수효과가 목적인 모듈이다.
"""
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")
