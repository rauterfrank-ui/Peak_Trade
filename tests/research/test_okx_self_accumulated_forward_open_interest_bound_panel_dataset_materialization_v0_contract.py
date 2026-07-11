"""Contract tests for self-accumulated forward OI bound panel dataset materialization v0."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    load_effective_archive_states_from_snapshot_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    CONFIRM_GO,
    DATASET_ID,
    TARGET_INSTRUMENT_COUNT,
    MaterializationTerminalStatus,
    build_materializer_config_v0,
    compare_materialization_manifests_v0,
    compute_bound_panel_calendar_intersection_v0,
    derive_target_instrument_ids_v0,
    materialize_self_accumulated_bound_open_interest_panel_v0,
    materializer_roundtrip_contract_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/"
    "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0.json"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/"
    "materialize_okx_self_accumulated_forward_open_interest_bound_panel_dataset_v0.py"
)
MODULE_PATH = (
    REPO_ROOT / "src/research/"
    "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0.py"
)
PRODUCTION_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)

PANEL_TIMESTAMPS = (
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


def _build_fixture_archive(tmp_path: Path) -> Path:
    archive_dir = tmp_path / "archive"
    states_by_id: dict[str, InstrumentArchiveStateV0] = {}
    for instrument_id, native in CANONICAL_UNIVERSE_BINDING:
        for index, ts_utc in enumerate(PANEL_TIMESTAMPS):
            collected_utc = PANEL_TIMESTAMPS[min(index + 1, len(PANEL_TIMESTAMPS) - 1)]
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


class TestContractConfig:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_materializer_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["dataset_id"] == DATASET_ID
        assert config["target_instrument_count"] == TARGET_INSTRUMENT_COUNT
        assert config["no_fallback_to_399_instrument_dataset"] is True
        assert module_config["target_instrument_count"] == TARGET_INSTRUMENT_COUNT
        assert len(module_config["target_instrument_bindings"]) == TARGET_INSTRUMENT_COUNT

    def test_target_ids_match_canonical_binding(self) -> None:
        expected = tuple(inst_id for inst_id, _native in CANONICAL_UNIVERSE_BINDING)
        assert derive_target_instrument_ids_v0() == expected


class TestPanelCalendar:
    def test_intersection_requires_all_five_instruments(self, tmp_path: Path) -> None:
        archive_dir = _build_fixture_archive(tmp_path)
        states = load_effective_archive_states_from_snapshot_v0(archive_dir)
        calendar, reasons = compute_bound_panel_calendar_intersection_v0(states)
        assert not reasons
        assert calendar == PANEL_TIMESTAMPS


class TestMaterialization:
    def test_fixture_materialization_complete_and_deterministic(self, tmp_path: Path) -> None:
        archive_dir = _build_fixture_archive(tmp_path)
        first_out = tmp_path / "run_1"
        second_out = tmp_path / "run_2"
        first = materialize_self_accumulated_bound_open_interest_panel_v0(
            archive_root=archive_dir,
            output_root=first_out,
        )
        second = materialize_self_accumulated_bound_open_interest_panel_v0(
            archive_root=archive_dir,
            output_root=second_out,
        )
        assert first.status == MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        assert second.status == MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        assert first.instrument_count == TARGET_INSTRUMENT_COUNT
        assert first.row_count_total == TARGET_INSTRUMENT_COUNT * len(PANEL_TIMESTAMPS)
        assert first.panel_time_alignment_pass is True
        diff_empty, _diff = compare_materialization_manifests_v0(
            Path(first.manifest_path),
            Path(second.manifest_path),
        )
        assert diff_empty is True
        manifest = json.loads(Path(first.manifest_path).read_text(encoding="utf-8"))
        assert manifest["no_fallback_to_399_instrument_dataset"] is True
        assert manifest["source_mode"] == "SELF_ACCUMULATED_EFFECTIVE_ARCHIVE_VIEW"

    @pytest.mark.skipif(
        not PRODUCTION_ARCHIVE.is_dir(),
        reason="production archive not available in this environment",
    )
    def test_production_archive_materializes_five_instruments(self, tmp_path: Path) -> None:
        output_root = tmp_path / "production_run"
        result = materialize_self_accumulated_bound_open_interest_panel_v0(
            archive_root=PRODUCTION_ARCHIVE,
            output_root=output_root,
        )
        assert result.status == MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        assert result.instrument_count == TARGET_INSTRUMENT_COUNT
        assert set(result.actual_instrument_ids) == set(derive_target_instrument_ids_v0())
        assert all(item.gap_count == 0 for item in result.per_instrument)


class TestRoundtripContract:
    def test_materializer_roundtrip_contract_exports(self) -> None:
        contract = materializer_roundtrip_contract_v0()
        assert contract["confirm_go"] == CONFIRM_GO
        assert contract["target_instrument_count"] == TARGET_INSTRUMENT_COUNT
        assert "pit_semantics_contract" in contract


class TestRepoSurfaces:
    def test_required_surfaces_exist(self) -> None:
        assert MODULE_PATH.is_file()
        assert CLI_PATH.is_file()
        assert CONFIG_PATH.is_file()

    def test_cli_help(self) -> None:
        import subprocess

        proc = subprocess.run(
            ["python3", str(CLI_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        assert "--confirm-go-token" in proc.stdout
