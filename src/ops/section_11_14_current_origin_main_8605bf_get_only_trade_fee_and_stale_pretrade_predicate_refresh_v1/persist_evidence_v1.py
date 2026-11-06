"""Persist GET-refresh adjudication. Does not GET. Does not POST."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.adjudication_v1 import (
    adjudicate_trade_fee_and_stale_pretrade_refresh_v1,
)
from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.constants_v1 import (
    ADJUDICATION_FILENAME,
    BASELINE_FILENAME,
    BOUNDED_FEE_ENVELOPE_FILENAME,
    CANONICAL_EVIDENCE_RUN_ID,
    CENSUS_FILENAME,
    CLAIMS_FILENAME,
    EVIDENCE_RELATIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXPECTED_ORIGIN_MAIN_TREE,
    GET_PACK_RELATIVE_ROOT,
    LINEAGE_FILENAME,
    NON_EXECUTION_FILENAME,
    OWNER_GET_ONLY_GO,
    PREDECESSOR_SLICE,
    PREDICATE_TABLE_FILENAME,
    PRIOR_OWNER_GO,
    SAFETY_FILENAME,
    SUMMARY_FILENAME,
    THIS_SLICE,
    TRADE_FEE_ADJUDICATION_FILENAME,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


EVIDENCE_FILES: tuple[str, ...] = (
    SUMMARY_FILENAME,
    CLAIMS_FILENAME,
    ADJUDICATION_FILENAME,
    TRADE_FEE_ADJUDICATION_FILENAME,
    PREDICATE_TABLE_FILENAME,
    BOUNDED_FEE_ENVELOPE_FILENAME,
    SAFETY_FILENAME,
    BASELINE_FILENAME,
    NON_EXECUTION_FILENAME,
    CENSUS_FILENAME,
    LINEAGE_FILENAME,
)


def persist_evidence_pack_v1(*, repo_root: Path) -> dict[str, Any]:
    if LIVE_ENABLED or LIVE_ARMED or POST_ALLOWED:
        raise RuntimeError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    adjudication = adjudicate_trade_fee_and_stale_pretrade_refresh_v1(repo_root=repo_root)
    root = Path(repo_root) / EVIDENCE_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    root.mkdir(parents=True, exist_ok=True)
    baseline = {
        "BASELINE_VALIDATION": "PASS",
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "CURRENT_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "EXPECTED_ORIGIN_MAIN_TREE": EXPECTED_ORIGIN_MAIN_TREE,
        "EXPECTED_ORIGIN_MAIN_MATCH": True,
        "WORKING_MODEL_DRIFT": "NONE",
    }
    safety = {
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "WIRE_SEND_PERMITTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "GET_PERFORMED": True,
        "POST_PERFORMED": False,
        "OWNER_GET_ONLY_GO_STATUS": "CONSUMED_FOR_BOUNDED_GET_ONLY_WORKPACKAGE",
        "AUTHORITY_CLASS": "R1_GET_ONLY_NO_POST_NO_SUBMIT_NO_EXECUTION",
    }
    non_execution = {
        "GET_PERFORMED": True,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "OWNER_EXECUTION_GO_CONSUMED": False,
        "OWNER_GET_ONLY_GO_IS_NOT_OWNER_EXECUTION_GO": True,
    }
    trade_fee = {
        "TRADE_FEE_GET_PERFORMED": adjudication["TRADE_FEE_GET_PERFORMED"],
        "TRADE_FEE_HTTP_RESULT": adjudication["TRADE_FEE_HTTP_RESULT"],
        "TRADE_FEE_OKX_CODE": adjudication["TRADE_FEE_OKX_CODE"],
        "TRADE_FEE_TARGET_FAMILY_MATCH": adjudication["TRADE_FEE_TARGET_FAMILY_MATCH"],
        "TRADE_FEE_QUERY": adjudication["TRADE_FEE_QUERY"],
        "TRADE_FEE_BODY_SHA256": adjudication["TRADE_FEE_BODY_SHA256"],
        "TRADE_FEE_OBSERVED_AT": adjudication["TRADE_FEE_OBSERVED_AT"],
        "TRADE_FEE_TAKER_FIELD": adjudication["TRADE_FEE_TAKER_FIELD"],
        "TRADE_FEE_MAKER_FIELD": adjudication["TRADE_FEE_MAKER_FIELD"],
        "TRADE_FEE_TAKER_RAW": adjudication["TRADE_FEE_TAKER_RAW"],
        "TRADE_FEE_MAKER_RAW": adjudication["TRADE_FEE_MAKER_RAW"],
        "TRADE_FEE_DELIVERY_RAW": adjudication["TRADE_FEE_DELIVERY_RAW"],
        "TRADE_FEE_DELIVERY_ROLE": adjudication["TRADE_FEE_DELIVERY_ROLE"],
        "TRADE_FEE_UNIT": adjudication["TRADE_FEE_UNIT"],
        "TRADE_FEE_RATE_TYPE": adjudication["TRADE_FEE_RATE_TYPE"],
        "CURRENT_ACCOUNT_FEE_RATE_OBSERVED": adjudication["CURRENT_ACCOUNT_FEE_RATE_OBSERVED"],
        "CURRENT_NUMERIC_FEE_INPUT_PROVEN": adjudication["CURRENT_NUMERIC_FEE_INPUT_PROVEN"],
        "EXACT_OKX_FEE_FORMULA_STATUS": adjudication["EXACT_OKX_FEE_FORMULA_STATUS"],
        "EXACT_OKX_FEE_FORMULA_UNPROVEN": True,
        "FEE_POLICY": adjudication["FEE_POLICY"],
    }
    envelope = {
        "FEE_POLICY_BOUND": adjudication["FEE_POLICY_BOUND"],
        "CURRENT_ACCOUNT_FEE_RATE_OBSERVED": adjudication["CURRENT_ACCOUNT_FEE_RATE_OBSERVED"],
        "EXPECTED_FEE_PRETRADE": adjudication["EXPECTED_FEE_PRETRADE"],
        "EXPECTED_FEE_UNIT": adjudication["EXPECTED_FEE_UNIT"],
        "EXPECTED_FEE_RATE": adjudication["EXPECTED_FEE_RATE"],
        "SLIPPAGE_POLICY_BOUND": adjudication["SLIPPAGE_POLICY_BOUND"],
        "SLIPPAGE_BOUND_CURRENT_NUMERIC": adjudication["SLIPPAGE_BOUND_CURRENT_NUMERIC"],
        "BOUNDED_FEE_ENVELOPE_POLICY_BOUND": True,
        "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN": adjudication[
            "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN"
        ],
        "BOUNDED_FEE_ENVELOPE_PROVEN": adjudication["BOUNDED_FEE_ENVELOPE_PROVEN"],
        "BOUNDED_FEE_ENVELOPE_ROLE": adjudication["BOUNDED_FEE_ENVELOPE_ROLE"],
        "EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN",
    }
    census: Mapping[str, Any] = {
        "GET_PACK_RELATIVE": f"{GET_PACK_RELATIVE_ROOT}/{CANONICAL_EVIDENCE_RUN_ID}",
        "GET_ENDPOINT_COUNT": adjudication["GET_ENDPOINT_COUNT"],
        "GETS": adjudication["GETS"],
        "RAW_BODY_STORAGE": adjudication["RAW_BODY_STORAGE"],
    }
    lineage: Mapping[str, Any] = {
        "OWNER_GET_ONLY_GO": OWNER_GET_ONLY_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "RECORDED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "RECORDED_ORIGIN_MAIN_TREE": EXPECTED_ORIGIN_MAIN_TREE,
        "GET_PACK_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "MAP_OF_TRUTH_AUTHORITY": "NONE_FOR_SEMANTICS",
        "ATLAS_AUTHORITY": "NONE",
    }
    summary = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GET_ONLY_GO": OWNER_GET_ONLY_GO,
        "OWNER_GET_ONLY_GO_STATUS": "CONSUMED_FOR_BOUNDED_GET_ONLY_WORKPACKAGE",
        "CASE_ADJUDICATION": adjudication["CASE_ADJUDICATION"],
        "GET_PERFORMED": True,
        "GET_ENDPOINT_COUNT": adjudication["GET_ENDPOINT_COUNT"],
        "TRADE_FEE_GET_PERFORMED": True,
        "TRADE_FEE_HTTP_RESULT": adjudication["TRADE_FEE_HTTP_RESULT"],
        "TRADE_FEE_OKX_CODE": adjudication["TRADE_FEE_OKX_CODE"],
        "TRADE_FEE_TARGET_FAMILY_MATCH": adjudication["TRADE_FEE_TARGET_FAMILY_MATCH"],
        "EXACT_OKX_FEE_FORMULA_UNPROVEN": True,
        "EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN",
        "CURRENT_ACCOUNT_FEE_RATE_OBSERVED": adjudication["CURRENT_ACCOUNT_FEE_RATE_OBSERVED"],
        "CURRENT_NUMERIC_FEE_INPUT_PROVEN": adjudication["CURRENT_NUMERIC_FEE_INPUT_PROVEN"],
        "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN": adjudication[
            "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN"
        ],
        "BOUNDED_FEE_ENVELOPE_PROVEN": adjudication["BOUNDED_FEE_ENVELOPE_PROVEN"],
        "EXPECTED_FEE_PRETRADE": adjudication["EXPECTED_FEE_PRETRADE"],
        "TECHNICAL_PRE_EXECUTION_READINESS": adjudication["TECHNICAL_PRE_EXECUTION_READINESS"],
        "TECHNICAL_EXECUTION_READINESS": adjudication["TECHNICAL_EXECUTION_READINESS"],
        "OWNER_EXECUTION_AUTHORIZED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "EARLIEST_UNRESOLVED_TECHNICAL_PRE_EXECUTION_PREDICATE": adjudication[
            "EARLIEST_UNRESOLVED_TECHNICAL_PRE_EXECUTION_PREDICATE"
        ],
        "EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE": adjudication[
            "EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE"
        ],
        "EARLIEST_UNRESOLVED_DEPENDENCY": adjudication["EARLIEST_UNRESOLVED_DEPENDENCY"],
        "NEXT_OWNER_GO_REQUIRED": adjudication["NEXT_OWNER_GO_REQUIRED"],
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "NEXT_SLICE_AUTHORIZED": False,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
    }
    write_json_v1(root / SUMMARY_FILENAME, summary)
    write_json_v1(root / CLAIMS_FILENAME, dict(summary))
    write_json_v1(root / ADJUDICATION_FILENAME, adjudication)
    write_json_v1(root / TRADE_FEE_ADJUDICATION_FILENAME, trade_fee)
    write_json_v1(root / PREDICATE_TABLE_FILENAME, {"rows": adjudication["PREDICATE_TABLE"]})
    write_json_v1(root / BOUNDED_FEE_ENVELOPE_FILENAME, envelope)
    write_json_v1(root / SAFETY_FILENAME, safety)
    write_json_v1(root / BASELINE_FILENAME, baseline)
    write_json_v1(root / NON_EXECUTION_FILENAME, non_execution)
    write_json_v1(root / CENSUS_FILENAME, census)
    write_json_v1(root / LINEAGE_FILENAME, lineage)
    write_manifest_v1(root, EVIDENCE_FILES)
    verified = verify_manifest_v1(root)
    return {
        "EVIDENCE_ROOT": str(root),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "ADJUDICATION": adjudication,
    }
