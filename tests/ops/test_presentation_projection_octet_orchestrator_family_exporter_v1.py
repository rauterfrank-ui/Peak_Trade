"""Focused tests: PR-C dynamic_scope exporter family integration into octet orchestrator."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    DEFAULT_DRY_RUN,
    DYNAMIC_SCOPE_EXPORTER_CLI_RELATIVE_PATH,
    ERROR_EXPORTER_FAMILY_NOT_INTEGRATED,
    ERROR_EXPORTER_NONZERO_EXIT,
    ERROR_EXPORTER_STATE_ROOT_REQUIRED,
    ERROR_EXPORTER_SUBPROCESS_FAILED,
    EXPORTER_INTEGRATED_FAMILIES,
    FAMILY_DYNAMIC_SCOPE,
    FAMILY_ORDER,
)
from src.ops.presentation_projection_octet_orchestrator_v1.family_exporter_dispatch_v1 import (
    build_family_exporter_argv_v1,
    exporter_cli_relative_path_for_family_v1,
    integrated_exporter_families_v1,
    run_octet_family_exporter_v1,
    run_octet_family_exporters_v1,
)

REPO = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO / "src/ops/presentation_projection_octet_orchestrator_v1"
CLI_PATH = REPO / "scripts/ops/run_presentation_projection_octet_orchestrator_v1.py"
DYNAMIC_SCOPE_CLI = REPO / DYNAMIC_SCOPE_EXPORTER_CLI_RELATIVE_PATH


def _ok_cli_stdout(*, dry_run: bool = True, write_authorized: bool = False) -> str:
    return json.dumps(
        {
            "ok": True,
            "effect": "WOULD_WRITE" if dry_run else "WRITTEN",
            "write_performed": (not dry_run) and write_authorized,
            "dry_run": dry_run,
            "write_authorized": write_authorized,
        },
        sort_keys=True,
    )


def test_family_registration_dynamic_scope_only() -> None:
    assert integrated_exporter_families_v1() == (FAMILY_DYNAMIC_SCOPE,)
    assert EXPORTER_INTEGRATED_FAMILIES == (FAMILY_DYNAMIC_SCOPE,)
    assert exporter_cli_relative_path_for_family_v1(FAMILY_DYNAMIC_SCOPE) == (
        DYNAMIC_SCOPE_EXPORTER_CLI_RELATIVE_PATH
    )
    for family_id in FAMILY_ORDER:
        if family_id == FAMILY_DYNAMIC_SCOPE:
            continue
        assert exporter_cli_relative_path_for_family_v1(family_id) is None


def test_default_dry_run_true_and_write_gate_closed() -> None:
    assert DEFAULT_DRY_RUN is True
    sig = inspect.signature(run_octet_family_exporter_v1)
    assert sig.parameters["dry_run"].default is True
    assert sig.parameters["write_authorized"].default is False

    argv, errors = build_family_exporter_argv_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        repo_root=REPO,
    )
    assert errors == ()
    assert argv is not None
    assert "--dry-run" in argv
    assert "--no-dry-run" not in argv
    assert "--write-authorized" not in argv


def test_correct_cli_invocation_argv(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    state = tmp_path / "state"
    archive.mkdir()
    state.mkdir()

    captured: dict[str, object] = {}

    def fake_runner(argv, **kwargs):  # noqa: ANN001
        captured["argv"] = list(argv)
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout=_ok_cli_stdout(), stderr="")

    result = run_octet_family_exporter_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root=archive,
        dynamic_scope_state_root=state,
        dry_run=True,
        write_authorized=False,
        repo_root=REPO,
        subprocess_runner=fake_runner,
    )
    assert result.ok is True
    argv = captured["argv"]
    assert isinstance(argv, list)
    assert argv[1] == str(DYNAMIC_SCOPE_CLI.resolve())
    assert "--archive-root" in argv
    assert str(archive) in argv
    assert "--dynamic-scope-state-root" in argv
    assert str(state) in argv
    assert "--dry-run" in argv
    assert result.cli_relative_path == DYNAMIC_SCOPE_EXPORTER_CLI_RELATIVE_PATH


def test_no_write_without_both_gates() -> None:
    # dry_run=false alone must not open the write gate or emit --write-authorized
    argv_no_auth, errors = build_family_exporter_argv_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        dry_run=False,
        write_authorized=False,
        repo_root=REPO,
    )
    assert errors == ()
    assert argv_no_auth is not None
    assert "--no-dry-run" in argv_no_auth
    assert "--write-authorized" not in argv_no_auth

    # write_authorized alone keeps dry-run (gate closed)
    argv_dry_auth, errors = build_family_exporter_argv_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        dry_run=True,
        write_authorized=True,
        repo_root=REPO,
    )
    assert errors == ()
    assert argv_dry_auth is not None
    assert "--dry-run" in argv_dry_auth
    assert "--write-authorized" in argv_dry_auth

    both, errors = build_family_exporter_argv_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        dry_run=False,
        write_authorized=True,
        repo_root=REPO,
    )
    assert errors == ()
    assert both is not None
    assert "--no-dry-run" in both
    assert "--write-authorized" in both

    def fake_runner(argv, **kwargs):  # noqa: ANN001
        return SimpleNamespace(
            returncode=0,
            stdout=_ok_cli_stdout(dry_run=False, write_authorized=False),
            stderr="",
        )

    blocked = run_octet_family_exporter_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        dry_run=False,
        write_authorized=False,
        repo_root=REPO,
        subprocess_runner=fake_runner,
    )
    assert blocked.write_gate_open is False
    assert blocked.write_performed is False


def test_error_propagation_nonzero_exit_and_subprocess_failure() -> None:
    def nonzero_runner(argv, **kwargs):  # noqa: ANN001
        return SimpleNamespace(
            returncode=1,
            stdout=json.dumps({"ok": False, "effect": "BLOCKED", "write_performed": False}),
            stderr="blocked",
        )

    failed = run_octet_family_exporter_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        repo_root=REPO,
        subprocess_runner=nonzero_runner,
    )
    assert failed.ok is False
    assert failed.exit_code == 1
    assert ERROR_EXPORTER_NONZERO_EXIT in failed.errors

    def boom_runner(argv, **kwargs):  # noqa: ANN001
        raise OSError("spawn failed")

    crashed = run_octet_family_exporter_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root="/tmp/state",
        repo_root=REPO,
        subprocess_runner=boom_runner,
    )
    assert crashed.ok is False
    assert ERROR_EXPORTER_SUBPROCESS_FAILED in crashed.errors


def test_missing_state_root_fail_closed() -> None:
    result = run_octet_family_exporter_v1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        archive_root="/tmp/archive",
        dynamic_scope_state_root=None,
        repo_root=REPO,
        subprocess_runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no spawn")),
    )
    assert result.ok is False
    assert ERROR_EXPORTER_STATE_ROOT_REQUIRED in result.errors
    assert result.argv == ()


def test_no_other_families_integrated() -> None:
    for family_id in (
        "regime_bull_bear_switch",
        "canonical_decision",
        "double_play",
        "safety_authority",
        "risk_sizing_capital",
        "execution_reconciliation",
        "economic_summary",
        "not_a_family",
    ):
        result = run_octet_family_exporter_v1(
            family_id=family_id,
            archive_root="/tmp/archive",
            dynamic_scope_state_root="/tmp/state",
            repo_root=REPO,
            subprocess_runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no spawn")),
        )
        assert result.ok is False
        assert ERROR_EXPORTER_FAMILY_NOT_INTEGRATED in result.errors

    batch = run_octet_family_exporters_v1(
        archive_root="/tmp/archive",
        families=("dynamic_scope", "economic_summary"),
        dynamic_scope_state_root="/tmp/state",
        repo_root=REPO,
        subprocess_runner=lambda argv, **kwargs: SimpleNamespace(
            returncode=0, stdout=_ok_cli_stdout(), stderr=""
        ),
    )
    assert len(batch) == 2
    assert batch[0].family_id == FAMILY_DYNAMIC_SCOPE
    assert batch[0].ok is True
    assert batch[1].family_id == "economic_summary"
    assert batch[1].ok is False
    assert ERROR_EXPORTER_FAMILY_NOT_INTEGRATED in batch[1].errors


def test_dispatch_uses_cli_path_not_duplicated_export_logic() -> None:
    dispatch_src = (PACKAGE_DIR / "family_exporter_dispatch_v1.py").read_text(encoding="utf-8")
    assert "run_dynamic_scope_archive_sibling_exporter_v1.py" in dispatch_src
    assert "export_archive_sibling_json_v1" not in dispatch_src
    assert "export_dynamic_scope_state_to_archive_sibling_v1" not in dispatch_src
    assert "subprocess" in dispatch_src

    tree = ast.parse(dispatch_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith("src.ops.dynamic_scope_archive_sibling_exporter_v1")
            assert not module.startswith("src.ops.archive_sibling_export_contract_v1")
            assert not module.startswith("src.webui")


def test_orchestrator_cli_exporter_mode_defaults_dry_run() -> None:
    spec = importlib.util.spec_from_file_location(
        "run_presentation_projection_octet_orchestrator_v1_cli",
        CLI_PATH,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    parser = mod._build_parser()
    args = parser.parse_args(
        [
            "--archive-root",
            "/tmp/archive",
            "--export-source-siblings",
            "--dynamic-scope-state-root",
            "/tmp/state",
        ]
    )
    assert args.export_source_siblings is True
    assert args.dry_run is True
    assert args.write_authorized is False


def test_existing_materializer_path_untouched_by_exporter_defaults() -> None:
    # Materializer orchestrator signature must not default to exporter writes.
    from src.ops.presentation_projection_octet_orchestrator_v1.orchestrator_v1 import (
        run_presentation_projection_octet_orchestrator_v1,
    )

    sig = inspect.signature(run_presentation_projection_octet_orchestrator_v1)
    assert "write_authorized" not in sig.parameters
    assert "dry_run" not in sig.parameters
    assert DYNAMIC_SCOPE_CLI.is_file()
