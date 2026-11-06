"""Regression tests for PREREGISTRATION_PROBE_FIXTURE_REPOSITORY_SHA_BINDING_V1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.constants_v1 import (
    BRIDGED_CAPABILITY,
    GO_FOR_1H_RUN,
    GO_FOR_AUTHORIZATION,
    GO_FOR_PREREGISTRATION,
    HARD_STOP,
    LOCAL_OPERATOR_COPY_BYTE_IDENTICAL,
    PROBE_TYPE_CANONICAL,
    PROBE_TYPE_FORCED_FIXTURE,
    RUNBOOK_NORMATIVE_FILENAME,
    RUNBOOK_SHA256,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.probe_fixture_sha_verifier_v1 import (
    verify_probe_fixture_repository_sha_binding_v1,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.repository_sha_source_v1 import (
    RepositoryShaResolutionErrorV1,
    assert_valid_repository_sha_v1,
    resolve_repository_sha_from_git_head_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.canonical_strategy_probe_v2 import (
    run_canonical_strategy_probe_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.forced_wiring_fixture_v2 import (
    FORCED_WIRING_FIXTURE_MODULE,
    run_forced_wiring_fixture_v2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_SHA = "a" * 40
OTHER_SHA = "b" * 40


def test_runbook_attestation_constants() -> None:
    assert RUNBOOK_NORMATIVE_FILENAME == (
        "Peak_Trade_Full_System_Paper_Shadow_1h_Runbook_v4_forensic_safe(6).md"
    )
    assert RUNBOOK_SHA256 == "a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a"
    assert LOCAL_OPERATOR_COPY_BYTE_IDENTICAL is True
    assert GO_FOR_PREREGISTRATION is False
    assert GO_FOR_AUTHORIZATION is False
    assert GO_FOR_1H_RUN is False
    assert HARD_STOP is True
    assert BRIDGED_CAPABILITY.endswith("RUNTIME_BRIDGE_V1")


def test_assert_valid_repository_sha_fail_closed() -> None:
    assert assert_valid_repository_sha_v1(VALID_SHA) == VALID_SHA
    with pytest.raises(RepositoryShaResolutionErrorV1, match="MISSING"):
        assert_valid_repository_sha_v1(None)
    with pytest.raises(RepositoryShaResolutionErrorV1, match="EMPTY"):
        assert_valid_repository_sha_v1("")
    with pytest.raises(RepositoryShaResolutionErrorV1, match="INVALID_LENGTH"):
        assert_valid_repository_sha_v1("abc123")
    with pytest.raises(RepositoryShaResolutionErrorV1, match="INVALID_HEX_FORMAT"):
        assert_valid_repository_sha_v1("g" * 40)
    with pytest.raises(RepositoryShaResolutionErrorV1, match="NOT_LOWERCASE"):
        assert_valid_repository_sha_v1(("A" * 40))


def test_resolve_repository_sha_from_git_head() -> None:
    sha = resolve_repository_sha_from_git_head_v1(repo_root=REPO_ROOT)
    assert len(sha) == 40
    assert sha == sha.lower()
    assert all(c in "0123456789abcdef" for c in sha)


def test_canonical_probe_persists_full_repository_sha(tmp_path: Path) -> None:
    result = run_canonical_strategy_probe_v2(
        evidence_root=tmp_path / "canonical",
        repository_sha=VALID_SHA,
    )
    assert result["canonical_strategy_probe_pass"] is True
    assert result["canonical_strategy_probe_sha_bound"] is True
    assert result["canonical_strategy_probe_repository_sha"] == VALID_SHA
    assert result["canonical_strategy_probe_expected_sha"] == VALID_SHA
    manifest = json.loads((tmp_path / "canonical" / "session_manifest.json").read_text())
    assert manifest["repository_sha"] == VALID_SHA
    assert manifest["probe_type"] == PROBE_TYPE_CANONICAL
    assert manifest["capability"] == BRIDGED_CAPABILITY
    assert manifest["created_at_utc"]
    assert manifest["evidence_schema_version"]
    completion = json.loads((tmp_path / "canonical" / "completion_verdict.json").read_text())
    integrity = json.loads((tmp_path / "canonical" / "integrity_manifest.json").read_text())
    assert completion["repository_sha"] == VALID_SHA
    assert integrity["repository_sha"] == VALID_SHA


def test_forced_fixture_persists_full_repository_sha(tmp_path: Path) -> None:
    result = run_forced_wiring_fixture_v2(
        evidence_root=tmp_path / "forced",
        repository_sha=VALID_SHA,
    )
    assert result["forced_wiring_fixture_pass"] is True
    assert result["forced_wiring_fixture_sha_bound"] is True
    assert result["forced_wiring_fixture_repository_sha"] == VALID_SHA
    assert result["forced_fixture_wallclock_reachable"] is False
    assert result["forced_fixture_economic_metrics_excluded"] is True
    assert result["forced_fixture_can_consume_productive_authorization"] is False
    manifest = json.loads((tmp_path / "forced" / "session_manifest.json").read_text())
    assert manifest["repository_sha"] == VALID_SHA
    assert manifest["probe_type"] == PROBE_TYPE_FORCED_FIXTURE


def _mutate_sha(evidence_root: Path, *, artifact: str, value: object) -> None:
    path = evidence_root / artifact
    payload = json.loads(path.read_text(encoding="utf-8"))
    if value is None:
        payload.pop("repository_sha", None)
    else:
        payload["repository_sha"] = value
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_sha_missing_empty_short_nonhex_uppercase_mismatch_fail(tmp_path: Path) -> None:
    run_canonical_strategy_probe_v2(
        evidence_root=tmp_path / "base",
        repository_sha=VALID_SHA,
    )
    # missing
    root = tmp_path / "missing"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="session_manifest.json", value=None)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert bad.sha_bound is False
    assert any("MISSING" in b for b in bad.blockers)

    # empty
    root = tmp_path / "empty"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="session_manifest.json", value="")
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("EMPTY" in b for b in bad.blockers)

    # short
    root = tmp_path / "short"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="session_manifest.json", value="abc123")
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("INVALID_LENGTH" in b for b in bad.blockers)

    # non-hex
    root = tmp_path / "nonhex"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="session_manifest.json", value="z" * 40)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("INVALID_HEX_FORMAT" in b for b in bad.blockers)

    # uppercase
    root = tmp_path / "upper"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="session_manifest.json", value=("A" * 40))
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("NOT_LOWERCASE" in b for b in bad.blockers)

    # expected mismatch
    root = tmp_path / "mismatch"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=OTHER_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("MISMATCH" in b for b in bad.blockers)


def test_cross_artifact_conflict_and_substitution_fail(tmp_path: Path) -> None:
    root = tmp_path / "conflict"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="completion_verdict.json", value=OTHER_SHA)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("CROSS_ARTIFACT_CONFLICT" in b for b in bad.blockers)

    root = tmp_path / "integrity_conflict"
    run_canonical_strategy_probe_v2(evidence_root=root, repository_sha=VALID_SHA)
    _mutate_sha(root, artifact="integrity_manifest.json", value=OTHER_SHA)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("CROSS_ARTIFACT_CONFLICT" in b for b in bad.blockers)

    # Substitution: verify forced evidence as canonical must fail.
    forced_root = tmp_path / "forced_sub"
    run_forced_wiring_fixture_v2(evidence_root=forced_root, repository_sha=VALID_SHA)
    bad = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=forced_root,
        expected_repository_sha=VALID_SHA,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    assert bad.ok is False
    assert any("PROBE_TYPE_MISMATCH" in b or "SUBSTITUTION" in b for b in bad.blockers)


def test_fixture_isolation_invariants(tmp_path: Path) -> None:
    result = run_forced_wiring_fixture_v2(
        evidence_root=tmp_path / "forced_iso",
        repository_sha=VALID_SHA,
    )
    assert result["forced_fixture_wallclock_reachable"] is False
    assert result["forced_fixture_economic_metrics_excluded"] is True
    assert result["forced_fixture_can_consume_productive_authorization"] is False
    runtime = (
        REPO_ROOT / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "session_runtime_v1.py"
    ).read_text(encoding="utf-8")
    assert "forced_wiring_fixture_v2" not in runtime
    assert FORCED_WIRING_FIXTURE_MODULE.endswith("forced_wiring_fixture_v2")


def test_no_private_api_or_order_routing_in_sha_binding_package() -> None:
    pkg = REPO_ROOT / "src/ops/preregistration_probe_fixture_repository_sha_binding_v1"
    forbidden = {"place_order", "submit_order", "create_order", "cancel_order"}
    for path in pkg.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                assert name not in forbidden
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "private" not in node.module.lower()
                assert not node.module.startswith("src.execution.venue")
