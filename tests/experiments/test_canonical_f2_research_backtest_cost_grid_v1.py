"""F2 research backtest cost grid optimizable surface and E2E execution tests."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
    SOURCE_STEP29M_CONFIG,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    ALLOWED_POLICY_DOMAIN_REF,
    BOUNDS_REF,
    SURFACE_ID,
    SURFACE_OWNER_REF,
    TARGET_FAMILY,
    build_f2_research_backtest_cost_grid_envelope_payload_v1,
    compute_f2_reproducibility_digest_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalCodeProvenanceV1,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    D27_TEST_ENTRY_GATE,
    EXECUTION_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
    F2ResearchBacktestCostGridExecutionError,
    PRODUCTIVE_PARAMETER_MUTATION,
    PRODUCTIVE_TRADING_EFFECT,
    PROMOTION_PERFORMED,
    PROPOSAL_ONLY,
    SELECTION_AUTHORITY,
    TRADING_AUTHORITY,
    prove_f2_e2e_research_execution_materialization_v1,
    run_f2_research_backtest_cost_grid_offline_v1,
)
from src.experiments.canonical_f3_strategy_hyperparameter_optimizable_surface_exclusion_v1 import (
    GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    build_optimizable_envelope_v1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.f2_research_evidence_materialization_v1 import REQUIRED_EVIDENCE_CLASSES
from src.experiments.f2_step29m_config_authority_v1 import resolve_f2_step29m_config_authority_v1
from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    ALLOWED_CALIBRATABLE_PARAMETERS,
    DIAGNOSTIC_ONLY_PARAMETERS,
)
from tests.governance.d27_native_baseline_fixtures_v1 import (
    build_fixture_native_baseline_evidence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
F2_MODULE = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_f2_research_backtest_cost_grid_optimizable_surface_v1.py"
)
_LEGACY_OFFLINE_GIT_SHA = "25b0518b93f91a9609d70c30fb8cd3bf96401a46"
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _research_bars(n: int = 48) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1h" for _ in close],
        },
        index=idx,
    )


def test_f2_domain_matches_step29m_grid_ssot() -> None:
    step29m = json.loads((REPO_ROOT / SOURCE_STEP29M_CONFIG).read_text(encoding="utf-8"))
    grid = step29m["backtest"]["parameter_sensitivity"]["grid"]
    assert grid["grid_id"] == GRID_ID
    assert grid["parameter_names"] == list(ALLOWED_CALIBRATABLE_PARAMETERS)
    domain = json.loads((REPO_ROOT / ALLOWED_POLICY_DOMAIN_REF).read_text(encoding="utf-8"))
    bounds = json.loads((REPO_ROOT / BOUNDS_REF).read_text(encoding="utf-8"))
    assert tuple(domain["fee_bps"]) == OPERATOR_BOUND_FEE_BPS
    assert tuple(domain["slippage_bps"]) == OPERATOR_BOUND_SLIPPAGE_BPS
    assert tuple(bounds["fee_bps"]) == OPERATOR_BOUND_FEE_BPS
    assert tuple(grid["parameter_values"][0]) == OPERATOR_BOUND_FEE_BPS
    assert tuple(grid["parameter_values"][1]) == OPERATOR_BOUND_SLIPPAGE_BPS


def test_f2_resolver_admits_surface() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID)
    )
    assert result["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert result["surface_id"] == SURFACE_ID


def test_f1_f2_authorization_isolation() -> None:
    registry = build_authorized_surface_registry_v1()
    assert M9_SURFACE_ID in registry["authorized_surface_ids"]
    assert SURFACE_ID in registry["authorized_surface_ids"]
    m9 = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=M9_SURFACE_ID)
    )
    f2 = resolve_optimizable_envelope_v1(OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID))
    assert m9["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert f2["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert m9["envelope_identity"] != f2["envelope_identity"]


@pytest.fixture
def f2_clean_git_provenance(monkeypatch: pytest.MonkeyPatch) -> str:
    """Bind identity to HEAD SHA while allowing local dirty worktrees in tests."""
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    def _clean_provenance(repo_root: Path) -> CanonicalCodeProvenanceV1:
        return CanonicalCodeProvenanceV1(
            git_sha=head_sha,
            working_tree_status=WORKING_TREE_CLEAN,
            dirty_paths_digest=None,
        )

    monkeypatch.setattr(
        "src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1.inspect_code_provenance_v1",
        _clean_provenance,
    )
    return head_sha


def test_f2_e2e_research_execution(f2_clean_git_provenance: str) -> None:
    native_baseline = build_fixture_native_baseline_evidence_v1()
    authority = resolve_f2_step29m_config_authority_v1(repo_root=REPO_ROOT)
    first = run_f2_research_backtest_cost_grid_offline_v1(
        native_baseline_evidence_v1=native_baseline,
        research_bars_v1=_research_bars(),
        repo_root=REPO_ROOT,
        require_clean_git_provenance=False,
    )
    second = run_f2_research_backtest_cost_grid_offline_v1(
        native_baseline_evidence_v1=native_baseline,
        research_bars_v1=_research_bars(),
        repo_root=REPO_ROOT,
        require_clean_git_provenance=False,
    )
    assert first["execution_digest"] == second["execution_digest"]
    assert first["combination_count"] == 9
    assert first["grid_id"] == GRID_ID
    assert first["baseline_fee_bps"] == BASELINE_FEE_BPS
    assert first["baseline_slippage_bps"] == BASELINE_SLIPPAGE_BPS
    assert first["d27_test_entry_gate"] == D27_TEST_ENTRY_GATE
    assert first["d27_test_entry_gate_phases"]["bounded_sensitivity_oos"] == "COMPLETE"
    assert first["source_step29m_config_ref"] == authority.authoritative_config_rel_path
    assert first["f2_config_authority"]["config_content_digest"] == authority.config_content_digest

    provenance = first["code_provenance"]
    assert _GIT_SHA_RE.match(provenance["git_sha"])
    assert provenance["git_sha"] == f2_clean_git_provenance
    assert provenance["git_sha"] != _LEGACY_OFFLINE_GIT_SHA
    assert provenance["working_tree_status"] == WORKING_TREE_CLEAN

    evidence = first["required_evidence_materialization"]["evidence_by_class"]
    for cls in REQUIRED_EVIDENCE_CLASSES:
        assert cls in evidence
    assert evidence["REPRODUCIBILITY_DIGEST"] == compute_f2_reproducibility_digest_v1()
    assert evidence["GRID_DIGEST"] == first["grid_digest"]
    assert evidence["ECONOMIC_EVALUATION_BINDING"]["dataset_digest"] == authority.dataset_digest
    assert first["parameter_sensitivity_pipeline_status"] == "PIPELINE_PASS"

    baselines = [c for c in first["candidates"] if c["is_baseline"]]
    assert len(baselines) == 1
    assert baselines[0]["fee_bps"] == BASELINE_FEE_BPS
    assert baselines[0]["slippage_bps"] == BASELINE_SLIPPAGE_BPS
    assert first["proposal_only"] is True
    assert first["productive_parameter_mutation"] is False
    assert first["promotion_performed"] is False
    assert first["external_effect_authorized"] is False
    assert first["productive_trading_effect"] == PRODUCTIVE_TRADING_EFFECT
    assert first["trading_authority"] == TRADING_AUTHORITY == "NONE"
    assert first["selection_authority"] == SELECTION_AUTHORITY == "NONE"
    assert first["execution_authority"] == EXECUTION_AUTHORITY == "NONE"


def test_f2_envelope_identity_and_owner() -> None:
    envelope = build_optimizable_envelope_v1(
        build_f2_research_backtest_cost_grid_envelope_payload_v1()
    )
    assert envelope["surface_id"] == SURFACE_ID
    assert envelope["surface_owner_ref"] == SURFACE_OWNER_REF
    assert envelope["target_family"] == TARGET_FAMILY
    assert envelope["productive_authority"] == "NONE"
    digest = compute_f2_reproducibility_digest_v1()
    assert envelope["reproducibility_digest"] == digest


def test_f2_module_no_trading_imports() -> None:
    tree = ast.parse(F2_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "src.trading.master_v2" not in imported
    assert "src.execution" not in imported


def test_f3_excluded_and_ols_diagnostic_only() -> None:
    assert GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED is False
    assert "signal_scale" in DIAGNOSTIC_ONLY_PARAMETERS
    assert set(ALLOWED_CALIBRATABLE_PARAMETERS) == {"fee_bps", "slippage_bps"}


def test_f2_governance_materialization_proof_hook() -> None:
    assert prove_f2_e2e_research_execution_materialization_v1(repo_root=REPO_ROOT) is True


def test_f2_instrument_matches_mv2_required() -> None:
    authority = resolve_f2_step29m_config_authority_v1(repo_root=REPO_ROOT)
    assert authority.instrument_id == mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID


def test_f2_fail_closed_without_research_bars() -> None:
    native = build_fixture_native_baseline_evidence_v1()
    with pytest.raises(F2ResearchBacktestCostGridExecutionError, match="F2_RESEARCH_BARS_REQUIRED"):
        run_f2_research_backtest_cost_grid_offline_v1(
            native_baseline_evidence_v1=native,
            repo_root=REPO_ROOT,
            require_clean_git_provenance=False,
        )
