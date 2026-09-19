"""F2 research-only execution: envelope-bound okx_eth_perp cost grid identity and evidence."""

from __future__ import annotations

import itertools
from types import MappingProxyType
from typing import Any, Final, Mapping

import pandas as pd

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
    SOURCE_STEP29M_CONFIG,
)
from src.backtest.parameter_sensitivity_v1 import (
    PARAMETER_SENSITIVITY_OWNER,
    build_parameter_grid_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID,
    compute_f2_reproducibility_digest_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_f2_research_backtest_cost_grid_research_execution_v1"
EXECUTION_DOMAIN: Final[str] = (
    "peak_trade.canonical_f2_research_backtest_cost_grid_research_execution.v1"
)
RESEARCH_OPTIMIZATION_ONLY: Final[bool] = True
PRODUCTIVE_TRADING_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROMOTION_PERFORMED: Final[bool] = False
PRODUCTIVE_PARAMETER_MUTATION: Final[bool] = False

_OFFLINE_GIT_SHA: Final[str] = "25b0518b93f91a9609d70c30fb8cd3bf96401a46"[:40]


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _digest(label: str) -> str:
    return compute_content_sha256({"digest_label": label})


def _identity_request(
    *, fee_bps: float, slippage_bps: float
) -> CanonicalExperimentIdentityRequestV1:
    return CanonicalExperimentIdentityRequestV1(
        git_sha=_OFFLINE_GIT_SHA,
        working_tree_status=WORKING_TREE_CLEAN,
        strategy_identity=f"f2.cost_grid.{GRID_ID}",
        strategy_params={"fee_bps": fee_bps, "slippage_bps": slippage_bps},
        dataset_digest=_digest("f2-dataset"),
        feature_pipeline_digest=_digest("f2-features"),
        fee_model_digest=_digest(f"fee-{fee_bps}"),
        slippage_model_digest=_digest(f"slip-{slippage_bps}"),
        funding_model_digest=_digest("f2-funding-binding-only"),
        risk_policy_digest=_digest("f2-risk-frozen"),
        portfolio_digest=_digest("f2-portfolio"),
        split_policy_digest=_digest("f2-split"),
        market_context_contract_digest=_digest("f2-market-context"),
        bull_bear_logic_digest=_digest("f2-bull-bear"),
        state_switch_logic_digest=_digest("f2-state-switch"),
        survival_logic_digest=_digest("f2-survival"),
        suitability_logic_digest=_digest("f2-suitability"),
        double_play_logic_digest=_digest("f2-double-play"),
        entry_position_exit_logic_digest=_digest("f2-entry-exit"),
        seed=GRID_SEED,
        environment={"python_version": "3.11.14", "python_implementation": "CPython"},
        parent_lineage_ref=None,
        dirty_paths_digest=None,
    )


def _grid_spec() -> dict[str, Any]:
    return {
        "grid_id": GRID_ID,
        "grid_version": GRID_VERSION,
        "parameter_names": list(PARAMETER_NAMES),
        "parameter_values": [
            list(OPERATOR_BOUND_FEE_BPS),
            list(OPERATOR_BOUND_SLIPPAGE_BPS),
        ],
        "search_space_bounds": SEARCH_SPACE_BOUNDS,
        "seed": GRID_SEED,
    }


def run_f2_research_backtest_cost_grid_offline_v1(
    *,
    strategy_id: str = "ma_crossover",
    strategy_version: str = "v1",
    data_digest: str = "f2_offline_research_fixture_digest_v1",
    instrument_id: str = "okx:linear_perpetual:ETH:USDT:USDT:perp",
) -> MappingProxyType[str, Any]:
    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID)
    )
    if resolution["resolution"] != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise ValueError(f"F2_ENVELOPE_NOT_AUTHORIZED:{resolution.get('reason')}")

    timestamps = pd.date_range("2024-05-30T20:00:00Z", periods=32, freq="1h", tz="UTC")
    bars = pd.DataFrame(
        {
            "open": [100.0] * len(timestamps),
            "high": [101.0] * len(timestamps),
            "low": [99.0] * len(timestamps),
            "close": [100.0] * len(timestamps),
            "volume": [1000.0] * len(timestamps),
        },
        index=timestamps,
    )
    cfg: dict[str, Any] = {
        "backtest": {
            "fee_bps": BASELINE_FEE_BPS,
            "slippage_bps": BASELINE_SLIPPAGE_BPS,
            "parameter_sensitivity": {"grid": _grid_spec()},
        }
    }
    grid = build_parameter_grid_v1(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        cfg=cfg,
        bars=bars,
        data_digest=data_digest,
        instrument_id=instrument_id,
        grid_spec=_grid_spec(),
    )
    combinations = list(itertools.product(OPERATOR_BOUND_FEE_BPS, OPERATOR_BOUND_SLIPPAGE_BPS))
    candidate_identities: list[dict[str, Any]] = []
    for fee_bps, slippage_bps in combinations:
        identity = build_canonical_experiment_identity_v1(
            _identity_request(fee_bps=fee_bps, slippage_bps=slippage_bps)
        )
        candidate_identities.append(
            {
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "experiment_identity": dict(identity),
                "is_baseline": fee_bps == BASELINE_FEE_BPS
                and slippage_bps == BASELINE_SLIPPAGE_BPS,
                "proposal_only": True,
            }
        )

    serializable_candidates = [
        {
            "fee_bps": item["fee_bps"],
            "slippage_bps": item["slippage_bps"],
            "experiment_identity": _json_safe(item["experiment_identity"]),
            "is_baseline": item["is_baseline"],
            "proposal_only": item["proposal_only"],
        }
        for item in candidate_identities
    ]
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": EXECUTION_DOMAIN,
        "surface_id": SURFACE_ID,
        "envelope_resolution": _json_safe(resolution),
        "grid_id": grid.grid_id,
        "grid_digest": grid.grid_digest,
        "combination_count": grid.combination_count,
        "baseline_fee_bps": BASELINE_FEE_BPS,
        "baseline_slippage_bps": BASELINE_SLIPPAGE_BPS,
        "source_step29m_config_ref": SOURCE_STEP29M_CONFIG,
        "surface_reproducibility_digest": compute_f2_reproducibility_digest_v1(),
        "candidates": serializable_candidates,
        "research_optimization_only": RESEARCH_OPTIMIZATION_ONLY,
        "productive_trading_effect": PRODUCTIVE_TRADING_EFFECT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "promotion_performed": PROMOTION_PERFORMED,
        "productive_parameter_mutation": PRODUCTIVE_PARAMETER_MUTATION,
    }
    body["execution_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "execution_digest"}
    )
    return MappingProxyType(body)
