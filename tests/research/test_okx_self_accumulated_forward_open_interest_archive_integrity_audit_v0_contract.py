"""Contract tests for OKX self-accumulated forward OI archive integrity audit v0."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    CONFIRM_GO,
    MODULE_VERSION,
    ArchiveIntegrityAuditStatus,
    ArchiveIntegrityFailureClass,
    audit_archive_snapshot_v0,
    audit_result_to_dict_v0,
    build_audit_config_v0,
    compute_audit_implementation_digest_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    BAR_INTERVAL,
    COLLECTION_MODE_FORWARD_ONLY,
    OPEN_INTEREST_UNIT,
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    compute_observation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    verify_manifest_sha256_v0,
    write_manifest_sha256_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0.json"
)
AUDIT_MODULE_PATH = (
    REPO_ROOT
    / "src/research/okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0.py"
)
CLI_PATH = REPO_ROOT / "scripts/ops/audit_okx_self_accumulated_forward_open_interest_archive_v0.py"
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


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str = "1000.0") -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _eth_state() -> InstrumentArchiveStateV0:
    return InstrumentArchiveStateV0(
        instrument_id=ETH_INST_ID,
        native_instrument_id=ETH_NATIVE,
    )


def _make_obs(ts_utc: str, oi: str = "1000.0", collected_utc: str | None = None) -> object:
    collected = collected_utc or ts_utc.replace(":00Z", ":30Z")
    if collected == ts_utc:
        collected = "2026-07-11T11:00:00Z"
    return normalize_forward_open_interest_observation_v0(
        _oi_row(ts_utc, oi),
        instrument_id=ETH_INST_ID,
        native_instrument_id=ETH_NATIVE,
        collected_at_utc=collected if collected_utc is None else collected_utc,
    )


def _write_snapshot(
    tmp_path: Path,
    *,
    observations: list[object],
    mutate_manifest_digest: str | None = None,
    write_sha_manifest: bool = True,
) -> Path:
    state = _eth_state()
    for obs in observations:
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    manifest = persist_archive_snapshot_v0([state], output_dir=tmp_path)
    if mutate_manifest_digest is not None:
        manifest_path = tmp_path / "archive_manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["archive_digest"] = mutate_manifest_digest
        manifest_path.write_text(
            json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    if write_sha_manifest:
        write_manifest_sha256_v0(tmp_path)
    return tmp_path


class TestAuditConfigAndBoundaries:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_audit_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["schema_version"] == MODULE_VERSION
        assert module_config["implementation_digest"] == compute_audit_implementation_digest_v0()

    def test_no_forbidden_imports(self) -> None:
        source = AUDIT_MODULE_PATH.read_text(encoding="utf-8")
        cli_source = CLI_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert prefix not in source
            assert prefix not in cli_source


class TestValidArchiveAudits:
    def test_valid_empty_snapshot_without_files(self, tmp_path: Path) -> None:
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.VALID_EMPTY
        assert result.observation_count == 0
        assert result.jsonl_consistency_verified is True

    def test_valid_single_observation_insufficient_data(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(tmp_path, observations=[obs])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA
        assert result.observation_count == 1
        assert result.digest_chain_verified is True
        assert result.manifest_sha256_verify_rc == 0

    def test_valid_multi_observation_pass(self, tmp_path: Path) -> None:
        obs1 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(tmp_path, observations=[obs1, obs2])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.PASS
        assert result.observation_count == 2
        assert result.deterministic_audit_digest is not None

    def test_deterministic_audit_digest(self, tmp_path: Path) -> None:
        obs1 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(tmp_path, observations=[obs1, obs2])
        first = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        second = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert first.deterministic_audit_digest == second.deterministic_audit_digest

    def test_append_only_prefix_preserved(self, tmp_path: Path) -> None:
        prior_dir = tmp_path / "prior"
        current_dir = tmp_path / "current"
        obs1 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(prior_dir, observations=[obs1])
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(current_dir, observations=[obs1, obs2])
        result = audit_archive_snapshot_v0(
            snapshot_dir=current_dir,
            prior_snapshot_dir=prior_dir,
        )
        assert result.status == ArchiveIntegrityAuditStatus.PASS
        assert result.append_only_prefix_verified is True


class TestFailureClasses:
    def _write_raw_jsonl(self, tmp_path: Path, lines: list[str]) -> None:
        (tmp_path / "observations.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_malformed_json(self, tmp_path: Path) -> None:
        self._write_raw_jsonl(tmp_path, ["{not-json"])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.MALFORMED_JSON.value in result.failure_classes

    def test_truncated_final_line(self, tmp_path: Path) -> None:
        (tmp_path / "observations.jsonl").write_text('{"instrument_id":"x"}', encoding="utf-8")
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.TRUNCATED_JSONL_LINE.value in result.failure_classes

    def test_missing_required_field(self, tmp_path: Path) -> None:
        self._write_raw_jsonl(
            tmp_path, ['{"instrument_id":"okx:linear_perpetual:ETH:USDT:USDT:perp"}']
        )
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.MISSING_REQUIRED_FIELD.value in result.failure_classes

    def test_invalid_field_type(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["venue_timestamp_ms"] = "bad"
        self._write_raw_jsonl(tmp_path, [serialize_canonical_json(row)])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.INVALID_FIELD_TYPE.value in result.failure_classes

    def test_digest_mismatch(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["observation_digest"] = "0" * 64
        self._write_raw_jsonl(tmp_path, [serialize_canonical_json(row)])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.DIGEST_MISMATCH.value in result.failure_classes

    def test_bitcoin_instrument_blocked(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        assert obs is not None
        row = serialize_observation_v0(obs)
        row["native_instrument_id"] = "BTC-USDT-SWAP"
        row["observation_digest"] = compute_observation_digest_v0(
            {k: v for k, v in row.items() if k != "observation_digest"}
        )
        self._write_raw_jsonl(tmp_path, [serialize_canonical_json(row)])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert (
            ArchiveIntegrityFailureClass.BITCOIN_INSTRUMENT_BLOCKED.value in result.failure_classes
        )

    def test_out_of_order_timestamp(self, tmp_path: Path) -> None:
        obs1 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        obs2 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        assert obs1 is not None and obs2 is not None
        lines = [
            serialize_canonical_json(serialize_observation_v0(obs1)),
            serialize_canonical_json(serialize_observation_v0(obs2)),
        ]
        self._write_raw_jsonl(tmp_path, lines)
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.OUT_OF_ORDER_TIMESTAMP.value in result.failure_classes

    def test_idempotent_duplicate_allowed(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        assert obs is not None
        row = serialize_canonical_json(serialize_observation_v0(obs))
        self._write_raw_jsonl(tmp_path, [row, row])
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA
        assert result.observation_count == 1

    def test_conflicting_duplicate(self, tmp_path: Path) -> None:
        obs1 = _make_obs("2026-07-11T10:00:00Z", "1000.0", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T10:00:00Z", "2000.0", collected_utc="2026-07-11T12:00:00Z")
        assert obs1 is not None and obs2 is not None
        lines = [
            serialize_canonical_json(serialize_observation_v0(obs1)),
            serialize_canonical_json(serialize_observation_v0(obs2)),
        ]
        self._write_raw_jsonl(tmp_path, lines)
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.CONFLICTING_DUPLICATE.value in result.failure_classes

    def test_archive_digest_mismatch(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(tmp_path, observations=[obs], mutate_manifest_digest="0" * 64)
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.ARCHIVE_DIGEST_MISMATCH.value in result.failure_classes

    def test_manifest_sha256_mismatch(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(tmp_path, observations=[obs], write_sha_manifest=True)
        (tmp_path / "MANIFEST.sha256").write_text(
            "deadbeef  observations.jsonl\n", encoding="utf-8"
        )
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.MANIFEST_MISMATCH.value in result.failure_classes

    def test_manifest_missing_when_required(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(tmp_path, observations=[obs], write_sha_manifest=False)
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path, require_manifest_sha256=True)
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.MANIFEST_MISSING.value in result.failure_classes

    def test_historical_prefix_mutated(self, tmp_path: Path) -> None:
        prior_dir = tmp_path / "prior"
        current_dir = tmp_path / "current"
        obs1 = _make_obs("2026-07-11T10:00:00Z", "1000.0", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(prior_dir, observations=[obs1])
        assert obs1 is not None
        mutated = _make_obs("2026-07-11T10:00:00Z", "2000.0", collected_utc="2026-07-11T11:30:00Z")
        _write_snapshot(current_dir, observations=[mutated, obs2])
        result = audit_archive_snapshot_v0(
            snapshot_dir=current_dir,
            prior_snapshot_dir=prior_dir,
        )
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert (
            ArchiveIntegrityFailureClass.HISTORICAL_PREFIX_MUTATED.value in result.failure_classes
        )

    def test_historical_row_removed(self, tmp_path: Path) -> None:
        prior_dir = tmp_path / "prior"
        current_dir = tmp_path / "current"
        obs1 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(prior_dir, observations=[obs1, obs2])
        _write_snapshot(current_dir, observations=[obs2])
        result = audit_archive_snapshot_v0(
            snapshot_dir=current_dir,
            prior_snapshot_dir=prior_dir,
        )
        assert result.status == ArchiveIntegrityAuditStatus.FAIL
        assert ArchiveIntegrityFailureClass.HISTORICAL_ROW_REMOVED.value in result.failure_classes


class TestCliAdapter:
    def test_cli_validate_only_pass(self, tmp_path: Path) -> None:
        obs1 = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        obs2 = _make_obs("2026-07-11T11:00:00Z", collected_utc="2026-07-11T12:00:00Z")
        _write_snapshot(tmp_path, observations=[obs1, obs2])
        proc = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--enabled",
                "--snapshot-dir",
                str(tmp_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["status"] == ArchiveIntegrityAuditStatus.PASS.value


class TestAuditResultSerialization:
    def test_result_dict_contains_contract_fields(self, tmp_path: Path) -> None:
        result = audit_archive_snapshot_v0(snapshot_dir=tmp_path)
        payload = audit_result_to_dict_v0(result)
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["economic_evaluation_executed"] is False

    def test_manifest_verify_helper_on_snapshot(self, tmp_path: Path) -> None:
        obs = _make_obs("2026-07-11T10:00:00Z", collected_utc="2026-07-11T11:00:00Z")
        _write_snapshot(tmp_path, observations=[obs])
        assert verify_manifest_sha256_v0(tmp_path) == 0
