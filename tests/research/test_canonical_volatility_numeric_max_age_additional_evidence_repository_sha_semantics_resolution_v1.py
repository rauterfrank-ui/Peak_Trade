"""Tests for additional-evidence repository SHA semantics resolution (contract v2)."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.architecture_guards_v2 import (
    assert_architecture_guards_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    ARTIFACT_RELATIVE_PATH,
    CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
    CRITICAL_SURFACE_PATHS,
    DEFAULT_CODE_BASELINE_SHA,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    PREREGISTRATION_RELATIVE_PATH,
    REPOSITORY_BINDING_MODE,
    V1_CANDIDATE_SCHEMA_VERSION,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    build_active_additional_evidence_session_preregistration_v2,
    build_example_additional_session_candidate_v2,
    compute_candidate_preregistration_digest_v2,
    count_active_v2_preregistrations,
    render_additional_evidence_session_preregistration_contract_v2,
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.critical_surface_v2 import (
    compute_critical_surface_manifest_digest_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.readiness_v2 import (
    evaluate_authorization_readiness_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.contract_v1 import (
    build_example_additional_session_candidate_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    EXIT_PRECEDENCE_PRESERVED,
    REVERSAL_REDUCE_FIRST_PRESERVED,
)

ROOT = Path(__file__).resolve().parents[2]


def _rehash(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out.pop("preregistration_digest", None)
    out["preregistration_digest"] = compute_candidate_preregistration_digest_v2(out)
    return out


def _surface_overrides_from_root(root: Path = ROOT) -> dict[str, bytes]:
    return {rel: (root / rel).read_bytes() for rel in CRITICAL_SURFACE_PATHS}


def _valid_candidate(**kwargs: Any) -> dict[str, Any]:
    return build_example_additional_session_candidate_v2(repo_root=ROOT, **kwargs).to_dict()


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return (proc.stdout or "").strip()


def _init_temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "README")
    _git(repo, "commit", "-m", "baseline")
    return repo


def test_01_v2_happy_path_baseline_equals_execution() -> None:
    payload = _valid_candidate()
    assert (
        validate_additional_evidence_session_preregistration_candidate_v2(payload)["valid"] is True
    )
    result = evaluate_authorization_readiness_v2(
        payload,
        execution_repository_sha=payload["code_baseline_sha"],
        repo_root=ROOT,
        path_content_overrides=_surface_overrides_from_root(),
    )
    assert result["ready"] is True
    assert result["CODE_BASELINE_IS_ANCESTOR_OF_EXECUTION_SHA"] is True
    assert result["CRITICAL_SURFACE_DIGEST_MATCH"] is True
    assert result["TIP_OF_MAIN_EQUALITY_REQUIRED"] is False


def test_02_descendant_happy_path(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path)
    baseline = _git(repo, "rev-parse", "HEAD")
    # Create a descendant commit (non-critical path change).
    (repo / "README").write_text("descendant\n", encoding="utf-8")
    _git(repo, "add", "README")
    _git(repo, "commit", "-m", "descendant")
    execution = _git(repo, "rev-parse", "HEAD")
    assert baseline != execution

    overrides = _surface_overrides_from_root()
    digest = compute_critical_surface_manifest_digest_v2(
        repo_root=ROOT, path_content_overrides=overrides
    )
    payload = _valid_candidate(
        code_baseline_sha=baseline,
        artifact_creation_sha=baseline,
        critical_surface_manifest_digest=digest,
    )
    # Ancestor check uses temp repo; critical surface via overrides.
    # Patch git root for ancestor by evaluating with repo_root=temp for ancestor
    # and overrides for surface — readiness uses same repo_root for both.
    # Seed critical surface files into temp repo at execution for git show.
    for rel, content in overrides.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "add critical surfaces")
    execution = _git(repo, "rev-parse", "HEAD")
    # Recompute digest at seeded content (same bytes)
    digest2 = compute_critical_surface_manifest_digest_v2(repo_root=repo)
    payload = _valid_candidate(
        code_baseline_sha=baseline,
        artifact_creation_sha=baseline,
        critical_surface_manifest_digest=digest2,
    )
    result = evaluate_authorization_readiness_v2(
        payload,
        execution_repository_sha=execution,
        repo_root=repo,
    )
    assert result["ready"] is True
    assert result["execution_repository_sha"] == execution
    assert result["code_baseline_sha"] == baseline


def test_03_non_ancestor_reject(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path)
    baseline = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "--orphan", "other")
    (repo / "OTHER").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "OTHER")
    _git(repo, "commit", "-m", "other-root")
    other = _git(repo, "rev-parse", "HEAD")
    overrides = _surface_overrides_from_root()
    for rel, content in overrides.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    digest = compute_critical_surface_manifest_digest_v2(
        repo_root=ROOT, path_content_overrides=overrides
    )
    payload = _valid_candidate(
        code_baseline_sha=baseline,
        artifact_creation_sha=baseline,
        critical_surface_manifest_digest=digest,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="code_baseline_not_ancestor_of_execution_sha",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=other,
            repo_root=repo,
            path_content_overrides=overrides,
        )


def test_04_unknown_baseline_sha_reject() -> None:
    unknown = "a" * 40
    payload = _valid_candidate(code_baseline_sha=unknown, artifact_creation_sha=unknown)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="code_baseline_sha_unknown_commit|unknown_commit",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=DEFAULT_CODE_BASELINE_SHA,
            repo_root=ROOT,
            path_content_overrides=_surface_overrides_from_root(),
        )


def test_05_unknown_execution_sha_reject() -> None:
    payload = _valid_candidate()
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="execution_repository_sha_unknown_commit|unknown_commit",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha="b" * 40,
            repo_root=ROOT,
            path_content_overrides=_surface_overrides_from_root(),
        )


def test_06_critical_surface_drift_reject() -> None:
    payload = _valid_candidate()
    overrides = _surface_overrides_from_root()
    # Drift one critical surface file.
    key = next(iter(overrides))
    overrides[key] = overrides[key] + b"\n#drift\n"
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="critical_surface_manifest_digest_mismatch",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=payload["code_baseline_sha"],
            repo_root=ROOT,
            path_content_overrides=overrides,
        )


def test_07_contract_validator_drift_reject() -> None:
    payload = _valid_candidate()
    overrides = _surface_overrides_from_root()
    rel = next(r for r in CRITICAL_SURFACE_PATHS if r.endswith("validate_v2.py"))
    overrides[rel] = overrides[rel] + b"\n# validator drift\n"
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="critical_surface_manifest_digest_mismatch",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=payload["code_baseline_sha"],
            repo_root=ROOT,
            path_content_overrides=overrides,
        )


def test_08_builder_drift_reject() -> None:
    payload = _valid_candidate()
    overrides = _surface_overrides_from_root()
    rel = next(r for r in CRITICAL_SURFACE_PATHS if r.endswith("contract_v2.py"))
    overrides[rel] = overrides[rel] + b"\n# builder drift\n"
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="critical_surface_manifest_digest_mismatch",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=payload["code_baseline_sha"],
            repo_root=ROOT,
            path_content_overrides=overrides,
        )


@pytest.mark.parametrize(
    ("field", "bad", "code"),
    [
        ("venue", "BINANCE", "venue_binding_mismatch"),
        ("instrument", "BTC-USD_UM_XPERP-1", "instrument_binding_mismatch"),
        ("network_scope", "OTHER", "network_scope_binding_mismatch"),
        ("session_scope", "OTHER_SCOPE", "session_scope_binding_mismatch"),
    ],
)
def test_09_scope_drift_reject(field: str, bad: str, code: str) -> None:
    payload = _valid_candidate()
    payload[field] = bad
    payload = _rehash(payload)
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractV2Error, match=code):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_10_unknown_contract_field_reject() -> None:
    payload = _valid_candidate()
    payload["unexpected_field"] = True
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="unknown_candidate_fields:unexpected_field",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_11_unknown_authority_field_reject() -> None:
    payload = _valid_candidate()
    payload["trading_decision_authority"] = True
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="unknown_authority_fields",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_12_unknown_binding_mode_reject() -> None:
    payload = _valid_candidate()
    payload["repository_binding_mode"] = "TIP_OF_MAIN_EQUALITY"
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="unknown_binding_mode",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_13_unknown_contract_version_reject() -> None:
    payload = _valid_candidate()
    payload["schema_version"] = (
        "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v99"
    )
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="unknown_contract_version",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_14_invalid_sha_format_reject() -> None:
    payload = _valid_candidate()
    payload["code_baseline_sha"] = "abc123"
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="code_baseline_sha_invalid",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)


def test_15_artifact_creation_before_baseline_reject(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path)
    first = _git(repo, "rev-parse", "HEAD")
    (repo / "README").write_text("second\n", encoding="utf-8")
    _git(repo, "add", "README")
    _git(repo, "commit", "-m", "second")
    second = _git(repo, "rev-parse", "HEAD")
    overrides = _surface_overrides_from_root()
    digest = compute_critical_surface_manifest_digest_v2(
        repo_root=ROOT, path_content_overrides=overrides
    )
    # Baseline after artifact creation: baseline=second, artifact=first
    payload = _valid_candidate(
        code_baseline_sha=second,
        artifact_creation_sha=first,
        critical_surface_manifest_digest=digest,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="code_baseline_after_artifact_creation_sha",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=second,
            repo_root=repo,
            path_content_overrides=overrides,
        )


def test_16_tip_of_main_equality_not_required() -> None:
    payload = _valid_candidate()
    result = evaluate_authorization_readiness_v2(
        payload,
        execution_repository_sha=payload["code_baseline_sha"],
        repo_root=ROOT,
        path_content_overrides=_surface_overrides_from_root(),
        require_head_equals_origin_main=False,
    )
    assert result["TIP_OF_MAIN_EQUALITY_REQUIRED"] is False
    assert result["ready"] is True
    # Even if HEAD != some other tip, readiness still passes without tip gate.
    contract = render_additional_evidence_session_preregistration_contract_v2(
        repo_root=ROOT,
        code_baseline_sha=payload["code_baseline_sha"],
        artifact_creation_sha=payload["artifact_creation_sha"],
        critical_surface_manifest_digest=payload["critical_surface_manifest_digest"],
    )
    assert contract["tip_of_main_equality_required"] is False


def test_17_squash_merge_simulation(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path)
    baseline = _git(repo, "rev-parse", "HEAD")
    overrides = _surface_overrides_from_root()
    for rel, content in overrides.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    digest = compute_critical_surface_manifest_digest_v2(repo_root=repo)
    payload = _valid_candidate(
        code_baseline_sha=baseline,
        artifact_creation_sha=baseline,
        critical_surface_manifest_digest=digest,
    )
    # Capability integrated as new commit (squash-merge simulation).
    (repo / "CAPABILITY").write_text("merged\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "squash-merge-capability")
    execution = _git(repo, "rev-parse", "HEAD")
    assert baseline != execution
    result = evaluate_authorization_readiness_v2(
        payload,
        execution_repository_sha=execution,
        repo_root=repo,
    )
    assert result["ready"] is True
    assert result["CODE_BASELINE_IS_ANCESTOR_OF_EXECUTION_SHA"] is True
    assert result["CRITICAL_SURFACE_DIGEST_MATCH"] is True


def test_18_semantic_surface_change_after_baseline_fail_closed(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path)
    baseline = _git(repo, "rev-parse", "HEAD")
    overrides = _surface_overrides_from_root()
    for rel, content in overrides.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    digest = compute_critical_surface_manifest_digest_v2(repo_root=repo)
    payload = _valid_candidate(
        code_baseline_sha=baseline,
        artifact_creation_sha=baseline,
        critical_surface_manifest_digest=digest,
    )
    # Semantic drift after baseline on a critical surface.
    rel = next(r for r in CRITICAL_SURFACE_PATHS if r.endswith("constants_v2.py"))
    path = repo / rel
    path.write_bytes(path.read_bytes() + b"\nDRIFT=True\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "surface-drift")
    execution = _git(repo, "rev-parse", "HEAD")
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="critical_surface_manifest_digest_mismatch",
    ):
        evaluate_authorization_readiness_v2(
            payload,
            execution_repository_sha=execution,
            repo_root=repo,
        )


def test_19_v1_no_new_authorization_readiness() -> None:
    v1 = build_example_additional_session_candidate_v1().to_dict()
    assert v1["schema_version"] == V1_CANDIDATE_SCHEMA_VERSION
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="v1_new_authorization_readiness_unsupported",
    ):
        evaluate_authorization_readiness_v2(
            v1,
            execution_repository_sha=DEFAULT_CODE_BASELINE_SHA,
            repo_root=ROOT,
            path_content_overrides=_surface_overrides_from_root(),
        )


def test_20_exactly_one_active_v2_preregistration() -> None:
    assert count_active_v2_preregistrations(repo_root=ROOT) == 1
    active = json.loads((ROOT / PREREGISTRATION_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert active["schema_version"].endswith("/v2")
    assert active["repository_binding_mode"] == REPOSITORY_BINDING_MODE
    assert "repository_sha" not in active
    validate_additional_evidence_session_preregistration_candidate_v2(active)


def test_21_existing_quarantine_and_s01_s02_evidence_unchanged() -> None:
    # Capability must not mutate productive s01/s02 preregistration.
    productive = ROOT / (
        "config/research/"
        "canonical_volatility_numeric_max_age_productive_evidence_"
        "session_preregistration_v1.json"
    )
    assert productive.is_file()
    before = hashlib.sha256(productive.read_bytes()).hexdigest()
    # Touching builders must not rewrite that path.
    _ = build_active_additional_evidence_session_preregistration_v2(repo_root=ROOT)
    after = hashlib.sha256(productive.read_bytes()).hexdigest()
    assert before == after
    # Quarantine path (if present locally) is outside this capability write set.
    assert ARTIFACT_RELATIVE_PATH.endswith("contract_v2.json")
    assert not ARTIFACT_RELATIVE_PATH.endswith("preregistration_v1.json")


def test_artifact_and_guards() -> None:
    verify_additional_evidence_session_preregistration_contract_artifact_v2(repo_root=ROOT)
    guards = assert_architecture_guards_v2(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["tip_of_main_equality_required"] is False
    assert (ROOT / CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH).is_file()


def test_scope_bindings_preserved() -> None:
    payload = _valid_candidate()
    result = validate_additional_evidence_session_preregistration_candidate_v2(payload)
    assert result["venue"] == EXPECTED_VENUE
    assert result["instrument"] == EXPECTED_INSTRUMENT
    assert result["network_scope"] == EXPECTED_NETWORK_SCOPE
    assert result["session_scope"] == EXPECTED_SESSION_SCOPE


def test_strategy_safety_smoke_unchanged() -> None:
    assert EXIT_PRECEDENCE_PRESERVED is True
    assert REVERSAL_REDUCE_FIRST_PRESERVED is True


def test_removed_repository_sha_field_rejected() -> None:
    payload = _valid_candidate()
    payload["repository_sha"] = DEFAULT_CODE_BASELINE_SHA
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractV2Error,
        match="unknown_candidate_fields:repository_sha",
    ):
        validate_additional_evidence_session_preregistration_candidate_v2(payload)
