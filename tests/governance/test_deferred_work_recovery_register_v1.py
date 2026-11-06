"""Capability 0.4 — Deferred-Work Recovery Register + rotation policy resubmission."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.deferred_work_recovery_register_contract_v1 import (
    ACTIVATION_AUTHORIZED,
    CANONICAL_REGISTER_PATH,
    CAPABILITY_RECOVERY_ID,
    CLASSIFICATION_DEFERRED_REQUIRED,
    HUMAN_COMPANION_PATH,
    IMPLEMENTATION_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PHASE_1_MAX_POSITIONS,
    PHASE_1_SELECTION,
    REMINDER_PATH,
    REQUIRED_BLOCKING_DEPENDENCIES,
    REQUIRED_REVIEW_CLOSURES,
    ROTATION_CAPABILITY_ID,
    TARGET_PHASE_6,
    DeferredWorkRecoveryRegisterError,
    assert_no_productive_top5_claims,
    get_entry,
    load_register,
    validate_register,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_TRUTH_MAP = (
    REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md"
)
CAPABILITY_RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md"
)
CAPABILITY_SPEC = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1.md"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


def test_capability_constants_stable() -> None:
    assert CAPABILITY_RECOVERY_ID.endswith("ROTATION_POLICY_RESUBMISSION_V1")
    assert ROTATION_CAPABILITY_ID == "MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0"
    assert IMPLEMENTATION_AUTHORIZED is False
    assert ACTIVATION_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert PHASE_1_SELECTION == "SINGLE_SELECTED_FUTURE"
    assert PHASE_1_MAX_POSITIONS == 1


def test_canonical_register_present_and_validates() -> None:
    assert CANONICAL_REGISTER_PATH.is_file()
    register = validate_register()
    assert register["register_id"] == "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1"
    assert register["parallel_register_forbidden"] is True


def test_rotation_capability_registered_with_required_semantics() -> None:
    register = load_register()
    entry = get_entry(register, ROTATION_CAPABILITY_ID)
    assert entry["CLASSIFICATION"] == CLASSIFICATION_DEFERRED_REQUIRED
    assert entry["TARGET_PHASE"] == TARGET_PHASE_6
    assert entry["IMPLEMENTATION_AUTHORIZED"] is False
    assert entry["ACTIVATION_AUTHORIZED"] is False
    assert entry["CURRENT_RUNTIME_EFFECT"] == "NONE"
    assert entry["PHASE_1_SELECTION"] == "SINGLE_SELECTED_FUTURE"
    assert entry["PHASE_1_MAX_POSITIONS"] == 1
    assert entry["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False

    deps = set(entry["BLOCKING_DEPENDENCIES"])
    assert REQUIRED_BLOCKING_DEPENDENCIES.issubset(deps)

    trigger = entry["REVIEW_TRIGGER"]
    assert trigger["event_based"] is True
    assert trigger["reminder_only"] is False
    assert REQUIRED_REVIEW_CLOSURES.issubset(set(trigger["required_closures"]))

    guards = register["semantic_guards"]
    assert guards["SINGLE_SELECTED_FUTURE_IS_CURRENT_AUTHORITY"] is True
    assert guards["TOP_N_ACTIVE_SET_IS_DEFERRED"] is True
    assert guards["TOP5_PRODUCTIVE"] is False
    assert guards["TOP5_REGRESSED"] is False
    assert guards["MULTI_FUTURE_IMPLEMENTED"] is False
    assert guards["MULTI_FUTURE_AUTHORIZED"] is False
    assert guards["MAX_POSITIONS_EFFECTIVE"] == 1
    assert guards["ROTATION_POLICY_RATIFIED"] is False
    assert guards["ROTATION_IMPLEMENTATION_STARTED"] is False


def test_human_companion_and_spec_crosslinks() -> None:
    companion = _read(HUMAN_COMPANION_PATH)
    assert "DOCS_TOKEN_PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1" in companion
    assert ROTATION_CAPABILITY_ID in companion
    assert "DEFERRED_REQUIRED_CAPABILITY" in companion
    assert "PHASE_6" in companion
    assert "TOP5_PRODUCTIVE=false" in companion
    assert "SINGLE_SELECTED_FUTURE" in companion
    assert "does **not** change the current trading path" in companion

    spec = _read(CAPABILITY_SPEC)
    assert "DOCS_TOKEN_DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1" in spec
    assert CAPABILITY_RECOVERY_ID in spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in spec
    assert "ACTIVATION_AUTHORIZED=false" in spec
    assert "MULTI_FUTURE_RUNTIME_AUTHORIZED=false" in spec


def test_reminder_remains_reminder_only_and_points_to_register() -> None:
    reminder = _read(REMINDER_PATH)
    assert "REMINDER" in reminder.upper() or "reminder" in reminder
    assert "IMPLEMENTATION_STARTED=false" in reminder
    assert "TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false" in reminder
    assert "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1" in reminder
    assert "DEFERRED_REQUIRED_CAPABILITY" in reminder
    assert "AUTHORITY_SUPERSEDED_BY_CANONICAL_REGISTER=true" in reminder


def test_runtime_truth_map_and_runbook_point_to_register() -> None:
    truth = _read(RUNTIME_TRUTH_MAP)
    assert "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1" in truth
    assert "deferred_work_recovery_register_v1.json" in truth
    assert "TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false" in truth

    runbook = _read(CAPABILITY_RUNBOOK)
    assert "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1" in runbook
    assert "deferred_work_recovery_register_v1.json" in runbook
    assert "MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0" in runbook


def test_no_productive_top5_claims_in_capability_surfaces() -> None:
    register = load_register()
    assert register["semantic_guards"]["TOP5_PRODUCTIVE"] is False
    assert "Top-5 Rotation exists productively" in register["forbidden_claims"]

    prose = [
        _read(HUMAN_COMPANION_PATH),
        _read(CAPABILITY_SPEC),
        _read(REMINDER_PATH),
    ]
    assert_no_productive_top5_claims(*prose)
    for text in prose:
        assert "TOP5_PRODUCTIVE=true" not in text
        assert "Top-5 is productive" not in text.lower()
        # Affirmative productive claim must not appear outside denylist context.
        assert "Top-5 Rotation exists productively." not in text


def test_validate_register_rejects_authorized_implementation() -> None:
    register = load_register()
    entry = get_entry(register, ROTATION_CAPABILITY_ID)
    entry["IMPLEMENTATION_AUTHORIZED"] = True
    with pytest.raises(DeferredWorkRecoveryRegisterError, match="IMPLEMENTATION_AUTHORIZED"):
        validate_register(register)
