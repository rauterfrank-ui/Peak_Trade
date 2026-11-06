"""Bounded Dynamic Scope archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
import os
import time
from pathlib import Path

import pytest

from src.ops.dynamic_scope_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_MISSING,
    ERROR_SOURCE_SCHEMA_MISMATCH,
    ERROR_SOURCE_STATE_VERSION_MISMATCH,
    ERROR_WRITE_FAILED,
    TARGET_RELATIVE_PATH,
)
from src.ops.dynamic_scope_archive_sibling_exporter_v1.exporter_v1 import (
    export_dynamic_scope_state_to_archive_sibling_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.cycle_harness_v1 import (
    ScopeHarnessEventV1,
    run_dynamic_scope_harness_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
    canonical_digest_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    load_dynamic_scope_state_v1,
    scope_state_path,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
)

REPO_SHA = "7beeba1ce93013461d45773a0390d7c9148571c8"
EXPORTER_PKG = Path("src/ops/dynamic_scope_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
)


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


def test_successful_one_to_one_export(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    source = scope_state_path(state_root)
    source_bytes_before = source.read_bytes()
    source_mtime_before = source.stat().st_mtime_ns
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    expected_payload = loaded.to_dict()
    expected_digest = canonical_digest_v1(expected_payload)

    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is True
    assert out.error_code is None
    assert out.source_payload_digest == expected_digest
    assert out.target_payload_digest == expected_digest
    assert out.source_payload_digest == out.target_payload_digest
    assert out.replaced_existing is False
    assert out.bytes_written > 0
    assert out.schema_version == expected_payload["schema_version"]
    assert out.state_version == expected_payload["state_version"]
    assert out.scope_session_id == expected_payload["scope_session_id"]
    assert out.instrument_id == expected_payload["instrument_id"]

    target = archive_root / TARGET_RELATIVE_PATH
    assert target.is_file()
    assert (
        target.resolve() == (archive_root / "readmodels" / "dynamic_scope_state_v1.json").resolve()
    )
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == expected_payload
    # Same writer convention as persistence → byte identity with source file.
    assert target.read_bytes() == source_bytes_before
    # Source untouched.
    assert source.read_bytes() == source_bytes_before
    assert source.stat().st_mtime_ns == source_mtime_before


def test_no_semantic_or_presentation_fields_added(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    expected_keys = set(loaded.to_dict().keys())

    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is True
    written = json.loads((archive_root / TARGET_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert set(written.keys()) == expected_keys
    for forbidden in (
        "generated_at",
        "effective_at",
        "source_reference",
        "next_scope_ref",
        "observed_at",
        "saved_at",
        "scope_state",
        "current_scope_ref",
    ):
        assert forbidden not in written


def test_fail_closed_missing_source(tmp_path: Path) -> None:
    state_root = tmp_path / "empty_state_root"
    state_root.mkdir()
    archive_root = tmp_path / "archive_root"
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_MISSING
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()
    assert not (archive_root / "readmodels").exists() or not any(
        (archive_root / "readmodels").iterdir()
    )


def test_fail_closed_corrupt_json(tmp_path: Path) -> None:
    state_root = tmp_path / "corrupt_state_root"
    state_root.mkdir()
    scope_state_path(state_root).write_text("{not-json", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_CORRUPT
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_fail_closed_wrong_state_version(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    source = scope_state_path(state_root)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["state_version"] = "v999"
    source.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_STATE_VERSION_MISMATCH
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_fail_closed_schema_mismatch_via_to_dict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    bad = dict(loaded.to_dict())
    bad["schema_version"] = "not_the_canonical_schema"

    class _BadState:
        def to_dict(self) -> dict:
            return bad

    def _fake_load(*_a: object, **_k: object) -> object:
        return _BadState()

    monkeypatch.setattr(
        "src.ops.dynamic_scope_archive_sibling_exporter_v1.exporter_v1.load_dynamic_scope_state_v1",
        _fake_load,
    )
    # Bypass isinstance check by also patching CanonicalDynamicScopeStateV1 used in isinstance
    monkeypatch.setattr(
        "src.ops.dynamic_scope_archive_sibling_exporter_v1.exporter_v1.CanonicalDynamicScopeStateV1",
        _BadState,
    )
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_SCHEMA_MISMATCH
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()


def test_atomic_replace_existing_target(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    stale = {"stale": True, "not": "canonical"}
    target.write_text(json.dumps(stale) + "\n", encoding="utf-8")

    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is True
    assert out.replaced_existing is True
    written = json.loads(target.read_text(encoding="utf-8"))
    loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    assert loaded is not None
    assert written == loaded.to_dict()
    assert "stale" not in written


def test_write_failure_preserves_prior_or_absent_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    prior = {"prior": True}
    target.write_text(json.dumps(prior) + "\n", encoding="utf-8")
    prior_bytes = target.read_bytes()

    def _boom(*, destination: Path, body: str) -> None:
        raise OSError("injected write failure")

    monkeypatch.setattr(
        "src.ops.dynamic_scope_archive_sibling_exporter_v1.exporter_v1._atomic_write_text",
        _boom,
    )
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_WRITE_FAILED
    assert target.read_bytes() == prior_bytes


def test_identical_source_target_paths_fail_closed(tmp_path: Path) -> None:
    # Make state_root == archive_root/readmodels so filenames collide.
    archive_root = tmp_path / "archive_root"
    state_root = archive_root / "readmodels"
    state_root.mkdir(parents=True)
    # Persist into that colliding layout.
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(6)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=state_root,
    )
    assert result.ok
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_IDENTICAL_PATHS


def test_path_boundary_only_authorized_sibling(tmp_path: Path) -> None:
    state_root = _persist_valid_state(tmp_path)
    archive_root = tmp_path / "archive_root"
    out = export_dynamic_scope_state_to_archive_sibling_v1(
        dynamic_scope_state_root=state_root,
        archive_root=archive_root,
    )
    assert out.exported is True
    written_files = sorted(
        p.relative_to(archive_root).as_posix() for p in archive_root.rglob("*") if p.is_file()
    )
    assert written_files == ["readmodels/dynamic_scope_state_v1.json"]


def test_exporter_package_forbids_dashboard_and_presentation_imports() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    pkg = repo_root / EXPORTER_PKG
    assert pkg.is_dir()
    for path in sorted(pkg.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    assert not name.startswith(FORBIDDEN_IMPORT_PREFIXES), path
                    assert "presentation_projection" not in name, path
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith(FORBIDDEN_IMPORT_PREFIXES), path
                assert "presentation_projection" not in mod, path
                assert "webui" not in mod.split("."), path


def test_no_productive_automatic_caller_wiring() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    symbol = "export_dynamic_scope_state_to_archive_sibling_v1"
    forbidden_roots = [
        repo_root / "src" / "webui",
        repo_root
        / "src"
        / "ops"
        / "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
        repo_root / "src" / "ops" / "dynamic_scope_persistence_binding_v1",
        repo_root / "src" / "ops" / "full_decision_path_atomic_restart_closure_v1",
    ]
    hits: list[str] = []
    for root in forbidden_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if symbol in text:
                hits.append(str(path.relative_to(repo_root)))
    assert hits == []


def test_capability_id_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_DYNAMIC_SCOPE_ARCHIVE_SIBLING_EXPORTER_V1"
    # Touch clock so mtime assertions remain meaningful across fast FS.
    time.sleep(0.01)
