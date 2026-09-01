"""§11.13.5.Z2CT persist invariants. Docs/governance plus sanitized snapshot. No runtime."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import verify_manifest_v1
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    THIS_WINDOW_OWNER_GO as OBSERVATION_OWNER_GO,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2ct_prerequisite_08_single_unfiltered_position_observation_v1"
    / "20260901T095111Z"
)
SNAPSHOT = EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json"
ADJUDICATION = EVIDENCE_PACK / "ADJUDICATION.json"

Z2CS_HEADING = (
    "### 11.13.5.Z2CS Post-Z2CR Prerequisite-08 resolution-authority adjudication persist"
)
Z2CT_HEADING = (
    "### 11.13.5.Z2CT Post-Z2CS single unfiltered Prerequisite-08 position observation persist"
)
Z2CU_HEADING = "### 11.13.5.Z2CU Post-Z2CT named progression-track adjudication persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_PREREQUISITE_08_SINGLE_UNFILTERED_POSITION_OBSERVATION_V1"
)
BASELINE_SHA = "607c80bfb608be1cab6575f30ee79a387cf3b7d6"
EMPTY_ENVELOPE_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ct_section(text: str) -> str:
    start = text.find(Z2CT_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CT heading"
    end = text.find(Z2CU_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CU boundary after Z2CT"
    return text[start:end]


def _z2cs_section(text: str) -> str:
    start = text.find(Z2CS_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CS heading"
    end = text.find(Z2CT_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CT boundary after Z2CS"
    return text[start:end]


def test_z2ct_heading_is_unique_and_follows_z2cs() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CT_HEADING) == 1
    z2cs = text.find(Z2CS_HEADING)
    z2ct = text.find(Z2CT_HEADING)
    z2cu = text.find(Z2CU_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cs < z2ct < z2cu < ladder


def test_z2cs_historical_adjudication_slice_was_not_rewritten() -> None:
    section = _z2cs_section(_read(MASTER_RUNBOOK))
    assert "GET_EXECUTED_THIS_PERSIST=false" in section
    assert "ADJUDICATION=RESOLUTION_PATH_ALREADY_EXISTS" in section
    assert "CONTRACT_GAP_CLASS=NONE" in section
    assert "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW" in section
    assert "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CR" in section
    assert "Z2CT" not in section


def test_z2ct_docs_bind_not_observed_without_zero_or_flatten() -> None:
    section = _z2ct_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CT_PREREQUISITE_08_SINGLE_UNFILTERED_POSITION_OBSERVATION_AND_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_STARTING_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PR_6193_STATUS=MERGED",
        "ADJUDICATION_AT_BASELINE=RESOLUTION_PATH_ALREADY_EXISTS",
        "CONTRACT_GAP_CLASS=NONE",
        "PREDECESSOR_SLICE=11.13.5.Z2CS",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CT",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=true",
        "AUTHENTICATED_GET_CALLS=1",
        "VENUE_API_CALLS=1",
        "FILTERED_INSTID_GET_PERFORMED=false",
        "INSTID_FILTER_USED=false",
        "INSTID_QUERY_PARAMETER_PRESENT=false",
        "GET_FILTER_MODE=UNFILTERED",
        "MAX_RETRIES=0",
        "CLASSIFICATION_RESULT=TARGET_POSITION_NOT_OBSERVED",
        "TARGET_ROW_OBSERVED=false",
        "TARGET_POSITION_STATE=NOT_OBSERVED",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "TARGET_POSITION_QTY_NUMERIC=UNRESOLVED",
        "TARGET_POSITION_QTY_UNIT=UNPROVEN",
        "POSITION_QTY_UNIT_STATUS=UNPROVEN",
        "EMPTY_DATA_IS_ZERO=false",
        "EMPTY_DATA_ARRAY_IS_ZERO=false",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "EXECUTION_PREREQUISITE_09_STATUS=DEPENDENT_PREREQUISITE_BLOCKED_BY_08",
        "EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "FLATTEN_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "FRESHNESS_STATUS=PASS",
        "OBSERVATION_WINDOW_FRESHNESS_STATUS=PASS",
        "FRESHNESS_POLICY_MAX_AGE_MS=5000",
        "OBSERVATION_AGE_AT_ADJUDICATION_MS=0",
        "FLATTEN_PRE_SEND_PERMIT_EVALUATED=false",
        "FLATTEN_PRE_SEND_FRESHNESS_EVALUATED=false",
        "SEND_TIME_PASS=UNPROVEN",
        "UNIQUE_WINDOW_IDENTITY_PRESERVED=true",
        "BYTE_IDENTICAL_EMPTY_ENVELOPE_SHA_DOES_NOT_MERGE_SOURCE_IDENTITIES=true",
        f"BODY_SHA256={EMPTY_ENVELOPE_SHA}",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "Z2CT_DOES_NOT_CONSTRUCT_FLATTEN_PAYLOAD=true",
        "Z2CS_TEXT_REWRITTEN=false",
        "Z2CR_TEXT_REWRITTEN=false",
        "Z2CN_TEXT_REWRITTEN=false",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    )
    for token in required:
        assert token in section, token


def test_z2ct_docs_forbid_activation_and_08_proof() -> None:
    section = _z2ct_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nFLATTEN_AUTHORIZED=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nEMPTY_DATA_ARRAY_IS_ZERO=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nSEND_TIME_PASS=PROVEN\n",
        "\nSEND_TIME_PASS_18_19_21_24=PROVEN\n",
        "\nPOSITION_QTY_UNIT_STATUS=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CT" not in text
    assert "11.13.5.Z2CT" not in text


def test_snapshot_and_adjudication_remain_distinct_and_not_zero() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    adjudication = json.loads(ADJUDICATION.read_text(encoding="utf-8"))
    assert snapshot["DOCUMENT_ROLE"] == "RAW_SANITIZED_RUNTIME_EVIDENCE_NOT_SSOT"
    assert adjudication["DOCUMENT_ROLE"] == "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT"
    assert snapshot["DOCUMENT_CLASS"].startswith("SECTION_11_13_5_Z2CT_")
    assert adjudication["DOCUMENT_CLASS"].startswith("SECTION_11_13_5_Z2CT_")
    assert snapshot["SECRET_VALUES_INCLUDED"] is False
    assert snapshot["INSTID_FILTER_USED"] is False
    assert snapshot["QUERY_PARAMETERS"] == {}
    assert snapshot["ENDPOINT"] == "/api/v5/account/positions"
    assert snapshot["HTTP_STATUS"] == 200
    assert snapshot["OKX_CODE"] == "0"
    assert snapshot["BODY_SHA256"] == EMPTY_ENVELOPE_SHA
    assert snapshot["UNIQUE_WINDOW_IDENTITY_PRESERVED"] is True
    assert snapshot["BYTE_IDENTICAL_EMPTY_ENVELOPE_SHA_DOES_NOT_MERGE_SOURCE_IDENTITIES"] is True
    body = snapshot["REDACTED_PAYLOAD"]
    assert body == {"code": "0", "data": [], "msg": ""}
    classified = classify_target_position_state_v1(
        positions_payload=body,
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED
    assert classified.state != TARGET_POSITION_ZERO_PROVEN
    assert classified.state != TARGET_POSITION_NONZERO_PROVEN
    assert classified.empty_data_is_zero is False
    assert classified.reason == "TARGET_INSTRUMENT_NOT_OBSERVED"
    assert adjudication["TARGET_ROW_OBSERVED"] is False
    assert adjudication["TARGET_POSITION_STATE"] == "NOT_OBSERVED"
    assert adjudication["EXECUTION_PREREQUISITE_08_STATUS"] == (
        "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
    )
    assert adjudication["EXECUTION_PREREQUISITE_09_STATUS"] == (
        "DEPENDENT_PREREQUISITE_BLOCKED_BY_08"
    )
    assert adjudication["POSITION_QTY_UNIT_STATUS"] == "UNPROVEN"
    assert adjudication["BYTE_IDENTICAL_Z2CN_EMPTY_SHA_DOES_NOT_MERGE_THIS_WINDOW"] is True
    assert adjudication["FRESHNESS_STATUS"] == "PASS"
    assert adjudication["FLATTEN_PRE_SEND_PERMIT_EVALUATED"] is False
    assert adjudication["FLATTEN_PRE_SEND_FRESHNESS_EVALUATED"] is False
    assert adjudication["SEND_TIME_PASS_18_19_21_24"] == "UNPROVEN"
    assert int(adjudication["OBSERVATION_AGE_AT_ADJUDICATION_MS"]) == 0
    verify = verify_manifest_v1(EVIDENCE_PACK)
    assert verify["MANIFEST_VERIFY_RC"] == 0


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert "TARGET_POSITION_STATE" in GATE_NAMES
    assert OWNER_GO == OBSERVATION_OWNER_GO
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
