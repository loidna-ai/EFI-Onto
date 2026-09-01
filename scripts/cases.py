# -*- coding: utf-8 -*-
"""조사서에서 관찰 부분만 떼어낸다.

왜 필요한가
  조사서 본문에는 판정 결과가 그대로 서술돼 있다. '절연열화 된 전선에서', '트래킹에
  의한 단락으로'. 그대로 넣으면 시스템이 판정하는 것이 아니라 정답을 읽는다.
  판정 문장을 걷어내고 관찰만 남겨야 대조가 성립한다.

기준
  애매하면 버린다. 관찰을 잘못 버리면 입력이 약해질 뿐이지만, 판정을 하나라도
  남기면 정답이 새서 측정 전체가 무의미해진다. 두 오류의 무게가 다르다.

떼어낸 뒤 반드시 확인할 것
  잔여 누출 0건. 관찰 텍스트에 가설 이름이 남아 있으면 안 된다.
"""
import zipfile, glob, os, re, json, sys, pathlib, collections
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "cases" / "raw"
OUT = ROOT / "cases" / "observed"

# 폴더명 → 우리 가설. '기계적 손상'은 압착손상이다(확인함).
LABEL = {
    "접촉불량": "PoorContactScenario",
    "기계적 손상": "CrushDamageScenario",
    "반단선": "PartialDisconnectionScenario",
    "절연열화": "InsulationDegradationScenario",
    "트래킹": "TrackingScenario",
}

# 가설 이름. 관찰 텍스트에 남으면 정답 누출이다.
VERDICT_WORDS = ["절연열화", "절연 열화", "트래킹", "접촉불량", "접촉 불량", "접속불량",
                 "반단선", "반 단선", "부분단선", "압착손상", "기계적 손상"]

# 판정을 내리는 문장의 표지
JUDGMENT = ["종합", "판단", "추정", "판정", "결론", "발화원인", "발화 원인",
            "에 의한 발화", "으로 인하여 발생", "로 인하여 발생", "에 의해 발생",
            "발화한 것으로", "발화된 것으로", "원인으로 보", "요인으로 보",
            # 소거 추론. 정답 누출은 아니나 관찰이 아니라 판단이다.
            "배제", "부정한다", "가능성은 낮", "가능성 없", "볼 수 있을", "사료",
            "기인한", "특이점으로 볼"]

# 사진 캡션·서식 부스러기
NOISE = [r"^사진\s*\d+", r"^촬영\s*(일자|날짜|일)", r"^출처$", r"^현장사진$",
         r"^국립과학수사(연구소|연구원)?\s*(감정결과)?$", r"^끝\.$", r"^\d{4}\.\s*\d",
         r"^['‘’]\d{2}\.", r"^화재\s*요인\s*판정$"]


def paragraphs(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("Contents/section0.xml").decode("utf-8"))
    out, cur = [], []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "t" and el.text:
            cur.append(el.text)
        elif tag == "p":
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))
    return [l.strip() for l in out if l.strip()]


def sentences(paras):
    out = []
    for p in paras:
        for s in re.split(r"(?<=[.。])\s+|(?<=음\.)\s*|(?<=함\.)\s*", p):
            s = s.strip()
            if s:
                out.append(s)
    return out


def is_noise(s):
    return any(re.search(p, s) for p in NOISE)


def is_judgment(s):
    return any(w in s for w in JUDGMENT) or any(w in s.replace(" ", "") for w in
                                                [w.replace(" ", "") for w in VERDICT_WORDS])


def observed(path):
    """관찰 문장만. 판정·노이즈는 버린다."""
    keep = []
    for s in sentences(paragraphs(path)):
        s = re.sub(r"[（(]\s*사진[^)）]*[)）]", "", s).strip()   # 사진 참조 지우기
        s = re.sub(r"^[❍○⦁•\-–\s]+", "", s).strip()          # 글머리 기호
        if is_noise(s) or is_judgment(s):
            continue
        if len(s) < 12:         # 표 조각·머리글·시각 표기
            continue
        keep.append(s)
    return keep


def leak(text):
    """관찰 텍스트에 남은 가설 이름."""
    flat = text.replace(" ", "")
    return [w for w in VERDICT_WORDS if w.replace(" ", "") in flat]


def build():
    OUT.mkdir(exist_ok=True)
    manifest, stats = [], collections.defaultdict(lambda: [0, 0, 0])
    for f in sorted(glob.glob(str(RAW / "*" / "*.hwpx"))):
        folder = os.path.basename(os.path.dirname(f))
        cid = os.path.splitext(os.path.basename(f))[0]
        raw = " ".join(paragraphs(f))
        obs = observed(f)
        text = " ".join(obs)
        st = stats[folder]
        st[0] += 1
        st[1] += len(raw)
        st[2] += len(text)
        manifest.append({
            "case_id": cid,
            "label_ko": folder,
            "actual_scenario": LABEL[folder],
            "raw_chars": len(raw),
            "observed_chars": len(text),
            "sentences": len(obs),
            "leak": leak(text),
            "usable": len(text) >= 60 and not leak(text),
        })
        (OUT / f"{cid}.txt").write_text("\n".join(obs), encoding="utf-8")
    (ROOT / "cases" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest, stats


if __name__ == "__main__":
    man, stats = build()
    print(f"{'분류':10s} {'건수':>4s} {'원문':>7s} {'관찰':>7s} {'잔존율':>6s} {'사용가능':>7s}")
    for k, (n, r, o) in sorted(stats.items()):
        ok = sum(1 for m in man if m["label_ko"] == k and m["usable"])
        print(f"{k:10s} {n:4d} {r // n:7d} {o // n:7d} {o / r * 100:5.0f}% {ok:5d}건")
    bad = [m for m in man if m["leak"]]
    print(f"\n잔여 누출 {len(bad)}건")
    for m in bad[:10]:
        print(f"   {m['case_id']:28s} {m['leak']}")
    thin = [m for m in man if not m["leak"] and m["observed_chars"] < 60]
    print(f"관찰 부족(60자 미만) {len(thin)}건")
    for m in thin[:10]:
        print(f"   {m['case_id']:28s} {m['observed_chars']}자")
    print(f"\n사용 가능 {sum(1 for m in man if m['usable'])}/{len(man)}건")
