"""출처가 있는 조사 입력을 RDF로 직렬화한다. 판정 제약·도출은 TBox에 둔다."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal
from urllib.parse import quote

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from rdflib import Graph, Literal as RdfLiteral, Namespace, RDF, URIRef

E = Namespace('https://w3id.org/efi-onto#')
PROV = Namespace('http://www.w3.org/ns/prov#')


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: str = Field(min_length=1)
    status: Literal['Confirmed', 'ConfirmedAbsent', 'Unverifiable', 'Missing']
    attributed_to: str = Field(min_length=1)
    source: str = Field(min_length=1)
    observed_at: AwareDatetime | None = None


class Component(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1)
    cls: Literal['PowerSource', 'ServiceEquipment', 'ProtectiveDevice', 'Circuit',
                 'BranchCircuit', 'ConnectionPoint', 'TerminalBlock', 'PlugReceptacle',
                 'Conductor', 'Conduit', 'GroundedSurface', 'ElectricalLoad',
                 'ElectricalSwitch', 'Enclosure', 'GroundFaultProtectiveDevice',
                 'ArcFaultProtectiveDevice', 'ElectricMeter', 'Insulation', 'TerminalFastener']
    container: str | None = None
    circuit: str | None = None
    role: Literal['Ungrounded', 'Neutral', 'Grounding', 'Unknown'] | None = None


class Connection(Record):
    from_component: str
    to_component: str
    kind: Literal['Supply', 'Grounding', 'SwitchControl', 'Protection'] = 'Supply'


class PathAssessment(Record):
    source_component: str
    load_component: str


class DeviceState(Record):
    component: str
    found_state: Literal['On', 'Off', 'Tripped', 'FuseOpen', 'Unknown']


class ComponentExamination(Record):
    component: str
    damage_state: Literal['Damaged', 'NoDamageObserved', 'NotAccessible', 'Unknown']
    arc_site_status: Literal['Confirmed', 'ConfirmedAbsent', 'Unverifiable', 'Missing'] | None = None
    insulation_material: Literal['Rubber', 'PVC', 'Polyethylene', 'Other', 'Unknown'] | None = None
    insulation_material_basis: str | None = None
    insulation_filler: Literal['CalciumCarbonate', 'Other', 'None', 'Unknown'] | None = None
    insulation_filler_basis: str | None = None


class InsulationExposure(Record):
    component: str
    kind: Literal['Heating', 'SurfaceMoisture']
    earliest: AwareDatetime | None = None
    latest: AwareDatetime | None = None
    exposure_basis: str | None = None
    temperature_min_C: Decimal | None = Field(default=None, allow_inf_nan=False)
    temperature_max_C: Decimal | None = Field(default=None, allow_inf_nan=False)
    temperature_basis_kind: Literal['Measured', 'Reconstructed', 'Unknown'] | None = None
    moisture_presence: Literal['Present', 'Absent', 'Unknown'] | None = None
    moisture_origin: Literal['AmbientAir', 'DirectWater', 'Other', 'Unknown'] | None = None


class InsulationHistoryReview(Record):
    examination: str
    heating: str
    moisture: str
    ignition_event: str | None = None
    applicability_basis: str | None = None
    assessment_complete: bool = False
    claim_pre_ignition_sequence: bool = False


class ElectricalEvent(Record):
    component: str
    kind: Literal['PowerDisconnected', 'PowerRestored', 'AutomaticTrip', 'ManualSwitchOff',
                  'ManualSwitchOn', 'ManualReset', 'Replacement', 'Removal', 'Modification',
                  'Disassembly', 'Bending', 'TensionHandling', 'Sampling', 'ArcOccurrence', 'FireArrival', 'Ignition',
                  'ContactArcOccurrence', 'InsulationBreakdown']
    supply_source: str | None = None
    replacement_component: str | None = None
    replacement_compatible: bool | None = None
    earliest: AwareDatetime | None = None
    latest: AwareDatetime | None = None


class PowerCoverage(Record):
    supply_source: str
    availability: Literal['Available', 'Unavailable', 'Unknown']
    collected_kinds: list[Literal['PowerDisconnected', 'PowerRestored', 'Usage']] = Field(default_factory=list)
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None
    history_complete: bool = False


class FirstFuelEvidence(Record):
    scenario: str
    fuel_class: Literal['InsulationMaterialFuel', 'EnclosureMaterialFuel', 'AccumulatedDustFuel',
                        'CelluloseFuel', 'ThermalInsulationFuel', 'FlammableVaporFuel']
    presence_basis: str | None = None


class HeatTransferEvidence(Record):
    scenario: str
    description: str | None = None
    adequacy_basis: str | None = None
    duration_basis: str | None = None
    fuel_condition_basis: str | None = None


class DamageComparison(Record):
    component: str
    comparator: str | None = None
    kind: Literal['MetalExposure', 'PanelInsideOutside']
    location: str | None = None
    comparator_location: str | None = None
    side: Literal['Inside', 'Outside', 'Unknown'] | None = None
    comparator_side: Literal['Inside', 'Outside', 'Unknown'] | None = None
    finding: str | None = None
    comparator_finding: str | None = None
    metal: str | None = None
    comparator_metal: str | None = None
    exposure_status: Literal['Confirmed', 'ConfirmedAbsent', 'Unverifiable', 'Missing'] = 'Missing'
    exposure_basis: str | None = None
    assessment_complete: bool = False


class HeatingObservation(Record):
    component: str
    characteristic: int = Field(ge=1, le=13)
    detail: str | None = None
    comparison: str | None = None


class InvestigationProblem(Record):
    statement: str | None = None


class InvestigationPlan(Record):
    problem: str
    scope: str = Field(min_length=1)
    method: str = Field(min_length=1)
    required_expertise: str = Field(min_length=1)
    complete: bool = False


class VerificationRecord(Record):
    plan: str
    result: str | None = None
    evidence_records: list[str] = Field(default_factory=list)


class ReviewScope(Record):
    plan: str
    competence_basis: str | None = None
    documentation_access: Literal['Confirmed', 'ConfirmedAbsent', 'Unverifiable', 'Missing'] = 'Missing'
    access_basis: str | None = None
    critique: str | None = None


class TechnicalReviewRecord(Record):
    reviewer: str = Field(min_length=1)
    requested_plans: list[str] = Field(default_factory=list)
    scope_kind: Literal['Selected', 'All'] = 'Selected'
    scopes: list[ReviewScope] = Field(default_factory=list)
    documentation_access: bool | None = None
    reviewer_relationship: str | None = None
    complete: bool = False


class MetalDeposition(Record):
    component: str
    source_event: str | None = None
    source_link_basis: str | None = None
    deposit_basis: str | None = None
    earliest: AwareDatetime | None = None
    latest: AwareDatetime | None = None
    breakdown_event: str | None = None
    ignition_event: str | None = None
    assessment_complete: bool = False


TerminationMethod = Literal['ScrewTerminal', 'PushInSpring', 'PushInScrewClamp', 'WireWrapPin',
                            'Soldered', 'Crimped', 'TwistOnConnector', 'Twisted', 'Other', 'Unknown']
ConductorMetal = Literal['Copper', 'PureAluminum', 'AluminumAlloy', 'CopperCladAluminum', 'Other', 'Unknown']
FastenerMetal = Literal['Steel', 'Brass', 'Other', 'Unknown']
TorqueKind = Literal['AppliedTightening', 'ResidualTightening', 'BreakawayLoosening', 'Unknown']
ConductorForm = Literal['Solid', 'Stranded', 'Other', 'Unknown']
ContactMetal = Literal['Copper', 'PureAluminum', 'AluminumAlloy', 'CopperAlloy', 'Brass', 'Steel', 'Other', 'Unknown']
ContactCoating = Literal['Zinc', 'Nickel', 'Tin', 'Silver', 'Indium', 'Copper', 'Other', 'None', 'Unknown']
OxideBehavior = Literal['Semiconductive', 'NegligibleConductivity', 'Other', 'Unknown']
InstallationUse = Literal['BranchCircuit', 'ServiceEntrance', 'ServiceDrop', 'Other', 'Unknown']
DeviceMarking = Literal['AL-CU', 'CO-ALR', 'CopperOnly', 'Other', 'None', 'Unknown']


class TerminationRecord(Record):
    component: str
    device: str
    conductor: str
    connection: str
    method: TerminationMethod = 'Unknown'
    conductor_material: ConductorMetal = 'Unknown'
    conductor_material_basis: str | None = None
    conductor_alloy_grade: str | None = None
    conductor_form: ConductorForm = 'Unknown'
    conductor_size: str | None = None
    product_id: str | None = None
    terminal_marking: str | None = None
    identification_basis: str | None = None
    assessment_complete: bool = False


class FastenerRecord(Record):
    component: str
    termination: str
    material: FastenerMetal = 'Unknown'
    magnetic_response: Literal['Attracted', 'NotAttracted', 'Unknown'] = 'Unknown'
    identification_method: Literal['Magnet', 'ProductDocumentation', 'MaterialAnalysis', 'Other', 'Unknown'] = 'Unknown'
    identification_basis: str | None = None


class MatingContactRecord(Record):
    component: str
    termination: str
    base_material: ContactMetal = 'Unknown'
    surface_coating: ContactCoating = 'Unknown'
    material_basis: str | None = None
    coating_basis: str | None = None
    assessment_complete: bool = False


class MetalInterfaceReference(Record):
    basis_kind: Literal['ScientificSource', 'HistoricalStudy', 'Manufacturer', 'Standard', 'Other']
    conductor_material: ConductorMetal
    conductor_alloy_grade: str | None = None
    conductor_size: str | None = None
    conductor_form: ConductorForm | None = None
    termination_method: TerminationMethod | None = None
    mating_material: ContactMetal | None = None
    mating_coating: ContactCoating | None = None
    installation_region: str | None = None
    installation_year_from: int | None = None
    installation_year_to: int | None = None
    installation_use: InstallationUse | None = None
    device_marking: DeviceMarking | None = None
    conductor_oxide_behavior: OxideBehavior | None = None
    mating_oxide_behavior: OxideBehavior | None = None
    glow_path_explanation: str | None = None
    applicability_scope: str = Field(min_length=1)


class MetalInterfaceComparison(Record):
    termination: str
    mating_contact: str
    reference: str
    installation_region: str | None = None
    installation_year: int | None = None
    installation_use: InstallationUse = 'Unknown'
    installation_use_basis: str | None = None
    device_marking: DeviceMarking = 'Unknown'
    device_marking_basis: str | None = None
    connector_approval_status: Literal['Confirmed', 'ConfirmedAbsent', 'Unverifiable', 'Missing'] = 'Missing'
    approval_basis: str | None = None
    applicability_basis: str | None = None
    assessment_complete: bool = False


class TorqueMeasurement(Record):
    termination: str
    fastener: str | None = None
    value_Nm: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    quantity_kind: TorqueKind = 'Unknown'
    phase: Literal['BeforeFire', 'AsFoundAfterFire', 'AfterHandling', 'Unknown'] = 'Unknown'
    measured_at: AwareDatetime | None = None
    measurement_method: str | None = None
    timing_basis: str | None = None
    ignition_event: str | None = None


class TorqueReference(Record):
    basis_kind: Literal['Manufacturer', 'Study', 'Other']
    product_id: str | None = None
    termination_method: TerminationMethod = 'Unknown'
    conductor_material: ConductorMetal = 'Unknown'
    conductor_size: str | None = None
    fastener_material: FastenerMetal | None = None
    quantity_kind: TorqueKind = 'Unknown'
    minimum_Nm: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    maximum_Nm: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    applicability_scope: str | None = None


class TorqueComparison(Record):
    measurement: str
    reference: str
    applicability_basis: str | None = None
    assessment_complete: bool = False
    claim_pre_fire_applied_torque: bool = False


class SystemModel(Record):
    components: list[Component]
    connections: list[Connection] = Field(default_factory=list)
    paths: list[PathAssessment] = Field(default_factory=list)
    review_complete: bool = False
    source_inventory_complete: bool = False

    @model_validator(mode='after')
    def references(self):
        components = {c.id: c for c in self.components}
        if len(components) != len(self.components):
            raise ValueError('duplicate component ID')
        records = [*self.connections, *self.paths]
        if len({r.id for r in records}) != len(records):
            raise ValueError('duplicate system record ID')
        refs = [r for c in self.components for r in (c.container, c.circuit) if r]
        refs += [r for c in self.connections for r in (c.from_component, c.to_component)]
        refs += [r for p in self.paths for r in (p.source_component, p.load_component)]
        if any(r not in components for r in refs):
            raise ValueError('reference to unknown component')
        if any(components[p.source_component].cls != 'PowerSource' for p in self.paths):
            raise ValueError('path source must be PowerSource')
        return self


class InvestigationData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    system: SystemModel | None = None
    device_states: list[DeviceState] = Field(default_factory=list)
    events: list[ElectricalEvent] = Field(default_factory=list)
    power_records: list[PowerCoverage] = Field(default_factory=list)
    first_fuels: list[FirstFuelEvidence] = Field(default_factory=list)
    heat_transfers: list[HeatTransferEvidence] = Field(default_factory=list)
    examinations: list[ComponentExamination] = Field(default_factory=list)
    insulation_exposures: list[InsulationExposure] = Field(default_factory=list)
    insulation_history_reviews: list[InsulationHistoryReview] = Field(default_factory=list)
    comparisons: list[DamageComparison] = Field(default_factory=list)
    heating_observations: list[HeatingObservation] = Field(default_factory=list)
    problems: list[InvestigationProblem] = Field(default_factory=list)
    plans: list[InvestigationPlan] = Field(default_factory=list)
    verifications: list[VerificationRecord] = Field(default_factory=list)
    technical_reviews: list[TechnicalReviewRecord] = Field(default_factory=list)
    depositions: list[MetalDeposition] = Field(default_factory=list)
    terminations: list[TerminationRecord] = Field(default_factory=list)
    fasteners: list[FastenerRecord] = Field(default_factory=list)
    mating_contacts: list[MatingContactRecord] = Field(default_factory=list)
    metal_interface_references: list[MetalInterfaceReference] = Field(default_factory=list)
    metal_interface_comparisons: list[MetalInterfaceComparison] = Field(default_factory=list)
    torque_measurements: list[TorqueMeasurement] = Field(default_factory=list)
    torque_references: list[TorqueReference] = Field(default_factory=list)
    torque_comparisons: list[TorqueComparison] = Field(default_factory=list)

    @model_validator(mode='after')
    def references(self):
        components = {c.id: c for c in self.system.components} if self.system else {}
        records = [*self.device_states, *self.events, *self.power_records, *self.first_fuels, *self.heat_transfers,
                   *self.examinations, *self.insulation_exposures, *self.insulation_history_reviews,
                   *self.comparisons, *self.heating_observations, *self.problems, *self.plans,
                   *self.verifications, *self.technical_reviews, *self.depositions,
                   *self.terminations, *self.fasteners, *self.mating_contacts, *self.metal_interface_references,
                   *self.metal_interface_comparisons, *self.torque_measurements, *self.torque_references, *self.torque_comparisons,
                   *(scope for review in self.technical_reviews for scope in review.scopes)]
        if self.system:
            records += [*self.system.connections, *self.system.paths]
        if len({r.id for r in records}) != len(records):
            raise ValueError('duplicate investigation record ID')
        for r in [*self.device_states, *self.events, *self.examinations, *self.comparisons,
                  *self.heating_observations, *self.depositions, *self.terminations, *self.fasteners,
                  *self.mating_contacts, *self.insulation_exposures]:
            if r.component not in components:
                raise ValueError('record references unknown component')
        for r in self.device_states:
            if components[r.component].cls not in ('ProtectiveDevice', 'GroundFaultProtectiveDevice', 'ArcFaultProtectiveDevice'):
                raise ValueError('device state must refer to protective device')
        for r in self.events:
            if r.supply_source and (r.supply_source not in components or components[r.supply_source].cls != 'PowerSource'):
                raise ValueError('event supply must refer to PowerSource')
            if r.replacement_component and r.replacement_component not in components:
                raise ValueError('replacement references unknown component')
        for r in self.power_records:
            if r.supply_source not in components or components[r.supply_source].cls != 'PowerSource':
                raise ValueError('power record must refer to PowerSource')
        def known(refs, items, kind):
            if any(ref not in {x.id for x in items} for ref in refs if ref is not None):
                raise ValueError('reference to unknown ' + kind)

        for r in self.comparisons:
            known([r.comparator], self.system.components, 'comparator')
        for r in self.heating_observations:
            known([r.comparison], self.comparisons, 'comparison')
        for r in self.plans:
            known([r.problem], self.problems, 'problem')
        for r in self.verifications:
            known([r.plan], self.plans, 'plan')
            evidence = [*self.device_states, *self.events, *self.power_records, *self.first_fuels,
                        *self.heat_transfers, *self.examinations, *self.insulation_exposures, *self.comparisons,
                        *self.heating_observations, *self.depositions, *self.terminations,
                        *self.fasteners, *self.mating_contacts, *self.torque_measurements]
            if self.system:
                evidence += [*self.system.connections, *self.system.paths]
            known(r.evidence_records, evidence, 'evidence record')
            if r.id in r.evidence_records:
                raise ValueError('verification cannot cite itself')
        for r in self.technical_reviews:
            known(r.requested_plans + [s.plan for s in r.scopes], self.plans, 'review plan')
            if len(set(r.requested_plans)) != len(r.requested_plans):
                raise ValueError('duplicate requested review plan')
            if len({s.plan for s in r.scopes}) != len(r.scopes):
                raise ValueError('duplicate scope in review')
        for r in self.depositions:
            known([r.source_event, r.breakdown_event, r.ignition_event], self.events, 'deposition event')
            if components[r.component].cls != 'Insulation':
                raise ValueError('metal deposition target must be Insulation')
        for r in self.terminations:
            known([r.device, r.conductor], self.system.components, 'termination component')
            known([r.connection], self.system.connections, 'termination connection')
            if components[r.component].cls not in ('ConnectionPoint', 'TerminalBlock'):
                raise ValueError('termination target must be a terminal or connection point')
            if components[r.conductor].cls != 'Conductor':
                raise ValueError('termination conductor must be Conductor')
        for r in self.fasteners:
            known([r.termination], self.terminations, 'fastener termination')
            if components[r.component].cls != 'TerminalFastener':
                raise ValueError('fastener target must be TerminalFastener')
        for r in self.mating_contacts:
            known([r.termination], self.terminations, 'mating contact termination')
        for r in self.metal_interface_comparisons:
            known([r.termination], self.terminations, 'metal interface termination')
            known([r.mating_contact], self.mating_contacts, 'mating contact')
            known([r.reference], self.metal_interface_references, 'metal interface reference')
        for r in self.torque_measurements:
            known([r.termination], self.terminations, 'torque termination')
            known([r.fastener], self.fasteners, 'torque fastener')
            known([r.ignition_event], self.events, 'torque ignition event')
        for r in self.torque_comparisons:
            known([r.measurement], self.torque_measurements, 'torque measurement')
            known([r.reference], self.torque_references, 'torque reference')
        for r in self.insulation_exposures:
            if components[r.component].cls != 'Insulation':
                raise ValueError('insulation exposure target must be Insulation')
        for r in self.insulation_history_reviews:
            known([r.examination], self.examinations, 'insulation examination')
            known([r.heating, r.moisture], self.insulation_exposures, 'insulation exposure')
            known([r.ignition_event], self.events, 'insulation ignition event')
        return self

    def add_to_graph(self, graph: Graph, session: URIRef, hypotheses=None):
        """별도 기록은 hasFact에 넣지 않는다. 출처의 확인만으로 가점을 만들지 않는다."""
        def node(kind, value):
            return URIRef(f'{session}/investigation/{kind}/{quote(value, safe="")}')

        def record(item, cls, kind='record'):
            n = node(kind, item.id)
            graph.add((n, RDF.type, E[cls]))
            graph.add((n, E.recordSession, session))
            graph.add((session, E.hasInvestigationRecord, n))
            graph.add((n, E.confirmationStatus, E[item.status]))
            graph.add((n, PROV.wasAttributedTo, node('agent', item.attributed_to)))
            graph.add((n, E.recordSource, RdfLiteral(item.source)))
            if item.observed_at is not None:
                graph.add((n, E.recordObservedAt, RdfLiteral(item.observed_at)))
            return n

        def values(n, pairs):
            for prop, value in pairs:
                if value is not None:
                    graph.add((n, E[prop], RdfLiteral(value)))

        if self.system is not None:
            model = self.system
            sys = record(model, 'ElectricalSystemModel', 'system')
            graph.add((session, E.hasSystemModel, sys))
            graph.add((sys, E.systemReviewComplete, RdfLiteral(model.review_complete)))
            graph.add((sys, E.sourceInventoryComplete, RdfLiteral(model.source_inventory_complete)))
            comp = lambda name: node('component', model.id + '/' + name)
            for c in model.components:
                n = comp(c.id)
                graph.add((n, RDF.type, E[c.cls]))
                graph.add((sys, E.systemComponent, n))
                graph.add((n, E.componentModel, sys))
                if c.container:
                    graph.add((n, E.componentContainer, comp(c.container)))
                if c.circuit:
                    graph.add((n, E.componentCircuit, comp(c.circuit)))
                if c.role:
                    graph.add((n, E.componentRole, RdfLiteral(c.role)))
            for c in model.connections:
                n = record(c, 'ConnectionRecord')
                graph.add((n, E.recordSystem, sys))
                graph.add((n, E.connectionFrom, comp(c.from_component)))
                graph.add((n, E.connectionTo, comp(c.to_component)))
                graph.add((n, E.connectionKind, RdfLiteral(c.kind)))
            for p in model.paths:
                n = record(p, 'SupplyPathAssessment')
                graph.add((n, E.recordSystem, sys))
                graph.add((n, E.assessedSource, comp(p.source_component)))
                graph.add((n, E.assessedLoad, comp(p.load_component)))
            for state in self.device_states:
                n = record(state, 'DeviceStateRecord')
                graph.add((n, E.recordComponent, comp(state.component)))
                graph.add((n, E.deviceFoundState, RdfLiteral(state.found_state)))
            for exam in self.examinations:
                n = record(exam, 'ComponentExamination')
                graph.add((n, E.recordComponent, comp(exam.component)))
                graph.add((n, E.componentDamageState, RdfLiteral(exam.damage_state)))
                if exam.arc_site_status is not None:
                    graph.add((n, E.observedArcSiteStatus, E[exam.arc_site_status]))
                if exam.insulation_material is not None:
                    graph.add((n, E.observedInsulationMaterial, RdfLiteral(exam.insulation_material)))
                values(n, [('insulationMaterialBasis', exam.insulation_material_basis),
                           ('observedInsulationFiller', exam.insulation_filler),
                           ('insulationFillerBasis', exam.insulation_filler_basis)])
            for event in self.events:
                n = record(event, 'ElectricalEventRecord')
                graph.add((n, E.recordComponent, comp(event.component)))
                graph.add((n, E.electricalEventKind, RdfLiteral(event.kind)))
                if event.supply_source:
                    graph.add((n, E.eventSupplySource, comp(event.supply_source)))
                if event.replacement_component:
                    graph.add((n, E.replacementComponent, comp(event.replacement_component)))
                if event.replacement_compatible is not None:
                    graph.add((n, E.replacementCompatibility, RdfLiteral(event.replacement_compatible)))
                for prop, value in ((E.eventEarliest, event.earliest), (E.eventLatest, event.latest)):
                    if value is not None:
                        graph.add((n, prop, RdfLiteral(value)))
                if event.kind in ('ArcOccurrence', 'ContactArcOccurrence', 'FireArrival'):
                    event_node = node('event', event.id)
                    graph.add((n, E.describesElectricalEvent, event_node))
                    graph.add((event_node, RDF.type, E.FireExposureEvent if event.kind == 'FireArrival' else E.ArcEvent))
            for power in self.power_records:
                n = record(power, 'PowerRecordCoverage')
                graph.add((n, E.eventSupplySource, comp(power.supply_source)))
                graph.add((n, E.recordAvailability, RdfLiteral(power.availability)))
                graph.add((n, E.powerHistoryComplete, RdfLiteral(power.history_complete)))
                for kind in power.collected_kinds:
                    graph.add((n, E.collectedEventKind, RdfLiteral(kind)))
                for prop, value in ((E.coverageStart, power.start), (E.coverageEnd, power.end)):
                    if value is not None:
                        graph.add((n, prop, RdfLiteral(value)))
            for c in self.comparisons:
                n = record(c, 'DamageComparison')
                graph.add((n, E.recordComponent, comp(c.component)))
                if c.comparator:
                    graph.add((n, E.comparisonComponent, comp(c.comparator)))
                graph.add((n, E.equivalentFireExposureStatus, E[c.exposure_status]))
                values(n, [('comparisonKind', c.kind), ('comparisonLocation', c.location),
                           ('comparatorLocation', c.comparator_location), ('comparisonFinding', c.finding),
                           ('comparisonSide', c.side), ('comparatorSide', c.comparator_side),
                           ('comparatorFinding', c.comparator_finding), ('comparisonMetal', c.metal),
                           ('comparatorMetal', c.comparator_metal), ('exposureComparisonBasis', c.exposure_basis),
                           ('comparisonComplete', c.assessment_complete)])
            for observation in self.heating_observations:
                n = record(observation, 'HeatingCharacteristicObservation')
                graph.add((n, E.recordComponent, comp(observation.component)))
                graph.add((n, E.observedHeatingCharacteristic, E[f'HeatingCharacteristic{observation.characteristic:02}']))
                values(n, [('characteristicDetail', observation.detail)])
                if observation.comparison:
                    graph.add((n, E.characteristicComparison, node('record', observation.comparison)))
            for d in self.depositions:
                n = record(d, 'MetalDepositionRecord')
                graph.add((n, RDF.type, E.ElectricalEventRecord))
                graph.add((n, E.recordComponent, comp(d.component)))
                values(n, [('electricalEventKind', 'MetalDeposition'), ('depositBasis', d.deposit_basis),
                           ('sourceArcLinkBasis', d.source_link_basis), ('eventEarliest', d.earliest),
                           ('eventLatest', d.latest), ('depositionAssessmentComplete', d.assessment_complete)])
                for prop, ref in [('sourceContactArcRecord', d.source_event),
                                  ('subsequentBreakdownRecord', d.breakdown_event), ('relatedIgnitionRecord', d.ignition_event)]:
                    if ref is not None:
                        graph.add((n, E[prop], node('record', ref)))
            for term in self.terminations:
                n = record(term, 'TerminationRecord')
                for prop, ref in [('recordComponent', term.component), ('terminationDevice', term.device),
                                  ('terminationConductor', term.conductor)]:
                    graph.add((n, E[prop], comp(ref)))
                graph.add((n, E.terminationConnection, node('record', term.connection)))
                values(n, [('terminationMethod', term.method), ('terminationConductorMaterial', term.conductor_material),
                           ('terminationConductorMaterialBasis', term.conductor_material_basis),
                           ('terminationConductorGrade', term.conductor_alloy_grade),
                           ('terminationConductorForm', term.conductor_form),
                           ('terminationConductorSize', term.conductor_size), ('terminationProduct', term.product_id),
                           ('terminalMarking', term.terminal_marking), ('terminationIdentificationBasis', term.identification_basis),
                           ('terminationAssessmentComplete', term.assessment_complete)])
            for fastener in self.fasteners:
                n = record(fastener, 'FastenerRecord')
                graph.add((n, E.recordComponent, comp(fastener.component)))
                graph.add((n, E.fastenerTermination, node('record', fastener.termination)))
                values(n, [('fastenerMaterial', fastener.material), ('magneticResponse', fastener.magnetic_response),
                           ('fastenerIdentificationMethod', fastener.identification_method),
                           ('fastenerIdentificationBasis', fastener.identification_basis)])
            for contact in self.mating_contacts:
                n = record(contact, 'MatingContactRecord')
                graph.add((n, E.recordComponent, comp(contact.component)))
                graph.add((n, E.matingContactTermination, node('record', contact.termination)))
                values(n, [('matingBaseMaterial', contact.base_material), ('matingSurfaceCoating', contact.surface_coating),
                           ('matingMaterialBasis', contact.material_basis), ('matingCoatingBasis', contact.coating_basis),
                           ('matingContactAssessmentComplete', contact.assessment_complete)])
            for exposure in self.insulation_exposures:
                n = record(exposure, 'InsulationExposureRecord')
                graph.add((n, E.recordComponent, comp(exposure.component)))
                values(n, [('insulationExposureKind', exposure.kind), ('exposureEarliest', exposure.earliest),
                           ('exposureLatest', exposure.latest), ('insulationExposureBasis', exposure.exposure_basis),
                           ('exposureTemperatureMin_C', exposure.temperature_min_C),
                           ('exposureTemperatureMax_C', exposure.temperature_max_C),
                           ('temperatureBasisKind', exposure.temperature_basis_kind),
                           ('surfaceMoisturePresence', exposure.moisture_presence), ('surfaceMoistureOrigin', exposure.moisture_origin)])
        for review in self.insulation_history_reviews:
            n = record(review, 'InsulationHistoryReview')
            for prop, ref in [('historyExamination', review.examination), ('historyHeating', review.heating),
                              ('historyMoisture', review.moisture), ('historyIgnitionRecord', review.ignition_event)]:
                if ref is not None:
                    graph.add((n, E[prop], node('record', ref)))
            values(n, [('insulationApplicabilityBasis', review.applicability_basis),
                       ('insulationHistoryComplete', review.assessment_complete),
                       ('claimsPreIgnitionHeatingMoisture', review.claim_pre_ignition_sequence)])
        for measurement in self.torque_measurements:
            n = record(measurement, 'TorqueMeasurement')
            graph.add((n, E.measuredTermination, node('record', measurement.termination)))
            for prop, ref in [('measuredFastener', measurement.fastener), ('torqueIgnitionRecord', measurement.ignition_event)]:
                if ref is not None:
                    graph.add((n, E[prop], node('record', ref)))
            values(n, [('torqueValue_Nm', measurement.value_Nm), ('torqueQuantityKind', measurement.quantity_kind),
                       ('torqueMeasurementPhase', measurement.phase), ('torqueMeasuredAt', measurement.measured_at),
                       ('torqueMeasurementMethod', measurement.measurement_method), ('torqueTimingBasis', measurement.timing_basis)])
        for reference in self.torque_references:
            n = record(reference, 'TorqueReference')
            values(n, [('torqueReferenceKind', reference.basis_kind), ('torqueReferenceProduct', reference.product_id),
                       ('torqueReferenceTerminationMethod', reference.termination_method),
                       ('torqueReferenceConductorMaterial', reference.conductor_material),
                       ('torqueReferenceConductorSize', reference.conductor_size),
                       ('torqueReferenceFastenerMaterial', reference.fastener_material),
                       ('torqueQuantityKind', reference.quantity_kind), ('torqueMinimum_Nm', reference.minimum_Nm),
                       ('torqueMaximum_Nm', reference.maximum_Nm), ('torqueReferenceScope', reference.applicability_scope)])
        for comparison in self.torque_comparisons:
            n = record(comparison, 'TorqueComparison')
            graph.add((n, E.comparedTorqueMeasurement, node('record', comparison.measurement)))
            graph.add((n, E.comparedTorqueReference, node('record', comparison.reference)))
            values(n, [('torqueApplicabilityBasis', comparison.applicability_basis),
                       ('torqueAssessmentComplete', comparison.assessment_complete),
                       ('claimsPreFireAppliedTorque', comparison.claim_pre_fire_applied_torque)])
        for reference in self.metal_interface_references:
            n = record(reference, 'MetalInterfaceReference')
            values(n, [('metalReferenceKind', reference.basis_kind),
                       ('metalReferenceConductorMaterial', reference.conductor_material),
                       ('metalReferenceConductorGrade', reference.conductor_alloy_grade),
                       ('metalReferenceConductorSize', reference.conductor_size),
                       ('metalReferenceConductorForm', reference.conductor_form),
                       ('metalReferenceTerminationMethod', reference.termination_method),
                       ('metalReferenceMatingMaterial', reference.mating_material),
                       ('metalReferenceMatingCoating', reference.mating_coating),
                       ('metalReferenceInstallationRegion', reference.installation_region),
                       ('metalReferenceInstallationYearFrom', reference.installation_year_from),
                       ('metalReferenceInstallationYearTo', reference.installation_year_to),
                       ('metalReferenceInstallationUse', reference.installation_use),
                       ('metalReferenceDeviceMarking', reference.device_marking),
                       ('referenceConductorOxideBehavior', reference.conductor_oxide_behavior),
                       ('referenceMatingOxideBehavior', reference.mating_oxide_behavior),
                       ('referenceGlowPathExplanation', reference.glow_path_explanation),
                       ('metalReferenceScope', reference.applicability_scope)])
        for comparison in self.metal_interface_comparisons:
            n = record(comparison, 'MetalInterfaceComparison')
            graph.add((n, E.comparedMetalTermination, node('record', comparison.termination)))
            graph.add((n, E.comparedMatingContact, node('record', comparison.mating_contact)))
            graph.add((n, E.comparedMetalReference, node('record', comparison.reference)))
            graph.add((n, E.connectorApprovalStatus, E[comparison.connector_approval_status]))
            values(n, [('installationRegion', comparison.installation_region),
                       ('installationYear', comparison.installation_year),
                       ('installationUse', comparison.installation_use),
                       ('installationUseBasis', comparison.installation_use_basis),
                       ('deviceCompatibilityMarking', comparison.device_marking),
                       ('deviceCompatibilityMarkingBasis', comparison.device_marking_basis),
                       ('connectorApprovalBasis', comparison.approval_basis),
                       ('metalInterfaceApplicabilityBasis', comparison.applicability_basis),
                       ('metalInterfaceAssessmentComplete', comparison.assessment_complete)])
        for p in self.problems:
            n = record(p, 'InvestigationProblemRecord')
            values(n, [('problemStatement', p.statement)])
        for p in self.plans:
            n = record(p, 'InvestigationPlanRecord')
            graph.add((n, E.addressesProblem, node('record', p.problem)))
            values(n, [('plannedScope', p.scope), ('plannedMethod', p.method),
                       ('requiredExpertise', p.required_expertise), ('planComplete', p.complete)])
        for v in self.verifications:
            n = record(v, 'VerificationRecord')
            graph.add((n, E.verifiesPlan, node('record', v.plan)))
            values(n, [('verificationResult', v.result)])
            for ref in v.evidence_records:
                graph.add((n, E.verificationEvidence, node('record', ref)))
        for review in self.technical_reviews:
            n = record(review, 'TechnicalReviewRecord')
            activity = node('review', review.id)
            graph.add((activity, RDF.type, E.TechnicalReview))
            graph.add((activity, E.reviews, session))
            graph.add((activity, E.reviewer, node('agent', review.reviewer)))
            graph.add((n, E.documentsReview, activity))
            values(activity, [('hasDocumentationAccess', review.documentation_access),
                              ('reviewerRelationship', review.reviewer_relationship)])
            if review.reviewer_relationship:
                graph.add((activity, E.reviewerRelationshipDisclosed, RdfLiteral(True)))
            values(n, [('reviewScopeKind', review.scope_kind), ('reviewComplete', review.complete)])
            for ref in review.requested_plans:
                graph.add((n, E.requestedReviewPlan, node('record', ref)))
            for scope in review.scopes:
                sn = record(scope, 'ReviewScopeAssessment')
                graph.add((n, E.hasScopeAssessment, sn))
                graph.add((sn, E.assessesReviewPlan, node('record', scope.plan)))
                graph.add((sn, E.scopeDocumentationAccess, E[scope.documentation_access]))
                values(sn, [('competenceBasis', scope.competence_basis), ('scopeAccessBasis', scope.access_basis),
                            ('scopeCritique', scope.critique)])
        for fuel in self.first_fuels:
            h, _, f = hypotheses[fuel.scenario]
            n = record(fuel, 'FirstFuelAssessment')
            graph.add((h, E.hasFirstFuel, f))
            graph.add((f, RDF.type, E[fuel.fuel_class]))
            graph.add((n, E.assessedScenario, h))
            graph.add((n, E.assessedFuel, f))
            if fuel.presence_basis is not None:
                graph.add((n, E.fuelPresenceBasis, RdfLiteral(fuel.presence_basis)))
        for heat in self.heat_transfers:
            h, m, f = hypotheses[heat.scenario]
            n = record(heat, 'HeatTransferAssessment')
            graph.add((n, E.assessedScenario, h))
            graph.add((n, E.assessedMechanism, m))
            graph.add((n, E.assessedFuel, f))
            for prop, value in ((E.transferDescription, heat.description), (E.heatAdequacyBasis, heat.adequacy_basis),
                                (E.durationBasis, heat.duration_basis), (E.fuelConditionBasis, heat.fuel_condition_basis)):
                if value is not None:
                    graph.add((n, prop, RdfLiteral(value)))
            if heat.description is not None:
                graph.add((h, E.heatTransferPath, RdfLiteral(heat.description)))


def supply_questions(graph: Graph, session: URIRef) -> list[dict]:
    """SHACL이 도출한 경로 확인 결과를 조사 질의로 노출한다."""
    rows = graph.query('''
      PREFIX efi: <https://w3id.org/efi-onto#>
      SELECT ?path ?source ?load WHERE {
        { ?path a efi:SupplyPathAssessment ; efi:recordSession ?session ;
            efi:assessedSource ?source ; efi:assessedLoad ?load .
          FILTER NOT EXISTS { ?path efi:pathConnected true } }
        UNION { ?session efi:hasSystemModel ?model . ?model efi:systemComponent ?source .
          ?source a efi:PowerSource .
          FILTER NOT EXISTS { ?p a efi:SupplyPathAssessment ; efi:recordSystem ?model ; efi:assessedSource ?source }
          BIND (?model AS ?path) }
      } ORDER BY ?path
    ''', initBindings={'session': session})
    return [{'record': str(p), 'source': str(s), 'load': str(t) if t is not None else None,
             'question': '공급원에서 이 대상까지 미확인 연결 구간을 확인하십시오.' if t is not None
             else '이 공급원에서 검토할 부하·회로와 요구 경로를 지정하십시오.'}
            for p, s, t in rows]


def timeline_questions(graph: Graph, session: URIRef) -> list[dict]:
    rows = graph.query('''
      PREFIX efi: <https://w3id.org/efi-onto#>
      SELECT DISTINCT ?record ?reason WHERE {
        ?record efi:recordSession ?session .
        { ?record a efi:ElectricalEventRecord .
          FILTER NOT EXISTS { ?record efi:eventEarliest ?a ; efi:eventLatest ?b ; efi:confirmationStatus efi:Confirmed }
          BIND ("사건 발생 시간 범위와 확인 상태를 확인하십시오. 관찰 시각으로 대체하지 마십시오." AS ?reason) }
        UNION { ?record a efi:ElectricalEventRecord ; efi:electricalEventKind ?kind .
          FILTER (?kind IN ("ArcOccurrence", "ContactArcOccurrence", "PowerDisconnected", "PowerRestored"))
          FILTER NOT EXISTS { ?record efi:eventSupplySource ?source }
          BIND ("이 사건에 해당하는 공급원을 확인하십시오." AS ?reason) }
        UNION { ?record a efi:PowerRecordCoverage .
          FILTER NOT EXISTS { ?record efi:recordAvailability "Available" ; efi:powerHistoryComplete true ; efi:confirmationStatus efi:Confirmed }
          BIND ("전력 기록의 확보 여부·수집 종류·시간 범위를 확인하십시오. 미확보를 정전·복전 부재로 읽지 마십시오." AS ?reason) }
      } ORDER BY ?record ?reason
    ''', initBindings={'session': session})
    return [{'record': str(record), 'question': str(reason)} for record, reason in rows]


def detail_questions(graph: Graph, session: URIRef) -> list[dict]:
    """SHACL의 근거 연결 결과를 다음 조사 질문으로 노출한다. 사실 부재를 도출하지 않는다."""
    queries = [
        ('DamageComparison', 'comparisonContextComplete', '비교 대상의 위치·손상·노출 조건과 금속 재질을 확인하십시오.'),
        ('InvestigationPlanRecord', 'planVerificationSupported', '조사 문제에서 이 계획의 수행 결과와 확인된 근거까지 연결하십시오.'),
        ('TechnicalReviewRecord', 'reviewCoverageSupported', '요청 범위마다 검토자 전문성·자료 접근·실질 비평의 누락을 보완하십시오.'),
        ('MetalDepositionRecord', 'preIgnitionDepositionSequence', '접점 아크 발생원, 절연면 부착, 같은 면의 절연파괴와 발화의 발생 시간 범위를 확인하십시오.'),
        ('TerminationRecord', 'terminationContextSupported', '실제 도체·단자·기기 연결과 접속 구조를 확인하십시오. 뒤쪽 구멍만으로 스프링식과 나사 조임식을 구별하지 마십시오.'),
        ('FastenerRecord', 'fastenerMaterialSupported', '해당 단자 나사의 재질과 식별 근거를 확인하십시오. 자석 반응과 재질 판정을 구분해 기록하십시오.'),
        ('TorqueComparison', 'torqueComparisonSupported', '제품·접속 방식·도체 조건·측정 종류가 일치하는 실제 제품 기준을 확인하십시오. 문헌 시험값을 공통 기준으로 적용하지 마십시오.'),
        ('InsulationHistoryReview', 'insulationHistoryDocumented', '같은 절연재의 재질·충전재와 가열·표면 수분의 발생 시각·근거를 확인하십시오. 110°C만으로 습윤이나 발화 원인을 확정하지 마십시오.'),
        ('MatingContactRecord', 'matingContactIdentified', '실제로 맞닿는 단자·나사·스프링의 모재와 도금, 각각의 식별 근거를 확인하십시오.'),
        ('MetalInterfaceComparison', 'metalInterfaceComparisonSupported', '도체 재질·등급·크기·형태와 접속 금속·도금·방식·사용 위치·설치 시기·지역·적합 표시가 문헌의 적용 범위와 맞는지 확인하십시오.'),
    ]
    questions = []
    for cls, flag, question in queries:
        for record in graph.subjects(RDF.type, E[cls]):
            if (record, E.recordSession, session) in graph and (record, E[flag], RdfLiteral(True)) not in graph:
                questions.append(dict(record=str(record), question=question))
    for problem in graph.subjects(RDF.type, E.InvestigationProblemRecord):
        if (problem, E.recordSession, session) not in graph:
            continue
        if not any((plan, E.recordSession, session) in graph for plan in graph.subjects(E.addressesProblem, problem)):
            questions.append(dict(record=str(problem), question='이 조사 문제를 해결할 범위·방법·전문성 요구를 계획으로 연결하십시오.'))
    return sorted(questions, key=lambda row: (row['record'], row['question']))
