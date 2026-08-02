"""DEFERRED_WORK_RECOVERY_REGISTER_V1 — Capability 0.4 register owner.

Governance recovery surface only. Loads and validates the canonical
Deferred-Work Recovery Register. Does not authorize implementation,
activation, multi-future runtime, ranking/selection changes, live trading,
network sessions, or authorization consumption.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

CAPABILITY_RECOVERY_ID = (
    "CAPABILITY_0_4_DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1"
)
REGISTER_ID = "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1"
SCHEMA_VERSION = "deferred_work_recovery_register.v1"
PRODUCER_FAMILY = "ops.deferred_work_recovery_register_contract_v1"
OWNER = PRODUCER_FAMILY
ROTATION_CAPABILITY_ID = "MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0"
CLASSIFICATION_DEFERRED_REQUIRED = "DEFERRED_REQUIRED_CAPABILITY"
TARGET_PHASE_6 = "PHASE_6"

IMPLEMENTATION_AUTHORIZED = False
ACTIVATION_AUTHORIZED = False
CORE_LOGIC_CHANGE_ALLOWED = False
CURRENT_RUNTIME_CHANGED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MAX_POSITIONS_EFFECTIVE = 1
PHASE_1_SELECTION = "SINGLE_SELECTED_FUTURE"
PHASE_1_MAX_POSITIONS = 1

REQUIRED_ENTRY_FIELDS: frozenset[str] = frozenset(
    {
        "CAPABILITY_ID",
        "TITLE",
        "CLASSIFICATION",
        "OWNER_REQUIREMENT",
        "TRADING_PATH_VALUE",
        "CURRENT_STATE",
        "TARGET_STATE",
        "DEFERRED_REASON",
        "BLOCKING_DEPENDENCIES",
        "DEPENDENCY_STATUS",
        "AUTHORITY_OWNER",
        "TARGET_PHASE",
        "REVIEW_TRIGGER",
        "REVIEW_DATE_OR_EVENT",
        "EXPIRY_OR_REASSESSMENT_RULE",
        "IMPLEMENTATION_AUTHORIZED",
        "ACTIVATION_AUTHORIZED",
        "CORE_LOGIC_CHANGE_ALLOWED",
        "CURRENT_RUNTIME_EFFECT",
        "EXPECTED_FUTURE_RUNTIME_EFFECT",
        "SAFETY_INVARIANTS",
        "SOURCE_REFERENCES",
        "REPOSITORY_SHA",
        "LAST_VERIFIED_AT",
        "CURRENT_STATUS",
        "NEXT_REQUIRED_DECISION",
        "CLOSURE_CRITERIA",
    }
)

REQUIRED_BLOCKING_DEPENDENCIES: frozenset[str] = frozenset(
    {
        "Productive Reconciliation Runtime Closure",
        "Governed Futures Universe Authority",
        "Productive Ranking Authority",
        "Single Selected Future Persistence",
        "Single Selected Future Restart Recovery",
        "Futures Accounting Runtime Closure",
        "Per-Instrument State Isolation Design",
        "Global Portfolio Risk Design",
        "Global Safety Arbitration",
        "Single Global Execution Writer",
        "Canonical Runtime Pre-Activation Closure",
    }
)

REQUIRED_REVIEW_CLOSURES: frozenset[str] = frozenset(
    {
        "Productive Reconciliation",
        "Single Selected Future Authority and Runtime Binding",
        "Futures Accounting Runtime Wiring",
        "Canonical Runtime Pre-Activation Closure",
    }
)

REQUIRED_SEMANTIC_GUARDS: Mapping[str, Any] = {
    "TOP20_IS_CONTEXT_ONLY": True,
    "SINGLE_SELECTED_FUTURE_IS_CURRENT_AUTHORITY": True,
    "TOP_N_ACTIVE_SET_IS_DEFERRED": True,
    "TOP5_PRODUCTIVE": False,
    "TOP5_REGRESSED": False,
    "MULTI_FUTURE_IMPLEMENTED": False,
    "MULTI_FUTURE_AUTHORIZED": False,
    "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
    "MAX_POSITIONS_EFFECTIVE": 1,
    "PHASE_1_SELECTION": "SINGLE_SELECTED_FUTURE",
    "PHASE_1_MAX_POSITIONS": 1,
    "ROTATION_POLICY_RATIFIED": False,
    "ROTATION_IMPLEMENTATION_STARTED": False,
    "CURRENT_RUNTIME_CHANGED": False,
    "DASHBOARD_RANKING_IS_RUNTIME_AUTHORITY": False,
}

FORBIDDEN_PRODUCTIVE_TOP5_PHRASES: tuple[str, ...] = (
    "Top-5 Rotation exists productively",
    "Top-5 is productive",
    "TOP5_PRODUCTIVE=true",
    "Top-5 Rotation was lost or regressed",
    "Active Set is already authoritative",
    "Multi-Future is ready",
    "Multi-Future is activated",
    "Ranking currently authorizes multiple instruments",
    "Dashboard ranking is Runtime Authority",
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_REGISTER_PATH = (
    _REPO_ROOT / "docs" / "governance" / "deferred_work_recovery_register_v1.json"
)
HUMAN_COMPANION_PATH = (
    _REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md"
)
REMINDER_PATH = (
    _REPO_ROOT
    / "docs"
    / "planning"
    / "deferred"
    / "MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md"
)


class DeferredWorkRecoveryRegisterError(ValueError):
    """Fail-closed deferred-work recovery register violation."""


def load_register(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical deferred-work recovery register JSON."""
    register_path = path or CANONICAL_REGISTER_PATH
    if not register_path.is_file():
        raise DeferredWorkRecoveryRegisterError(
            f"canonical deferred-work register missing: {register_path}"
        )
    raw = json.loads(register_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DeferredWorkRecoveryRegisterError("register root must be object")
    return raw


def get_entry(register: Mapping[str, Any], capability_id: str) -> dict[str, Any]:
    entries = register.get("entries")
    if not isinstance(entries, list):
        raise DeferredWorkRecoveryRegisterError("register.entries must be a list")
    for item in entries:
        if isinstance(item, dict) and item.get("CAPABILITY_ID") == capability_id:
            return item
    raise DeferredWorkRecoveryRegisterError(f"capability not registered: {capability_id}")


def validate_register(register: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate register schema and rotation-policy entry invariants."""
    payload = dict(register) if register is not None else load_register()

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise DeferredWorkRecoveryRegisterError("schema_version mismatch")
    if payload.get("register_id") != REGISTER_ID:
        raise DeferredWorkRecoveryRegisterError("register_id mismatch")
    if payload.get("capability_recovery_id") != CAPABILITY_RECOVERY_ID:
        raise DeferredWorkRecoveryRegisterError("capability_recovery_id mismatch")
    if payload.get("parallel_register_forbidden") is not True:
        raise DeferredWorkRecoveryRegisterError("parallel register must be forbidden")
    if payload.get("implementation_authorized") is not False:
        raise DeferredWorkRecoveryRegisterError("register implementation_authorized must be false")
    if payload.get("activation_authorized") is not False:
        raise DeferredWorkRecoveryRegisterError("register activation_authorized must be false")
    if payload.get("current_runtime_changed") is not False:
        raise DeferredWorkRecoveryRegisterError("current_runtime_changed must be false")

    guards = payload.get("semantic_guards")
    if not isinstance(guards, dict):
        raise DeferredWorkRecoveryRegisterError("semantic_guards missing")
    for key, expected in REQUIRED_SEMANTIC_GUARDS.items():
        if guards.get(key) != expected:
            raise DeferredWorkRecoveryRegisterError(
                f"semantic guard mismatch: {key} expected={expected!r} actual={guards.get(key)!r}"
            )

    entry = get_entry(payload, ROTATION_CAPABILITY_ID)
    missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
    if missing:
        raise DeferredWorkRecoveryRegisterError(
            f"rotation entry missing required fields: {missing}"
        )

    if entry.get("CLASSIFICATION") != CLASSIFICATION_DEFERRED_REQUIRED:
        raise DeferredWorkRecoveryRegisterError("rotation CLASSIFICATION mismatch")
    if entry.get("TARGET_PHASE") != TARGET_PHASE_6:
        raise DeferredWorkRecoveryRegisterError("rotation TARGET_PHASE must be PHASE_6")
    if entry.get("IMPLEMENTATION_AUTHORIZED") is not False:
        raise DeferredWorkRecoveryRegisterError("rotation IMPLEMENTATION_AUTHORIZED must be false")
    if entry.get("ACTIVATION_AUTHORIZED") is not False:
        raise DeferredWorkRecoveryRegisterError("rotation ACTIVATION_AUTHORIZED must be false")
    if entry.get("CORE_LOGIC_CHANGE_ALLOWED") is not False:
        raise DeferredWorkRecoveryRegisterError("rotation CORE_LOGIC_CHANGE_ALLOWED must be false")
    if entry.get("CURRENT_RUNTIME_EFFECT") != "NONE":
        raise DeferredWorkRecoveryRegisterError("CURRENT_RUNTIME_EFFECT must be NONE")
    if entry.get("PHASE_1_SELECTION") != PHASE_1_SELECTION:
        raise DeferredWorkRecoveryRegisterError("PHASE_1_SELECTION must be SINGLE_SELECTED_FUTURE")
    if entry.get("PHASE_1_MAX_POSITIONS") != PHASE_1_MAX_POSITIONS:
        raise DeferredWorkRecoveryRegisterError("PHASE_1_MAX_POSITIONS must be 1")
    if entry.get("MULTI_FUTURE_RUNTIME_AUTHORIZED") is not False:
        raise DeferredWorkRecoveryRegisterError(
            "MULTI_FUTURE_RUNTIME_AUTHORIZED must be false on rotation entry"
        )

    deps = entry.get("BLOCKING_DEPENDENCIES")
    if not isinstance(deps, list):
        raise DeferredWorkRecoveryRegisterError("BLOCKING_DEPENDENCIES must be a list")
    missing_deps = sorted(REQUIRED_BLOCKING_DEPENDENCIES - set(deps))
    if missing_deps:
        raise DeferredWorkRecoveryRegisterError(f"missing blocking dependencies: {missing_deps}")

    trigger = entry.get("REVIEW_TRIGGER")
    if not isinstance(trigger, dict):
        raise DeferredWorkRecoveryRegisterError("REVIEW_TRIGGER must be an object")
    if trigger.get("event_based") is not True:
        raise DeferredWorkRecoveryRegisterError("REVIEW_TRIGGER.event_based must be true")
    if trigger.get("reminder_only") is not False:
        raise DeferredWorkRecoveryRegisterError("REVIEW_TRIGGER.reminder_only must be false")
    closures = trigger.get("required_closures")
    if not isinstance(closures, list):
        raise DeferredWorkRecoveryRegisterError("REVIEW_TRIGGER.required_closures must be a list")
    missing_closures = sorted(REQUIRED_REVIEW_CLOSURES - set(closures))
    if missing_closures:
        raise DeferredWorkRecoveryRegisterError(
            f"missing review trigger closures: {missing_closures}"
        )

    owner_req = str(entry.get("OWNER_REQUIREMENT") or "")
    for token in (
        "dynamically evaluated futures universe",
        "ranking as context",
        "promotion",
        "demotion",
        "hysteresis",
        "open position",
        "global risk",
        "state isolation",
        "restart",
        "Top-N",
        "N=5",
        "neither productive nor activated",
    ):
        if token.lower() not in owner_req.lower():
            raise DeferredWorkRecoveryRegisterError(
                f"OWNER_REQUIREMENT missing required token: {token}"
            )

    trading_path = str(entry.get("TRADING_PATH_VALUE") or "")
    for token in (
        "Universe",
        "Ranking",
        "Active-Set",
        "Master V2",
        "Double Play",
        "Global Risk",
        "Global Safety",
        "Intent Arbitration",
        "Execution",
        "does not alter the current trading path",
    ):
        if token not in trading_path:
            raise DeferredWorkRecoveryRegisterError(
                f"TRADING_PATH_VALUE missing required token: {token}"
            )

    return payload


def assert_no_productive_top5_claims(*texts: str) -> None:
    """Fail closed if any provided text asserts productive/regressed Top-5 rotation.

    Mentions inside an explicit denylist / ``forbidden_claims`` enumeration are
    allowed when they appear only as prohibited examples, not as affirmations.
    """
    for text in texts:
        lowered = text.lower()
        for phrase in FORBIDDEN_PRODUCTIVE_TOP5_PHRASES:
            needle = phrase.lower()
            search_from = 0
            while True:
                idx = lowered.find(needle, search_from)
                if idx < 0:
                    break
                window_start = max(0, idx - 80)
                window = lowered[window_start : idx + len(needle) + 40]
                denylist_context = (
                    "forbidden_claims" in window
                    or "forbidden claim" in window
                    or "must not" in window
                    or "verbot" in window
                    or "prevent" in window
                    or "misverständliche" in window
                    or "denylist" in window
                )
                if not denylist_context:
                    raise DeferredWorkRecoveryRegisterError(
                        f"forbidden productive/regressed Top-5 or multi-future claim: {phrase}"
                    )
                search_from = idx + len(needle)
        if "top5_productive=true" in lowered.replace(" ", ""):
            raise DeferredWorkRecoveryRegisterError("TOP5_PRODUCTIVE=true is forbidden")
