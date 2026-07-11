"""Contract tests for OKX self-accumulated forward open-interest archive v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    SCOPE_STATUS,
    is_historical_backfill_allowed,
    is_scope_parked,
    is_self_accumulated_archive_allowed,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    OkxLifecycleSourceErrorCode,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_SCHEMA_VERSION,
    COLLECTION_MODE_BACKFILL,
    COLLECTION_MODE_FORWARD_ONLY,
    CONFIRM_GO,
    MODULE_VERSION,
    OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
    RESEARCH_SCOPE,
    ArchiveAppendVerdict,
    GapStalenessStatus,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    assess_gap_and_staleness_v0,
    assert_archive_preconditions_v0,
    build_archive_config_v0,
    build_overlap_validation_readiness_v0,
    compute_implementation_digest_v0,
    compute_observation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    validate_instrument_for_forward_archive_v0,
    write_manifest_sha256_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/okx_self_accumulated_forward_open_interest_archive_v0.json"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)

ETH_INST = {
    "instId": "ETH-USDT-SWAP",
    "instType": "SWAP",
    "uly": "ETH-USDT",
    "state": "live",
    "settleCcy": "USDT",
    "listTime": "1609459200000",
    "ctType": "linear",
    "expTime": "",
}
BTC_INST = {
    "instId": "BTC-USDT-SWAP",
    "instType": "SWAP",
    "uly": "BTC-USDT",
    "state": "live",
    "settleCcy": "USDT",
    "listTime": "1609459200000",
    "ctType": "linear",
    "expTime": "",
}
SPOT_INST = {
    "instId": "ETH-USDT",
    "instType": "SPOT",
    "uly": "ETH-USDT",
    "state": "live",
    "listTime": "1609459200000",
}


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str = "1000.0") -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _eth_state() -> InstrumentArchiveStateV0:
    return InstrumentArchiveStateV0(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
    )


class TestArchivePreconditionsAndConfig:
    def test_scope_parked_but_self_accumulated_archive_allowed(self) -> None:
        assert is_scope_parked()
        assert is_self_accumulated_archive_allowed()
        assert not is_historical_backfill_allowed()
        assert_archive_preconditions_v0()

    def test_config_on_disk_matches_module_constants(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_archive_config_v0()
        assert config["research_scope"] == RESEARCH_SCOPE
        assert config["scope_status"] == SCOPE_STATUS
        assert config["go_token"] == CONFIRM_GO
        assert config["archive_schema_version"] == ARCHIVE_SCHEMA_VERSION
        assert config["collection_mode"] == COLLECTION_MODE_FORWARD_ONLY
        assert config["historical_backfill_allowed"] is False
        assert config["overlap_validation_status"] == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED
        assert module_config["implementation_digest"] == compute_implementation_digest_v0()

    def test_implementation_digest_deterministic(self) -> None:
        assert compute_implementation_digest_v0() == compute_implementation_digest_v0()

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/okx_self_accumulated_forward_open_interest_archive_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestInstrumentEligibility:
    def test_futures_eth_eligible(self) -> None:
        ok, inst_id, reason = validate_instrument_for_forward_archive_v0(ETH_INST)
        assert ok is True
        assert inst_id is not None
        assert reason is None

    def test_bitcoin_excluded(self) -> None:
        ok, inst_id, reason = validate_instrument_for_forward_archive_v0(BTC_INST)
        assert ok is False
        assert inst_id is None
        assert reason == OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value

    def test_spot_excluded(self) -> None:
        ok, inst_id, reason = validate_instrument_for_forward_archive_v0(SPOT_INST)
        assert ok is False
        assert inst_id is None


class TestNormalizationAndPitProvenance:
    def test_normalize_forward_observation_with_provenance(self) -> None:
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z", "1234.5"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert obs is not None
        assert obs.venue_timestamp_utc == "2026-07-11T10:00:00Z"
        assert obs.collected_at_utc == "2026-07-11T11:00:00Z"
        assert obs.bar_interval == "PT1H"
        assert obs.collection_mode == COLLECTION_MODE_FORWARD_ONLY
        assert obs.observation_digest == compute_observation_digest_v0(
            {
                "instrument_id": obs.instrument_id,
                "native_instrument_id": obs.native_instrument_id,
                "venue_timestamp_ms": obs.venue_timestamp_ms,
                "venue_timestamp_utc": obs.venue_timestamp_utc,
                "collected_at_ms": obs.collected_at_ms,
                "collected_at_utc": obs.collected_at_utc,
                "open_interest_raw": obs.open_interest_raw,
                "open_interest_unit": obs.open_interest_unit,
                "bar_interval": obs.bar_interval,
                "source_schema_version": obs.source_schema_version,
                "source_endpoint": obs.source_endpoint,
                "source_record_key": obs.source_record_key,
                "collection_mode": obs.collection_mode,
            }
        )

    def test_lookahead_rejected_when_venue_after_collected(self) -> None:
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T12:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert obs is None


class TestAppendDeduplicationAndConflict:
    def test_append_and_idempotent_duplicate(self) -> None:
        state = _eth_state()
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert obs is not None
        first = append_forward_observation_v0(state, obs, preconditions_checked=True)
        second = append_forward_observation_v0(state, obs, preconditions_checked=True)
        assert first.verdict == ArchiveAppendVerdict.APPENDED
        assert second.verdict == ArchiveAppendVerdict.DUPLICATE_SKIPPED
        assert len(state.observations) == 1

    def test_conflict_rejected_no_overwrite(self) -> None:
        state = _eth_state()
        base = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z", "1000.0"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert base is not None
        append_forward_observation_v0(state, base, preconditions_checked=True)
        conflicting = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z", "2000.0"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T12:00:00Z",
        )
        assert conflicting is not None
        result = append_forward_observation_v0(state, conflicting, preconditions_checked=True)
        assert result.verdict == ArchiveAppendVerdict.CONFLICT_REJECTED
        assert result.conflict_existing_digest == base.observation_digest
        assert len(state.observations) == 1

    def test_backfill_rejected(self) -> None:
        state = _eth_state()
        first = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T11:00:00Z"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T12:00:00Z",
        )
        assert first is not None
        append_forward_observation_v0(state, first, preconditions_checked=True)
        backfill = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T12:30:00Z",
        )
        assert backfill is not None
        result = append_forward_observation_v0(state, backfill, preconditions_checked=True)
        assert result.verdict == ArchiveAppendVerdict.BACKFILL_REJECTED


class TestGapAndStaleness:
    def test_gap_detected(self) -> None:
        prior = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T08:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T09:00:00Z",
        )
        current = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T11:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T12:00:00Z",
        )
        assert prior is not None and current is not None
        assessment = assess_gap_and_staleness_v0(current, prior=prior)
        assert assessment.status == GapStalenessStatus.GAP
        assert assessment.gap_hours == 3

    def test_stale_detected(self) -> None:
        prior = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T08:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T09:00:00Z",
        )
        current = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T09:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T12:00:00Z",
        )
        assert prior is not None and current is not None
        assessment = assess_gap_and_staleness_v0(current, prior=prior)
        assert assessment.status == GapStalenessStatus.STALE


class TestOverlapValidationReadiness:
    def test_not_executed_but_ready_when_populated(self) -> None:
        state = _eth_state()
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
        readiness = build_overlap_validation_readiness_v0([state])
        assert readiness.status == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED
        assert readiness.overlap_validation_executable is True
        assert readiness.archive_observation_count == 1


class TestPersistenceAndManifest:
    def test_persist_archive_snapshot_and_manifest_verify(self, tmp_path: Path) -> None:
        state = _eth_state()
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z"),
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T11:00:00Z",
        )
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
        manifest = persist_archive_snapshot_v0([state], output_dir=tmp_path)
        assert manifest["observation_count"] == 1
        assert manifest["futures_only"] is True
        assert manifest["bitcoin_present"] is False
        assert manifest["historical_backfill_allowed"] is False
        assert manifest["overlap_validation_status"] == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED
        write_manifest_sha256_v0(tmp_path)
        import subprocess

        result = subprocess.run(
            ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_backfill_collection_mode_rejected_at_normalization(self) -> None:
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row("2026-07-11T10:00:00Z"),
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            collected_at_utc="2026-07-11T11:00:00Z",
            collection_mode=COLLECTION_MODE_BACKFILL,
        )
        assert obs is None
