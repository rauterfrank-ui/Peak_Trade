"""Contract tests for ETH self-accumulated OI gap remediation v0."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (
    CONFIRM_GO_EXECUTION,
    CORRECTED_OBSERVATIONS_JSONL_FILENAME,
    CorrectionExecutionTerminalStatus,
    execute_archive_correction_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    OBSERVATIONS_JSONL_FILENAME,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    compute_observation_digest_v0,
    load_effective_archive_states_from_snapshot_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_eth_gap_remediation_v0 import (
    CONFIRM_GO,
    ETH_INSTRUMENT_ID,
    ETH_NATIVE_INSTRUMENT_ID,
    REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
    GapFetchValidationVerdict,
    build_eth_gap_insert_bound_execution_plan_v0,
    compute_eth_gap_fetch_window_v0,
    execute_eth_gap_remediation_v0,
    normalized_rows_to_gap_insert_observations_v0,
    validate_fetched_gap_bars_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    compute_contiguous_tail_bars,
    compute_max_internal_gap_bars,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = (
    REPO_ROOT
    / "scripts/ops/execute_okx_self_accumulated_forward_open_interest_eth_gap_remediation_v0.py"
)
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_eth_gap_remediation_v0.json"
)
FORBIDDEN_PREFIXES = ("src.execution", "src.scheduler", "src.broker")

PRODUCTION_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _normalized(ts_utc: str, oi: str = "7000000.0") -> NormalizedOpenInterestObservationV0:
    ts_ms = _ms(ts_utc)
    return NormalizedOpenInterestObservationV0(
        instrument_id=ETH_INSTRUMENT_ID,
        native_instrument_id=ETH_NATIVE_INSTRUMENT_ID,
        observation_time_ms=ts_ms,
        observation_time_utc=ts_utc,
        open_interest_raw=oi,
        open_interest_unit="okx_native_contract_count",
        source_schema_version="okx_rubik_open_interest_history.v0",
        source_record_key=f"{ETH_NATIVE_INSTRUMENT_ID}:{ts_ms}",
    )


def _write_gap_archive(tmp_path: Path) -> Path:
    archive_dir = tmp_path / "archive"
    state = InstrumentArchiveStateV0(
        instrument_id=ETH_INSTRUMENT_ID,
        native_instrument_id=ETH_NATIVE_INSTRUMENT_ID,
    )
    for ts, oi in (
        ("2026-07-11T11:00:00Z", "1234.5"),
        ("2026-07-11T12:00:00Z", "1350.0"),
        ("2026-07-11T20:00:00Z", "7438662.71"),
        ("2026-07-11T21:00:00Z", "7443188.78"),
        ("2026-07-11T22:00:00Z", "7451477.31"),
    ):
        row = [str(_ms(ts)), oi, "100.0", "2000000.0"]
        obs = normalize_forward_open_interest_observation_v0(
            row,
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T22:07:20Z",
        )
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    persist_archive_snapshot_v0([state], output_dir=archive_dir)
    write_manifest_sha256_v0(archive_dir)
    return archive_dir


def _gap_rows(collected_at_utc: str = "2026-07-12T00:00:00Z") -> list[dict]:
    rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC]
    return normalized_rows_to_gap_insert_observations_v0(rows, collected_at_utc=collected_at_utc)


class TestConfigAndImports:
    def test_config_and_no_runtime_imports(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["go_token"] == CONFIRM_GO
        assert config["reuse_decision"] == "REUSE_WITH_NARROW_ADAPTER"
        module = (
            REPO_ROOT
            / "src/research/okx_self_accumulated_forward_open_interest_eth_gap_remediation_v0.py"
        )
        cli = CLI_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_PREFIXES:
            assert prefix not in module.read_text(encoding="utf-8")
            assert prefix not in cli


class TestFetchValidation:
    def test_exact_seven_bars_accepted(self) -> None:
        rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC]
        result = validate_fetched_gap_bars_v0(rows)
        assert result.verdict is GapFetchValidationVerdict.PASS

    def test_missing_bar_rejected(self) -> None:
        rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[:-1]]
        result = validate_fetched_gap_bars_v0(rows)
        assert result.verdict is GapFetchValidationVerdict.FAIL_MISSING_BAR

    def test_unexpected_timestamp_rejected(self) -> None:
        rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC] + [
            _normalized("2026-07-11T10:00:00Z")
        ]
        result = validate_fetched_gap_bars_v0(rows)
        assert result.verdict is GapFetchValidationVerdict.FAIL_UNEXPECTED_BAR

    def test_duplicate_timestamp_rejected(self) -> None:
        rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC]
        rows.append(_normalized(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[0]))
        result = validate_fetched_gap_bars_v0(rows)
        assert result.verdict is GapFetchValidationVerdict.FAIL_DUPLICATE_BAR

    def test_wrong_instrument_rejected(self) -> None:
        bad = _normalized(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[0])
        bad = NormalizedOpenInterestObservationV0(
            instrument_id="okx:linear_perpetual:SOL:USDT:USDT:perp",
            native_instrument_id="SOL-USDT-SWAP",
            observation_time_ms=bad.observation_time_ms,
            observation_time_utc=bad.observation_time_utc,
            open_interest_raw=bad.open_interest_raw,
            open_interest_unit=bad.open_interest_unit,
            source_schema_version=bad.source_schema_version,
            source_record_key="SOL-USDT-SWAP:" + str(bad.observation_time_ms),
        )
        result = validate_fetched_gap_bars_v0([bad])
        assert result.verdict is GapFetchValidationVerdict.FAIL_WRONG_INSTRUMENT

    def test_incomplete_gap_rows_rejected(self) -> None:
        rows = [_normalized(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC]
        with pytest.raises(ValueError):
            normalized_rows_to_gap_insert_observations_v0(
                rows[:3], collected_at_utc="2026-07-12T00:00:00Z"
            )


class TestArchiveCorrectionAndEffectiveView:
    def test_observations_jsonl_unchanged_and_gap_inserts_written(self, tmp_path: Path) -> None:
        archive_dir = _write_gap_archive(tmp_path)
        before = (archive_dir / OBSERVATIONS_JSONL_FILENAME).read_bytes()
        gap_rows = _gap_rows()
        plan = build_eth_gap_insert_bound_execution_plan_v0(
            target_archive_path=archive_dir,
            gap_insert_rows=gap_rows,
            collection_execution_id="test-gap-exec-1",
            evidence_ref=str(tmp_path / "evidence"),
        )
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=False,
            execute_mutation=True,
            enabled=True,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert result.status is CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE
        after = (archive_dir / OBSERVATIONS_JSONL_FILENAME).read_bytes()
        assert before == after
        corrected = [
            json.loads(line)
            for line in (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME)
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        gap_venues = {row["venue_timestamp_utc"] for row in gap_rows}
        corrected_gap = [row for row in corrected if row["venue_timestamp_utc"] in gap_venues]
        assert len(corrected_gap) == 7

    def test_existing_corrections_preserved(self, tmp_path: Path) -> None:
        if not PRODUCTION_ARCHIVE.is_dir():
            pytest.skip("production archive unavailable")
        archive_dir = tmp_path / "archive"
        shutil.copytree(PRODUCTION_ARCHIVE, archive_dir)
        before_corrected = (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME).read_bytes()
        gap_rows = _gap_rows()
        plan = build_eth_gap_insert_bound_execution_plan_v0(
            target_archive_path=archive_dir,
            gap_insert_rows=gap_rows,
            collection_execution_id="test-gap-exec-preserve",
            evidence_ref=str(tmp_path / "evidence"),
        )
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
        execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=False,
            execute_mutation=True,
            enabled=True,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        after_text = (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME).read_text(
            encoding="utf-8"
        )
        assert before_corrected.decode("utf-8") in after_text

    def test_second_correction_idempotent(self, tmp_path: Path) -> None:
        archive_dir = _write_gap_archive(tmp_path)
        gap_rows = _gap_rows()
        plan = build_eth_gap_insert_bound_execution_plan_v0(
            target_archive_path=archive_dir,
            gap_insert_rows=gap_rows,
            collection_execution_id="test-gap-exec-idem",
            evidence_ref=str(tmp_path / "evidence"),
        )
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
        first = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=False,
            execute_mutation=True,
            enabled=True,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        snapshot_after_first = {
            rel: (archive_dir / rel).read_bytes()
            for rel in (
                OBSERVATIONS_JSONL_FILENAME,
                CORRECTED_OBSERVATIONS_JSONL_FILENAME,
                "supersession_records.jsonl",
                "archive_manifest.json",
                "MANIFEST.sha256",
            )
            if (archive_dir / rel).is_file()
        }
        second = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=False,
            execute_mutation=True,
            enabled=True,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        snapshot_after_second = {
            rel: (archive_dir / rel).read_bytes() for rel in snapshot_after_first
        }
        assert first.status is CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE
        assert second.status in {
            CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE,
            CorrectionExecutionTerminalStatus.ALREADY_APPLIED_NOOP,
        }
        assert snapshot_after_first == snapshot_after_second

    def test_effective_view_includes_gap_inserts_and_zero_gap(self, tmp_path: Path) -> None:
        archive_dir = _write_gap_archive(tmp_path)
        before_states = load_effective_archive_states_from_snapshot_v0(archive_dir)
        assert len(before_states) == 1
        assert compute_max_internal_gap_bars(before_states[0].observations) == 7
        gap_rows = _gap_rows()
        plan = build_eth_gap_insert_bound_execution_plan_v0(
            target_archive_path=archive_dir,
            gap_insert_rows=gap_rows,
            collection_execution_id="test-effective-view",
            evidence_ref=str(tmp_path / "evidence"),
        )
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
        execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=False,
            execute_mutation=True,
            enabled=True,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        after_states = load_effective_archive_states_from_snapshot_v0(archive_dir)
        assert len(after_states) == 1
        assert len(after_states[0].observations) == 12
        assert compute_max_internal_gap_bars(after_states[0].observations) == 0
        assert compute_contiguous_tail_bars(after_states[0].observations) == 12

    def test_conflicting_correction_fail_closed(self, tmp_path: Path) -> None:
        archive_dir = _write_gap_archive(tmp_path)
        gap_rows = _gap_rows()
        first = dict(gap_rows[0])
        second = dict(gap_rows[0])
        second["open_interest_raw"] = "9999999.0"
        second["observation_digest"] = compute_observation_digest_v0(
            {k: v for k, v in second.items() if k != "observation_digest"}
        )
        (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME).write_text(
            json.dumps(first, sort_keys=True) + "\n" + json.dumps(second, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="EFFECTIVE_VIEW_CONFLICTING_GAP_INSERT"):
            load_effective_archive_states_from_snapshot_v0(archive_dir)


class TestProductionLikeFetchPath:
    @pytest.mark.skipif(not PRODUCTION_ARCHIVE.is_dir(), reason="production archive unavailable")
    def test_live_fetch_validate_and_mutate_production_copy(self, tmp_path: Path) -> None:
        import scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as ingest

        archive_dir = tmp_path / "production_copy"
        shutil.copytree(PRODUCTION_ARCHIVE, archive_dir)
        before_obs = (archive_dir / OBSERVATIONS_JSONL_FILENAME).read_bytes()
        before_manifest = json.loads(
            (archive_dir / "archive_manifest.json").read_text(encoding="utf-8")
        )
        before_digest = before_manifest["archive_digest"]

        def _build_url(path: str, params: dict[str, str]) -> str:
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"https://www.okx.com{path}?{query}"

        result = execute_eth_gap_remediation_v0(
            confirm=CONFIRM_GO,
            enabled=True,
            target_archive_path=archive_dir,
            collected_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            collection_execution_id="live-gap-remediation-test",
            evidence_ref=str(tmp_path / "evidence"),
            fetcher=ingest.okx_public_fetch_v1,
            rate_limiter=ingest.RateLimiter(),
            fetch_with_retry=ingest.fetch_with_retry,
            build_url=_build_url,
            parse_json=lambda body: json.loads(body.decode()),
            raw_dir=tmp_path / "raw",
            execute_mutation=True,
        )
        assert result.fetch_validation.verdict is GapFetchValidationVerdict.PASS
        assert result.status == "REMEDIATION_COMPLETE"
        assert (archive_dir / OBSERVATIONS_JSONL_FILENAME).read_bytes() == before_obs
        after_manifest = json.loads(
            (archive_dir / "archive_manifest.json").read_text(encoding="utf-8")
        )
        assert after_manifest["archive_digest"] == before_digest
        effective = load_effective_archive_states_from_snapshot_v0(archive_dir)
        assert compute_max_internal_gap_bars(effective[0].observations) == 0

    def test_fetch_window_covers_exact_gap(self) -> None:
        window = compute_eth_gap_fetch_window_v0()
        assert window.start_inclusive_utc == REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[0]
        assert window.end_exclusive_utc == "2026-07-11T20:00:00Z"
