"""Contract tests for self-accumulated OI historical depth sufficiency and materialization admissibility v0."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_and_scope_parking_reopen_v0 import (
    assess_source_admissibility_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    ArchiveIntegrityAuditStatus,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0 import (
    FreshnessStatus,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    CONFIRM_GO,
    MATERIALIZATION_STATUS_DEFERRED,
    MATERIALIZATION_STATUS_READY,
    MINIMUM_INSTRUMENT_COUNT,
    NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY,
    REQUIRED_CONTIGUOUS_BARS,
    REQUIRED_OBSERVATION_COUNT,
    AdmissibilityReason,
    assessment_to_dict_v0,
    assess_materialization_admissibility_from_states_v0,
    assess_materialization_admissibility_v0,
    build_bridge_contract_v0,
    build_collection_termination_contract_v0,
    build_contract_config_v0,
    build_gap_and_continuity_contract_v0,
    compute_contiguous_tail_bars,
    default_sufficiency_policy_v0,
    panel_minimum_instrument_gate_unchanged_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_overlap_validation_v0 import (
    OverlapValidationStatus,
    OverlapValidationVerdict,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/"
    "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
    "and_materialization_admissibility_contract_v0.json"
)
MODULE_PATH = (
    REPO_ROOT / "src/research/"
    "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
    "and_materialization_admissibility_contract_v0.py"
)
CLI_PATH = (
    REPO_ROOT / "scripts/ops/"
    "assess_okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
    "and_materialization_admissibility_v0.py"
)
PRODUCTION_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)

ETH_INST_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
ETH_NATIVE = "ETH-USDT-SWAP"
SOL_INST_ID = "okx:linear_perpetual:SOL:USDT:USDT:perp"
SOL_NATIVE = "SOL-USDT-SWAP"
AVAX_INST_ID = "okx:linear_perpetual:AVAX:USDT:USDT:perp"
AVAX_NATIVE = "AVAX-USDT-SWAP"
MATIC_INST_ID = "okx:linear_perpetual:MATIC:USDT:USDT:perp"
MATIC_NATIVE = "MATIC-USDT-SWAP"
LINK_INST_ID = "okx:linear_perpetual:LINK:USDT:USDT:perp"
LINK_NATIVE = "LINK-USDT-SWAP"
AS_OF_UTC = "2026-07-11T22:07:21Z"

INSTRUMENTS = (
    (ETH_INST_ID, ETH_NATIVE),
    (SOL_INST_ID, SOL_NATIVE),
    (AVAX_INST_ID, AVAX_NATIVE),
    (MATIC_INST_ID, MATIC_NATIVE),
    (LINK_INST_ID, LINK_NATIVE),
)


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
    collected_utc: str,
    oi: str = "1000.0",
):
    return normalize_forward_open_interest_observation_v0(
        _oi_row(ts_utc, oi),
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        collected_at_utc=collected_utc,
    )


def _hourly_series(
    *,
    instrument_id: str,
    native_instrument_id: str,
    start_utc: str,
    bar_count: int,
    collected_offset_hours: int = 1,
):
    start = datetime.strptime(start_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    observations = []
    for offset in range(bar_count):
        ts = start + timedelta(hours=offset)
        ts_utc = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        collected = (ts + timedelta(hours=collected_offset_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        obs = _make_obs(
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            ts_utc=ts_utc,
            collected_utc=collected,
        )
        assert obs is not None
        observations.append(obs)
    return observations


def _write_snapshot(tmp_path: Path, observations: list[object]) -> Path:
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


class TestContractConfigAndBridge:
    def test_config_exists_and_bridge_excludes_fixed_2024_horizon(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_contract_config_v0()
        bridge = build_bridge_contract_v0()
        assert config["go_token"] == CONFIRM_GO
        assert bridge["excluded_horizon_owner"] == "okx_historical_open_interest_public_fetch_v0"
        assert "2024" in bridge["excluded_horizon_note"]
        assert module_config["authority_effect"] == "NONE"
        assert build_gap_and_continuity_contract_v0()["maximum_allowed_gap_bars"] == 0
        assert (
            build_collection_termination_contract_v0()["next_canonical_scope_after_sufficiency"]
            == NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY
        )

    def test_policy_derived_from_pit_semantics(self) -> None:
        policy = default_sufficiency_policy_v0()
        assert REQUIRED_CONTIGUOUS_BARS == LOOKBACK_K + SIGNAL_LAG_BARS + 1
        assert policy.required_contiguous_bars == REQUIRED_CONTIGUOUS_BARS
        assert policy.required_observation_count == REQUIRED_OBSERVATION_COUNT
        assert policy.minimum_instrument_count == MINIMUM_INSTRUMENT_COUNT

    def test_no_forbidden_runtime_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        cli_source = CLI_PATH.read_text(encoding="utf-8")
        for prefix in ("src.execution", "src.scheduler", "src.broker"):
            assert prefix not in source
            assert prefix not in cli_source


class TestProductionLikeStateFailClosed:
    @pytest.mark.skipif(not PRODUCTION_ARCHIVE.is_dir(), reason="production archive unavailable")
    def test_current_production_archive_remains_fail_closed(self) -> None:
        result = assess_materialization_admissibility_v0(
            archive_root=PRODUCTION_ARCHIVE,
            as_of_utc=AS_OF_UTC,
        )
        assert result.current_observation_count == 5
        assert result.current_instrument_count == 1
        assert result.historical_depth_sufficient is False
        assert result.dataset_materialization_allowed is False
        assert result.materialization_status == MATERIALIZATION_STATUS_DEFERRED
        assert result.collection_continue_required is True
        assert result.next_canonical_scope is None
        assert AdmissibilityReason.GAP_EXCEEDS_MAXIMUM_ALLOWED.value in result.reason_codes
        assert (
            AdmissibilityReason.FIXED_2024_PUBLIC_FETCH_HORIZON_NOT_APPLICABLE.value
            in result.reason_codes
        )

    def test_production_like_gap_state_fail_closed(self, tmp_path: Path) -> None:
        observations = [
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T11:00:00Z",
                collected_utc="2026-07-11T12:00:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T12:00:00Z",
                collected_utc="2026-07-11T13:00:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T20:00:00Z",
                collected_utc="2026-07-11T21:00:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T21:00:00Z",
                collected_utc="2026-07-11T22:00:00Z",
            ),
            _make_obs(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                ts_utc="2026-07-11T22:00:00Z",
                collected_utc="2026-07-11T23:00:00Z",
            ),
        ]
        snapshot = _write_snapshot(tmp_path, [obs for obs in observations if obs is not None])
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc=AS_OF_UTC,
        )
        assert result.current_observation_count == 5
        assert result.current_contiguous_tail_bars == 3
        assert result.historical_depth_sufficient is False
        assert result.dataset_materialization_allowed is False


class TestThresholdAndContinuity:
    def test_below_threshold_stays_false(self, tmp_path: Path) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=REQUIRED_CONTIGUOUS_BARS - 1,
        )
        snapshot = _write_snapshot(tmp_path, observations)
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T18:00:00Z",
        )
        assert result.historical_depth_sufficient is False
        assert result.continuity_sufficient is False

    def test_exact_threshold_with_full_panel_passes(self, tmp_path: Path) -> None:
        observations = []
        start = "2026-07-11T10:00:00Z"
        for instrument_id, native in INSTRUMENTS:
            observations.extend(
                _hourly_series(
                    instrument_id=instrument_id,
                    native_instrument_id=native,
                    start_utc=start,
                    bar_count=REQUIRED_CONTIGUOUS_BARS,
                )
            )
        snapshot = _write_snapshot(tmp_path, observations)
        as_of = "2026-07-11T16:00:00Z"
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc=as_of,
        )
        assert result.current_observation_count == REQUIRED_OBSERVATION_COUNT
        assert result.current_instrument_count == MINIMUM_INSTRUMENT_COUNT
        assert result.current_contiguous_tail_bars == REQUIRED_CONTIGUOUS_BARS
        assert result.continuity_sufficient is True
        assert result.instrument_coverage_sufficient is True
        assert result.sample_sufficiency_met is True
        assert result.historical_depth_sufficient is True
        assert result.dataset_materialization_allowed is True
        assert result.materialization_status == MATERIALIZATION_STATUS_READY
        assert result.collection_continue_required is False
        assert result.collection_termination_condition is True
        assert result.next_canonical_scope == NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY

    def test_gap_over_allowed_threshold_blocks(self, tmp_path: Path) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=3,
        )
        gap_obs = _make_obs(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            ts_utc="2026-07-11T20:00:00Z",
            collected_utc="2026-07-11T21:00:00Z",
        )
        assert gap_obs is not None
        observations.append(gap_obs)
        snapshot = _write_snapshot(tmp_path, observations)
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T21:00:00Z",
        )
        assert result.historical_depth_sufficient is False
        assert AdmissibilityReason.GAP_EXCEEDS_MAXIMUM_ALLOWED.value in result.reason_codes

    def test_insufficient_instrument_count_blocks(self, tmp_path: Path) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=REQUIRED_CONTIGUOUS_BARS,
        )
        snapshot = _write_snapshot(tmp_path, observations)
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T17:00:00Z",
        )
        assert result.instrument_coverage_sufficient is False
        assert result.historical_depth_sufficient is False
        assert AdmissibilityReason.INSUFFICIENT_INSTRUMENT_COUNT.value in result.reason_codes

    def test_stale_freshness_blocks_materialization(self, tmp_path: Path) -> None:
        observations = []
        for instrument_id, native in INSTRUMENTS:
            observations.extend(
                _hourly_series(
                    instrument_id=instrument_id,
                    native_instrument_id=native,
                    start_utc="2026-07-11T01:00:00Z",
                    bar_count=REQUIRED_CONTIGUOUS_BARS,
                )
            )
        snapshot = _write_snapshot(tmp_path, observations)
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T20:00:00Z",
        )
        assert result.historical_depth_sufficient is True
        assert result.dataset_materialization_allowed is False
        assert AdmissibilityReason.STALE_FRESHNESS.value in result.reason_codes


class TestInvariants:
    def test_materialization_requires_historical_depth(self, tmp_path: Path) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=2,
        )
        snapshot = _write_snapshot(tmp_path, observations)
        result = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T13:00:00Z",
        )
        assert result.historical_depth_sufficient is False
        assert result.dataset_materialization_allowed is False

    def test_ratification_delegates_to_contract_assessment(self) -> None:
        states = [
            InstrumentArchiveStateV0(
                instrument_id=ETH_INST_ID,
                native_instrument_id=ETH_NATIVE,
                observations=_hourly_series(
                    instrument_id=ETH_INST_ID,
                    native_instrument_id=ETH_NATIVE,
                    start_utc="2026-07-11T10:00:00Z",
                    bar_count=2,
                ),
            )
        ]
        materialization = assess_materialization_admissibility_from_states_v0(
            states=states,
            archive_root="/tmp/unused",
            as_of_utc="2026-07-11T13:00:00Z",
            integrity_status=ArchiveIntegrityAuditStatus.PASS,
            freshness_status=FreshnessStatus.OK.value,
        )
        assessment = assess_source_admissibility_v0(
            overlap_result={
                "status": OverlapValidationStatus.PASS.value,
                "verdict": OverlapValidationVerdict.PASS.value,
            },
            correction_reexecution_report={
                "PROVENANCE_VALIDATION_PASS": True,
                "INTEGRITY_AUDIT_PASS": True,
                "APPEND_ONLY_PRESERVED": True,
                "HISTORICAL_EVIDENCE_PRESERVED": True,
            },
            observation_count=2,
            materialization_assessment=materialization,
        )
        assert assessment.historical_depth_sufficient is False
        assert assessment.source_sufficient_for_panel_materialization is False

    def test_panel_minimum_instrument_gate_reused(self) -> None:
        assert panel_minimum_instrument_gate_unchanged_v0(["a"]) is False
        assert panel_minimum_instrument_gate_unchanged_v0([f"i{n}" for n in range(5)]) is True

    def test_contiguous_tail_computation(self) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=3,
        )
        assert compute_contiguous_tail_bars(observations) == 3

    def test_deterministic_repeat(self, tmp_path: Path) -> None:
        observations = _hourly_series(
            instrument_id=ETH_INST_ID,
            native_instrument_id=ETH_NATIVE,
            start_utc="2026-07-11T10:00:00Z",
            bar_count=3,
        )
        snapshot = _write_snapshot(tmp_path, observations)
        first = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T14:00:00Z",
        )
        second = assess_materialization_admissibility_v0(
            archive_root=snapshot,
            as_of_utc="2026-07-11T14:00:00Z",
        )
        assert assessment_to_dict_v0(first) == assessment_to_dict_v0(second)


class TestCli:
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

    def test_cli_enabled_valid_empty(self, tmp_path: Path) -> None:
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
        assert payload["historical_depth_sufficient"] is False
