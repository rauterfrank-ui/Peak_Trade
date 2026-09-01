"""Hindsight-leakage guards for offline DDO evaluation v0.

Safety correctness may use only the decision-time information set.
Later economics, later prices, and evaluation-time labels cannot relabel
safety. This module does not confer safety or trading authority.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

HINDSIGHT_LEAKAGE_ALLOWED: Final[bool] = False

FORBIDDEN_SAFETY_RELABEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "kill_switch_correctness",
        "forced_false_positive",
        "forced_false_negative",
        "forced_true_positive",
        "forced_true_negative",
        "safety_score",
        "safety_correctness",
    }
)

_LATER_ECONOMIC_KEYS: Final[frozenset[str]] = frozenset(
    {
        "later_economic_path",
        "later_favorable_price_move",
        "later_pnl",
        "economic_score",
        "actual_outcome_ref",
        "evaluation_time_information_set_ref",
    }
)


def assert_no_hindsight_safety_relabel_v0(payload: Mapping[str, Any] | None) -> None:
    """Reject nested safety-relabel keys on evaluation-time payloads."""
    if payload is None:
        return
    _scan(payload, ancestry=())


def assert_safety_inputs_exclude_later_economics_v0(payload: Mapping[str, Any]) -> None:
    """Fail closed if a safety-input mapping carries later-economic fields."""
    extra = sorted(key for key in payload if key in _LATER_ECONOMIC_KEYS)
    if extra:
        raise DdoValidationError(f"HINDSIGHT_SAFETY_INPUT_CONTAINS_LATER_ECONOMICS:{extra}")
    assert_no_hindsight_safety_relabel_v0(payload)


def _scan(value: Any, *, ancestry: tuple[str, ...]) -> None:
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if not isinstance(key, str):
                raise DdoValidationError("HINDSIGHT_GUARD_KEY_MUST_BE_STRING")
            if key in FORBIDDEN_SAFETY_RELABEL_KEYS:
                raise DdoValidationError(
                    f"HINDSIGHT_CANNOT_RELABEL_SAFETY_CORRECTNESS:{'.'.join((*ancestry, key))}"
                )
            _scan(inner, ancestry=(*ancestry, key))
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _scan(item, ancestry=ancestry)
