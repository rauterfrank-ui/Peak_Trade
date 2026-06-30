from __future__ import annotations

import json
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import economic_viability_evidence_v1 as ev
from src.backtest import mv2_research_wiring_v1 as wiring


def _cfg(*, fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }


def _bars(n: int = 20) -> pd.DataFrame:
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
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def _admissibility(bars: pd.DataFrame) -> ev.DataAdmissibilityV1:
    return ev.DataAdmissibilityV1(
        source_kind=ev.DataSourceKind.SYNTHETIC_CONTRACT_FIXTURE,
        instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
        data_digest=ev.compute_bars_data_digest(bars),
        data_ref="tests/backtest/test_economic_viability_evidence_v1.py::_bars",
    )


def _build(**kwargs: Any) -> ev.EconomicViabilityEvidenceV1:
    bars = kwargs.pop("bars", _bars())
    return ev.build_economic_viability_evidence_v1(
        bars=bars,
        data_admissibility=kwargs.pop("data_admissibility", _admissibility(bars)),
        strategy_id=kwargs.pop("strategy_id", "ma_crossover"),
        cfg=kwargs.pop("cfg", _cfg()),
        **kwargs,
    )


def test_contract_layer_version() -> None:
    assert ev.ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION == "v1"


def test_policy_not_bound_fail_closed() -> None:
    assert ev.ECONOMIC_VIABILITY_POLICY_VERSION == "NOT_BOUND"


def test_build_evidence_research_only_for_synthetic_fixture() -> None:
    result = _build()
    assert result.status is ev.EconomicViabilityStatus.RESEARCH_ONLY
    assert result.economic_validity_proven is False
    assert result.profitability_claim_allowed is False
    assert "admissible_versioned_futures_dataset_missing" in result.reason_codes
    assert "economic_viability_policy_not_versioned" in result.reason_codes


def test_build_evidence_deterministic_semantics() -> None:
    a = _build()
    b = _build()
    assert a.to_semantic_dict() == b.to_semantic_dict()
    assert a.manifest_digest == b.manifest_digest


def test_data_digest_mismatch_fail_closed() -> None:
    bars = _bars()
    bad = ev.DataAdmissibilityV1(
        source_kind=ev.DataSourceKind.SYNTHETIC_CONTRACT_FIXTURE,
        instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
        data_digest="0" * 64,
        data_ref="bad",
    )
    with pytest.raises(ev.EconomicViabilityEvidenceError, match="data_digest_mismatch"):
        _build(bars=bars, data_admissibility=bad)


def test_forbidden_bitcoin_instrument_rejected() -> None:
    bars = _bars()
    with pytest.raises(ev.EconomicViabilityEvidenceError, match="instrument_kind_forbidden"):
        ev.build_economic_viability_evidence_v1(
            bars=bars,
            data_admissibility=_admissibility(bars),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            instrument_id="inst-btc-usdt-perp",
        )


def test_zero_cost_without_flag_rejected() -> None:
    with pytest.raises(Exception):
        _build(cfg=_cfg(fee_bps=0.0, slippage_bps=0.0))


def test_zero_cost_explicit_flag_sets_reason_code() -> None:
    result = _build(cfg=_cfg(fee_bps=0.0, slippage_bps=0.0), explicit_zero_cost_non_economic=True)
    assert "explicit_zero_cost_non_economic_mode" in result.reason_codes


def test_required_metric_fields_present() -> None:
    result = _build()
    payload = result.to_dict()
    for key in ev.economic_viability_evidence_schema_v1()["required_fields"]:
        assert key in payload


def test_not_computed_metrics_not_zero_filled() -> None:
    result = _build()
    assert result.turnover.semantic is ev.MetricSemantic.NOT_COMPUTED
    assert result.turnover.value is None
    assert result.funding_drag.reason_code == "funding_drag_not_bound"


def test_walk_forward_monte_carlo_stress_sections_present() -> None:
    result = _build()
    assert "window_count" in result.walk_forward_results
    assert "num_runs" in result.monte_carlo_results
    assert "class_statuses" in result.stress_results


def test_mv2_chain_digest_present() -> None:
    result = _build()
    assert len(result.wiring_chain_digest) == 64


def test_cost_binding_present() -> None:
    result = _build()
    assert result.cost_binding["economic_interpretation_allowed"] is False
    assert result.fee_model_version
    assert result.slippage_model_version


def test_schema_contract() -> None:
    schema = ev.economic_viability_evidence_schema_v1()
    assert schema["contract_name"] == "economic_viability_evidence_v1"
    assert schema["runtime_effect"] is False


def test_persist_bundle_manifest_verify(tmp_path) -> None:
    result = _build()
    out = tmp_path / "evidence"
    bundle = ev.persist_economic_viability_evidence_bundle_v1(
        out,
        result,
        config_snapshot={"cfg": dict(_cfg())},
        metrics={"total_return": result.gross_return.value},
        input_provenance={"source": "synthetic_fixture"},
    )
    assert bundle.manifest_verify_rc == 0
    assert bundle.evidence_path.is_file()
    loaded = json.loads(bundle.evidence_path.read_text(encoding="utf-8"))
    assert loaded["status"] == "RESEARCH_ONLY"


def test_inadmissible_data_source_reason_code() -> None:
    bars = _bars()
    adm = ev.DataAdmissibilityV1(
        source_kind=ev.DataSourceKind.INADMISSIBLE,
        instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
        data_digest=ev.compute_bars_data_digest(bars),
        data_ref="inadmissible",
    )
    result = _build(bars=bars, data_admissibility=adm)
    assert "data_source_inadmissible" in result.reason_codes


def test_walk_forward_insufficient_bars_reason() -> None:
    bars = _bars(10)
    result = _build(bars=bars)
    assert "walk_forward_insufficient_bars" in result.reason_codes


def test_parameter_sensitivity_not_computed() -> None:
    result = _build()
    assert result.parameter_sensitivity_results["semantic"] == "NOT_COMPUTED"


def test_status_never_exceeds_step29m_allowed_set() -> None:
    result = _build()
    assert result.status.value in ev._STEP29M_ALLOWED_STATUSES


def test_economically_viable_offline_not_claimed_without_policy() -> None:
    result = _build()
    assert result.status is not ev.EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE
