"""Offline PR #6252 merge-closeout adjudication. No GET. No POST. No merge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.constants_v1 import (
    APRPI_CLOSED,
    APT_CLOSED,
    AUTHORIZED_OPERATION,
    AUTHORIZED_SCOPE,
    CENSUS_CLOSED,
    CENSUS_RUNTIME_RESIDUAL,
    CLOSEOUT_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    CLOSEOUT_DOES_NOT_AUTHORIZE_GET_VALUE,
    CLOSEOUT_DOES_NOT_AUTHORIZE_POST_VALUE,
    CLOSEOUT_DOES_NOT_AUTHORIZE_RETRY_VALUE,
    CLOSEOUT_DOES_NOT_AUTHORIZE_SECTION_11_14_VALUE,
    CLOSEOUT_DOES_NOT_SET_CANARY_AUTHORIZED_VALUE,
    CLOSEOUT_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO_VALUE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_EMPTY_DATA_PROMOTED_TO_ZERO_VALUE,
    FAIL_CLOSED_IF_G12_MARKED_CLOSED_VALUE,
    FAIL_CLOSED_IF_SECTION_11_14_AUTHORIZED_VALUE,
    G12_STATUS_VALUE,
    GET_PERFORMED_THIS_PERSIST_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    LIVE_FLATTEN_PROVABILITY_PROVEN_VALUE,
    MERGE_AUTHORIZED_BY_THIS_PERSIST_VALUE,
    MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    NEXT_WORKPACKAGE,
    OWNER_GO,
    OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P12_CLOSED,
    P13_CLOSED,
    P16_CLOSED,
    P20_CLOSED,
    P25_CLOSED,
    POST_PERFORMED_VALUE,
    PR_6252_FILE_COUNT,
    PR_6252_HEAD_SHA,
    PR_6252_MERGE_PARENT,
    PR_6252_MERGE_SHA,
    PR_6252_NUMBER,
    PR_6252_STATUS_VALUE,
    PREDECESSOR_EVIDENCE_PACK,
    PREDECESSOR_RECOVERY_PACK,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED_VALUE,
    PRODUCTIVE_FLATTEN_POST_CLOSED,
    PRODUCTIVE_FLATTEN_TEXT_REWRITTEN_VALUE,
    RECOVERY_POSITION_SEMANTICS_VALUE,
    RETRY_ALLOWED_VALUE,
    SECTION_11_14_AUTHORIZED_VALUE,
    STALE_NEXT_POINTER_CORRECTED_VALUE,
    STALE_POINTER_WAS_VALUE,
    STP_CLOSED,
    STPR_CLOSED,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_ZERO_PROVEN_VALUE,
    THIS_GO_GET_COUNT,
    THIS_GO_POST_COUNT,
    THIS_SLICE,
    WORKPACKAGE_COUNT,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.contract_v1 import (
    assert_no_runtime_authority_v1,
    assert_preserved_flatten_residuals_v1,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.lineage_v1 import (
    lineage_census_summary_v1,
    pr_6252_merge_closeout_lineage_v1,
)

FLATTEN_HEADING = "### 11.13.5 PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
CLOSEOUT_HEADING = "### 11.13.5 PR_6252_MERGE_CLOSEOUT"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


class Pr6252MergeCloseoutAdjudicationError(RuntimeError):
    """Fail-closed PR #6252 merge-closeout adjudication violation."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _flatten_section(text: str) -> str:
    start = text.find(FLATTEN_HEADING)
    if start < 0:
        raise Pr6252MergeCloseoutAdjudicationError("FLATTEN_PERSIST_HEADING_MISSING")
    closeout = text.find(CLOSEOUT_HEADING, start)
    ladder = text.find(LADDER_HEADING, start)
    end = closeout if closeout > start else ladder
    if end <= start:
        raise Pr6252MergeCloseoutAdjudicationError("SUCCESSOR_BOUNDARY_MISSING")
    return text[start:end]


def _load_json(rel: str) -> dict[str, Any]:
    path = _repo_root() / rel
    if not path.is_file():
        raise Pr6252MergeCloseoutAdjudicationError(f"MISSING_FORENSIC_PATH:{rel}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Pr6252MergeCloseoutAdjudicationError(f"FORENSIC_JSON_NOT_OBJECT:{rel}")
    return payload


def adjudicate_pr_6252_merge_closeout_v1(*, origin_main_sha: str) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Pr6252MergeCloseoutAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise Pr6252MergeCloseoutAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise Pr6252MergeCloseoutAdjudicationError("IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE")
    confirm = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
    execute_ok, _reasons = evaluate_flatten_execute_authority_v1(
        token=confirm,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise Pr6252MergeCloseoutAdjudicationError("IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE")
    runbook = (_repo_root() / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    flatten = _flatten_section(runbook)
    if "NEXT_OWNER_GO_REQUIRED=OWNER_MERGE_GO" not in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_OWNER_MERGE_POINTER_MISSING")
    if "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN" not in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_G12_OPEN_MISSING")
    if "TARGET_POSITION_ZERO_PROVEN=false" not in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_ZERO_UNPROVEN_MISSING")
    if "LIVE_FLATTEN_PROVABILITY_PROVEN=false" not in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_FLATTEN_UNPROVEN_MISSING")
    if "RECOVERY_POSITION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO" not in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_CASE_C_MISSING")
    if "PRODUCTIVE_FLATTEN_TEXT_REWRITTEN=true" in flatten:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_TEXT_REWRITTEN")
    adjudication = _load_json(f"{PREDECESSOR_EVIDENCE_PACK}/ADJUDICATION.json")
    recovery = _load_json(f"{PREDECESSOR_RECOVERY_PACK}/RECOVERY_RECON.sanitized.json")
    if adjudication.get("G12_STATUS") != G12_STATUS_VALUE:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_EVIDENCE_G12_DRIFT")
    if adjudication.get("TARGET_POSITION_ZERO_PROVEN") is True:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_EVIDENCE_ZERO_PROMOTED")
    if adjudication.get("LIVE_FLATTEN_PROVABILITY_PROVEN") is True:
        raise Pr6252MergeCloseoutAdjudicationError("PREDECESSOR_EVIDENCE_FLATTEN_PROMOTED")
    observation = recovery.get("OBSERVATION")
    if not isinstance(observation, dict):
        raise Pr6252MergeCloseoutAdjudicationError("RECOVERY_OBSERVATION_MISSING")
    if observation.get("POSITION_OBSERVATION_CLASS") != RECOVERY_POSITION_SEMANTICS_VALUE:
        raise Pr6252MergeCloseoutAdjudicationError("RECOVERY_CASE_C_DRIFT")
    if observation.get("TARGET_POSITION_ZERO_PROVEN") is True:
        raise Pr6252MergeCloseoutAdjudicationError("RECOVERY_ZERO_PROMOTED")
    payload = {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "AUTHORIZED_SCOPE": AUTHORIZED_SCOPE,
        "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "PR_6252_NUMBER": PR_6252_NUMBER,
        "PR_6252_STATUS": PR_6252_STATUS_VALUE,
        "PR_6252_MERGE_SHA": PR_6252_MERGE_SHA,
        "PR_6252_MERGE_PARENT": PR_6252_MERGE_PARENT,
        "PR_6252_HEAD_SHA": PR_6252_HEAD_SHA,
        "PR_6252_FILE_COUNT": PR_6252_FILE_COUNT,
        "OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS": (
            OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS
        ),
        "PRODUCTIVE_FLATTEN_TEXT_REWRITTEN": PRODUCTIVE_FLATTEN_TEXT_REWRITTEN_VALUE,
        "STALE_NEXT_POINTER_CORRECTED": STALE_NEXT_POINTER_CORRECTED_VALUE,
        "STALE_POINTER_WAS": STALE_POINTER_WAS_VALUE,
        "G12_STATUS": G12_STATUS_VALUE,
        "TARGET_POSITION_ZERO_PROVEN": TARGET_POSITION_ZERO_PROVEN_VALUE,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": LIVE_FLATTEN_PROVABILITY_PROVEN_VALUE,
        "RECOVERY_POSITION_SEMANTICS": RECOVERY_POSITION_SEMANTICS_VALUE,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO_VALUE,
        "SECTION_11_14_AUTHORIZED": SECTION_11_14_AUTHORIZED_VALUE,
        "RETRY_ALLOWED": RETRY_ALLOWED_VALUE,
        "GET_PERFORMED_THIS_PERSIST": GET_PERFORMED_THIS_PERSIST_VALUE,
        "POST_PERFORMED": POST_PERFORMED_VALUE,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED_VALUE,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": MERGE_AUTHORIZED_BY_THIS_PERSIST_VALUE,
        "CLOSEOUT_DOES_NOT_SET_LIVE_AUTHORIZED": CLOSEOUT_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "CLOSEOUT_DOES_NOT_SET_CANARY_AUTHORIZED": CLOSEOUT_DOES_NOT_SET_CANARY_AUTHORIZED_VALUE,
        "CLOSEOUT_DOES_NOT_AUTHORIZE_GET": CLOSEOUT_DOES_NOT_AUTHORIZE_GET_VALUE,
        "CLOSEOUT_DOES_NOT_AUTHORIZE_POST": CLOSEOUT_DOES_NOT_AUTHORIZE_POST_VALUE,
        "CLOSEOUT_DOES_NOT_AUTHORIZE_RETRY": CLOSEOUT_DOES_NOT_AUTHORIZE_RETRY_VALUE,
        "CLOSEOUT_DOES_NOT_AUTHORIZE_FLATTEN": CLOSEOUT_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "CLOSEOUT_DOES_NOT_AUTHORIZE_SECTION_11_14": (
            CLOSEOUT_DOES_NOT_AUTHORIZE_SECTION_11_14_VALUE
        ),
        "FAIL_CLOSED_IF_G12_MARKED_CLOSED": FAIL_CLOSED_IF_G12_MARKED_CLOSED_VALUE,
        "FAIL_CLOSED_IF_EMPTY_DATA_PROMOTED_TO_ZERO": (
            FAIL_CLOSED_IF_EMPTY_DATA_PROMOTED_TO_ZERO_VALUE
        ),
        "FAIL_CLOSED_IF_SECTION_11_14_AUTHORIZED": FAIL_CLOSED_IF_SECTION_11_14_AUTHORIZED_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "CENSUS_RUNTIME_RESIDUAL": CENSUS_RUNTIME_RESIDUAL,
        "NEXT_WORKPACKAGE": NEXT_WORKPACKAGE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT": MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
        "WORKPACKAGE_COUNT": WORKPACKAGE_COUNT,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "THIS_GO_POST_COUNT": THIS_GO_POST_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_CLOSED": P11_CLOSED,
        "P12_CLOSED": P12_CLOSED,
        "P13_CLOSED": P13_CLOSED,
        "P16_CLOSED": P16_CLOSED,
        "P20_CLOSED": P20_CLOSED,
        "P25_CLOSED": P25_CLOSED,
        "STP_CLOSED": STP_CLOSED,
        "APT_CLOSED": APT_CLOSED,
        "STPR_CLOSED": STPR_CLOSED,
        "CENSUS_CLOSED": CENSUS_CLOSED,
        "APRPI_CLOSED": APRPI_CLOSED,
        "PRODUCTIVE_FLATTEN_POST_CLOSED": PRODUCTIVE_FLATTEN_POST_CLOSED,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "EXECUTION_READY": False,
        "FAIL_CLOSED_STATUS": "PASS",
        "PREDECESSOR_EVIDENCE_PACK": PREDECESSOR_EVIDENCE_PACK,
        "PREDECESSOR_RECOVERY_PACK": PREDECESSOR_RECOVERY_PACK,
    }
    assert_preserved_flatten_residuals_v1(payload)
    assert_no_runtime_authority_v1(payload)
    lineage = pr_6252_merge_closeout_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise Pr6252MergeCloseoutAdjudicationError("LINEAGE_CENSUS_DRIFT")
    payload["CENSUS"] = census
    payload["LINEAGE"] = lineage
    return payload
