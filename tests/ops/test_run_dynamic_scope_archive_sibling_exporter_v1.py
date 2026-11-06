"""Focused tests: Dynamic Scope archive sibling exporter CLI (PR B)."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.archive_sibling_export_contract_v1 import (
    ArchiveSiblingExportEffectV1,
    ArchiveSiblingExportResultV1,
    canonical_digest_v1,
)
from src.ops.archive_sibling_export_contract_v1.contracts import (
    BLOCK_WRITE_NOT_AUTHORIZED,
)
from src.ops.dynamic_scope_archive_sibling_exporter_v1.constants_v1 import (
    TARGET_RELATIVE_PATH,
)
from src.ops.dynamic_scope_persistence_binding_v1.cycle_harness_v1 import (
    ScopeHarnessEventV1,
    run_dynamic_scope_harness_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    load_dynamic_scope_state_v1,
    scope_state_path,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
)

REPO = Path(__file__).resolve().parents[2]
CLI_PATH = REPO / "scripts/ops/run_dynamic_scope_archive_sibling_exporter_v1.py"
REPO_SHA = "7beeba1ce93013461d45773a0390d7c9148571c8"
FORBIDDEN_IMPORT_TOKENS = (
    "src.webui",
    "playwright",
    "presentation_projection_octet",
    "workflow_dashboard",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "playwright",
)


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        "run_dynamic_scope_archive_sibling_exporter_v1",
        CLI_PATH,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CLI = _load_cli()


def _market(mid: float) -> ScopeHarnessEventV1:
    return ScopeHarnessEventV1(kind=ObservationCycleKindV1.MARKET_SAMPLE, mid_price=mid)


def _persist_valid_state(tmp_path: Path) -> Path:
    state_root = tmp_path / "dynamic_scope_state_root"
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(6)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=state_root,
    )
    assert result.ok
    assert scope_state_path(state_root).is_file()
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert isinstance(loaded, CanonicalDynamicScopeStateV1)
    return state_root


def _list_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_cli_defaults_dry_run_true() -> None:
    parser = CLI.build_parser()
    args = parser.parse_args(
        [
            "--archive-root",
            "/tmp/archive",
            "--dynamic-scope-state-root",
            "/tmp/state",
        ]
    )
    assert args.dry_run is True
    assert args.write_authorized is False
    assert CLI.DEFAULT_DRY_RUN is True

    sig = inspect.signature(CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1)
    assert sig.parameters["dry_run"].default is True
    assert sig.parameters["write_authorized"].default is False


def test_default_dry_run_mutates_nothing(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    source = scope_state_path(state_root)
    source_before = source.read_bytes()
    before = _list_files(tmp_path)

    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
    )
    assert out.ok is True
    assert out.dry_run is True
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.CREATE.value
    assert out.target_relative_path == "readmodels/dynamic_scope_state_v1.json"
    assert out.target_relative_path == TARGET_RELATIVE_PATH
    assert not archive_root.exists()
    assert source.read_bytes() == source_before
    assert _list_files(tmp_path) == before


def test_missing_write_authorization_blocks(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    before = _list_files(tmp_path)

    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=False,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.BLOCKED.value
    assert out.block_reason == BLOCK_WRITE_NOT_AUTHORIZED
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()
    assert _list_files(tmp_path) == before


def test_authorized_write_uses_pr_a_contract_exactly(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    expected_payload = loaded.to_dict()
    expected_digest = canonical_digest_v1(expected_payload)

    captured: dict[str, object] = {}

    def _spy(**kwargs: object) -> ArchiveSiblingExportResultV1:
        captured.update(kwargs)
        return ArchiveSiblingExportResultV1(
            effect=ArchiveSiblingExportEffectV1.CREATE,
            write_performed=True,
            dry_run=False,
            contract_name=str(kwargs["contract_name"]),
            target_path=str(Path(str(kwargs["archive_root"])) / TARGET_RELATIVE_PATH),
            source_digest=expected_digest,
            target_digest_before=None,
            target_digest_after=expected_digest,
            expected_target_digest=expected_digest,
            block_reason=None,
            schema_name=str(kwargs["contract_name"]),
        )

    with patch.object(CLI, "export_archive_sibling_json_v1", side_effect=_spy) as mocked:
        out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
            archive_root=archive_root,
            dynamic_scope_state_root=state_root,
            dry_run=False,
            write_authorized=True,
        )

    assert mocked.call_count == 1
    assert captured["target_relative_path"] == TARGET_RELATIVE_PATH
    assert captured["target_relative_path"] == "readmodels/dynamic_scope_state_v1.json"
    assert captured["dry_run"] is False
    assert captured["write_authorized"] is True
    assert captured["contract_name"] == CLI.CONTRACT_NAME
    assert captured["required_fields"] == CLI.REQUIRED_PAYLOAD_FIELDS
    assert captured["payload"] == expected_payload
    assert out.ok is True
    assert out.write_performed is True
    assert out.export_contract == "export_archive_sibling_json_v1"
    assert out.source_digest == expected_digest


def test_authorized_write_payload_semantically_unchanged(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    source = scope_state_path(state_root)
    source_before = source.read_bytes()
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    expected_payload = loaded.to_dict()
    expected_digest = canonical_digest_v1(expected_payload)

    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is True
    assert out.write_performed is True
    assert out.effect == ArchiveSiblingExportEffectV1.CREATE.value
    assert out.target_relative_path == "readmodels/dynamic_scope_state_v1.json"

    target = archive_root / TARGET_RELATIVE_PATH
    assert target.is_file()
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == expected_payload
    assert canonical_digest_v1(written) == expected_digest
    assert out.source_digest == expected_digest
    assert out.target_digest_after == expected_digest
    assert source.read_bytes() == source_before


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    state_root = tmp_path / "missing_state_root"
    state_root.mkdir()
    archive_root = tmp_path / "archive_root"
    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_MISSING
    assert not archive_root.exists()


def test_corrupt_source_fail_closed(tmp_path: Path) -> None:
    state_root = tmp_path / "corrupt_state_root"
    state_root.mkdir()
    scope_state_path(state_root).write_text("{not-json", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_CORRUPT
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_invalid_state_version_fail_closed(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    source = scope_state_path(state_root)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["state_version"] = "v999-invalid"
    source.write_text(json.dumps(payload), encoding="utf-8")
    archive_root = tmp_path / "archive_root"

    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_STATE_VERSION_MISMATCH
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_symlink_escape_blocked(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive = tmp_path / "archive"
    outside = tmp_path / "outside"
    outside.mkdir()
    escape_target = outside / "dynamic_scope_state_v1.json"
    escape_target.write_text('{"schema_version":"x"}\n', encoding="utf-8")

    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    link = readmodels / "dynamic_scope_state_v1.json"
    link.symlink_to(escape_target)

    outside_before = escape_target.read_bytes()
    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive,
        dynamic_scope_state_root=state_root,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.BLOCKED.value
    assert out.block_reason is not None
    assert "PATH_INVALID" in out.block_reason
    assert escape_target.read_bytes() == outside_before


def test_result_output_has_no_payload_or_secrets(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    out = CLI.run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        dynamic_scope_state_root=state_root,
    )
    payload = out.to_dict()
    text = json.dumps(payload, sort_keys=True)
    assert "price_path_tail" not in payload
    assert "position_context" not in payload
    assert "existing_scope" not in payload
    assert "runtime_scope_state" not in payload
    assert '"payload"' not in text
    assert "api_key" not in text.lower()
    assert "secret" not in text.lower()
    assert "password" not in text.lower()


def test_cli_main_dry_run_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    rc = CLI.main(
        [
            "--archive-root",
            str(archive_root),
            "--dynamic-scope-state-root",
            str(state_root),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    printed = json.loads(captured.out)
    assert printed["ok"] is True
    assert printed["dry_run"] is True
    assert printed["write_performed"] is False
    assert printed["target_relative_path"] == "readmodels/dynamic_scope_state_v1.json"
    assert not archive_root.exists()


def test_forbidden_imports_and_no_atomic_write_duplication() -> None:
    src = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.add(mod)

    for name in imported:
        assert not name.startswith(FORBIDDEN_IMPORT_PREFIXES), name
        for token in FORBIDDEN_IMPORT_TOKENS:
            assert token not in name, name

    assert "export_archive_sibling_json_v1" in src
    assert "atomic_write_text_v1" not in src
    assert "tempfile" not in src
    assert "os.replace" not in src
    assert "export_dynamic_scope_state_to_archive_sibling_v1" not in src
    assert "TARGET_RELATIVE_PATH" in src
    assert "latest" not in src.lower() or "no latest" in src.lower()
    assert "playwright" not in src.lower()
    assert "src.webui" not in src
