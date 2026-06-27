"""Producer tests for Package I offline BACKTEST LineageRef production."""

from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    BACKTEST_LINEAGE_REF_REQUIRED,
    BACKTEST_OWNER_DOMAIN,
    RUN_SUMMARY_REL_PATH,
    BacktestLineageRefProducerError,
    build_backtest_lineage_ref_from_run_summary,
    compute_backtest_lineage_ref_digest,
    produce_backtest_lineage_ref_v1,
    produce_backtest_lineage_ref_v1_to_path,
    serialize_backtest_lineage_ref_v1,
    write_backtest_lineage_ref_v1_atomic,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateType,
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    lineage_ref_to_mapping,
    serialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

FIXED_STARTED = "2025-01-15T10:00:00+00:00"
FIXED_FINISHED = "2025-01-15T10:05:00+00:00"
RUN_ID = "test-run-123"
LINEAGE_ID = "11111111-1111-4111-8111-111111111111"
CONTRACT_REF = "22222222-2222-4222-8222-222222222222"


def _minimal_run_summary_data(*, run_id: str = RUN_ID, status: str = "FINISHED") -> dict:
    return {
        "run_id": run_id,
        "started_at_utc": FIXED_STARTED,
        "finished_at_utc": FIXED_FINISHED,
        "status": status,
        "tracking_backend": "null",
    }


def _full_run_summary_data(*, run_id: str = RUN_ID, status: str = "FINISHED") -> dict:
    return {
        **_minimal_run_summary_data(run_id=run_id, status=status),
        "tags": {"experiment": "test", "version": "v1"},
        "params": {"fast_period": 10, "slow_period": 20, "enabled": True},
        "metrics": {"sharpe": 1.5, "total_return": 0.25},
        "artifacts": ["results/equity_curve.png", "results/trades.csv"],
        "git_sha": "abc123def456",
        "worktree": "clever-varahamihira",
        "hostname": "test-machine",
    }


def _write_run_dir(
    tmp_path: Path,
    data: dict,
    *,
    run_dir_name: str = "completed-run",
) -> Path:
    run_dir = tmp_path / run_dir_name
    run_dir.mkdir()
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    summary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return run_dir


def test_minimal_completed_run_produces_valid_backtest_ref(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    ref = result.ref
    assert ref.ref_type == LineageRefType.BACKTEST
    assert ref.ref_id == RUN_ID
    assert ref.relation == LineageRelation.EVALUATES
    assert ref.owner_domain == BACKTEST_OWNER_DOMAIN
    assert ref.required is BACKTEST_LINEAGE_REF_REQUIRED
    assert ref.artifact_path == RUN_SUMMARY_REL_PATH
    assert ref.digest == compute_backtest_lineage_ref_digest(
        RunSummary.read_json(result.run_summary_path)
    )


def test_full_completed_run_produces_valid_backtest_ref(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _full_run_summary_data())
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    assert result.ref.ref_id == RUN_ID
    payload = json.loads(serialize_backtest_lineage_ref_v1(result.ref))
    assert "params" not in payload
    assert "metrics" not in payload
    assert "returns" not in payload
    assert "equity" not in payload
    assert "trades" not in payload


def test_uses_existing_run_summary_loader(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    calls: list[Path] = []

    original = RunSummary.read_json

    def _tracked_read(path):  # type: ignore[no-untyped-def]
        calls.append(Path(path))
        return original(path)

    monkeypatch.setattr(RunSummary, "read_json", _tracked_read)
    produce_backtest_lineage_ref_v1(run_dir=run_dir)
    assert calls == [run_dir / RUN_SUMMARY_REL_PATH]


def test_run_id_exactly_adopted_from_run_summary(tmp_path: Path) -> None:
    explicit_id = "canonical-run-id-42"
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(run_id=explicit_id))
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    assert result.ref.ref_id == explicit_id


def test_deterministic_digest_and_relative_artifact_path(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _full_run_summary_data())
    first = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    second = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    assert first.ref.digest == second.ref.digest
    assert first.ref.artifact_path == RUN_SUMMARY_REL_PATH
    assert not first.ref.artifact_path.startswith("/")


def test_byte_identical_canonical_json_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    first = serialize_backtest_lineage_ref_v1(result.ref)
    second = serialize_backtest_lineage_ref_v1(result.ref)
    assert first == second
    assert json.loads(first) == json.loads(second)


def test_candidate_lineage_manifest_v1_accepts_producer_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    ref = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref
    fixed_now = datetime(2026, 6, 27, 18, 0, 0, tzinfo=timezone.utc)
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": LINEAGE_ID,
            "candidate_id": "candidate-package-i-001",
            "candidate_type": CandidateType.CONFIG_PATCH_BUNDLE.value,
            "candidate_contract_ref": CONTRACT_REF,
            "refs": [lineage_ref_to_mapping(ref)],
            "created_at": fixed_now.isoformat(),
        },
        created_at=fixed_now,
    )
    payload = json.loads(serialize_candidate_lineage_manifest_v1(manifest))
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, (phase, errors)
    assert payload["refs"][0]["ref_id"] == RUN_ID
    assert payload["refs"][0]["ref_type"] == LineageRefType.BACKTEST.value


def test_missing_run_dir_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(BacktestLineageRefProducerError, match="run_dir not found"):
        produce_backtest_lineage_ref_v1(run_dir=tmp_path / "missing")


def test_run_path_is_file_not_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(BacktestLineageRefProducerError, match="not a directory"):
        produce_backtest_lineage_ref_v1(run_dir=file_path)


def test_missing_run_summary_json_fails_closed(tmp_path: Path) -> None:
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()
    with pytest.raises(BacktestLineageRefProducerError, match="run_summary.json not found"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


def test_invalid_json_fails_closed(tmp_path: Path) -> None:
    run_dir = tmp_path / "bad-json-run"
    run_dir.mkdir()
    (run_dir / RUN_SUMMARY_REL_PATH).write_text("{not-json", encoding="utf-8")
    with pytest.raises(BacktestLineageRefProducerError, match="invalid run_summary.json"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


def test_unknown_fields_fail_closed(tmp_path: Path) -> None:
    data = _minimal_run_summary_data()
    data["unknown_field"] = "forbidden"
    run_dir = _write_run_dir(tmp_path, data)
    with pytest.raises(BacktestLineageRefProducerError, match="invalid run_summary.json"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


def test_missing_run_id_fails_closed(tmp_path: Path) -> None:
    data = _minimal_run_summary_data()
    del data["run_id"]
    run_dir = _write_run_dir(tmp_path, data)
    with pytest.raises(BacktestLineageRefProducerError, match="invalid run_summary.json"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


@pytest.mark.parametrize("run_id", ["", "   "])
def test_empty_or_invalid_run_id_fails_closed(tmp_path: Path, run_id: str) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(run_id=run_id))
    with pytest.raises(BacktestLineageRefProducerError, match="run_id"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


@pytest.mark.parametrize("status", ["RUNNING", "FAILED", "KILLED"])
def test_non_completed_run_fails_closed(tmp_path: Path, status: str) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(status=status))
    with pytest.raises(BacktestLineageRefProducerError, match="not completed"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


def test_run_dir_symlink_fails_closed(tmp_path: Path) -> None:
    real_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(), run_dir_name="real-run")
    link = tmp_path / "linked-run"
    link.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(BacktestLineageRefProducerError, match="must not be a symlink"):
        produce_backtest_lineage_ref_v1(run_dir=link)


def test_run_summary_symlink_fails_closed(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-with-link"
    run_dir.mkdir()
    external = tmp_path / "external_summary.json"
    external.write_text(json.dumps(_minimal_run_summary_data()), encoding="utf-8")
    (run_dir / RUN_SUMMARY_REL_PATH).symlink_to(external)
    with pytest.raises(BacktestLineageRefProducerError, match="must not be a symlink"):
        produce_backtest_lineage_ref_v1(run_dir=run_dir)


def test_mtime_does_not_change_digest(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    first = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref.digest
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    old = summary_path.stat().st_mtime
    os.utime(summary_path, (old + 3600, old + 3600))
    second = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref.digest
    assert first == second


def test_hostname_in_summary_does_not_change_ref_id_or_digest(tmp_path: Path) -> None:
    base = _minimal_run_summary_data()
    run_dir_a = _write_run_dir(tmp_path, base, run_dir_name="run-a")
    mutated = dict(base)
    mutated["hostname"] = "other-host"
    run_dir_b = _write_run_dir(tmp_path, mutated, run_dir_name="run-b")
    ref_a = produce_backtest_lineage_ref_v1(run_dir=run_dir_a).ref
    ref_b = produce_backtest_lineage_ref_v1(run_dir=run_dir_b).ref
    assert ref_a.ref_id == ref_b.ref_id
    assert ref_a.digest == ref_b.digest


def test_run_summary_file_not_modified(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    before = summary_path.read_bytes()
    produce_backtest_lineage_ref_v1(run_dir=run_dir)
    assert summary_path.read_bytes() == before


def test_atomic_writer_success_and_fail_closed_existing(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    ref = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref
    output_path = tmp_path / "ref.json"
    write_backtest_lineage_ref_v1_atomic(ref, output_path)
    assert output_path.is_file()
    with pytest.raises(BacktestLineageRefProducerError, match="already exists"):
        write_backtest_lineage_ref_v1_atomic(ref, output_path)


def test_end_to_end_producer_writes_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    output_path = tmp_path / "out" / "backtest_ref.json"
    produce_backtest_lineage_ref_v1_to_path(run_dir=run_dir, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_type"] == LineageRefType.BACKTEST.value
    assert payload["ref_id"] == RUN_ID


def test_digest_matches_compute_content_sha256_of_stable_summary_fields() -> None:
    summary = RunSummary(**_full_run_summary_data())
    ref = build_backtest_lineage_ref_from_run_summary(summary)
    stable_payload = {
        "run_id": summary.run_id,
        "started_at_utc": summary.started_at_utc,
        "finished_at_utc": summary.finished_at_utc,
        "status": summary.status,
        "tracking_backend": summary.tracking_backend,
    }
    assert ref.digest == compute_content_sha256(stable_payload)


def test_non_writable_output_parent_fails_without_partial_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    readonly_parent = tmp_path / "readonly"
    readonly_parent.mkdir()
    output_path = readonly_parent / "ref.json"
    os.chmod(readonly_parent, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(OSError):
            produce_backtest_lineage_ref_v1_to_path(run_dir=run_dir, output_path=output_path)
    finally:
        os.chmod(readonly_parent, stat.S_IRWXU)
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_writer_replace_failure_cleans_tmp_and_leaves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())
    ref = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref
    output_path = tmp_path / "ref.json"
    output_path.write_text('{"existing": true}', encoding="utf-8")
    original = Path.replace

    def _fail_replace(self, target):  # type: ignore[no-untyped-def]
        if self.name.endswith(".tmp"):
            raise OSError("forced replace failure")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", _fail_replace)
    with pytest.raises(OSError, match="forced replace failure"):
        write_backtest_lineage_ref_v1_atomic(
            ref,
            output_path,
            fail_closed_if_exists=False,
        )
    assert output_path.read_text(encoding="utf-8") == '{"existing": true}'
    assert list(output_path.parent.glob("*.tmp")) == []


def test_no_backtest_or_runtime_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data())

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("backtest or runtime invocation forbidden")

    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
        _forbidden,
    )
    produce_backtest_lineage_ref_v1(run_dir=run_dir)
