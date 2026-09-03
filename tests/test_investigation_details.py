"""비교·검토 범위·부착 사건열이 과도한 결론으로 바뀌지 않는 종단 시험."""
import copy

import pytest
from rdflib import Literal, RDF, URIRef

from test_investigation import record, system, run_input, focuses, at, contact, EFI
from investigation import InvestigationData, detail_questions


def comparison_data():
    return dict(system=system(), comparisons=[record('compare', component='outlet', comparator='breaker',
        kind='MetalExposure', location='문제 단자', comparator_location='옆 단자',
        finding='두꺼운 산화층', comparator_finding='얇은 표면 산화', metal='Copper', comparator_metal='Copper',
        exposure_status='Confirmed', exposure_basis='같은 함체 위치·노출 영상 대조', assessment_complete=True)],
        heating_observations=[record('feature', component='outlet', characteristic=1, detail='같은 재질보다 심한 산화', comparison='compare')])


def flag(g, name):
    return set(g.subjects(EFI[name], Literal(True)))


def test_confirmed_relative_oxidation_needs_a_confirmed_comparator():
    data = comparison_data()
    g, report = run_input(data, hypotheses=contact())
    assert flag(g, 'comparisonContextComplete')
    assert not focuses(report, 'HeatingCharacteristicObservationShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))
    assert not list(g.subjects(RDF.type, EFI.Conclusion))
    data['comparisons'][0].update(exposure_status='Unverifiable')
    g, report = run_input(data)
    assert not flag(g, 'comparisonContextComplete')
    assert focuses(report, 'DamageComparisonShape')
    assert focuses(report, 'HeatingCharacteristicObservationShape')
    assert detail_questions(g, EFI.session_test)
    data['comparisons'][0].update(exposure_status='Confirmed', comparator_metal='Steel')
    g, _ = run_input(data)
    assert not flag(g, 'comparisonContextComplete')


def test_panel_comparison_requires_explicit_outside_location_not_missing_container():
    data = comparison_data()
    data['system']['components'].append(dict(id='panel', cls='Enclosure'))
    data['system']['components'][2]['container'] = 'panel'
    data['heating_observations'] = []
    data['comparisons'][0].update(kind='PanelInsideOutside', side='Inside', comparator_side='Unknown', exposure_status='Missing')
    g, _ = run_input(data)
    assert not flag(g, 'comparisonContextComplete')
    data['comparisons'][0]['comparator_side'] = 'Outside'
    g, report = run_input(data)
    assert flag(g, 'comparisonContextComplete')
    assert not focuses(report, 'DamageComparisonShape')
    data['system']['components'][1]['container'] = 'panel'
    g, _ = run_input(data)
    assert not flag(g, 'comparisonContextComplete')


def test_one_characteristic_is_allowed_without_turning_it_into_a_cause_fact():
    data = dict(system=system(), heating_observations=[record('oxide', component='outlet', characteristic=13,
                detail='산화물 방울인지 금속 비드인지 성분 분석 필요')])
    g, report = run_input(data, hypotheses=contact())
    assert not focuses(report, 'HeatingCharacteristicObservationShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))
    assert not list(g.subjects(RDF.type, EFI.CuprousOxideGrowth))


def workflow_data():
    data = comparison_data()
    data.update(problems=[record('problem', statement='접속부 과열이 발화 전에 있었는가?')],
        plans=[record('plan1', problem='problem', scope='동종 금속의 산화 비교', method='같은 노출의 금속 대조', required_expertise='금속 산화·화재 손상 감식', complete=True),
               record('plan2', problem='problem', scope='영상 시간선', method='영상 원본 시간 대조', required_expertise='영상 시간 분석')],
        verifications=[record('verification', plan='plan1', result='산화 차이 관찰. 원인 확정은 유보', evidence_records=['compare'])],
        technical_reviews=[record('review', reviewer='reviewer', requested_plans=['plan1'], scope_kind='Selected',
            documentation_access=True, reviewer_relationship='동일 기관의 다른 조사관', complete=True,
            scopes=[record('scope1', plan='plan1', competence_basis='금속 감식 업무·교육 경력과 본 분석 범위 대조',
                documentation_access='Confirmed', access_basis='비교 사진·분석 원자료 전체 접근', critique='같은 노출 판단의 영상 근거 확인. 산화만으로 원인 결론 불가')])])
    return data


def test_problem_plan_verification_accepts_documented_absence_but_not_unknown_evidence():
    data = workflow_data()
    data['verifications'][0]['evidence_records'] = ['feature']
    data['heating_observations'][0]['status'] = 'ConfirmedAbsent'
    g, _ = run_input(data)
    assert len(flag(g, 'planVerificationSupported')) == 1
    data['heating_observations'][0]['status'] = 'Unverifiable'
    g, report = run_input(data)
    assert not flag(g, 'planVerificationSupported')
    assert focuses(report, 'InvestigationPlanShape')


def test_selected_review_cannot_be_presented_as_review_of_all_scopes():
    data = workflow_data()
    g, report = run_input(data)
    assert flag(g, 'reviewCoverageSupported')
    assert not focuses(report, 'TechnicalReviewCoverageShape')
    data['technical_reviews'][0]['scope_kind'] = 'All'
    g, report = run_input(data)
    assert not flag(g, 'reviewCoverageSupported')
    assert focuses(report, 'TechnicalReviewCoverageShape')
    data['technical_reviews'][0]['requested_plans'].append('plan2')
    scope = copy.deepcopy(data['technical_reviews'][0]['scopes'][0])
    scope.update(id='scope2', plan='plan2', competence_basis='영상 원본·시계 오차 분석 교육·실무 경력', critique='영상 촬영 장치 시각 보정 근거 검토')
    data['technical_reviews'][0]['scopes'].append(scope)
    g, _ = run_input(data)
    assert flag(g, 'reviewCoverageSupported')


@pytest.mark.parametrize('missing', ['competence_basis', 'access_basis', 'critique'])
def test_reviewer_name_and_global_access_cannot_replace_scope_evidence(missing):
    data = workflow_data()
    data['technical_reviews'][0]['scopes'][0].pop(missing)
    g, report = run_input(data)
    assert not flag(g, 'reviewCoverageSupported')
    assert focuses(report, 'TechnicalReviewCoverageShape')


def deposition_data():
    model = system()
    model['components'] += [dict(id='switch', cls='ElectricalSwitch'), dict(id='surface', cls='Insulation')]
    return dict(system=model, events=[
        record('arc', component='switch', kind='ContactArcOccurrence', earliest=at(7), latest=at(7)),
        record('breakdown', component='surface', kind='InsulationBreakdown', earliest=at(9), latest=at(9)),
        record('ignition', component='load', kind='Ignition', earliest=at(10), latest=at(10))],
        depositions=[record('deposit', component='surface', source_event='arc', source_link_basis='접점과 부착물 성분·위치 대조',
            deposit_basis='해당 절연면 금속분 분석', earliest=at(8), latest=at(8), observed_at=at(14),
            breakdown_event='breakdown', ignition_event='ignition', assessment_complete=True)])


def test_confirmed_deposition_sequence_remains_evidence_not_an_automatic_cause():
    data = deposition_data()
    g, report = run_input(data, hypotheses=contact())
    assert flag(g, 'preIgnitionDepositionSequence')
    assert not focuses(report, 'MetalDepositionSequenceShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))
    assert not list(g.subjects(RDF.type, EFI.ContaminatedEnvironment))
    assert not list(g.subjects(RDF.type, EFI.Conclusion))
    # 발생 시간이 없으면 사후 관찰 시각을 넣어도 선행 오염이 되지 않는다.
    data['depositions'][0].update(earliest=None, latest=None)
    g, report = run_input(data)
    assert not flag(g, 'preIgnitionDepositionSequence')
    assert focuses(report, 'MetalDepositionSequenceShape')


@pytest.mark.parametrize('case', ['post_fire', 'overlap', 'other_surface', 'unknown_arc', 'generic_arc'])
def test_deposition_requires_correct_target_confirmed_source_and_pre_fire_time(case):
    data = deposition_data()
    if case == 'post_fire': data['depositions'][0].update(earliest=at(11), latest=at(11))
    if case == 'overlap': data['events'][0].update(latest=at(8))
    if case == 'other_surface': data['events'][1]['component'] = 'outlet'
    if case == 'unknown_arc': data['events'][0]['status'] = 'Unverifiable'
    if case == 'generic_arc': data['events'][0]['kind'] = 'ArcOccurrence'
    g, report = run_input(data)
    assert not flag(g, 'preIgnitionDepositionSequence')
    assert focuses(report, 'MetalDepositionSequenceShape')
    assert detail_questions(g, EFI.session_test)


def test_detail_input_rejects_dangling_ids_and_client_claimed_readiness():
    data = workflow_data()
    data['technical_reviews'][0]['requested_plans'] = ['nonexistent']
    with pytest.raises(ValueError, match='unknown review plan'):
        InvestigationData.model_validate(data)
    data = deposition_data()
    data['depositions'][0]['pre_ignition_deposition_sequence'] = True
    with pytest.raises(ValueError):
        InvestigationData.model_validate(data)


def test_raw_rdf_cross_session_review_does_not_fill_missing_local_scope():
    data = workflow_data()
    data['technical_reviews'][0]['scopes'] = []
    extra = '''
    <https://w3id.org/efi-onto#session_test/investigation/record/review> efi:hasScopeAssessment efi:foreignScope .
    efi:foreignScope a efi:ReviewScopeAssessment ; efi:recordSession efi:anotherSession ;
     efi:assessesReviewPlan <https://w3id.org/efi-onto#session_test/investigation/record/plan1> ;
     efi:confirmationStatus efi:Confirmed ; efi:competenceBasis "경력" ; efi:scopeDocumentationAccess efi:Confirmed ;
     efi:scopeAccessBasis "자료 접근" ; efi:scopeCritique "비평" .
    '''
    g, report = run_input(data, extra=extra)
    assert not flag(g, 'reviewCoverageSupported')
    assert focuses(report, 'InvestigationDetailReferenceShape')


def test_a_plan_cannot_serve_as_its_own_observational_verification_evidence():
    data = workflow_data()
    data['verifications'][0]['evidence_records'] = ['plan1']
    with pytest.raises(ValueError, match='unknown evidence record'):
        InvestigationData.model_validate(data)
    data['verifications'][0]['evidence_records'] = []
    extra = '''
    <https://w3id.org/efi-onto#session_test/investigation/record/verification> efi:verificationEvidence
    <https://w3id.org/efi-onto#session_test/investigation/record/plan1> .
    '''
    g, report = run_input(data, extra=extra)
    assert not flag(g, 'planVerificationSupported')
    assert focuses(report, 'InvestigationPlanShape')
