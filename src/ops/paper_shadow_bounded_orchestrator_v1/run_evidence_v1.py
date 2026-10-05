"""Bounded Run-001 evidence accumulator (composition-only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunEvidenceAccumulatorV1:
    run_id: str
    fixpoint_sha: str
    fixpoint_tree: str
    settings_digest: str
    authorization_binding: dict[str, Any] = field(default_factory=dict)
    start_wall_unix: float = 0.0
    end_wall_unix: float = 0.0
    elapsed_seconds: float = 0.0
    stop_reason: str = ""
    observation_count: int = 0
    cycle_count: int = 0
    simulated_execution_count: int = 0
    natural_enter_count: int = 0
    long_count: int = 0
    short_count: int = 0
    pre_external_count: int = 0
    shadow_continuation_count: int = 0
    reconciliation_ok_count: int = 0
    duplicate_prevented_count: int = 0
    decision_outcomes: dict[str, int] = field(default_factory=dict)
    real_post_count: int = 0
    testnet_post_count: int = 0
    wire_send_count: int = 0
    external_effect_count: int = 0
    cycle_samples: list[dict[str, Any]] = field(default_factory=list)
    shadow_samples: list[dict[str, Any]] = field(default_factory=list)

    def record_productive_cycle(self, *, bridge_cycle: dict[str, Any] | None) -> None:
        if bridge_cycle is None:
            return
        outcome = str(bridge_cycle.get("decision_outcome") or "")
        self.decision_outcomes[outcome] = int(self.decision_outcomes.get(outcome, 0)) + 1
        if outcome in {"enter_long", "enter_short"}:
            self.natural_enter_count += 1
        side = str(bridge_cycle.get("selected_side") or "").lower()
        if side == "long":
            self.long_count += 1
        elif side == "short":
            self.short_count += 1
        if len(self.cycle_samples) < 50:
            sample: dict[str, Any] = {
                "cycle_id": bridge_cycle.get("cycle_id"),
                "decision_outcome": outcome,
                "selected_side": bridge_cycle.get("selected_side"),
            }
            # Passive observability only — values already computed in bridge_cycle.
            for key in (
                "reason_codes",
                "feature_blockers",
                "required_window_complete",
                "regime_id",
                "direction",
            ):
                if key in bridge_cycle:
                    sample[key] = bridge_cycle.get(key)
            self.cycle_samples.append(sample)

    def record_pre_external(self) -> None:
        self.pre_external_count += 1

    def record_shadow(self, *, sample: dict[str, Any], reconcile_ok: bool) -> None:
        self.shadow_continuation_count += 1
        if reconcile_ok:
            self.reconciliation_ok_count += 1
        if len(self.shadow_samples) < 50:
            self.shadow_samples.append(sample)

    def finalize(self, *, stop_reason: str, elapsed: float, end_wall: float) -> dict[str, Any]:
        self.stop_reason = stop_reason
        self.elapsed_seconds = elapsed
        self.end_wall_unix = end_wall
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "RUN_ID": self.run_id,
            "FIXPOINT_SHA": self.fixpoint_sha,
            "FIXPOINT_TREE": self.fixpoint_tree,
            "SETTINGS_DIGEST": self.settings_digest,
            "authorization_binding": dict(self.authorization_binding),
            "start_wall_unix": self.start_wall_unix,
            "end_wall_unix": self.end_wall_unix,
            "elapsed_seconds": self.elapsed_seconds,
            "stop_reason": self.stop_reason,
            "observation_count": self.observation_count,
            "cycle_count": self.cycle_count,
            "simulated_execution_count": self.simulated_execution_count,
            "natural_enter_count": self.natural_enter_count,
            "long_count": self.long_count,
            "short_count": self.short_count,
            "pre_external_count": self.pre_external_count,
            "shadow_continuation_count": self.shadow_continuation_count,
            "reconciliation_ok_count": self.reconciliation_ok_count,
            "duplicate_prevented_count": self.duplicate_prevented_count,
            "decision_distribution": dict(self.decision_outcomes),
            "REAL_POST_COUNT": self.real_post_count,
            "TESTNET_POST_COUNT": self.testnet_post_count,
            "WIRE_SEND_COUNT": self.wire_send_count,
            "EXTERNAL_EFFECT_COUNT": self.external_effect_count,
            "cycle_samples": list(self.cycle_samples),
            "shadow_samples": list(self.shadow_samples),
            "AUTO_RESTART": False,
        }
