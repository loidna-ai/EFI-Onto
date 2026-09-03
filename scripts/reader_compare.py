# -*- coding: utf-8 -*-
"""두 판독기로 같은 온톨로지를 돌려 차이를 낸다.

읽는 법
  두 값의 차이가 판독이 가진 한계의 크기다. 온톨로지는 양쪽에서 똑같으므로
  차이는 전부 '조사서에서 무엇을 뽑았는가'에서 온다.

  차이가 크면      병목은 판독이다. 온톨로지를 고칠 때가 아니다.
  차이가 작으면    판독은 할 만큼 했다. 남은 것이 온톨로지 몫이다.

  상한도 함께 본다. 상한이 오른다는 것은 조사서에 있던 것을 새로 읽었다는 뜻이고,
  상한이 그대로인데 정확도만 오르면 이미 읽던 것을 더 잘 쓴 것이다.
"""
import sys, json, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import reader
import eval as E


def run(sessions, onto):
    ok = und = 0
    per = collections.defaultdict(lambda: [0, 0, 0])       # 실제 → [맞음, 전체, 상한]
    for s in sessions:
        pred, _ = E.predict(s, onto)
        a = s["actual_scenario"]
        per[a][1] += 1
        if pred == a:
            ok += 1; per[a][0] += 1
        if pred in E.HELD:
            und += 1
        if any(any(onto.matches(f["cls"], r.indicator) for r in onto.rules
                   if r.scenario == a and r.role.value in ("Core", "Supporting"))
               for f in s["facts"] if f["status"] == "Confirmed"):
            per[a][2] += 1
    n = len(sessions)
    ceil = sum(v[2] for v in per.values())
    return {"n": n, "ok": ok, "und": und, "wrong": n - ok - und, "ceil": ceil, "per": per}


if __name__ == "__main__":
    from efi_schema import Ontology
    onto = Ontology.load(str(ROOT / "ontology" / "efi_tbox.ttl"))
    d = run(reader.dictionary(), onto)
    l = run(reader.llm()[0], onto)

    print("같은 온톨로지, 다른 판독기\n")
    print(f"{'':14s}{'사전 판독':>10s}{'LLM 판독':>10s}{'차이':>8s}")
    for k, lab in (("ok", "정확"), ("wrong", "오판"), ("und", "판단보류"), ("ceil", "상한")):
        a, b = d[k] / d["n"] * 100, l[k] / l["n"] * 100
        print(f"  {lab:12s}{a:9.1f}%{b:9.1f}%{b - a:+8.1f}%p")

    print(f"\n{'요인':10s}{'사전':>8s}{'LLM':>8s}{'차이':>8s}   {'사전 상한':>9s}{'LLM 상한':>9s}")
    for a in sorted(d["per"], key=lambda x: -d["per"][x][1]):
        dc, t, dl = d["per"][a]
        lc, _, ll = l["per"][a]
        print(f"{E.KO[a]:10s}{dc / t * 100:7.1f}%{lc / t * 100:7.1f}%{(lc - dc) / t * 100:+7.1f}%p"
              f"   {dl / t * 100:8.1f}%{ll / t * 100:8.1f}%")

    gap = (l["ok"] - d["ok"]) / d["n"] * 100
    print(f"\n판독이 가진 한계의 크기: {gap:+.1f}%p")
    if abs(gap) < 1:
        print("  두 판독이 사실상 같다. 남은 것은 온톨로지 몫이거나 조사서 몫이다.")
    elif gap > 0:
        print("  사전 판독이 조사서에 있는 것을 놓치고 있다. 온톨로지를 고치기 전에 판독을 본다.")
    else:
        print("  LLM 판독이 사전보다 못하다. 오독을 의심한다 — 실제로 그런 적이 있다.")
