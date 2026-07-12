"""Contract tests for historical panel depth extension v0."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    load_effective_archive_states_from_snapshot_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    compare_materialization_manifests_v0,
    materialize_self_accumulated_bound_open_interest_panel_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0 import (
    CONFIRM_GO,
    FIRST_RANKABLE_EPOCH_INDEX,
    MINIMUM_REQUIRED_HISTORY_DEPTH,
    TARGET_HISTORY_BARS,
    HistoricalDepthExtensionTerminalStatus,
    HistoricalFetchValidationVerdict,
    build_extension_config_v0,
    compute_acquisition_window_v0,
    compute_common_panel_intersection_v0,
    compute_missing_timestamps_v0,
    compute_target_panel_calendar_v0,
    detect_digest_conflicts_v0,
    execute_historical_panel_depth_extension_v0,
    validate_fetched_historical_bars_v0,
    validate_post_extension_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/"
    "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0.json"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/"
    "execute_okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0.py"
)
MODULE_PATH = (
    REPO_ROOT / "src/research/"
    "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0.py"
)

SHALLOW_PANEL_TIMESTAMPS = (
    "2026-07-11T18:00:00Z",
    "2026-07-11T19:00:00Z",
    "2026-07-11T20:00:00Z",
    "2026-07-11T21:00:00Z",
    "2026-07-11T22:00:00Z",
    "2026-07-11T23:00:00Z",
)


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str) -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _make_obs(
    *,
    instrument_id: str,
    native_instrument_id: str,
    ts_utc: str,
    collected_utc: str,
    oi: str,
):
    return normalize_forward_open_interest_observation_v0(
        _oi_row(ts_utc, oi),
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        collected_at_utc=collected_utc,
    )


def _build_shallow_fixture_archive(tmp_path: Path) -> Path:
    archive_dir = tmp_path / "archive"
    states_by_id: dict[str, InstrumentArchiveStateV0] = {}
    for instrument_id, native in CANONICAL_UNIVERSE_BINDING:
        for index, ts_utc in enumerate(SHALLOW_PANEL_TIMESTAMPS):
            collected_utc = SHALLOW_PANEL_TIMESTAMPS[
                min(index + 1, len(SHALLOW_PANEL_TIMESTAMPS) - 1)
            ]
            obs = _make_obs(
                instrument_id=instrument_id,
                native_instrument_id=native,
                ts_utc=ts_utc,
                collected_utc=collected_utc,
                oi=f"{1000 + index}.{index}",
            )
            assert obs is not None
            state = states_by_id.get(instrument_id)
            if state is None:
                state = InstrumentArchiveStateV0(
                    instrument_id=instrument_id,
                    native_instrument_id=native,
                )
                states_by_id[instrument_id] = state
            append_forward_observation_v0(state, obs, preconditions_checked=True)
    persist_archive_snapshot_v0(list(states_by_id.values()), output_dir=archive_dir)
    write_manifest_sha256_v0(archive_dir)
    return archive_dir


def _normalized(
    *,
    instrument_id: str,
    native_instrument_id: str,
    ts_utc: str,
    oi: str = "1000.0",
) -> NormalizedOpenInterestObservationV0:
    return NormalizedOpenInterestObservationV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        observation_time_ms=_ms(ts_utc),
        observation_time_utc=ts_utc,
        open_interest_raw=oi,
        open_interest_unit="okx_native_contract_count",
        source_schema_version="okx_rubik_open_interest_history.v0",
        source_record_key=f"{native_instrument_id}:{_ms(ts_utc)}",
    )


def _extended_fixture_rows(
    native: str, instrument_id: str, tail_end: str = "2026-07-11T23:00:00Z"
) -> list[NormalizedOpenInterestObservationV0]:
    calendar = compute_target_panel_calendar_v0(
        tail_end_venue_utc=tail_end,
        bar_count=TARGET_HISTORY_BARS,
    )
    missing = compute_missing_timestamps_v0(
        existing_common=SHALLOW_PANEL_TIMESTAMPS,
        target_calendar=calendar,
    )
    return [
        _normalized(
            instrument_id=instrument_id,
            native_instrument_id=native,
            ts_utc=ts_utc,
            oi=f"{2000 + index}.0",
        )
        for index, ts_utc in enumerate(missing)
    ]


class TestContractConfig:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_extension_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["minimum_required_history_depth"] == MINIMUM_REQUIRED_HISTORY_DEPTH
        assert config["target_history_bars"] == TARGET_HISTORY_BARS
        assert module_config["rank_lookback_k"] == LOOKBACK_K
        assert module_config["signal_lag_bars"] == SIGNAL_LAG_BARS

    def test_cli_and_module_exist(self) -> None:
        assert CLI_PATH.is_file()
        assert MODULE_PATH.is_file()


class TestAcquisitionWindow:
    def test_target_calendar_has_safety_margin_over_minimum(self) -> None:
        window = compute_acquisition_window_v0(tail_end_venue_utc="2026-07-11T23:00:00Z")
        assert window["target_history_bars"] >= MINIMUM_REQUIRED_HISTORY_DEPTH
        assert window["target_history_bars"] == TARGET_HISTORY_BARS
        assert window["expected_rankable_epoch_count"] >= 50
        assert window["first_rankable_epoch_index"] == FIRST_RANKABLE_EPOCH_INDEX

    def test_missing_timestamps_for_shallow_panel(self) -> None:
        calendar = compute_target_panel_calendar_v0(tail_end_venue_utc="2026-07-11T23:00:00Z")
        missing = compute_missing_timestamps_v0(
            existing_common=SHALLOW_PANEL_TIMESTAMPS,
            target_calendar=calendar,
        )
        assert len(SHALLOW_PANEL_TIMESTAMPS) == 6
        assert len(calendar) == TARGET_HISTORY_BARS
        assert len(missing) == TARGET_HISTORY_BARS - 6


class TestFetchValidation:
    def test_validate_passes_for_complete_fixture(self) -> None:
        instrument_id, native = CANONICAL_UNIVERSE_BINDING[0]
        required = ("2026-07-11T12:00:00Z", "2026-07-11T13:00:00Z")
        rows = [
            _normalized(instrument_id=instrument_id, native_instrument_id=native, ts_utc=ts)
            for ts in required
        ]
        result = validate_fetched_historical_bars_v0(
            rows,
            instrument_id=instrument_id,
            native_instrument_id=native,
            required_timestamps_utc=required,
        )
        assert result.verdict is HistoricalFetchValidationVerdict.PASS


class TestHistoricalDepthExtension:
    def test_fixture_extension_reaches_minimum_depth_and_materializes(self, tmp_path: Path) -> None:
        archive_dir = _build_shallow_fixture_archive(tmp_path)
        fixture_dir = tmp_path / "fixtures"
        fixture_dir.mkdir()
        for instrument_id, native in CANONICAL_UNIVERSE_BINDING:
            rows = _extended_fixture_rows(native, instrument_id)
            (fixture_dir / f"{native}.json").write_text(
                json.dumps(
                    {
                        "observations": [
                            {
                                "instrument_id": row.instrument_id,
                                "native_instrument_id": row.native_instrument_id,
                                "observation_time_ms": row.observation_time_ms,
                                "observation_time_utc": row.observation_time_utc,
                                "open_interest_raw": row.open_interest_raw,
                                "open_interest_unit": row.open_interest_unit,
                                "source_schema_version": row.source_schema_version,
                                "source_record_key": row.source_record_key,
                            }
                            for row in rows
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

        fixture_map = {}
        for path in fixture_dir.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            fixture_map[path.stem] = tuple(
                NormalizedOpenInterestObservationV0(**item) for item in payload["observations"]
            )

        result = execute_historical_panel_depth_extension_v0(
            confirm=CONFIRM_GO,
            enabled=True,
            target_archive_path=archive_dir,
            collected_at_utc="2026-07-12T01:00:00Z",
            collection_execution_id="test-depth-extension",
            evidence_ref=str(tmp_path / "evidence"),
            raw_dir=tmp_path / "raw",
            fixture_observations_by_native=fixture_map,
            execute_mutation=True,
        )
        assert result.status is HistoricalDepthExtensionTerminalStatus.EXTENSION_COMPLETE
        assert result.history_depth_before == 6
        assert result.history_depth_after >= MINIMUM_REQUIRED_HISTORY_DEPTH
        assert result.expected_rankable_epoch_count >= 50
        assert result.observations_jsonl_byte_identical is True
        assert result.panel_time_alignment_pass is True

        post = validate_post_extension_v0(target_archive_path=archive_dir)
        assert post["history_depth_after"] >= MINIMUM_REQUIRED_HISTORY_DEPTH
        assert post["panel_time_alignment_pass"] is True

        first_out = tmp_path / "mat_a"
        second_out = tmp_path / "mat_b"
        first = materialize_self_accumulated_bound_open_interest_panel_v0(
            archive_root=archive_dir,
            output_root=first_out,
        )
        second = materialize_self_accumulated_bound_open_interest_panel_v0(
            archive_root=archive_dir,
            output_root=second_out,
        )
        assert first.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        assert second.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        diff_empty, _ = compare_materialization_manifests_v0(
            Path(first.manifest_path),
            Path(second.manifest_path),
        )
        assert diff_empty is True
        assert (
            len(
                compute_common_panel_intersection_v0(
                    load_effective_archive_states_from_snapshot_v0(archive_dir)
                )
            )
            >= MINIMUM_REQUIRED_HISTORY_DEPTH
        )

    def test_digest_conflict_fail_closed(self, tmp_path: Path) -> None:
        archive_dir = _build_shallow_fixture_archive(tmp_path)
        states = load_effective_archive_states_from_snapshot_v0(archive_dir)
        effective_index = {
            (obs.instrument_id, obs.venue_timestamp_utc): obs
            for state in states
            for obs in state.observations
        }
        existing = next(iter(effective_index.values()))
        candidate = dict(
            instrument_id=existing.instrument_id,
            venue_timestamp_utc=existing.venue_timestamp_utc,
            observation_digest="deadbeef" * 8,
        )
        ok, conflicts = detect_digest_conflicts_v0(
            effective_index=effective_index,
            candidate_rows=[candidate],
        )
        assert ok is False
        assert conflicts
