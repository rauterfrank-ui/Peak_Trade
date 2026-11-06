"""Fail-closed binding checks for digests, dataset, index, state, and ledger refs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.bollinger_mr_economic_failure_decomposition_development_v1.constants_v1 import (
    BASELINE_CONFIG_ID,
    DATASET_CLASS,
    DATASET_ID,
    DEVELOPMENT_SPLIT_DIGEST,
    EVIDENCE_CLASS_ID,
    EXECUTION_ID,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    HOLDOUT_OPAQUE_ID,
    PARENT_BASELINE_METRICS,
    SCOPE_ID,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    assert_not_holdout_path,
    verify_development_panel_hashes,
)
from src.research.entry_effective_mr_eligibility_hypothesis_preregistration_v1 import (
    HypothesisPreregistrationError,
    reject_holdout_dataset_or_path,
)


class DecompositionBindingError(ValueError):
    """Fail-closed binding / digest / ledger integrity error."""


def load_contract(repo: Path) -> dict[str, Any]:
    path = repo / "config/research/bollinger_mr_economic_failure_decomposition_development_v1.json"
    if not path.is_file():
        raise DecompositionBindingError(f"CONTRACT_MISSING:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DecompositionBindingError("CONTRACT_NOT_OBJECT")
    return payload


def assert_contract_gates(config: Mapping[str, Any]) -> None:
    if config.get("scope_id") != SCOPE_ID:
        raise DecompositionBindingError("SCOPE_ID_MISMATCH")
    if config.get("execution_id") != EXECUTION_ID:
        raise DecompositionBindingError("EXECUTION_ID_MISMATCH")
    if config.get("evidence_class_id") != EVIDENCE_CLASS_ID:
        raise DecompositionBindingError("EVIDENCE_CLASS_ID_MISMATCH")
    if config.get("dataset_id") != DATASET_ID:
        raise DecompositionBindingError("DATASET_ID_MISMATCH")
    if config.get("dataset_class") != DATASET_CLASS:
        raise DecompositionBindingError("DATASET_CLASS_MISMATCH")
    if config.get("baseline_config_id") != BASELINE_CONFIG_ID:
        raise DecompositionBindingError("BASELINE_CONFIG_ID_MISMATCH")
    if config.get("development_split_digest") != DEVELOPMENT_SPLIT_DIGEST:
        raise DecompositionBindingError("DEVELOPMENT_SPLIT_DIGEST_MISMATCH")
    if config.get("non_authorizing") is not True:
        raise DecompositionBindingError("NON_AUTHORIZING_REQUIRED")
    for flag in (
        "economic_validity_offline_gate_pass",
        "promotion_eligible",
        "runtime_activated",
        "orders_allowed",
        "holdout_access_authorized",
        "new_hypothesis_authorized",
        "parameter_tuning_authorized",
        "master_v2_mutation_allowed",
        "double_play_mutation_allowed",
        "risk_sizing_execution_mutation_allowed",
    ):
        if config.get(flag) is not False:
            raise DecompositionBindingError(f"FLAG_MUST_BE_FALSE:{flag}")
    reject_holdout_dataset_or_path(str(config.get("dataset_id") or ""))
    sealed_holdout = str(config.get("sealed_holdout_id") or "")
    if sealed_holdout != HOLDOUT_OPAQUE_ID:
        raise DecompositionBindingError("SEALED_HOLDOUT_ID_MISMATCH")
    if config.get("holdout_forbidden") is not True:
        raise DecompositionBindingError("HOLDOUT_FORBIDDEN_REQUIRED")


def assert_baseline_binding_digests(repo: Path, config: Mapping[str, Any]) -> dict[str, str]:
    binding_path = repo / "config/research" / f"{BASELINE_CONFIG_ID}.json"
    if not binding_path.is_file():
        raise DecompositionBindingError(f"BASELINE_BINDING_MISSING:{binding_path}")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if not isinstance(binding, dict):
        raise DecompositionBindingError("BASELINE_BINDING_NOT_OBJECT")
    inner = binding.get("binding")
    if not isinstance(inner, dict):
        raise DecompositionBindingError("BASELINE_BINDING_INNER_MISSING")
    required = (
        "binding_semantic_digest",
        "config_digest",
        "data_digest",
        "implementation_digest",
    )
    digests: dict[str, str] = {}
    for key in required:
        value = str(inner.get(key) or "")
        if len(value) != 64:
            raise DecompositionBindingError(f"BASELINE_DIGEST_MISSING_OR_INVALID:{key}")
        digests[key] = value
    expected = config.get("baseline_binding_digests")
    if not isinstance(expected, dict):
        raise DecompositionBindingError("CONTRACT_BASELINE_DIGESTS_MISSING")
    for key, value in digests.items():
        if str(expected.get(key) or "") != value:
            raise DecompositionBindingError(f"BASELINE_DIGEST_MISMATCH:{key}")
    return digests


def assert_panel_index_and_state_binding(archive_root: Path) -> dict[str, Any]:
    assert_not_holdout_path(archive_root)
    proof = verify_development_panel_hashes(archive_root)
    if proof.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise DecompositionBindingError("PANEL_MANIFEST_DIGEST_MISMATCH")
    if proof.get("content_hash") != EXPECTED_CONTENT_HASH:
        raise DecompositionBindingError("PANEL_CONTENT_HASH_MISMATCH")
    if proof.get("dataset_id") != DATASET_ID:
        raise DecompositionBindingError("PANEL_DATASET_ID_MISMATCH")
    return proof


def assert_parent_baseline_ledger_binding(
    *,
    observed: Mapping[str, Any],
    rel_tol: float = 1e-9,
    abs_tol: float = 1e-6,
) -> None:
    """Fail closed if replayed baseline ledger fields are missing or internally inconsistent.

    Parent sealed ADX-DI control aggregates are lineage metadata only: MV2/wiring
    evolution may change trade counts versus archived summaries. Binding truth is
    digest/panel/split/cost freeze plus a consistent trade ledger.
    """
    required_keys = (
        "trade_count",
        "long_trades",
        "short_trades",
        "gross_pnl",
        "fees",
        "slippage",
        "net_pnl",
    )
    for key in required_keys:
        if key not in observed:
            raise DecompositionBindingError(f"LEDGER_FIELD_MISSING:{key}")
        if observed[key] is None:
            raise DecompositionBindingError(f"LEDGER_FIELD_NULL:{key}")
    trade_count = int(observed["trade_count"])
    long_n = int(observed["long_trades"])
    short_n = int(observed["short_trades"])
    if trade_count <= 0:
        raise DecompositionBindingError("LEDGER_ZERO_TRADES")
    if long_n + short_n != trade_count:
        raise DecompositionBindingError(
            f"LEDGER_SIDE_COUNT_MISMATCH:{long_n}+{short_n}!={trade_count}"
        )
    gross = float(observed["gross_pnl"])
    fees = float(observed["fees"])
    slip = float(observed["slippage"])
    net = float(observed["net_pnl"])
    if fees < 0.0 or slip < 0.0:
        raise DecompositionBindingError("LEDGER_NEGATIVE_COSTS")
    expected_net = gross - fees - slip
    if abs(expected_net - net) > max(abs_tol, rel_tol * max(abs(expected_net), abs(net), 1.0)):
        raise DecompositionBindingError(f"LEDGER_GROSS_COST_NET_INCONSISTENT:{expected_net}!={net}")
    # Lineage metadata must remain present for governance traceability.
    for key in ("trade_count", "gross_pnl", "net_pnl"):
        if key not in PARENT_BASELINE_METRICS:
            raise DecompositionBindingError(f"PARENT_LINEAGE_METRIC_MISSING:{key}")


def assert_trade_ledger_fields(trade: Mapping[str, Any]) -> None:
    required = (
        "side",
        "gross_pnl",
        "fees",
        "slippage",
        "net_pnl",
        "entry_time",
        "exit_time",
        "instrument_id",
    )
    for key in required:
        if trade.get(key) is None:
            raise DecompositionBindingError(f"TRADE_LEDGER_FIELD_MISSING:{key}")
    side = str(trade["side"]).lower()
    if side not in {"long", "short"}:
        raise DecompositionBindingError(f"TRADE_SIDE_UNKNOWN:{side}")


def reject_holdout_access(path_or_id: str | Path) -> None:
    try:
        reject_holdout_dataset_or_path(str(path_or_id))
        assert_not_holdout_path(path_or_id)
    except HypothesisPreregistrationError as exc:
        raise DecompositionBindingError(str(exc)) from exc
