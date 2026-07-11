"""Contract tests for OKX self-accumulated forward OI overlap validation v0."""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

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
from src.research.okx_self_accumulated_forward_open_interest_overlap_validation_v0 import (
    CONFIRM_GO,
    MODULE_VERSION,
    OverlapValidationConfigV0,
    OverlapValidationStatus,
    OverlapValidationVerdict,
    TimestampAlignmentStatus,
    ValueComparisonStatus,
    build_overlap_validation_config_v0,
    compute_implementation_digest_v0,
    exit_code_for_overlap_validation_result_v0,
    load_versioned_config_v0,
    overlap_validation_result_to_dict_v0,
    validate_overlap_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_overlap_validation_v0.json"
)
MODULE_PATH = (
    REPO_ROOT / "src/research/okx_self_accumulated_forward_open_interest_overlap_validation_v0.py"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/validate_okx_self_accumulated_forward_open_interest_overlap_v0.py"
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
    collected_utc: str | None = None,
) -> object:
    collected = collected_utc or "2026-07-11T11:00:00Z"
    return normalize_forward_open_interest_observation_v0(
        _oi_row(ts_utc, oi),
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        collected_at_utc=collected,
    )


def _write_snapshot(
    tmp_path: Path,
    *,
    instrument_id: str = ETH_INST_ID,
    native_instrument_id: str = ETH_NATIVE,
    observations: list[object],
) -> Path:
    state = InstrumentArchiveStateV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
    )
    for obs in observations:
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    persist_archive_snapshot_v0([state], output_dir=tmp_path)
    write_manifest_sha256_v0(tmp_path)
    return tmp_path


def _strict_config(**overrides: object) -> OverlapValidationConfigV0:
    base = load_versioned_config_v0()
    payload = {
        "schema_version": base.schema_version,
        "timestamp_alignment_policy": base.timestamp_alignment_policy,
        "maximum_timestamp_delta_seconds": base.maximum_timestamp_delta_seconds,
        "absolute_tolerance": base.absolute_tolerance,
        "relative_tolerance": base.relative_tolerance,
        "minimum_aligned_pairs": base.minimum_aligned_pairs,
        "duplicate_policy": base.duplicate_policy,
        "missing_pair_policy": base.missing_pair_policy,
        "fail_closed_on_missing_reference": base.fail_closed_on_missing_reference,
    }
    payload.update(overrides)
    return OverlapValidationConfigV0(**payload)


class TestConfigAndBoundaries:
    def test_config_matches_module_contract(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["go_token"] == CONFIRM_GO
        assert config["schema_version"] == MODULE_VERSION
        assert config["fail_closed_on_missing_reference"] is True
        assert config["offline_only"] is True
        assert config["no_collector_execution"] is True
        assert compute_implementation_digest_v0()

    def test_no_runtime_or_network_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert prefix not in source

    def test_authority_and_runtime_effect_none(self) -> None:
        result = validate_overlap_v0(
            self_accumulated_source=Path("/tmp/unused"),
            external_reference_source=None,
        )
        assert result.authority_effect == "NONE"
        assert result.runtime_effect == "NONE"


class TestFailClosedBlocking:
    def test_missing_external_reference_blocks_fail_closed(self) -> None:
        result = validate_overlap_v0(
            self_accumulated_source=Path("/tmp/unused"),
            external_reference_source=None,
        )
        assert result.status == OverlapValidationStatus.BLOCKED_MISSING_REFERENCE.value
        assert result.verdict == OverlapValidationVerdict.NOT_EXECUTABLE.value
        assert exit_code_for_overlap_validation_result_v0(result) == 2

    def test_same_input_dual_binding_blocked(self, tmp_path: Path) -> None:
        snapshot = _write_snapshot(
            tmp_path / "archive",
            observations=[
                _make_obs(
                    instrument_id=ETH_INST_ID,
                    native_instrument_id=ETH_NATIVE,
                    ts_utc="2026-07-11T11:00:00Z",
                )
            ],
        )
        result = validate_overlap_v0(
            self_accumulated_source=snapshot,
            external_reference_source=snapshot,
        )
        assert result.status == OverlapValidationStatus.BLOCKED_INVALID_REFERENCE.value
        assert result.verdict == OverlapValidationVerdict.NOT_EXECUTABLE.value
        assert "SAME_INPUT_DUAL_BINDING_FORBIDDEN" in result.reason_codes

    def test_cli_missing_reference_exits_nonzero(self, tmp_path: Path) -> None:
        snapshot = _write_snapshot(
            tmp_path / "self",
            observations=[
                _make_obs(
                    instrument_id=ETH_INST_ID,
                    native_instrument_id=ETH_NATIVE,
                    ts_utc="2026-07-11T11:00:00Z",
                )
            ],
        )
        proc = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--enabled",
                "--self-accumulated-input",
                str(snapshot),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        payload = json.loads(proc.stdout)
        assert payload["status"] == OverlapValidationStatus.BLOCKED_MISSING_REFERENCE.value


class TestComparisonSemantics:
    def test_exact_match_passes(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            oi="1234.5",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.status == OverlapValidationStatus.PASS.value
        assert result.verdict == OverlapValidationVerdict.PASS.value
        assert result.aligned_pair_count == 1
        assert result.matched_pair_count == 1
        assert result.mismatched_pair_count == 0
        assert result.timestamp_alignment_status == TimestampAlignmentStatus.ALIGNED.value
        assert result.value_comparison_status == ValueComparisonStatus.ALL_MATCHED.value

    def test_value_outside_tolerance_fails(self, tmp_path: Path) -> None:
        self_obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            oi="1000.0",
        )
        ref_obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            oi="2000.0",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[self_obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[ref_obs])
        result = validate_overlap_v0(
            self_accumulated_source=self_dir,
            external_reference_source=ref_dir,
            config=_strict_config(absolute_tolerance="0.0", relative_tolerance="0.0"),
        )
        assert result.status == OverlapValidationStatus.FAIL.value
        assert result.verdict == OverlapValidationVerdict.FAIL.value
        assert result.mismatched_pair_count == 1

    def test_value_inside_tolerance_passes(self, tmp_path: Path) -> None:
        self_obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            oi="1000.0",
        )
        ref_obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            oi="1000.5",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[self_obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[ref_obs])
        result = validate_overlap_v0(
            self_accumulated_source=self_dir,
            external_reference_source=ref_dir,
            config=_strict_config(absolute_tolerance="1.0", relative_tolerance="0.01"),
        )
        assert result.status == OverlapValidationStatus.PASS.value
        assert result.matched_pair_count == 1

    def test_missing_reference_timestamp_classified(self, tmp_path: Path) -> None:
        self_obs = [
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T11:00:00Z",
                collected_utc="2026-07-11T11:30:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T12:00:00Z",
                collected_utc="2026-07-11T12:30:00Z",
            ),
        ]
        ref_obs = [
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T11:00:00Z",
                collected_utc="2026-07-11T11:30:00Z",
            )
        ]
        self_dir = _write_snapshot(tmp_path / "self", observations=self_obs)
        ref_dir = _write_snapshot(tmp_path / "ref", observations=ref_obs)
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.missing_reference_count == 1
        assert "MISSING_REFERENCE_TIMESTAMP" in result.reason_codes

    def test_missing_self_accumulated_timestamp_classified(self, tmp_path: Path) -> None:
        self_obs = [
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T11:00:00Z",
                collected_utc="2026-07-11T11:30:00Z",
            )
        ]
        ref_obs = [
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T11:00:00Z",
                collected_utc="2026-07-11T11:30:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T12:00:00Z",
                collected_utc="2026-07-11T12:30:00Z",
            ),
        ]
        self_dir = _write_snapshot(tmp_path / "self", observations=self_obs)
        ref_dir = _write_snapshot(tmp_path / "ref", observations=ref_obs)
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.missing_self_accumulated_count == 1
        assert "MISSING_SELF_ACCUMULATED_TIMESTAMP" in result.reason_codes

    def test_stale_collection_lag_does_not_block_overlap(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T18:00:00Z",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.status == OverlapValidationStatus.PASS.value


class TestSchemaAndInputRejection:
    def test_duplicate_timestamps_rejected(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T11:30:00Z",
        )
        assert obs is not None
        row = serialize_canonical_json(serialize_observation_v0(obs)) + "\n"
        snapshot = tmp_path / "self"
        snapshot.mkdir()
        (snapshot / "observations.jsonl").write_text(row + row, encoding="utf-8")
        ref = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=snapshot, external_reference_source=ref
        )
        assert result.status == OverlapValidationStatus.BLOCKED_UNSUPPORTED_SCHEMA.value
        assert "DUPLICATE_VENUE_TIMESTAMP" in result.reason_codes

    def test_mismatched_instrument_rejected(self, tmp_path: Path) -> None:
        self_dir = _write_snapshot(
            tmp_path / "self",
            observations=[
                _make_obs(
                    instrument_id=ETH_INST_ID,
                    native_instrument_id=ETH_NATIVE,
                    ts_utc="2026-07-11T11:00:00Z",
                )
            ],
        )
        ref_dir = _write_snapshot(
            tmp_path / "ref",
            instrument_id=SOL_INST_ID,
            native_instrument_id=SOL_NATIVE,
            observations=[
                _make_obs(
                    instrument_id=SOL_INST_ID,
                    native_instrument_id=SOL_NATIVE,
                    ts_utc="2026-07-11T11:00:00Z",
                )
            ],
        )
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.status == OverlapValidationStatus.BLOCKED_INVALID_REFERENCE.value
        assert "MISMATCHED_INSTRUMENT_ID" in result.reason_codes

    def test_invalid_schema_rejected(self, tmp_path: Path) -> None:
        self_dir = tmp_path / "self"
        self_dir.mkdir()
        (self_dir / "observations.jsonl").write_text('{"bad":"row"}\n', encoding="utf-8")
        ref_dir = _write_snapshot(
            tmp_path / "ref",
            observations=[
                _make_obs(
                    instrument_id=ETH_INST_ID,
                    native_instrument_id=ETH_NATIVE,
                    ts_utc="2026-07-11T11:00:00Z",
                )
            ],
        )
        result = validate_overlap_v0(
            self_accumulated_source=self_dir, external_reference_source=ref_dir
        )
        assert result.status in {
            OverlapValidationStatus.BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE.value,
            OverlapValidationStatus.BLOCKED_UNSUPPORTED_SCHEMA.value,
        }

    def test_negative_oi_rejected(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T11:30:00Z",
        )
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["open_interest_raw"] = "-1.0"
        row["observation_digest"] = compute_observation_digest_v0(row)
        snapshot = tmp_path / "self"
        snapshot.mkdir()
        (snapshot / "observations.jsonl").write_text(
            serialize_canonical_json(row) + "\n", encoding="utf-8"
        )
        ref = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=snapshot, external_reference_source=ref
        )
        assert "NEGATIVE_OPEN_INTEREST_VALUE" in result.reason_codes

    def test_non_finite_oi_rejected(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
            collected_utc="2026-07-11T11:30:00Z",
        )
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["open_interest_raw"] = "nan"
        row["observation_digest"] = compute_observation_digest_v0(row)
        snapshot = tmp_path / "self"
        snapshot.mkdir()
        (snapshot / "observations.jsonl").write_text(
            serialize_canonical_json(row) + "\n", encoding="utf-8"
        )
        ref = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=snapshot, external_reference_source=ref
        )
        assert "NON_FINITE_OPEN_INTEREST_VALUE" in result.reason_codes

    def test_insufficient_aligned_pairs_classified(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[obs])
        result = validate_overlap_v0(
            self_accumulated_source=self_dir,
            external_reference_source=ref_dir,
            config=_strict_config(minimum_aligned_pairs=2),
        )
        assert result.status == OverlapValidationStatus.INSUFFICIENT_DATA.value
        assert result.verdict == OverlapValidationVerdict.INSUFFICIENT_DATA.value
        assert "INSUFFICIENT_ALIGNED_PAIRS" in result.reason_codes


class TestDeterminismAndImmutability:
    def test_deterministic_repeated_output(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[obs])
        first = overlap_validation_result_to_dict_v0(
            validate_overlap_v0(self_accumulated_source=self_dir, external_reference_source=ref_dir)
        )
        second = overlap_validation_result_to_dict_v0(
            validate_overlap_v0(self_accumulated_source=self_dir, external_reference_source=ref_dir)
        )
        assert first == second
        assert first["validation_id"] == second["validation_id"]

    def test_input_files_remain_byte_identical(self, tmp_path: Path) -> None:
        obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T11:00:00Z",
        )
        self_dir = _write_snapshot(tmp_path / "self", observations=[obs])
        ref_dir = _write_snapshot(tmp_path / "ref", observations=[obs])
        before_self = (self_dir / "observations.jsonl").read_bytes()
        before_ref = (ref_dir / "observations.jsonl").read_bytes()
        validate_overlap_v0(self_accumulated_source=self_dir, external_reference_source=ref_dir)
        assert (self_dir / "observations.jsonl").read_bytes() == before_self
        assert (ref_dir / "observations.jsonl").read_bytes() == before_ref

    def test_config_json_matches_build_helper(self) -> None:
        assert build_overlap_validation_config_v0() == json.loads(
            CONFIG_PATH.read_text(encoding="utf-8")
        )

    def test_no_collector_boundary_in_cli_help(self) -> None:
        proc = subprocess.run(
            ["uv", "run", "python", str(CLI_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        assert "collect" not in proc.stdout.lower()
