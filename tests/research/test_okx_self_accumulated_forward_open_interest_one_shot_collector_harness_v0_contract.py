"""Contract tests for OKX self-accumulated forward OI one-shot collector harness v0."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    SCOPE_STATUS,
    is_scope_parked,
    is_self_accumulated_archive_allowed,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
    ArchiveAppendVerdict,
    COLLECTION_MODE_FORWARD_ONLY,
)
from src.research.okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0 import (
    CONFIRM_GO,
    DEFAULT_ENABLED,
    CollectionMode,
    HarnessTerminalVerdict,
    build_cli_contract_v0,
    build_harness_config_v0,
    build_latest_oi_request_url_v0,
    build_policy_contract_v0,
    compute_harness_implementation_digest_v0,
    result_to_final_report_dict_v0,
    run_one_shot_collection_cycle_v0,
    validate_operator_go_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0.json"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/collect_okx_self_accumulated_forward_open_interest_one_shot_v0.py"
)
HARNESS_MODULE = (
    REPO_ROOT
    / "src/research/okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0.py"
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


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _fixture_payload(ts_utc: str, oi: str = "1234.5") -> dict:
    return {
        "code": "0",
        "data": [[str(_ms(ts_utc)), oi, "100.0", "2000000.0"]],
    }


class TestPolicyAndConfig:
    def test_default_off_and_operator_go_required(self) -> None:
        assert DEFAULT_ENABLED is False
        policy = build_policy_contract_v0()
        assert policy.default_enabled is False
        assert policy.operator_go_required is True
        assert policy.exactly_one_collection_cycle is True
        assert policy.no_scheduler is True
        assert policy.no_retry_loop is True
        assert policy.research_scope_remains_parked is True
        assert policy.overlap_validation_executed is False

    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_harness_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["default_enabled"] is False
        assert config["scope_status"] == SCOPE_STATUS
        assert config["overlap_validation_status"] == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED
        assert module_config["implementation_digest"] == compute_harness_implementation_digest_v0()

    def test_scope_parked_and_archive_allowed(self) -> None:
        assert is_scope_parked()
        assert is_self_accumulated_archive_allowed()

    def test_invalid_go_token_blocked(self) -> None:
        with pytest.raises(ValueError, match="DEFAULT_OFF_OPERATOR_GO_REQUIRED"):
            validate_operator_go_v0(confirm="WRONG_TOKEN")

    def test_no_runtime_or_scheduler_imports(self) -> None:
        source = HARNESS_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestValidateOnly:
    def test_validate_only_does_not_persist(self, tmp_path: Path) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.VALIDATE_ONLY,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.verdict == HarnessTerminalVerdict.VALIDATE_ONLY_PASS
        assert result.persisted is False
        assert result.request_count == 0
        assert not (tmp_path / "observations.jsonl").exists()
        assert result.observation is not None
        assert result.observation.bar_interval == BAR_INTERVAL
        assert result.observation.collection_mode == COLLECTION_MODE_FORWARD_ONLY
        assert result.overlap_readiness is not None
        assert result.overlap_readiness["status"] == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED

    def test_missing_go_token_fail_closed(self) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm="WRONG",
            mode=CollectionMode.VALIDATE_ONLY,
            instrument=ETH_INST,
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.verdict == HarnessTerminalVerdict.FAIL_CLOSED_OPERATOR_GO


class TestCollectOnce:
    def test_collect_once_single_cycle_persists_manifest(self, tmp_path: Path) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.verdict == HarnessTerminalVerdict.COLLECT_ONCE_COMPLETE
        assert result.persisted is True
        assert result.request_count == 0
        assert (tmp_path / "observations.jsonl").is_file()
        assert (tmp_path / "archive_manifest.json").is_file()
        assert (tmp_path / "MANIFEST.sha256").is_file()
        verify = subprocess.run(
            ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert verify.returncode == 0

    def test_idempotent_duplicate_on_second_collect(self, tmp_path: Path) -> None:
        fixture = _fixture_payload("2026-07-11T11:00:00Z")
        collected_at = "2026-07-11T12:00:00Z"
        first = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc=collected_at,
            fixture_response=fixture,
        )
        second = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc=collected_at,
            fixture_response=fixture,
        )
        assert first.append_result is not None
        assert first.append_result.verdict == ArchiveAppendVerdict.APPENDED
        assert second.append_result is not None
        assert second.append_result.verdict == ArchiveAppendVerdict.DUPLICATE_SKIPPED
        lines = (tmp_path / "observations.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

    def test_conflict_not_overwritten(self, tmp_path: Path) -> None:
        run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z", "1000.0"),
        )
        conflict = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T13:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z", "2000.0"),
        )
        assert conflict.verdict == HarnessTerminalVerdict.FAIL_CLOSED_APPEND
        row = json.loads((tmp_path / "observations.jsonl").read_text(encoding="utf-8").strip())
        assert row["open_interest_raw"] == "1000.0"


class TestInstrumentGates:
    def test_bitcoin_excluded(self) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.VALIDATE_ONLY,
            instrument=BTC_INST,
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.verdict == HarnessTerminalVerdict.FAIL_CLOSED_INELIGIBLE_INSTRUMENT

    def test_provenance_fields_bound(self) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.VALIDATE_ONLY,
            instrument=ETH_INST,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.observation is not None
        assert result.observation.venue_timestamp_utc == "2026-07-11T11:00:00Z"
        assert result.observation.collected_at_utc == "2026-07-11T12:00:00Z"


class TestGapStalenessAndOverlap:
    def test_gap_staleness_preserved(self, tmp_path: Path) -> None:
        run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T09:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T08:00:00Z"),
        )
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.COLLECT_ONCE,
            instrument=ETH_INST,
            output_dir=tmp_path,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        assert result.gap_staleness is not None
        assert result.gap_staleness["status"] == "GAP"
        assert result.overlap_readiness is not None
        assert result.overlap_readiness["overlap_validation_executable"] is True
        assert result.overlap_readiness["status"] == OVERLAP_VALIDATION_STATUS_NOT_EXECUTED


class TestCliContract:
    def test_cli_contract_fields(self) -> None:
        cli = build_cli_contract_v0()
        assert cli.confirm_parameter == "--confirm-go-token"
        assert cli.default_mode == CollectionMode.VALIDATE_ONLY.value

    def test_cli_missing_go_exits_nonzero(self, tmp_path: Path) -> None:
        inst = tmp_path / "inst.json"
        inst.write_text(json.dumps(ETH_INST), encoding="utf-8")
        fixture = tmp_path / "fixture.json"
        fixture.write_text(json.dumps(_fixture_payload("2026-07-11T11:00:00Z")), encoding="utf-8")
        proc = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(CLI_PATH),
                "--confirm-go-token",
                "WRONG",
                "--instrument-file",
                str(inst),
                "--fixture-response",
                str(fixture),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0

    def test_public_request_url_uses_allowlisted_endpoint(self) -> None:
        url = build_latest_oi_request_url_v0(native_instrument_id="ETH-USDT-SWAP")
        assert "/api/v5/rubik/stat/contracts/open-interest-history" in url
        assert "instId=ETH-USDT-SWAP" in url
        assert "limit=1" in url


class TestFinalReport:
    def test_final_report_dict_scope_parked(self) -> None:
        result = run_one_shot_collection_cycle_v0(
            confirm=CONFIRM_GO,
            mode=CollectionMode.VALIDATE_ONLY,
            instrument=ETH_INST,
            collected_at_utc="2026-07-11T12:00:00Z",
            fixture_response=_fixture_payload("2026-07-11T11:00:00Z"),
        )
        report = result_to_final_report_dict_v0(result)
        assert report["scope_status"] == SCOPE_STATUS
        assert report["overlap_validation_executed"] is False
        assert report["runtime_effect"] == "NONE"
