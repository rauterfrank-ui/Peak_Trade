"""Optional DDO learning capture join for CURRENT productive Master-V2 cycle.

Observation-only: binds ``DdoCaptureBindingV0`` around integrated offline replay
and invokes ``record_productive_cycle_capture_v0`` after the authoritative replay.
Does not change replay decisions. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import asdict
import hashlib
import json
from typing import Any

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    bind_host_cycle_capture_context_v0,
    record_productive_cycle_capture_v0,
    reset_capture_session_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)

assert CAPTURE_FAILURE_CHANGES_DECISION is False


def productive_scope_learning_config_hash_v1(bind_input: IntegratedOfflineReplayInputV1) -> str:
    """Versioned replay configuration identity; never includes cycle market values.

    Legacy bounded comparisons and raw GGE learning pools cannot share identity.
    State ownership (sealed L1-L10 vs ordinary trailing) is also explicit.
    """
    from trading.master_v2.canonical_scope_initialization_v1 import (
        scope_initialization_policy_uses_instrument_relative_magnitude_v1,
        snapshot_uses_instrument_relative_scope_magnitude_v1,
    )

    raw = (
        snapshot_uses_instrument_relative_scope_magnitude_v1(bind_input.existing_scope)
        if bind_input.existing_scope is not None
        else scope_initialization_policy_uses_instrument_relative_magnitude_v1(
            bind_input.policies.scope_initialization
        )
    )
    payload = {
        "contract": "scope_learning_configuration_v3_gge_only",
        "instrument_id": bind_input.instrument_id,
        "market_type": str(bind_input.canonical_market_context.market_type.value),
        "distance_mode": (
            "sealed_explicit_dt_v1"
            if bind_input.layered_core_authority_seal is not None
            else "gge_raw_v2"
            if raw
            else "legacy_bounded_v1"
        ),
        "distance_owner": (
            "sealed_layered_core"
            if bind_input.layered_core_authority_seal is not None
            else "integrated_trailing"
        ),
        "declared_config_digest": bind_input.config_digest,
        "policies": asdict(bind_input.policies),
        "effective_scope_policy": (
            {
                "version": bind_input.existing_scope.policy_version,
                "min_band": bind_input.existing_scope.min_scope_band,
                "max_band": bind_input.existing_scope.max_scope_band,
            }
            if bind_input.existing_scope is not None
            else {
                "version": bind_input.policies.scope_initialization.policy_version,
                "min_band": bind_input.policies.scope_initialization.min_scope_band,
                "max_band": bind_input.policies.scope_initialization.max_scope_band,
            }
        ),
        "dynamic_rules": (
            asdict(bind_input.dynamic_scope_rules)
            if bind_input.dynamic_scope_rules is not None
            else None
        ),
    }
    if payload["dynamic_rules"] is not None:
        # Resolved volatility is market evidence, not a new config each cycle.
        payload["dynamic_rules"].pop("volatility_estimate", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False
        ).encode()
    ).hexdigest()


def build_productive_ddo_capture_binding_v1(*, ledger_path: Path) -> DdoCaptureBindingV0:
    # The ledger owner creates its parent during append. Creating it here
    # would let an observation-only I/O failure abort the authoritative replay
    # before capture's existing fail-open durability handling can classify it.
    return DdoCaptureBindingV0(enabled=True, ledger_path=ledger_path)


def run_integrated_offline_replay_with_productive_ddo_capture_v1(
    bind_input: IntegratedOfflineReplayInputV1,
    *,
    ddo_capture_binding: DdoCaptureBindingV0 | None,
    repository_sha: str,
    session_id: str,
    cycle_index: int,
    event_ts_unix: float,
    observation_acceptance_result: Any,
    features: Any,
    confirmation_binding: Any,
) -> tuple[IntegratedOfflineReplayResultV1, dict[str, Any] | None]:
    """Run replay; when binding is enabled, observe producer results fail-open."""
    capture_token = None
    context_error = None
    if ddo_capture_binding is not None and ddo_capture_binding.enabled:
        # Establish identity before decorated producers observe the replay.
        # Clear a reused binding first so a failed clock conversion cannot
        # attribute this cycle to the previous one.
        ddo_capture_binding.capture_event_time_utc = None
        ddo_capture_binding.capture_correlation_id = None
        ddo_capture_binding.capture_cycle_id = None
        ddo_capture_binding.capture_repository_sha = repository_sha
        ddo_capture_binding.capture_scope_config_hash = None
        try:
            bind_host_cycle_capture_context_v0(
                ddo_capture_binding,
                event_ts_unix=event_ts_unix,
                session_id=session_id,
                cycle_index=cycle_index,
                repository_sha=repository_sha,
            )
        except (ValueError, TypeError, OverflowError, OSError) as exc:
            context_error = f"host_cycle_capture:{type(exc).__name__}"
            ddo_capture_binding.last_error = context_error
        try:
            ddo_capture_binding.capture_scope_config_hash = (
                productive_scope_learning_config_hash_v1(bind_input)
            )
        except (ValueError, TypeError, AttributeError) as exc:
            # Observation failure cannot authorize/block/rewrite the replay.
            ddo_capture_binding.last_error = f"scope_config_capture:{type(exc).__name__}"
            ddo_capture_binding.capture_scope_config_hash = "UNKNOWN"
        capture_token = bind_capture_session_v0(
            ddo_capture_binding if context_error is None else DdoCaptureBindingV0(enabled=False)
        )
    try:
        replay = run_integrated_offline_trading_logic_replay_v1(bind_input)
    finally:
        if capture_token is not None:
            reset_capture_session_v0(capture_token)

    scope_capture_binding: Any = None
    intermediate = getattr(replay, "intermediate", None)
    if intermediate is not None:
        scope_capture_binding = getattr(intermediate, "scope_event", None)

    summary: dict[str, Any] | None = None
    if context_error is not None:
        summary = {"ok": False, "skipped": True, "error": context_error}
        ddo_capture_binding.last_result = summary
        return replay, summary
    if ddo_capture_binding is not None and ddo_capture_binding.enabled:
        summary = dict(
            record_productive_cycle_capture_v0(
                ddo_capture_binding,
                repository_sha=repository_sha,
                session_id=session_id,
                cycle_index=cycle_index,
                event_ts_unix=event_ts_unix,
                observation_acceptance_result=observation_acceptance_result,
                features=features,
                replay=replay,
                confirmation_binding=confirmation_binding,
                dynamic_scope_binding=scope_capture_binding,
            )
        )
    return replay, summary
