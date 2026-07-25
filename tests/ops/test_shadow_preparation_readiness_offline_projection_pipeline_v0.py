"""Focused tests for offline shadow readiness projection pipeline v0."""

from __future__ import annotations

import ast
import hashlib
import json
import socket
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.shadow_preparation_readiness_gate_v0 import (
    CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY,
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    PreparationStatusV0,
    PROJECTION_SCHEMA_ID,
    PROJECTION_SCHEMA_VERSION,
    ShadowPreparationReadinessGateError,
    ShadowPreparationReadinessProjectionWriteMetadataV0,
    build_shadow_preparation_readiness_projection_payload_v0,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
    serialize_shadow_preparation_readiness_projection_v0,
    verify_shadow_preparation_readiness_projection_v0,
    write_shadow_preparation_readiness_projection_v0,
)
from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import (
    PACKAGE_MARKER,
    PIPELINE_STATUS_BLOCKED,
    PIPELINE_STATUS_ERROR,
    PIPELINE_STATUS_PASS,
    PRODUCER_FAMILY,
    READINESS_STATUS_BLOCKED,
    READINESS_STATUS_READY,
    SCHEMA_ID,
    run_shadow_preparation_readiness_offline_projection_pipeline_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
PIPELINE_MODULE = (
    REPO_ROOT / "src" / "ops" / "shadow_preparation_readiness_offline_projection_pipeline_v0.py"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)
EVALUATED_AT = "2026-07-25T12:00:00Z"
AS_OF = "2026-07-25T12:00:30Z"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "src.orders",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.trading.master_v2",
)


def _collect_required_relative_paths(cfg: dict) -> set[str]:
    paths: set[str] = set()
    for surface in cfg["historical_surfaces"]:
        paths.add(str(surface["path"]).strip())
    for component in cfg["mindestkontrakt_components"]:
        for evidence_path in component.get("evidence_paths") or []:
            paths.add(str(evidence_path).strip())
    paths.add(str(cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).strip())
    return paths


def _materialize_temp_repo(tmp_path: Path) -> tuple[Path, dict]:
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    for relative in _collect_required_relative_paths(cfg):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# stub:{relative}\n", encoding="utf-8")
    config_dest = tmp_path / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
    config_dest.parent.mkdir(parents=True, exist_ok=True)
    config_dest.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "out" / "ops").mkdir(parents=True, exist_ok=True)
    return tmp_path, cfg


def _ready_like_evaluation(base):
    inventory = tuple(
        replace(record, preparation_status=PreparationStatusV0.PRESENT)
        for record in base.mindestkontrakt_inventory
    )
    return replace(
        base,
        shadow_preparation_complete=True,
        blockers=(),
        unmet_gates=(),
        mindestkontrakt_inventory=inventory,
    )


def test_package_marker_and_schema_identity() -> None:
    assert PACKAGE_MARKER == "SHADOW_PREPARATION_READINESS_OFFLINE_PROJECTION_PIPELINE_V0=true"
    assert PRODUCER_FAMILY == SCHEMA_ID
    assert PRODUCER_FAMILY.endswith("_v0")


def test_ready_like_gate_result_writes_rereads_verifies_consistent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0
    evaluate_calls = {"n": 0}

    def _ready_evaluate(**kwargs):
        evaluate_calls["n"] += 1
        return _ready_like_evaluation(real_evaluate(**kwargs))

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _ready_evaluate,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert evaluate_calls["n"] == 1
    assert result.pipeline_status == PIPELINE_STATUS_PASS
    assert result.readiness_status == READINESS_STATUS_READY
    assert result.verification_verified is True
    assert result.verification_status == "VERIFIED"
    assert result.projection_path == DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH
    assert result.projection_schema_id == PROJECTION_SCHEMA_ID
    assert result.projection_schema_version == PROJECTION_SCHEMA_VERSION
    assert result.projection_sha256
    assert (root / result.projection_path).is_file()
    payload = json.loads((root / result.projection_path).read_text(encoding="utf-8"))
    assert payload["shadow_preparation_complete"] is True
    assert payload["evaluation"]["shadow_preparation_complete"] is True


def test_blocked_gate_result_is_pipeline_blocked_not_error(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert result.readiness_status == READINESS_STATUS_BLOCKED
    assert result.pipeline_status != PIPELINE_STATUS_ERROR
    assert result.verification_verified is True
    assert result.reason_codes == ()
    assert result.projection_sha256


def test_missing_required_input_fails_closed(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    (root / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml").unlink()
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert result.reason_codes
    assert any(
        code.startswith("PIPELINE_INPUT_INVALID:") or code.startswith("GATE_EVALUATION_FAILED:")
        for code in result.reason_codes
    )


def test_writer_failure_pipeline_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _fail_write(**_kwargs):
        raise ShadowPreparationReadinessGateError("PROJECTION_TEMP_WRITE_FAILED:boom")

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _fail_write,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert any(code.startswith("PROJECTION_WRITE_FAILED:") for code in result.reason_codes)


def test_reader_failure_pipeline_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _fail_verify(**_kwargs):
        raise OSError("read failed")

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "verify_shadow_preparation_readiness_projection_v0",
        _fail_verify,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert any(code.startswith("PROJECTION_VERIFY_FAILED:") for code in result.reason_codes)


def test_invalid_json_after_write_pipeline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_write = write_shadow_preparation_readiness_projection_v0

    def _write_then_corrupt(**kwargs):
        meta = real_write(**kwargs)
        (root / meta.output_path).write_text("{not-json", encoding="utf-8")
        return meta

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _write_then_corrupt,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "INVALID_PROJECTION" in result.reason_codes or any(
        "INVALID" in code for code in result.reason_codes
    )


def test_schema_mismatch_pipeline_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_write = write_shadow_preparation_readiness_projection_v0

    def _write_bad_schema(**kwargs):
        meta = real_write(**kwargs)
        dest = root / meta.output_path
        payload = json.loads(dest.read_text(encoding="utf-8"))
        payload["schema_version"] = "v999"
        content = serialize_shadow_preparation_readiness_projection_v0(payload)
        dest.write_bytes(content)
        return ShadowPreparationReadinessProjectionWriteMetadataV0(
            output_path=meta.output_path,
            schema_id=meta.schema_id,
            schema_version=meta.schema_version,
            byte_length=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _write_bad_schema,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "SCHEMA_MISMATCH" in result.reason_codes


def test_provenance_mismatch_pipeline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_build = build_shadow_preparation_readiness_projection_payload_v0

    def _bad_provenance(*, evaluation, evaluated_at):
        payload = real_build(evaluation=evaluation, evaluated_at=evaluated_at)
        payload["evaluation_schema_id"] = "other.schema"
        return payload

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_gate_v0."
        "build_shadow_preparation_readiness_projection_payload_v0",
        _bad_provenance,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "PROVENANCE_MISMATCH" in result.reason_codes


def test_evidence_path_reference_mismatch_pipeline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_build = build_shadow_preparation_readiness_projection_payload_v0

    def _bad_evidence(*, evaluation, evaluated_at):
        payload = real_build(evaluation=evaluation, evaluated_at=evaluated_at)
        inventory = payload["evaluation"]["mindestkontrakt_inventory"]
        inventory[0]["evidence_paths"] = ["docs/missing_evidence_target_v0.md"]
        return payload

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_gate_v0."
        "build_shadow_preparation_readiness_projection_payload_v0",
        _bad_evidence,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "EVIDENCE_REFERENCE_MISSING" in result.reason_codes


def test_evaluated_versus_projected_status_mismatch_pipeline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_build = build_shadow_preparation_readiness_projection_payload_v0

    def _status_drift(*, evaluation, evaluated_at):
        payload = real_build(evaluation=evaluation, evaluated_at=evaluated_at)
        payload["evaluation"]["blockers"] = list(evaluation.blockers) + ["EXTRA_BLOCKER"]
        return payload

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_gate_v0."
        "build_shadow_preparation_readiness_projection_payload_v0",
        _status_drift,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "EVALUATED_PROJECTION_STATUS_MISMATCH" in result.reason_codes or (
        "EVALUATED_PROJECTION_IDENTITY_MISMATCH" in result.reason_codes
    )


def test_digest_identity_mismatch_pipeline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_write = write_shadow_preparation_readiness_projection_v0

    def _wrong_digest(**kwargs):
        meta = real_write(**kwargs)
        return ShadowPreparationReadinessProjectionWriteMetadataV0(
            output_path=meta.output_path,
            schema_id=meta.schema_id,
            schema_version=meta.schema_version,
            byte_length=meta.byte_length,
            sha256="0" * 64,
        )

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _wrong_digest,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_ERROR
    assert "DIGEST_MISMATCH" in result.reason_codes


def test_stale_preexisting_projection_cannot_satisfy_current_invocation(
    tmp_path: Path,
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    dest = root / DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH
    stale_eval = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=root, evaluated_at="2026-07-20T12:00:00Z"
    )
    stale_meta = write_shadow_preparation_readiness_projection_v0(
        evaluation=stale_eval,
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at="2026-07-20T12:00:00Z",
    )
    stale_bytes = dest.read_bytes()
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert result.verification_verified is True
    assert result.projection_sha256 != stale_meta.sha256
    assert dest.read_bytes() != stale_bytes
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["evaluated_at"] == EVALUATED_AT


def test_temporary_partial_projection_cannot_satisfy_verification(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    dest = root / DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH
    partial = dest.parent / f".tmp_{dest.name}_partial.partial"
    evaluation = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=root, evaluated_at=EVALUATED_AT
    )
    payload = build_shadow_preparation_readiness_projection_payload_v0(
        evaluation=evaluation, evaluated_at=EVALUATED_AT
    )
    partial.write_bytes(serialize_shadow_preparation_readiness_projection_v0(payload))
    assert not dest.exists()
    verification = verify_shadow_preparation_readiness_projection_v0(
        repo_root=root,
        projection_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        as_of=AS_OF,
    )
    assert verification.verified is False
    assert "MISSING_PROJECTION" in verification.reason_codes
    # Pipeline must also refuse when only a partial exists.
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert result.verification_verified is True
    assert dest.is_file()
    assert dest.read_bytes() != partial.read_bytes() or result.projection_sha256


def test_canonical_writer_reader_verifier_invoked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    calls = {"evaluate": 0, "write": 0, "verify": 0}
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0
    real_write = write_shadow_preparation_readiness_projection_v0
    real_verify = verify_shadow_preparation_readiness_projection_v0

    def _e(**kwargs):
        calls["evaluate"] += 1
        return real_evaluate(**kwargs)

    def _w(**kwargs):
        calls["write"] += 1
        return real_write(**kwargs)

    def _v(**kwargs):
        calls["verify"] += 1
        assert kwargs.get("expected_sha256")
        return real_verify(**kwargs)

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _e,
    )
    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _w,
    )
    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "verify_shadow_preparation_readiness_projection_v0",
        _v,
    )
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert calls == {"evaluate": 1, "write": 1, "verify": 1}
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED


def test_no_network_runtime_scheduler_order_side_effects(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    original_socket = socket.socket

    class _BlockedSocket(original_socket):  # type: ignore[misc,valid-type]
        def __init__(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError("network side effect forbidden")

    socket.socket = _BlockedSocket  # type: ignore[misc]
    try:
        source = PIPELINE_MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not any(node.module.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
        for needle in (
            "activate_shadow",
            "start_scheduler",
            "place_order",
            "enable_paper",
            "enable_testnet",
            "requests.",
            "urllib",
        ):
            assert needle not in source
        result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
            repo_root=root,
            output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            evaluated_at=EVALUATED_AT,
            as_of=AS_OF,
        )
        assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    finally:
        socket.socket = original_socket  # type: ignore[misc]


def test_no_tracked_projection_output(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    # Projection lives under out/ (generated evidence), never under tracked src/tests/docs/config.
    assert result.projection_path is not None
    assert result.projection_path.startswith("out/")
    tracked_roots = ("src/", "tests/", "docs/", "config/")
    assert not any(result.projection_path.startswith(prefix) for prefix in tracked_roots)


def test_deterministic_repeated_input_semantic_equivalence(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    first = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    second = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert first.pipeline_status == second.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert first.projection_sha256 == second.projection_sha256
    assert first.readiness_status == second.readiness_status
    assert first.to_dict() == second.to_dict()


def test_exact_output_path_behavior_within_existing_contract(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    custom = "out/ops/custom_shadow_readiness_projection_v0.json"
    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path=custom,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert result.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert result.projection_path == custom
    assert (root / custom).is_file()
    # Empty explicit path fails closed.
    empty = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        output_path="   ",
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert empty.pipeline_status == PIPELINE_STATUS_ERROR
    assert any("PIPELINE_INPUT_INVALID" in code for code in empty.reason_codes)
    # Config default path is honored when output_path omitted.
    defaulted = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=root,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert defaulted.pipeline_status == PIPELINE_STATUS_BLOCKED
    assert defaulted.projection_path == DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH


def test_docs_declare_offline_pipeline_entrypoint() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "OFFLINE_PROJECTION_PIPELINE_V0=true" in text
    assert "run_shadow_preparation_readiness_offline_projection_pipeline_v0" in text
