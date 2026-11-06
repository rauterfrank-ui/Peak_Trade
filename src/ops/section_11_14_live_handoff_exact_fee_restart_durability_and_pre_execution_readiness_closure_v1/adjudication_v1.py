"""Offline forensic adjudication. No GET. No POST. No restart. No crash."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.constants_v1 import (
    BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN,
    BOUNDED_FEE_ENVELOPE_POLICY_BOUND,
    BOUNDED_FEE_ENVELOPE_PROVEN,
    BOUND_CLORDID,
    BOUND_CT_VAL,
    BOUND_EXEC_TYPE,
    BOUND_FEE_CCY,
    BOUND_FEE_RAW,
    BOUND_FILL_IDX_PX,
    BOUND_FILL_MARK_PX,
    BOUND_FILL_PX,
    BOUND_FILL_SZ,
    BOUND_INST_FAMILY,
    BOUND_INSTRUMENT_ID,
    BOUND_ORDID,
    CANARY_AUTHORIZED_EXACT_FIELD,
    CODE_GAP_FOUND,
    CODE_PATH_EXISTS,
    CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED,
    EARLIEST_LADDER_BLOCKER,
    EARLIEST_REMAINING_BLOCKER,
    EARLIEST_TECHNICAL_BLOCKER,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXACT_OKX_FEE_FORMULA_UNPROVEN,
    EXACT_SETTLED_FEE_STATUS,
    EXECUTION_AUTHORIZATION_STATUS,
    EXPECTED_FEE_PRETRADE_STATUS,
    HANDOFF_WRITTEN,
    HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID,
    HISTORICAL_PRETRADE_GET_RUN_ID,
    HOST_CRASH_DURABILITY_STATUS,
    HOST_CRASH_DURABILITY_UNPROVEN,
    HYPOTHESIS_CLASS,
    HYPOTHESIS_TAKER_RATE_MATCHING_FILL,
    LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN,
    LIVE_RESTART_OBSERVATION_EXISTS,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN,
    LOCAL_FEE_ESTIMATE_STATUS,
    OFFLINE_RECONSTRUCTION_PROOF_EXISTS,
    OWNER_EXECUTION_AUTHORIZED,
    POST_ALLOWED_EXACT_FIELD,
    POST_RESTART_RECONCILIATION_PROOF_EXISTS,
    POWER_LOSS_DURABILITY_STATUS,
    PROCESS_CRASH_DURABILITY_STATIC_MODEL,
    PROCESS_CRASH_DURABILITY_STATUS,
    PRODUCTIVE_BINDING_EXISTS,
    REPAIR_IMPLEMENTED,
    SCHEMA_VERSION,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    TECHNICAL_EXECUTION_READY,
    TECHNICAL_PRE_EXECUTION_READINESS,
    THIS_SLICE,
    VENUE_REPORTED_FEE_POST_FILL_STATUS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED as LADDER_RUNTIME_EXECUTION_AUTHORIZED,
)


class ExactFeeRestartDurabilityClosureError(RuntimeError):
    """Fail-closed forensic closure violation."""


def _dec(raw: object) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExactFeeRestartDurabilityClosureError(f"UNPARSEABLE:{raw}") from exc
    if not value.is_finite():
        raise ExactFeeRestartDurabilityClosureError(f"NON_FINITE:{raw}")
    return value


def assert_standing_live_flags_remain_false_v1() -> dict[str, bool]:
    flags = {
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": bool(LADDER_RUNTIME_EXECUTION_AUTHORIZED),
    }
    if any(flags.values()):
        raised = ",".join(name for name, value in flags.items() if value)
        raise ExactFeeRestartDurabilityClosureError(
            f"STANDING_LIVE_FLAG_MUST_REMAIN_FALSE:{raised}"
        )
    return flags


def historical_fill_hypothesis_algebra_v1() -> dict[str, Any]:
    """Classify the single historical fill algebra. Hypothesis, not OEM proof."""
    fill_px = _dec(BOUND_FILL_PX)
    fill_sz = _dec(BOUND_FILL_SZ)
    ct_val = _dec(BOUND_CT_VAL)
    fee_abs = abs(_dec(BOUND_FEE_RAW))
    hypothesized_rate = _dec(HYPOTHESIS_TAKER_RATE_MATCHING_FILL)
    notional_fill_px = fill_sz * ct_val * fill_px
    reconstructed = hypothesized_rate * notional_fill_px
    mark_notional = fill_sz * ct_val * _dec(BOUND_FILL_MARK_PX)
    idx_notional = fill_sz * ct_val * _dec(BOUND_FILL_IDX_PX)
    return {
        "AUTHORITY_CLASS": HYPOTHESIS_CLASS,
        "IDENTITY": {
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTRUMENT_ID,
            "fillSz": BOUND_FILL_SZ,
            "fillPx": BOUND_FILL_PX,
            "fillMarkPx": BOUND_FILL_MARK_PX,
            "fillIdxPx": BOUND_FILL_IDX_PX,
            "execType": BOUND_EXEC_TYPE,
            "fee": BOUND_FEE_RAW,
            "feeCcy": BOUND_FEE_CCY,
            "ctVal_from_later_instrument_get": BOUND_CT_VAL,
            "evidence_run_id": HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID,
        },
        "MATCHES_FILL_PX_TIMES_HYPOTHESIZED_0_0005": reconstructed == fee_abs,
        "RECONSTRUCTED_AMOUNT_USING_FILL_PX": format(reconstructed, "f"),
        "OBSERVED_FEE_ABS": format(fee_abs, "f"),
        "MARK_PX_RECONSTRUCTION": format(hypothesized_rate * mark_notional, "f"),
        "IDX_PX_RECONSTRUCTION": format(hypothesized_rate * idx_notional, "f"),
        "MARK_PX_EXACT_MATCH": (hypothesized_rate * mark_notional) == fee_abs,
        "IDX_PX_EXACT_MATCH": (hypothesized_rate * idx_notional) == fee_abs,
        "CONTEMPORANEOUS_SUI_TRADE_FEE_GET": False,
        "N_FILLS": 1,
        "MAKER_OBSERVED": False,
        "OEM_ROUNDING_RULE_PROVEN": False,
        "CANNOT_PROVE": [
            "OEM_OKX_FEE_FORMULA",
            "CONTEMPORANEOUS_SUI_FAMILY_RATE",
            "GENERAL_ROUNDING",
            "MAKER_ALGEBRA",
            "MINIMUM_FEE",
            "USD_VS_USDC_SETTLEMENT_RULE",
            "CONTRACT_MULTIPLIER_GENERALITY",
        ],
        "DOES_NOT_CLOSE_EXACT_OKX_FEE_FORMULA": True,
    }


def fee_provenance_table_v1() -> tuple[dict[str, Any], ...]:
    return (
        {
            "PREDICATE": "EXACT_OKX_FEE_FORMULA",
            "VALUE": "UNPROVEN",
            "UNIT": "NONE",
            "SCOPE": f"{BOUND_INST_FAMILY} exact-single entry fill",
            "SOURCE": "Master Runbook §11.14 standing fee persist; fee_policy_v1 EXACT_OKX_FEE_FORMULA_STATUS",
            "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
            "TEMPORAL_BINDING": "CURRENT_STANDING",
            "ACCOUNT_BINDING": "NOT_SUFFICIENT_WITHOUT_CURRENT_TRADE_FEE_GET",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "UNPROVEN",
            "CLOSURE_STATUS": "OPEN",
        },
        {
            "PREDICATE": "EXPECTED_FEE_PRETRADE",
            "VALUE": EXPECTED_FEE_PRETRADE_STATUS,
            "UNIT": "FRACTION_OF_INTERNAL_NOTIONAL_AND_USDC_AMOUNT",
            "SCOPE": "non-executing envelope when current GET present",
            "SOURCE": "standing fee policy bind; NEW_GET_EXECUTED=false; pretrade pack omitted trade-fee",
            "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
            "TEMPORAL_BINDING": "POLICY_CURRENT_NUMERIC_ABSENT",
            "ACCOUNT_BINDING": "REQUIRES_CURRENT_GET",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "UNPROVEN",
            "CLOSURE_STATUS": "OPEN",
        },
        {
            "PREDICATE": "VENUE_REPORTED_FEE_POST_FILL",
            "VALUE": BOUND_FEE_RAW,
            "UNIT": BOUND_FEE_CCY,
            "SCOPE": f"historical identity-bound fill {BOUND_ORDID}",
            "SOURCE": f"evidence/{HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID}/GET_FILLS.raw.json",
            "AUTHORITY_CLASS": "FORENSIC_RAW_EVIDENCE",
            "TEMPORAL_BINDING": HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID,
            "ACCOUNT_BINDING": "IDENTITY_BOUND_HISTORICAL",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "PROVEN_SINGLE_FILL",
            "CLOSURE_STATUS": "CLOSED_AS_POST_FILL_OBSERVATION_NOT_PRETRADE_FORMULA",
        },
        {
            "PREDICATE": "LOCAL_FEE_ESTIMATE",
            "VALUE": "conservative_debit_rate=max(debit(taker),debit(maker)); amount=rate*qty*ctVal*worst_fill_px",
            "UNIT": "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_NOT_OEM_OKX_FEE_FORMULA",
            "SCOPE": "standing policy",
            "SOURCE": "src/ops/.../fee_policy_v1.py",
            "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
            "TEMPORAL_BINDING": "POLICY_BOUND",
            "ACCOUNT_BINDING": "NUMERIC_REQUIRES_CURRENT_GET",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "POLICY_PROVEN_NUMERIC_UNPROVEN",
            "CLOSURE_STATUS": "OPEN_NUMERIC",
        },
        {
            "PREDICATE": "EXACT_SETTLED_FEE",
            "VALUE": EXACT_SETTLED_FEE_STATUS,
            "UNIT": BOUND_FEE_CCY,
            "SCOPE": "historical single fill; not general settlement formula",
            "SOURCE": f"GET /api/v5/trade/fills fee={BOUND_FEE_RAW}",
            "AUTHORITY_CLASS": "FORENSIC_RAW_EVIDENCE",
            "TEMPORAL_BINDING": HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID,
            "ACCOUNT_BINDING": "IDENTITY_BOUND_HISTORICAL",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "PROVEN_SINGLE_FILL",
            "CLOSURE_STATUS": "NOT_GENERAL_FORMULA",
        },
        {
            "PREDICATE": "BOUNDED_FEE_ENVELOPE",
            "VALUE": "false",
            "UNIT": "POLICY_BOUND_NUMERIC_UNPROVEN",
            "SCOPE": BOUND_INSTRUMENT_ID,
            "SOURCE": f"pretrade pack {HISTORICAL_PRETRADE_GET_RUN_ID} omitted /api/v5/account/trade-fee",
            "AUTHORITY_CLASS": "ALREADY_ADJUDICATED_RESULTS",
            "TEMPORAL_BINDING": "CURRENT_GET_ABSENT",
            "ACCOUNT_BINDING": "UNBOUND_NUMERIC",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "UNPROVEN",
            "CLOSURE_STATUS": "OPEN",
        },
        {
            "PREDICATE": "MAKER_VS_TAKER",
            "VALUE": f"historical execType={BOUND_EXEC_TYPE}; pretrade uses max(debit(taker),debit(maker))",
            "UNIT": "NONE",
            "SCOPE": "entry fill",
            "SOURCE": "GET_FILLS.raw.json execType; fee_policy_v1 MAKER_TAKER_ASSUMPTION",
            "AUTHORITY_CLASS": "FORENSIC_RAW_EVIDENCE",
            "TEMPORAL_BINDING": "MIXED_HISTORICAL_AND_POLICY",
            "ACCOUNT_BINDING": "HISTORICAL_FILL_TAKER_ONLY",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "PARTIAL",
            "CLOSURE_STATUS": "OPEN_FOR_GENERAL_FORMULA",
        },
        {
            "PREDICATE": "DELIVERY_VS_TRADE_FEE",
            "VALUE": "delivery observable and NOT_PART_OF_ENTRY_FILL",
            "UNIT": "FRACTION_OF_NOTIONAL",
            "SCOPE": "entry fill vs expiry",
            "SOURCE": "Master Runbook standing fee persist A",
            "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
            "TEMPORAL_BINDING": "CURRENT_POLICY",
            "ACCOUNT_BINDING": "N/A",
            "INSTRUMENT_BINDING": BOUND_INST_FAMILY,
            "PROVENANCE_STATUS": "POLICY_PROVEN",
            "CLOSURE_STATUS": "CLOSED_AS_EXCLUSION",
        },
        {
            "PREDICATE": "SIGN_CONVENTION",
            "VALUE": "VENUE_NEGATIVE_IS_DEBIT",
            "UNIT": "NONE",
            "SCOPE": "trade-fee rates and fill fee",
            "SOURCE": "fee_policy_v1; observed fee=-0.000374",
            "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
            "TEMPORAL_BINDING": "CURRENT_POLICY_PLUS_HISTORICAL_FILL",
            "ACCOUNT_BINDING": "IDENTITY_BOUND_HISTORICAL_FOR_FILL",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "PROVEN_FOR_OBSERVED_FILL_AND_POLICY",
            "CLOSURE_STATUS": "CLOSED_AS_POLICY_NOT_OEM_PROOF",
        },
        {
            "PREDICATE": "HISTORICAL_0_0005_FILL_PX_MATCH",
            "VALUE": HYPOTHESIS_TAKER_RATE_MATCHING_FILL,
            "UNIT": "FRACTION_OF_FILLPX_NOTIONAL",
            "SCOPE": "one historical taker fill",
            "SOURCE": "computed from GET_FILLS.raw.json; not contemporaneous trade-fee GET",
            "AUTHORITY_CLASS": "HYPOTHESES",
            "TEMPORAL_BINDING": HISTORICAL_FILL_FEE_EVIDENCE_RUN_ID,
            "ACCOUNT_BINDING": "IDENTITY_BOUND_HISTORICAL",
            "INSTRUMENT_BINDING": BOUND_INSTRUMENT_ID,
            "PROVENANCE_STATUS": "HYPOTHESIS",
            "CLOSURE_STATUS": "NOT_FORMULA_PROOF",
        },
    )


def restart_adjudication_v1() -> dict[str, Any]:
    return {
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN": LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN,
        "LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN": LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN,
        "CODE_PATH_EXISTS": CODE_PATH_EXISTS,
        "PRODUCTIVE_BINDING_EXISTS": PRODUCTIVE_BINDING_EXISTS,
        "OFFLINE_RECONSTRUCTION_PROOF_EXISTS": OFFLINE_RECONSTRUCTION_PROOF_EXISTS,
        "LIVE_RESTART_OBSERVATION_EXISTS": LIVE_RESTART_OBSERVATION_EXISTS,
        "POST_RESTART_RECONCILIATION_PROOF_EXISTS": POST_RESTART_RECONCILIATION_PROOF_EXISTS,
        "HANDOFF_WRITTEN": HANDOFF_WRITTEN,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED,
        "PRODUCTIVE_HOST_ENTRY_POINT": "NOT_STARTED_THIS_WORKPACKAGE",
        "LIFECYCLE_OWNER": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1",
        "RESTART_READER": (
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_handoff_reader_v1.py::read_validated_durable_pre_restart_handoff_v1"
        ),
        "CAPTURE_READER": "same_as_restart_reader_validated_handoff",
        "STATE_RESTORATION_PATH": (
            "fail_closed_MISSING_HANDOFF_when_durable_record_absent;"
            "identity_restore_only_from_contemporaneous_handoff"
        ),
        "DURABLE_STATE_SOURCE": (
            "durable_state/section_11_14_live_durable_pre_restart_handoff_v1/pre_restart/"
            "restart_with_open_position_pre_restart_v1.json"
        ),
        "TRANSIENT_ONLY_STATE": (
            "in_memory_runtime_gates;ephemeral_credentials;wire_handle;clOrdId_until_execution_GO"
        ),
        "AUTHORIZATION_SURVIVES_RESTART": False,
        "AUTHORIZATION_INTENTIONALLY_MUST_NOT_SURVIVE_RESTART": True,
        "AUTHORIZATION_RESTORATION_SEMANTICS": (
            "LIVE_ENABLED/LIVE_ARMED/POST_ALLOWED/CANARY_AUTHORIZED/"
            "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED remain compile-time false;"
            "no persisted execution grant is reconstituted"
        ),
        "OUTSTANDING_ORDER_POSITION_RECONCILIATION": (
            "requires_fresh_GET_after_restart_not_performed"
        ),
        "IDEMPOTENCY_DUPLICATE_SUBMIT_PROTECTION": (
            "writer rejects second identity; empirical restart not observed"
        ),
        "FACTS_LOADED_VS_RECOMPUTED": {
            "loaded_if_present": ["clOrdId", "ordId", "instId", "posSide", "pos"],
            "must_fresh_GET": [
                "account_balance",
                "positions",
                "pending_orders",
                "fills",
                "trade_fee",
                "ticker",
                "price_limit",
            ],
            "must_not_reload_as_true": [
                "LIVE_ENABLED",
                "LIVE_ARMED",
                "OWNER_EXECUTION_AUTHORIZED",
                "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            ],
        },
        "FAIL_CLOSED_WHEN_EVIDENCE_ABSENT_OR_STALE": True,
        "STATIC_SUCCESSFUL_IDENTITY_RECONSTRUCTION_PROVEN": False,
        "STATIC_FAIL_CLOSED_RECONSTRUCTION_PROVEN": True,
        "RESTART_EXECUTED": False,
        "DOES_NOT_CLOSE_LIVE_RESTART_RECONSTRUCTED": True,
    }


def durability_adjudication_v1() -> dict[str, Any]:
    return {
        "PERSIST_OWNER": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1",
        "WRITE_PATH": ("restart_reconstructed_handoff_owner_and_writer_v1._atomic_replace_write"),
        "TEMP_FILE_SEMANTICS": "path.with_suffix(.json.tmp) then os.replace",
        "RENAME_REPLACE_SEMANTICS": "os.replace",
        "FLUSH": "os.write then fsync(file) before replace",
        "FSYNC_FILE": True,
        "FSYNC_DIRECTORY": True,
        "FSYNC_DIRECTORY_FAILURE": "FSYNC_DURABILITY_UNCERTAINTY fail-closed",
        "ATOMICITY_ASSUMPTIONS": "POSIX os.replace of fully fsynced tmp file",
        "PROCESS_CRASH_SEMANTICS": PROCESS_CRASH_DURABILITY_STATIC_MODEL,
        "HOST_CRASH_SEMANTICS": HOST_CRASH_DURABILITY_STATUS,
        "POWER_LOSS_SEMANTICS": POWER_LOSS_DURABILITY_STATUS,
        "FILESYSTEM_ASSUMPTIONS": "POSIX_RENAME_ATOMICITY_NOT_STABLE_MEDIA_PROOF",
        "PARTIAL_WRITE_BEHAVIOR": "tmp discarded on WRITE_FAILURE; target unchanged if replace not reached",
        "STALE_READER_BEHAVIOR": "MISSING_HANDOFF or STALE_HANDOFF fail-closed",
        "CORRUPT_ARTIFACT_HANDLING": "CORRUPT_OR_TORN_RECORD / MALFORMED_HANDOFF",
        "STARTUP_VALIDATION": "schema/owner/provenance/identity/completeness checks",
        "CHECKSUM_HASH_SCHEMA_VERSION": "schema_version plus owner_id plus provenance_class; no content checksum",
        "WRITE_ORDERING": "serialize then fsync(file) then replace then fsync(dir)",
        "MULTI_FILE_TRANSACTIONALITY": "single_file_handoff",
        "PROCESS_CRASH_DURABILITY_STATUS": PROCESS_CRASH_DURABILITY_STATUS,
        "HOST_CRASH_DURABILITY_UNPROVEN": HOST_CRASH_DURABILITY_UNPROVEN,
        "HOST_CRASH_DURABILITY_STATUS": HOST_CRASH_DURABILITY_STATUS,
        "POWER_LOSS_DURABILITY_STATUS": POWER_LOSS_DURABILITY_STATUS,
        "F_FULLFSYNC_USED_BY_11_14_WRITER": False,
        "DDO_A1_PRIMITIVE_REUSED_BY_11_14_WRITER": False,
        "SYSCALL_SUCCESS_IS_HOST_CRASH_PROOF": False,
        "PROCESS_KILL_IS_HOST_CRASH_PROOF": False,
        "DDO_A1_PROOF_IS_NOT_THIS_OWNER": True,
        "CODE_GAP_FOUND": CODE_GAP_FOUND,
        "REPAIR_IMPLEMENTED": REPAIR_IMPLEMENTED,
        "DOES_NOT_CLOSE_HOST_CRASH_DURABILITY": True,
        "CRASH_TEST_EXECUTED": False,
    }


def predicate_row(
    *,
    name: str,
    value: object,
    status: str,
    source: str,
    authority: str,
    freshness: str,
    blocking: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "PREDICATE": name,
        "VALUE": value,
        "STATUS": status,
        "SOURCE": source,
        "AUTHORITY": authority,
        "FRESHNESS": freshness,
        "BLOCKING": blocking,
        "NOTES": notes,
    }


def complete_pre_execution_predicate_table_v1() -> tuple[dict[str, Any], ...]:
    return (
        predicate_row(
            name="ORIGIN_MAIN_BOUND",
            value="0731a62bec6dd7ef87d80b1c7959d30381f1b983",
            status="PROVEN",
            source="git rev-parse origin/main after fetch",
            authority="CANONICAL_AUTHORITY",
            freshness="THIS_WORKPACKAGE",
            blocking=False,
            notes="matches EXPECTED_ORIGIN_MAIN_SHA and PR_6334 merge commit",
        ),
        predicate_row(
            name="TRACKED_TREE_CLEAN",
            value="0033a378a9ca223f6ad34e75ed1f5276794f4198",
            status="PROVEN",
            source="git rev-parse origin/main^{tree}; git diff HEAD origin/main empty",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="THIS_WORKPACKAGE_PRE_MUTATION",
            blocking=False,
            notes="untracked artifacts exist and were not touched",
        ),
        predicate_row(
            name="CURRENT_PHASE",
            value=THIS_SLICE,
            status="PROVEN",
            source="this workpackage persist",
            authority="CANONICAL_AUTHORITY",
            freshness="THIS_WORKPACKAGE",
            blocking=False,
            notes="additive persist; predecessor standing-fee envelope remains bound",
        ),
        predicate_row(
            name="CURRENT_INSTRUMENT_BOUND",
            value=BOUND_INSTRUMENT_ID,
            status="PROVEN",
            source="Master Runbook latest persist; pretrade GET pack",
            authority="CANONICAL_AUTHORITY",
            freshness="POLICY_CURRENT_OBSERVATION_STALE_RELATIVE_TO_THIS_WP",
            blocking=False,
            notes="instrument identity bound; live state observation not refreshed here",
        ),
        predicate_row(
            name="CURRENT_ACCOUNT_BOUND",
            value="uid_sha256=2444af6ea59bad87ee2aa709df3aa6888607cb3ba31f1946729f3f4f4697fb2c",
            status="PROVEN",
            source=f"pretrade GET pack {HISTORICAL_PRETRADE_GET_RUN_ID} account/config",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness=HISTORICAL_PRETRADE_GET_RUN_ID,
            blocking=False,
            notes="historical current-as-of 20260907T182140Z; not re-GET this WP",
        ),
        predicate_row(
            name="NETWORK_READINESS",
            value="PASS_AT_20260907T182140Z",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} NETWORK_EGRESS_COMPATIBILITY_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="no current GET this WP; previous pack is not this WP's observation",
        ),
        predicate_row(
            name="PRIVATE_GET_READINESS",
            value="SURFACE_EXISTS_NOT_INVOKED",
            status="UNPROVEN",
            source="GET-only orchestrator allowlist",
            authority="CANONICAL_AUTHORITY",
            freshness="NOT_OBSERVED_THIS_WP",
            blocking=True,
            notes="optional GET not executed; NEW_GET_EXECUTED=false",
        ),
        predicate_row(
            name="INSTRUMENT_STATE",
            value="live",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} INSTRUMENT_STATE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="observed live at 18:21Z; not re-proven here",
        ),
        predicate_row(
            name="ACCOUNT_MODE",
            value="2",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} ACCOUNT_MODE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="acctLv=2 at prior GET; not re-proven here",
        ),
        predicate_row(
            name="POSITION_MODE",
            value="net_mode",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} POSITION_MODE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="posMode=net_mode at prior GET; not re-proven here",
        ),
        predicate_row(
            name="MARGIN_MODE",
            value="cross",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} MARGIN_MODE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="mgnMode=cross at prior GET; not re-proven here",
        ),
        predicate_row(
            name="LEVERAGE",
            value="3",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} LEVERAGE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="lever=3 cross net at prior GET; not re-proven here",
        ),
        predicate_row(
            name="PRICE_BAND",
            value="buyLmt=0.8277 sellLmt=0.8194 at prior GET",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} PRICE_BAND_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="price-limit is time-varying; not re-GET",
        ),
        predicate_row(
            name="MAX_SIZE",
            value="maxBuy=7 at px=0.8237 prior GET",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} MAX_AVAILABLE_MAX_SIZE_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="max-size depends on px and margin; not re-GET",
        ),
        predicate_row(
            name="MAX_AVAILABLE",
            value="maxBuy=7",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID}",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="same observation as MAX_SIZE",
        ),
        predicate_row(
            name="AVAILABLE_MARGIN",
            value="availEq=2.1076094140463697 USDC at prior GET",
            status="UNPROVEN",
            source=f"{HISTORICAL_PRETRADE_GET_RUN_ID} AVAILABLE_MARGIN_CURRENT",
            authority="FORENSIC_RAW_EVIDENCE",
            freshness="STALE_NOT_THIS_WP",
            blocking=True,
            notes="balance is time-varying; not re-GET",
        ),
        predicate_row(
            name="EXPECTED_FEE_MODEL",
            value="conservative_max_debit_internal_notional",
            status="PROVEN",
            source="standing fee policy",
            authority="CANONICAL_AUTHORITY",
            freshness="POLICY_BOUND",
            blocking=False,
            notes="model is not OEM exact formula",
        ),
        predicate_row(
            name="EXACT_OKX_FEE_FORMULA",
            value=EXACT_OKX_FEE_FORMULA_STATUS,
            status="UNPROVEN",
            source="Master Runbook; fee_policy_v1; this forensic census",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="single historical fill algebra is hypothesis only",
        ),
        predicate_row(
            name="FEE_ENVELOPE",
            value=BOUNDED_FEE_ENVELOPE_PROVEN,
            status="UNPROVEN",
            source="policy bound; current SUI trade-fee GET absent",
            authority="CANONICAL_AUTHORITY",
            freshness="NUMERIC_ABSENT",
            blocking=True,
            notes="BOUNDED_FEE_ENVELOPE_POLICY_BOUND=true; current numeric false",
        ),
        predicate_row(
            name="SLIPPAGE_BOUND",
            value="LIMIT_WORST_FILL_EQUALS_LIMIT_PX",
            status="PROVEN",
            source="standing slippage policy",
            authority="CANONICAL_AUTHORITY",
            freshness="POLICY_BOUND",
            blocking=False,
            notes="numeric worst price still requires current ticker/limit; not refreshed here",
        ),
        predicate_row(
            name="LIVE_RESTART_STATIC_RECONSTRUCTION",
            value=LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN,
            status="PROVEN",
            source="writer/reader/validators fail-closed missing handoff",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT_CODE",
            blocking=False,
            notes="fail-closed static path proven; successful empirical reconstruction unproven",
        ),
        predicate_row(
            name="LIVE_RESTART_EMPIRICAL_RECONSTRUCTION",
            value=LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN,
            status="UNPROVEN",
            source="HANDOFF_WRITTEN=false; no restart executed",
            authority="ALREADY_ADJUDICATED_RESULTS",
            freshness="CURRENT",
            blocking=True,
            notes="cannot close without contemporaneous capture then restart observation",
        ),
        predicate_row(
            name="PROCESS_CRASH_DURABILITY",
            value=PROCESS_CRASH_DURABILITY_STATUS,
            status="UNPROVEN",
            source="atomic replace + fsync(file) + fsync(dir)",
            authority="INTERPRETATION",
            freshness="STATIC_MODEL",
            blocking=False,
            notes="static model supported; empirical process-kill on this owner not executed",
        ),
        predicate_row(
            name="HOST_CRASH_DURABILITY",
            value=HOST_CRASH_DURABILITY_STATUS,
            status="UNPROVEN",
            source="DDO_A1 plus 11.14 writer; no crash/power-loss test",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=False,
            notes="HOST_CRASH_DURABILITY_REQUIRED_FOR_LIVE_RESTART_RECONSTRUCTED=false; still unproven",
        ),
        predicate_row(
            name="CAPTURE_PROVENANCE",
            value="COMPLETE_SEAM_OFFLINE_NO_PRODUCTIVE_CAPTURE",
            status="UNPROVEN",
            source="complete capture seam proven offline; productive capture false",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="required for LIVE_RESTART_RECONSTRUCTED success path",
        ),
        predicate_row(
            name="POST_FILL_RECONCILIATION",
            value="HISTORICAL_IDENTITY_BOUND_TRUE_NOT_CURRENT_FILL",
            status="UNPROVEN",
            source="LIVE_POSITION_RECONCILED/ACCOUNTING historical",
            authority="ALREADY_ADJUDICATED_RESULTS",
            freshness="HISTORICAL_NOT_CURRENT_FILL",
            blocking=False,
            notes="historical fill/fee/position/accounting remain true; not a new fill",
        ),
        predicate_row(
            name="LIVE_ENABLED",
            value=False,
            status="PROVEN",
            source="constants_v1.LIVE_ENABLED",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="standing false; this GO must not set true",
        ),
        predicate_row(
            name="LIVE_ARMED",
            value=False,
            status="PROVEN",
            source="constants_v1.LIVE_ARMED",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="standing false",
        ),
        predicate_row(
            name="CANARY_EXECUTE_AUTHORIZED",
            value=False,
            status="PROVEN",
            source="Master Runbook §4.9 standing fail-closed",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="related gate; not reconstructed as CANARY_AUTHORIZED persist field",
        ),
        predicate_row(
            name="OWNER_EXECUTION_AUTHORIZED",
            value=OWNER_EXECUTION_AUTHORIZED,
            status="PROVEN",
            source="this GO and predecessor persist",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="this GO is not OWNER_EXECUTION_GO",
        ),
        predicate_row(
            name="SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            value=SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
            status="PROVEN",
            source="constants_v1 and this persist",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="remains false",
        ),
        predicate_row(
            name="ORDER_SUBMIT_AUTHORIZED",
            value=False,
            status="PROVEN",
            source="Master Runbook §4.9",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="related standing gate",
        ),
        predicate_row(
            name="SUBMIT_UNLOCKED",
            value=False,
            status="PROVEN",
            source="constants_v1.SUBMIT_UNLOCKED",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT",
            blocking=True,
            notes="standing false",
        ),
        predicate_row(
            name="POST_ALLOWED_EXACT_FIELD",
            value=POST_ALLOWED_EXACT_FIELD,
            status="INDETERMINATE",
            source="absent from latest Master Runbook persist block 71122-71217",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT_PERSIST_ABSENT",
            blocking=False,
            notes="code constant POST_ALLOWED=false exists; persist token absent so not reconstructed",
        ),
        predicate_row(
            name="CANARY_AUTHORIZED_EXACT_FIELD",
            value=CANARY_AUTHORIZED_EXACT_FIELD,
            status="INDETERMINATE",
            source="absent from latest Master Runbook persist block 71122-71217",
            authority="CANONICAL_AUTHORITY",
            freshness="CURRENT_PERSIST_ABSENT",
            blocking=False,
            notes="code constant CANARY_AUTHORIZED=false exists; persist token absent so not reconstructed",
        ),
    )


def adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1(
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    flags = assert_standing_live_flags_remain_false_v1()
    if OWNER_EXECUTION_AUTHORIZED or SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED:
        raise ExactFeeRestartDurabilityClosureError("EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if LIVE_RESTART_RECONSTRUCTED:
        raise ExactFeeRestartDurabilityClosureError("RESTART_FIELD_MUST_REMAIN_FALSE")
    if not EXACT_OKX_FEE_FORMULA_UNPROVEN:
        raise ExactFeeRestartDurabilityClosureError("EXACT_FORMULA_MUST_REMAIN_UNPROVEN")
    if BOUNDED_FEE_ENVELOPE_PROVEN:
        raise ExactFeeRestartDurabilityClosureError("NUMERIC_ENVELOPE_MUST_REMAIN_UNPROVEN")
    if not HOST_CRASH_DURABILITY_UNPROVEN:
        raise ExactFeeRestartDurabilityClosureError("HOST_CRASH_MUST_REMAIN_UNPROVEN")
    payload: dict[str, Any] = {
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "THIS_SLICE": THIS_SLICE,
        "EXACT_OKX_FEE_FORMULA_UNPROVEN": EXACT_OKX_FEE_FORMULA_UNPROVEN,
        "EXACT_OKX_FEE_FORMULA_STATUS": EXACT_OKX_FEE_FORMULA_STATUS,
        "BOUNDED_FEE_ENVELOPE_POLICY_BOUND": BOUNDED_FEE_ENVELOPE_POLICY_BOUND,
        "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN": BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN,
        "BOUNDED_FEE_ENVELOPE_PROVEN": BOUNDED_FEE_ENVELOPE_PROVEN,
        "EXPECTED_FEE_PRETRADE_STATUS": EXPECTED_FEE_PRETRADE_STATUS,
        "VENUE_REPORTED_FEE_POST_FILL_STATUS": VENUE_REPORTED_FEE_POST_FILL_STATUS,
        "LOCAL_FEE_ESTIMATE_STATUS": LOCAL_FEE_ESTIMATE_STATUS,
        "EXACT_SETTLED_FEE_STATUS": EXACT_SETTLED_FEE_STATUS,
        "LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN": LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN,
        "LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN": LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "PROCESS_CRASH_DURABILITY_STATUS": PROCESS_CRASH_DURABILITY_STATUS,
        "HOST_CRASH_DURABILITY_UNPROVEN": HOST_CRASH_DURABILITY_UNPROVEN,
        "HOST_CRASH_DURABILITY_STATUS": HOST_CRASH_DURABILITY_STATUS,
        "POWER_LOSS_DURABILITY_STATUS": POWER_LOSS_DURABILITY_STATUS,
        "CODE_GAP_FOUND": CODE_GAP_FOUND,
        "REPAIR_IMPLEMENTED": REPAIR_IMPLEMENTED,
        "CANARY_AUTHORIZED_EXACT_FIELD": CANARY_AUTHORIZED_EXACT_FIELD,
        "POST_ALLOWED_EXACT_FIELD": POST_ALLOWED_EXACT_FIELD,
        "OWNER_EXECUTION_AUTHORIZED": OWNER_EXECUTION_AUTHORIZED,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
        "TECHNICAL_PRE_EXECUTION_READINESS": TECHNICAL_PRE_EXECUTION_READINESS,
        "TECHNICAL_EXECUTION_READY": TECHNICAL_EXECUTION_READY,
        "EXECUTION_AUTHORIZATION_STATUS": EXECUTION_AUTHORIZATION_STATUS,
        "EARLIEST_REMAINING_BLOCKER": EARLIEST_REMAINING_BLOCKER,
        "EARLIEST_TECHNICAL_BLOCKER": EARLIEST_TECHNICAL_BLOCKER,
        "EARLIEST_LADDER_BLOCKER": EARLIEST_LADDER_BLOCKER,
        "STANDING_LIVE_FLAGS": flags,
        "FEE_HYPOTHESIS": historical_fill_hypothesis_algebra_v1(),
        "FEE_PROVENANCE": list(fee_provenance_table_v1()),
        "RESTART": restart_adjudication_v1(),
        "DURABILITY": durability_adjudication_v1(),
        "PREDICATE_TABLE": list(complete_pre_execution_predicate_table_v1()),
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "CASE_ADJUDICATION": (
            "CASE_EXACT_FEE_UNPROVEN_BOUNDED_NUMERIC_ENVELOPE_UNPROVEN_"
            "STATIC_RESTART_FAIL_CLOSED_PROVEN_EMPIRICAL_RESTART_FALSE_"
            "HOST_CRASH_UNPROVEN_TECHNICAL_PRE_EXECUTION_READINESS_FALSE_"
            "OWNER_EXECUTION_NOT_AUTHORIZED"
        ),
    }
    if extra:
        payload.update(dict(extra))
    return payload
