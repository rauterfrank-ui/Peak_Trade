"""U3 — U2a→U1→producer closeout chain dry verification (no runtime)."""

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
from src.webui.workflow_dashboard_readmodel_v1 import (
    build_workflow_dashboard_readmodel_v1,
    to_json_dict,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_fixture_source_v1 import (
    fixture_root_under,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    ENV_PRODUCER_V1_ENABLED,
    ENV_UPSTREAM_FIXTURE_PATH,
    MANIFEST_VERIFY_LOG_FILENAME,
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
    build_upstream_mapped_universe_selection_readmodel,
    maybe_write_missing_truth_after_bounded_closeout,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,
    try_load_universe_selection_for_dashboard,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"
FIXTURE_ROOT = fixture_root_under(project_root)
PRODUCER_MODULE = (
    project_root
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_producer_v1.py"
)
READER_MODULE = (
    project_root
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_reader_v1.py"
)
FORBIDDEN_TOUCH_PREFIXES = (
    "src/execution/",
    "src/risk/",
    "src/governance/",
    ".github/workflows/",
)
FORBIDDEN_SPOT_SYMBOLS = ("BTC/USD", "BTC/EUR", "ETH/USD", "BTCUSD")
ADAPTER_SCRIPTS = (
    project_root / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py",
    project_root / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py",
    project_root / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
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
def _clear_env_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_PRODUCER_V1_ENABLED, raising=False)
    monkeypatch.delenv(ENV_UPSTREAM_FIXTURE_PATH, raising=False)


def _fixture_path(name: str) -> Path:
    return FIXTURE_ROOT / name


def _readmodels_dir(archive_root: Path) -> Path:
    return archive_root / READMODELS_DIRNAME


def _readmodel_path(archive_root: Path) -> Path:
    return _readmodels_dir(archive_root) / READMODEL_FILENAME


def _synthetic_closeout_bundle(archive_root: Path) -> Path:
    bundle = archive_root / "runs" / "paper" / "p1_u3_chain_test"
    bundle.mkdir(parents=True)
    (bundle / "CLOSEOUT.md").write_text("# u3 chain test\n", encoding="utf-8")
    return bundle


def _assert_no_spot_selected_truth(text: str) -> None:
    for symbol in FORBIDDEN_SPOT_SYMBOLS:
        assert symbol not in text


def test_tc1_gate_off_unchanged(archive_root: Path) -> None:
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    assert result.enabled is False
    assert result.skipped is True
    assert result.written is False
    assert result.reason == "DISABLED"
    assert not _readmodel_path(archive_root).exists()


def test_tc2_gate_on_without_fixture_path_missing_truth(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodel_path = _readmodel_path(archive_root)
    assert result.written is True
    assert result.manifest_verify_rc == 0
    assert readmodel_path.is_file()

    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE
    assert payload["missing_truth"]["ranking"] == MISSING_TRUTH_RANKING
    assert payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED
    assert payload.get("fixture_marked") is not True
    _assert_no_spot_selected_truth(readmodel_path.read_text(encoding="utf-8"))


def test_tc3_gate_on_valid_fixture_u2a_u1_producer_writes_fixture_marked(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodel_path = _readmodel_path(archive_root)
    assert result.written is True
    assert result.manifest_verify_rc == 0
    ok, msg = verify_manifest_sha256(readmodels_dir)
    assert ok, msg

    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["fixture_marked"] is True
    assert payload["non_authorizing"] is True
    assert payload["selected_future"]["symbol"] == "ETHUSDT"
    assert payload["evidence"]["upstream_adapter"] == "futures_universe_upstream_adapter.v1"
    assert str(fixture) in payload["evidence"]["links"]
    _assert_no_spot_selected_truth(readmodel_path.read_text(encoding="utf-8"))


def test_tc4_reader_does_not_promote_fixture_marked_as_ssr_truth(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )
    assert hook_result.written is True

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is False
    assert reader_result.load_errors == (LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,)
    assert reader_result.universe == ()
    assert reader_result.selected_future is None

    model = build_workflow_dashboard_readmodel_v1(archive_root)
    assert model.universe_selection.loaded is False
    assert model.universe_missing.truth_status == MISSING_TRUTH_UNIVERSE
    assert model.top20_missing.truth_status == MISSING_TRUTH_RANKING
    assert model.selected_future_missing.truth_status == MISSING_TRUTH_SELECTED
    _assert_no_spot_selected_truth(str(to_json_dict(model)))


def test_tc5_empty_fixture_missing_truth_no_dummy(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_missing_empty.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodel_path = _readmodel_path(archive_root)
    assert result.written is True
    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["fixture_marked"] is True
    assert payload["universe"] == []
    assert payload["ranking"] == []
    assert payload["selected_future"] == {"truth_status": "NOT_PERSISTED"}
    assert payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE
    _assert_no_spot_selected_truth(readmodel_path.read_text(encoding="utf-8"))


def test_tc6_spot_fixture_not_selected_truth(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_spot_invalid.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodel_path = _readmodel_path(archive_root)
    assert result.written is True
    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    selected = payload.get("selected_future")
    assert selected is not None
    assert selected.get("truth_status") != "PERSISTED"
    assert selected.get("symbol") not in FORBIDDEN_SPOT_SYMBOLS
    exclusions = payload.get("evidence", {}).get("eligibility_exclusions", [])
    assert any(item.get("symbol") == "BTC/USD" for item in exclusions)


def test_tc7_forbidden_market_surface_fixture_rejected_at_load(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_forbidden_market_surface.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    assert result.written is False
    assert result.reason == "ERROR"
    assert not _readmodel_path(archive_root).exists()


def test_tc7b_forbidden_upstream_maps_to_missing_truth_via_helper() -> None:
    from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_fixture_source_v1 import (
        FuturesProducerPacketFixtureSourceError,
    )

    fixture = _fixture_path("futures_packet_forbidden_market_surface.json")
    with pytest.raises(FuturesProducerPacketFixtureSourceError):
        build_upstream_mapped_universe_selection_readmodel(fixture_path=fixture)


def test_tc8_no_forbidden_imports_or_side_effects() -> None:
    forbidden_import_roots = ("urllib", "requests", "httpx", "aiohttp", "socket")

    for module_path in (PRODUCER_MODULE, READER_MODULE):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in forbidden_import_roots
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in forbidden_import_roots

    for script in ADAPTER_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert "ENV_UPSTREAM_FIXTURE_PATH" not in text
        assert "write_upstream_mapped_universe_selection_readmodel" not in text


def test_tc8_forbidden_fixture_path_outside_tests_fixtures_rejected(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    outside = tmp_path / "outside_fixture.json"
    outside.write_text("{}", encoding="utf-8")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(outside))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    assert result.written is False
    assert result.reason == "ERROR"
    assert not _readmodel_path(archive_root).exists()


def test_tc9_gated_write_emits_manifest_verify_log(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodels_dir = _readmodels_dir(archive_root)
    verify_log = readmodels_dir / MANIFEST_VERIFY_LOG_FILENAME
    assert result.written is True
    assert verify_log.is_file()
    assert "MANIFEST_VERIFY_RC=0" in verify_log.read_text(encoding="utf-8")


def test_tc10_parse_manifest_verify_log_rc_zero(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodels_dir = _readmodels_dir(archive_root)
    assert result.manifest_verify_rc == 0
    rc, msg, log_name = parse_manifest_verify_log_rc(readmodels_dir)
    assert rc == 0, msg
    assert log_name == MANIFEST_VERIFY_LOG_FILENAME


def test_tc11_manifest_sha256_includes_manifest_verify_log(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = _synthetic_closeout_bundle(archive_root)

    maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodels_dir = _readmodels_dir(archive_root)
    manifest_text = (readmodels_dir / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert MANIFEST_VERIFY_LOG_FILENAME in manifest_text
    ok, msg = verify_manifest_sha256(readmodels_dir)
    assert ok, msg


def test_tc12_fixture_marked_evidence_path_not_approval_or_observability_truth(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    fixture = _fixture_path("futures_packet_valid_minimal.json")
    monkeypatch.setenv(ENV_UPSTREAM_FIXTURE_PATH, str(fixture))
    run_bundle = _synthetic_closeout_bundle(archive_root)

    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_u3_chain_test",
        source_stage="paper",
    )

    readmodels_dir = _readmodels_dir(archive_root)
    verify_log = readmodels_dir / MANIFEST_VERIFY_LOG_FILENAME
    assert hook_result.written is True
    assert verify_log.is_file()
    assert "MANIFEST_VERIFY_RC=0" in verify_log.read_text(encoding="utf-8")

    payload = json.loads(_readmodel_path(archive_root).read_text(encoding="utf-8"))
    assert payload["fixture_marked"] is True
    assert payload["non_authorizing"] is True
    assert payload.get("live_authorized") is not True
    assert payload.get("approval") is not True

    reader_result = try_load_universe_selection_for_dashboard(archive_root)
    assert reader_result.loaded is False
    assert reader_result.load_errors == (LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,)
    _assert_no_spot_selected_truth(_readmodel_path(archive_root).read_text(encoding="utf-8"))
