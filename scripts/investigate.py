"""조사 JSON을 TBox로 검증하고 경로·시간·비교·검토의 추가 확인 질문을 출력한다."""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); import _utf8  # noqa: F401
import argparse
import json
from pathlib import Path
import sys

from rdflib import Graph, SH, URIRef
from pyshacl import validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from efi_schema import EFI, Session, load_graph
from investigation import supply_questions, timeline_questions, detail_questions


def inspect(session):
    graph = load_graph()
    graph.parse(data=session.to_turtle(include_derived=False), format='turtle')
    conforms, report, _ = validate(graph, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    issues = []
    for result in report.subjects(SH.resultMessage, None):
        issues.append(dict(shape=str(report.value(result, SH.sourceShape)),
                           focus=str(report.value(result, SH.focusNode)),
                           severity=str(report.value(result, SH.resultSeverity)).split('#')[-1],
                           message=str(report.value(result, SH.resultMessage))))
    node = URIRef(f'{EFI}session_{session.case_id}')
    return dict(case_id=session.case_id, conforms=conforms,
                issues=sorted(issues, key=lambda i: (i['focus'], i['message'])),
                supply_questions=supply_questions(graph, node),
                timeline_questions=timeline_questions(graph, node),
                detail_questions=detail_questions(graph, node))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect(Session.model_validate_json(args.input.read_text(encoding='utf-8')))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + '\n', encoding='utf-8')
        print(args.output.resolve())
    else:
        print(text)
    return 0 if result['conforms'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
