"""Focused tests: Canonical Decision archive sibling exporter CLI."""

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
from src.ops.canonical_decision_archive_sibling_exporter_v1.constants_v1 import (
    SOURCE_EVIDENCE_SCHEMA_VERSION,
    TARGET_RELATIVE_PATH,
)

REPO = Path(__file__).resolve().parents[2]
CLI_PATH = REPO / "scripts/ops/run_canonical_decision_archive_sibling_exporter_v1.py"
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
        "run_canonical_decision_archive_sibling_exporter_v1",
        CLI_PATH,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CLI = _load_cli()


def _evidence(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "instrument_id": "ETH-USDT-SWAP",
        "decision_outcome": "observe",
        "next_direction_state": "neutral_observe",
        "decision_id": "decision-cli-1",
        "evidence_schema_version": SOURCE_EVIDENCE_SCHEMA_VERSION,
        "reason_codes": ["WARMUP_ACTIVE"],
        "semantic_digest": "c" * 64,
    }
    base.update(overrides)
    return base


def _write_source(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "evidence_source.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


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
            "--evidence-source-path",
            "/tmp/evidence.json",
        ]
    )
    assert args.dry_run is True
    assert args.write_authorized is False
    assert CLI.DEFAULT_DRY_RUN is True

    sig = inspect.signature(CLI.run_canonical_decision_archive_sibling_exporter_cli_v1)
    assert sig.parameters["dry_run"].default is True
    assert sig.parameters["write_authorized"].default is False


def test_default_dry_run_mutates_nothing(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _evidence())
    archive_root = tmp_path / "archive_root"
    source_before = source.read_bytes()
    before = _list_files(tmp_path)

    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
    )
    assert out.ok is True
    assert out.dry_run is True
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.CREATE.value
    assert out.target_relative_path == TARGET_RELATIVE_PATH
    assert out.target_relative_path == "readmodels/canonical_trading_decision_evidence.v1.json"
    assert not archive_root.exists()
    assert source.read_bytes() == source_before
    assert _list_files(tmp_path) == before


def test_missing_write_authorization_blocks(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _evidence())
    archive_root = tmp_path / "archive_root"
    before = _list_files(tmp_path)

    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
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
    payload = _evidence()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    expected_digest = canonical_digest_v1(payload)
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
        out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
            archive_root=archive_root,
            evidence_source_path=source,
            dry_run=False,
            write_authorized=True,
        )

    assert mocked.call_count == 1
    assert captured["target_relative_path"] == TARGET_RELATIVE_PATH
    assert captured["dry_run"] is False
    assert captured["write_authorized"] is True
    assert captured["contract_name"] == CLI.CONTRACT_NAME
    assert captured["required_fields"] == CLI.REQUIRED_PAYLOAD_FIELDS
    assert captured["payload"] == payload
    assert out.ok is True
    assert out.write_performed is True
    assert out.export_contract == "export_archive_sibling_json_v1"
    assert out.source_digest == expected_digest


def test_authorized_write_payload_semantically_unchanged(tmp_path: Path) -> None:
    payload = _evidence()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    source_before = source.read_bytes()
    expected_digest = canonical_digest_v1(payload)

    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is True
    assert out.write_performed is True
    assert out.effect == ArchiveSiblingExportEffectV1.CREATE.value
    assert out.target_relative_path == "readmodels/canonical_trading_decision_evidence.v1.json"

    target = archive_root / TARGET_RELATIVE_PATH
    assert target.is_file()
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == payload
    assert canonical_digest_v1(written) == expected_digest
    assert out.source_digest == expected_digest
    assert out.target_digest_after == expected_digest
    assert source.read_bytes() == source_before


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_root"
    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=tmp_path / "missing.json",
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_MISSING_CLI
    assert not archive_root.exists()


def test_corrupt_source_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.json"
    source.write_text("{not-json", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_CORRUPT_CLI
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _evidence(evidence_schema_version="other.v9"))
    archive_root = tmp_path / "archive_root"
    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_SCHEMA_MISMATCH_CLI
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_symlink_escape_blocked(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _evidence())
    archive = tmp_path / "archive"
    outside = tmp_path / "outside"
    outside.mkdir()
    escape_target = outside / "canonical_trading_decision_evidence.v1.json"
    escape_target.write_text('{"evidence_schema_version":"x"}\n', encoding="utf-8")

    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    link = readmodels / "canonical_trading_decision_evidence.v1.json"
    link.symlink_to(escape_target)

    outside_before = escape_target.read_bytes()
    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive,
        evidence_source_path=source,
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
    source = _write_source(tmp_path, _evidence())
    archive_root = tmp_path / "archive_root"
    out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
    )
    payload = out.to_dict()
    text = json.dumps(payload, sort_keys=True)
    assert '"payload"' not in text
    assert "api_key" not in text.lower()
    assert "secret" not in text.lower()
    assert "password" not in text.lower()
    assert "reason_codes" not in payload


def test_cli_main_dry_run_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = _write_source(tmp_path, _evidence())
    archive_root = tmp_path / "archive_root"
    rc = CLI.main(
        [
            "--archive-root",
            str(archive_root),
            "--evidence-source-path",
            str(source),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    printed = json.loads(captured.out)
    assert printed["ok"] is True
    assert printed["write_performed"] is False
    assert printed["dry_run"] is True


def test_cli_has_no_forbidden_imports() -> None:
    tree = ast.parse(CLI_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for token in FORBIDDEN_IMPORT_TOKENS:
                    assert token not in alias.name
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not alias.name.startswith(prefix)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for token in FORBIDDEN_IMPORT_TOKENS:
                assert token not in node.module
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not node.module.startswith(prefix)


def test_exported_sibling_is_materializer_source_shape(tmp_path: Path) -> None:
    """Prove export closes the upstream sibling required by the materializer path."""
    from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_materializer_v1 import (
        SOURCE_EVIDENCE_RELATIVE_PATH,
        STATUS_WRITTEN,
        materialize_canonical_decision_presentation_projection_v1,
        try_load_canonical_decision_evidence_source_v1,
    )
    from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_v1 import (
        STORAGE_RELATIVE_PATH,
        try_load_canonical_decision_presentation_projection_v1,
    )

    payload = _evidence(decision_id="decision-materialize-bridge-1")
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"

    export_out = CLI.run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        evidence_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert export_out.ok is True
    assert export_out.write_performed is True
    assert (archive_root / SOURCE_EVIDENCE_RELATIVE_PATH).is_file()

    loaded, errors, path = try_load_canonical_decision_evidence_source_v1(archive_root)
    assert errors == ()
    assert loaded is not None
    assert loaded["decision_id"] == "decision-materialize-bridge-1"
    assert path is not None

    materialize = materialize_canonical_decision_presentation_projection_v1(
        archive_root,
        generated_at="2026-08-05T00:00:00Z",
        effective_at="2026-08-05T00:00:00Z",
    )
    assert materialize.written is True
    assert materialize.status == STATUS_WRITTEN
    assert (archive_root / STORAGE_RELATIVE_PATH).is_file()

    projection = try_load_canonical_decision_presentation_projection_v1(archive_root)
    assert projection.loaded is True
    assert projection.decision_id == "decision-materialize-bridge-1"
