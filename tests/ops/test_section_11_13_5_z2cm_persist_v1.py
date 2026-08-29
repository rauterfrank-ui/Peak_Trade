"""§11.13.5.Z2CM persist invariants. Docs/governance only. No runtime."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
PRE_SEND_GATE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "flatten_pre_send_gate_v1.py"
)

Z2CL_HEADING = (
    "### 11.13.5.Z2CL Post-Z2CK CHOICE_B post-action success predicate and "
    "offline productive flatten urllib persist"
)
Z2CM_HEADING = (
    "### 11.13.5.Z2CM Post-Z2CL fail-closed position-state predicate and "
    "flatten_execute post-action wiring persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_11_13_5_Z2CM_FAIL_CLOSED_POSITION_STATE_PREDICATE_AND_"
    "FLATTEN_EXECUTE_POST_ACTION_WIRING_V1"
)
BASELINE_SHA = "c3614ec0ef5d2c964e2de2f6b0df97db9b7331ab"
PARENT_SHA = "71ad51e29bd522a84d6ae3fb848c6af7e03dc7f7"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cm_section(text: str) -> str:
    start = text.find(Z2CM_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CM heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CM"
    return text[start:end]


def _z2cl_section(text: str) -> str:
    start = text.find(Z2CL_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CL heading"
    end = text.find(Z2CM_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CM boundary after Z2CL"
    return text[start:end]


def test_z2cm_heading_is_unique_and_follows_z2cl() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CM_HEADING) == 1
    z2cl = text.find(Z2CL_HEADING)
    z2cm = text.find(Z2CM_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cl < z2cm < ladder


def test_z2cl_historical_slice_was_not_rewritten() -> None:
    section = _z2cl_section(_read(MASTER_RUNBOOK))
    assert "OWNER_CANONICAL_DECISION=CHOICE_B" in section
    assert "POST_ACTION_SUCCESS_PREDICATE_STATUS=BOUND_CHOICE_B" in section
    assert "AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS=REMAINS_UNRESOLVED" in section
    assert "CLASS_D_CONSUMED=false" in section
    assert "Z2CM" not in section


def test_z2cm_docs_bind_predicate_without_flatten_or_live() -> None:
    section = _z2cm_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CM_FAIL_CLOSED_POSITION_STATE_PREDICATE_AND_FLATTEN_EXECUTE_POST_ACTION_WIRING_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"PREVIOUS_ORIGIN_MAIN_SHA={PARENT_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2CL",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CM",
        "P6_RECOVERY_LOOP_ACTIVE=false",
        "POSITION_STATE_PREDICATE_IMPLEMENTED=true",
        "EMPTY_DATA_ARRAY_IS_ZERO=false",
        "DATA_NONE_IS_EMPTY=false",
        "DATA_NONE_IS_NOT_OBSERVED=false",
        "HTTP_200_OR_CODE0_IMPLIES_COMPLETENESS=false",
        "CURRENT_SUI_ZERO_STATE_STATUS=UNPROVEN",
        "POST_ACTION_WIRED_IN_FLATTEN_EXECUTE=true",
        "FLATTEN_POSITION_PROVEN=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "CATEGORY_C_ADDED_TO_GATE_NAMES=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "EMPTY_EQUALS_ZERO=false",
        "Z2CL_TEXT_REWRITTEN=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for token in required:
        assert token in section, token


def test_map_of_truth_not_semantically_mutated_by_z2cm() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "11.13.5.Z2CM" not in text


def test_category_c_remains_absent_from_pre_send_gate_source() -> None:
    src = _read(PRE_SEND_GATE)
    assert "category_c_open_algo_pending_observer_v1" not in src
