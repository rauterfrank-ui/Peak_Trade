"""Evidence and registry contracts for VTDC v1 development evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.constants_v1 import (
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
    REQUIRED_EVIDENCE_METRIC_KEYS,
    STRATEGY_IDENTITY,
)
from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.evidence_schema_v1 import (
    validate_evidence_surface_complete,
)

REQUIRED_REGISTRY_KEYS = (
    "evaluation_run_id",
    "hypothesis_id",
    "strategy_identity",
    "evaluation_executed",
    "runner_started",
    "evaluation_run_count",
    "runner_start_count",
    "development_evaluation_authorized",
    "holdout_accessed",
    "config_digest",
    "strategy_params_digest",
    "dataset_id",
    "dataset_digest",
    "terminal_development_verdict",
)


def build_run_slot_claim_v1(
    *,
    config_digest: str,
    strategy_params_digest: str,
    dataset_id: str,
    dataset_digest: str,
) -> dict[str, Any]:
    return {
        "schema_version": "evaluate_volatility_term_structure_depressed_continuation_run_slot_claim.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "evaluation_run_count": 1,
        "runner_start_count": 1,
        "config_digest": config_digest,
        "strategy_params_digest": strategy_params_digest,
        "dataset_id": dataset_id,
        "dataset_digest": dataset_digest,
        "retry_forbidden": True,
        "holdout_accessed": False,
    }


def build_registry_metadata_v1(
    *,
    evaluation_executed: bool,
    runner_started: bool,
    evaluation_run_count: int,
    runner_start_count: int,
    development_evaluation_authorized: bool,
    config_digest: str,
    strategy_params_digest: str,
    dataset_id: str,
    dataset_digest: str,
    terminal_development_verdict: str,
    holdout_accessed: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": "evaluate_volatility_term_structure_depressed_continuation_registry.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "evaluation_executed": evaluation_executed,
        "runner_started": runner_started,
        "evaluation_run_count": evaluation_run_count,
        "runner_start_count": runner_start_count,
        "development_evaluation_authorized": development_evaluation_authorized,
        "holdout_accessed": holdout_accessed,
        "config_digest": config_digest,
        "strategy_params_digest": strategy_params_digest,
        "dataset_id": dataset_id,
        "dataset_digest": dataset_digest,
        "terminal_development_verdict": terminal_development_verdict,
        "evidence_ref": EVIDENCE_REL_PATH,
    }


def validate_registry_contract_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_REGISTRY_KEYS if k not in payload]
    if missing:
        raise ValueError(f"REGISTRY_CONTRACT_INCOMPLETE:{','.join(missing)}")
    return {"valid": True, "required_key_count": len(REQUIRED_REGISTRY_KEYS)}


def validate_evidence_and_registry_contracts_v1(
    evidence: Mapping[str, Any], registry: Mapping[str, Any]
) -> dict[str, Any]:
    validate_evidence_surface_complete(evidence)
    reg = validate_registry_contract_v1(registry)
    for key in REQUIRED_EVIDENCE_METRIC_KEYS:
        if key not in evidence:
            raise ValueError(f"EVIDENCE_MISSING:{key}")
    return {"evidence": {"valid": True}, "registry": reg, "valid": True}


def write_evidence_bundle_v1(
    output_dir: Path,
    *,
    summary: Mapping[str, Any],
    registry: Mapping[str, Any],
    run_slot_claim: Mapping[str, Any] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "registry.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if run_slot_claim is not None:
        (output_dir / "run_slot_claim.json").write_text(
            json.dumps(run_slot_claim, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
