"""Models and digest helpers for multi-session typed-vol evidence v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class MultiSessionTypedVolEvidenceError(ValueError):
    """Fail-closed capability error (never carries confirm-token material)."""


def sha256_hex_canonical(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AlphaComponentSnapshotV1:
    """Read-only alpha component outcomes for one injected-volatility evaluation."""

    directional_assessment: str
    survival: str
    suitability: str
    composition: str
    switch_state: str
    entry_permission: str
    entry_outcome: str
    hold_reduce_exit: str
    final_outcome: str
    evaluation_digest: str
    order_intents: tuple[str, ...] = ()
    state_mutations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "composition": self.composition,
            "directional_assessment": self.directional_assessment,
            "entry_outcome": self.entry_outcome,
            "entry_permission": self.entry_permission,
            "evaluation_digest": self.evaluation_digest,
            "final_outcome": self.final_outcome,
            "hold_reduce_exit": self.hold_reduce_exit,
            "order_intents": list(self.order_intents),
            "state_mutations": list(self.state_mutations),
            "suitability": self.suitability,
            "survival": self.survival,
            "switch_state": self.switch_state,
        }


COMPONENT_ORDER: tuple[str, ...] = (
    "directional_assessment",
    "survival",
    "suitability",
    "composition",
    "switch_state",
    "entry_permission",
    "entry_outcome",
    "hold_reduce_exit",
    "final_outcome",
)


def classify_first_divergence_v1(
    aged: AlphaComponentSnapshotV1,
    fresh: AlphaComponentSnapshotV1,
) -> tuple[str, str]:
    """Return (classification, first_divergence_component)."""
    a = aged.to_dict()
    f = fresh.to_dict()
    for key in COMPONENT_ORDER:
        if a.get(key) != f.get(key):
            mapping = {
                "directional_assessment": "DIRECTIONAL_ASSESSMENT_CHANGE",
                "survival": "SURVIVAL_CHANGE",
                "suitability": "SUITABILITY_CHANGE",
                "composition": "COMPOSITION_CHANGE",
                "switch_state": "SWITCH_STATE_CHANGE",
                "entry_permission": "ENTRY_PERMISSION_CHANGE",
                "entry_outcome": "ENTRY_OUTCOME_CHANGE",
                "hold_reduce_exit": "HOLD_REDUCE_EXIT_CHANGE",
                "final_outcome": "ENTRY_OUTCOME_CHANGE",
            }
            return mapping[key], key
    return "NO_DECISION_CHANGE", "NONE"
