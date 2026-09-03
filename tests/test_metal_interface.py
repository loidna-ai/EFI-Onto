"""접속 금속 문헌의 범위를 실제 설비의 보편 원인 규칙으로 바꾸지 않는 시험."""
import pytest
from pydantic import ValidationError
from rdflib import RDF

from test_investigation import record, run_input, focuses, EFI, contact
from investigation import InvestigationData, detail_questions


def data():
    return dict(system=record('system', components=[
        dict(id='branch',cls='BranchCircuit'), dict(id='device',cls='PlugReceptacle',circuit='branch'),
        dict(id='terminal',cls='ConnectionPoint',container='device',circuit='branch',role='Ungrounded'),
        dict(id='wire',cls='Conductor',circuit='branch',role='Ungrounded'),
        dict(id='screw',cls='TerminalFastener',container='terminal')],
        connections=[record('link',from_component='wire',to_component='terminal')]),
        terminations=[record('term',component='terminal',device='device',conductor='wire',connection='link',
            method='ScrewTerminal',conductor_material='AluminumAlloy',conductor_material_basis='[합성] 성분 분석과 제조 기록',
            conductor_alloy_grade='EC-H19',conductor_form='Solid',conductor_size='12 AWG',product_id='SYNTH-OLD-OUTLET',
            identification_basis='[합성] 실제 단자 구조 확인',assessment_complete=True)],
        mating_contacts=[record('mate',component='screw',termination='term',base_material='Steel',surface_coating='Zinc',
            material_basis='[합성] 나사 모재 분석',coating_basis='[합성] 표면 도금 분석',assessment_complete=True)],
        metal_interface_references=[record('reference',basis_kind='HistoricalStudy',conductor_material='AluminumAlloy',
            conductor_alloy_grade='EC-H19',conductor_size='12 AWG',conductor_form='Solid',termination_method='ScrewTerminal',
            mating_material='Steel',mating_coating='Zinc',installation_region='United States',
            installation_year_from=1964,installation_year_to=1972,installation_use='BranchCircuit',device_marking='AL-CU',
            applicability_scope='[합성 구조] Ignition Handbook pp.762–764의 미국 소구경 분기배선·구형 접속 조건')],
        metal_interface_comparisons=[record('comparison',termination='term',mating_contact='mate',reference='reference',
            installation_region='United States',installation_year=1970,installation_use='BranchCircuit',
            installation_use_basis='[합성] 분기회로 도면',device_marking='AL-CU',
            device_marking_basis='[합성] 기기 표시 사진',connector_approval_status='Confirmed',
            approval_basis='[합성] 당시 제품 자료의 적용 범위 확인',
            applicability_basis='[합성] 도체 등급·크기·나사 모재·도금·지역·연도·용도를 항목별 대조',assessment_complete=True)])


def values(g, prop):
    return {str(x) for x in g.objects(None, EFI[prop])}


def test_scoped_historical_comparison_does_not_create_a_cause_or_score():
    g, report=run_input(data(),hypotheses=contact())
    assert values(g,'conductorMaterialIdentified')=={'true'}
    assert values(g,'matingContactIdentified')=={'true'}
    assert values(g,'metalInterfaceComparisonSupported')=={'true'}
    assert not focuses(report,'MetalInterfaceComparisonShape')
    assert not detail_questions(g,EFI.session_test)
    assert not list(g.objects(EFI.session_test,EFI.hasFact))
    assert not list(g.subjects(RDF.type,EFI.GlowingConnection))
    assert values(g,'supportScore')=={'50'}


@pytest.mark.parametrize('where,value',[
    ('material','Copper'),('grade','AA-8000'),('size','10 AWG'),('form','Stranded'),('method','PushInSpring'),
    ('mating','Brass'),('coating','Tin'),('use','ServiceEntrance'),('marking','CO-ALR'),
    ('region','Republic of Korea'),('year',1963),('year',1973),('approval','Missing')])
def test_historical_result_requires_every_declared_condition(where,value):
    x=data()
    if where=='material':x['terminations'][0]['conductor_material']=value
    if where=='grade':x['terminations'][0]['conductor_alloy_grade']=value
    if where=='size':x['terminations'][0]['conductor_size']=value
    if where=='form':x['terminations'][0]['conductor_form']=value
    if where=='method':x['terminations'][0]['method']=value
    if where=='mating':x['mating_contacts'][0]['base_material']=value
    if where=='coating':x['mating_contacts'][0]['surface_coating']=value
    if where=='use':x['metal_interface_comparisons'][0]['installation_use']=value
    if where=='marking':x['metal_interface_comparisons'][0]['device_marking']=value
    if where=='region':x['metal_interface_comparisons'][0]['installation_region']=value
    if where=='year':x['metal_interface_comparisons'][0]['installation_year']=value
    if where=='approval':x['metal_interface_comparisons'][0]['connector_approval_status']=value
    g,report=run_input(x)
    assert not values(g,'metalInterfaceComparisonSupported')
    assert focuses(report,'MetalInterfaceComparisonShape')
    assert detail_questions(g,EFI.session_test)


@pytest.mark.parametrize('change',['unknown_conductor','no_conductor_basis','unknown_form','unknown_mating','no_coating_basis','other_component'])
def test_unidentified_materials_and_wrong_contact_cannot_complete_comparison(change):
    x=data()
    if change=='unknown_conductor':x['terminations'][0]['conductor_material']='Unknown'
    if change=='no_conductor_basis':x['terminations'][0]['conductor_material_basis']=None
    if change=='unknown_form':x['terminations'][0]['conductor_form']='Unknown'
    if change=='unknown_mating':x['mating_contacts'][0]['base_material']='Unknown'
    if change=='no_coating_basis':x['mating_contacts'][0]['coating_basis']=None
    if change=='other_component':
        x['system']['components'].append(dict(id='other-screw',cls='TerminalFastener'))
        x['mating_contacts'][0]['component']='other-screw'
    g,report=run_input(x)
    assert not values(g,'metalInterfaceComparisonSupported')
    assert focuses(report,'MetalInterfaceComparisonShape')
    if change in ('unknown_mating','no_coating_basis','other_component'):
        assert focuses(report,'MatingContactRecordShape')


def test_scientific_oxide_reference_is_stored_without_historical_scope_or_inference():
    x=data();x['terminations'][0].update(conductor_material='PureAluminum',conductor_alloy_grade=None)
    x['metal_interface_references'][0]=record('reference',basis_kind='ScientificSource',conductor_material='PureAluminum',
        conductor_oxide_behavior='NegligibleConductivity',
        glow_path_explanation='[문헌 설명] 산화막 통전이 아니라 중간 전도도의 금속간화합물 경로가 제안됨',
        applicability_scope='Ignition Handbook p.550의 알루미늄 산화막·제안 메커니즘 설명')
    x['metal_interface_comparisons'][0].update(installation_region=None,installation_year=None,device_marking='None',
        device_marking_basis='[합성] 표시 없음 확인',connector_approval_status='ConfirmedAbsent',
        approval_basis='[합성] 과학 문헌 대조에는 제품 승인 판단을 적용하지 않음',
        applicability_basis='[합성] 순알루미늄 시료의 산화막 설명만 대조')
    g,report=run_input(x)
    assert values(g,'metalInterfaceComparisonSupported')=={'true'}
    assert values(g,'referenceConductorOxideBehavior')=={'NegligibleConductivity'}
    assert not focuses(report,'MetalInterfaceReferenceShape')
    assert not list(g.subjects(RDF.type,EFI.GlowingConnection))
    assert not list(g.objects(EFI.session_test,EFI.hasFact))


def test_pure_aluminum_is_not_retyped_as_alloy_and_copper_oxide_is_separate():
    x=data();x['terminations'][0].update(conductor_material='PureAluminum',conductor_alloy_grade=None)
    x['metal_interface_comparisons'][0]['assessment_complete']=False
    x['metal_interface_references'][0]=record('reference',basis_kind='ScientificSource',conductor_material='Copper',
        conductor_oxide_behavior='Semiconductive',applicability_scope='Ignition Handbook p.550의 구리 산화물 설명')
    g,report=run_input(x)
    assert values(g,'terminationConductorMaterial')=={'PureAluminum'}
    assert not list(g.subjects(RDF.type,EFI.AlloyConductor))
    assert not values(g,'metalInterfaceComparisonSupported')
    assert not focuses(report,'MetalInterfaceComparisonShape')
    assert detail_questions(g,EFI.session_test)


def test_historical_reference_without_scope_and_reversed_period_is_invalid():
    for change in ('no_region','no_coating','reversed'):
        x=data();x['metal_interface_comparisons'][0]['assessment_complete']=False
        if change=='no_region':x['metal_interface_references'][0]['installation_region']=None
        if change=='no_coating':x['metal_interface_references'][0]['mating_coating']=None
        if change=='reversed':x['metal_interface_references'][0].update(installation_year_from=1972,installation_year_to=1964)
        _,report=run_input(x)
        assert focuses(report,'MetalInterfaceReferenceShape')

    x=data();x['metal_interface_comparisons'][0]['assessment_complete']=False
    x['metal_interface_references'][0]=record('reference',basis_kind='ScientificSource',conductor_material='Copper',
        applicability_scope='출처의 범위를 적었으나 산화막 특성·제안 경로가 없음')
    _,report=run_input(x)
    assert focuses(report,'MetalInterfaceReferenceShape')


def test_incomplete_records_are_saved_as_questions_without_false_absence():
    x=data();x['mating_contacts'][0].update(base_material='Unknown',assessment_complete=False)
    x['metal_interface_comparisons'][0]['assessment_complete']=False
    g,report=run_input(x)
    assert not focuses(report,'MatingContactRecordShape')
    assert not focuses(report,'MetalInterfaceComparisonShape')
    assert detail_questions(g,EFI.session_test)
    assert not list(g.subjects(RDF.type,EFI.ConfirmedAbsent))


def test_raw_cross_session_reference_is_rejected():
    x=data();x['metal_interface_comparisons'][0]['assessment_complete']=False
    extra='''
    <https://w3id.org/efi-onto#session_test/investigation/record/comparison>
       efi:comparedMetalReference <urn:other-reference> .
    <urn:other-reference> a efi:MetalInterfaceReference ; efi:recordSession <urn:other-session> .
    '''
    _,report=run_input(x,extra=extra)
    assert focuses(report,'InvestigationDetailReferenceShape')


def test_reference_and_comparison_are_not_observational_verification_evidence():
    x=data();x.update(problems=[record('problem',statement='접속 금속 확인')],
        plans=[record('plan',problem='problem',scope='접속부',method='성분 분석',required_expertise='금속 분석')],
        verifications=[record('verification',plan='plan',evidence_records=['reference'])])
    with pytest.raises(ValidationError,match='unknown evidence'):InvestigationData.model_validate(x)
    x['verifications'][0]['evidence_records']=['mate']
    assert InvestigationData.model_validate(x)


def test_unknown_ids_blank_sources_and_forged_flags_fail_input():
    for change in ('contact','reference','blank','flag'):
        x=data()
        if change=='contact':x['metal_interface_comparisons'][0]['mating_contact']='not-a-record'
        if change=='reference':x['metal_interface_comparisons'][0]['reference']='not-a-record'
        if change=='blank':x['mating_contacts'][0]['source']=' '
        if change=='flag':x['metal_interface_comparisons'][0]['metalInterfaceComparisonSupported']=True
        with pytest.raises(ValidationError):InvestigationData.model_validate(x)
