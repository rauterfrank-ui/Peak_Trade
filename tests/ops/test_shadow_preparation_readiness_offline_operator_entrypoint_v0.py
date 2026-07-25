"""Focused contract tests for offline shadow readiness operator entrypoint v0."""

from __future__ import annotations

import ast
import io
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
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
)
from src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 import (
    EXIT_BLOCKED,
    EXIT_ERROR,
    EXIT_PASS,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_ID,
    exit_code_for_pipeline_result,
    main,
)
from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import (
    PIPELINE_STATUS_BLOCKED,
    PIPELINE_STATUS_ERROR,
    PIPELINE_STATUS_PASS,
    READINESS_STATUS_BLOCKED,
    READINESS_STATUS_READY,
    ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
    run_shadow_preparation_readiness_offline_projection_pipeline_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
ENTRYPOINT_MODULE = (
    REPO_ROOT / "src" / "ops" / "shadow_preparation_readiness_offline_operator_entrypoint_v0.py"
)
PIPELINE_MODULE = (
    REPO_ROOT / "src" / "ops" / "shadow_preparation_readiness_offline_projection_pipeline_v0.py"
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


def _run_main(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    code = main(argv, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def test_package_marker_and_identity() -> None:
    assert PACKAGE_MARKER == "SHADOW_PREPARATION_READINESS_OFFLINE_OPERATOR_ENTRYPOINT_V0=true"
    assert PRODUCER_FAMILY == SCHEMA_ID
    assert PRODUCER_FAMILY.endswith("_v0")
    assert EXIT_PASS == 0
    assert EXIT_ERROR == 1
    assert EXIT_BLOCKED == 2


def test_pass_exit_code_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0

    def _ready_evaluate(**kwargs):
        return _ready_like_evaluation(real_evaluate(**kwargs))

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _ready_evaluate,
    )
    code, stdout, _stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--format",
            "text",
        ]
    )
    assert code == EXIT_PASS == 0
    assert "status=PIPELINE_PASS" in stdout


def test_blocked_exit_code_two(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    code, stdout, stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--format",
            "text",
        ]
    )
    assert code == EXIT_BLOCKED == 2
    assert "status=PIPELINE_BLOCKED" in stdout
    assert "authorizes nothing" in stderr
    assert "Traceback" not in stdout
    assert "Traceback" not in stderr


def test_error_exit_code_one(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    (root / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml").unlink()
    code, stdout, _stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--format",
            "text",
        ]
    )
    assert code == EXIT_ERROR == 1
    assert "status=PIPELINE_ERROR" in stdout


def test_pipeline_invoked_exactly_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    calls = {"n": 0}
    real = run_shadow_preparation_readiness_offline_projection_pipeline_v0

    def _once(**kwargs):
        calls["n"] += 1
        return real(**kwargs)

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0."
        "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
        _once,
    )
    code, _stdout, _stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
        ]
    )
    assert calls["n"] == 1
    assert code == EXIT_BLOCKED


def test_json_output_parseable_and_deterministic_structure(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    argv = [
        "--repo-root",
        str(root),
        "--output-path",
        DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        "--evaluated-at",
        EVALUATED_AT,
        "--as-of",
        AS_OF,
        "--format",
        "json",
    ]
    code1, stdout1, _ = _run_main(argv)
    code2, stdout2, _ = _run_main(argv)
    assert code1 == code2 == EXIT_BLOCKED
    payload1 = json.loads(stdout1)
    payload2 = json.loads(stdout2)
    assert payload1 == payload2
    for key in (
        "schema_id",
        "schema_version",
        "pipeline_status",
        "projection_path",
        "verification_status",
        "reason_codes",
        "authority_effect",
        "activation_authority",
        "projection_only",
    ):
        assert key in payload1
    assert payload1["pipeline_status"] == PIPELINE_STATUS_BLOCKED
    assert payload1["authority_effect"] == "NONE"
    assert payload1["activation_authority"] is False
    assert payload1["projection_only"] is True


def test_text_output_distinguishes_pass_blocked_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _fake_result(status: str) -> ShadowPreparationReadinessOfflineProjectionPipelineResultV0:
        readiness = (
            READINESS_STATUS_READY if status == PIPELINE_STATUS_PASS else READINESS_STATUS_BLOCKED
        )
        if status == PIPELINE_STATUS_ERROR:
            readiness = None
        return ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
            pipeline_status=status,  # type: ignore[arg-type]
            readiness_status=readiness,  # type: ignore[arg-type]
            evaluated_at=EVALUATED_AT,
            projection_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            projection_schema_id="shadow_preparation_readiness_projection",
            projection_schema_version="v0",
            projection_sha256="abc",
            verification_status="VERIFIED" if status != PIPELINE_STATUS_ERROR else None,
            verification_verified=True if status != PIPELINE_STATUS_ERROR else None,
            reason_codes=("X",) if status == PIPELINE_STATUS_ERROR else (),
            evidence_reference_count=0,
        )

    for status, expected_code, needle in (
        (PIPELINE_STATUS_PASS, EXIT_PASS, "status=PIPELINE_PASS"),
        (PIPELINE_STATUS_BLOCKED, EXIT_BLOCKED, "status=PIPELINE_BLOCKED"),
        (PIPELINE_STATUS_ERROR, EXIT_ERROR, "status=PIPELINE_ERROR"),
    ):

        def _make_runner(selected: str):
            def _runner(**_kwargs: Any):
                return _fake_result(selected)

            return _runner

        monkeypatch.setattr(
            "src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0."
            "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
            _make_runner(status),
        )
        code, stdout, _stderr = _run_main(["--repo-root", str(root), "--format", "text"])
        assert code == expected_code
        assert needle in stdout


def test_blocked_authorizes_nothing(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    code, stdout, stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--format",
            "json",
        ]
    )
    assert code == EXIT_BLOCKED
    payload = json.loads(stdout)
    assert payload["activation_authority"] is False
    assert payload["authority_effect"] == "NONE"
    assert payload["projection_only"] is True
    assert "authorizes nothing" in stderr


def test_no_shadow_paper_testnet_scheduler_runtime_calls(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    source = ENTRYPOINT_MODULE.read_text(encoding="utf-8")
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
    code, _stdout, _stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
        ]
    )
    assert code == EXIT_BLOCKED


def test_reuses_canonical_pipeline_writer_verifier_no_duplicate_serialization() -> None:
    source = ENTRYPOINT_MODULE.read_text(encoding="utf-8")
    assert "run_shadow_preparation_readiness_offline_projection_pipeline_v0" in source
    assert (
        "from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import" in source
    )
    # Must not reimplement gate/writer/reader/verify/serialize.
    for forbidden in (
        "evaluate_shadow_preparation_readiness_gate_v0",
        "write_shadow_preparation_readiness_projection_v0",
        "verify_shadow_preparation_readiness_projection_v0",
        "serialize_shadow_preparation_readiness_projection_v0",
        "build_shadow_preparation_readiness_projection_payload_v0",
    ):
        assert forbidden not in source
    assert "to_dict()" in source
    # Pipeline module remains the sole orchestration owner.
    assert PIPELINE_MODULE.is_file()


def test_unexpected_exception_remains_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _boom(**_kwargs):
        raise RuntimeError("unexpected boom")

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0."
        "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
        _boom,
    )
    with pytest.raises(RuntimeError, match="unexpected boom"):
        main(
            ["--repo-root", str(root), "--format", "text"],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )


def test_invalid_cli_arguments_fail_closed_without_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    calls = {"n": 0}

    def _must_not_run(**_kwargs: Any):
        calls["n"] += 1
        raise AssertionError("pipeline must not run on invalid CLI args")

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0."
        "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
        _must_not_run,
    )
    code, _stdout, _stderr = _run_main(["--repo-root", str(root), "--format", "xml"])
    assert code == EXIT_ERROR
    assert calls["n"] == 0
    code2, _stdout2, _stderr2 = _run_main(["--format", "json"])  # missing --repo-root
    assert code2 == EXIT_ERROR
    assert calls["n"] == 0


def test_no_network_dependency(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    original_socket = socket.socket

    class _BlockedSocket(original_socket):  # type: ignore[misc,valid-type]
        def __init__(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError("network side effect forbidden")

    socket.socket = _BlockedSocket  # type: ignore[misc]
    try:
        code, _stdout, _stderr = _run_main(
            [
                "--repo-root",
                str(root),
                "--output-path",
                DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
                "--evaluated-at",
                EVALUATED_AT,
                "--as-of",
                AS_OF,
                "--format",
                "json",
            ]
        )
        assert code == EXIT_BLOCKED
    finally:
        socket.socket = original_socket  # type: ignore[misc]


def test_no_tracked_projection_output(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    code, stdout, _stderr = _run_main(
        [
            "--repo-root",
            str(root),
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--format",
            "json",
        ]
    )
    assert code == EXIT_BLOCKED
    payload = json.loads(stdout)
    path = payload["projection_path"]
    assert path.startswith("out/")
    assert not any(path.startswith(prefix) for prefix in ("src/", "tests/", "docs/", "config/"))
    assert (root / path).is_file()


def test_exit_code_mapping_helpers() -> None:
    for status, expected in (
        (PIPELINE_STATUS_PASS, EXIT_PASS),
        (PIPELINE_STATUS_BLOCKED, EXIT_BLOCKED),
        (PIPELINE_STATUS_ERROR, EXIT_ERROR),
    ):
        result = ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
            pipeline_status=status,  # type: ignore[arg-type]
            readiness_status=None,
            evaluated_at=None,
            projection_path=None,
            projection_schema_id=None,
            projection_schema_version=None,
            projection_sha256=None,
            verification_status=None,
            verification_verified=None,
            reason_codes=(),
            evidence_reference_count=None,
        )
        assert exit_code_for_pipeline_result(result) == expected
