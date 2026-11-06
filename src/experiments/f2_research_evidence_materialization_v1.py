"""F2 research evidence materialization v1 — envelope-required evidence classes only."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    GRID_SEED,
    GRID_VERSION,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
    PARAMETER_NAMES,
    SEARCH_SPACE_BOUNDS,
)
from src.backtest.parameter_sensitivity_v1 import ParameterSensitivityResultV1
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    EVIDENCE_REQUIREMENTS_REF,
    SURFACE_ID,
    compute_f2_reproducibility_digest_v1,
)
from src.experiments.f2_step29m_config_authority_v1 import F2Step29mConfigAuthorityV1
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "f2_research_evidence_materialization_v1"
REQUIRED_EVIDENCE_CLASSES: Final[tuple[str, ...]] = (
    "GRID_IDENTITY",
    "GRID_DIGEST",
    "BASELINE_COST_BINDING",
    "ECONOMIC_EVALUATION_BINDING",
    "REPRODUCIBILITY_DIGEST",
)


class F2ResearchEvidenceMaterializationError(ValueError):
    """Fail-closed F2 evidence materialization error."""


def _load_required_evidence_classes(repo_root: Path) -> tuple[str, ...]:
    payload = json.loads((repo_root / EVIDENCE_REQUIREMENTS_REF).read_text(encoding="utf-8"))
    classes = payload.get("required_evidence_classes")
    if not isinstance(classes, list) or not classes:
        raise F2ResearchEvidenceMaterializationError("evidence_requirements_missing_classes")
    return tuple(str(item) for item in classes)


def materialize_f2_required_evidence_v1(
    *,
    authority: F2Step29mConfigAuthorityV1,
    grid_digest: str,
    sensitivity: ParameterSensitivityResultV1,
    repo_root: Path | None = None,
) -> MappingProxyType[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = _load_required_evidence_classes(root)
    if tuple(required) != REQUIRED_EVIDENCE_CLASSES:
        raise F2ResearchEvidenceMaterializationError("evidence_class_ssot_mismatch")

    reproducibility_digest = compute_f2_reproducibility_digest_v1()
    materialized: dict[str, Any] = {
        "GRID_IDENTITY": {
            "grid_id": GRID_ID,
            "grid_version": GRID_VERSION,
            "parameter_names": list(PARAMETER_NAMES),
            "fee_bps": list(OPERATOR_BOUND_FEE_BPS),
            "slippage_bps": list(OPERATOR_BOUND_SLIPPAGE_BPS),
            "search_space_bounds": SEARCH_SPACE_BOUNDS,
            "seed": GRID_SEED,
            "combination_count": sensitivity.combination_count,
            "surface_id": SURFACE_ID,
        },
        "GRID_DIGEST": grid_digest,
        "BASELINE_COST_BINDING": {
            "baseline_fee_bps": BASELINE_FEE_BPS,
            "baseline_slippage_bps": BASELINE_SLIPPAGE_BPS,
            "authoritative_config_rel_path": authority.authoritative_config_rel_path,
            "config_content_digest": authority.config_content_digest,
        },
        "ECONOMIC_EVALUATION_BINDING": {
            "parameter_sensitivity_owner": sensitivity.owner,
            "parameter_sensitivity_contract_version": sensitivity.contract_version,
            "pipeline_status": sensitivity.pipeline_status.value,
            "parameter_robustness_policy_status": sensitivity.parameter_robustness_policy_status,
            "parameter_robustness_policy_pass": sensitivity.parameter_robustness_policy_pass,
            "result_digest": sensitivity.result_digest,
            "grid_digest": sensitivity.grid_digest,
            "strategy_id": authority.strategy_id,
            "dataset_digest": authority.dataset_digest,
            "instrument_id": authority.instrument_id,
            "economic_validity_policy_required": True,
            "pipeline_pass_not_imply_policy_pass": True,
        },
        "REPRODUCIBILITY_DIGEST": reproducibility_digest,
    }
    missing = [key for key in required if key not in materialized]
    if missing:
        raise F2ResearchEvidenceMaterializationError(f"missing_evidence_classes:{missing}")

    body = {
        "schema_version": SCHEMA_VERSION,
        "surface_id": SURFACE_ID,
        "required_evidence_classes": list(required),
        "evidence_by_class": materialized,
        "promotion_evidence_forbidden": True,
        "productive_apply_evidence_forbidden": True,
    }
    body["evidence_bundle_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "evidence_bundle_digest"}
    )
    return MappingProxyType(body)
