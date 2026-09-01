# -*- coding: utf-8 -*-
"""슬롯이 담지 못한 결론 층 정보를 원문에서 보충한다.

왜 필요한가
  dataset.xlsx 의 슬롯 10개는 전부 관찰이다. 시간선·접촉 정황·열전달 경로 같은
  분석 항목을 담을 칸이 없다. 그래서 NFPA 결론 요건을 재면 전부 '없음'이 나온다.
  그런데 원문 조사서에는 있다 — 시간선 37%, 접촉 정황 27%, 열전달 경로 37%.

  확신도는 더 심하다. 82% 의 조사서가 '추정·판단됨'으로 쓰는데, 정답 누출을
  막으려고 그것을 판정 표지로 걷어냈다. 지우고 나서 없다고 센 셈이다.

누출을 어떻게 막는가
  문장을 옮기지 않는다. '있다/없다'와 확신도 수준만 가져온다. §19.6.3 이 묻는
  것은 '질문에 답했는가'이지 '무엇이라고 답했는가'가 아니므로, 있다/없다만으로
  충분하다. 가설 이름은 어차피 옮기지 않으니 판정에 쓰일 수 없다.

무엇이 달라지는가
  정확도는 그대로다. 여기서 채우는 것은 결론 층 필드이고 지표 규칙이 쓰지 않는다.
  달라지는 것은 'NFPA 결론 요건을 충족하는가' 하나다. 그리고 그것이 이 측정이
  원래 물으려던 것이다 — 슬롯이 아니라 조사서가 요건을 채우는가.
"""
import zipfile, glob, os, re, json, pathlib, collections
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "cases" / "raw"

# 확신도. 원문의 어미가 NFPA 의 probable/possible 에 대응한다.
#   판단됨·확인됨  → 단정적 판단     → Probable
#   추정·보인다·사료 → 추론          → Possible
PROBABLE = r"판단됨|판단된다|판단하였|확인되었|단정"
POSSIBLE = r"추정|보인다|보임|사료|가능성이\s*높|여겨"

# 결론 층 질문에 원문이 답하고 있는가 (§19.6.3, §9.9.1.4, §19.6.5.2)
PROBE = {
    "timeline":  r"\d+\s*시|\d+\s*분|당시|직전|이후|무렵|경에|사이에",
    "contact":   r"접촉|맞닿|닿아|눌린\s*상태|끼인|사이에\s*끼|밀착",
    "heatpath":  r"착화|옮겨붙|전도|복사열|불티|불씨|번져|접촉하여",
    "safety":    r"차단기|누전차단기|퓨즈|트립|보호장치",
    "spread":    r"연소\s*확대|확산|번져|연소\s*진행|비화",
}


def text_of(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("Contents/section0.xml").decode("utf-8"))
    out, cur = [], []
    for el in root.iter():
        t = el.tag.split("}")[-1]
        if t == "t" and el.text:
            cur.append(el.text)
        elif t == "p":
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))
    return " ".join(out)


def certainty(text):
    """원문이 쓴 확신도 수준만. 문장은 가져오지 않는다."""
    if re.search(PROBABLE, text):
        return "Probable"
    if re.search(POSSIBLE, text):
        return "Possible"
    return None


def enrich():
    originals = {os.path.splitext(os.path.basename(f))[0].upper(): f
                 for f in glob.glob(str(RAW / "*" / "*.hwpx"))}
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))
    stat = collections.Counter()
    for s in sessions:
        f = originals.get(s["case_id"].upper())
        if not f:
            continue
        t = text_of(f)
        c = certainty(t)
        s["certainty"] = c
        if c:
            stat[f"확신도:{c}"] += 1
        for k, pat in PROBE.items():
            hit = bool(re.search(pat, t))
            s[k] = hit
            if hit:
                stat[k] += 1
    (ROOT / "cases" / "sessions.json").write_text(
        json.dumps(sessions, ensure_ascii=False, indent=1), encoding="utf-8")
    return sessions, stat


if __name__ == "__main__":
    sessions, stat = enrich()
    n = len(sessions)
    print(f"사례 {n}건에 결론 층 정보를 보충했다\n")
    print(f"{'항목':16s} {'건수':>5s} {'비율':>6s}")
    for k in ("확신도:Probable", "확신도:Possible", "timeline", "contact",
              "heatpath", "safety", "spread"):
        v = stat.get(k, 0)
        print(f"{k:16s} {v:5d} {v / n * 100:5.0f}%")
    nc = sum(1 for s in sessions if s.get("certainty"))
    print(f"\n확신도 표기 있음 {nc}/{n} = {nc / n * 100:.0f}%")
