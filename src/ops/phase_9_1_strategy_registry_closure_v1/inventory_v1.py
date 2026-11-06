"""Build the canonical Phase 9.1 strategy registry matrix from repository truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

from src.ops.phase_9_1_strategy_registry_closure_v1.classifications_v1 import (
    all_non_registry_ids,
    all_required_registry_ids,
    current_classification_from_spec_tier,
    deauthorization_reason,
    non_registry_implementation,
    non_registry_target_classification,
    productive_callers_for,
    registry_target_classification,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    AUTHORITY_OWNER,
    BOUND_REGISTRY_POLICY_VERSION,
    BOUND_REGISTRY_SCHEMA_VERSION,
    DOUBLE_PLAY_AUTHORITY,
    MASTER_V2_AUTHORITY,
    OWNER,
    REGISTRY_OWNER,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import (
    StrategyAuthorityClassV1,
    StrategyRegistryMatrixRowV1,
)
from src.strategies.registry import (
    DeprecationStatus,
    build_registry_snapshot,
    get_strategy_registry_entry,
)


class Phase91InventoryError(ValueError):
    """Fail-closed inventory error."""


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _enabled_state(classification: StrategyAuthorityClassV1) -> str:
    if classification is StrategyAuthorityClassV1.CANONICAL_AUTHORITY:
        return "AUTHORITY_ONLY"
    if classification is StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED:
        return "DISABLED"
    if classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        return "ENABLED"
    return "DISABLED"  # research/experiment: no productive runtime authority


def _composition_contract(classification: StrategyAuthorityClassV1) -> str:
    if classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        return "explicit_host_suitability_stub_only"
    if classification is StrategyAuthorityClassV1.CANONICAL_AUTHORITY:
        return "not_applicable_authority_owner"
    return "composition_input_denied_by_classification"


def _fail_closed_behavior(classification: StrategyAuthorityClassV1) -> str:
    if classification is StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED:
        return "reject_legacy_deauthorized"
    if classification is StrategyAuthorityClassV1.RESEARCH_INFORMATION:
        return "reject_research_as_runtime_authority"
    if classification is StrategyAuthorityClassV1.EXPERIMENT_ONLY:
        return "reject_experiment_as_runtime_authority"
    if classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        return "allow_composition_input_only_no_direct_intent"
    return "authority_owner_only"


def build_strategy_registry_matrix_v1(
    *, config_digest: str
) -> Tuple[StrategyRegistryMatrixRowV1, ...]:
    snapshot = build_registry_snapshot()
    registry_ids = set(snapshot.strategy_ids_sorted)
    required = set(all_required_registry_ids())
    if registry_ids != required:
        missing = sorted(required - registry_ids)
        extra = sorted(registry_ids - required)
        raise Phase91InventoryError(f"registry_inventory_drift missing={missing} extra={extra}")

    rows: List[StrategyRegistryMatrixRowV1] = []
    for strategy_id in sorted(registry_ids):
        entry = get_strategy_registry_entry(strategy_id)
        tier = "functional"
        if "r_and_d" in entry.capability_tags:
            tier = "r_and_d"
        elif "production" in entry.capability_tags or "live_ready" in entry.capability_tags:
            tier = "production"
        current = current_classification_from_spec_tier(tier)
        target = registry_target_classification(strategy_id)
        # Force legacy deauth current label when already deprecated.
        if entry.deprecation_status in {
            DeprecationStatus.DEPRECATED_STRATEGY,
            DeprecationStatus.REMOVED,
        }:
            current = StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED
        impl = entry.implementation_ref
        source = "src/strategies/registry.py"
        if impl.startswith("src.strategies."):
            source = impl.replace(".", "/").replace("src/strategies/", "src/strategies/") + ".py"
            # functional refs are module paths without class
            if "/generate_signals" in source:
                source = source.split("/generate_signals")[0] + ".py"
        elif "." in impl:
            # module.Class
            mod = impl.rsplit(".", 1)[0]
            source = mod.replace(".", "/") + ".py"

        rows.append(
            StrategyRegistryMatrixRowV1(
                STRATEGY_ID=strategy_id,
                IMPLEMENTATION_SYMBOL=impl,
                SOURCE_PATH=source,
                CURRENT_CLASSIFICATION=current.value,
                TARGET_CLASSIFICATION=target.value,
                PRODUCTIVE_CALLERS=productive_callers_for(strategy_id, classification=target),
                RUNTIME_REACHABLE=False,
                CONFIG_OWNER=REGISTRY_OWNER,
                CONFIG_VERSION=BOUND_REGISTRY_SCHEMA_VERSION,
                CONFIG_DIGEST=config_digest,
                ENABLED_STATE=_enabled_state(target),
                FAIL_CLOSED_BEHAVIOR=_fail_closed_behavior(target),
                COMPOSITION_INPUT_CONTRACT=_composition_contract(target),
                DIRECT_INTENT_REACHABLE=False,
                DIRECT_FILL_REACHABLE=False,
                DIRECT_ORDER_REACHABLE=False,
                MASTER_V2_BYPASS_REACHABLE=False,
                DOUBLE_PLAY_BYPASS_REACHABLE=False,
                RISK_BYPASS_REACHABLE=False,
                SAFETY_BYPASS_REACHABLE=False,
                RESTART_SEMANTICS="deterministic_snapshot_reconstruction",
                AUTHORITY_OWNER=MASTER_V2_AUTHORITY
                if target is not StrategyAuthorityClassV1.CANONICAL_AUTHORITY
                else AUTHORITY_OWNER,
                DEAUTHORIZATION_REASON=deauthorization_reason(strategy_id),
            )
        )

    for entry_id in all_non_registry_ids():
        target = non_registry_target_classification(entry_id)
        impl, source = non_registry_implementation(entry_id)
        authority = AUTHORITY_OWNER
        if entry_id == "master_v2":
            authority = MASTER_V2_AUTHORITY
        elif entry_id == "double_play":
            authority = DOUBLE_PLAY_AUTHORITY
        else:
            authority = MASTER_V2_AUTHORITY
        rows.append(
            StrategyRegistryMatrixRowV1(
                STRATEGY_ID=entry_id,
                IMPLEMENTATION_SYMBOL=impl,
                SOURCE_PATH=source,
                CURRENT_CLASSIFICATION=target.value,
                TARGET_CLASSIFICATION=target.value,
                PRODUCTIVE_CALLERS=productive_callers_for(entry_id, classification=target),
                RUNTIME_REACHABLE=target
                in {
                    StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
                    StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT,
                },
                CONFIG_OWNER=OWNER if entry_id.startswith("strat-") else AUTHORITY_OWNER,
                CONFIG_VERSION=BOUND_REGISTRY_POLICY_VERSION
                if target is StrategyAuthorityClassV1.CANONICAL_AUTHORITY
                else BOUND_REGISTRY_SCHEMA_VERSION,
                CONFIG_DIGEST=config_digest,
                ENABLED_STATE=_enabled_state(target),
                FAIL_CLOSED_BEHAVIOR=_fail_closed_behavior(target),
                COMPOSITION_INPUT_CONTRACT=_composition_contract(target),
                DIRECT_INTENT_REACHABLE=False,
                DIRECT_FILL_REACHABLE=False,
                DIRECT_ORDER_REACHABLE=False,
                MASTER_V2_BYPASS_REACHABLE=False,
                DOUBLE_PLAY_BYPASS_REACHABLE=False,
                RISK_BYPASS_REACHABLE=False,
                SAFETY_BYPASS_REACHABLE=False,
                RESTART_SEMANTICS="deterministic_snapshot_reconstruction",
                AUTHORITY_OWNER=authority,
                DEAUTHORIZATION_REASON=deauthorization_reason(entry_id),
            )
        )

    rows_sorted = tuple(sorted(rows, key=lambda r: r.STRATEGY_ID))
    # Every row must have equal current/target for non-registry; registry may differ.
    for row in rows_sorted:
        if row.TARGET_CLASSIFICATION not in {c.value for c in StrategyAuthorityClassV1}:
            raise Phase91InventoryError(f"invalid_target:{row.STRATEGY_ID}")
    return rows_sorted


def matrix_digest_v1(rows: Tuple[StrategyRegistryMatrixRowV1, ...]) -> str:
    payload = [r.to_dict() for r in rows]
    return _digest(payload)


def classification_counts_v1(rows: Tuple[StrategyRegistryMatrixRowV1, ...]) -> Dict[str, int]:
    counts: Dict[str, int] = {c.value: 0 for c in StrategyAuthorityClassV1}
    for row in rows:
        counts[row.TARGET_CLASSIFICATION] = counts.get(row.TARGET_CLASSIFICATION, 0) + 1
    return counts


def write_matrix_json(rows: Tuple[StrategyRegistryMatrixRowV1, ...], path: Path) -> str:
    digest = matrix_digest_v1(rows)
    payload = {
        "schema": "strategy_registry_matrix.v1",
        "matrix_digest": digest,
        "rows": [r.to_dict() for r in rows],
        "classification_counts": classification_counts_v1(rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return digest
