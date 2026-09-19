"""F2 research backtest cost grid optimizable surface and offline execution tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

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
from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    PRODUCTIVE_PARAMETER_MUTATION,
    PRODUCTIVE_TRADING_EFFECT,
    PROMOTION_PERFORMED,
    run_f2_research_backtest_cost_grid_offline_v1,
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
from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    ALLOWED_CALIBRATABLE_PARAMETERS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
F2_MODULE = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_f2_research_backtest_cost_grid_optimizable_surface_v1.py"
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


def test_f2_research_execution_grid_and_baseline() -> None:
    first = run_f2_research_backtest_cost_grid_offline_v1()
    second = run_f2_research_backtest_cost_grid_offline_v1()
    assert first["execution_digest"] == second["execution_digest"]
    assert first["combination_count"] == 9
    assert first["grid_id"] == GRID_ID
    assert first["baseline_fee_bps"] == BASELINE_FEE_BPS
    assert first["baseline_slippage_bps"] == BASELINE_SLIPPAGE_BPS
    baselines = [c for c in first["candidates"] if c["is_baseline"]]
    assert len(baselines) == 1
    assert baselines[0]["fee_bps"] == BASELINE_FEE_BPS
    assert baselines[0]["slippage_bps"] == BASELINE_SLIPPAGE_BPS
    assert first["productive_parameter_mutation"] is False
    assert first["promotion_performed"] is False
    assert first["external_effect_authorized"] is False
    assert first["productive_trading_effect"] == PRODUCTIVE_TRADING_EFFECT


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
