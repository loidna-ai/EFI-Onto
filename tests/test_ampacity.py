"""허용전류 기준의 관할·조건·수치 비교를 발화 원인 추론과 분리하는 시험."""
import copy

import pytest
from pydantic import ValidationError
from rdflib import RDF

from test_investigation import record, run_input, focuses, EFI, contact
from investigation import InvestigationData, detail_questions


def data():
    return dict(
        system=record('system', components=[
            dict(id='branch', cls='BranchCircuit'),
            dict(id='wire', cls='Conductor', circuit='branch', role='Ungrounded'),
            dict(id='breaker', cls='ProtectiveDevice', circuit='branch'),
            dict(id='outlet', cls='PlugReceptacle', circuit='branch'),
        ]),
        conductor_installations=[record(
            'installation', component='wire', circuit='branch', protective_device='breaker', equipment='outlet',
            conductor_material='Copper', conductor_material_basis='[합성] 성분 분석과 제조 표기',
            size_system='mm2', size_value='2.5', size_basis='[합성] 피복 표기와 단면 측정',
            insulation_designation='XLPE-90C', insulation_basis='[합성] 제조 표기와 재질 분석',
            installation_method='InConduit', installation_method_basis='[합성] 현장 배선 경로 확인',
            bundle_condition='CableAssembly', current_carrying_conductor_count=3,
            bundle_basis='[합성] 전류 운반 도체 세 가닥 확인', ambient_temperature_C=30,
            ambient_basis='[합성] 사고 전 환경 기록', circuit_use='GeneralBranch',
            circuit_use_basis='[합성] 회로도와 부하 목록', load_current_A=18,
            load_current_basis='[합성] 사고 전 계측과 부하 재구성', protective_device_rating_A=20,
            protective_device_rating_basis='[합성] 차단기 명판 사진', equipment_rating_A=20,
            equipment_rating_basis='[합성] 콘센트 명판 사진', assessment_complete=True)],
        ampacity_references=[
            record('applicable', reference_role='ApplicableRating', basis_kind='GoverningCode',
                   jurisdiction='Republic of Korea', document_id='SYNTH-KR-ELECTRICAL-CODE', edition='2026 synthetic',
                   section='Synthetic Table 1', conductor_material='Copper', size_system='mm2', size_value='2.5',
                   insulation_designation='XLPE-90C', installation_method='InConduit',
                   bundle_condition='CableAssembly', current_carrying_conductor_count=3,
                   circuit_use='GeneralBranch', ambient_min_C=0, ambient_max_C=40,
                   ampacity_max_A=20, maximum_protective_device_rating_A=20,
                   minimum_equipment_rating_A=20,
                   applicability_scope='[합성] 국내 관할·판본과 지정 포설 조건에만 쓰는 예시 기준'),
            record('nfpa-context', reference_role='ContextOnly', basis_kind='ContextTable',
                   jurisdiction='United States', document_id='NFPA 921', edition='2024', section='Table 9.7.2',
                   conductor_material='Copper', size_system='AWG', size_value='12',
                   circuit_use='SmallApplianceBranch', ampacity_min_A=20, ampacity_max_A=25,
                   applicability_scope='미국 분기회로의 도체 크기·용도 설명 문맥. 국내 적용 정격이 아님'),
        ],
        ampacity_assessments=[record('assessment', installation='installation', reference='applicable',
                                     applicability_basis='[합성] 관할·판본과 모든 설치 조건을 항목별 대조',
                                     assessment_complete=True)],
    )


def values(graph, prop):
    return {str(value) for value in graph.objects(None, EFI[prop])}


def test_source_scoped_assessment_derives_only_comparison_results():
    graph, report = run_input(data(), hypotheses=contact())
    assert values(graph, 'conductorInstallationIdentified') == {'true'}
    assert values(graph, 'ampacityReferenceApplicable') == {'true'}
    assert values(graph, 'loadAmpacityResult') == {'Within'}
    assert values(graph, 'protectiveDeviceRatingResult') == {'Within'}
    assert values(graph, 'equipmentRatingResult') == {'Meets'}
    assert values(graph, 'ampacityAssessmentSupported') == {'true'}
    for shape in ('ConductorInstallationRecordShape', 'AmpacityReferenceShape', 'AmpacityAssessmentShape'):
        assert not focuses(report, shape)
    assert not detail_questions(graph, EFI.session_test)
    assert not list(graph.objects(EFI.session_test, EFI.hasFact))
    assert not list(graph.subjects(RDF.type, EFI.OverloadState))
    assert values(graph, 'supportScore') == {'50'}


def test_exceeding_values_are_reported_without_creating_overload_or_score():
    item = data()
    item['conductor_installations'][0].update(load_current_A=25, protective_device_rating_A=30,
                                              equipment_rating_A=15)
    graph, report = run_input(item, hypotheses=contact())
    assert values(graph, 'ampacityReferenceApplicable') == {'true'}
    assert values(graph, 'loadAmpacityResult') == {'Exceeds'}
    assert values(graph, 'protectiveDeviceRatingResult') == {'Exceeds'}
    assert values(graph, 'equipmentRatingResult') == {'Below'}
    assert values(graph, 'ampacityAssessmentSupported') == {'true'}
    assert not focuses(report, 'AmpacityAssessmentShape')
    assert not list(graph.subjects(RDF.type, EFI.OverloadState))
    assert values(graph, 'supportScore') == {'50'}


@pytest.mark.parametrize('where,value', [
    ('material', 'AluminumAlloy'), ('size_system', 'AWG'), ('size', '4'),
    ('insulation', 'PVC-70C'), ('method', 'OpenAir'), ('bundle', 'Bundled'),
    ('count', 4), ('use', 'SmallApplianceBranch'), ('ambient', -1), ('ambient', 41),
])
def test_every_declared_reference_condition_must_match(where, value):
    item = data()
    actual = item['conductor_installations'][0]
    if where == 'material': actual['conductor_material'] = value
    if where == 'size_system': actual['size_system'] = value
    if where == 'size': actual['size_value'] = value
    if where == 'insulation': actual['insulation_designation'] = value
    if where == 'method': actual['installation_method'] = value
    if where == 'bundle': actual['bundle_condition'] = value
    if where == 'count': actual['current_carrying_conductor_count'] = value
    if where == 'use': actual['circuit_use'] = value
    if where == 'ambient': actual['ambient_temperature_C'] = value
    graph, report = run_input(item)
    assert not values(graph, 'ampacityReferenceApplicable')
    assert not values(graph, 'ampacityAssessmentSupported')
    assert focuses(report, 'AmpacityAssessmentShape')
    assert detail_questions(graph, EFI.session_test)


def test_nfpa_context_table_is_stored_but_cannot_be_an_applicable_rating():
    item = data()
    item['ampacity_assessments'][0]['reference'] = 'nfpa-context'
    graph, report = run_input(item)
    assert not focuses(report, 'AmpacityReferenceShape')
    assert focuses(report, 'AmpacityAssessmentShape')
    assert not values(graph, 'ampacityReferenceApplicable')
    assert not values(graph, 'loadAmpacityResult')
    assert values(graph, 'referenceAmpacityMin_A') == {'20.0'}
    assert '25.0' in values(graph, 'referenceAmpacityMax_A')
    assert not list(graph.subjects(RDF.type, EFI.OverloadState))


@pytest.mark.parametrize('change', ['missing_insulation', 'missing_method', 'unknown_bundle',
                                     'missing_count', 'missing_protection_limit', 'context_as_rating'])
def test_conditionless_applicable_reference_is_rejected(change):
    item = data()
    ref = item['ampacity_references'][0]
    item['ampacity_assessments'][0]['assessment_complete'] = False
    if change == 'missing_insulation': ref['insulation_designation'] = None
    if change == 'missing_method': ref['installation_method'] = None
    if change == 'unknown_bundle': ref['bundle_condition'] = 'Unknown'
    if change == 'missing_count': ref['current_carrying_conductor_count'] = None
    if change == 'missing_protection_limit': ref['maximum_protective_device_rating_A'] = None
    if change == 'context_as_rating': ref['basis_kind'] = 'ContextTable'
    _, report = run_input(item)
    assert focuses(report, 'AmpacityReferenceShape')


@pytest.mark.parametrize('change', ['unknown_material', 'no_size_basis', 'no_insulation_basis',
                                     'no_bundle_basis', 'no_load_basis', 'no_protection_basis',
                                     'equipment_without_rating'])
def test_incomplete_actual_conditions_cannot_be_marked_complete(change):
    item = data()
    actual = item['conductor_installations'][0]
    if change == 'unknown_material': actual['conductor_material'] = 'Unknown'
    if change == 'no_size_basis': actual['size_basis'] = None
    if change == 'no_insulation_basis': actual['insulation_basis'] = None
    if change == 'no_bundle_basis': actual['bundle_basis'] = None
    if change == 'no_load_basis': actual['load_current_basis'] = None
    if change == 'no_protection_basis': actual['protective_device_rating_basis'] = None
    if change == 'equipment_without_rating': actual['equipment_rating_A'] = None
    graph, report = run_input(item)
    assert not values(graph, 'conductorInstallationIdentified')
    assert focuses(report, 'ConductorInstallationRecordShape')
    assert focuses(report, 'AmpacityAssessmentShape')


def test_unknown_records_remain_questions_and_do_not_mean_absence():
    item = data()
    item['conductor_installations'][0].update(conductor_material='Unknown', assessment_complete=False)
    item['ampacity_assessments'][0]['assessment_complete'] = False
    graph, report = run_input(item)
    assert not focuses(report, 'ConductorInstallationRecordShape')
    assert not focuses(report, 'AmpacityAssessmentShape')
    assert len(detail_questions(graph, EFI.session_test)) == 2
    assert not list(graph.subjects(RDF.type, EFI.ConfirmedAbsent))


def test_awg_and_square_millimetres_are_not_implicitly_converted():
    item = data()
    item['ampacity_references'][0].update(size_system='AWG', size_value='14')
    graph, report = run_input(item)
    assert not values(graph, 'ampacityReferenceApplicable')
    assert focuses(report, 'AmpacityAssessmentShape')


def test_wrong_circuit_links_are_detected():
    item = data()
    item['system']['components'].append(dict(id='other', cls='BranchCircuit'))
    item['system']['components'][1]['circuit'] = 'other'
    graph, report = run_input(item)
    assert not values(graph, 'conductorInstallationIdentified')
    assert focuses(report, 'ConductorInstallationRecordShape')


def test_reversed_reference_ranges_are_invalid():
    for change in ('ampacity', 'ambient'):
        item = data()
        item['ampacity_assessments'][0]['assessment_complete'] = False
        if change == 'ampacity': item['ampacity_references'][0].update(ampacity_min_A=30, ampacity_max_A=20)
        else: item['ampacity_references'][0].update(ambient_min_C=40, ambient_max_C=0)
        _, report = run_input(item)
        assert focuses(report, 'AmpacityReferenceShape')


def test_raw_cross_session_reference_is_rejected():
    item = data()
    item['ampacity_assessments'][0]['assessment_complete'] = False
    extra = '''
    <https://w3id.org/efi-onto#session_test/investigation/record/assessment>
       efi:comparedAmpacityReference <urn:other-reference> .
    <urn:other-reference> a efi:AmpacityReference ; efi:recordSession <urn:other-session> .
    '''
    _, report = run_input(item, extra=extra)
    assert focuses(report, 'InvestigationDetailReferenceShape')


def test_only_the_actual_installation_is_observational_verification_evidence():
    item = data()
    item.update(problems=[record('problem', statement='허용전류 조건 확인')],
                plans=[record('plan', problem='problem', scope='분기회로', method='표기·도면·계측 대조',
                              required_expertise='전기 설비')],
                verifications=[record('verification', plan='plan', evidence_records=['applicable'])])
    with pytest.raises(ValidationError, match='unknown evidence'):
        InvestigationData.model_validate(item)
    item['verifications'][0]['evidence_records'] = ['assessment']
    with pytest.raises(ValidationError, match='unknown evidence'):
        InvestigationData.model_validate(item)
    item['verifications'][0]['evidence_records'] = ['installation']
    assert InvestigationData.model_validate(item)


def test_unknown_ids_wrong_types_blank_sources_and_forged_flags_fail_input():
    changes = ('installation', 'reference', 'wrong_conductor', 'wrong_protection', 'blank', 'flag')
    for change in changes:
        item = copy.deepcopy(data())
        if change == 'installation': item['ampacity_assessments'][0]['installation'] = 'missing'
        if change == 'reference': item['ampacity_assessments'][0]['reference'] = 'missing'
        if change == 'wrong_conductor': item['conductor_installations'][0]['component'] = 'outlet'
        if change == 'wrong_protection': item['conductor_installations'][0]['protective_device'] = 'outlet'
        if change == 'blank': item['ampacity_references'][0]['source'] = ' '
        if change == 'flag': item['ampacity_assessments'][0]['ampacityAssessmentSupported'] = True
        with pytest.raises(ValidationError):
            InvestigationData.model_validate(item)
