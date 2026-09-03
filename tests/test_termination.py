"""실험 토크·사후 측정·접속 구조를 발화 전 접촉불량으로 오인하지 않는 시험."""
import copy

import pytest
from rdflib import Literal, RDF

from test_investigation import record, run_input, focuses, at, contact, EFI
from investigation import InvestigationData, detail_questions


def data():
    return dict(system=record('system', components=[
        dict(id='device', cls='PlugReceptacle'),
        dict(id='terminal', cls='ConnectionPoint', container='device', role='Ungrounded'),
        dict(id='wire', cls='Conductor', role='Ungrounded'),
        dict(id='screw', cls='TerminalFastener', container='terminal')],
        connections=[record('link', from_component='wire', to_component='terminal')]),
        events=[record('fire', component='device', kind='Ignition', earliest=at(10), latest=at(10))],
        terminations=[record('term', component='terminal', device='device', conductor='wire', connection='link',
            method='ScrewTerminal', conductor_material='Copper', conductor_size='14 AWG', product_id='SYNTH-R1 rev.A',
            terminal_marking='L, 황동색 나사 단자', identification_basis='[합성] 단자 사진과 실제 구조 대조', assessment_complete=True)],
        fasteners=[record('fastener', component='screw', termination='term', material='Steel', magnetic_response='Attracted',
            identification_method='MaterialAnalysis', identification_basis='[합성] 해당 나사 성분 분석')],
        torque_measurements=[record('measurement', termination='term', fastener='fastener', value_Nm='0.5',
            quantity_kind='AppliedTightening', phase='BeforeFire', measured_at=at(8), observed_at=at(14),
            measurement_method='[합성] 교정된 계측기 작업 기록', timing_basis='[합성] 발화 전 설치 작업 로그', ignition_event='fire')],
        torque_references=[record('reference', basis_kind='Manufacturer', product_id='SYNTH-R1 rev.A',
            termination_method='ScrewTerminal', conductor_material='Copper', conductor_size='14 AWG', fastener_material='Steel',
            quantity_kind='AppliedTightening', minimum_Nm='1.0', maximum_Nm='1.2', applicability_scope='[합성] 해당 모델·개정·도체·단자 조건의 예시 범위')],
        torque_comparisons=[record('comparison', measurement='measurement', reference='reference',
            applicability_basis='[합성] 같은 제품 개정·단자·도체 조건 확인', assessment_complete=True, claim_pre_fire_applied_torque=True)])


def values(g, prop):
    return {str(x) for x in g.objects(None, EFI[prop])}


def test_product_scoped_comparison_does_not_create_a_cause_or_a_score():
    g, report = run_input(data(), hypotheses=contact())
    assert values(g, 'torqueComparisonResult') == {'BelowMinimum'}
    assert values(g, 'preFireAppliedTorqueSupported') == {'true'}
    assert not focuses(report, 'TorqueComparisonShape')
    assert not focuses(report, 'PreFireAppliedTorqueShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))
    assert not list(g.subjects(RDF.type, EFI.LooseConnection))
    assert not list(g.subjects(RDF.type, EFI.InsufficientContactPressure))
    assert values(g, 'supportScore') == {'50'}


def test_spring_and_screw_clamp_back_wiring_are_different_structures():
    x=data();x['terminations'][0]['method']='PushInSpring'
    g, report=run_input(x)
    assert values(g, 'terminationContextSupported') == {'true'}
    assert not values(g, 'torqueComparisonResult')
    assert focuses(report, 'TorqueComparisonShape')
    x['terminations'][0]['method']='PushInScrewClamp'
    x['torque_references'][0]['termination_method']='PushInScrewClamp'
    g, report=run_input(x)
    assert values(g, 'torqueComparisonResult') == {'BelowMinimum'}
    assert not focuses(report, 'TorqueComparisonShape')


def test_unknown_link_and_different_device_cannot_complete_a_termination():
    x=data();x['system']['connections'][0]['status']='Unverifiable'
    g, report=run_input(x)
    assert not values(g, 'terminationContextSupported')
    assert not values(g, 'torqueComparisonResult')
    assert focuses(report, 'TerminationRecordShape')
    x=data();x['system']['components'].append(dict(id='other',cls='PlugReceptacle'))
    x['terminations'][0]['device']='other'
    g, report=run_input(x)
    assert not values(g, 'terminationContextSupported')
    assert focuses(report, 'TerminationRecordShape')


def test_magnet_response_does_not_automatically_identify_brass_or_steel():
    x=data();x['fasteners'][0].update(material='Unknown',magnetic_response='NotAttracted',identification_method='Magnet',identification_basis=None)
    g, report=run_input(x)
    assert values(g, 'fastenerMaterial') == {'Unknown'}
    assert not values(g, 'fastenerMaterialSupported')
    assert not values(g, 'torqueComparisonResult')
    assert detail_questions(g,EFI.session_test)
    x['fasteners'][0]['magnetic_response']='Attracted'
    g,_=run_input(x)
    assert values(g, 'fastenerMaterial') == {'Unknown'}
    assert not values(g, 'fastenerMaterialSupported')


@pytest.mark.parametrize('field,value', [('product_id','OTHER-R2'),('conductor_size','12 AWG'),('conductor_material','AluminumAlloy'),('fastener_material','Brass')])
def test_reference_for_a_different_product_or_material_does_not_apply(field,value):
    x=data();x['torque_references'][0][field]=value
    g,report=run_input(x)
    assert not values(g,'torqueComparisonResult')
    assert focuses(report,'TorqueComparisonShape')


def test_study_value_is_not_a_manufacturer_requirement_even_with_matching_metadata():
    x=data();x['torque_references'][0].update(basis_kind='Study',minimum_Nm='0.7',maximum_Nm=None,
        source='Babrauskas p.759, 특정 14 AWG 구리선 연구',applicability_scope='기존 시험 조건')
    g,report=run_input(x)
    assert not values(g,'torqueComparisonResult')
    assert focuses(report,'TorqueComparisonShape')
    assert not list(g.objects(EFI.session_test,EFI.hasFact))


def test_breakaway_torque_is_not_an_applied_tightening_measurement():
    x=data();x['torque_measurements'][0].update(quantity_kind='BreakawayLoosening',phase='AsFoundAfterFire',measured_at=at(14))
    g,report=run_input(x)
    assert not values(g,'torqueComparisonResult')
    assert not values(g,'preFireAppliedTorqueSupported')
    assert focuses(report,'TorqueComparisonShape')
    assert focuses(report,'PreFireAppliedTorqueShape')


@pytest.mark.parametrize('change', ['after_handling','false_before_fire','unknown_fire','missing_time'])
def test_after_fire_or_uncertain_timing_cannot_support_pre_fire_applied_torque(change):
    x=data()
    if change=='after_handling':x['torque_measurements'][0].update(phase='AfterHandling',measured_at=at(14))
    if change=='false_before_fire':x['torque_measurements'][0]['measured_at']=at(14)
    if change=='unknown_fire':x['events'][0]['status']='Unverifiable'
    if change=='missing_time':x['torque_measurements'][0]['measured_at']=None
    g,report=run_input(x)
    assert not values(g,'preFireAppliedTorqueSupported')
    assert focuses(report,'PreFireAppliedTorqueShape')
    assert not list(g.objects(EFI.session_test,EFI.hasFact))


def test_one_sided_reference_does_not_invent_a_missing_upper_bound():
    x=data();x['torque_measurements'][0]['value_Nm']='2.0';x['torque_references'][0]['maximum_Nm']=None
    g,report=run_input(x)
    assert values(g,'torqueComparisonResult') == {'AtOrAboveMinimum'}
    assert not focuses(report,'TorqueComparisonShape')
    x['torque_references'][0].update(minimum_Nm='1.2',maximum_Nm='1.0')
    g,report=run_input(x)
    assert not values(g,'torqueComparisonResult')
    assert focuses(report,'TorqueComparisonShape')


def test_decimal_boundary_is_preserved_and_invalid_measurements_are_rejected():
    x=data();x['torque_measurements'][0]['value_Nm']='1.2000'
    g,_=run_input(x)
    assert values(g,'torqueComparisonResult') == {'WithinRange'}
    for v in ['-0.1','NaN','Infinity']:
        bad=copy.deepcopy(x);bad['torque_measurements'][0]['value_Nm']=v
        with pytest.raises(ValueError):InvestigationData.model_validate(bad)
    x['torque_measurements'][0]['termination']='absent'
    with pytest.raises(ValueError,match='unknown torque termination'):InvestigationData.model_validate(x)


def test_a_different_session_cannot_supply_the_torque_reference():
    x=data();x['torque_comparisons'][0]['assessment_complete']=False
    # RDF로 추가한 다른 세션의 기준도 일반 기록 연결 제약이 검사한다.
    extra='''
    <https://w3id.org/efi-onto#session_test/investigation/record/comparison> efi:comparedTorqueReference efi:foreignReference .
    efi:foreignReference a efi:TorqueReference ; efi:recordSession efi:foreignSession .
    '''
    _,report=run_input(x,extra=extra)
    assert focuses(report,'InvestigationDetailReferenceShape')
