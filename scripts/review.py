# -*- coding: utf-8 -*-
"""efi_tbox.ttl 의 판단 기준을 조사관 검토용 xlsx 로 내보낸다."""
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

G = json.load(open('build/graph.json', encoding='utf-8'))
O = json.load(open('build/onto.json', encoding='utf-8'))
KO = {n['id']: n['ko'] for n in G['nodes']}
k = lambda x: KO.get(x, x)
SCEN = {'PoorContactScenario': '접촉불량', 'CrushDamageScenario': '압착손상',
        'PartialDisconnectionScenario': '반단선', 'InsulationDegradationScenario': '절연열화',
        'TrackingScenario': '트래킹', 'ExternalFlameScenario': '외부화염',
        'ElectricalIgnitionScenario': '전기적 발화 공통'}
ROLE = {'Core': '핵심', 'Supporting': '보강', 'Refuting': '반증', 'DecisiveRefuting': '결정적 반증'}

FONT = 'Arial'
H_FILL = PatternFill('solid', fgColor='1F3A4D')
H_FONT = Font(name=FONT, bold=True, color='FFFFFF', size=10)
BODY = Font(name=FONT, size=10)
HI = PatternFill('solid', fgColor='FFF2CC')      # 우선 검토
IN = PatternFill('solid', fgColor='FFFFCC')      # 조사관 기입란
THIN = Side(style='thin', color='D0D0D0')
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')
CTR = Alignment(horizontal='center', vertical='center')

wb = Workbook()

# ── 0. 안내 ────────────────────────────────────────────────────────────────
ws = wb.active
ws.title = '검토 안내'
ws.sheet_view.showGridLines = False

DV = lambda: DataValidation(type='list', formula1='"O,X,△"', allow_blank=True)


def sheet(title, headers, data, widths, note, hi_idx=None, extra_inputs=()):
    w = wb.create_sheet(title)
    w.sheet_view.showGridLines = False
    w['A1'] = note
    w['A1'].font = Font(name=FONT, size=9, italic=True, color='666666')
    w.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers) + 2)
    w.row_dimensions[1].height = 26
    w['A1'].alignment = WRAP
    hdr = headers + list(extra_inputs) + ['판정', '의견·수정할 내용']
    for j, h in enumerate(hdr, 1):
        c = w.cell(3, j, h); c.font = H_FONT; c.fill = H_FILL; c.alignment = CTR; c.border = BOX
    dv = DV(); w.add_data_validation(dv)
    for i, row in enumerate(data, 4):
        for j, v in enumerate(row, 1):
            c = w.cell(i, j, v); c.font = BODY; c.border = BOX; c.alignment = WRAP
            if hi_idx is not None and hi_idx(row):
                c.fill = HI
        jd = len(headers) + 1
        ne = len(extra_inputs)
        for off in range(ne + 1):
            c = w.cell(i, jd + off); c.fill = IN; c.border = BOX; c.alignment = CTR
        w.cell(i, jd + ne + 1).fill = IN; w.cell(i, jd + ne + 1).border = BOX
        dv.add(w.cell(i, jd + ne))
    for j, wd in enumerate(widths + [8] * len(extra_inputs) + [7, 34], 1):
        w.column_dimensions[get_column_letter(j)].width = wd
    w.freeze_panes = 'A4'
    return w


# ── 1. 단서와 점수 ────────────────────────────────────────────────────────
rules = sorted(O['rules'], key=lambda r: (list(SCEN).index(r['sc'][0]) if r['sc'] and r['sc'][0] in SCEN else 9,
                                          -abs(r['d'][0] if r['d'] else 0)))
d1 = []
for r in rules:
    sc = SCEN.get(r['sc'][0], r['sc'][0]) if r['sc'] else ''
    ind = k(r['ind'][0]) if r['ind'] else ''
    role = ROLE.get(r['role'][0], '') if r['role'] else ''
    dv_ = r['d'][0] if r['d'] else 0
    st = '없음이 확인됨' if (r['st'] and r['st'][0] == 'ConfirmedAbsent') else '확인됨'
    sent = (f'{sc} 가설을 검토할 때, {ind}이(가) {st} 상태이면 '
            f'{"지지점수를 " + str(dv_) + "점 올린다" if dv_ > 0 else "지지점수를 " + str(-dv_) + "점 내린다"}.')
    d1.append([sc, ind, role, st, dv_, sent])
sheet('1 단서와 점수',
      ['가설', '확인 항목', '역할', '필요 상태', '가감점', '문장으로 읽으면'],
      d1, [12, 24, 12, 13, 8, 52],
      '가감점은 사람이 정한 값이 아니라 변별력에서 계산된 값입니다. 몇 가설이 같은 단서를 낼 수 있는지로 '
      '정해지며, 6개 가설 전부가 내는 단서는 0점이 됩니다. 그러니 점수 하나하나가 맞는지는 보지 마시고, '
      '같은 가설 안에서 항목들의 순서가 뒤집힌 곳이 있는지만 봐 주십시오. '
      '“이게 저것보다 중요한데 점수가 낮다” 싶은 곳을 X 로 표시해 주시면 됩니다.',
      hi_idx=lambda r: abs(r[4]) >= 15)

# ── 2. 형태 발현 ──────────────────────────────────────────────────────────
CH = O['chain']
shared = O['shared']
d2 = []
for a, b in sorted(CH['producesDamage'], key=lambda x: (k(x[0]), k(x[1]))):
    n = shared.get(b, 0)
    d2.append([k(a), k(b), n if n else '',
               f'{k(a)}이(가) 일어나면 {k(b)}이(가) 남을 수 있다.'])
sheet('2 형태 발현',
      ['발열 메커니즘', '남길 수 있는 손상 양상', '이 흔적을 남기는 가설 수', '문장으로 읽으면'],
      d2, [20, 24, 12, 52],
      '이 시트가 혼동 쌍 판정의 근거입니다. 여러 가설이 같은 흔적을 남기면 사진만으로 못 가른다고 판단합니다. '
      '노란 줄은 3개 이상의 가설이 공유하는 흔적으로, 변별력이 없다고 본 것입니다.',
      hi_idx=lambda r: isinstance(r[2], int) and r[2] >= 3)

# ── 3. 선행조건과 착화물 ─────────────────────────────────────────────────
d3 = []
for a, b in sorted(CH['enables'], key=lambda x: (k(x[0]), k(x[1]))):
    d3.append(['선행조건 → 발열', k(a), k(b), f'{k(a)} 상태에서는 {k(b)}이(가) 일어날 수 있다.'])
for a, b in sorted(CH['ignites'], key=lambda x: (k(x[0]), k(x[1]))):
    d3.append(['발열 → 착화물', k(a), k(b), f'{k(a)}은(는) {k(b)}에 불을 붙일 수 있다.'])
sheet('3 선행조건과 착화물', ['관계', '앞', '뒤', '문장으로 읽으면'], d3, [17, 22, 22, 52],
      '조건이 발열을 일으킬 수 있는지, 그 발열이 그 물질에 착화시킬 수 있는지를 봐 주십시오. '
      '특히 착화물 쪽은 실무 판단이 갈릴 수 있는 부분입니다.')

# ── 4. 현장사실과 증거물 ─────────────────────────────────────────────────
d4 = []
for a, b in sorted(CH['attests'], key=lambda x: (k(x[0]), k(x[1]))):
    d4.append(['현장사실 → 선행조건', k(a), k(b), f'{k(a)}이(가) 확인되면 {k(b)}이(가) 있었다고 본다.'])
for a, b in sorted(CH['exhibits'], key=lambda x: (k(x[0]), k(x[1]))):
    d4.append(['증거물 → 손상 양상', k(a), k(b), f'{k(a)}에서는 {k(b)}이(가) 관찰될 수 있다.'])
sheet('4 현장사실과 증거물', ['관계', '앞', '뒤', '문장으로 읽으면'], d4, [19, 22, 22, 52],
      '현장에서 확인한 사실이 어떤 조건의 존재를 뒷받침하는지, 각 증거물에서 어떤 흔적이 관찰될 수 있는지를 봐 주십시오.')

# ── 5. 용어 ───────────────────────────────────────────────────────────────
AXN = {'mech': '발열 메커니즘', 'evid': '물리 증거물', 'ante': '선행 조건', 'fuel': '착화물',
       'dmg': '손상 양상', 'scene': '현장 사실', 'scen': '가설·판정', 'evt': '사건',
       'obs': '계측', 'meta': '절차 기록', 'enum': '열거값', 'agent': '행위자', 'other': '기타'}
AX = {n['id']: n['ax'] for n in G['nodes']}
d5 = []
for n in sorted(G['nodes'], key=lambda x: (AXN.get(x['ax'], ''), x['ko'])):
    sup = O['c'].get(n['id'], {}).get('sup', [])
    d5.append([AXN.get(n['ax'], n['ax']), n['ko'], ' · '.join(k(s) for s in sup),
               O['c'].get(n['id'], {}).get('cm', '')])
sheet('5 용어', ['축', '이름', '상위 개념', '설명'], d5, [15, 24, 22, 48],
      '용어가 실무에서 쓰는 말과 맞는지, 상위-하위 관계가 뒤집힌 곳은 없는지 봐 주십시오. '
      '이름만 고치는 것은 결과에 영향을 주지 않으니 부담 없이 지적해 주셔도 됩니다.')


# ── 6. 반증 후보 ──────────────────────────────────────────────────────────
#  혼동 쌍마다 질문 하나. 사진으로 못 가르는 두 가설 사이의 반증이 가장 값지다.
#  후보풀에서 비형태·상위 개념을 대표로 뽑는다 — 하위 개념은 조사관이 한 번만 답하면 된다.
import score
from rdflib import Graph, Namespace as _NS
_g = Graph().parse('ontology/efi_tbox.ttl', format='turtle')
_E = _NS('https://w3id.org/efi-onto#')
_ln = lambda u: str(u).split('#')[-1]
_man = {sc: {_ln(d) for d in _g.objects(_E[sc], _E.canManifest)} for sc in score.SCENARIOS}
_conf = {(a, b): len(_man[a] & _man[b])
         for a in score.SCENARIOS for b in score.SCENARIOS
         if a != b and len(_man[a] & _man[b]) >= 2}
_compat = score.compatibility(_g)
_excl = {i: next(iter(v)) for i, v in _compat.items() if len(v) == 1}
_cov = {}
for _n, _sc, _ind, _r in score.rules(_g):
    for _x in (score.ELECTRICAL if _sc == 'ElectricalIgnitionScenario' else [_sc]):
        _cov.setdefault(_x, set()).add(_ind)
_morph = lambda i: 'DamagePattern' in score._ancestors(_g, _E[i])

d6 = []
for (sc, own), n in _conf.items():
    pool = [i for i, o in _excl.items() if o == own and i not in _cov.get(sc, set())]
    anc = {i: score._ancestors(_g, _E[i]) for i in pool}
    pool = [i for i in pool if not (anc[i] & set(pool))]
    if not pool:
        continue
    pool.sort(key=lambda i: (_morph(i), len(anc[i]), i))
    ind = pool[0]
    d6.append([SCEN[sc], SCEN[own], k(ind), n, -21 if _morph(ind) else -30,
               f'{SCEN[sc]} 가설을 보고 있을 때 {k(ind)}이(가) 확인되면, 이것은 {SCEN[own]}에서만 '
               f'성립하는 것이므로 {SCEN[sc]}을(를) 약화시킨다 — 맞습니까?'])
d6.sort(key=lambda r: (r[0], r[4]))
sheet('6 반증 후보', ['가설', '경쟁 가설', '확인 항목', '공유 흔적 수', '가감점', '문장으로 읽으면'],
      d6, [12, 12, 22, 10, 8, 56],
      '가설마다 반증 단서가 하나뿐이라 반증이 잘 작동하지 않습니다. 사진으로 잘 안 갈리는 가설 쌍마다 '
      '질문을 하나씩 만들었습니다. O 로 표시하신 항목은 그대로 반증 규칙이 됩니다. '
      '중요한 조건: 화재로 사라지는 것은 반증이 될 수 없습니다. 불에 타 없어질 것이라면 X 로 봐 주십시오. '
      '대부분 X 여도 정상입니다.')

wb.save('build/EFI-Onto_검토표.xlsx')
print('rows', len(d1), len(d2), len(d3), len(d4), len(d5), len(d6))
