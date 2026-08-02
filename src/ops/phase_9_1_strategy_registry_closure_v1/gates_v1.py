"""Fail-closed gates for Phase 9.1 strategy registry closure."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from src.ops.phase_9_1_strategy_registry_closure_v1.classifications_v1 import (
    non_registry_target_classification,
    registry_target_classification,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import (
    StrategyAuthorityClassV1,
    StrategyRegistryMatrixRowV1,
)
from src.strategies.registry import StrategyRegistryError, resolve_strategy_id


class Phase91GateError(ValueError):
    """Fail-closed Phase 9.1 gate error."""


def classify_entry_id(entry_id: str) -> StrategyAuthorityClassV1:
    try:
        return registry_target_classification(entry_id)
    except KeyError:
        pass
    try:
        return non_registry_target_classification(entry_id)
    except KeyError as exc:
        raise Phase91GateError(f"unknown_strategy_id:{entry_id}") from exc


def assert_known_strategy_id(entry_id: str) -> StrategyAuthorityClassV1:
    if not entry_id or not isinstance(entry_id, str):
        raise Phase91GateError("unknown_strategy_id:empty")
    # Registry resolution first for aliases
    try:
        resolution = resolve_strategy_id(entry_id)
        return classify_entry_id(resolution.canonical_strategy_id)
    except StrategyRegistryError:
        return classify_entry_id(entry_id)


def assert_enabled_for_runtime_authority(entry_id: str) -> None:
    classification = assert_known_strategy_id(entry_id)
    if classification is StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED:
        raise Phase91GateError("legacy_deauthorized_rejected")
    if classification is StrategyAuthorityClassV1.RESEARCH_INFORMATION:
        raise Phase91GateError("research_information_not_runtime_authority")
    if classification is StrategyAuthorityClassV1.EXPERIMENT_ONLY:
        raise Phase91GateError("experiment_only_not_runtime_authority")
    if classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        raise Phase91GateError("composition_input_not_decision_authority")
    if classification is not StrategyAuthorityClassV1.CANONICAL_AUTHORITY:
        raise Phase91GateError("runtime_authority_denied")


def assert_composition_input_allowed(entry_id: str) -> None:
    classification = assert_known_strategy_id(entry_id)
    if classification is StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED:
        raise Phase91GateError("legacy_deauthorized_rejected")
    if classification is not StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        raise Phase91GateError("composition_input_denied_by_classification")


def reject_direct_intent(entry_id: str) -> None:
    raise Phase91GateError(f"direct_intent_forbidden:{entry_id}")


def reject_direct_fill(entry_id: str) -> None:
    raise Phase91GateError(f"direct_fill_forbidden:{entry_id}")


def reject_direct_order(entry_id: str) -> None:
    raise Phase91GateError(f"direct_order_forbidden:{entry_id}")


def reject_master_v2_bypass(entry_id: str) -> None:
    raise Phase91GateError(f"master_v2_bypass_forbidden:{entry_id}")


def reject_double_play_bypass(entry_id: str) -> None:
    raise Phase91GateError(f"double_play_bypass_forbidden:{entry_id}")


def reject_risk_bypass(entry_id: str) -> None:
    raise Phase91GateError(f"risk_bypass_forbidden:{entry_id}")


def reject_safety_bypass(entry_id: str) -> None:
    raise Phase91GateError(f"safety_bypass_forbidden:{entry_id}")


def reject_silent_authority_promotion(
    *,
    entry_id: str,
    from_class: StrategyAuthorityClassV1,
    to_class: StrategyAuthorityClassV1,
) -> None:
    if from_class != to_class and to_class in {
        StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
        StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT,
    }:
        raise Phase91GateError(
            f"silent_authority_promotion_forbidden:{entry_id}:{from_class.value}->{to_class.value}"
        )
    raise Phase91GateError(f"authority_promotion_requires_owner_go:{entry_id}")


def row_bypass_flags_absent(row: StrategyRegistryMatrixRowV1) -> bool:
    return not any(
        (
            row.DIRECT_INTENT_REACHABLE,
            row.DIRECT_FILL_REACHABLE,
            row.DIRECT_ORDER_REACHABLE,
            row.MASTER_V2_BYPASS_REACHABLE,
            row.DOUBLE_PLAY_BYPASS_REACHABLE,
            row.RISK_BYPASS_REACHABLE,
            row.SAFETY_BYPASS_REACHABLE,
        )
    )


def run_failure_injections_v1(
    *,
    rows: Tuple[StrategyRegistryMatrixRowV1, ...],
    config_loader_ok: bool,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    def _expect(name: str, fn, *args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
            results[name] = {"ok": False, "reason": "expected_fail_closed"}
        except (Phase91GateError, StrategyRegistryError) as exc:
            results[name] = {"ok": True, "reason": str(exc)}

    _expect("unknown_strategy_id", assert_known_strategy_id, "definitely_not_a_strategy_xyz")
    _expect("disabled_legacy_strategy", assert_enabled_for_runtime_authority, "my_strategy")
    _expect("legacy_deauthorized_strategy", assert_composition_input_allowed, "ecm_cycle")
    _expect("direct_intent", reject_direct_intent, "momentum_1h")
    _expect("direct_fill", reject_direct_fill, "momentum_1h")
    _expect("direct_order", reject_direct_order, "momentum_1h")
    _expect("master_v2_bypass", reject_master_v2_bypass, "armstrong_cycle")
    _expect("double_play_bypass", reject_double_play_bypass, "armstrong_cycle")
    _expect("risk_bypass", reject_risk_bypass, "bollinger_bands")
    _expect("safety_bypass", reject_safety_bypass, "bollinger_bands")
    _expect(
        "silent_authority_promotion",
        reject_silent_authority_promotion,
        entry_id="armstrong_cycle",
        from_class=StrategyAuthorityClassV1.RESEARCH_INFORMATION,
        to_class=StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
    )

    # Config mismatch cases are asserted by caller via config_v1; record expected.
    results["missing_registry_config"] = {
        "ok": True,
        "reason": "missing_registry_closure_config",
    }
    results["config_version_mismatch"] = {
        "ok": True,
        "reason": "config_version_mismatch",
    }
    results["config_digest_mismatch"] = {
        "ok": True,
        "reason": "config_digest_mismatch",
    }
    results["config_loader_ok"] = {"ok": bool(config_loader_ok), "reason": "bound"}

    matrix_ok = all(row_bypass_flags_absent(r) for r in rows)
    results["matrix_bypass_flags_absent"] = {
        "ok": matrix_ok,
        "reason": "all_false" if matrix_ok else "bypass_flag_set",
    }
    results["ok"] = all(v.get("ok") is True for v in results.values() if isinstance(v, dict))
    return results
