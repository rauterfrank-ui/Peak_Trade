"""Exhaustive first-party census records for Route-C net-mode posSide contract evidence.

Each record is a frozen adjudication of one repository surface. This module does
not perform network I/O and does not treat implementation choices as normative
venue contract proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FirstPartyEvidenceRecordV1:
    record_id: str
    path: str
    symbol_or_range: str
    evidence_role: str
    authority_class: str
    producer: str
    consumer: str
    runtime_reachability: str
    request_body_constructed: bool
    pos_side_present_in_submit_body: bool | None
    pos_side_value_if_present: str | None
    omission_asserted: bool | None
    net_mode_bound: bool | None
    path_kind: str
    transfer_to_route_c_proven: bool
    provenance: str
    currentness: str
    adjudication: str
    proves_submit_body_semantics: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "path": self.path,
            "symbol_or_range": self.symbol_or_range,
            "evidence_role": self.evidence_role,
            "authority_class": self.authority_class,
            "producer": self.producer,
            "consumer": self.consumer,
            "runtime_reachability": self.runtime_reachability,
            "request_body_constructed": self.request_body_constructed,
            "pos_side_present_in_submit_body": self.pos_side_present_in_submit_body,
            "pos_side_value_if_present": self.pos_side_value_if_present,
            "omission_asserted": self.omission_asserted,
            "net_mode_bound": self.net_mode_bound,
            "path_kind": self.path_kind,
            "transfer_to_route_c_proven": self.transfer_to_route_c_proven,
            "provenance": self.provenance,
            "currentness": self.currentness,
            "adjudication": self.adjudication,
            "proves_submit_body_semantics": self.proves_submit_body_semantics,
        }


FIRST_PARTY_EVIDENCE_RECORDS_V1: tuple[FirstPartyEvidenceRecordV1, ...] = (
    FirstPartyEvidenceRecordV1(
        record_id="ORDER_BODY_BUILDER_OMIT",
        path="src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/okx_response_mapper_v1.py",
        symbol_or_range="build_venue_native_order_body_v1",
        evidence_role="VENUE_NATIVE_ORDER_BODY_BUILDER",
        authority_class="FIRST_PARTY_IMPLEMENTATION_NOT_NORMATIVE_CONTRACT",
        producer="okx_response_mapper_v1",
        consumer="canary_order_plan_v1; flatten_order_plan_v1; route_c_offline_candidate",
        runtime_reachability="PRODUCTIVE_BUILDER_CODE_EXISTS_WIRE_UNAUTHORIZED_FOR_ROUTE_C",
        request_body_constructed=True,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=False,
        path_kind="SHARED_ORDER_BODY_BUILDER",
        transfer_to_route_c_proven=False,
        provenance="Cap 11.4 field mapping; omits posSide and posMode by construction",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Builder omission is an implementation choice, not first-party proof that "
            "OKX net_mode create submit bodies must omit posSide for Route-C."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="CANARY_ENTRY_SUBMIT_OMIT",
        path="tests/ops/test_section_11_13_5_canary_submit_transport_v1.py",
        symbol_or_range="test_order_plan_body_equals_proven_builder_contract; test_canary_submit_post_omits_pos_side",
        evidence_role="CANARY_ENTRY_CONTRACT_TEST",
        authority_class="FIRST_PARTY_RAW_EVIDENCE_CANARY_PATH_ONLY",
        producer="build_minimum_valid_canary_order_plan_v1",
        consumer="run_canary_submit_transport_v1",
        runtime_reachability="CANARY_MINIMUM_EXPOSURE_FIXTURE_PATH",
        request_body_constructed=True,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=True,
        path_kind="CANARY_CREATE",
        transfer_to_route_c_proven=False,
        provenance="§11.13.5 canary minimum-exposure entry submit tests",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Canary omit-on-net-mode is a separate path. POS_MODE spec explicitly forbids "
            "transfer to Route-C without direct evidence."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="FLATTEN_SUBMIT_OMIT",
        path="tests/ops/test_section_11_13_5_live_flatten_offline_contract_core_v1.py",
        symbol_or_range="flatten body keys; assert posSide not in body",
        evidence_role="FLATTEN_EXIT_CONTRACT_TEST",
        authority_class="FIRST_PARTY_RAW_EVIDENCE_EXIT_PATH_ONLY",
        producer="build_minimum_valid_canary_flatten_order_plan_v1",
        consumer="flatten submit transport",
        runtime_reachability="FLATTEN_OFFLINE_CONTRACT_ONLY",
        request_body_constructed=True,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=False,
        path_kind="FLATTEN_EXIT",
        transfer_to_route_c_proven=False,
        provenance="LF-01/LF-02 offline flatten contract-core tests",
        currentness="origin/main at 9a764d7e",
        adjudication="Flatten exit bodies omit posSide. Exit path is not Route-C create.",
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="LEVERAGE_INFO_POSSIDE_NET",
        path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/leverage_observation_v1.py",
        symbol_or_range="posSide response field on GET /account/leverage-info",
        evidence_role="LEVERAGE_GET_RESPONSE_FIELD",
        authority_class="FIRST_PARTY_RAW_EVIDENCE_GET_RESPONSE_NOT_SUBMIT_BODY",
        producer="leverage_observation_v1",
        consumer="pretrade leverage gate",
        runtime_reachability="PRIVATE_GET_CONSUMER_CODE",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present="net",
        omission_asserted=False,
        net_mode_bound=True,
        path_kind="LEVERAGE_GET",
        transfer_to_route_c_proven=False,
        provenance="PEAK_TRADE_LEVERAGE_FORENSIC_BINDING spec; posSide=net is row filter",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "leverage-info posSide=net is a GET response scoping field, not submit-body "
            "posSide proof. Explicitly not POS_MODE authority."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="ACCOUNT_CONFIG_POSMODE_NET_MODE",
        path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pos_mode_observation_v1.py",
        symbol_or_range="POS_MODE_REQUIRED_VALUE=net_mode",
        evidence_role="ACCOUNT_CONFIG_POSMODE_OBSERVATION",
        authority_class="CANONICAL_AUTHORITY_POS_MODE_DOMAIN",
        producer="pos_mode_observation_v1",
        consumer="pretrade POS_MODE gate",
        runtime_reachability="PRIVATE_GET_CONSUMER_CODE",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present=None,
        omission_asserted=None,
        net_mode_bound=True,
        path_kind="ACCOUNT_CONFIG_GET",
        transfer_to_route_c_proven=False,
        provenance="PEAK_TRADE_POS_MODE_FORENSIC_BINDING spec §5.3",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "posMode=net_mode is account configuration, not submit-body posSide. "
            "posSide net is a different domain."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="POSITION_GET_POSSIDE",
        path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/prerequisite_08_fresh_position_observation_v1.py",
        symbol_or_range="positions GET row fields include posSide",
        evidence_role="POSITION_REPRESENTATION_GET",
        authority_class="FIRST_PARTY_RAW_EVIDENCE_POSITION_NOT_ORDER_REQUEST",
        producer="prerequisite_08_fresh_position_observation_v1",
        consumer="classify_target_position_state_v1",
        runtime_reachability="PRIVATE_GET_CONSUMER_CODE",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present="observed_on_position_row",
        omission_asserted=None,
        net_mode_bound=False,
        path_kind="POSITIONS_GET",
        transfer_to_route_c_proven=False,
        provenance="Prerequisite-08 positive observation gate",
        currentness="origin/main at 9a764d7e",
        adjudication="Position GET posSide is representation, not order submit semantics.",
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="POS_MODE_SPEC_CANARY_OMIT",
        path="docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md",
        symbol_or_range="posSide construction: unchanged omit-on-net-mode canary contract",
        evidence_role="POS_MODE_CANONICAL_SPEC",
        authority_class="CANONICAL_AUTHORITY_POS_MODE_NOT_SUBMIT_BODY",
        producer="Master Runbook §11.13.5 POS_MODE persist",
        consumer="pretrade POS_MODE consumer",
        runtime_reachability="DOCS_CONTRACT",
        request_body_constructed=False,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=True,
        path_kind="CANARY_CREATE",
        transfer_to_route_c_proven=False,
        provenance="Owner-adjudicated POS_MODE binding; explicit non-transfer rule",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Spec binds POS_MODE only. Canary omit contract is explicitly not Route-C "
            "submit-body proof."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="Z2DP_CREATE_READINESS_ADJUDICATION",
        path="evidence/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/20260903T114921Z/ADJUDICATION.json",
        symbol_or_range="POSITION_MODE_REASON",
        evidence_role="FRESH_GET_READINESS_EVIDENCE",
        authority_class="ALREADY_ADJUDICATED_CONCLUSION",
        producer="z2dp execute_v1/adjudicate_v1",
        consumer="Master Runbook §11.13.5.Z2DP",
        runtime_reachability="GET_EVIDENCE_PACK_NON_SSOT",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present=None,
        omission_asserted=None,
        net_mode_bound=True,
        path_kind="ROUTE_C_CREATE_READINESS",
        transfer_to_route_c_proven=False,
        provenance="Z2DP fresh GET package on LIVE_CANARY credential class",
        currentness="20260903T114921Z evidence pack",
        adjudication=(
            "NO_REPOSITORY_FIRST_PARTY_OKX_SUBMIT_BODY_CONTRACT_FOR_NET_MODE_POSSIDE. "
            "posMode=net_mode observed; posSide submit semantics remain UNPROVEN."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="ROUTE_C_FAIL_CLOSED_CONTRACT",
        path="src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1/position_mode_submit_body_contract_v1.py",
        symbol_or_range="evaluate_position_mode_submit_body_v1",
        evidence_role="ROUTE_C_SUBMIT_BODY_FAIL_CLOSED_GUARD",
        authority_class="CANONICAL_AUTHORITY_STANDING_FAIL_CLOSED",
        producer="route_c_submit_composition_v1",
        consumer="Route-C offline gated submit composition",
        runtime_reachability="OFFLINE_ONLY_NO_HTTP",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present=None,
        omission_asserted=None,
        net_mode_bound=False,
        path_kind="ROUTE_C_CREATE",
        transfer_to_route_c_proven=False,
        provenance="Z2DO offline gated submit composition persist",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Standing guard keeps POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN. "
            "Guard is not proof of required semantics."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="FORENSIC_FLATTEN_OMIT_INVENTORY",
        path="docs/forensics/persistence/inventories/P6_P3_CLASS_D_Z2AP_FLATTEN_PREEXECUTION_READINESS_ADJUDICATION_OBSERVATION_V1.json",
        symbol_or_range="REQUIRED_STATE posSide omitted",
        evidence_role="HISTORICAL_FLATTEN_READINESS_INVENTORY",
        authority_class="HISTORICAL_INTERMEDIATE",
        producer="forensic inventory persist",
        consumer="flatten preexecution track",
        runtime_reachability="HISTORICAL_INVENTORY_ONLY",
        request_body_constructed=True,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=False,
        path_kind="FLATTEN_EXIT",
        transfer_to_route_c_proven=False,
        provenance="P6 Class-D flatten preexecution readiness inventory",
        currentness="historical intermediate",
        adjudication="Historical flatten requirement posSide omitted. Not Route-C create.",
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="TESTNET_POSITION_POSIDE",
        path="evidence/ops/section_11_12_testnet_restart_proven_v1/20260810T223606Z/PATH_restart_with_open_position.json",
        symbol_or_range="positions row posSide net",
        evidence_role="TESTNET_POSITION_EVIDENCE",
        authority_class="HISTORICAL_INTERMEDIATE",
        producer="§11.12.8 testnet campaign",
        consumer="testnet lifecycle proof",
        runtime_reachability="TESTNET_HISTORICAL_NOT_LIVE_ROUTE_C",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present="net",
        omission_asserted=None,
        net_mode_bound=False,
        path_kind="TESTNET_POSITION_GET",
        transfer_to_route_c_proven=False,
        provenance="Testnet restart proven evidence pack",
        currentness="historical testnet campaign",
        adjudication="Testnet position row posSide is not live Route-C order submit proof.",
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="HTTP_CLIENT_SIGNING_FIELD_LIST",
        path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py",
        symbol_or_range="SIGNED_BODY_FIELD_ALLOWLIST includes posSide",
        evidence_role="HTTP_SIGNING_FIELD_ENUMERATION",
        authority_class="FIRST_PARTY_IMPLEMENTATION_NOT_NORMATIVE_CONTRACT",
        producer="LiveCanaryHttpClientV1",
        consumer="entry/flatten submit transport",
        runtime_reachability="GATED_SUBMIT_SURFACE_TYPE_ONLY_FOR_ROUTE_C",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present=None,
        omission_asserted=None,
        net_mode_bound=False,
        path_kind="TRANSPORT_SIGNING",
        transfer_to_route_c_proven=False,
        provenance="Allowed signing fields list for OKX REST bodies",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Signing allowlist permits posSide key if present; does not prove required "
            "semantics for net_mode create."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="Z2DO_ROUTE_C_COMPOSITION",
        path="src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1/route_c_submit_composition_v1.py",
        symbol_or_range="evaluate_position_mode_submit_body_v1 integration",
        evidence_role="ROUTE_C_OFFLINE_COMPOSITION",
        authority_class="CANONICAL_AUTHORITY_STANDING_FAIL_CLOSED",
        producer="compose_route_c_submit_v1",
        consumer="Route-C offline path",
        runtime_reachability="OFFLINE_ONLY",
        request_body_constructed=True,
        pos_side_present_in_submit_body=False,
        pos_side_value_if_present=None,
        omission_asserted=True,
        net_mode_bound=False,
        path_kind="ROUTE_C_CREATE",
        transfer_to_route_c_proven=False,
        provenance="Z2DO three-gap offline composition closure",
        currentness="origin/main at 9a764d7e",
        adjudication=(
            "Route-C candidate uses builder that omits posSide, then fail-closes on "
            "UNPROVEN semantics. Composition is not normative venue proof."
        ),
        proves_submit_body_semantics=False,
    ),
    FirstPartyEvidenceRecordV1(
        record_id="ATLAS_VENUE_FIELD_INDEX",
        path="docs/system_atlas/venue/okx/fields.yaml",
        symbol_or_range="VENUE_FIELD:posSide",
        evidence_role="NAVIGATION_FIELD_INDEX",
        authority_class="NAVIGATION_INDEX",
        producer="system atlas catalog",
        consumer="navigation only",
        runtime_reachability="NONE",
        request_body_constructed=False,
        pos_side_present_in_submit_body=None,
        pos_side_value_if_present=None,
        omission_asserted=None,
        net_mode_bound=False,
        path_kind="NAVIGATION",
        transfer_to_route_c_proven=False,
        provenance="Atlas field census",
        currentness="origin/main at 9a764d7e",
        adjudication="Atlas enumerates posSide field existence; Atlas is not trading authority.",
        proves_submit_body_semantics=False,
    ),
)


def census_summary_v1() -> dict[str, Any]:
    records = FIRST_PARTY_EVIDENCE_RECORDS_V1
    relevant = [r for r in records if r.evidence_role != "NAVIGATION_FIELD_INDEX"]
    proven = [r for r in records if r.proves_submit_body_semantics]
    contradictions = [
        r.record_id
        for r in records
        if r.proves_submit_body_semantics and not r.transfer_to_route_c_proven
    ]
    return {
        "FIRST_PARTY_CANDIDATE_COUNT": len(records),
        "FIRST_PARTY_RELEVANT_EVIDENCE_COUNT": len(relevant),
        "HISTORICAL_CANDIDATE_COUNT": sum(
            1 for r in records if r.authority_class == "HISTORICAL_INTERMEDIATE"
        ),
        "CONTRADICTION_COUNT": len(contradictions),
        "PROVEN_SUBMIT_BODY_SEMANTICS_COUNT": len(proven),
        "UNADJUDICATED_RELEVANT_HIT_COUNT": 0,
        "RECORD_IDS": [r.record_id for r in records],
    }
