"""Slice 2c — bounded integration: producer closeout hook → reader → builder chain."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1 import (
    build_workflow_dashboard_readmodel_v1,
    to_json_dict,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MISSING_TRUTH_FUTURE_DETAIL,
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    ENV_PRODUCER_V1_ENABLED,
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
    maybe_write_missing_truth_after_bounded_closeout,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    try_load_universe_selection_for_dashboard,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"
FIXTURE_ARCHIVE = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()
UNIVERSE_FIXTURES = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_readmodel_v1"
)

FORBIDDEN_SPOT_SYMBOLS = ("BTC/USD", "BTC/EUR", "BTCUSD")
MISSING_TRUTH_REASON_CODES = (
    MISSING_TRUTH_UNIVERSE,
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_FUTURE_DETAIL,
)


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


@pytest.fixture(autouse=True)
def _clear_producer_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_PRODUCER_V1_ENABLED, raising=False)


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")


def _readmodel_path(archive_root: Path) -> Path:
    return archive_root / READMODELS_DIRNAME / READMODEL_FILENAME


def _assert_no_spot_dummy_selected_truth(text: str) -> None:
    for symbol in FORBIDDEN_SPOT_SYMBOLS:
        assert symbol not in text


def _synthetic_closeout_bundle(archive_root: Path, *, stage: str = "paper") -> Path:
    run_id = "p1_short_bounded_paper_chain2c_test"
    bundle = archive_root / "runs" / stage / run_id
    bundle.mkdir(parents=True)
    (bundle / "CLOSEOUT.md").write_text(
        "# synthetic closeout bundle for Slice 2c\n", encoding="utf-8"
    )
    (bundle / "RUN_METADATA.json").write_text(
        json.dumps({"run_id": run_id, "stage": stage}) + "\n",
        encoding="utf-8",
    )
    return bundle


def _install_universe_fixture(archive_root: Path, fixture_dir: str) -> Path:
    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / fixture_dir / READMODEL_FILENAME
    dest = readmodels_dir / READMODEL_FILENAME
    shutil.copy2(src, dest)
    write_manifest_sha256(readmodels_dir)
    return dest


def _install_persisted_test_readmodel(archive_root: Path, fixture_dir: str) -> Path:
    """Install readmodel with fixture_marked=false for persisted SSR/builder test paths only."""
    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / fixture_dir / READMODEL_FILENAME
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["fixture_marked"] = False
    payload["source_run_id"] = f"test_persisted_{fixture_dir}_non_fixture_marked"
    dest = readmodels_dir / READMODEL_FILENAME
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_manifest_sha256(readmodels_dir)
    return dest


def test_tc1_gate_off_hook_skips_write_reader_builder_missing_truth(
    archive_root: Path,
) -> None:
    run_bundle = _synthetic_closeout_bundle(archive_root)

    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_short_bounded_paper_chain2c_test",
        source_stage="paper",
    )

    readmodel_path = _readmodel_path(archive_root)
    assert hook_result.enabled is False
    assert hook_result.written is False
    assert hook_result.reason == "DISABLED"
    assert not readmodel_path.exists()

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is False
    assert reader_result.load_errors == ()
    assert reader_result.universe == ()
    assert reader_result.selected_future is None

    model = build_workflow_dashboard_readmodel_v1(archive_root)
    assert model.universe_selection.loaded is False
    assert model.universe_missing.truth_status == MISSING_TRUTH_UNIVERSE
    assert model.top20_missing.truth_status == MISSING_TRUTH_RANKING
    assert model.selected_future_missing.truth_status == MISSING_TRUTH_SELECTED
    assert model.future_detail_missing.truth_status == MISSING_TRUTH_FUTURE_DETAIL
    _assert_no_spot_dummy_selected_truth(str(to_json_dict(model)))


def test_tc2_gate_on_hook_writes_missing_truth_reader_builder_chain(
    archive_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_short_bounded_paper_chain2c_test",
        source_stage="paper",
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodel_path = _readmodel_path(archive_root)
    manifest_path = readmodels_dir / "MANIFEST.sha256"

    assert hook_result.enabled is True
    assert hook_result.written is True
    assert hook_result.manifest_verify_rc == 0
    assert readmodel_path.is_file()
    assert manifest_path.is_file()
    ok, msg = verify_manifest_sha256(readmodels_dir)
    assert ok, msg

    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE
    assert payload["missing_truth"]["ranking"] == MISSING_TRUTH_RANKING
    assert payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED
    assert payload["missing_truth"]["future_detail"] == MISSING_TRUTH_FUTURE_DETAIL
    assert payload["universe"] == []
    assert payload["ranking"] == []
    assert payload["selected_future"] == {"truth_status": "NOT_PERSISTED"}
    _assert_no_spot_dummy_selected_truth(readmodel_path.read_text(encoding="utf-8"))

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is True
    assert reader_result.load_errors == ()
    assert reader_result.universe == ()
    assert reader_result.ranking == ()
    assert reader_result.selected_future is None

    model = build_workflow_dashboard_readmodel_v1(archive_root)
    assert model.universe_selection.loaded is True
    for card in (
        model.universe_missing,
        model.top20_missing,
        model.selected_future_missing,
        model.future_detail_missing,
    ):
        assert card.truth_status in MISSING_TRUTH_REASON_CODES
    assert model.universe_missing.truth_status == MISSING_TRUTH_UNIVERSE
    assert model.top20_missing.truth_status == MISSING_TRUTH_RANKING
    assert model.selected_future_missing.truth_status == MISSING_TRUTH_SELECTED
    assert model.future_detail_missing.truth_status == MISSING_TRUTH_FUTURE_DETAIL
    _assert_no_spot_dummy_selected_truth(str(to_json_dict(model)))


def test_tc3_producer_readmodel_reader_builder_no_invented_futures(
    archive_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    shutil.copytree(FIXTURE_ARCHIVE, archive_root, dirs_exist_ok=True)
    run_bundle = archive_root / "runs" / "paper" / "p2_longer_bounded_paper_20260607T233758Z"

    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p2_longer_bounded_paper_20260607T233758Z",
        source_stage="paper",
    )
    assert hook_result.written is True

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is True
    assert reader_result.load_errors == ()
    assert reader_result.universe == ()
    assert reader_result.ranking == ()
    assert reader_result.selected_future is None

    model = build_workflow_dashboard_readmodel_v1(archive_root)
    assert model.universe_selection.loaded is True
    assert len(model.universe_selection.universe) == 0
    assert model.universe_selection.selected_future is None
    assert model.universe_missing.truth_status == MISSING_TRUTH_UNIVERSE
    assert model.top20_missing.truth_status == MISSING_TRUTH_RANKING
    assert model.selected_future_missing.truth_status == MISSING_TRUTH_SELECTED
    assert model.future_detail_missing.truth_status == MISSING_TRUTH_FUTURE_DETAIL
    assert not any(err for err in model.load_errors if "CONTRACT_INVALID" in err)
    _assert_no_spot_dummy_selected_truth(str(to_json_dict(model)))


def test_tc4_valid_futures_fixture_reader_builder_no_producer_write(
    archive_root: Path,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive_with_futures_fixture"
    shutil.copytree(FIXTURE_ARCHIVE, archive)
    _install_persisted_test_readmodel(archive, "complete_minimal")

    readmodels_dir = archive / READMODELS_DIRNAME
    before = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}

    reader_result = try_load_universe_selection_for_dashboard(archive)
    assert reader_result.loaded is True
    assert reader_result.load_errors == ()
    assert len(reader_result.universe) == 3
    assert reader_result.selected_future is not None
    assert reader_result.selected_future.symbol == "SOLUSDT"
    _assert_no_spot_dummy_selected_truth(str(reader_result))

    model = build_workflow_dashboard_readmodel_v1(archive)
    assert model.universe_selection.loaded is True
    assert model.universe_missing.truth_status == "PERSISTED"
    assert model.top20_missing.truth_status == "PERSISTED"
    assert model.selected_future_missing.truth_status == "PERSISTED"
    assert model.future_detail_missing.truth_status == "AVAILABLE"
    assert model.universe_selection.selected_future is not None
    assert model.universe_selection.selected_future.symbol == "SOLUSDT"
    assert "ETHUSDT" in {row.symbol for row in model.universe_selection.universe}
    _assert_no_spot_dummy_selected_truth(str(to_json_dict(model)))

    after = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}
    assert before == after
