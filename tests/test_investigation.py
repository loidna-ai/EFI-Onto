"""연결·시각·연료의 미확인 정보를 확정 사실로 승격하지 않는 종단 시험."""
import copy
import sys

import pytest
from rdflib import Graph, Namespace, RDF, SH, URIRef
from pyshacl import validate
from test_ontology import ROOT, TTL, EFI

sys.path.insert(0, str(ROOT / 'src'))
from efi_schema import Hypothesis, Mechanism, Scenario, Session, ontology_text
from investigation import InvestigationData, supply_questions

PROV = Namespace('http://www.w3.org/ns/prov#')


def record(id, **fields):
    return dict(id=id, status='Confirmed', attributed_to='investigator',
                source='현장 사진/기록 ' + id, **fields)


def system():
    return record('supply', components=[
        dict(id='grid', cls='PowerSource'), dict(id='breaker', cls='ProtectiveDevice'),
        dict(id='outlet', cls='PlugReceptacle'), dict(id='load', cls='ElectricalLoad')],
        connections=[record('link1', from_component='grid', to_component='breaker'),
                     record('link2', from_component='breaker', to_component='outlet'),
                     record('link3', from_component='outlet', to_component='load')],
        paths=[record('path', source_component='grid', load_component='load')],
        review_complete=True, source_inventory_complete=True)


def run_input(data, case='test', extra='', hypotheses=None, proposed=None):
    session = Session(case_id=case, investigation=InvestigationData.model_validate(data),
                      hypotheses=hypotheses or [], proposed_conclusion=proposed)
    g = Graph().parse(data=ontology_text() + session.to_turtle(False) + extra, format='turtle')
    _, report, _ = validate(g, advanced=True, inplace=True, allow_infos=True, allow_warnings=True)
    return g, report


def focuses(report, shape):
    return {report.value(r, SH.focusNode) for r in report.subjects(SH.sourceShape, EFI[shape])}


def test_feed_through_and_unknown_connections_have_distinct_results():
    complete = system()
    g, report = run_input(dict(system=complete))
    assert not focuses(report, 'SystemReviewCoverageShape')
    assert not supply_questions(g, EFI.session_test)
    assert list(g.subjects(EFI.pathConnected, None))
    # 플러그 접속·기기 사용 사실 없이 배선만으로 연결된다. 통전 사실은 생기지 않는다.
    assert not list(g.subjects(RDF.type, EFI.EnergizedState))
    complete['connections'][1]['status'] = 'Unverifiable'
    g, report = run_input(dict(system=complete))
    assert focuses(report, 'SystemReviewCoverageShape')
    assert len(supply_questions(g, EFI.session_test)) == 1
    assert not list(g.subjects(EFI.pathConnected, None))
    assert not list(g.subjects(RDF.type, EFI.DeEnergizedState))


def test_each_identified_supply_path_requires_its_own_confirmation():
    model = system()
    model['components'].append(dict(id='backup', cls='PowerSource'))
    g, report = run_input(dict(system=model))
    assert focuses(report, 'SystemReviewCoverageShape'), '알려진 공급원을 검토 목록에서 빼도 완료가 되어서는 안 된다'
    assert supply_questions(g, EFI.session_test)[0]['load'] is None
    model['paths'].append(record('backup_path', source_component='backup', load_component='load'))
    g, report = run_input(dict(system=model))
    questions = supply_questions(g, EFI.session_test)
    assert len(questions) == 1 and questions[0]['record'].endswith('backup_path')
    assert focuses(report, 'SystemReviewCoverageShape')
    model['connections'].append(record('backup_link', from_component='backup', to_component='load', kind='Grounding'))
    g, _ = run_input(dict(system=model))
    assert len(supply_questions(g, EFI.session_test)) == 1


def test_system_input_rejects_dangling_references_and_claimed_derivations():
    model = system()
    model['connections'][0]['from_component'] = 'not_in_this_system'
    with pytest.raises(ValueError, match='unknown component'):
        InvestigationData.model_validate(dict(system=model))
    model = system()
    model['paths'][0]['path_connected'] = True
    with pytest.raises(ValueError):
        InvestigationData.model_validate(dict(system=model))


def test_found_off_and_manual_reset_do_not_prove_pre_fire_power_or_automatic_trip():
    data = dict(system=system(), device_states=[record('found', component='breaker', found_state='Off', observed_at='2026-09-03T12:00:00+09:00')],
                events=[record('reset', component='breaker', kind='ManualReset'),
                        record('opened', component='grid', kind='PowerDisconnected', supply_source='grid')])
    g, report = run_input(data)
    assert not focuses(report, 'DeviceStateRecordShape')
    assert len(list(g.subjects(RDF.type, EFI.DeviceStateRecord))) == 1
    assert len(list(g.subjects(RDF.type, EFI.ElectricalEventRecord))) == 2
    for cls in (EFI.EnergizedState, EFI.DeEnergizedState, EFI.BreakerTripRecord, EFI.ProtectiveDeviceFailedToOperate):
        assert not list(g.subjects(RDF.type, cls))


def at(hour):
    return f'2026-09-03T{hour:02}:00:00+09:00'


def timeline():
    model = system()
    model['components'].append(dict(id='backup', cls='PowerSource'))
    model['review_complete'] = False
    return dict(system=model, events=[
        record('cut', component='grid', kind='PowerDisconnected', supply_source='grid', earliest=at(8), latest=at(8)),
        record('arc', component='load', kind='ArcOccurrence', supply_source='grid', earliest=at(10), latest=at(10)),
    ], power_records=[record('ami', supply_source='grid', availability='Available', collected_kinds=['PowerDisconnected','PowerRestored'], start=at(7), end=at(12), history_complete=True)])


def test_timeline_requires_same_source_and_complete_restoration_history():
    data = timeline()
    g, report = run_input(data)
    assert focuses(report, 'SupplyTimelineConflictShape')
    data['events'][1]['supply_source'] = 'backup'
    _, report = run_input(data)
    assert not focuses(report, 'SupplyTimelineConflictShape')
    data['events'][1]['supply_source'] = 'grid'
    data['power_records'][0].update(availability='Unavailable', history_complete=False)
    _, report = run_input(data)
    assert not focuses(report, 'SupplyTimelineConflictShape')


def test_restoration_or_uncertain_time_prevents_false_timeline_conflict():
    data = timeline()
    data['events'].append(record('restore', component='grid', kind='PowerRestored', supply_source='grid', earliest=at(9), latest=at(9)))
    _, report = run_input(data)
    assert not focuses(report, 'SupplyTimelineConflictShape')
    data['events'][-1].update(status='Unverifiable', earliest=None, latest=None)
    _, report = run_input(data)
    assert not focuses(report, 'SupplyTimelineConflictShape')
    data['events'].pop()
    data['events'][0].update(earliest=at(8), latest=at(11))
    _, report = run_input(data)
    assert not focuses(report, 'SupplyTimelineConflictShape')


def test_local_fire_time_reaches_arc_classification_but_observation_time_does_not():
    data = dict(system=system(), events=[
        record('fire', component='load', kind='FireArrival', earliest=at(9), latest=at(9)),
        record('arc', component='load', kind='ArcOccurrence', earliest=at(10), latest=at(10), observed_at=at(14))])
    extra = 'efi:mark a efi:ArcMeltMark ; efi:formedBy <https://w3id.org/efi-onto#session_test/investigation/event/arc> .'
    g, _ = run_input(data, extra=extra)
    assert (EFI.mark, RDF.type, EFI.SecondaryArcMark) in g
    assert (EFI.mark, RDF.type, EFI.PrimaryArcMark) not in g
    data['events'][1].update(earliest=None, latest=None)
    g, _ = run_input(data, extra=extra)
    assert (EFI.mark, RDF.type, EFI.SecondaryArcMark) not in g
    data['events'][1].update(earliest=at(10), latest=at(10))
    data['events'][0]['component'] = 'outlet'
    g, _ = run_input(data, extra=extra)
    assert (EFI.mark, RDF.type, EFI.SecondaryArcMark) not in g


def fuel_data():
    return dict(first_fuels=[record('fuel', scenario='PoorContactScenario', fuel_class='InsulationMaterialFuel',
                                   presence_basis='발화부 접속 단자의 피복 잔존물 및 발화 전 배치 사진')],
                heat_transfers=[record('heat', scenario='PoorContactScenario', description='과열 단자에서 접촉 피복으로 전도',
                                      adequacy_basis='동일 피복·접촉 조건에서 재현 시험으로 열손실을 포함해 검토',
                                      duration_basis='영상의 가열 지속 구간과 재현 시험 노출 구간 대조',
                                      fuel_condition_basis='피복 두께·접촉 위치를 잔존물과 도면으로 확인')])


def contact():
    return [Hypothesis(scenario=Scenario.POOR_CONTACT, mechanism=Mechanism.POOR_CONTACT_HEATING)]


def test_candidate_keeps_missing_fuel_but_final_proposal_requires_evidence():
    _, report = run_input({}, hypotheses=contact())
    assert not focuses(report, 'ConclusionFirstFuelEvidenceShape')
    _, report = run_input({}, hypotheses=contact(), proposed=Scenario.POOR_CONTACT)
    assert focuses(report, 'ConclusionFirstFuelEvidenceShape')
    assert focuses(report, 'ConclusionHeatTransferEvidenceShape')
    # Python은 같은 제약을 재구현하지 않고 실제 결론 노드를 SHACL에 넘긴다.
    session = Session(case_id='no_fuel', hypotheses=contact(), proposed_conclusion=Scenario.POOR_CONTACT)
    assert any('최초 착화물의 발화 당시 존재' in m for m in session.validate())


def test_final_fuel_and_transfer_need_same_hypothesis_confirmed_records():
    data = fuel_data()
    _, report = run_input(data, hypotheses=contact(), proposed=Scenario.POOR_CONTACT)
    assert not focuses(report, 'ConclusionFirstFuelEvidenceShape')
    assert not focuses(report, 'ConclusionHeatTransferEvidenceShape')
    data['first_fuels'][0]['status'] = 'Unverifiable'
    _, report = run_input(data, hypotheses=contact(), proposed=Scenario.POOR_CONTACT)
    assert focuses(report, 'ConclusionFirstFuelEvidenceShape')
    data['first_fuels'][0]['status'] = 'Confirmed'
    data['heat_transfers'][0].pop('duration_basis')
    _, report = run_input(data, hypotheses=contact(), proposed=Scenario.POOR_CONTACT)
    assert focuses(report, 'ConclusionHeatTransferEvidenceShape')


def test_temperature_values_alone_do_not_complete_heat_transfer_evidence():
    data = fuel_data()
    data['heat_transfers'] = []
    hypotheses = contact()
    hypotheses[0].mechanism_max_temp_c = 1000
    hypotheses[0].fuel_ignition_temp_c = 300
    g, report = run_input(data, hypotheses=hypotheses, proposed=Scenario.POOR_CONTACT,
                         extra='efi:test_PoorContactScenario efi:heatTransferPath "접촉 가열" ; efi:sourceCompetentForFuel true .')
    assert list(g.objects(None, EFI.maxAttainableTemperature_C))
    assert list(g.objects(None, EFI.ignitionTemperature_C))
    assert focuses(report, 'ConclusionHeatTransferEvidenceShape')


def test_fuel_conflicts_and_bad_time_ranges_are_reported():
    data = fuel_data()
    absent = copy.deepcopy(data['first_fuels'][0])
    absent.update(id='absent_fuel', status='ConfirmedAbsent')
    data['first_fuels'].append(absent)
    _, report = run_input(data, hypotheses=contact(), proposed=Scenario.POOR_CONTACT)
    assert focuses(report, 'ConclusionFirstFuelEvidenceShape')
    data = timeline()
    data['events'][1].update(earliest=at(11), latest=at(10))
    _, report = run_input(data)
    assert list(report.subjects(SH.sourceConstraintComponent, SH.LessThanOrEqualsConstraintComponent))
    assert not focuses(report, 'SupplyTimelineConflictShape')
