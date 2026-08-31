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
#  기존 반증 규칙과 같은 논리로 기계 생성한 후보다. 경쟁 가설에서만 나타나는 흔적이
#  발화부에 있으면 이 가설은 약해진다. 이미 규칙이 있는 조합은 제외했다.
MAN = O['man']
OWNER = {}
for sc, ds in MAN.items():
    for d in ds:
        OWNER.setdefault(d, set()).add(sc)
EXCL = {d: next(iter(scs)) for d, scs in OWNER.items() if len(scs) == 1}
ELEC = [x for x in SCEN if x not in ('ExternalFlameScenario', 'ElectricalIgnitionScenario')]

covered = {}
for r in O['rules']:
    if not r['sc'] or not r['ind']:
        continue
    tgt = ELEC if r['sc'][0] == 'ElectricalIgnitionScenario' else [r['sc'][0]]
    for t in tgt:
        covered.setdefault(t, set()).add(r['ind'][0])

d6 = []
for sc in [x for x in SCEN if x != 'ElectricalIgnitionScenario']:
    for d, own in sorted(EXCL.items(), key=lambda x: (SCEN.get(x[1], x[1]), k(x[0]))):
        if own == sc or d in covered.get(sc, set()):
            continue
        d6.append([SCEN[sc], k(d), SCEN.get(own, own),
                   f'{SCEN[sc]} 가설을 보고 있을 때 발화부에서 {k(d)}이(가) 확인되면, '
                   f'이 흔적은 {SCEN.get(own, own)}에서만 나타나므로 {SCEN[sc]}을(를) 약화시킨다 — 맞습니까?'])
sheet('6 반증 후보', ['가설', '후보 흔적', '어느 가설의 전용 흔적인가', '문장으로 읽으면'],
      d6, [12, 24, 20, 60],
      '현재 가설마다 반증 단서가 하나뿐이라 반증이 잘 작동하지 않습니다. 후보를 기계로 뽑았으니 '
      '성립하는 것만 O 로 표시해 주십시오. 대부분 X 여도 정상입니다. '
      '중요한 조건: 화재로 사라지는 것은 반증이 될 수 없습니다. 불에 타 없어질 흔적이라면 X 로 봐 주십시오.')

rows = [
    ('EFI-Onto 판단 기준 검토표', ''),
    ('', ''),
    ('무엇을 검토하는가', 'efi_tbox.ttl 에 들어 있는 판단 기준을 한글 문장으로 풀어 놓은 것입니다. '
     '온톨로지 파일을 직접 보실 필요 없이 이 표만 보시면 됩니다.'),
    ('', ''),
    ('어떻게 표시하는가', 'D열 판정에서 O / X / △ 를 고르시고, 틀렸거나 고칠 것이 있으면 E열에 적어 주십시오. '
     'O = 맞다, X = 틀렸다, △ = 경우에 따라 다르다·판단 보류'),
    ('', ''),
    ('어디부터 보는가', '시트 순서가 곧 우선순위입니다. 앞 시트일수록 결과를 크게 바꿉니다. '
     '시간이 없으시면 1번과 2번만 보셔도 됩니다.'),
    ('', ''),
    ('시트 1  단서와 점수', f'{len(d1)}건. 어떤 사실이 어느 가설을 얼마나 지지·반증하는가. '
     '가감점은 변별력에서 계산됩니다. 값 자체가 아니라 항목 사이의 순서가 뒤집힌 곳을 봐 주십시오.'),
    ('시트 2  형태 발현', f'{len(d2)}건. 어떤 발열이 어떤 흔적을 남기는가. '
     '여기가 틀리면 혼동 쌍 판정이 통째로 어긋납니다.'),
    ('시트 3  선행조건과 착화물', f'{len(d3)}건. 어떤 조건이 어떤 발열을 일으키고, 그 발열이 무엇에 불을 붙이는가.'),
    ('시트 4  현장사실과 증거물', f'{len(d4)}건. 현장에서 확인한 것이 무엇을 증언하는가. 증거물이 어떤 흔적을 지니는가.'),
    ('시트 5  용어', f'{len(d5)}건. 개념 이름과 상하위 관계. 오류 가능성은 낮으나 용어가 실무와 맞는지 봐 주십시오.'),
    ('시트 6  반증 후보', f'{len(d6)}건. 기계로 뽑은 후보입니다. 성립하는 것만 골라 주시면 됩니다.'),
    ('', ''),
    ('표 밖에서 할 검토', '이 표는 규칙이 맞는지 보는 것입니다. 규칙이 실제로 맞는 답을 내는지는 '
     '조사서 사례를 넣어 돌려 봐야 확인됩니다. 종결된 사례 10건 정도를 정답을 가린 채 넣고 '
     '시스템 결론과 실제 결론을 대조하는 것이 다음 단계입니다.'),
    ('', ''),
    ('출처에 관한 고지', '이 기준은 논문 Table 1·2 와 선행연구를 근거로 작성자가 구성한 것입니다. '
     'NFPA 921 에서 직접 가져온 것은 절차의 뼈대(가설수립·검증·확정, 반증 우선, negative corpus 배제)이며, '
     '개별 판단 기준은 국내 실무 기준입니다.'),
]
ws['A1'].font = Font(name=FONT, bold=True, size=16)
for i, (a, b) in enumerate(rows, 1):
    ws.cell(i, 1, a).font = Font(name=FONT, bold=(i == 1 or (a and not b)), size=16 if i == 1 else 10)
    c = ws.cell(i, 2, b); c.font = BODY; c.alignment = WRAP
ws.column_dimensions['A'].width = 24
ws.column_dimensions['B'].width = 95
for i in range(3, len(rows) + 1):
    ws.row_dimensions[i].height = 30

wb.save('build/EFI-Onto_검토표.xlsx')
print('rows', len(d1), len(d2), len(d3), len(d4), len(d5), len(d6))
