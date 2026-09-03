"""NFPA 추가 본문에서 확인한 입력 의미·시간·재질 경계의 회귀 시험."""
import sys
from rdflib import Graph, RDF, SH, OWL
from pyshacl import validate
from test_ontology import ROOT, TTL, EFI, PROV, run

sys.path.insert(0, str(ROOT / "scripts"))


def test_oxide_detection_needs_confirmed_growth_to_support_poor_contact():
    inputs = [("Confirmed", ""), ("Confirmed", "false"), ("Confirmed", "true"),
              ("Unverifiable", "true"), ("ConfirmedAbsent", "true")]
    data = "efi:inv a efi:InvestigatorAgent .\n"
    for i, (status, growth) in enumerate(inputs):
        qualifier = f"; efi:oxideMassGrowthConfirmed {growth}" if growth else ""
        data += f"""
        efi:s{i} a efi:InvestigationSession ; efi:hasFact efi:cp{i} .
        efi:cp{i} a efi:ConnectionPoint ; efi:cuprousOxidePresent true
            {qualifier} ; efi:confirmationStatus efi:{status} ; prov:wasAttributedTo efi:inv .
        efi:h{i} a efi:PoorContactScenario ; efi:inSession efi:s{i} .
        """
    gr = run(data)
    for i in range(len(inputs)):
        types = {t for f in gr.objects(EFI[f"s{i}"], EFI.hasFact) for t in gr.objects(f, RDF.type)}
        assert (EFI.CuprousOxideGrowth in types) == (i == 2)
        assert (EFI.CuprousOxideDeposit in types) == (i < 3)
        assert (int(gr.value(EFI[f"h{i}"], EFI.supportScore)) > 50) == (i == 2)


def test_corrosion_observation_does_not_establish_pre_fire_condition():
    inputs = [("Confirmed", ""), ("Confirmed", "false"), ("Confirmed", "true"),
              ("Unverifiable", "true")]
    data = "efi:inv a efi:InvestigatorAgent .\n"
    for i, (status, prior) in enumerate(inputs):
        qualifier = f"; efi:corrosionPredatesFire {prior}" if prior else ""
        data += f"""
        efi:s{i} a efi:InvestigationSession ; efi:hasFact efi:cp{i} .
        efi:cp{i} a efi:ConnectionPoint ; efi:corrosionPresent true
            {qualifier} ; efi:confirmationStatus efi:{status} ; prov:wasAttributedTo efi:inv .
        efi:h{i} a efi:PoorContactScenario ; efi:inSession efi:s{i} .
        """
    gr = run(data)
    for i in range(len(inputs)):
        facts = list(gr.objects(EFI[f"s{i}"], EFI.hasFact))
        types = {t for f in facts for t in gr.objects(f, RDF.type)}
        assert (EFI.CorrodedConnection in types) == (i == 2)
        assert (EFI.ContactCorrosion in types) == (i < 3)
        assert (int(gr.value(EFI[f"h{i}"], EFI.supportScore)) > 50) == (i == 2)
        assert not any((f, EFI.confirmationStatus, EFI.ConfirmedAbsent) in gr for f in facts)
        assert all((f, PROV.wasAttributedTo, EFI.inv) in gr for f in facts)


def test_material_assessment_is_required_without_banning_supported_arc_evidence():
    data = ""
    for i, (material, basis) in enumerate([
        ("AlloyConductor", ""), ("PureAluminumConductor", ""),
        ("PureAluminumConductor", 'efi:materialSpecificArcAssessment "  " ;'),
        ("PureAluminumConductor", 'efi:materialSpecificArcAssessment "재질 분석 및 대응 도체의 아크 손상 대조 기록" ;'),
        ("AlloyConductor", 'efi:materialSpecificArcAssessment "합금 성분 분석과 독립 아크 발생 기록의 대조" ;'),
    ]):
        data += f"""
        efi:c{i} a efi:Conclusion ; efi:concludes efi:h{i} .
        efi:h{i} a efi:PoorContactScenario ; efi:supportedBy efi:f{i} .
        efi:f{i} a efi:ArcMeltMark .
        efi:wire{i} a efi:{material} ; {basis} efi:exhibits efi:f{i} .
        """
    gr = Graph().parse(data=TTL.read_text(encoding="utf-8") + data, format="turtle")
    assert (EFI.PureAluminumConductor, OWL.disjointWith, EFI.AlloyConductor) in gr
    _, report, _ = validate(gr, advanced=True, allow_infos=True, allow_warnings=True)
    affected = {report.value(r, SH.focusNode) for r in report.subjects(SH.sourceShape, EFI.AlloyConductorArcMarkShape)}
    assert affected == {EFI.c0, EFI.c1, EFI.c2}


def test_tia_visible_arc_absence_does_not_infer_no_arcing_or_external_fire():
    gr = run("""
    efi:inv a efi:InvestigatorAgent .
    efi:p a efi:ArcMapPoint ; efi:arcSiteFound false ; prov:wasAttributedTo efi:inv .
    efi:hidden a efi:ArcMapPoint ; efi:arcSiteFound false ; efi:obscuredByMelting true .
    efi:s a efi:InvestigationSession ; efi:hasFact efi:p .
    efi:h a efi:ExternalFlameScenario ; efi:inSession efi:s .
    """)
    assert (EFI.p, EFI.confirmationStatus, EFI.ConfirmedAbsent) in gr
    assert (EFI.hidden, EFI.confirmationStatus, EFI.Unverifiable) in gr
    assert (EFI.hidden, EFI.confirmationStatus, EFI.ConfirmedAbsent) not in gr
    assert not list(gr.subjects(RDF.type, EFI.NoArcOrSpatter))
    assert int(gr.value(EFI.h, EFI.supportScore)) == 50


def test_slot_reader_preserves_detection_growth_and_corrosion_distinctions():
    from slots import map_slot
    slot = "slot_additional_visual_evidence"
    assert ("CuprousOxideDeposit", "Confirmed") in map_slot(slot, "아산화동 피막 검출")[0]
    assert ("CuprousOxideGrowth", "Confirmed") not in map_slot(slot, "아산화동 피막 검출")[0]
    assert ("CuprousOxideGrowth", "Confirmed") in map_slot(slot, "접속부 아산화동 증식 확인")[0]
    assert ("CuprousOxideGrowth", "Unverifiable") in map_slot(slot, "아산화동 증식 확인 불가")[0]
    observed = map_slot(slot, "진화 후 접속부 부식 관찰")[0]
    assert ("ContactCorrosion", "Confirmed") in observed
    assert not any(c == "CorrodedConnection" for c, _ in observed)
    assert ("DeEnergizedState", "Confirmed") in map_slot("slot_energized_status", "발화 전부터 전원 차단 상태")[0]
    assert not any(c == "DeEnergizedState" for c, _ in map_slot("slot_energized_status", "진화 후 조사를 위해 전원 차단 상태")[0])


def test_evaluation_helpers_agree_on_both_held_outcomes(monkeypatch):
    import eval as ev
    import reader_compare
    import refute_audit
    from types import SimpleNamespace
    sessions = [{"case_id": outcome, "actual_scenario": "PoorContactScenario", "facts": []}
                for outcome in ("PoorContactScenario", "TrackingScenario", "Undetermined", "UnidentifiedShortCircuit")]
    monkeypatch.setattr(ev, "predict", lambda s, _: (s["case_id"], None))
    result = reader_compare.run(sessions, SimpleNamespace(rules=[]))
    assert (result["ok"], result["wrong"], result["und"]) == (1, 1, 2)
    assert refute_audit._accuracy(None, sessions) == (0.25, 0.5, 0.25)
