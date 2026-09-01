# -*- coding: utf-8 -*-
"""판독기를 둘로 나눈다 — 사전 판독과 LLM 판독을 나란히 잰다.

왜 나누는가
  조사서에서 사실을 뽑는 일과 그 사실로 판정하는 일은 다른 일이다. 그런데 한
  숫자만 보면 갈리지 않는다. 실제로 두 번 잘못 짚었다 — 사전이 못 읽은 것을
  '조사서에 없다'고 읽었고, 그 위에서 온톨로지의 한계를 논했다.

  판독을 갈라 두면 세 숫자가 나온다.
    사전 판독 정확도    투명하고 재현되지만 표기 변이에 약하다
    LLM 판독 정확도     유연하지만 왜 그렇게 읽었는지 사후 추적이 어렵다
    둘의 차이           판독이 가진 한계의 크기

  차이가 크면 병목은 온톨로지가 아니라 판독이다. 차이가 작은데도 못 맞히면
  그때가 온톨로지 차례다.

왜 사전을 버리지 않는가
  slots.py 가 처음부터 적어 둔 이유 그대로다 — LLM 판독은 틀렸을 때 온톨로지가
  틀린 것인지 판독기가 틀린 것인지 갈리지 않는다. 실제로 이 파일을 만들며 LLM
  판독(내가 직접 읽은 것)이 셋을 오독했고, 오판이 2.0%에서 7.3%로 뛰었다.
  사전이었기에 어느 규칙이 어떤 문자열에서 왔는지 되짚어 되돌릴 수 있었다.

  그래서 사전은 계기로 남기고 LLM 판독은 별도 경로로 둔다.

LLM 판독은 어떻게 기록되는가
  cases/llm_reading.json 에 사례·슬롯·클래스·근거를 적어 둔다. 호출이 아니라
  기록이다. 누가 언제 무엇을 왜 그렇게 읽었는지가 남고, 사전 판독과 diff 가 된다.
  읽지 못한 것도 이유와 함께 남긴다 — 그것이 서식 문제의 목록이 된다.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "cases" / "sessions.json"
LLM = ROOT / "cases" / "llm_reading.json"


def dictionary():
    """사전 판독 — scripts/slots.py 가 만든 그대로."""
    return json.loads(SESSIONS.read_text(encoding="utf-8"))


def llm():
    """사전 판독 + LLM 판독 덧입힘.

    덧입힘이지 대체가 아니다. 사전이 읽은 것은 그대로 두고 놓친 것만 더한다.
    사전의 오독(있는데 잘못 읽은 것)은 여기서 고치지 않는다 — 그것을 재려면
    전량 재판독이 필요하고, 지금 기록은 '놓친 것'만 담고 있다.
    """
    sessions = dictionary()
    d = json.loads(LLM.read_text(encoding="utf-8"))
    by = {s["case_id"]: s for s in sessions}
    added = 0
    for r in d["readings"]:
        s = by.get(r["case"])
        if not s:
            continue
        have = {f["cls"] for f in s["facts"]}
        for c in r["classes"]:
            if c in have:
                continue
            s["facts"].append({"cls": c, "status": "Confirmed", "agent": "InvestigatorAgent",
                               "slot": "slot_" + r["slot"], "src": "[LLM] " + r["why"][:60]})
            added += 1
    return sessions, added


def get(name):
    return dictionary() if name == "dict" else llm()[0]


if __name__ == "__main__":
    d = json.loads(LLM.read_text(encoding="utf-8"))
    sess, added = llm()
    base = dictionary()
    nb = sum(len(s["facts"]) for s in base)
    print(f"사전 판독      사실 {nb}개")
    print(f"LLM 판독 기록  {len(d['readings'])}건 → 사실 {added}개 추가 (총 {nb + added}개)")
    print(f"판독 불가      {len(d['unmappable'])}항목 — 이유와 함께 기록됨\n")
    for u in d["unmappable"]:
        print(f"  · {u['text'][:46]:48s} {u['why'][:56]}")
