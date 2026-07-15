"""Dataset digest reconciliation repair contract tests for pairwise spillover v1 baseline preflight."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    REASON_DATASET_DIGEST_NOT_VERIFIED,
    REEVALUATION_BASELINE_DATASET_DIGEST_RECONCILIATION_REPAIR_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNTIME_EFFECT,
    RATIFIED_DATASET_DIGEST,
    run_reevaluation_baseline_execution_preflight_v0,
    validate_reevaluation_baseline_dataset_digest_reconciliation_repair_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    PRIOR_RATIFIED_DATASET_DIGEST,
    RATIFIED_NORMALIZED_PANEL_DIGEST,
    RATIFIED_SEMANTIC_DATA_DIGEST,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    validate_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    materialize_bound_panel_dataset_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
PY310_STAGING = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="panel staging loader requires Python 3.10+ zip(strict=True)",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


def test_repair_go_token_accepted() -> None:
    ok, reasons = validate_reevaluation_baseline_dataset_digest_reconciliation_repair_go_token_v0(
        REEVALUATION_BASELINE_DATASET_DIGEST_RECONCILIATION_REPAIR_GO_TOKEN
    )
    assert ok is True
    assert reasons == ()


def test_binding_uses_semantic_dataset_digest(complete_binding: dict) -> None:
    assert complete_binding["dataset_digest"] == RATIFIED_SEMANTIC_DATA_DIGEST
    assert complete_binding["panel_dataset_binding"]["normalized_panel_digest"] == (
        RATIFIED_NORMALIZED_PANEL_DIGEST
    )
    assert PRIOR_RATIFIED_DATASET_DIGEST == RATIFIED_NORMALIZED_PANEL_DIGEST
    assert RATIFIED_DATASET_DIGEST != PRIOR_RATIFIED_DATASET_DIGEST


def test_materializer_to_binder_roundtrip_passes(complete_binding: dict) -> None:
    roundtrip = materializer_to_binder_roundtrip_v0(complete_binding)
    assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


@PY310_STAGING
@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging_root_unavailable")
def test_canonical_materializer_digest_matches_ratified_dataset_digest(
    complete_binding: dict,
) -> None:
    materialization = materialize_bound_panel_dataset_v0(
        STAGING_ROOT,
        period_binding=complete_binding["period_binding"],
    )
    repeat = materialize_bound_panel_dataset_v0(
        STAGING_ROOT,
        period_binding=complete_binding["period_binding"],
    )
    assert materialization.panel_data_digest == RATIFIED_DATASET_DIGEST
    assert repeat.panel_data_digest == materialization.panel_data_digest
    assert materialization.idempotent_digest_stable is True


@PY310_STAGING
@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging_root_unavailable")
def test_preflight_dataset_digest_verified_and_repaired(
    authorization_ratification: dict,
    complete_binding: dict,
) -> None:
    result = run_reevaluation_baseline_execution_preflight_v0(
        go_token=REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
        repo_root=REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=complete_binding,
        staging_root=STAGING_ROOT,
        verify_source_manifests=True,
        materialize_dataset=True,
    )
    assert result.dataset_digest_verified is True
    assert result.dataset_digest_repaired is True
    assert result.baseline_executed is False
    assert result.economic_evaluation_executed is False
    assert result.runtime_effect == RUNTIME_EFFECT
    assert result.authority_effect == AUTHORITY_EFFECT
    assert REASON_DATASET_DIGEST_NOT_VERIFIED not in result.reason_codes


@PY310_STAGING
@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging_root_unavailable")
def test_stale_dataset_digest_rejected(
    authorization_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["binding"]["digest_bindings"]["dataset_digest"]["value"] = PRIOR_RATIFIED_DATASET_DIGEST
    stale["dataset_digest"] = PRIOR_RATIFIED_DATASET_DIGEST
    verdict, reasons = validate_versioned_hypothesis_binding_v0(stale)
    assert verdict.value == "REJECTED_INCOMPLETE"
    assert "DATASET_DIGEST_MISMATCH" in reasons

    result = run_reevaluation_baseline_execution_preflight_v0(
        go_token=REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
        repo_root=REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=stale,
        staging_root=STAGING_ROOT,
        verify_source_manifests=True,
        materialize_dataset=True,
    )
    assert result.dataset_digest_verified is False
    assert result.dataset_digest_repaired is False
    assert "DATASET_DIGEST_MISMATCH" in result.reason_codes
