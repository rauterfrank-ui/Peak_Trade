"""Offline productive factor exposure diagnostics v0.

Consumes manifest-verified productive trade/factor evidence and orthogonality
interpretation context. Diagnostic-only: no strategy selection or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.factor_exposure import (
    FactorExposureDiagnosticsConfigV0,
    FactorExposureDiagnosticsEvidenceV0,
    FactorExposureInputV1,
    PRODUCTIVE_FACTOR_GROUPS_V0,
    build_cross_entity_exposure_diagnostics_v0,
    fit_factor_exposure_diagnostics_v0,
)
from src.research.linear_evidence.factor_exposure_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    TARGET_NAME,
    stable_digest_v0,
)
from src.research.offline_factor_exposure_productive_input_join_materializer_v0 import (
    MaterializationResultV0,
    materialize_from_manifest_paths_v0,
)

DIAGNOSTICS_SCOPE_VERSION = "offline_productive_factor_exposure_diagnostics.v0"

REQUIRED_ORTHOGONALITY_INTERPRETATION_FILES: tuple[str, ...] = (
    "pairwise_interpretation.json",
    "productive_evidence_inventory.json",
    "authority_boundary_assertions.json",
)

REQUIRED_JOIN_MATERIALIZATION_FILES: tuple[str, ...] = (
    "materialization_report.json",
    "productive_factor_exposure_inputs.jsonl",
)


class ProductiveFactorExposureValidationError(ValueError):
    """Fail-closed validation for productive factor exposure diagnostics inputs."""


@dataclass(frozen=True)
class ProductiveInputInventoryV0:
    trade_ledger_path: str
    factor_snapshot_path: str
    trade_ledger_digest: str
    factor_snapshot_digest: str
    row_count_before_filter: int
    row_count_after_filter: int
    instrument_universe_digest: str
    time_range: dict[str, str]
    strategy_or_signal_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_ledger_path": self.trade_ledger_path,
            "factor_snapshot_path": self.factor_snapshot_path,
            "trade_ledger_digest": self.trade_ledger_digest,
            "factor_snapshot_digest": self.factor_snapshot_digest,
            "row_count_before_filter": self.row_count_before_filter,
            "row_count_after_filter": self.row_count_after_filter,
            "instrument_universe_digest": self.instrument_universe_digest,
            "time_range": dict(self.time_range),
            "strategy_or_signal_ids": list(self.strategy_or_signal_ids),
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_bundle_manifest(path: Path, *, verify_fn: Any) -> int:
    ok, _ = verify_fn(path)
    return 0 if ok else 1


def load_orthogonality_interpretation_context(bundle_dir: Path) -> dict[str, Any]:
    root = bundle_dir.expanduser().resolve()
    if not root.is_dir():
        raise ProductiveFactorExposureValidationError(f"INTERPRETATION_BUNDLE_MISSING:{root}")
    loaded: dict[str, Any] = {}
    for name in REQUIRED_ORTHOGONALITY_INTERPRETATION_FILES:
        path = root / name
        if not path.is_file():
            raise ProductiveFactorExposureValidationError(f"MISSING_REQUIRED_FILE:{name}")
        loaded[name.removesuffix(".json")] = _read_json(path)
    return loaded


def load_join_materialization_bundle(bundle_dir: Path) -> dict[str, Any]:
    root = bundle_dir.expanduser().resolve()
    if not root.is_dir():
        raise ProductiveFactorExposureValidationError(f"JOIN_BUNDLE_MISSING:{root}")
    report_path = root / "materialization_report.json"
    inputs_path = root / "productive_factor_exposure_inputs.jsonl"
    if not report_path.is_file():
        raise ProductiveFactorExposureValidationError(
            "MISSING_REQUIRED_FILE:materialization_report.json"
        )
    if not inputs_path.is_file():
        raise ProductiveFactorExposureValidationError(
            "MISSING_REQUIRED_FILE:productive_factor_exposure_inputs.jsonl"
        )
    report = _read_json(report_path)
    records: list[FactorExposureInputV1] = []
    for line in inputs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        records.append(
            FactorExposureInputV1(
                instrument_id=str(payload["instrument_id"]),
                timestamp=int(payload["timestamp"]),
                target_return=float(payload["target_return"]),
                factor_values=dict(payload["factor_values"]),
                factor_time=payload.get("factor_time"),
                decision_time=payload.get("decision_time"),
            )
        )
    return {"report": report, "records": tuple(records)}


def materialize_productive_inputs_from_paths(
    *,
    trade_ledger_path: Path,
    factor_snapshot_path: Path,
) -> MaterializationResultV0:
    return materialize_from_manifest_paths_v0(
        trade_ledger_path=trade_ledger_path,
        factor_snapshot_path=factor_snapshot_path,
    )


def _group_records_by_instrument(
    records: Sequence[FactorExposureInputV1],
) -> dict[str, tuple[FactorExposureInputV1, ...]]:
    grouped: dict[str, list[FactorExposureInputV1]] = {}
    for record in records:
        grouped.setdefault(record.instrument_id, []).append(record)
    return {key: tuple(items) for key, items in sorted(grouped.items())}


def build_productive_input_inventory_v0(
    *,
    trade_ledger_path: Path,
    factor_snapshot_path: Path,
    materialization: MaterializationResultV0,
    strategy_or_signal_ids: Sequence[str],
) -> ProductiveInputInventoryV0:
    provenance = materialization.provenance
    return ProductiveInputInventoryV0(
        trade_ledger_path=str(trade_ledger_path),
        factor_snapshot_path=str(factor_snapshot_path),
        trade_ledger_digest=materialization.source_trade_ledger_digest,
        factor_snapshot_digest=materialization.source_factor_snapshot_digest,
        row_count_before_filter=materialization.join_result.row_count_before_filter,
        row_count_after_filter=materialization.join_result.row_count_after_filter,
        instrument_universe_digest=provenance.instrument_universe_digest,
        time_range=dict(provenance.time_range),
        strategy_or_signal_ids=tuple(sorted(strategy_or_signal_ids)),
    )


def build_factor_binding_v0(
    records: Sequence[FactorExposureInputV1],
) -> dict[str, Any]:
    if not records:
        return {
            "factor_groups_available": [],
            "factor_groups_missing": sorted(
                {
                    "market_common_return",
                    "volatility",
                    "trend",
                    "momentum",
                    "liquidity_spread",
                    "funding",
                    "regime",
                    "instrument_common_cluster",
                }
            ),
            "feature_names": [],
            "feature_order_stable": True,
        }
    feature_names = tuple(sorted(records[0].factor_values.keys()))
    available_groups = sorted(
        {PRODUCTIVE_FACTOR_GROUPS_V0.get(name, "NOT_AVAILABLE") for name in feature_names}
    )
    all_groups = {
        "market_common_return",
        "volatility",
        "trend",
        "momentum",
        "liquidity_spread",
        "funding",
        "regime",
        "instrument_common_cluster",
    }
    return {
        "factor_groups_available": available_groups,
        "factor_groups_missing": sorted(all_groups - set(available_groups)),
        "feature_names": list(feature_names),
        "feature_order_stable": True,
        "feature_source_fields": {
            name: PRODUCTIVE_FACTOR_GROUPS_V0.get(name, "NOT_COMPUTED") for name in feature_names
        },
    }


def build_validation_policy_v0(
    config: FactorExposureDiagnosticsConfigV0,
) -> dict[str, Any]:
    return {
        "validation_policy": "time_ordered",
        "random_validation_split_blocked": True,
        "validation_fraction": config.validation_fraction,
        "lookahead_guard": "factor_time < decision_time < target_time",
        "finalized_bar_only": True,
        "feature_time_less_than_target_time": True,
        "target_shift_explicit": True,
    }


def build_authority_boundary_v0() -> dict[str, Any]:
    return {
        "offline_only": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "strategy_selection_changed": False,
        "active_set_changed": False,
        "portfolio_allocation_changed": False,
        "economic_evaluation_executed": False,
        "economic_validity_gate_changed": False,
        "promotion_pass_created": False,
        "runtime_rewire_admissible": False,
        "no_economic_claim_from_ols_alone": True,
        "interpretation_boundary": [
            "Exposure may be reported as redundant/concentrated/diversified/unstable/inconclusive.",
            "Strategies may share high linear exposures without selection authority.",
            "Betas may be temporally unstable without replacement authority.",
            "Large residual share limits linear explanation.",
            "Results support later portfolio-research questions only.",
        ],
        "forbidden_claims": [
            "automatic strategy removal",
            "automatic weight increase",
            "active set replacement",
            "multi-future-runtime authorization",
            "economic validity proof",
            "promotion admissibility",
        ],
    }


def build_failure_taxonomy_v0(
    *,
    pooled: FactorExposureDiagnosticsEvidenceV0,
    per_entity: Mapping[str, FactorExposureDiagnosticsEvidenceV0],
) -> dict[str, Any]:
    statuses = {pooled.status}
    statuses.update(item.status for item in per_entity.values())
    all_reasons: set[str] = set(pooled.reason_codes)
    for item in per_entity.values():
        all_reasons.update(item.reason_codes)
    return {
        "supported_statuses": sorted(
            {
                "DIAGNOSTIC_ONLY",
                "INSUFFICIENT_DATA",
                "LEAKAGE_BLOCKED",
                "RANK_DEFICIENT_BLOCKED",
                "ROBUSTNESS_FAILED",
            }
        ),
        "observed_statuses": sorted(statuses),
        "observed_reason_codes": sorted(all_reasons),
    }


def build_productive_factor_exposure_diagnostics_artifacts_v0(
    *,
    records: Sequence[FactorExposureInputV1],
    materialization: MaterializationResultV0,
    trade_ledger_path: Path,
    factor_snapshot_path: Path,
    orthogonality_interpretation_bundle: Path | None = None,
    strategy_or_signal_ids: Sequence[str] = ("trend_following/v1",),
    config: FactorExposureDiagnosticsConfigV0 | None = None,
) -> dict[str, Any]:
    cfg = config or FactorExposureDiagnosticsConfigV0()
    cfg.validate()

    provenance = materialization.provenance
    source_refs = [
        str(trade_ledger_path),
        str(factor_snapshot_path),
    ]
    if orthogonality_interpretation_bundle is not None:
        source_refs.append(str(orthogonality_interpretation_bundle))

    pooled = fit_factor_exposure_diagnostics_v0(
        records,
        strategy_or_signal_id="pooled",
        config=cfg,
        source_evidence_refs=source_refs,
        instrument_universe_digest=provenance.instrument_universe_digest,
        time_range=provenance.time_range,
        dropped_rows_by_reason=dict(materialization.join_result.dropped_rows_by_reason),
    )

    grouped = _group_records_by_instrument(records)
    per_entity, similarity, cluster_assignments, cluster_diag = (
        build_cross_entity_exposure_diagnostics_v0(
            grouped,
            config=cfg,
            source_evidence_refs=source_refs,
            instrument_universe_digest=provenance.instrument_universe_digest,
            time_range=provenance.time_range,
            dropped_rows_by_reason=dict(materialization.join_result.dropped_rows_by_reason),
        )
    )

    inventory = build_productive_input_inventory_v0(
        trade_ledger_path=trade_ledger_path,
        factor_snapshot_path=factor_snapshot_path,
        materialization=materialization,
        strategy_or_signal_ids=strategy_or_signal_ids,
    )
    factor_binding = build_factor_binding_v0(records)
    validation_policy = build_validation_policy_v0(cfg)
    authority_boundary = build_authority_boundary_v0()
    failure_taxonomy = build_failure_taxonomy_v0(pooled=pooled, per_entity=per_entity)

    interpretation_context: dict[str, Any] = {}
    if orthogonality_interpretation_bundle is not None:
        interpretation_context = load_orthogonality_interpretation_context(
            orthogonality_interpretation_bundle
        )

    beta_stability = {
        "pooled": pooled.beta_stability,
        "per_entity": {key: value.beta_stability for key, value in sorted(per_entity.items())},
    }

    output_digest = _stable_digest(
        {
            "scope_version": DIAGNOSTICS_SCOPE_VERSION,
            "pooled": pooled.to_dict(),
            "per_entity": {key: value.to_dict() for key, value in sorted(per_entity.items())},
            "similarity": similarity,
            "cluster_diag": cluster_diag,
            "inventory": inventory.to_dict(),
        }
    )

    return {
        "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
        "target_name": TARGET_NAME,
        "output_digest": output_digest,
        "input_evidence_inventory": inventory.to_dict(),
        "factor_binding": factor_binding,
        "feature_matrix_binding": {
            "feature_matrix_digest": pooled.feature_matrix_digest,
            "target_digest": pooled.target_digest,
            "config_digest": pooled.config_digest,
            "validation_policy": validation_policy,
        },
        "validation_policy": validation_policy,
        "factor_exposure_results": {
            "pooled": pooled.to_dict(),
            "per_entity": {key: value.to_dict() for key, value in sorted(per_entity.items())},
        },
        "beta_stability": beta_stability,
        "exposure_similarity_matrix": similarity,
        "cluster_risk_diagnostics": {
            **cluster_diag,
            "exposure_cluster_assignments": cluster_assignments,
            "computed": bool(similarity),
        },
        "failure_taxonomy": failure_taxonomy,
        "authority_boundary": authority_boundary,
        "orthogonality_interpretation_context_present": bool(interpretation_context),
        "interpretation_status": _interpretation_status(pooled, per_entity, cluster_diag),
    }


def _interpretation_status(
    pooled: FactorExposureDiagnosticsEvidenceV0,
    per_entity: Mapping[str, FactorExposureDiagnosticsEvidenceV0],
    cluster_diag: Mapping[str, object],
) -> dict[str, str]:
    statuses: dict[str, str] = {"pooled_exposure": "inconclusive"}
    if pooled.status == "DIAGNOSTIC_ONLY":
        if pooled.unexplained_residual_share > 0.9:
            statuses["pooled_exposure"] = "large_unexplained_residual"
        elif pooled.dominant_factor_exposures:
            statuses["pooled_exposure"] = "dominant_exposures_identified"
        else:
            statuses["pooled_exposure"] = "diversified_or_weak_linear_explanation"

    if cluster_diag.get("cluster_concentration_high"):
        statuses["common_exposure"] = "concentrated"
    elif float(cluster_diag.get("max_pairwise_similarity", 0.0)) >= 0.85:
        statuses["common_exposure"] = "redundant"
    else:
        statuses["common_exposure"] = "diversified"

    unstable = any(
        item.beta_stability.get("sign_unstable_factors")
        for item in per_entity.values()
        if item.beta_stability.get("computed")
    )
    statuses["beta_stability"] = "unstable" if unstable else "stable_or_inconclusive"
    statuses["cluster_risk"] = (
        "cluster_concentration_high"
        if cluster_diag.get("cluster_concentration_high")
        else "not_elevated"
    )
    return statuses


__all__ = [
    "DIAGNOSTICS_SCOPE_VERSION",
    "ProductiveFactorExposureValidationError",
    "ProductiveInputInventoryV0",
    "build_authority_boundary_v0",
    "build_factor_binding_v0",
    "build_failure_taxonomy_v0",
    "build_productive_factor_exposure_diagnostics_artifacts_v0",
    "build_productive_input_inventory_v0",
    "build_validation_policy_v0",
    "load_join_materialization_bundle",
    "load_orthogonality_interpretation_context",
    "materialize_productive_inputs_from_paths",
    "verify_bundle_manifest",
]
