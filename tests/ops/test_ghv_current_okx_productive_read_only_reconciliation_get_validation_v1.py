"""Phase-7/8 boundary and evidence-bound readiness tests (offline only)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

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
from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
    build_bounded_read_only_get_endpoint_v1,
    evaluate_productive_get_safety_gates_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    _sign_request_path_from_url,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ORIGIN_MAIN = "adfa1efdec0e1ef1d288866ae444cb795c1d3e19"
SQUASH_SUCCESSOR_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


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


def _exact_baseline_checkout_v1() -> bool:
    origin = _origin_main()
    return origin == EXPECTED_ORIGIN_MAIN and _head_sha() == origin


def _gate_request(origin_sha: str) -> PostSubmitLifecycleReconciliationOrchestrationRequestV1:
    return PostSubmitLifecycleReconciliationOrchestrationRequestV1(
        mode=LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY,
        work_package_owner_go="GRANTED",
        private_get_go="GRANTED_SCOPED_READ_ONLY",
        offline_implementation_go="GRANTED",
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
            declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
        )
    assert status == "FAIL"
    assert detail == "MANIFEST_PROVENANCE_ANCHOR_MISSING_IN_REVIEW_DOC"


def test_head_drift_fails_runtime_baseline_verify() -> None:
    with patch(
        "src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1.resolve_git_head_sha_v1",
        return_value="d" * 40,
    ):
        with pytest.raises(Phase7ReadinessAdjudicationError, match="HEAD_NOT_AT_DECLARED"):
            verify_current_baseline_checkout_v1(
                repo_root=REPO_ROOT,
                declared_origin_main_sha=EXPECTED_ORIGIN_MAIN,
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
        EXPECTED_ORIGIN_MAIN,
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
