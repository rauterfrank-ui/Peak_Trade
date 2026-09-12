"""Required-field capture-seam and owner-vacancy contract tests for §11.14."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    HOST_CRASH_DURABILITY,
)
from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
    ADMISSION_TRUE,
    DEPENDENT_MUTATION_ALLOWED,
    PRODUCTIVE_HOST_BINDING,
    SUPERVISOR_ACTIVATED,
)
from src.learning.mutation_critical_control_state_storage_v1.crash_reproof_v1 import (
    POWER_LOSS_DURABILITY,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_OWNER_REUSE,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
    HISTORICAL_HANDOFF_READER_PRESENT,
    HISTORICAL_HANDOFF_WRITER_PRESENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_offline_codec_v1 import (
    deserialize_handoff_offline_v1,
    evaluate_offline_handoff_roundtrip_v1,
    serialize_handoff_offline_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    PROPOSED_FIRST_OWNER_ID,
    bind_section_11_14_live_handoff_owner_vacancy_contract_v1,
    refuse_productive_reader_join_v1,
    refuse_productive_writer_join_v1,
    refuse_second_owner_reuse_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_derivation_refusal_v1 import (
    POS_DERIVATION_ALLOWED,
    bind_pos_derivation_adjudication_v1,
    refuse_ambiguous_pos_semantics_v1,
    refuse_pos_derivation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_census_v1 import (
    bind_pos_producer_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_capture_execute_v1 import (
    execute_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS,
    bind_live_order_timeline_capture_v1,
    bind_required_field_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _identity_handoff() -> dict[str, str]:
    return {
        "clOrdId": BOUND_CLORDID,
        "ordId": BOUND_ORDID,
        "instId": BOUND_INSTID,
        "posSide": BOUND_POS_SIDE,
        "pos": "1",
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_V1",
        "provenance_class": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    }


def test_exact_required_field_schema() -> None:
    contract = bind_required_field_contract_v1()
    names = [row["FIELD_NAME"] for row in contract["fields"]]
    assert names == list(REQUIRED_HANDOFF_FIELDS)
    assert names == ["clOrdId", "ordId", "instId", "posSide", "pos"]
    for row in contract["fields"]:
        assert row["NULL_ALLOWED"] is False
        assert row["PEAK_TRADE_OWNERSHIP_REQUIRED"] is True
        assert row["VENUE_DERIVATION_ALLOWED"] is False
        assert row["ACCOUNTING_DERIVATION_ALLOWED"] is False
        assert row["POST_HOC_DERIVATION_ALLOWED"] is False


def test_explicit_pos_semantics_remain_unproven() -> None:
    contract = bind_required_field_contract_v1()
    assert contract["POS_SEMANTICS"] == "UNPROVEN"
    assert POS_SEMANTICS == "UNPROVEN"
    assert contract["POS_IS_INTENDED_POSITION"] == "UNPROVEN"
    assert contract["POS_IS_ACKNOWLEDGED_POSITION"] == "UNPROVEN"
    assert contract["POS_IS_FILLED_POSITION"] == "UNPROVEN"
    assert contract["POS_IS_VENUE_POSITION_AFTER_FILL"] == "UNPROVEN"
    assert contract["POS_IS_PEAK_TRADE_ACCOUNTING_POSITION"] == "UNPROVEN"
    assert contract["POS_ZERO_ALLOWED"] is False
    assert contract["POS_NULL_ALLOWED"] is False


def test_reject_ambiguous_pos_semantics() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="AMBIGUOUS_POS_SEMANTICS"):
        refuse_ambiguous_pos_semantics_v1(claimed_semantics="filled_position")
    accepted = refuse_ambiguous_pos_semantics_v1(claimed_semantics="UNPROVEN")
    assert accepted["POS_SEMANTICS"] == "UNPROVEN"
    assert accepted["ALLOWED"] is False


def test_reject_missing_pos() -> None:
    incomplete = {
        "clOrdId": BOUND_CLORDID,
        "ordId": BOUND_ORDID,
        "instId": BOUND_INSTID,
        "posSide": BOUND_POS_SIDE,
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="MISSING"):
        serialize_handoff_offline_v1(incomplete)


def test_reject_venue_get_substitution() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json"
        ),
        synthetic_from_venue_get=True,
    )
    assert result["claim_value"] is False
    refused = refuse_pos_derivation_v1(derivation_id="E")
    assert refused["ALLOWED"] is False
    assert refused["DISPOSITION"] != POS_DERIVATION_ALLOWED


def test_reject_accounting_substitution() -> None:
    refused = refuse_pos_derivation_v1(derivation_id="F")
    assert refused["ALLOWED"] is False
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["ACCOUNTING_SUBSTITUTION_ALLOWED"] is False


def test_reject_a1_wal_substitution() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["A1_WAL_SUBSTITUTION_ALLOWED"] is False
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="src/learning/mutation_critical_control_state_storage_v1/wal_x.json",
        claimed_owner="MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False


def test_reject_evidence_pack_substitution() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["EVIDENCE_PACK_SUBSTITUTION_ALLOWED"] is False
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T185000Z/ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json"
        ),
        provenance_class="EVIDENCE_PACK_RECLASSIFIED_AS_CONTROL_HANDOFF",
    )
    assert result["claim_value"] is False


def test_reject_testnet_state_substitution() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["TESTNET_STATE_SUBSTITUTION_ALLOWED"] is False
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_12_testnet_restart_proven_v1/"
            "20260810T223606Z/durable_state/restart_with_open_position_pre_restart_v1.json"
        ),
    )
    assert result["claim_value"] is False


def test_reject_timestamp_backfill() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["TIMESTAMP_BACKFILL_ALLOWED"] is False
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        timestamp_backfill=True,
        provenance_class="TIMESTAMP_BACKFILL",
    )
    assert result["claim_value"] is False


def test_reject_retroactive_synthesis() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["RETROACTIVE_SYNTHESIS_ALLOWED"] is False
    refused = refuse_pos_derivation_v1(derivation_id="I")
    assert refused["ALLOWED"] is False


def test_reject_stale_capture() -> None:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["STALE_REJECTION"] is True
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        restart_at_utc="2026-09-04T16:00:00Z",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["temporal"]["TEMPORAL_OK"] is False


def test_reject_identity_mismatch() -> None:
    payload = _identity_handoff()
    payload["clOrdId"] = "wrong"
    result = evaluate_handoff_proof_bundle_v1(
        handoff=payload,
        source_kind=ADMISSIBLE_SOURCE_KIND,
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["identity"]["STALE_OR_IDENTITY_MISMATCH"] is True


def test_reject_wrong_owner() -> None:
    refused = refuse_second_owner_reuse_v1(claimed_owner="SOME_OTHER_OWNER")
    assert refused["ALLOWED"] is False
    assert refused["REASON"] == "REJECT_SECOND_OWNER_REUSE"


def test_reject_second_owner_reuse() -> None:
    for name in FORBIDDEN_OWNER_REUSE:
        refused = refuse_second_owner_reuse_v1(claimed_owner=name)
        assert refused["ALLOWED"] is False
        assert refused["OWNER_IS_SECOND_RESTART_OWNER"] is False


def test_serialize_deserialize_offline_only() -> None:
    payload = _identity_handoff()
    encoded = serialize_handoff_offline_v1(payload)
    decoded = deserialize_handoff_offline_v1(encoded)
    assert decoded["clOrdId"] == BOUND_CLORDID
    assert decoded["pos"] == "1"
    assert decoded["OFFLINE_ONLY"] is True
    assert decoded["PRODUCTIVE_WRITER_JOIN"] is False
    roundtrip = evaluate_offline_handoff_roundtrip_v1(
        payload=payload,
        source_kind=ADMISSIBLE_SOURCE_KIND,
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert roundtrip["OFFLINE_ONLY"] is True
    assert roundtrip["PRODUCTIVE_WRITER_JOIN"] is False
    assert roundtrip["PRODUCTIVE_READER_JOIN"] is False


def test_no_productive_writer_or_reader_binding() -> None:
    writer = refuse_productive_writer_join_v1()
    reader = refuse_productive_reader_join_v1()
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert writer["PRODUCTIVE_WRITER_JOIN_CREATED"] is False
    assert reader["PRODUCTIVE_READER_JOIN_CREATED"] is False
    assert HISTORICAL_HANDOFF_WRITER_PRESENT is False
    assert HISTORICAL_HANDOFF_READER_PRESENT is False
    assert HISTORICAL_HANDOFF_PRODUCTIVE_BINDING is False
    assert vacancy["LATER_WRITER_CLAIMED_POSSIBLE"] is False
    assert vacancy["OWNER_ID"] == "NONE"
    assert vacancy["PROPOSED_FIRST_OWNER_ID"] == PROPOSED_FIRST_OWNER_ID
    assert vacancy["PROPOSED_FIRST_OWNER_IS_NOT_BOUND"] is True


def test_live_restart_reconstructed_admission_supervisor_remain_false() -> None:
    assert LIVE_RESTART_RECONSTRUCTED is False
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert vacancy["ADMISSION_PROMOTION_ALLOWED"] is False
    assert vacancy["SUPERVISOR_PROMOTION_ALLOWED"] is False
    assert vacancy["LIVE_RESTART_PROMOTION_ALLOWED"] is False
    assert ADMISSION_TRUE is False
    assert SUPERVISOR_ACTIVATED is False


def test_execute_is_offline_no_wire_no_live_action() -> None:
    result = execute_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1(
        owner_go=HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO,
        origin_main_sha=HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA,
        repo_root=REPO_ROOT,
        run_id="20260906T210000Z-test",
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["PRODUCTIVE_WRITER_JOIN_CREATED"] is False
    assert summary["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert summary["EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN"] is False
    assert summary["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == "NONE"
    assert result["raw_exchanges"] == []
    assert HISTORICAL_HANDOFF_OWNER_CURRENT_NONE == "NONE"


def test_pos_producer_census_rejects_named_candidates() -> None:
    census = bind_pos_producer_census_v1()
    assert census["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert census["POS_PRODUCER_CANDIDATE_COUNT"] >= 16
    assert census["POS_UNPROVEN_PRODUCER_COUNT"] == 1
    ids = {row["PRODUCER_ID"] for row in census["rows"]}
    assert "LIVE_CANARY_RETURN_PAYLOAD" in ids
    assert "POSITION_GET_POS" in ids
    assert "FILL_SZ" in ids
    for row in census["rows"]:
        assert row["CAN_SATISFY_SECTION_11_14_POS"] is False


def test_capture_moment_has_no_complete_seam() -> None:
    timeline = bind_live_order_timeline_capture_v1()
    assert timeline["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert timeline["EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT"] == "NONE"
    assert (
        "pos" in timeline["MISSING_FIELD_AT_EACH_CANDIDATE_SEAM"]["T4_HTTP_VENUE_ACKNOWLEDGEMENT"]
    )
    assert timeline["CANARY_ACK_OMITS_POS"] is True


def test_all_pos_derivations_are_refused() -> None:
    adjudication = bind_pos_derivation_adjudication_v1()
    assert adjudication["ALLOWED_COUNT"] == 0
    assert adjudication["SUBMITTED_QUANTITY_IS_NOT_FILLED_POSITION"] is True
    assert adjudication["VENUE_GET_IS_NOT_CONTEMPORANEOUS_HANDOFF"] is True
    assert adjudication["ACCOUNTING_IS_NOT_RESTART_HANDOFF"] is True


def test_no_full_core_29p_or_master_v2_mutation() -> None:
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED"
    )
    assert CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY is False
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert PRODUCTIVE_HOST_BINDING is False
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    assert "DOES_NOT_PROVE_HOST_CRASH_OR_POWER_LOSS" in vacancy["PROCESS_RESTART_CLAIM"]


def test_forbidden_provenance_cannot_roundtrip() -> None:
    payload = _identity_handoff()
    payload["provenance_class"] = "VENUE_GET_COPY"
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_PROVENANCE"):
        serialize_handoff_offline_v1(payload)
