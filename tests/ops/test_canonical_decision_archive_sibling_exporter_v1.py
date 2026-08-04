"""Bounded Canonical Decision archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.ops.archive_sibling_export_contract_v1 import canonical_digest_v1
from src.ops.canonical_decision_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_MISSING,
    ERROR_SOURCE_SCHEMA_MISMATCH,
    SOURCE_EVIDENCE_SCHEMA_VERSION,
    TARGET_RELATIVE_PATH,
)
from src.ops.canonical_decision_archive_sibling_exporter_v1.exporter_v1 import (
    export_canonical_decision_evidence_to_archive_sibling_v1,
)

EXPORTER_PKG = Path("src/ops/canonical_decision_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
    "trading.master_v2.integrated_offline",
    "src.trading.master_v2.integrated_offline",
)


def _evidence(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "instrument_id": "ETH-USDT-SWAP",
        "decision_outcome": "observe",
        "next_direction_state": "neutral_observe",
        "decision_id": "decision-export-1",
        "evidence_schema_version": SOURCE_EVIDENCE_SCHEMA_VERSION,
        "reason_codes": ["WARMUP_ACTIVE", "NO_ENTRY"],
        "semantic_digest": "a" * 64,
    }
    base.update(overrides)
    return base


def _write_source(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "source" / "canonical_trading_decision_evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_CANONICAL_DECISION_ARCHIVE_SIBLING_EXPORTER_V1"


def test_successful_one_to_one_export(tmp_path: Path) -> None:
    payload = _evidence()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    source_bytes_before = source.read_bytes()
    expected_digest = canonical_digest_v1(payload)

    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is True
    assert out.error_code is None
    assert out.source_payload_digest == expected_digest
    assert out.target_payload_digest == expected_digest
    assert out.decision_id == "decision-export-1"
    assert out.instrument_id == "ETH-USDT-SWAP"
    assert out.decision_outcome == "observe"
    assert out.evidence_schema_version == SOURCE_EVIDENCE_SCHEMA_VERSION
    assert out.replaced_existing is False
    assert out.bytes_written > 0
    assert out.authority_effect == "NONE"
    assert out.decision_authority_effect == "NONE"

    target = archive_root / TARGET_RELATIVE_PATH
    assert target.is_file()
    assert (
        target.resolve()
        == (archive_root / "readmodels" / "canonical_trading_decision_evidence.v1.json").resolve()
    )
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == payload
    assert source.read_bytes() == source_bytes_before


def test_nested_evidence_envelope_export(tmp_path: Path) -> None:
    nested = _evidence(decision_id="decision-nested-1")
    source = _write_source(tmp_path, {"evidence": nested, "meta": "ignored"})
    archive_root = tmp_path / "archive_root"

    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is True
    written = json.loads((archive_root / TARGET_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert written == nested
    assert out.decision_id == "decision-nested-1"


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_root"
    missing = tmp_path / "absent.json"
    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=missing,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_MISSING
    assert not archive_root.exists()


def test_corrupt_source_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("{not-json", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_CORRUPT
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _evidence(evidence_schema_version="wrong.v0"))
    archive_root = tmp_path / "archive_root"
    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_SCHEMA_MISMATCH
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_invalid_missing_required_field_fail_closed(tmp_path: Path) -> None:
    payload = _evidence()
    del payload["decision_outcome"]
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_INVALID
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_identical_source_target_fail_closed(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _evidence()
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=target,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_IDENTICAL_PATHS


def test_ambiguous_nested_decision_id_fail_closed(tmp_path: Path) -> None:
    nested = _evidence(decision_id="decision-a")
    source = _write_source(
        tmp_path,
        {
            "decision_id": "decision-b",
            "evidence": nested,
        },
    )
    archive_root = tmp_path / "archive_root"
    out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_INVALID


def test_replace_existing_sibling(tmp_path: Path) -> None:
    first = _evidence(decision_id="decision-first")
    second = _evidence(decision_id="decision-second")
    source = _write_source(tmp_path, first)
    archive_root = tmp_path / "archive_root"

    first_out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert first_out.exported is True
    assert first_out.replaced_existing is False

    source.write_text(json.dumps(second, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    second_out = export_canonical_decision_evidence_to_archive_sibling_v1(
        evidence_source_path=source,
        archive_root=archive_root,
    )
    assert second_out.exported is True
    assert second_out.replaced_existing is True
    written = json.loads((archive_root / TARGET_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert written["decision_id"] == "decision-second"


def test_package_has_no_presentation_or_replay_imports() -> None:
    for path in EXPORTER_PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), (path, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not node.module.startswith(prefix), (path, node.module)
