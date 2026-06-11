"""Offline tests for run_order_capability_fixture_binding_dry_validation_v1."""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER_SCRIPT = (
    ROOT / "scripts" / "ops" / "run_order_capability_fixture_binding_dry_validation_v1.py"
)
BROWSER_RENDER_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "order_capability"
    / "browser_rendered_vendor_docs_pf_xbtusd_candidate.v1.json"
)
TEST_PACKAGE_MARKER = "RUN_ORDER_CAPABILITY_FIXTURE_BINDING_DRY_VALIDATION_V1_TEST=true"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
CROSSLINK_PACKAGE_MARKER = (
    "ORDER_CAPABILITY_FIXTURE_BINDING_DOCS_TRUTH_MAP_STATIC_CROSSLINK_GUARD_V1=true"
)
PE8_WIRING_GUARD_PACKAGE_MARKER = (
    "ORDER_CAPABILITY_FIXTURE_BINDING_PE8_OFFLINE_DURABLE_CLOSEOUT_WIRING_GUARD_V0=true"
)
PE_WIRING_IMPL_PACKAGE_MARKER = "ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PE_WIRING_IMPL_V1=true"
REQUIRED_OPERATOR_GO_TOKEN = "GO_ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_IMPL_OPERATOR_GO_AUTOFILL_NO_RUN_V1"
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_order_capability_dry_validation_adapter_v1.py"
SHARED_HELPER = ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
RUNNER_REL = "scripts/ops/run_order_capability_fixture_binding_dry_validation_v1.py"
TEST_REL = "tests/ops/test_run_order_capability_fixture_binding_dry_validation_v1.py"


def _durable_archive(tmp_path: Path) -> Path:
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_write_argv(archive: Path, *, run_id: str = "fixture_binding_test_run") -> list[str]:
    return [
        "--fixture",
        str(BROWSER_RENDER_FIXTURE),
        "--archive-root",
        str(archive),
        "--run-id",
        run_id,
    ]


@pytest.fixture(autouse=True)
def _cleanup_archive_roots():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_order_capability_fixture_binding_dry_validation_v1", RUNNER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_runner_script_exists() -> None:
    assert TEST_PACKAGE_MARKER
    assert RUNNER_SCRIPT.is_file()
    assert BROWSER_RENDER_FIXTURE.is_file()


def test_help_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--fixture" in proc.stdout
    assert "--output" in proc.stdout
    assert "--format" in proc.stdout
    assert "--write-evidence" in proc.stdout
    assert "--archive-root" in proc.stdout
    assert "--operator-go-token" in proc.stdout


def test_cli_loads_repo_fixture_and_runs_chain() -> None:
    mod = _load_runner()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(["--fixture", str(BROWSER_RENDER_FIXTURE), "--format", "json"])
    assert rc == 0
    report = json.loads(buf.getvalue())
    assert report["verdict"] == "DRY_VALIDATION_COMPLETE"
    assert report["mode"] == "plan-only"
    assert report["source_type"] == "browser_rendered_vendor_docs_snapshot"
    assert "normalizer" in report
    assert "binding" in report
    assert report["normalizer_verdict"] == "FAIL_CLOSED"
    assert report["binding_verdict"] == "FAIL_CLOSED"


def test_normalizer_binding_chain_executes() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["normalizer"]["schema_valid"] is False
    assert report["binding"]["instrument_rules_offline_bound"] is False
    assert report["fail_closed_status_recognized"] is True


def test_browser_rendered_fixture_remains_candidate_only() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["provider_truth_bound"] is False
    assert report["provider_truth_flipped"] is False
    assert "PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE" in report["reason_codes"]
    assert report["binding_pass_possible_now"] is False


def test_provider_truth_remains_false() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["provider_truth_bound"] is False
    assert report["normalizer"]["provider_truth_bound"] is False
    assert report["normalizer"]["min_size_verified_offline"] is False


def test_missing_min_size_and_qty_step_block_binding_pass() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["missing_min_size"] is True
    assert report["missing_qty_step"] is True
    assert report["binding_pass_possible_now"] is False
    assert "MISSING_MIN_SIZE" in report["reason_codes"]
    assert "MISSING_QTY_STEP" in report["reason_codes"]


def test_ticksize_conflict_remains_fail_closed() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    disposition = json.loads(BROWSER_RENDER_FIXTURE.read_text(encoding="utf-8"))
    assert disposition["browser_render_disposition_v1"]["ticksize_conflict"] is True
    assert report["ticksize_conflict_fail_closed"] is False
    assert report["provider_truth_bound"] is False


def test_ticksize_conflict_fail_closed_when_price_tick_present(tmp_path: Path) -> None:
    mod = _load_runner()
    payload = json.loads(BROWSER_RENDER_FIXTURE.read_text(encoding="utf-8"))
    fixture = tmp_path / "ticksize_conflict_fixture.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    repo_fixture = ROOT / "tests" / ".pytest_fixture_roots" / fixture.name
    repo_fixture.parent.mkdir(parents=True, exist_ok=True)
    repo_fixture.write_text(json.dumps(payload), encoding="utf-8")
    try:
        full_fixture = {
            "schema_version": "order_capability_demo_instrument_rules_fixture.v1",
            "source_class": "ACCEPTABLE_IF_VERSIONED",
            "provenance": {
                "source_type": "browser_rendered_vendor_docs_snapshot",
                "source_uri_or_origin": str(repo_fixture),
                "captured_at": "2026-06-10T08:01:30Z",
                "captured_by_flow": "test",
                "network_authorized_by_go_token": "NONE",
                "raw_payload_hash": "a" * 64,
                "normalized_payload_hash": "b" * 64,
                "schema_version": "order_capability_demo_instrument_rules_fixture.v1",
                "venue": "kraken_futures_demo",
                "host": "demo-futures.kraken.com",
                "instrument": "PF_XBTUSD",
                "value_redacted": True,
                "no_secret_material": True,
                "repo_versioned": True,
            },
            "rules": {
                "min_size": None,
                "qty_step": None,
                "price_tick": "1",
                "qty_precision": None,
                "price_precision": None,
                "cap_feasibility_rule": None,
            },
            "raw_payload": payload,
        }
        repo_fixture.write_text(json.dumps(full_fixture), encoding="utf-8")
        report = mod.build_fixture_binding_dry_validation_report(repo_fixture)
        assert report["ticksize_conflict_fail_closed"] is True
        assert "TICKSIZE_CONFLICT_UNRESOLVED" in report["reason_codes"]
    finally:
        if repo_fixture.exists():
            repo_fixture.unlink()


def test_no_network_secrets_or_env_required() -> None:
    mod = _load_runner()
    tree = ast.parse(RUNNER_SCRIPT.read_text(encoding="utf-8"))
    forbidden_imports = {"requests", "httpx", "urllib", "socket", "os"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                assert root_name not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            root_name = node.module.split(".", 1)[0]
            assert root_name not in forbidden_imports
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["safety_flags"]["no_network"] is True
    assert report["safety_flags"]["no_secrets"] is True


def test_invalid_fixture_path_fails_closed() -> None:
    mod = _load_runner()
    rc = mod.main(["--fixture", str(ROOT / "does_not_exist_fixture.json")])
    assert rc != 0


def test_non_repo_local_fixture_path_fails_closed(tmp_path: Path) -> None:
    mod = _load_runner()
    outside = tmp_path / "outside_fixture.json"
    outside.write_text("{}", encoding="utf-8")
    rc = mod.main(["--fixture", str(outside)])
    assert rc != 0


def test_order_capability_lane_parked_flags() -> None:
    mod = _load_runner()
    report = mod.build_fixture_binding_dry_validation_report(BROWSER_RENDER_FIXTURE)
    assert report["order_capability_lane_parked"] is True
    assert report["safety_flags"]["no_network"] is True
    assert report["safety_flags"]["no_secrets"] is True
    assert report["safety_flags"]["order_capability_execute_authorized"] is False


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_order_capability_fixture_binding_crosslink_package_marker_v1() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert CROSSLINK_PACKAGE_MARKER in text


def test_docs_truth_map_order_capability_fixture_binding_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map, "Order-Capability fixture-binding DOCS_TRUTH_MAP static crosslink guard v1"
    )
    for required in (
        RUNNER_REL,
        TEST_REL,
        "ORDER_CAPABILITY_FIXTURE_BINDING_CROSSLINK_GUARD_IMPLEMENTED=true",
        "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED=true",
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "CANCEL_EXECUTE_AUTHORIZATION_CREATED=false",
        "non-authorizing",
        "parked/read-only",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_order_capability_fixture_binding_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Order-Capability fixture-binding DOCS_TRUTH_MAP static crosslink v1"
    )
    section_text = ci_audit[section_start : section_start + 3500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "ORDER_CAPABILITY_FIXTURE_BINDING_CROSSLINK_GUARD_IMPLEMENTED=true",
        "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED=true",
        RUNNER_REL,
        TEST_REL,
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "CANCEL_EXECUTE_AUTHORIZATION_CREATED=false",
        "READY_FOR_OPERATOR_ARMING_CHANGED=false",
        "non-authorizing",
        "plan-only",
    ):
        assert required.lower() in section_text.lower()


def test_order_capability_fixture_binding_runner_referenced_in_docs_v1() -> None:
    assert RUNNER_SCRIPT.is_file()
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert RUNNER_REL in truth_map
    assert RUNNER_REL in ci_audit


def test_order_capability_fixture_binding_tests_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert TEST_REL in truth_map
    assert TEST_REL in ci_audit


def test_pe8_wiring_guard_package_marker_v0() -> None:
    assert PE8_WIRING_GUARD_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_adapter_primary_evidence_wiring_referenced_guard_v0() -> None:
    adapter_text = ADAPTER_SCRIPT.read_text(encoding="utf-8")
    helper_text = SHARED_HELPER.read_text(encoding="utf-8")
    assert ADAPTER_SCRIPT.is_file()
    assert SHARED_HELPER.is_file()
    assert "primary_evidence_retention_v0" in adapter_text
    assert "validate_order_capability_offline_durable_run_root" in adapter_text
    assert "write_manifest_sha256" in adapter_text
    assert "def validate_order_capability_offline_durable_run_root" in helper_text


def test_pe_wiring_impl_package_marker_v1() -> None:
    assert PE_WIRING_IMPL_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_fixture_binding_runner_primary_evidence_wiring_impl_guard_v1() -> None:
    runner_text = RUNNER_SCRIPT.read_text(encoding="utf-8")
    preflight = (
        ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    ).read_text(encoding="utf-8")
    assert "primary_evidence_retention_v0" in runner_text
    assert "validate_order_capability_offline_durable_run_root" in runner_text
    assert "write_manifest_sha256" in runner_text
    assert "--write-evidence" in runner_text
    for token in (
        "FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_COMPLETE=true",
        "FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_GUARDED=true",
        "ADAPTER_PRIMARY_EVIDENCE_WIRING_REFERENCED=true",
        "ORDER_CAPABILITY_FIXTURE_BINDING_PE_CLOSEOUT_WIRING_GUARD_IMPLEMENTED=true",
        "ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PE_WIRING_IMPLEMENTED=true",
    ):
        assert token in preflight
    assert "FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_PENDING=true" not in preflight


def test_write_evidence_missing_operator_go_fails(tmp_path: Path) -> None:
    mod = _load_runner()
    archive = _durable_archive(tmp_path)
    rc = mod.main(_base_write_argv(archive) + ["--write-evidence"])
    assert rc != 0


def test_write_evidence_with_invalid_operator_go_fails(tmp_path: Path) -> None:
    mod = _load_runner()
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_write_argv(archive) + ["--write-evidence", "--operator-go-token", "INVALID_GO_TOKEN"]
    )
    assert rc != 0


def test_plan_only_does_not_write_durable_bundle(tmp_path: Path) -> None:
    mod = _load_runner()
    archive = _durable_archive(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_write_argv(archive))
    assert rc == 0
    assert not any(archive.rglob("ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json"))


def test_write_evidence_creates_durable_bundle(tmp_path: Path) -> None:
    mod = _load_runner()
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_write_argv(archive)
        + [
            "--write-evidence",
            "--operator-go-token",
            REQUIRED_OPERATOR_GO_TOKEN,
        ]
    )
    assert rc == 0
    dest = archive / "runs" / "testnet" / "fixture_binding_test_run"
    assert (dest / "RUN_METADATA.json").is_file()
    assert (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").is_file()
    assert (dest / "CLOSEOUT.md").is_file()
    assert (dest / "MANIFEST.sha256").is_file()
    from scripts.ops.primary_evidence_retention_v0 import (
        validate_order_capability_offline_durable_run_root,
        verify_manifest_sha256,
    )

    layout_ok, layout_issues = validate_order_capability_offline_durable_run_root(dest)
    assert layout_ok is True
    assert layout_issues == []
    manifest_ok, _msg = verify_manifest_sha256(dest)
    assert manifest_ok is True
    payload = json.loads(
        (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").read_text(encoding="utf-8")
    )
    assert payload["verdict"] == "DRY_VALIDATION_COMPLETE"
    assert payload["mode"] == "write-evidence"
    assert payload["safety_flags"]["order_capability_execute_authorized"] is False
    assert payload["order_capability_lane_parked"] is True


def test_write_evidence_fail_closed_when_layout_validation_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_runner()
    archive = _durable_archive(tmp_path)
    monkeypatch.setattr(
        mod,
        "validate_order_capability_offline_durable_run_root",
        lambda _dest: (False, ["missing durable required file: CLOSEOUT.md"]),
    )
    rc = mod.main(
        _base_write_argv(archive)
        + [
            "--write-evidence",
            "--operator-go-token",
            REQUIRED_OPERATOR_GO_TOKEN,
        ]
    )
    assert rc != 0


def test_output_written_only_when_explicit(tmp_path: Path) -> None:
    mod = _load_runner()
    output = tmp_path / "report.json"
    rc = mod.main(
        [
            "--fixture",
            str(BROWSER_RENDER_FIXTURE),
            "--output",
            str(output),
            "--format",
            "json",
        ]
    )
    assert rc == 0
    assert output.is_file()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["verdict"] == "DRY_VALIDATION_COMPLETE"
