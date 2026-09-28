"""Owner-GO consume/evidence for bounded productive continuous run + Fresh-C1 GET wiring.

Does not POST, mint permits, or access credentials. Module pins remain unchanged.

RUNTIME_AUTHORIZATION_EFFECT=OWNER_GO_EVIDENCE_AND_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    RUNTIME_OWNER_GO,
    RUNTIME_OWNER_GO_STATUS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    S4A_FRESH_C1_GET_OWNER_GO,
    S4A_FRESH_C1_GET_OWNER_GO_STATUS,
)

WORKPACKAGE_ID: Final[str] = (
    "CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json"
)
CONTINUOUS_RUN_CONSUME_FILENAME: Final[str] = "bounded_continuous_run_owner_go_consume_v1.json"
FRESH_C1_GET_LEDGER_FILENAME: Final[str] = "fresh_c1_get_owner_go_consumptions_v1.jsonl"

_REPO_ROOT = Path(__file__).resolve().parents[3]


class BoundedContinuousRunOwnerGoWiringError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_bounded_continuous_run_owner_go_decision_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = root / DECISION_CONFIG
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def validate_bounded_continuous_run_owner_go_decision_v1(
    *,
    repo_root: Path | None = None,
    baseline_origin_main_sha: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Fail-closed: decision record must grant both scoped Owner-GO tokens."""
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    decision = load_bounded_continuous_run_owner_go_decision_v1(repo_root=root)
    if not decision:
        return False, ("OWNER_GO_DECISION_MISSING",)
    if decision.get("owner_go") is not True:
        reasons.append("OWNER_GO_NOT_GRANTED")
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        reasons.append("WORKPACKAGE_ID_MISMATCH")
    if baseline_origin_main_sha:
        bound = str(decision.get("baseline_origin_main_sha") or "")
        if bound != baseline_origin_main_sha:
            reasons.append("BASELINE_SHA_MISMATCH")
    tokens = decision.get("owner_go_tokens")
    if not isinstance(tokens, list):
        reasons.append("OWNER_GO_TOKENS_MISSING")
    else:
        expected = {RUNTIME_OWNER_GO, S4A_FRESH_C1_GET_OWNER_GO}
        if set(str(t) for t in tokens) != expected:
            reasons.append("OWNER_GO_TOKENS_MISMATCH")
    if decision.get("continuous_run_owner_go") != RUNTIME_OWNER_GO:
        reasons.append("CONTINUOUS_RUN_OWNER_GO_MISMATCH")
    if decision.get("fresh_c1_get_owner_go") != S4A_FRESH_C1_GET_OWNER_GO:
        reasons.append("FRESH_C1_GET_OWNER_GO_MISMATCH")
    for key in (
        "external_effect_authorized",
        "post_allowed",
        "credential_access_authorized",
        "permit_mint_authorized",
        "continuous_run_authorized_module_pin_mutation",
    ):
        if decision.get(key) is True:
            reasons.append(f"FORBIDDEN_IMPLICATION_{key.upper()}")
    return (not reasons, tuple(reasons))


def assert_module_pins_unchanged_v1() -> None:
    if RUNTIME_OWNER_GO_STATUS != "DEFINED_NOT_CONSUMED":
        raise BoundedContinuousRunOwnerGoWiringError("RUNTIME_OWNER_GO_STATUS_MODULE_PIN_DRIFT")
    if S4A_FRESH_C1_GET_OWNER_GO_STATUS != "DEFINED_NOT_CONSUMED":
        raise BoundedContinuousRunOwnerGoWiringError(
            "FRESH_C1_GET_OWNER_GO_STATUS_MODULE_PIN_DRIFT"
        )


def persist_bounded_continuous_run_owner_go_consume_v1(
    *,
    evidence_root: Path,
    run_id: str,
    baseline_origin_main_sha: str,
    binding_digest: str,
) -> dict[str, Any]:
    """Session-scoped consume evidence for RUNTIME_OWNER_GO (not a module pin flip)."""
    assert_module_pins_unchanged_v1()
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        baseline_origin_main_sha=baseline_origin_main_sha,
    )
    if not ok:
        raise BoundedContinuousRunOwnerGoWiringError("OWNER_GO_DECISION_INVALID", ",".join(reasons))
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CONTINUOUS_RUN_CONSUME_FILENAME
    if path.is_file():
        raise BoundedContinuousRunOwnerGoWiringError("CONTINUOUS_RUN_OWNER_GO_ALREADY_CONSUMED")
    record = {
        "consumed": True,
        "owner_go_token": RUNTIME_OWNER_GO,
        "module_pin_status_after": RUNTIME_OWNER_GO_STATUS,
        "run_id": str(run_id),
        "binding_digest": str(binding_digest),
        "baseline_origin_main_sha": str(baseline_origin_main_sha),
        "consumed_at_utc": _utc_now_iso_v1(),
        "external_effect_authorized": False,
        "post_allowed": False,
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def append_fresh_c1_get_owner_go_consumption_v1(
    *,
    evidence_root: Path,
    run_id: str,
    poll_index: int,
    endpoint: str,
    get_performed: bool,
) -> dict[str, Any]:
    """Per-poll Fresh-C1 GET consume ledger line (public readonly only)."""
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1()
    if not ok:
        raise BoundedContinuousRunOwnerGoWiringError(
            "FRESH_C1_GET_OWNER_GO_DECISION_INVALID", ",".join(reasons)
        )
    row = {
        "owner_go_token": S4A_FRESH_C1_GET_OWNER_GO,
        "module_pin_status": S4A_FRESH_C1_GET_OWNER_GO_STATUS,
        "run_id": str(run_id),
        "poll_index": int(poll_index),
        "endpoint": str(endpoint),
        "get_performed": bool(get_performed),
        "auth_required": False,
        "consumed_at_utc": _utc_now_iso_v1(),
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    ledger = root / FRESH_C1_GET_LEDGER_FILENAME
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    return row


def owner_go_consumption_semantics_v1() -> dict[str, str]:
    return {
        "continuous_run_owner_go": RUNTIME_OWNER_GO,
        "continuous_run_module_pin": RUNTIME_OWNER_GO_STATUS,
        "fresh_c1_get_owner_go": S4A_FRESH_C1_GET_OWNER_GO,
        "fresh_c1_get_module_pin": S4A_FRESH_C1_GET_OWNER_GO_STATUS,
        "consume_effect": "EVIDENCE_BOUND_SESSION_AND_PER_POLL_GET_LEDGER",
        "module_pins_mutated": "false",
    }


__all__ = [
    "DECISION_CONFIG",
    "WORKPACKAGE_ID",
    "BoundedContinuousRunOwnerGoWiringError",
    "append_fresh_c1_get_owner_go_consumption_v1",
    "assert_module_pins_unchanged_v1",
    "load_bounded_continuous_run_owner_go_decision_v1",
    "owner_go_consumption_semantics_v1",
    "persist_bounded_continuous_run_owner_go_consume_v1",
    "validate_bounded_continuous_run_owner_go_decision_v1",
]
