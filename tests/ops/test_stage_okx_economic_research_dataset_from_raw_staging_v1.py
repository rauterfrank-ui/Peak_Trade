"""RUNBOOK STEP 29M — OKX economic research dataset staging from raw cache v1 tests."""

from __future__ import annotations
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    located_runtime_evidence_20260520,
)

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from scripts.ops import stage_okx_economic_research_dataset_from_raw_staging_v1 as staging
from src.backtest import admissible_versioned_futures_dataset_v1 as ds


RAW_ROOT = Path(
    str(
        located_runtime_evidence_20260520()
        / "datasets/admissible_futures/inst-eth-usdt-perp/.tmp_20260701T100850Z"
    )
)


def _minimal_raw_tree(tmp_path: Path) -> Path:
    if not RAW_ROOT.is_dir():
        pytest.skip("authorized raw staging cache unavailable")
    dst = tmp_path / "raw_staging"
    shutil.copytree(RAW_ROOT, dst)
    return dst


class TestRawDigestVerification:
    def test_verify_raw_staging_digests_passes_on_authorized_cache(self) -> None:
        if not RAW_ROOT.is_dir():
            pytest.skip("authorized raw staging cache unavailable")
        report = staging.verify_raw_staging_digests(RAW_ROOT)
        assert report.verified
        assert report.mismatch_count == 0

    def test_digest_mismatch_fail_closed(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        tampered = raw_root / "raw" / "ohlcv_p0000_b6459852001951a4.json"
        tampered.write_text(tampered.read_text() + " ", encoding="utf-8")
        request_log = json.loads((raw_root / "reports" / "REQUEST_LOG.json").read_text())
        for entry in request_log:
            rel = Path(str(entry["raw_response_path"])).name
            entry["raw_response_path"] = str(raw_root / "raw" / rel)
        (raw_root / "reports" / "REQUEST_LOG.json").write_text(
            json.dumps(request_log, indent=2) + "\n", encoding="utf-8"
        )
        report = staging.verify_raw_staging_digests(raw_root)
        assert not report.verified
        assert report.mismatch_count >= 1


class TestNormalization:
    def test_normalize_produces_research_columns_only(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        config = json.loads((raw_root / "INGESTION_CONFIG.json").read_text())
        bars, report = staging.normalize_economic_research_bars(
            raw_dir=raw_root / "raw",
            start_utc=config["data_period"]["start_utc"],
            end_utc=config["data_period"]["end_utc"],
        )
        assert report.passed
        assert "best_bid" not in bars.columns
        assert "best_ask" not in bars.columns
        required = ds.required_bar_columns_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
        assert required.issubset(set(bars.columns))
        assert bars["is_final"].all()

    def test_normalize_materializes_volatility_estimate(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        config = json.loads((raw_root / "INGESTION_CONFIG.json").read_text())
        bars, report = staging.normalize_economic_research_bars(
            raw_dir=raw_root / "raw",
            start_utc=config["data_period"]["start_utc"],
            end_utc=config["data_period"]["end_utc"],
        )
        assert report.passed
        result = staging.vol_materializer.materialize_volatility_estimate_on_bars_v1(bars)
        frame = result.bars
        assert "volatility_estimate" in frame.columns
        assert frame["volatility_estimate"].notna().any()
        assert (
            frame["volatility_estimate_contract_version"].iloc[-1]
            == staging.vol_contract.CONTRACT_VERSION
        )


class TestCostBinding:
    def test_positive_cost_binding_no_zero_cost(self) -> None:
        binding = staging.build_cost_model_binding()
        assert binding["fee_bps"] > 0
        assert binding["slippage_bps"] > 0
        assert binding["conservative_half_spread_bps"] > 0
        assert binding["effective_entry_cost_bps"] > binding["fee_bps"]
        assert binding["roundtrip_cost_bps"] > 2 * binding["fee_bps"]


class TestStagingIntegration:
    def test_staging_from_raw_cache_no_network(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        target = tmp_path / "datasets" / "inst-eth-usdt-perp" / "v1"
        evidence = tmp_path / "evidence"
        result = staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=raw_root,
            target_dataset_root=target,
            durable_evidence_root=evidence,
        )
        assert result["verdict"] == "OKX_ECONOMIC_RESEARCH_DATASET_STAGING_COMPLETE"
        assert target.is_dir()
        assert (target / "bars.parquet").is_file()
        manifest = json.loads((target / "dataset_manifest.json").read_text())
        assert manifest["dataset_profile"] == "economic_research_v1"
        assert manifest["l1_observation_status"] == "EXECUTION_MODEL_BOUND_NOT_OBSERVED"
        assert manifest["observed_l1_used"] is False
        assert manifest["manifest_digest"]

    def test_runtime_profile_rejects_staged_dataset(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        target = tmp_path / "datasets" / "inst-eth-usdt-perp" / "v1"
        staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=raw_root,
            target_dataset_root=target,
            durable_evidence_root=tmp_path / "evidence",
        )
        bars = pd.read_parquet(target / "bars.parquet")
        bars.index = pd.to_datetime(bars["timestamp"], utc=True)
        bars = bars.drop(columns=["timestamp"])
        bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
        digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
        train, val, oos = ds.compute_split_periods_from_bars(bars)
        idx = bars.sort_index().index
        descriptor = ds.VersionedFuturesDatasetDescriptorV1(
            dataset_id="test",
            dataset_version="v1",
            dataset_schema_version=ds.DATASET_SCHEMA_VERSION,
            dataset_digest=digest,
            instrument_id=staging.okx_ingest.CANONICAL_INSTRUMENT_ID,
            contract_type="perpetual",
            futures_only=True,
            bitcoin_direction_allowed=False,
            venue_id="OKX",
            start_time=str(idx[0]),
            end_time=str(idx[-1]),
            row_count=len(bars),
            field_bindings=bindings,
            training_period=train,
            validation_period=val,
            out_of_sample_period=oos,
            split_policy_version=ds.SPLIT_POLICY_VERSION,
            timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
            timezone=ds.TIMEZONE,
            ordering_status=ds.ORDERING_STATUS_SORTED,
            duplicate_policy=ds.DUPLICATE_POLICY,
            missing_data_policy=ds.MISSING_DATA_POLICY,
        )
        provenance = ds.DatasetProvenanceV1(
            source_type="operator_staged_futures_v1",
            venue_id="OKX",
            ingestion_timestamp="2026-07-01T10:10:12Z",
            generation_method="test",
            provenance_ref=str(target / "PROVENANCE.json"),
        )
        runtime = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=descriptor,
            provenance=provenance,
            instrument_id=staging.okx_ingest.CANONICAL_INSTRUMENT_ID,
            profile_binding=ds.default_runtime_profile_binding_v1(),
        )
        assert (
            runtime.admissibility_status is ds.AdmissibilityStatus.BLOCKED_L1_REQUIRED_FOR_RUNTIME
        )

    def test_existing_target_not_overwritten(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        target = tmp_path / "datasets" / "inst-eth-usdt-perp" / "v1"
        evidence = tmp_path / "evidence"
        first = staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=raw_root,
            target_dataset_root=target,
            durable_evidence_root=evidence,
        )
        assert first["verdict"] == "OKX_ECONOMIC_RESEARCH_DATASET_STAGING_COMPLETE"
        manifest_path = target / "dataset_manifest.json"
        original_digest = json.loads(manifest_path.read_text())["normalized_dataset_digest"]
        tampered = json.loads(manifest_path.read_text())
        tampered["normalized_dataset_digest"] = "0" * 64
        manifest_path.write_text(json.dumps(tampered, indent=2) + "\n")
        second_root = tmp_path / "raw_staging_copy"
        shutil.copytree(raw_root, second_root)
        second = staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=second_root,
            target_dataset_root=target,
            durable_evidence_root=evidence,
        )
        assert second["verdict"] == "OKX_ECONOMIC_RESEARCH_DATASET_STAGING_COMPLETE"
        assert second["dataset_version"] == "v2"
        v2_manifest = json.loads((target.parent / "v2" / "dataset_manifest.json").read_text())
        assert v2_manifest["normalized_dataset_digest"] == original_digest
        still_tampered = json.loads(manifest_path.read_text())
        assert still_tampered["normalized_dataset_digest"] == "0" * 64

    def test_confirm_token_required(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            staging.run_economic_research_staging_from_raw(
                confirm="WRONG",
                raw_staging_root=tmp_path,
                target_dataset_root=tmp_path / "v1",
                durable_evidence_root=tmp_path,
            )

    def test_split_binding_disjoint(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        target = tmp_path / "datasets" / "inst-eth-usdt-perp" / "v1"
        staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=raw_root,
            target_dataset_root=target,
            durable_evidence_root=tmp_path / "evidence",
        )
        split = json.loads((target / "SPLIT_BINDING.json").read_text())
        assert split["disjoint"] is True
        assert split["leakage_free"] is True


_NON_ETH_NATIVE = "0G-USDT-SWAP"
_NON_ETH_CANONICAL = "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap"
_NON_ETH_SELECTION_ID = "ssf_7614cb32f5bac2c25ac1ef08"
_NON_ETH_SELECTION_DIGEST = "abc123selectiondigest"


def _non_eth_binding(**overrides: object) -> dict:
    payload = {
        "native_instrument_id": _NON_ETH_NATIVE,
        "canonical_instrument_id": _NON_ETH_CANONICAL,
        "selection_id": _NON_ETH_SELECTION_ID,
        "selection_integrity_digest": _NON_ETH_SELECTION_DIGEST,
        "validated": True,
        "venue": "OKX",
        "instrument_metadata": {
            "instId": _NON_ETH_NATIVE,
            "canonical_instrument_id": _NON_ETH_CANONICAL,
            "canonical_contract_type": "perpetual",
        },
    }
    payload.update(overrides)
    return payload


def _non_eth_ingestion_config(**overrides: object) -> dict:
    payload = {
        "native_instrument_id": _NON_ETH_NATIVE,
        "canonical_instrument_id": _NON_ETH_CANONICAL,
        "data_period": {"start_utc": "2026-01-01T00:00:00Z", "end_utc": "2026-01-02T00:00:00Z"},
    }
    payload.update(overrides)
    return payload


class TestDynamicInstrumentIdentityBinding:
    def test_authority_flags_remain_false(self) -> None:
        assert staging.ECONOMIC_RESEARCH_STAGING_SELECTION_AUTHORITY is False
        assert staging.ECONOMIC_RESEARCH_STAGING_TRADING_AUTHORITY is False
        assert staging.ECONOMIC_RESEARCH_STAGING_MAY_RESELECT is False
        assert staging.ECONOMIC_RESEARCH_STAGING_MAY_SUBSTITUTE_INSTRUMENT is False

    def test_dynamic_non_eth_identity_passes_unchanged(self, tmp_path: Path) -> None:
        identity = staging.resolve_economic_research_staging_instrument_identity_v1(
            instrument_binding=_non_eth_binding(),
            ingestion_config=_non_eth_ingestion_config(),
            instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
        )
        assert identity.native_instrument_id == _NON_ETH_NATIVE
        assert identity.canonical_instrument_id == _NON_ETH_CANONICAL
        assert identity.selection_id == _NON_ETH_SELECTION_ID
        assert identity.selection_integrity_digest == _NON_ETH_SELECTION_DIGEST
        assert identity.native_instrument_id != staging.okx_ingest.NATIVE_INSTRUMENT_ID
        assert identity.canonical_instrument_id != staging.okx_ingest.CANONICAL_INSTRUMENT_ID

    def test_native_identity_mismatch_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(
            staging.StagingError, match="instrument_binding_native_ingestion_config_mismatch"
        ):
            staging.resolve_economic_research_staging_instrument_identity_v1(
                instrument_binding=_non_eth_binding(),
                ingestion_config=_non_eth_ingestion_config(native_instrument_id="ETH-USDT-SWAP"),
                instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
            )

    def test_canonical_identity_mismatch_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(
            staging.StagingError,
            match="instrument_binding_canonical_ingestion_config_mismatch",
        ):
            staging.resolve_economic_research_staging_instrument_identity_v1(
                instrument_binding=_non_eth_binding(),
                ingestion_config=_non_eth_ingestion_config(
                    canonical_instrument_id="inst-eth-usdt-perp"
                ),
                instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
            )

    def test_metadata_native_mismatch_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(
            staging.StagingError, match="instrument_binding_metadata_native_mismatch"
        ):
            staging.resolve_economic_research_staging_instrument_identity_v1(
                instrument_binding=_non_eth_binding(
                    instrument_metadata={
                        "instId": "ETH-USDT-SWAP",
                        "canonical_instrument_id": _NON_ETH_CANONICAL,
                        "canonical_contract_type": "perpetual",
                    }
                ),
                ingestion_config=_non_eth_ingestion_config(),
                instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
            )

    def test_missing_instrument_binding_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_root = tmp_path / "raw_staging"
        raw_root.mkdir()
        (raw_root / "INGESTION_CONFIG.json").write_text(
            json.dumps(_non_eth_ingestion_config()) + "\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            staging,
            "verify_raw_staging_digests",
            lambda *args, **kwargs: staging.RawDigestVerification(True, 1, 0, ()),
        )
        with pytest.raises(staging.StagingError, match="instrument_binding_missing"):
            staging.run_economic_research_staging_from_raw(
                confirm=staging.CONFIRM_GO,
                raw_staging_root=raw_root,
                target_dataset_root=tmp_path / "v1",
                durable_evidence_root=tmp_path / "evidence",
            )

    def test_malformed_instrument_binding_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_root = tmp_path / "raw_staging"
        raw_root.mkdir()
        (raw_root / "INGESTION_CONFIG.json").write_text(
            json.dumps(_non_eth_ingestion_config()) + "\n", encoding="utf-8"
        )
        (raw_root / "INSTRUMENT_BINDING.json").write_text("{not-json", encoding="utf-8")
        monkeypatch.setattr(
            staging,
            "verify_raw_staging_digests",
            lambda *args, **kwargs: staging.RawDigestVerification(True, 1, 0, ()),
        )
        with pytest.raises(staging.StagingError, match="instrument_binding_malformed"):
            staging.run_economic_research_staging_from_raw(
                confirm=staging.CONFIRM_GO,
                raw_staging_root=raw_root,
                target_dataset_root=tmp_path / "v1",
                durable_evidence_root=tmp_path / "evidence",
            )

    def test_unvalidated_binding_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(staging.StagingError, match="instrument_binding_not_validated"):
            staging.resolve_economic_research_staging_instrument_identity_v1(
                instrument_binding=_non_eth_binding(validated=False),
                ingestion_config=_non_eth_ingestion_config(),
                instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
            )

    def test_no_eth_fallback_on_valid_non_eth_binding(self, tmp_path: Path) -> None:
        identity = staging.resolve_economic_research_staging_instrument_identity_v1(
            instrument_binding=_non_eth_binding(),
            ingestion_config=_non_eth_ingestion_config(),
            instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
        )
        assert "ETH" not in identity.native_instrument_id
        assert "eth" not in identity.canonical_instrument_id.lower()
        assert identity.canonical_instrument_id == _NON_ETH_CANONICAL

    def test_selection_provenance_fields_preserved(self, tmp_path: Path) -> None:
        identity = staging.resolve_economic_research_staging_instrument_identity_v1(
            instrument_binding=_non_eth_binding(),
            ingestion_config=_non_eth_ingestion_config(),
            instrument_binding_path=tmp_path / "INSTRUMENT_BINDING.json",
        )
        assert identity.selection_id == _NON_ETH_SELECTION_ID
        assert identity.selection_integrity_digest == _NON_ETH_SELECTION_DIGEST

    def test_staging_manifest_uses_binding_not_module_constants(self, tmp_path: Path) -> None:
        raw_root = _minimal_raw_tree(tmp_path)
        binding = json.loads((raw_root / "INSTRUMENT_BINDING.json").read_text(encoding="utf-8"))
        target = tmp_path / "datasets" / "from_binding" / "v1"
        result = staging.run_economic_research_staging_from_raw(
            confirm=staging.CONFIRM_GO,
            raw_staging_root=raw_root,
            target_dataset_root=target,
            durable_evidence_root=tmp_path / "evidence",
        )
        assert result["verdict"] == "OKX_ECONOMIC_RESEARCH_DATASET_STAGING_COMPLETE"
        manifest = json.loads((target / "dataset_manifest.json").read_text(encoding="utf-8"))
        provenance = json.loads((target / "PROVENANCE.json").read_text(encoding="utf-8"))
        assert manifest["native_instrument_id"] == binding["native_instrument_id"]
        assert manifest["instrument_id"] == binding["canonical_instrument_id"]
        assert provenance["native_instrument_id"] == binding["native_instrument_id"]
        assert provenance["canonical_instrument_id"] == binding["canonical_instrument_id"]
        assert provenance["selection_id"] == binding.get("selection_id", "")
        assert manifest["instrument_identity_source"] == "INSTRUMENT_BINDING.json"
        assert result["native_instrument_id"] == binding["native_instrument_id"]
        assert result["canonical_instrument_id"] == binding["canonical_instrument_id"]
