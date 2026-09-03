# -*- coding: utf-8 -*-
"""NFPA 층만으로 무엇을 할 수 있는지 실측한다.

물음
  NFPA 921 직접 근거만으로 사례를 판정할 수 있는가?

답의 구조
  못 한다. 다섯 요인(접촉불량·압착손상·반단선·절연열화·트래킹)은 국내 실무의
  분류이고 NFPA 에는 그런 구분이 없다. 라벨 공간 자체가 국내 것이다.

  대신 NFPA 층은 다른 것을 한다 — 결론이 설 수 있는지 없는지를 본다.
  이 파일은 그것을 잰다. 각 사례에 결론을 세워 보고 어느 조항에서 막히는지 센다.

이 숫자가 뜻하는 것
  막히는 건수는 조사서의 부실이거나 우리 제약의 과도함이다. 어느 쪽인지는
  막은 조항을 보면 갈린다.
"""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import json, sys, pathlib, collections, re
from rdflib import Graph
from pyshacl import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TTL = (ROOT / "ontology" / "efi_tbox.ttl").read_text(encoding="utf-8")

from efi_schema import DEFAULT_MECHANISM as MECH  # 가설 → 정의 메커니즘. 한 곳에서만 든다


def abox(sess):
    """사례를 ABox 로. 정답 가설에 결론을 세워 본다 — 가장 유리한 조건이다."""
    sc = sess["actual_scenario"]
    out = [f'efi:s a efi:InvestigationSession ; efi:queryCount {sess["query_count"]} .',
           'efi:inv a efi:InvestigatorAgent .']
    for i, f in enumerate(sess["facts"]):
        out.append(f'efi:f{i} a efi:{f["cls"]} ; efi:confirmationStatus efi:{f["status"]} ; '
                   f'prov:wasAttributedTo efi:inv .')
        out.append(f'efi:s efi:hasFact efi:f{i} .')
    sup = " , ".join(f"efi:f{i}" for i, f in enumerate(sess["facts"])
                     if f["status"] == "Confirmed") or None
    # 슬롯이 담지 못한 결론 층 정보를 원문에서 보충한 것(scripts/enrich.py).
    # 문장은 옮기지 않는다 — 답했는가만 기록한다. §19.6.3 이 묻는 것은
    # '질문에 답했는가'이지 '무엇이라 답했는가'가 아니다.
    h = [f'efi:h a efi:{sc} ; efi:inSession efi:s',
         f' ; efi:hasMechanism [ a efi:{MECH[sc]} ] ; efi:verdict efi:Supported']
    if sup:
        h.append(f' ; efi:supportedBy {sup}')
    if sess.get("contact"):
        h.append(' ; efi:contactCircumstance "원문에 접촉 정황 서술 있음"')
        h.append(' ; efi:hasAntecedent [ a efi:%s ]' %
                 ("ExternalCrushing" if sc == "CrushDamageScenario" else "ElectricalState"))
    if sess.get("heatpath"):
        h.append(' ; efi:heatTransferPath "원문에 열전달 경로 서술 있음"')
    if sess.get("timeline"):
        h.append(' ; efi:timelineConsistent true')
    h.append(' ; efi:sourceCompetentForFuel true .')
    out.append("".join(h))
    c = ['efi:c a efi:Conclusion ; efi:concludes efi:h']
    if sess.get("certainty"):
        c.append(f' ; efi:certaintyLevel efi:{sess["certainty"]}')
    c.append(' .')
    out.append("".join(c))
    return "\n".join(out)


def run(sess):
    """위반(Violation)과 권고(Warning)를 갈라 돌려준다.

    NFPA 921 은 Guide 라 should 를 쓴다. 권고 미준수와 필수 위반을 한 칸에 세면
    권고를 안 지킨 모든 조사가 '결론 자격 없음'이 된다.
    """
    from rdflib import SH
    g = Graph().parse(data=TTL + "\n" + abox(sess), format="turtle")
    _, rg, _ = validate(g, advanced=True, allow_infos=True, allow_warnings=True)
    viol, warn = set(), set()
    for r in set(rg.subjects(SH.resultSeverity, None)):
        sev = rg.value(r, SH.resultSeverity)
        msg = str(rg.value(r, SH.resultMessage) or "")
        (warn if sev == SH.Warning else viol).add(msg)
    return viol, warn


def clause(msg):
    m = re.search(r"§[\d.]+", msg)
    return m.group(0) if m else "(조항 없음)"


if __name__ == "__main__":
    sessions = json.loads((ROOT / "cases" / "sessions.json").read_text(encoding="utf-8"))
    blocked, advised = collections.Counter(), collections.Counter()
    nv, nw, nv_cited = [], [], []
    for s in sessions:
        viol, warn = run(s)
        nv.append(len(viol)); nw.append(len(warn))
        # 조항 근거가 있는 위반만 따로 센다. 확정선 70점과 최소 사실 2건은
        # 논문 3.2절의 세션 확정 조건이지 NFPA 조항이 아니다. 'NFPA 요건을
        # 충족하는가'를 물을 때 우리 기준을 섞으면 답이 흐려진다.
        nv_cited.append(sum(1 for m in viol if re.search(r"§[\d.]+", m)))
        for m in viol:
            blocked[(clause(m), m[:64])] += 1
        for m in warn:
            advised[(clause(m), m[:64])] += 1
    n = len(sessions)
    clean = sum(1 for c in nv if c == 0)
    # 조항 근거가 있는 위반과 우리가 만든 기준을 가른다.
    # 확정선 70점, 최소 사실 2건은 논문 3.2절의 세션 확정 조건이지 NFPA 조항이
    # 아니다. 'NFPA 요건을 충족하는가'를 물을 때 우리 기준을 섞으면 답이 흐려진다.
    cited_clean = sum(1 for c in nv_cited if c == 0)
    print(f"사례 {n}건에 정답 가설로 결론을 세워 봤다 — 가장 유리한 조건이다\n")
    print(f"  전체 필수 요건 통과       {clean:3d}건  {clean / n * 100:.1f}%")
    print(f"  조항 근거 위반만 세면 통과 {cited_clean:3d}건  {cited_clean / n * 100:.1f}%")
    print(f"  필수 요건 위반           {n - clean:3d}건  {(n - clean) / n * 100:.1f}%")
    print(f"  사례당 위반 {sum(nv) / n:.1f}건, 권고 미준수 {sum(nw) / n:.1f}건\n")
    print("■ 필수 위반")
    for (cl, m), v in blocked.most_common(12):
        print(f"   {cl:10s} {v:5d}  {m}")
    print("\n■ 권고 미준수 — 결론 자격을 막지 않는다")
    for (cl, m), v in advised.most_common(12):
        print(f"   {cl:10s} {v:5d}  {m}")
