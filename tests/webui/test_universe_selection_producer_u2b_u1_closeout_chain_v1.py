"""U3 — U2b→U1→producer closeout chain dry verification (no runtime)."""

from __future__ import annotations

import ast
import json
import sys
import uuid
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    parse_manifest_verify_log_rc,
    verify_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1 import build_workflow_dashboard_readmodel_v1
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_fixture_source_v1 import (
    fixture_root_under,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    governed_root_under,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    ENV_PRODUCER_V1_ENABLED,
    ENV_REAL_METADATA_LOADER_V1_ENABLED,
    ENV_REAL_METADATA_SOURCE_PATH,
    ENV_UPSTREAM_FIXTURE_PATH,
    MANIFEST_VERIFY_LOG_FILENAME,
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
    REASON_UPSTREAM_SOURCE_PATH_CONFLICT,
    maybe_write_missing_truth_after_bounded_closeout,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,
    try_load_universe_selection_for_dashboard,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"
FIXTURE_ROOT = fixture_root_under(project_root)
GOVERNED_TEMPLATE_ROOT = governed_root_under(project_root)
PRODUCER_MODULE = (
    project_root
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_producer_v1.py"
)
FORBIDDEN_TOUCH_PREFIXES = (
    "src/execution/",
    "src/risk/",
    "src/governance/",
    ".github/workflows/",
)
FORBIDDEN_SPOT_SYMBOLS = ("BTC/USD", "BTC/EUR", "ETH/USD", "BTCUSD")


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
def _clear_env_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_PRODUCER_V1_ENABLED, raising=False)
    monkeypatch.delenv(ENV_UPSTREAM_FIXTURE_PATH, raising=False)
    monkeypatch.delenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, raising=False)
    monkeypatch.delenv(ENV_REAL_METADATA_SOURCE_PATH, raising=False)


def _seed_metadata_manifest(metadata_dir: Path) -> None:
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(metadata_dir)
    verify_ok, verify_msg = verify_manifest_sha256(metadata_dir)
    assert verify_ok, verify_msg
    (metadata_dir / "MANIFEST_VERIFY.log").write_text(
        f"verify_ok=true\nmessage={verify_msg}\nMANIFEST_VERIFY_RC=0\nSTATUS=OK\n",
        encoding="utf-8",
    )
    write_manifest_sha256(metadata_dir)


def _install_governed_bundle(archive_root: Path, template_name: str) -> Path:
    data = json.loads((GOVERNED_TEMPLATE_ROOT / template_name).read_text(encoding="utf-8"))
    metadata_dir = archive_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = metadata_dir / "futures_instrument_metadata_snapshot.v1.json"
    snapshot_path.write_text(
        (GOVERNED_TEMPLATE_ROOT / "futures_instrument_metadata_snapshot.v1.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    _seed_metadata_manifest(metadata_dir)

    evidence_link = archive_root / "runs" / "paper" / "u2b_evidence"
    evidence_link.mkdir(parents=True, exist_ok=True)
    (evidence_link / "CLOSEOUT.md").write_text("# u2b evidence\n", encoding="utf-8")

    data["metadata_table_ref"] = str(snapshot_path.resolve())
    data["evidence_links"] = [str(evidence_link.resolve())]

    bundle_path = metadata_dir / f"installed_{template_name}"
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return bundle_path.resolve()


def _readmodel_path(archive_root: Path) -> Path:
    return archive_root / READMODELS_DIRNAME / READMODEL_FILENAME


def _synthetic_closeout_bundle(archive_root: Path) -> Path:
    bundle = archive_root / "runs" / "paper" / "p1_u2b_chain_test"
    bundle.mkdir(parents=True)
    (bundle / "CLOSEOUT.md").write_text("# u2b chain test\n", encoding="utf-8")
    return bundle


def _assert_no_spot_selected_truth(text: str) -> None:
    for symbol in FORBIDDEN_SPOT_SYMBOLS:
        assert symbol not in text


def test_tc1_gate_off_unchanged(archive_root: Path) -> None:
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    assert result.enabled is False
    assert result.skipped is True
    assert result.written is False
    assert not _readmodel_path(archive_root).exists()


def test_tc2_loader_gate_on_without_path_fail_closed(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    monkeypatch.setenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    assert result.written is False
    assert result.reason == "ERROR"
    assert not _readmodel_path(archive_root).exists()


def test_tc3_producer_on_without_u2b_loader_missing_truth(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    payload = json.loads(_readmodel_path(archive_root).read_text(encoding="utf-8"))
    assert result.written is True
    assert payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE
    assert payload["missing_truth"]["ranking"] == MISSING_TRUTH_RANKING
    assert payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED


def test_tc4_valid_governed_path_u2b_u1_u3_writes_markers(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    monkeypatch.setenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, "1")
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_REAL_METADATA_SOURCE_PATH, str(bundle_path))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodel_path = _readmodel_path(archive_root)
    assert result.written is True
    assert result.manifest_verify_rc == 0
    ok, msg = verify_manifest_sha256(readmodels_dir)
    assert ok, msg

    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["fixture_marked"] is False
    assert payload["real_metadata_source_marked"] is True
    assert payload["observability_truth_allowed"] is False
    assert payload["non_authorizing"] is True
    assert payload["selected_future"]["symbol"] == "ETHUSDT"
    assert payload["evidence"]["real_metadata_loader"] == (
        "futures_producer_packet_real_metadata_source.v1"
    )
    _assert_no_spot_selected_truth(readmodel_path.read_text(encoding="utf-8"))


def test_tc5_payload_does_not_authorize_observability_truth_promotion(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    monkeypatch.setenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, "1")
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_REAL_METADATA_SOURCE_PATH, str(bundle_path))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    payload = json.loads(_readmodel_path(archive_root).read_text(encoding="utf-8"))
    assert payload["observability_truth_allowed"] is False
    assert payload["real_metadata_source_marked"] is True
    assert payload["non_authorizing"] is True
    assert payload.get("live_authorized") is not True
    assert payload.get("approval") is not True

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is False
    assert reader_result.load_errors == (LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,)
    assert reader_result.universe == ()
    assert reader_result.selected_future is None

    model = build_workflow_dashboard_readmodel_v1(archive_root)
    assert model.universe_selection.loaded is False
    assert model.universe_missing.truth_status == MISSING_TRUTH_UNIVERSE
    assert model.top20_missing.truth_status == MISSING_TRUTH_RANKING
    assert model.selected_future_missing.truth_status == MISSING_TRUTH_SELECTED


def test_tc6_conflict_fixture_and_real_metadata_paths_fail_closed(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    monkeypatch.setenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, "1")
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    fixture = FIXTURE_ROOT / "futures_packet_valid_minimal.json"
    monkeypatch.setenv(ENV_REAL_METADATA_SOURCE_PATH, str(bundle_path))
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    assert result.written is False
    assert result.reason == "ERROR"
    assert REASON_UPSTREAM_SOURCE_PATH_CONFLICT in (result.error or "")
    assert not _readmodel_path(archive_root).exists()


def test_tc7_manifest_verify_log_rc_zero_on_readmodels(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    monkeypatch.setenv(ENV_REAL_METADATA_LOADER_V1_ENABLED, "1")
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_REAL_METADATA_SOURCE_PATH, str(bundle_path))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u2b_chain_test",
        source_stage="paper",
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    verify_log = readmodels_dir / MANIFEST_VERIFY_LOG_FILENAME
    assert result.written is True
    assert verify_log.is_file()
    assert "MANIFEST_VERIFY_RC=0" in verify_log.read_text(encoding="utf-8")
    rc, msg, log_name = parse_manifest_verify_log_rc(readmodels_dir)
    assert rc == 0, msg
    assert log_name == MANIFEST_VERIFY_LOG_FILENAME


def test_tc8_no_forbidden_imports_in_producer_module() -> None:
    forbidden_import_roots = ("urllib", "requests", "httpx", "aiohttp", "socket")
    tree = ast.parse(PRODUCER_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots

    rel = PRODUCER_MODULE.relative_to(project_root).as_posix()
    for prefix in FORBIDDEN_TOUCH_PREFIXES:
        assert not rel.startswith(prefix)
