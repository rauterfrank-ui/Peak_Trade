"""Focused tests: CAPABILITY_ARCHIVE_SIBLING_EXPORT_CONTRACT_V1."""

from __future__ import annotations

import ast
import inspect
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.ops.archive_sibling_export_contract_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ArchiveSiblingExportEffectV1,
    canonical_digest_v1,
    export_archive_sibling_json_v1,
)
from src.ops.archive_sibling_export_contract_v1.atomic_write import atomic_write_text_v1
from src.ops.archive_sibling_export_contract_v1.contracts import (
    BLOCK_WRITE_NOT_AUTHORIZED,
    export_archive_sibling_json_v1 as export_fn,
)

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "src/ops/archive_sibling_export_contract_v1"
CONTRACT = "unit_test_archive_sibling_contract_v1"
TARGET_REL = Path("readmodels/unit_sibling.v1.json")

FORBIDDEN_IMPORT_PREFIXES = (
    "trading",
    "src.trading",
    "src.risk_layer",
    "src.governance",
    "src.backtest",
    "src.webui",
    "src.execution",
)


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "alpha": 1,
        "beta": "x",
        "nested": {"z": 3, "a": 2},
    }
    base.update(overrides)
    return base


def _list_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_capability_constants() -> None:
    assert CAPABILITY_ID == "CAPABILITY_ARCHIVE_SIBLING_EXPORT_CONTRACT_V1"
    assert AUTHORITY_EFFECT == "NONE"


def test_digest_deterministic_across_key_order() -> None:
    left = {"b": 2, "a": 1, "nested": {"y": 2, "x": 1}}
    right = {"nested": {"x": 1, "y": 2}, "a": 1, "b": 2}
    assert canonical_digest_v1(left) == canonical_digest_v1(right)


def test_public_api_defaults_to_dry_run() -> None:
    sig = inspect.signature(export_archive_sibling_json_v1)
    assert sig.parameters["dry_run"].default is True
    assert sig.parameters["write_authorized"].default is False


def test_create_dry_run_no_filesystem_mutation(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    before = _list_files(tmp_path)
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        required_fields=("alpha", "beta"),
    )
    assert result.effect == ArchiveSiblingExportEffectV1.CREATE
    assert result.dry_run is True
    assert result.write_performed is False
    assert result.source_digest
    assert result.expected_target_digest == result.source_digest
    assert result.target_digest_after is None
    assert _list_files(tmp_path) == before
    assert not archive.exists()


def test_create_authorized_write(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    payload = _payload()
    digest = canonical_digest_v1(payload)
    result = export_archive_sibling_json_v1(
        payload=payload,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        required_fields=("alpha",),
        dry_run=False,
        write_authorized=True,
    )
    target = archive / TARGET_REL
    assert result.effect == ArchiveSiblingExportEffectV1.CREATE
    assert result.write_performed is True
    assert result.dry_run is False
    assert result.source_digest == digest
    assert result.target_digest_after == digest
    assert target.is_file()
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == payload
    assert canonical_digest_v1(loaded) == digest


def test_no_change_skips_write(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    payload = _payload()
    first = export_archive_sibling_json_v1(
        payload=payload,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    assert first.write_performed is True
    target = archive / TARGET_REL
    before_bytes = target.read_bytes()
    mtime_before = target.stat().st_mtime_ns

    second = export_archive_sibling_json_v1(
        payload={"nested": payload["nested"], "beta": "x", "alpha": 1},
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    assert second.effect == ArchiveSiblingExportEffectV1.NO_CHANGE
    assert second.write_performed is False
    assert target.read_bytes() == before_bytes
    assert target.stat().st_mtime_ns == mtime_before


def test_replace_dry_run_and_authorized_write(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    original = _payload(alpha=1)
    export_archive_sibling_json_v1(
        payload=original,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    target = archive / TARGET_REL
    before_bytes = target.read_bytes()
    updated = _payload(alpha=99)

    dry = export_archive_sibling_json_v1(
        payload=updated,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
    )
    assert dry.effect == ArchiveSiblingExportEffectV1.REPLACE
    assert dry.write_performed is False
    assert dry.target_digest_before == canonical_digest_v1(original)
    assert dry.expected_target_digest == canonical_digest_v1(updated)
    assert target.read_bytes() == before_bytes

    written = export_archive_sibling_json_v1(
        payload=updated,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    assert written.effect == ArchiveSiblingExportEffectV1.REPLACE
    assert written.write_performed is True
    assert written.target_digest_after == canonical_digest_v1(updated)
    assert json.loads(target.read_text(encoding="utf-8"))["alpha"] == 99


def test_dry_run_false_without_write_authorized_blocked(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=False,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason == BLOCK_WRITE_NOT_AUTHORIZED
    assert result.write_performed is False
    assert not (archive / TARGET_REL).exists()


def test_write_authorized_true_with_dry_run_still_dry(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=True,
        write_authorized=True,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.CREATE
    assert result.dry_run is True
    assert result.write_performed is False
    assert not archive.exists()


def test_missing_required_field_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=tmp_path / "archive",
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        required_fields=("alpha", "missing_field"),
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "REQUIRED_FIELD_MISSING" in result.block_reason
    assert "missing_field" in result.block_reason


def test_payload_not_object_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload=["not", "an", "object"],  # type: ignore[arg-type]
        archive_root=tmp_path / "archive",
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "PAYLOAD_NOT_OBJECT" in result.block_reason


def test_non_serializable_payload_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload={"ok": 1, "bad": {1, 2, 3}},
        archive_root=tmp_path / "archive",
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "NOT_SERIALIZABLE" in result.block_reason


def test_absolute_target_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=tmp_path / "archive",
        target_relative_path=tmp_path / "readmodels" / "x.json",
        contract_name=CONTRACT,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "PATH_INVALID" in result.block_reason


def test_path_traversal_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=tmp_path / "archive",
        target_relative_path=Path("readmodels/../secret.json"),
        contract_name=CONTRACT,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "PATH_INVALID" in result.block_reason


def test_target_outside_readmodels_blocked(tmp_path: Path) -> None:
    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=tmp_path / "archive",
        target_relative_path=Path("other/unit_sibling.v1.json"),
        contract_name=CONTRACT,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "PATH_INVALID" in result.block_reason


def test_symlink_escape_blocked(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    outside = tmp_path / "outside"
    outside.mkdir()
    escape_target = outside / "escaped.json"
    escape_target.write_text('{"alpha":1}\n', encoding="utf-8")

    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    link = readmodels / "escape_link"
    link.symlink_to(outside)

    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=archive,
        target_relative_path=Path("readmodels/escape_link/escaped.json"),
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "PATH_INVALID" in result.block_reason
    assert escape_target.read_text(encoding="utf-8") == '{"alpha":1}\n'


def test_invalid_existing_json_blocked_and_unchanged(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    target = archive / TARGET_REL
    target.parent.mkdir(parents=True)
    original = b"{not-json"
    target.write_bytes(original)

    result = export_archive_sibling_json_v1(
        payload=_payload(),
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
    assert result.block_reason is not None
    assert "TARGET_INVALID_JSON" in result.block_reason
    assert target.read_bytes() == original


def test_blocked_cases_preserve_existing_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    payload = _payload()
    export_archive_sibling_json_v1(
        payload=payload,
        archive_root=archive,
        target_relative_path=TARGET_REL,
        contract_name=CONTRACT,
        dry_run=False,
        write_authorized=True,
    )
    target = archive / TARGET_REL
    before = target.read_bytes()

    blocked_cases = [
        dict(
            payload=_payload(alpha=2),
            dry_run=False,
            write_authorized=False,
        ),
        dict(
            payload=_payload(),
            required_fields=("nope",),
        ),
        dict(
            payload=_payload(),
            target_relative_path=Path("readmodels/../x.json"),
        ),
    ]
    for kwargs in blocked_cases:
        call: dict[str, Any] = {
            "payload": _payload(),
            "archive_root": archive,
            "target_relative_path": TARGET_REL,
            "contract_name": CONTRACT,
        }
        call.update(kwargs)
        result = export_archive_sibling_json_v1(**call)
        assert result.effect == ArchiveSiblingExportEffectV1.BLOCKED
        assert target.read_bytes() == before


def test_temp_cleanup_on_write_failure(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    target = archive / TARGET_REL

    def boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated_replace_failure")

    with patch(
        "src.ops.archive_sibling_export_contract_v1.atomic_write.os.replace",
        side_effect=boom,
    ):
        with pytest.raises(Exception):
            atomic_write_text_v1(destination=target, body='{"a":1}\n')

    leftovers = list(target.parent.glob(target.name + ".*")) if target.parent.exists() else []
    assert leftovers == []


def test_os_replace_only_after_validation(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    calls: list[str] = []

    real_replace = os.replace

    def tracked_replace(src: str, dst: str) -> None:
        calls.append("replace")
        real_replace(src, dst)

    with patch(
        "src.ops.archive_sibling_export_contract_v1.atomic_write.os.replace",
        side_effect=tracked_replace,
    ):
        blocked = export_archive_sibling_json_v1(
            payload=_payload(),
            archive_root=archive,
            target_relative_path=Path("readmodels/../evil.json"),
            contract_name=CONTRACT,
            dry_run=False,
            write_authorized=True,
        )
        assert blocked.effect == ArchiveSiblingExportEffectV1.BLOCKED
        assert calls == []

        ok = export_archive_sibling_json_v1(
            payload=_payload(),
            archive_root=archive,
            target_relative_path=TARGET_REL,
            contract_name=CONTRACT,
            dry_run=False,
            write_authorized=True,
        )
        assert ok.write_performed is True
        assert calls == ["replace"]


def test_no_mkdir_in_dry_run(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    with patch("pathlib.Path.mkdir") as mkdir_mock:
        result = export_archive_sibling_json_v1(
            payload=_payload(),
            archive_root=archive,
            target_relative_path=TARGET_REL,
            contract_name=CONTRACT,
        )
        assert result.effect == ArchiveSiblingExportEffectV1.CREATE
        mkdir_mock.assert_not_called()


def test_forbidden_domain_imports_absent() -> None:
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), path
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not mod.startswith(prefix), path


def test_export_fn_alias_is_public_api() -> None:
    assert export_fn is export_archive_sibling_json_v1
