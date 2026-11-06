"""Full-Core atomic one-shot Owner-GO consumption (reuses canary durable implementation).

Extended immutable payload binding includes decision + envelope + venue plan digests.
Does not authorize POST. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    CanaryAuthorizationBindingV1,
    CanaryAtomicAuthorizationStateV1,
    CanaryAtomicOneShotError,
    STATE_AVAILABLE,
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_SUBMITTED_ACKNOWLEDGED,
    STATE_TERMINAL_RECONCILED,
    atomic_mark_halted_unresolved_v1,
    atomic_mark_reconciliation_pending_v1,
    atomic_mark_submit_boundary_v1,
    atomic_mark_submitted_acknowledged_v1,
    atomic_mark_terminal_reconciled_v1,
    atomic_mark_unknown_submit_v1,
    atomic_reserve_owner_go_authorization_v1,
    assert_atomic_entry_authorization_available_v1,
    durable_entry_state_for_guard_v1,
    load_atomic_authorization_state_v1,
)

CONTRACT_ID = "FULL_CORE_CAPITAL_GUARD_ATOMIC_ONE_SHOT_V1"
DEFAULT_STATE_DIR_REL = "evidence/ops/full_core_capital_guard_atomic_one_shot_v1/states"


class FullCoreAtomicOneShotError(RuntimeError):
    """Fail-closed Full-Core atomic one-shot violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class FullCoreAuthorizationBindingV1:
    owner_go: str
    origin_main_sha: str
    account_scope: str
    environment: str
    execution_mode: str
    canonical_decision_id: str
    instrument_id: str
    native_id: str
    selected_direction: str
    order_side: str
    final_quantity: str
    order_type: str
    order_price: str
    venue_plan_digest: str
    envelope_digest: str
    guard_config_digest: str
    session_id: str
    clordid: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go": self.owner_go,
            "origin_main_sha": self.origin_main_sha,
            "account_scope": self.account_scope,
            "environment": self.environment,
            "execution_mode": self.execution_mode,
            "canonical_decision_id": self.canonical_decision_id,
            "instrument_id": self.instrument_id,
            "native_id": self.native_id,
            "selected_direction": self.selected_direction,
            "order_side": self.order_side,
            "final_quantity": self.final_quantity,
            "order_type": self.order_type,
            "order_price": self.order_price,
            "venue_plan_digest": self.venue_plan_digest,
            "envelope_digest": self.envelope_digest,
            "guard_config_digest": self.guard_config_digest,
            "session_id": self.session_id,
            "clordid": self.clordid,
            "contract_id": CONTRACT_ID,
        }

    def consumption_key(self) -> str:
        material = _canonical_json(
            {
                "owner_go": self.owner_go.strip(),
                "origin_main_sha": self.origin_main_sha.strip().lower(),
                "account_scope": self.account_scope.strip(),
                "environment": self.environment.strip().upper(),
            }
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def binding_digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()

    def to_canary_atomic_binding_v1(self) -> CanaryAuthorizationBindingV1:
        return CanaryAuthorizationBindingV1(
            owner_go=self.owner_go,
            origin_main_sha=self.origin_main_sha,
            account_scope=self.account_scope,
            environment=self.environment,
            instrument_id=self.instrument_id,
            plan_digest=self.binding_digest(),
            guard_config_digest=self.guard_config_digest,
            session_id=self.session_id,
            clordid=self.clordid,
        )


def default_full_core_atomic_state_dir_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    return root / DEFAULT_STATE_DIR_REL


def assert_full_core_entry_authorization_available_v1(
    *,
    state_dir: Path,
    binding: FullCoreAuthorizationBindingV1,
) -> None:
    try:
        assert_atomic_entry_authorization_available_v1(
            state_dir=state_dir,
            binding=binding.to_canary_atomic_binding_v1(),
        )
    except CanaryAtomicOneShotError as exc:
        raise FullCoreAtomicOneShotError(str(exc)) from exc


def full_core_atomic_reserve_owner_go_authorization_v1(
    *,
    state_dir: Path,
    binding: FullCoreAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    try:
        return atomic_reserve_owner_go_authorization_v1(
            state_dir=state_dir,
            binding=binding.to_canary_atomic_binding_v1(),
        )
    except CanaryAtomicOneShotError as exc:
        raise FullCoreAtomicOneShotError(str(exc)) from exc


def full_core_atomic_mark_submit_boundary_v1(
    *,
    state_dir: Path,
    binding: FullCoreAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    try:
        return atomic_mark_submit_boundary_v1(
            state_dir=state_dir,
            binding=binding.to_canary_atomic_binding_v1(),
        )
    except CanaryAtomicOneShotError as exc:
        raise FullCoreAtomicOneShotError(str(exc)) from exc


def full_core_durable_entry_state_for_guard_v1(
    *,
    state_dir: Path,
    consumption_key: str,
) -> str:
    return durable_entry_state_for_guard_v1(state_dir=state_dir, consumption_key=consumption_key)


def load_full_core_atomic_authorization_state_v1(
    *,
    state_dir: Path,
    consumption_key: str,
) -> CanaryAtomicAuthorizationStateV1 | None:
    return load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=consumption_key)


__all__ = [
    "CONTRACT_ID",
    "FullCoreAtomicOneShotError",
    "FullCoreAuthorizationBindingV1",
    "STATE_AVAILABLE",
    "STATE_HALTED_UNRESOLVED",
    "STATE_RECONCILIATION_PENDING",
    "STATE_RESERVED_PRE_POST",
    "STATE_SUBMIT_MAY_HAVE_OCCURRED",
    "STATE_SUBMITTED_ACKNOWLEDGED",
    "STATE_TERMINAL_RECONCILED",
    "assert_full_core_entry_authorization_available_v1",
    "default_full_core_atomic_state_dir_v1",
    "full_core_atomic_mark_submit_boundary_v1",
    "full_core_atomic_reserve_owner_go_authorization_v1",
    "full_core_durable_entry_state_for_guard_v1",
    "load_full_core_atomic_authorization_state_v1",
    "atomic_mark_halted_unresolved_v1",
    "atomic_mark_reconciliation_pending_v1",
    "atomic_mark_submitted_acknowledged_v1",
    "atomic_mark_terminal_reconciled_v1",
    "atomic_mark_unknown_submit_v1",
]
