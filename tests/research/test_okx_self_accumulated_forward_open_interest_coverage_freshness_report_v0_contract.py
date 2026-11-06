"""Contract tests for OKX self-accumulated forward OI coverage/freshness report v0."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    ArchiveIntegrityAuditStatus,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    compute_observation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0 import (
    CONFIRM_GO,
    MODULE_VERSION,
    CoverageFreshnessArchiveStatus,
    CoverageStatus,
    ContinuityStatus,
    FreshnessStatus,
    build_report_config_v0,
    compute_report_implementation_digest_v0,
    generate_coverage_freshness_report_v0,
    report_result_to_dict_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0.json"
)
REPORT_MODULE_PATH = (
    REPO_ROOT
    / "src/research/okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0.py"
)
CLI_PATH = (
    REPO_ROOT
    / "scripts/ops/report_okx_self_accumulated_forward_open_interest_coverage_freshness_v0.py"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)

ETH_INST_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
ETH_NATIVE = "ETH-USDT-SWAP"
SOL_INST_ID = "okx:linear_perpetual:SOL:USDT:USDT:perp"
SOL_NATIVE = "SOL-USDT-SWAP"
AS_OF_UTC = "2026-07-11T14:00:00Z"


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str = "1000.0") -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _make_obs(
    *,
    instrument_id: str,
    native_instrument_id: str,
    ts_utc: str,
    oi: str = "1000.0",
    collected_utc: str,
) -> object:
    return normalize_forward_open_interest_observation_v0(
        _oi_row(ts_utc, oi),
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        collected_at_utc=collected_utc,
    )


def _write_snapshot(
    tmp_path: Path,
    *,
    observations: list[object],
) -> Path:
    states_by_id: dict[str, InstrumentArchiveStateV0] = {}
    for obs in observations:
        assert obs is not None
        state = states_by_id.get(obs.instrument_id)
        if state is None:
            state = InstrumentArchiveStateV0(
                instrument_id=obs.instrument_id,
                native_instrument_id=obs.native_instrument_id,
            )
            states_by_id[obs.instrument_id] = state
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    persist_archive_snapshot_v0(list(states_by_id.values()), output_dir=tmp_path)
    write_manifest_sha256_v0(tmp_path)
    return tmp_path


class TestReportConfigAndBoundaries:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_report_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["schema_version"] == MODULE_VERSION
        assert module_config["implementation_digest"] == compute_report_implementation_digest_v0()
        assert config["authority_effect"] == "NONE"
        assert config["runtime_effect"] == "NONE"

    def test_no_forbidden_imports(self) -> None:
        source = REPORT_MODULE_PATH.read_text(encoding="utf-8")
        cli_source = CLI_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert prefix not in source
            assert prefix not in cli_source


class TestValidEmptyAndMissing:
    def test_valid_empty_directory(self, tmp_path: Path) -> None:
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.VALID_EMPTY.value
        assert result.archive_row_count == 0
        assert result.archive_instrument_count == 0
        assert result.earliest_observation_utc is None
        assert result.latest_observation_utc is None
        assert result.archive_horizon_seconds is None
        assert result.freshness_status == FreshnessStatus.VALID_EMPTY.value
        assert result.continuity_status == ContinuityStatus.VALID_EMPTY.value
        assert result.coverage_status == CoverageStatus.INSUFFICIENT_DATA.value
        assert result.integrity_status == ArchiveIntegrityAuditStatus.VALID_EMPTY.value
        assert result.sufficient_for_overlap_validation is False
        assert result.sufficient_for_source_ratification is False
        assert result.authority_effect == "NONE"
        assert result.runtime_effect == "NONE"

    def test_missing_archive_root(self) -> None:
        result = generate_coverage_freshness_report_v0(archive_root=None, as_of_utc=AS_OF_UTC)
        assert result.archive_status == CoverageFreshnessArchiveStatus.MISSING_ARCHIVE_ROOT.value
        assert "MISSING_ARCHIVE_ROOT" in result.reason_codes
        assert result.sufficient_for_overlap_validation is False
        assert result.sufficient_for_source_ratification is False

    def test_missing_archive_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        result = generate_coverage_freshness_report_v0(
            archive_root=missing,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.MISSING_ARCHIVE.value
        assert "MISSING_ARCHIVE" in result.reason_codes


class TestDeterminism:
    def test_identical_output_on_repeat(self, tmp_path: Path) -> None:
        first = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        second = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert report_result_to_dict_v0(first) == report_result_to_dict_v0(second)
        assert first.report_id == second.report_id


class TestNonEmptyValid:
    def test_single_observation_insufficient_data(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        _write_snapshot(tmp_path, observations=[obs])
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.NON_EMPTY_VALID.value
        assert result.archive_row_count == 1
        assert result.archive_instrument_count == 1
        assert result.earliest_observation_utc == "2026-07-11T10:00:00Z"
        assert result.latest_observation_utc == "2026-07-11T10:00:00Z"
        assert result.archive_horizon_seconds == 0
        assert result.coverage_status == CoverageStatus.INSUFFICIENT_DATA.value
        assert result.integrity_status == ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA.value
        assert result.sufficient_for_overlap_validation is False
        assert result.sufficient_for_source_ratification is False

    def test_multi_observation_pass_with_freshness(self, tmp_path: Path) -> None:
        obs1 = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        obs2 = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T12:00:00Z",
        )
        _write_snapshot(tmp_path, observations=[obs1, obs2])
        as_of_fresh = "2026-07-11T12:00:00Z"
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=as_of_fresh,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.NON_EMPTY_VALID.value
        assert result.archive_row_count == 2
        assert result.earliest_observation_utc == "2026-07-11T10:00:00Z"
        assert result.latest_observation_utc == "2026-07-11T11:00:00Z"
        assert result.archive_horizon_seconds == 3600
        assert result.freshness_status == FreshnessStatus.OK.value
        assert result.freshness_age_seconds == 3600
        assert result.continuity_status == ContinuityStatus.OK.value
        assert result.coverage_status == CoverageStatus.SUFFICIENT.value
        assert result.integrity_status == ArchiveIntegrityAuditStatus.PASS.value
        assert result.sufficient_for_overlap_validation is True
        assert result.sufficient_for_source_ratification is True

    def test_multiple_instruments(self, tmp_path: Path) -> None:
        eth = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        sol = _make_obs(
            instrument_id=SOL_INST_ID,
            native_instrument_id=SOL_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        eth2 = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T12:00:00Z",
        )
        sol2 = _make_obs(
            instrument_id=SOL_INST_ID,
            native_instrument_id=SOL_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T12:00:00Z",
        )
        _write_snapshot(tmp_path, observations=[eth, sol, eth2, sol2])
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_instrument_count == 2
        assert result.archive_row_count == 4
        assert result.coverage_status == CoverageStatus.SUFFICIENT.value

    def test_unordered_input_rows_sorted_by_archive_contract(self, tmp_path: Path) -> None:
        obs1 = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T12:00:00Z",
        )
        obs2 = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        assert obs1 is not None and obs2 is not None
        lines = [
            serialize_canonical_json(serialize_observation_v0(obs1)),
            serialize_canonical_json(serialize_observation_v0(obs2)),
        ]
        (tmp_path / "observations.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.INVALID_OR_CORRUPT.value
        assert result.integrity_status == ArchiveIntegrityAuditStatus.FAIL.value


class TestInvalidOrCorrupt:
    def test_corrupt_jsonl(self, tmp_path: Path) -> None:
        (tmp_path / "observations.jsonl").write_text("{not-json", encoding="utf-8")
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.INVALID_OR_CORRUPT.value
        assert result.integrity_status == ArchiveIntegrityAuditStatus.FAIL.value
        assert result.sufficient_for_overlap_validation is False

    def test_digest_mismatch(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T10:00:00Z",
            collected_utc="2026-07-11T11:00:00Z",
        )
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["observation_digest"] = "0" * 64
        (tmp_path / "observations.jsonl").write_text(
            serialize_canonical_json(row) + "\n",
            encoding="utf-8",
        )
        result = generate_coverage_freshness_report_v0(
            archive_root=tmp_path,
            as_of_utc=AS_OF_UTC,
        )
        assert result.archive_status == CoverageFreshnessArchiveStatus.INVALID_OR_CORRUPT.value


class TestCli:
    def test_cli_valid_empty(self, tmp_path: Path) -> None:
        proc = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--archive-root",
                str(tmp_path),
                "--as-of-utc",
                AS_OF_UTC,
                "--enabled",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["archive_status"] == CoverageFreshnessArchiveStatus.VALID_EMPTY.value

    def test_cli_default_off(self, tmp_path: Path) -> None:
        proc = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--archive-root",
                str(tmp_path),
                "--as-of-utc",
                AS_OF_UTC,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        assert "DEFAULT_OFF_ENABLED_FLAG_REQUIRED" in proc.stderr
