"""RUNBOOK STEP 29M — admissible versioned futures dataset binding v1 tests."""

from __future__ import annotations

import copy
import json
from typing import Any, Mapping

import pandas as pd
import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest import economic_viability_evidence_v1 as ev
from src.backtest import mv2_research_wiring_v1 as wiring


def _bars(n: int = 24) -> pd.DataFrame:
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


def _provenance(**overrides: Any) -> ds.DatasetProvenanceV1:
    payload = {
        "source_type": "synthetic_contract_fixture",
        "venue_id": "offline_fixture_venue_v1",
        "ingestion_timestamp": "1970-01-01T00:00:00+00:00",
        "generation_method": "deterministic_test_fixture",
        "provenance_ref": "tests/backtest/test_admissible_versioned_futures_dataset_v1.py",
    }
    payload.update(overrides)
    return ds.DatasetProvenanceV1(**payload)


def _descriptor(bars: pd.DataFrame, **overrides: Any) -> ds.VersionedFuturesDatasetDescriptorV1:
    bindings = ds.default_field_bindings_v1()
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    train, val, oos = ds.compute_split_periods_from_bars(bars)
    idx = bars.sort_index().index
    payload: dict[str, Any] = {
        "dataset_id": "step29m_fixture_eth_perp_v1",
        "dataset_version": ds.DEFAULT_DATASET_VERSION,
        "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
        "dataset_digest": digest,
        "instrument_id": wiring.MV2_REQUIRED_INSTRUMENT_ID,
        "contract_type": "perpetual",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "venue_id": "offline_fixture_venue_v1",
        "start_time": str(idx[0]),
        "end_time": str(idx[-1]),
        "row_count": len(bars),
        "field_bindings": bindings,
        "training_period": train,
        "validation_period": val,
        "out_of_sample_period": oos,
        "split_policy_version": ds.SPLIT_POLICY_VERSION,
        "timestamp_semantics": ds.TIMESTAMP_SEMANTICS,
        "timezone": ds.TIMEZONE,
        "ordering_status": ds.ORDERING_STATUS_SORTED,
        "duplicate_policy": ds.DUPLICATE_POLICY,
        "missing_data_policy": ds.MISSING_DATA_POLICY,
    }
    payload.update(overrides)
    field_bindings = payload.pop("field_bindings")
    if isinstance(field_bindings, ds.DatasetFieldBindingsV1):
        bindings = field_bindings
    else:
        bindings = ds.DatasetFieldBindingsV1(**field_bindings)
    return ds.VersionedFuturesDatasetDescriptorV1(field_bindings=bindings, **payload)


def _evaluate(
    bars: pd.DataFrame | None = None, **overrides: Any
) -> ds.AdmissibleVersionedFuturesDatasetResultV1:
    frame = _bars() if bars is None else bars
    descriptor_overrides = overrides.pop("descriptor_overrides", {})
    provenance_overrides = overrides.pop("provenance_overrides", {})
    instrument_id = overrides.pop("instrument_id", wiring.MV2_REQUIRED_INSTRUMENT_ID)
    descriptor = _descriptor(frame, **descriptor_overrides)
    provenance = _provenance(**provenance_overrides)
    return ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=frame,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=instrument_id,
    )


def _cfg_with_dataset(bars: pd.DataFrame, **descriptor_overrides: Any) -> Mapping[str, Any]:
    descriptor = _descriptor(bars, **descriptor_overrides)
    provenance = _provenance()
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "dataset_admissibility": {
                "bind": True,
                "dataset": descriptor.to_dict(),
                "provenance": provenance.to_dict(),
            },
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }


class TestAdmissibleVersionedFuturesDatasetContract:
    def test_binding_requested(self) -> None:
        bars = _bars()
        assert ds.dataset_admissibility_binding_requested(_cfg_with_dataset(bars)) is True
        assert ds.dataset_admissibility_binding_requested({"backtest": {}}) is False

    def test_fully_versioned_futures_dataset_admissible(self) -> None:
        result = _evaluate()
        assert result.admissibility_status is ds.AdmissibilityStatus.ADMISSIBLE
        assert result.is_admissible() is True
        assert result.leakage_check_status == "PASS"
        assert result.mutation_check_status == "PASS"
        assert result.futures_only is True
        assert result.bitcoin_direction_allowed is False

    def test_missing_dataset_version_fail_closed(self) -> None:
        result = _evaluate(descriptor_overrides={"dataset_version": ""})
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_MISSING_VERSION

    def test_missing_dataset_digest_fail_closed(self) -> None:
        result = _evaluate(descriptor_overrides={"dataset_digest": ""})
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_MISSING_DIGEST

    def test_digest_mismatch_fail_closed(self) -> None:
        result = _evaluate(descriptor_overrides={"dataset_digest": "0" * 64})
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_DATA_MUTATION

    def test_missing_provenance_fail_closed(self) -> None:
        result = _evaluate(provenance_overrides={"provenance_ref": ""})
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_PROVENANCE_MISSING

    def test_spot_dataset_fail_closed(self) -> None:
        result = _evaluate(
            descriptor_overrides={"contract_type": "spot", "futures_only": False},
            provenance_overrides={"source_type": "spot"},
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_NON_FUTURES_DATA

    def test_bitcoin_direction_fail_closed(self) -> None:
        result = _evaluate(
            descriptor_overrides={
                "instrument_id": "inst-btc-usdt-perp",
                "bitcoin_direction_allowed": True,
            }
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_BITCOIN_DIRECTION

    def test_training_oos_overlap_fail_closed(self) -> None:
        bars = _bars()
        train, _, oos = ds.compute_split_periods_from_bars(bars)
        result = _evaluate(
            bars,
            descriptor_overrides={"training_period": train, "out_of_sample_period": train},
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_SPLIT_OVERLAP

    def test_validation_oos_overlap_fail_closed(self) -> None:
        bars = _bars()
        _, val, _ = ds.compute_split_periods_from_bars(bars)
        result = _evaluate(
            bars,
            descriptor_overrides={"validation_period": val, "out_of_sample_period": val},
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_SPLIT_OVERLAP

    def test_temporal_leakage_fail_closed(self) -> None:
        bars = _bars()
        idx = bars.sort_index().index
        bad_train = f"{idx[0]}..{idx[-2]}"
        bad_oos = f"{idx[1]}..{idx[-1]}"
        result = _evaluate(
            bars,
            descriptor_overrides={
                "training_period": bad_train,
                "out_of_sample_period": bad_oos,
            },
        )
        assert result.admissibility_status in {
            ds.AdmissibilityStatus.BLOCKED_TEMPORAL_LEAKAGE,
            ds.AdmissibilityStatus.BLOCKED_SPLIT_OVERLAP,
        }

    def test_unsorted_events_fail_closed(self) -> None:
        bars = _bars().sort_index(ascending=False)
        result = _evaluate(bars)
        assert (
            result.admissibility_status
            is ds.AdmissibilityStatus.BLOCKED_UNSORTED_OR_DUPLICATE_EVENTS
        )

    def test_duplicate_events_fail_closed(self) -> None:
        bars = _bars()
        dup = pd.concat([bars.iloc[:1], bars])
        result = _evaluate(dup)
        assert (
            result.admissibility_status
            is ds.AdmissibilityStatus.BLOCKED_UNSORTED_OR_DUPLICATE_EVENTS
        )

    def test_missing_required_futures_fields_fail_closed(self) -> None:
        bars = _bars().drop(columns=["funding_rate"])
        result = _evaluate(bars)
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_REQUIRED_FIELD_MISSING

    def test_deterministic_repeat(self) -> None:
        a = _evaluate()
        b = _evaluate()
        assert a.to_dict() == b.to_dict()
        assert a.evidence_digest() == b.evidence_digest()

    def test_manifest_binding_pass(self, tmp_path) -> None:
        result = _evaluate()
        payload = ds.serialize_dataset_admissibility_binding_v1(result)
        out = tmp_path / "dataset_binding"
        out.mkdir()
        artifact = out / "DATASET_ADMISSIBILITY_BINDING.json"
        artifact.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        write_manifest_sha256(out)
        ok, _message = verify_manifest_sha256(out)
        assert ok is True


class TestEconomicViabilityDatasetIntegration:
    def _admissible_data(self, bars: pd.DataFrame) -> ev.DataAdmissibilityV1:
        return ev.DataAdmissibilityV1(
            source_kind=ev.DataSourceKind.VERSIONED_CANONICAL_FUTURES,
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            data_digest=ev.compute_bars_data_digest(bars),
            data_ref="tests/admissible_fixture",
            versioned_dataset_id="step29m_fixture_eth_perp_v1",
        )

    def test_evidence_without_admissible_dataset_stays_research_only(self) -> None:
        bars = _bars()
        result = ev.build_economic_viability_evidence_v1(
            bars=bars,
            data_admissibility=ev.DataAdmissibilityV1(
                source_kind=ev.DataSourceKind.SYNTHETIC_CONTRACT_FIXTURE,
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
                data_digest=ev.compute_bars_data_digest(bars),
                data_ref="synthetic",
            ),
            strategy_id="ma_crossover",
            cfg={
                "backtest": {"initial_cash": 10_000.0, "fee_bps": 10.0, "slippage_bps": 5.0},
                "risk": {},
            },
        )
        assert result.status is ev.EconomicViabilityStatus.RESEARCH_ONLY
        assert result.economic_validity_proven is False
        assert "admissible_versioned_futures_dataset_missing" in result.reason_codes

    def test_evidence_with_admissible_binding_not_economically_viable(self) -> None:
        bars = _bars()
        result = ev.build_economic_viability_evidence_v1(
            bars=bars,
            data_admissibility=self._admissible_data(bars),
            strategy_id="ma_crossover",
            cfg=_cfg_with_dataset(bars),
        )
        assert result.data_admissibility["admissibility_status"] == "ADMISSIBLE"
        assert result.data_admissibility["binding_status"] == "PASS"
        assert "admissible_versioned_futures_dataset_bound" in result.reason_codes
        assert "admissible_versioned_futures_dataset_missing" not in result.reason_codes
        assert result.status is not ev.EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE
        assert result.economic_validity_proven is False
        assert result.profitability_claim_allowed is False

    def test_profitability_claim_remains_forbidden(self) -> None:
        bars = _bars()
        result = ev.build_economic_viability_evidence_v1(
            bars=bars,
            data_admissibility=self._admissible_data(bars),
            strategy_id="ma_crossover",
            cfg=_cfg_with_dataset(bars),
        )
        assert result.profitability_claim_allowed is False

    def test_trading_semantics_unchanged(self) -> None:
        bars = _bars()
        result = ev.build_economic_viability_evidence_v1(
            bars=bars,
            data_admissibility=self._admissible_data(bars),
            strategy_id="ma_crossover",
            cfg=_cfg_with_dataset(bars),
        )
        assert result.futures_only is True
        assert result.bitcoin_direction_allowed is False
        assert result.runtime_effect is False
        assert result.order_effect is False

    def test_forbidden_instrument_raises(self) -> None:
        bars = _bars()
        cfg = _cfg_with_dataset(bars)
        cfg = copy.deepcopy(dict(cfg))
        cfg["backtest"]["dataset_admissibility"]["dataset"]["instrument_id"] = "inst-btc-usdt-perp"
        with pytest.raises(ev.EconomicViabilityEvidenceError, match="instrument_kind_forbidden"):
            ev.build_economic_viability_evidence_v1(
                bars=bars,
                data_admissibility=self._admissible_data(bars),
                strategy_id="ma_crossover",
                cfg=cfg,
                instrument_id="inst-btc-usdt-perp",
            )
