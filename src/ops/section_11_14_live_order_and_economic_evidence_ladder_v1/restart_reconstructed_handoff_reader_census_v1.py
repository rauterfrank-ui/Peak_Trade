"""Offline census of existing restart/recovery/handoff-like readers.

Does not select a foreign reader. Does not GET. Does not POST.
"""

from __future__ import annotations

from typing import Any


def bind_restart_reader_census_v1() -> dict[str, Any]:
    rows: list[dict[str, Any]] = [
        {
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_handoff_owner_and_writer_v1.py"
            ),
            "SYMBOL": "load_durable_handoff_record_v1",
            "SOURCE_OWNER": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1",
            "EXPECTED_SCHEMA": "section_11_14_live_durable_pre_restart_handoff.v1",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_WRITER_INTERNAL_LOADER",
            "CURRENT_CALLERS": "commit_handoff_after_bound_fill_before_restart_v1",
            "FAILURE_BEHAVIOR": "RAISES_Section1114OfflineSurfaceError",
            "MISSING_DATA_BEHAVIOR": "DURABLE_HANDOFF_ABSENT",
            "STALE_DATA_BEHAVIOR": "NOT_A_TYPED_RESTART_READER",
            "PROVENANCE_BEHAVIOR": "OWNER_AND_PROVENANCE_CLASS_CHECK_ONLY",
            "INSTRUMENT_VALIDATION": "NONE_BEYOND_WRITER_IDENTITY_KEY",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "PARTIAL_LOADER_NOT_S05_VALIDATOR",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_NOT_TYPED_RESTART_READER",
        },
        {
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_execute_v1.py"
            ),
            "SYMBOL": "census_live_restart_handoff_v1",
            "SOURCE_OWNER": "SECTION_11_14_EVIDENCE_PACKS",
            "EXPECTED_SCHEMA": "NONE",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FORENSIC_CENSUS",
            "CURRENT_CALLERS": "execute_live_restart_reconstructed_v1",
            "FAILURE_BEHAVIOR": "RETURNS_ABSENT_HANDOFF",
            "MISSING_DATA_BEHAVIOR": "DURABLE_PRE_RESTART_HANDOFF_PRESENT=false",
            "STALE_DATA_BEHAVIOR": "NOT_APPLICABLE",
            "PROVENANCE_BEHAVIOR": "EVIDENCE_PACK_IS_NOT_CONTROL_HANDOFF",
            "INSTRUMENT_VALIDATION": "TESTNET_INSTID_DISTINCTNESS_ONLY",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE_EVIDENCE_PACK",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_EVIDENCE_PACK",
        },
        {
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_validators_v1.py"
            ),
            "SYMBOL": "evaluate_handoff_proof_bundle_v1",
            "SOURCE_OWNER": "NONE",
            "EXPECTED_SCHEMA": "section_11_14_live_durable_pre_restart_handoff.v1",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FIXTURE_VALIDATOR",
            "CURRENT_CALLERS": "restart reconstructed tests",
            "FAILURE_BEHAVIOR": "RETURNS_FAIL_CLOSED_CLAIM",
            "MISSING_DATA_BEHAVIOR": "MISSING_DURABLE_STATE",
            "STALE_DATA_BEHAVIOR": "IDENTITY_MISMATCH_OR_STALE",
            "PROVENANCE_BEHAVIOR": "REFUSES_RETROACTIVE_SYNTHESIS",
            "INSTRUMENT_VALIDATION": "BOUND_IDENTITY_EQUALITY",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "COMPATIBLE_BUT_NOT_OWNER_BOUND_READER",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_NOT_OWNER_BOUND_PRODUCTIVE_READER",
        },
        {
            "PATH": "src/ops/canonical_read_model_and_market_dashboard_rebuild_v1/durable_read_model_store_v1.py",
            "SYMBOL": "load_durable_read_model_v1",
            "SOURCE_OWNER": "DASHBOARD_READ_MODEL",
            "EXPECTED_SCHEMA": "dashboard_read_model",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FOR_SECTION_11_14",
            "CURRENT_CALLERS": "dashboard_http_host_v1",
            "FAILURE_BEHAVIOR": "RETURNS_NONE",
            "MISSING_DATA_BEHAVIOR": "NONE",
            "STALE_DATA_BEHAVIOR": "UNKNOWN",
            "PROVENANCE_BEHAVIOR": "NOT_A_LIVE_HANDOFF",
            "INSTRUMENT_VALIDATION": "NONE",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_DASHBOARD_READ_MODEL",
        },
        {
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "private_read_only_gets_v1.py"
            ),
            "SYMBOL": "private_read_only_gets",
            "SOURCE_OWNER": "VENUE_OKX_EEA",
            "EXPECTED_SCHEMA": "OKX_GET",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FORBIDDEN_FOR_HANDOFF",
            "CURRENT_CALLERS": "historical private-read-only slice",
            "FAILURE_BEHAVIOR": "VENUE_ERROR",
            "MISSING_DATA_BEHAVIOR": "VENUE_EMPTY",
            "STALE_DATA_BEHAVIOR": "VENUE_CURRENT_NOT_PRE_RESTART",
            "PROVENANCE_BEHAVIOR": "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF",
            "INSTRUMENT_VALIDATION": "VENUE_INSTID",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE_VENUE_GET",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_VENUE_GET",
        },
        {
            "PATH": (
                "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
                "durable_state_v1.py"
            ),
            "SYMBOL": "load_actual_start_durable_state_v1",
            "SOURCE_OWNER": "TESTNET_CAMPAIGN_DURABLE_STATE",
            "EXPECTED_SCHEMA": "TESTNET_CAMPAIGN_START",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FORBIDDEN",
            "CURRENT_CALLERS": "section_11_12_8 testnet campaign",
            "FAILURE_BEHAVIOR": "TESTNET_STATE_ERROR",
            "MISSING_DATA_BEHAVIOR": "TESTNET_ABSENT",
            "STALE_DATA_BEHAVIOR": "TESTNET_NOT_LIVE_HANDOFF",
            "PROVENANCE_BEHAVIOR": "TESTNET_DURABLE_STATE_NOT_THIS_FIELD",
            "INSTRUMENT_VALIDATION": "TESTNET_INSTID",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE_TESTNET",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_TESTNET_DURABLE_STATE",
        },
        {
            "PATH": (
                "src/ops/section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1/"
                "durable_campaign_state_v1.py"
            ),
            "SYMBOL": "load_campaign_durable_state_v1",
            "SOURCE_OWNER": "TESTNET_CAMPAIGN_DURABLE_STATE",
            "EXPECTED_SCHEMA": "TESTNET_CAMPAIGN_HANDOFF",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FORBIDDEN",
            "CURRENT_CALLERS": "section_11_12_8 campaign activation",
            "FAILURE_BEHAVIOR": "TESTNET_STATE_ERROR",
            "MISSING_DATA_BEHAVIOR": "TESTNET_ABSENT",
            "STALE_DATA_BEHAVIOR": "TESTNET_NOT_LIVE_HANDOFF",
            "PROVENANCE_BEHAVIOR": "TESTNET_DURABLE_STATE_NOT_THIS_FIELD",
            "INSTRUMENT_VALIDATION": "TESTNET_INSTID",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE_TESTNET",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_TESTNET_CAMPAIGN_HANDOFF",
        },
        {
            "PATH": "A1 WAL / DDO / FILEGATE / Cap-7.2 SideState",
            "SYMBOL": "FORBIDDEN_OWNER_REUSE",
            "SOURCE_OWNER": "FORBIDDEN",
            "EXPECTED_SCHEMA": "NOT_HANDOFF_V1",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "NONPRODUCTIVE_FORBIDDEN",
            "CURRENT_CALLERS": "other capabilities",
            "FAILURE_BEHAVIOR": "NOT_THIS_FIELD",
            "MISSING_DATA_BEHAVIOR": "NOT_THIS_FIELD",
            "STALE_DATA_BEHAVIOR": "NOT_THIS_FIELD",
            "PROVENANCE_BEHAVIOR": "FORBIDDEN_OWNER_REUSE",
            "INSTRUMENT_VALIDATION": "NOT_THIS_FIELD",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "INCOMPATIBLE",
            "SECTION_11_14_ELIGIBILITY": "REJECTED_FORBIDDEN_OWNER_REUSE",
        },
        {
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_handoff_reader_v1.py"
            ),
            "SYMBOL": "read_validated_durable_pre_restart_handoff_v1",
            "SOURCE_OWNER": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1",
            "EXPECTED_SCHEMA": "section_11_14_live_durable_pre_restart_handoff.v1",
            "PRODUCTIVE_OR_NONPRODUCTIVE": "PRODUCTIVE",
            "CURRENT_CALLERS": "restart_reconstructed_handoff_consumer_bind_v1",
            "FAILURE_BEHAVIOR": "TYPED_FAIL_CLOSED_RESULT",
            "MISSING_DATA_BEHAVIOR": "MISSING_HANDOFF",
            "STALE_DATA_BEHAVIOR": "STALE_HANDOFF",
            "PROVENANCE_BEHAVIOR": "CONTRACT_PROVEN_ENVELOPE_NO_EMPIRICAL_LIVE_OBSERVATION",
            "INSTRUMENT_VALIDATION": "EXACT_INSTID_EQUALITY",
            "SEMANTIC_COMPATIBILITY_WITH_S05": "COMPATIBLE",
            "SECTION_11_14_ELIGIBILITY": "SELECTED",
        },
    ]
    selected = [row for row in rows if row["SECTION_11_14_ELIGIBILITY"] == "SELECTED"]
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_READER_CENSUS_V1",
        "READER_CANDIDATE_COUNT": len(rows),
        "SELECTED_COUNT": len(selected),
        "SELECTED_PRODUCTIVE_READER": (selected[0]["SYMBOL"] if selected else "NONE"),
        "rows": rows,
    }
