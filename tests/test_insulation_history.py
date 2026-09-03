"""가열·수분의 출처와 시간 선후가 원인·시험 임계값으로 바뀌지 않는지 검증한다."""
import pytest
from pydantic import ValidationError
from rdflib import RDF

from test_investigation import record, run_input, focuses, at, contact, EFI
from investigation import InvestigationData, detail_questions


def data():
    return dict(system=record('system', components=[dict(id='insulation', cls='Insulation')]),
        examinations=[record('exam', component='insulation', damage_state='Damaged', insulation_material='PVC',
            insulation_material_basis='[합성] 해당 절연 시료의 재질 분석', insulation_filler='CalciumCarbonate',
            insulation_filler_basis='[합성] 해당 시료 충전재 성분 분석', observed_at=at(14))],
        insulation_exposures=[
            record('heat', component='insulation', kind='Heating', earliest=at(6), latest=at(7),
                temperature_min_C='115.25', temperature_max_C='120.5', temperature_basis_kind='Measured',
                exposure_basis='[합성] 해당 시료 위치 온도 로그 및 시간 보정', observed_at=at(14)),
            record('moisture', component='insulation', kind='SurfaceMoisture', earliest=at(8), latest=at(9),
                moisture_presence='Present', moisture_origin='AmbientAir',
                exposure_basis='[합성] 표면 수분·유래·발생 시각 조사 근거', observed_at=at(14))],
        events=[record('fire', component='insulation', kind='Ignition', earliest=at(10), latest=at(11))],
        insulation_history_reviews=[record('review', examination='exam', heating='heat', moisture='moisture',
            ignition_event='fire', applicability_basis='[합성] §9.9.4.5.1의 재질·충전재·온도·수분 조건을 대조. 메커니즘 성립은 별도 검증.',
            assessment_complete=True, claim_pre_ignition_sequence=True)])


def values(g, prop):
    return {str(x) for x in g.objects(None, EFI[prop])}


def test_documented_history_and_sequence_do_not_create_causal_facts_or_scores():
    g, report = run_input(data(), hypotheses=contact())
    assert values(g, 'insulationHistoryDocumented') == {'true'}
    assert values(g, 'preIgnitionHeatingMoistureSupported') == {'true'}
    assert not focuses(report, 'InsulationHistoryReviewShape')
    assert not focuses(report, 'PreIgnitionInsulationSequenceShape')
    assert not detail_questions(g, EFI.session_test)
    assert not list(g.objects(EFI.session_test, EFI.hasFact))
    for cls in ('ThermalDegradation', 'MoistureExposure', 'ContaminatedEnvironment', 'CarbonizedConductivePath'):
        assert not list(g.subjects(RDF.type, EFI[cls]))
    assert values(g, 'supportScore') == {'50'}
    assert values(g, 'exposureTemperatureMin_C') == {'115.25'}


@pytest.mark.parametrize('temperature', ['109.9', '110', '110.1'])
def test_110_degrees_is_not_a_universal_decision_boundary(temperature):
    x=data();x['insulation_exposures'][0].update(temperature_min_C=temperature, temperature_max_C=temperature)
    g, report=run_input(x)
    assert values(g, 'insulationHistoryDocumented') == {'true'}
    assert values(g, 'preIgnitionHeatingMoistureSupported') == {'true'}
    assert not focuses(report, 'InsulationHistoryReviewShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))


@pytest.mark.parametrize('change', ['unknown_filler', 'no_material_basis', 'no_temperature', 'unknown_moisture', 'missing_moisture', 'unknown_origin'])
def test_temperature_alone_cannot_complete_missing_context(change):
    x=data()
    if change=='unknown_filler':x['examinations'][0]['insulation_filler']='Unknown'
    if change=='no_material_basis':x['examinations'][0]['insulation_material_basis']=None
    if change=='no_temperature':x['insulation_exposures'][0]['temperature_min_C']=None
    if change=='unknown_moisture':x['insulation_exposures'][1]['moisture_presence']='Unknown'
    if change=='missing_moisture':x['insulation_exposures'][1]['status']='Missing'
    if change=='unknown_origin':x['insulation_exposures'][1]['moisture_origin']='Unknown'
    g, report=run_input(x)
    assert not values(g, 'insulationHistoryDocumented')
    assert not values(g, 'preIgnitionHeatingMoistureSupported')
    assert focuses(report, 'InsulationHistoryReviewShape')
    assert detail_questions(g, EFI.session_test)


def test_incomplete_review_can_be_saved_with_questions():
    x=data();x['examinations'][0]['insulation_filler']='Unknown'
    x['insulation_history_reviews'][0].update(assessment_complete=False, claim_pre_ignition_sequence=False)
    g, report=run_input(x)
    assert not focuses(report, 'InsulationHistoryReviewShape')
    assert not focuses(report, 'PreIgnitionInsulationSequenceShape')
    assert detail_questions(g, EFI.session_test)


def test_non_pvc_or_no_filler_can_be_documented_without_asserting_source_applicability():
    x=data();x['examinations'][0].update(insulation_material='Polyethylene', insulation_filler='None')
    x['insulation_history_reviews'][0]['applicability_basis']='[합성] PVC·탄산칼슘 조건과 달라 해당 설명을 적용하지 않음.'
    g, report=run_input(x)
    assert values(g, 'insulationHistoryDocumented') == {'true'}
    assert not focuses(report, 'InsulationHistoryReviewShape')
    assert not list(g.objects(EFI.session_test, EFI.hasFact))


def test_confirmed_surface_dryness_is_documentable_but_not_a_wetting_sequence():
    x=data();x['insulation_exposures'][1].update(moisture_presence='Absent', moisture_origin=None)
    g, report=run_input(x)
    assert values(g, 'insulationHistoryDocumented') == {'true'}
    assert not focuses(report, 'InsulationHistoryReviewShape')
    assert not values(g, 'preIgnitionHeatingMoistureSupported')
    assert focuses(report, 'PreIgnitionInsulationSequenceShape')


@pytest.mark.parametrize('timing', ['post_fire', 'overlap_fire', 'overlap_heat', 'observation_only'])
def test_post_fire_observation_is_not_pre_fire_exposure(timing):
    x=data();wet=x['insulation_exposures'][1]
    if timing=='post_fire':wet.update(earliest=at(12), latest=at(13), moisture_origin='DirectWater')
    if timing=='overlap_fire':wet.update(earliest=at(9), latest=at(10))
    if timing=='overlap_heat':wet.update(earliest=at(7), latest=at(8))
    if timing=='observation_only':wet.update(earliest=None,latest=None)
    g, report=run_input(x)
    assert not values(g, 'preIgnitionHeatingMoistureSupported')
    assert focuses(report, 'PreIgnitionInsulationSequenceShape')


def test_other_insulation_and_swapped_exposure_records_do_not_complete_review():
    x=data();x['system']['components'].append(dict(id='other',cls='Insulation'))
    x['insulation_exposures'][1]['component']='other'
    g, report=run_input(x)
    assert not values(g, 'insulationHistoryDocumented')
    assert focuses(report, 'InsulationHistoryReviewShape')
    x=data();x['insulation_history_reviews'][0].update(heating='moisture',moisture='heat')
    g, report=run_input(x)
    assert not values(g, 'insulationHistoryDocumented')
    assert focuses(report, 'InsulationHistoryReviewShape')


def test_reversed_ranges_and_mixed_observation_kinds_are_rejected():
    x=data();x['insulation_exposures'][0].update(temperature_min_C='130', earliest=at(8), moisture_presence='Present')
    g, report=run_input(x)
    assert focuses(report, 'InsulationExposureShape')
    assert not values(g, 'insulationHistoryDocumented')


def test_raw_rdf_cross_session_reference_is_rejected():
    # Pydantic이 참조를 검사해도 RDF 입력의 세션 경계를 SHACL이 독립 검증한다.
    x=data();x['insulation_history_reviews'][0].update(assessment_complete=False, claim_pre_ignition_sequence=False)
    extra='''
    <https://w3id.org/efi-onto#session_test/investigation/record/review>
       efi:historyIgnitionRecord <urn:other-fire> .
    <urn:other-fire> a efi:ElectricalEventRecord ; efi:recordSession <urn:other-session> .
    '''
    _, report=run_input(x,extra=extra)
    assert focuses(report, 'InvestigationDetailReferenceShape')


def test_invalid_references_nonfinite_temperature_and_forged_flags_fail_input():
    for change in ('missing','nan','flag','blank_source'):
        x=data()
        if change=='missing':x['insulation_history_reviews'][0]['heating']='not-a-record'
        if change=='nan':x['insulation_exposures'][0]['temperature_min_C']='NaN'
        if change=='flag':x['insulation_history_reviews'][0]['insulationHistoryDocumented']=True
        if change=='blank_source':x['insulation_exposures'][0]['source']=' '
        with pytest.raises(ValidationError):InvestigationData.model_validate(x)


def test_history_review_cannot_cite_itself_as_observational_verification():
    x=data();x.update(problems=[record('problem',statement='열이력 자료 확인')],
        plans=[record('plan',problem='problem',scope='시료',method='기록 대조',required_expertise='재질 분석')],
        verifications=[record('verification',plan='plan',evidence_records=['review'])])
    with pytest.raises(ValidationError,match='unknown evidence'):InvestigationData.model_validate(x)
    x['verifications'][0]['evidence_records']=['heat','moisture']
    assert InvestigationData.model_validate(x)
