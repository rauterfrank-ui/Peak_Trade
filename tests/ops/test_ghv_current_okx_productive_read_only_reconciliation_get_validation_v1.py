"""Phase-7/8 boundary and evidence-bound readiness tests (offline only)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    LifecycleReconciliationOrchestrationMode,
    PostSubmitLifecycleReconciliationOrchestrationRequestV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1 import (
    PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH,
    PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1,
    Phase7ReadinessAdjudicationError,
    adjudicate_ghv_current_okx_phase7_readiness_v1,
    adjudicate_phase7_adversarial_contract_review_v1,
    compute_reviewed_contract_paths_sha256_v1,
    execute_phase7_offline_reproof_pytest_v1,
    verify_current_baseline_checkout_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
    ACCEPTED_PRIVATE_GET_GO,
    ACCEPTED_WORK_PACKAGE_OWNER_GO,
    K1_SESSION_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
    DISPOSITION_SESSION_WALLCLOCK_EXCEEDED,
    DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK,
    DISPOSITION_STOP_BEFORE_NETWORK,
    GhvOkxProductiveReadOnlyValidationError,
    MAX_VALIDATION_GET_REQUESTS,
    Phase8CliOwnerAuthorizationV1,
    ProductiveOkxReadOnlyValidationSessionDeadlineV1,
    VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS,
    build_bounded_read_only_get_endpoint_v1,
    evaluate_phase8_k1_network_owner_authorization_v1,
    evaluate_phase8_pre_network_owner_authorization_v1,
    evaluate_productive_get_safety_gates_v1,
    run_bounded_productive_okx_read_only_validation_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    METHOD_GET,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    _sign_request_path_from_url,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_BASELINE_ORIGIN_MAIN_SHA = "adfa1efdec0e1ef1d288866ae444cb795c1d3e19"
SQUASH_SUCCESSOR_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
SHA_A_AFTER_REVIEW = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SHA_B_AFTER_SQUASH = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


@contextmanager
def _patch_review_baseline_is_ancestor(*, is_ancestor: bool = True) -> Iterator[None]:
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.git_is_ancestor_commit_v1",
        return_value=is_ancestor,
    ):
        yield


def _seed_adversarial_review_tree_v1(tmp_path: Path) -> dict:
    manifest_src = REPO_ROOT / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    dest = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review_rel = str(manifest["review_evidence_relpath"])
    (tmp_path / review_rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / review_rel).write_bytes((REPO_ROOT / review_rel).read_bytes())
    for rel in manifest["reviewed_contract_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())
    return manifest


def _origin_main() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return str(proc.stdout or "").strip().lower()


def _head_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return str(proc.stdout or "").strip().lower()


def _declared_origin_main_sha_v1() -> str:
    """Runtime declared SHA must track live origin/main, not a frozen review baseline."""

    return _origin_main()


def _exact_baseline_checkout_v1() -> bool:
    origin = _origin_main()
    return _head_sha() == origin


def _explicit_cli_auth() -> Phase8CliOwnerAuthorizationV1:
    return Phase8CliOwnerAuthorizationV1(
        work_package_owner_go=ACCEPTED_WORK_PACKAGE_OWNER_GO,
        private_get_go=ACCEPTED_PRIVATE_GET_GO,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        k1_session_owner_go=K1_SESSION_OWNER_GO,
    )


def _gate_request(origin_sha: str) -> PostSubmitLifecycleReconciliationOrchestrationRequestV1:
    return PostSubmitLifecycleReconciliationOrchestrationRequestV1(
        mode=LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY,
        work_package_owner_go=ACCEPTED_WORK_PACKAGE_OWNER_GO,
        private_get_go=ACCEPTED_PRIVATE_GET_GO,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        origin_main_sha=origin_sha,
        decision_outcome="VALIDATION_ONLY",
        venue_plan_identity="validation-vp",
        envelope_identity="validation-env",
        submit_attempt_id="validation-submit",
        local_durable_state_version="validation-v1",
        pretrade_decision_id="ghv-okx-productive-get-validation-v1",
    )


def test_empty_query_endpoint_matches_k1_sign_request_path() -> None:
    endpoint = build_bounded_read_only_get_endpoint_v1(ENDPOINT_ACCOUNT_CONFIG, {})
    assert endpoint == ENDPOINT_ACCOUNT_CONFIG
    assert "?" not in endpoint
    signed = _sign_request_path_from_url(f"https://eea.okx.com{endpoint}")
    assert signed == ENDPOINT_ACCOUNT_CONFIG


def test_non_empty_query_endpoint_matches_k1_sign_request_path() -> None:
    endpoint = build_bounded_read_only_get_endpoint_v1(
        "/api/v5/trade/orders-pending",
        {"instType": "SWAP", "instId": "BTC-USDT-SWAP"},
    )
    assert endpoint.startswith("/api/v5/trade/orders-pending?")
    signed = _sign_request_path_from_url(f"https://eea.okx.com{endpoint}")
    assert signed == endpoint


def test_evaluate_safety_gates_has_no_hardcoded_pass_booleans_in_signature() -> None:
    import inspect

    sig = inspect.signature(evaluate_productive_get_safety_gates_v1)
    assert "offline_reproof_pass" not in sig.parameters
    assert "adversarial_review_pass" not in sig.parameters


def test_stale_declared_origin_main_fails_closed() -> None:
    result = adjudicate_ghv_current_okx_phase7_readiness_v1(
        repo_root=REPO_ROOT,
        declared_origin_main_sha="0" * 40,
    )
    assert result.offline_reproof == "FAIL"
    assert result.adversarial_review == "FAIL"


def test_adversarial_review_fails_on_stale_contract_hash(tmp_path: Path) -> None:
    manifest_src = REPO_ROOT / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    manifest["reviewed_contract_paths_sha256"] = "0" * 64
    dest = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest), encoding="utf-8")
    review_doc = REPO_ROOT / str(manifest["review_evidence_relpath"])
    (tmp_path / str(manifest["review_evidence_relpath"])).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / str(manifest["review_evidence_relpath"])).write_bytes(review_doc.read_bytes())
    for rel in manifest["reviewed_contract_paths"]:
        if rel == PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH:
            continue
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())

    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert "STALE" in detail or "TAMPERED" in detail


def test_missing_test_owner_fails_offline_reproof(tmp_path: Path) -> None:
    status, detail = execute_phase7_offline_reproof_pytest_v1(repo_root=tmp_path)
    assert status == "FAIL"
    assert detail.startswith("MISSING_TEST_OWNER:")


def test_pytest_fail_fail_closed() -> None:
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="fail"),
    ):
        status, detail = execute_phase7_offline_reproof_pytest_v1(repo_root=REPO_ROOT)
    assert status == "FAIL"
    assert "PYTEST_EXIT_1" in detail


def test_open_defects_fail_adversarial_review(tmp_path: Path) -> None:
    manifest_src = REPO_ROOT / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    manifest["open_defects"] = ["DEFECT-1"]
    dest = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / str(manifest["review_evidence_relpath"])).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / str(manifest["review_evidence_relpath"])).write_bytes(
        (REPO_ROOT / str(manifest["review_evidence_relpath"])).read_bytes()
    )
    for rel in manifest["reviewed_contract_paths"]:
        if rel == PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH:
            continue
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())

    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "OPEN_DEFECTS_PRESENT"


def test_evaluate_gates_stop_before_network_when_reproof_fails() -> None:
    origin = _origin_main()
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.execute_phase7_offline_reproof_pytest_v1",
        return_value=("FAIL", "PYTEST_MOCK_FAIL"),
    ):
        gates = evaluate_productive_get_safety_gates_v1(
            orchestration_request=_gate_request(origin),
            repo_root=REPO_ROOT,
        )
    assert gates.overall == "FAIL"
    assert gates.offline_reproof == "FAIL"


@pytest.mark.skipif(
    not _exact_baseline_checkout_v1(),
    reason="HEAD == origin/main == expected SHA required for live manifest bind",
)
def test_manifest_contract_hash_matches_repo() -> None:
    manifest = json.loads(
        (REPO_ROOT / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH).read_text(encoding="utf-8")
    )
    rel_paths = tuple(str(p) for p in manifest["reviewed_contract_paths"])
    actual = compute_reviewed_contract_paths_sha256_v1(REPO_ROOT, rel_paths)
    assert actual == str(manifest["reviewed_contract_paths_sha256"]).lower()


@pytest.mark.skipif(
    not _exact_baseline_checkout_v1(),
    reason="HEAD == origin/main == expected SHA required",
)
def test_phase7_integration_with_mocked_pytest_pass() -> None:
    origin = _origin_main()
    verify_current_baseline_checkout_v1(
        repo_root=REPO_ROOT,
        declared_origin_main_sha=origin,
    )
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.execute_phase7_offline_reproof_pytest_v1",
        return_value=("PASS", "PYTEST_MOCK_OK"),
    ):
        gates = evaluate_productive_get_safety_gates_v1(
            orchestration_request=_gate_request(origin),
            repo_root=REPO_ROOT,
        )
    assert gates.offline_reproof == "PASS"
    assert gates.adversarial_review == "PASS"
    assert gates.overall == "PASS"


def test_offline_reproof_test_owner_files_exist() -> None:
    for rel in PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1:
        assert (REPO_ROOT / rel).is_file(), rel


def test_post_squash_successor_sha_accepted_when_ancestor_and_contracts_unchanged(
    tmp_path: Path,
) -> None:
    _seed_adversarial_review_tree_v1(tmp_path)
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.git_is_ancestor_commit_v1",
        return_value=True,
    ):
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=SQUASH_SUCCESSOR_SHA,
        )
    assert status == "PASS"
    assert detail.startswith("MANIFEST_OK")


def test_review_baseline_not_ancestor_fails_closed(tmp_path: Path) -> None:
    _seed_adversarial_review_tree_v1(tmp_path)
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.git_is_ancestor_commit_v1",
        return_value=False,
    ):
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "REVIEW_BASELINE_NOT_ANCESTOR_OF_CURRENT_ORIGIN_MAIN"


def test_contract_byte_change_fails_closed(tmp_path: Path) -> None:
    manifest = _seed_adversarial_review_tree_v1(tmp_path)
    tamper = tmp_path / manifest["reviewed_contract_paths"][2]
    tamper.write_text(tamper.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "REVIEWED_CONTRACT_STALE_OR_TAMPERED"


def test_manifest_metadata_tamper_fails_provenance_anchor(tmp_path: Path) -> None:
    manifest = _seed_adversarial_review_tree_v1(tmp_path)
    manifest_path = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    loaded["review_baseline_origin_main_sha"] = "c" * 40
    manifest_path.write_text(json.dumps(loaded, indent=2) + "\n", encoding="utf-8")
    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail in {
        "MANIFEST_PROVENANCE_BODY_MISMATCH_REVIEW_ANCHOR",
        "REVIEWED_CONTRACT_STALE_OR_TAMPERED",
    }


def test_review_document_change_fails_closed(tmp_path: Path) -> None:
    manifest = _seed_adversarial_review_tree_v1(tmp_path)
    review_path = tmp_path / str(manifest["review_evidence_relpath"])
    review_path.write_text(review_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "REVIEW_EVIDENCE_STALE_OR_TAMPERED"


def test_review_scope_incomplete_fails_closed(tmp_path: Path) -> None:
    manifest = _seed_adversarial_review_tree_v1(tmp_path)
    manifest_path = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    loaded["reviewed_contract_paths"] = [
        p
        for p in loaded["reviewed_contract_paths"]
        if not p.endswith("ghv_current_okx_phase7_readiness_adjudication_v1.py")
    ]
    manifest_path.write_text(json.dumps(loaded, indent=2) + "\n", encoding="utf-8")
    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "REVIEW_SCOPE_INCOMPLETE"


def test_missing_provenance_anchor_in_review_doc_fails_closed(tmp_path: Path) -> None:
    manifest = _seed_adversarial_review_tree_v1(tmp_path)
    review_path = tmp_path / str(manifest["review_evidence_relpath"])
    review_path.write_text(
        review_path.read_text(encoding="utf-8").replace(
            "MANIFEST_PROVENANCE_BODY_SHA256=", "REMOVED="
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1 import (
        sha256_file_v1,
    )

    loaded["review_evidence_sha256"] = sha256_file_v1(review_path)
    manifest_path.write_text(json.dumps(loaded, indent=2) + "\n", encoding="utf-8")
    with _patch_review_baseline_is_ancestor():
        status, detail = adjudicate_phase7_adversarial_contract_review_v1(
            repo_root=tmp_path,
            declared_origin_main_sha=_declared_origin_main_sha_v1(),
        )
    assert status == "FAIL"
    assert detail == "MANIFEST_PROVENANCE_ANCHOR_MISSING_IN_REVIEW_DOC"


def test_head_drift_fails_runtime_baseline_verify() -> None:
    declared = _declared_origin_main_sha_v1()
    drift_head = "dddddddddddddddddddddddddddddddddddddddd"
    assert drift_head != declared
    with (
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_origin_main_sha_v1",
            return_value=declared,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_head_sha_v1",
            return_value=drift_head,
        ),
    ):
        with pytest.raises(Phase7ReadinessAdjudicationError, match="HEAD_NOT_AT_DECLARED"):
            verify_current_baseline_checkout_v1(
                repo_root=REPO_ROOT,
                declared_origin_main_sha=declared,
            )


def test_origin_main_advances_a_to_b_head_drift_is_not_origin_drift() -> None:
    """After squash, declared must track successor B; HEAD drift must not masquerade as origin drift."""

    drift_head = "cccccccccccccccccccccccccccccccccccccccc"
    with (
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_origin_main_sha_v1",
            return_value=SHA_B_AFTER_SQUASH,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_head_sha_v1",
            return_value=drift_head,
        ),
    ):
        with pytest.raises(Phase7ReadinessAdjudicationError, match="HEAD_NOT_AT_DECLARED"):
            verify_current_baseline_checkout_v1(
                repo_root=REPO_ROOT,
                declared_origin_main_sha=SHA_B_AFTER_SQUASH,
            )

    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_origin_main_sha_v1",
        return_value=SHA_B_AFTER_SQUASH,
    ):
        with pytest.raises(Phase7ReadinessAdjudicationError, match="ORIGIN_MAIN_SHA_DRIFT"):
            verify_current_baseline_checkout_v1(
                repo_root=REPO_ROOT,
                declared_origin_main_sha=SHA_A_AFTER_REVIEW,
            )


def test_review_baseline_sha_is_manifest_not_runtime_origin() -> None:
    manifest = json.loads(
        (REPO_ROOT / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH).read_text(encoding="utf-8")
    )
    assert (
        str(manifest["review_baseline_origin_main_sha"]).lower() == REVIEW_BASELINE_ORIGIN_MAIN_SHA
    )


@pytest.mark.skipif(
    not _exact_baseline_checkout_v1(),
    reason="HEAD == origin/main == expected SHA required for runner integration",
)
def test_runner_skip_network_disposition(capsys: pytest.CaptureFixture[str]) -> None:
    runner_path = (
        REPO_ROOT
        / "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"
    )
    spec = importlib.util.spec_from_file_location("ghv_okx_runner_validation_v1", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    argv = [
        "run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
        "--skip-network",
        "--origin-main-sha",
        _declared_origin_main_sha_v1(),
        "--work-package-owner-go",
        ACCEPTED_WORK_PACKAGE_OWNER_GO,
        "--private-get-go",
        ACCEPTED_PRIVATE_GET_GO,
        "--offline-implementation-go",
        ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
    ]
    with (
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.execute_phase7_offline_reproof_pytest_v1",
            return_value=("PASS", "PYTEST_MOCK_OK"),
        ),
        patch.object(sys, "argv", argv),
    ):
        spec.loader.exec_module(module)
        exit_code = module._main()
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["DISPOSITION"] == "PHASE_7_PASS_NETWORK_SKIPPED"
    assert payload["PHASE_7_SAFETY_GATES"]["overall"] == "PASS"
    assert payload["KEYCHAIN_ACCESS_COUNT"] == 0
    assert payload["PRIVATE_GET_COUNT"] == 0


def test_no_owner_go_params_stop_before_network() -> None:
    decision = evaluate_phase8_pre_network_owner_authorization_v1(
        Phase8CliOwnerAuthorizationV1(None, None, None, None)
    )
    assert decision.disposition == DISPOSITION_STOP_BEFORE_NETWORK
    assert "OWNER_GO_REQUIRED" in decision.detail


def test_missing_private_get_go_stop_before_network() -> None:
    auth = Phase8CliOwnerAuthorizationV1(
        work_package_owner_go=ACCEPTED_WORK_PACKAGE_OWNER_GO,
        private_get_go=None,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        k1_session_owner_go=None,
    )
    decision = evaluate_phase8_pre_network_owner_authorization_v1(auth)
    assert decision.disposition == DISPOSITION_STOP_BEFORE_NETWORK


def test_missing_k1_go_stop_before_keychain() -> None:
    auth = Phase8CliOwnerAuthorizationV1(
        work_package_owner_go=ACCEPTED_WORK_PACKAGE_OWNER_GO,
        private_get_go=ACCEPTED_PRIVATE_GET_GO,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        k1_session_owner_go=None,
    )
    decision = evaluate_phase8_k1_network_owner_authorization_v1(auth)
    assert decision.disposition == DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK


def test_invalid_owner_token_fail_closed() -> None:
    auth = Phase8CliOwnerAuthorizationV1(
        work_package_owner_go="DENIED",
        private_get_go=ACCEPTED_PRIVATE_GET_GO,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        k1_session_owner_go=K1_SESSION_OWNER_GO,
    )
    assert (
        evaluate_phase8_pre_network_owner_authorization_v1(auth).disposition
        == DISPOSITION_STOP_BEFORE_NETWORK
    )
    assert (
        evaluate_phase8_k1_network_owner_authorization_v1(auth).disposition
        == DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK
    )


def test_explicit_valid_owner_authorization_ok() -> None:
    decision = evaluate_phase8_k1_network_owner_authorization_v1(_explicit_cli_auth())
    assert decision.disposition == "OWNER_AUTHORIZATION_OK"


def test_session_deadline_exceeded_before_use() -> None:
    deadline = ProductiveOkxReadOnlyValidationSessionDeadlineV1(
        started_at_monotonic=0.0,
        budget_seconds=0.001,
    )
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.time.monotonic",
        return_value=10.0,
    ):
        with pytest.raises(GhvOkxProductiveReadOnlyValidationError, match="SESSION_WALLCLOCK"):
            deadline.assert_within_budget_v1()


class _MockProductiveGetTransport:
    transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET

    def __init__(self) -> None:
        self.calls = 0
        self.request_count = 0
        self.methods_used: list[str] = []

    def get(self, **kwargs: object) -> FreshPretradeGetTransportResultV1:
        self.calls += 1
        self.request_count += 1
        self.methods_used.append(METHOD_GET)
        deadline = kwargs.get("session_deadline")
        if deadline is not None:
            deadline.assert_within_budget_v1()
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=str(kwargs.get("endpoint") or ""),
            http_status=200,
            payload={"code": "0", "data": [{}]},
            auth_header_sent=True,
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256="abc",
            data_safety_source_kind="REAL",
        )


def test_two_gets_within_budget_unchanged_with_deadline() -> None:
    transport = _MockProductiveGetTransport()
    deadline = ProductiveOkxReadOnlyValidationSessionDeadlineV1.start(
        budget_seconds=VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS
    )
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1._demo_from_config_payload",
        return_value=False,
    ):
        result = run_bounded_productive_okx_read_only_validation_session_v1(
            transport=transport,
            pretrade_decision_id="test",
            instrument_id="BTC-USDT-SWAP",
            session_deadline=deadline,
        )
    assert result.get_request_count == 2
    assert transport.calls == 2
    assert result.disposition == "VALIDATION_PASS"


def test_deadline_before_get_blocks_http() -> None:
    transport = _MockProductiveGetTransport()
    deadline = ProductiveOkxReadOnlyValidationSessionDeadlineV1(
        started_at_monotonic=0.0,
        budget_seconds=1.0,
    )
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.time.monotonic",
        return_value=5.0,
    ):
        with pytest.raises(GhvOkxProductiveReadOnlyValidationError, match="SESSION_WALLCLOCK"):
            run_bounded_productive_okx_read_only_validation_session_v1(
                transport=transport,
                pretrade_decision_id="test",
                instrument_id="BTC-USDT-SWAP",
                session_deadline=deadline,
            )
    assert transport.calls == 0


def test_request_budget_exceeded_fail_closed() -> None:
    transport = _MockProductiveGetTransport()
    transport.request_count = MAX_VALIDATION_GET_REQUESTS
    with pytest.raises(GhvOkxProductiveReadOnlyValidationError, match="MAX_VALIDATION_GET_BUDGET"):
        run_bounded_productive_okx_read_only_validation_session_v1(
            transport=transport,
            pretrade_decision_id="test",
            instrument_id="BTC-USDT-SWAP",
        )


def test_demo_mode_detected_fail_closed() -> None:
    transport = _MockProductiveGetTransport()

    def _get(**kwargs: object) -> FreshPretradeGetTransportResultV1:
        transport.request_count += 1
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=str(kwargs.get("endpoint") or ""),
            http_status=200,
            payload={"code": "0", "data": [{"simulatedTrading": True}]},
            auth_header_sent=True,
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256="abc",
            data_safety_source_kind="REAL",
        )

    transport.get = _get  # type: ignore[method-assign]
    with pytest.raises(GhvOkxProductiveReadOnlyValidationError, match="DEMO_MODE_DETECTED"):
        run_bounded_productive_okx_read_only_validation_session_v1(
            transport=transport,
            pretrade_decision_id="test",
            instrument_id="BTC-USDT-SWAP",
        )


def test_runner_no_owner_go_stop_before_network(capsys: pytest.CaptureFixture[str]) -> None:
    runner_path = (
        REPO_ROOT
        / "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"
    )
    spec = importlib.util.spec_from_file_location("ghv_okx_runner_no_go_v1", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    with patch.object(
        sys,
        "argv",
        ["run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"],
    ):
        spec.loader.exec_module(module)
        exit_code = module._main()
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["DISPOSITION"] == DISPOSITION_STOP_BEFORE_NETWORK


def test_runner_network_without_k1_go_stop_before_keychain(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner_path = (
        REPO_ROOT
        / "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"
    )
    spec = importlib.util.spec_from_file_location("ghv_okx_runner_no_k1_v1", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    argv = [
        "run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
        "--origin-main-sha",
        _declared_origin_main_sha_v1(),
        "--work-package-owner-go",
        ACCEPTED_WORK_PACKAGE_OWNER_GO,
        "--private-get-go",
        ACCEPTED_PRIVATE_GET_GO,
        "--offline-implementation-go",
        ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
    ]
    with (
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.execute_phase7_offline_reproof_pytest_v1",
            return_value=("PASS", "PYTEST_MOCK_OK"),
        ),
        patch.object(sys, "argv", argv),
    ):
        spec.loader.exec_module(module)
        exit_code = module._main()
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["DISPOSITION"] == DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK


def test_validation_session_wallclock_derived_from_existing_budgets() -> None:
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        CONNECT_TIMEOUT_SECONDS,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
        VALIDATION_TIMEOUT_SECONDS,
    )

    assert VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS == MAX_VALIDATION_GET_REQUESTS * (
        CONNECT_TIMEOUT_SECONDS + VALIDATION_TIMEOUT_SECONDS
    )


def _load_runner_module_v1():
    runner_path = (
        REPO_ROOT
        / "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"
    )
    spec = importlib.util.spec_from_file_location("ghv_okx_runner_closure_v1", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _network_runner_argv_v1() -> list[str]:
    return [
        "run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
        "--origin-main-sha",
        _declared_origin_main_sha_v1(),
        "--work-package-owner-go",
        ACCEPTED_WORK_PACKAGE_OWNER_GO,
        "--private-get-go",
        ACCEPTED_PRIVATE_GET_GO,
        "--offline-implementation-go",
        ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        "--k1-session-owner-go",
        K1_SESSION_OWNER_GO,
    ]


def _phase7_pass_patches():
    return patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.execute_phase7_offline_reproof_pytest_v1",
        return_value=("PASS", "PYTEST_MOCK_OK"),
    )


def test_h_http_timeout_during_get_single_attempt_no_retry() -> None:
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )

    handle = MagicMock()
    transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle, max_request_count=8)
    open_calls = {"n": 0}

    def _fake_open(*_args, **_kwargs):
        open_calls["n"] += 1
        raise TimeoutError

    with (
        patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_k1_okx_venue_auth_headers_v1",
            return_value={"Accept": "application/json", "User-Agent": "test"},
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener",
        ) as build_opener_mock,
    ):
        opener = MagicMock()
        opener.open.side_effect = _fake_open
        build_opener_mock.return_value.open = opener.open
        build_opener_mock.return_value = opener
        result = transport.get(
            endpoint=ENDPOINT_ACCOUNT_CONFIG,
            auth_required=True,
            pretrade_decision_id="test-h",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
    assert open_calls["n"] == 1
    assert transport.request_count == 1
    assert result.error_class == "TIMEOUT"
    assert result.get_performed is False


def test_f_deadline_before_k1_keychain_and_http_zero(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_runner_module_v1()
    k1_open = MagicMock()
    transport_ctor = MagicMock()

    def _always_expired(_self) -> float:
        return -1.0

    with (
        _phase7_pass_patches(),
        patch.object(
            ProductiveOkxReadOnlyValidationSessionDeadlineV1,
            "remaining_seconds",
            _always_expired,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.open_current_productive_k1_opaque_signing_handle_session_v1",
            k1_open,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.FullCoreProductiveReadOnlyGetTransportV1",
            transport_ctor,
        ),
        patch.object(sys, "argv", _network_runner_argv_v1()),
    ):
        exit_code = module._main()
    assert exit_code == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload["DISPOSITION"] == DISPOSITION_SESSION_WALLCLOCK_EXCEEDED
    k1_open.assert_not_called()
    transport_ctor.assert_not_called()


def test_i_slow_k1_expires_before_productive_get(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_runner_module_v1()
    k1_entered: list[int] = []
    bounded_calls: list[int] = []

    @contextmanager
    def _slow_k1_session(*_args, **_kwargs) -> Iterator[MagicMock]:
        k1_entered.append(1)
        yield MagicMock(signing_handle=MagicMock())

    def _remaining_after_k1_enter(_self) -> float:
        if k1_entered:
            return -1.0
        return 100.0

    def _spy_bounded(*_args, **_kwargs):
        bounded_calls.append(1)
        raise AssertionError("productive GET session must not run")

    with (
        _phase7_pass_patches(),
        patch.object(
            ProductiveOkxReadOnlyValidationSessionDeadlineV1,
            "remaining_seconds",
            _remaining_after_k1_enter,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.resolve_macos_security_framework_k1_lookup_backend_v1",
            return_value=MagicMock(),
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.open_current_productive_k1_opaque_signing_handle_session_v1",
            _slow_k1_session,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.run_bounded_productive_okx_read_only_validation_session_v1",
            _spy_bounded,
        ),
        patch.object(sys, "argv", _network_runner_argv_v1()),
    ):
        exit_code = module._main()
    assert exit_code == 4
    assert len(k1_entered) == 1
    assert bounded_calls == []
    payload = json.loads(capsys.readouterr().out)
    assert payload["DISPOSITION"] == DISPOSITION_SESSION_WALLCLOCK_EXCEEDED
    assert "SESSION_DEADLINE" in payload


def test_o_timeout_evidence_complete_without_secrets(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_runner_module_v1()

    def _always_expired(_self) -> float:
        return -1.0

    with (
        _phase7_pass_patches(),
        patch.object(
            ProductiveOkxReadOnlyValidationSessionDeadlineV1,
            "remaining_seconds",
            _always_expired,
        ),
        patch.object(sys, "argv", _network_runner_argv_v1()),
    ):
        module._main()
    raw = capsys.readouterr().out
    payload = json.loads(raw)
    deadline = payload["SESSION_DEADLINE"]
    assert isinstance(deadline, dict)
    for key in (
        "budget_seconds",
        "elapsed_seconds",
        "remaining_seconds",
        "hard_timeout_guarantee_scope",
    ):
        assert key in deadline
    lowered = raw.lower()
    for forbidden in (
        '"apikey":',
        '"secretkey":',
        '"passphrase":',
        "ok-access-passphrase",
        "ok-access-sign",
        "ok-access-key",
    ):
        assert forbidden not in lowered


def test_n_single_session_attempt_no_auto_restart(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_runner_module_v1()
    bounded_calls: list[int] = []

    @contextmanager
    def _instant_k1(*_args, **_kwargs) -> Iterator[MagicMock]:
        yield MagicMock(signing_handle=MagicMock())

    def _bounded_once(*_args, **_kwargs):
        bounded_calls.append(1)
        from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
            ProductiveOkxReadOnlyValidationSessionResultV1,
        )

        return ProductiveOkxReadOnlyValidationSessionResultV1(
            disposition="VALIDATION_PASS",
            get_request_count=2,
            authorized_host="eea.okx.com",
            account_config_http_status=200,
            account_config_api_code="0",
            orders_pending_http_status=200,
            orders_pending_api_code="0",
            environment_label="PRODUCTION_EEA_OKX",
            demo_mode_detected=False,
            provider_compatible=True,
            transport_class="FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
            methods_used=("GET", "GET"),
            surfaces_summary=(),
        )

    with (
        _phase7_pass_patches(),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.resolve_macos_security_framework_k1_lookup_backend_v1",
            return_value=MagicMock(),
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.open_current_productive_k1_opaque_signing_handle_session_v1",
            _instant_k1,
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.run_bounded_productive_okx_read_only_validation_session_v1",
            _bounded_once,
        ),
        patch.object(sys, "argv", _network_runner_argv_v1()),
    ):
        exit_code = module._main()
    assert exit_code == 0
    assert len(bounded_calls) == 1
    assert "while True" not in Path(
        REPO_ROOT
        / "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py"
    ).read_text(encoding="utf-8")
