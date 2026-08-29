"""§11.13.5.Z2CN persist invariants. Docs/governance plus sanitized snapshot. No runtime."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
SNAPSHOT = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2cn_fresh_unfiltered_target_position_observation_v1"
    / "20260829T011711Z"
    / "GET_SNAPSHOT.sanitized.json"
)

Z2CM_HEADING = (
    "### 11.13.5.Z2CM Post-Z2CL fail-closed position-state predicate and "
    "flatten_execute post-action wiring persist"
)
Z2CN_HEADING = (
    "### 11.13.5.Z2CN Post-Z2CM fresh unfiltered target-position runtime observation persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_POST_Z2CM_FRESH_UNFILTERED_TARGET_POSITION_RUNTIME_OBSERVATION_AND_PERSIST_V1"
)
BASELINE_SHA = "c2f31370aff75bf1973e0e2520a405b8b85c3767"
PARENT_SHA = "c3614ec0ef5d2c964e2de2f6b0df97db9b7331ab"
EMPTY_ENVELOPE_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cn_section(text: str) -> str:
    start = text.find(Z2CN_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CN heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CN"
    return text[start:end]


def _z2cm_section(text: str) -> str:
    start = text.find(Z2CM_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CM heading"
    end = text.find(Z2CN_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CN boundary after Z2CM"
    return text[start:end]


def test_z2cn_heading_is_unique_and_follows_z2cm() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CN_HEADING) == 1
    z2cm = text.find(Z2CM_HEADING)
    z2cn = text.find(Z2CN_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cm < z2cn < ladder


def test_z2cm_historical_slice_was_not_rewritten() -> None:
    section = _z2cm_section(_read(MASTER_RUNBOOK))
    assert "POSITION_STATE_PREDICATE_IMPLEMENTED=true" in section
    assert "POST_ACTION_WIRED_IN_FLATTEN_EXECUTE=true" in section
    assert "CLASS_D_CONSUMED=false" in section
    assert "Z2CN" not in section


def test_z2cn_docs_bind_not_observed_without_zero_or_flatten() -> None:
    section = _z2cn_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CN_FRESH_UNFILTERED_TARGET_POSITION_RUNTIME_OBSERVATION_AND_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"PREVIOUS_ORIGIN_MAIN_SHA={PARENT_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CN",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=true",
        "AUTHENTICATED_GET_CALLS=1",
        "FILTERED_INSTID_GET_PERFORMED=false",
        "INSTID_FILTER_USED=false",
        "CLASSIFICATION_RESULT=TARGET_POSITION_NOT_OBSERVED",
        "TARGET_POSITION_NOT_OBSERVED=true",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "EMPTY_DATA_ARRAY_IS_ZERO=false",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "LIVE_AUTHORIZED=false",
        "P6_RECOVERY_LOOP_ACTIVE=false",
        "BYTE_IDENTICAL_Z2CA_EMPTY_SHA_DOES_NOT_MERGE_THIS_WINDOW=true",
        f"BODY_SHA256={EMPTY_ENVELOPE_SHA}",
        "NO_MAP_OF_TRUTH_MUTATION=true",
    )
    for token in required:
        assert token in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CN" not in text


def test_snapshot_classifies_as_not_observed_not_zero() -> None:
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert payload["SECRET_VALUES_INCLUDED"] is False
    assert payload["INSTID_FILTER_USED"] is False
    assert payload["HTTP_STATUS"] == 200
    assert payload["OKX_CODE"] == "0"
    assert payload["BODY_SHA256"] == EMPTY_ENVELOPE_SHA
    assert payload["BYTE_IDENTICAL_EMPTY_ENVELOPE_SHA_DOES_NOT_MERGE_SOURCE_IDENTITIES"] is True
    body = payload["REDACTED_PAYLOAD"]
    assert body == {"code": "0", "data": [], "msg": ""}
    classified = classify_target_position_state_v1(
        positions_payload=body,
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED
    assert classified.state != TARGET_POSITION_ZERO_PROVEN
    assert classified.state != TARGET_POSITION_NONZERO_PROVEN
    assert classified.empty_data_is_zero is False
    assert classified.query_completeness_proven is False
    assert classified.reason == "TARGET_INSTRUMENT_NOT_OBSERVED"


def test_safety_non_regression_standing_flags_and_gates() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
