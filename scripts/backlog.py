"""원문 대조표의 미완료 행과 실행 작업을 대조하고 검토 문서를 생성한다."""
import argparse
import collections
import importlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "tbox_backlog.json"
REPORT = ROOT / "docs" / "TBox_미완료_목록.md"
STATES = ("구현대기", "설계검토", "기존보류", "자료대기", "범위제외", "구현완료", "정리완료")


def catalog():
    result = {}
    for name in ("nfpa", "silmu", "babrauskas"):
        module = importlib.import_module(name)
        for level, field in (("S", "SECTIONS"), ("L", "SUBSECTIONS")):
            for row in getattr(module, field):
                if name == "nfpa":
                    key, title, state = row[:3]
                else:
                    key = row[0] if level == "S" else f"{row[0]}/{row[1]}"
                    title, state = row[2:4]
                result[f"{name}:{level}:{key}"] = {
                    "source": name, "level": level, "section": key, "title": title,
                    "state": state, "note": row[-1], "file": f"scripts/{name}.py",
                }
    module = importlib.import_module("domestic")
    for i, row in enumerate(module.BRANCHES, 1):
        result[f"domestic:B:{i}"] = {
            "source": "domestic", "level": "B", "section": str(i), "title": row[2],
            "state": row[3], "note": row[4], "file": "scripts/domestic.py",
        }
    return result


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def validate(data, rows):
    errors, ids, covered = [], set(), set()
    for item in data["items"]:
        key = item["id"]
        if key in ids:
            errors.append(f"작업 ID 중복: {key}")
        ids.add(key)
        if item["state"] not in STATES:
            errors.append(f"상태 오류: {key}")
        for field in ("title", "current", "gap", "next", "done_when", "basis"):
            if not item.get(field):
                errors.append(f"{key}: {field} 누락")
        for ref in item["refs"]:
            if ref not in rows:
                errors.append(f"원문 항목 없음: {key} → {ref}")
            if item["state"] not in ("정리완료", "구현완료"):
                covered.add(ref)
        for evidence in item["evidence"]:
            path = (ROOT / evidence["file"]).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
                errors.append(f"근거 파일 없음: {key} → {evidence['file']}")
            elif evidence["anchor"] not in path.read_text(encoding="utf-8"):
                errors.append(f"근거 위치 없음: {key} → {evidence['anchor']}")
    for item in data["items"]:
        for dep in item["depends_on"]:
            if dep not in ids or dep == item["id"]:
                errors.append(f"의존 작업 오류: {item['id']} → {dep}")
    missing = {key for key, row in rows.items() if row["state"] in ("일부", "없음")} - covered
    errors.extend(f"미완료 원문 행의 작업 연결 누락: {key}" for key in sorted(missing))
    return errors


def counts(data):
    return collections.Counter(item["state"] for item in data["items"])


def line_link(file, anchor, label=None):
    path = ROOT / file
    lines = path.read_text(encoding="utf-8").splitlines()
    line = next(i for i, text in enumerate(lines, 1) if anchor in text)
    return f"[{label or anchor}]({path.as_posix()}:{line})"


def render(data, rows):
    n = counts(data)
    out = ["# TBox 원문 이식 미완료 목록", "",
           f"정리 기준: {data['reviewed_on']} · 원본은 `docs/tbox_backlog.json`, 재생성은 `python scripts/backlog.py --write`.", "",
           "이번 정리는 원문 대조표·현행 TTL·Python·인계 기록을 비교한 구현 현황 감사다. 모든 원문을 새로 완독하거나 과학적 타당성을 재검증한 결과는 아니다.", "",
           "## 읽는 방법", "",
           "- **원문 행 수**와 **중복을 합친 작업 수**는 다르다. 한 행에 여러 문제가 있으면 여러 작업에 연결한다. 상위 절과 하위 절도 합산하지 않는다.",
           "- 상태를 ‘범위제외·기존보류’로 나누어도 원문 대조표의 분모를 줄이거나 구현 완료로 세지 않는다.",
           "- ‘구현대기’는 현행 어휘를 이어 구현할 작업이다. 새 규칙의 상세 조건은 해당 원문을 다시 확인하고 구현한다. 실제 사례가 없다는 사실만으로 논리적 구현이 불가능한 것은 아니다.",
           "- ‘기존보류’는 인계·기존 대조표에 남은 운영 결정을 보존한 상태다. 표본 수 자체를 과학적 구현 기준으로 채택한 것이 아니다.",
           "- ‘범위제외’는 현재 남은 내용에 관한 기존 범위 결정이다. 이미 구현된 공통 부분을 삭제한다는 뜻은 아니다.",
           "- ‘구현완료’는 목록 작성 이후 구현한 작업이며 ‘정리완료’는 기존 구현을 확인하여 표시를 고친 기록이다.",
           "- 테스트·lint 통과와 과거 구조 결함 8건의 해소는 원문 이식 완료를 뜻하지 않는다.", "",
           "## 현재 집계", "", "| 구분 | 작업 수 |", "|---|---:|"]
    out += [f"| {state} | {n[state]} |" for state in STATES]
    out += ["", "‘구현대기’부터 진행하며 ‘설계검토’는 적용 범위·입력·추론 조건을 먼저 확정한다. 조사관 서식 검토와 신규 사례 검증은 별도 병행 업무다.", "",
            "| 원문 대조표 | 표시 정정 전 | 표시 정정 후 | 현재 구현/대상 | 일부·미구현 행 |", "|---|---:|---:|---:|---:|"]
    for name, label in (("nfpa", "NFPA 하위 절"), ("silmu", "실무Ⅳ 하위 절"), ("babrauskas", "Babrauskas 하위 절"), ("domestic", "국내 분류 갈래")):
        selected = [r for r in rows.values() if r["source"] == name and r["level"] in ("L", "B") and r["state"] not in ("범위밖", "현장절차")]
        done = sum(r["state"] == "구현" for r in selected)
        old = data["before"][name]
        audit = data.get("after_audit", data["before"])[name]
        out.append(f"| {label} | {old['done']}/{old['total']} | {audit['done']}/{audit['total']} | {done}/{len(selected)} | {len(selected)-done} |")
    out += ["", "상위 절의 ‘구현’은 개요 수준의 기존 표시다. 하위 절의 미완료를 덮지 않으며, 책 전체나 전체 프로젝트의 완성률로 읽지 않는다.", "",
            "## 이번에 바로잡은 표시", ""] + [f"- {entry}" for entry in data["corrections"]]
    out += ["", "## 작업 목록", ""]
    for state in STATES:
        out += [f"### {state}", ""]
        for item in sorted((x for x in data["items"] if x["state"] == state), key=lambda x: (x["priority"], x["id"])):
            out += [f"#### {item['id']} · {item['title']} (우선순위 {item['priority']})", "",
                    f"- 현재: {item['current']}", f"- 남은 것: {item['gap']}",
                    f"- 다음 조치: {item['next']}", f"- 완료/재개 조건: {item['done_when']}",
                    f"- 분류 근거: {item['basis']}"]
            if item["depends_on"]:
                out.append("- 선행 작업: " + ", ".join(item["depends_on"]))
            if item["refs"]:
                out.append("- 원문 행: " + ", ".join(f"`{ref}`" for ref in item["refs"]))
            out.append("- 코드·기록: " + " · ".join(line_link(e["file"], e["anchor"]) for e in item["evidence"]))
            out.append("")
    out += ["## 원문 행별 추적표", "",
            "이 표는 현재 ‘일부·없음’인 상위/하위 행 전체와 이번 감사에서 함께 확인한 행을 포함한다. 같은 작업 ID가 반복되어도 별도 작업으로 세지 않는다.", "",
            "| 원문 행 ID | 제목 | 대조표 상태 | 작업 |", "|---|---|---|---|"]
    reverse = collections.defaultdict(list)
    for item in data["items"]:
        for ref in item["refs"]:
            reverse[ref].append(f"{item['id']}({item['state']})")
    for ref in sorted(reverse):
        row = rows[ref]
        out.append(f"| `{ref}` | {row['title'].replace('|','/')} | {row['state']} | {', '.join(reverse[ref])} |")
    out += ["", "## 갱신 규칙", "",
            "1. 원문 행이나 작업 상태를 바꾸면 `python scripts/backlog.py --check`로 미연결 행·깨진 근거·문서 동기화를 확인한다.",
            "2. 구현 완료에는 해당 개념의 선언뿐 아니라 관계·조건·확인 상태·출처 및 필요한 실행 경로가 있어야 한다. 입력 수집이나 독립 성능 검증은 별도로 남긴다.",
            "3. 원문이 정량 기준을 주지 않거나 상충하는 경우 임의 임계값으로 항목을 닫지 않는다.",
            "4. 새로 구현한 작업은 ‘구현완료’, 기존 구현의 표시만 고친 작업은 ‘정리완료’로 남긴다. 범위 변경은 이유와 근거를 갱신한다.", ""]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, rows = load(), catalog()
    errors = validate(data, rows)
    if errors:
        raise SystemExit("\n".join(errors))
    result = render(data, rows)
    if args.write:
        REPORT.write_text(result, encoding="utf-8", newline="\n")
    if args.check and (not REPORT.exists() or REPORT.read_text(encoding="utf-8") != result):
        raise SystemExit("문서가 최신 목록과 다름: python scripts/backlog.py --write")
    n = counts(data)
    print(" / ".join(f"{state} {n[state]}" for state in STATES))
    print("현재 일부·미구현 행 연결 누락 0 / 근거 위치 오류 0")
    print(REPORT.as_posix())


if __name__ == "__main__":
    main()
