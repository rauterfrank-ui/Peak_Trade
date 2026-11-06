"""Contract tests for distinct external reference forward OI snapshot materialization v0."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.research.okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0 import (
    CONFIRM_GO,
    MODULE_VERSION,
    MaterializationTerminalStatus,
    build_materializer_config_v0,
    compute_implementation_digest_v0,
    count_exact_overlap_candidates_v0,
    exit_code_for_materialization_result_v0,
    load_raw_fetch_observations_v0,
    load_self_archive_overlap_window_v0,
    materialization_result_to_dict_v0,
    materialize_distinct_external_reference_snapshot_v0,
    normalize_fetched_observations_v0,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    OpenInterestFetchBudgetGuardV0,
    compute_open_interest_bounded_window_v0,
    paginate_bounded_open_interest_v0,
    parse_okx_open_interest_history_row_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_SCHEMA_VERSION,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0.json"
)
MODULE_PATH = (
    REPO_ROOT
    / "src/research/okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0.py"
)
CLI_PATH = (
    REPO_ROOT
    / "scripts/ops/materialize_okx_distinct_external_reference_forward_open_interest_snapshot_v0.py"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
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
ETH_INST_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
ETH_NATIVE = "ETH-USDT-SWAP"


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str = "1000.0") -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _write_self_archive(tmp_path: Path, *, timestamps: list[str], oi_values: list[str]) -> Path:
    state = InstrumentArchiveStateV0(
        instrument_id=ETH_INST_ID,
        native_instrument_id=ETH_NATIVE,
    )
    for ts, oi in zip(timestamps, oi_values):
        obs = normalize_forward_open_interest_observation_v0(
            _oi_row(ts, oi),
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            collected_at_utc="2026-07-11T18:10:07Z",
        )
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    archive_dir = tmp_path / "self_archive"
    persist_archive_snapshot_v0([state], output_dir=archive_dir)
    write_manifest_sha256_v0(archive_dir)
    return archive_dir


class _SeqFetcher:
    def __init__(self, responses: list[tuple[int, bytes]]) -> None:
        self._responses = list(responses)
        self._idx = 0
        self.requested_urls: list[str] = []

    def __call__(self, url: str, **_kwargs: Any) -> tuple[int, bytes, dict[str, str]]:
        self.requested_urls.append(url)
        if self._idx >= len(self._responses):
            return 200, b'{"code":"0","data":[]}', {}
        status, body = self._responses[self._idx]
        self._idx += 1
        return status, body, {}


def _noop_rate_limiter() -> None:
    return None


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode())


def _fetch_with_retry(
    url: str, *, fetcher: Any, **_kwargs: Any
) -> tuple[int, bytes, dict[str, str]]:
    return fetcher(url)


class TestDistinctExternalReferenceMaterializationConfig:
    def test_config_contract(self) -> None:
        config = build_materializer_config_v0()
        on_disk = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config == on_disk
        assert config["go_token"] == CONFIRM_GO
        assert config["acquisition_owner"] == "okx_historical_open_interest_public_fetch_v0"
        assert config["output_schema_version"] == ARCHIVE_SCHEMA_VERSION
        assert config["no_overlap_validation_execution"] is True
        assert config["no_self_archive_mutation"] is True

    def test_module_has_no_forbidden_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert f"import {prefix}" not in source
            assert f"from {prefix}" not in source

    def test_implementation_digest_stable(self) -> None:
        assert compute_implementation_digest_v0() == compute_implementation_digest_v0()


class TestDistinctExternalReferenceMaterializationBehavior:
    def test_default_off_blocks(self) -> None:
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm=CONFIRM_GO,
            instrument=ETH_INST,
            self_archive_source=Path("/tmp/unused"),
            output_dir=Path("/tmp/unused_out"),
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=False,
        )
        assert result.status == MaterializationTerminalStatus.FAIL_CLOSED_DEFAULT_OFF
        assert exit_code_for_materialization_result_v0(result) == 2

    def test_operator_go_mismatch_blocks(self) -> None:
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm="GO_WRONG",
            instrument=ETH_INST,
            self_archive_source=Path("/tmp/unused"),
            output_dir=Path("/tmp/unused_out"),
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=True,
        )
        assert result.status == MaterializationTerminalStatus.FAIL_CLOSED_OPERATOR_GO

    def test_load_self_archive_overlap_window(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z", "2026-07-11T12:00:00Z"],
            oi_values=["1234.5", "1350.0"],
        )
        overlap = load_self_archive_overlap_window_v0(archive)
        assert overlap.instrument_id == ETH_INST_ID
        assert overlap.self_observation_count == 2
        assert overlap.fetch_start_inclusive_utc == "2026-07-11T11:00:00Z"
        assert overlap.fetch_end_exclusive_utc == "2026-07-11T13:00:00Z"

    def test_same_output_path_rejected(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z"],
            oi_values=["1234.5"],
        )
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm=CONFIRM_GO,
            instrument=ETH_INST,
            self_archive_source=archive,
            output_dir=archive,
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=True,
            skip_fetch=True,
        )
        assert result.status == MaterializationTerminalStatus.FAIL_CLOSED_NOT_DISTINCT

    def test_end_to_end_fixture_materialization(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z", "2026-07-11T12:00:00Z"],
            oi_values=["1234.5", "1350.0"],
        )
        before = (archive / "observations.jsonl").read_bytes()
        body = json.dumps(
            {
                "code": "0",
                "data": [
                    _oi_row("2026-07-11T11:00:00Z", "1234.5"),
                    _oi_row("2026-07-11T12:00:00Z", "1350.0"),
                ],
            }
        ).encode()
        fetcher = _SeqFetcher([(200, body)])
        output_dir = tmp_path / "external_ref"
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm=CONFIRM_GO,
            instrument=ETH_INST,
            self_archive_source=archive,
            output_dir=output_dir,
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=True,
            fetcher=fetcher,
            fetch_with_retry=_fetch_with_retry,
            build_url=_build_url,
            parse_json=_parse_json,
            rate_limiter=_noop_rate_limiter,
        )
        after = (archive / "observations.jsonl").read_bytes()
        assert before == after
        assert result.status == MaterializationTerminalStatus.COMPLETE
        assert result.distinct_from_self_archive is True
        assert result.exact_overlap_candidate_count == 2
        assert result.second_materialization_diff_empty is True
        assert (output_dir / "observations.jsonl").is_file()
        assert (output_dir / "provenance.json").is_file()
        assert (output_dir / "dataset_manifest.json").is_file()
        assert (output_dir / "acquisition_report.json").is_file()
        assert (output_dir / "MANIFEST.sha256").is_file()

    def test_raw_rematerialization_is_deterministic(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z"],
            oi_values=["1234.5"],
        )
        body = json.dumps(
            {"code": "0", "data": [_oi_row("2026-07-11T11:00:00Z", "1234.5")]}
        ).encode()
        fetcher = _SeqFetcher([(200, body)])
        output_dir = tmp_path / "external_ref"
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm=CONFIRM_GO,
            instrument=ETH_INST,
            self_archive_source=archive,
            output_dir=output_dir,
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=True,
            fetcher=fetcher,
            fetch_with_retry=_fetch_with_retry,
            build_url=_build_url,
            parse_json=_parse_json,
            rate_limiter=_noop_rate_limiter,
        )
        assert result.status == MaterializationTerminalStatus.COMPLETE
        raw_dir = output_dir / "raw_fetch"
        window = compute_open_interest_bounded_window_v0(
            start_inclusive_utc="2026-07-11T11:00:00Z",
            end_exclusive_utc="2026-07-11T12:00:00Z",
            lookback_k=0,
            signal_lag_bars=0,
        )
        loaded = load_raw_fetch_observations_v0(
            raw_dir,
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            window=window,
        )
        normalized = normalize_fetched_observations_v0(
            loaded,
            collected_at_utc="2026-07-11T20:00:00Z",
        )
        assert (
            count_exact_overlap_candidates_v0(
                normalized,
                self_venue_timestamp_ms=[_ms("2026-07-11T11:00:00Z")],
            )
            == 1
        )

    def test_result_dict_roundtrip(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z"],
            oi_values=["1234.5"],
        )
        body = json.dumps(
            {"code": "0", "data": [_oi_row("2026-07-11T11:00:00Z", "1234.5")]}
        ).encode()
        fetcher = _SeqFetcher([(200, body)])
        result = materialize_distinct_external_reference_snapshot_v0(
            confirm=CONFIRM_GO,
            instrument=ETH_INST,
            self_archive_source=archive,
            output_dir=tmp_path / "external_ref",
            collected_at_utc="2026-07-11T20:00:00Z",
            enabled=True,
            fetcher=fetcher,
            fetch_with_retry=_fetch_with_retry,
            build_url=_build_url,
            parse_json=_parse_json,
            rate_limiter=_noop_rate_limiter,
        )
        payload = materialization_result_to_dict_v0(result)
        assert payload["module_version"] == MODULE_VERSION
        assert payload["status"] == MaterializationTerminalStatus.COMPLETE.value


class TestDistinctExternalReferenceMaterializationCli:
    def test_cli_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        assert "--confirm-go-token" in proc.stdout

    def test_cli_default_off(self, tmp_path: Path) -> None:
        archive = _write_self_archive(
            tmp_path,
            timestamps=["2026-07-11T11:00:00Z"],
            oi_values=["1234.5"],
        )
        inst = tmp_path / "instrument.json"
        inst.write_text(json.dumps(ETH_INST), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--self-archive-input",
                str(archive),
                "--output-dir",
                str(tmp_path / "external_ref"),
                "--instrument-file",
                str(inst),
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 2
        assert "DEFAULT_OFF_ENABLED_FLAG_REQUIRED" in proc.stderr
