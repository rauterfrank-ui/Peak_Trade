"""Contract tests for multi-instrument self-accumulated OI acquisition orchestration v0."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    load_effective_archive_states_from_snapshot_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    MINIMUM_INSTRUMENT_COUNT,
    REQUIRED_CONTIGUOUS_BARS,
    REQUIRED_OBSERVATION_COUNT,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
    CONFIRM_GO,
    REQUIRED_ADDITIONAL_INSTRUMENT_COUNT,
    AcquisitionTerminalStatus,
    build_orchestration_config_v0,
    compute_aligned_fetch_window_v0,
    execute_multi_instrument_acquisition_v0,
    select_additional_instruments_v0,
    validate_post_acquisition_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/"
    "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0.json"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/"
    "execute_okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_v0.py"
)
MODULE_PATH = (
    REPO_ROOT / "src/research/"
    "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0.py"
)
PRODUCTION_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)

ETH_INST_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
ADDITIONAL_NATIVES = ("AVAX-USDT-SWAP", "LINK-USDT-SWAP", "POL-USDT-SWAP", "SOL-USDT-SWAP")


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


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


def _fixture_tail_rows(
    native: str, instrument_id: str
) -> list[NormalizedOpenInterestObservationV0]:
    timestamps = [
        "2026-07-11T18:00:00Z",
        "2026-07-11T19:00:00Z",
        "2026-07-11T20:00:00Z",
        "2026-07-11T21:00:00Z",
        "2026-07-11T22:00:00Z",
        "2026-07-11T23:00:00Z",
    ]
    return [
        _normalized(
            instrument_id=instrument_id,
            native_instrument_id=native,
            ts_utc=ts_utc,
            oi=f"{1000 + index}.0",
        )
        for index, ts_utc in enumerate(timestamps)
    ]


def _fixture_map() -> dict[str, list[NormalizedOpenInterestObservationV0]]:
    fixtures: dict[str, list[NormalizedOpenInterestObservationV0]] = {}
    for instrument_id, native in CANONICAL_UNIVERSE_BINDING:
        if native == "ETH-USDT-SWAP":
            continue
        fixtures[native] = _fixture_tail_rows(native, instrument_id)
    return fixtures


class TestContractConfig:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_orchestration_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["historical_fetch_function"] == "paginate_bounded_open_interest_v0"
        assert (
            config["required_additional_instrument_count"] == REQUIRED_ADDITIONAL_INSTRUMENT_COUNT
        )
        assert module_config["minimum_instrument_count"] == MINIMUM_INSTRUMENT_COUNT
        assert module_config["required_observation_count"] == REQUIRED_OBSERVATION_COUNT

    def test_no_forbidden_runtime_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        cli_source = CLI_PATH.read_text(encoding="utf-8")
        for prefix in ("src.execution", "src.scheduler", "src.broker"):
            assert prefix not in source
            assert prefix not in cli_source


class TestDeterministicSelection:
    def test_selects_four_additional_non_eth_instruments(self) -> None:
        selected = select_additional_instruments_v0([ETH_INST_ID])
        assert len(selected) == REQUIRED_ADDITIONAL_INSTRUMENT_COUNT
        natives = {item.native_instrument_id for item in selected}
        assert "ETH-USDT-SWAP" not in natives
        assert natives == set(ADDITIONAL_NATIVES)

    def test_aligned_fetch_window_has_six_bars(self) -> None:
        window = compute_aligned_fetch_window_v0(tail_end_venue_utc="2026-07-11T23:00:00Z")
        assert window.start_inclusive_utc == "2026-07-11T18:00:00Z"
        assert window.end_exclusive_utc == "2026-07-12T00:00:00Z"
        assert REQUIRED_CONTIGUOUS_BARS == 6


def _eth_only_snapshot(tmp_path: Path) -> Path:
    """Build a one-instrument ETH-only snapshot for expansion tests."""
    snapshot = tmp_path / "archive"
    shutil.copytree(PRODUCTION_ARCHIVE, snapshot)
    lines = (snapshot / "observations.jsonl").read_text(encoding="utf-8").splitlines()
    eth_lines = [line for line in lines if line.strip() and "ETH-USDT-SWAP" in line]
    (snapshot / "observations.jsonl").write_text("\n".join(eth_lines) + "\n", encoding="utf-8")
    manifest_path = snapshot / "archive_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["instrument_count"] = 1
        manifest["observation_count"] = len(eth_lines)
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    return snapshot


@pytest.mark.skipif(not PRODUCTION_ARCHIVE.is_dir(), reason="production archive unavailable")
class TestProductionArchiveExpansion:
    def test_fixture_acquisition_reaches_thresholds(self, tmp_path: Path) -> None:
        snapshot = _eth_only_snapshot(tmp_path)
        before_states = load_effective_archive_states_from_snapshot_v0(snapshot)
        before_inst = len(before_states)
        before_obs = sum(len(state.observations) for state in before_states)

        result = execute_multi_instrument_acquisition_v0(
            confirm=CONFIRM_GO,
            enabled=True,
            target_archive_path=snapshot,
            collected_at_utc="2026-07-12T00:30:00Z",
            as_of_utc="2026-07-12T00:30:00Z",
            fixture_observations_by_native=_fixture_map(),
            execute_mutation=True,
        )
        assert result.status is AcquisitionTerminalStatus.ACQUISITION_COMPLETE
        assert result.instrument_count_before == before_inst
        assert result.instrument_count_after >= MINIMUM_INSTRUMENT_COUNT
        assert result.observation_count_after >= REQUIRED_OBSERVATION_COUNT
        assert result.archive_integrity_pass is True
        assert result.full_history_zero_gap_pass is True
        assert result.observations_jsonl_byte_identical_prefix is True

        validation = validate_post_acquisition_v0(
            target_archive_path=snapshot,
            prior_snapshot_dir=snapshot,
            as_of_utc="2026-07-12T00:30:00Z",
        )
        assert validation["eth_gap_count"] == 0
        assert validation["instrument_count_after"] >= MINIMUM_INSTRUMENT_COUNT
        assert validation["observation_count_after"] >= REQUIRED_OBSERVATION_COUNT

    def test_idempotent_second_run_no_additional_append(self, tmp_path: Path) -> None:
        snapshot = _eth_only_snapshot(tmp_path)
        kwargs = {
            "confirm": CONFIRM_GO,
            "enabled": True,
            "target_archive_path": snapshot,
            "collected_at_utc": "2026-07-12T00:30:00Z",
            "as_of_utc": "2026-07-12T00:30:00Z",
            "fixture_observations_by_native": _fixture_map(),
            "execute_mutation": True,
        }
        first = execute_multi_instrument_acquisition_v0(**kwargs)
        assert first.status is AcquisitionTerminalStatus.ACQUISITION_COMPLETE
        second = execute_multi_instrument_acquisition_v0(**kwargs)
        assert (
            second.status is AcquisitionTerminalStatus.FAIL_CLOSED_NO_ADDITIONAL_INSTRUMENTS_NEEDED
        )


class TestCli:
    def test_cli_default_off(self, tmp_path: Path) -> None:
        proc = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--confirm-go-token",
                CONFIRM_GO,
                "--evidence-dir",
                str(tmp_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        assert "DEFAULT_OFF_ENABLED_FLAG_REQUIRED" in proc.stderr
