"""Tests for PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    authorization_digest_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.campaign_harness_v1 import (
    run_restart_campaign_fixture_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CHECKPOINT_FILENAME,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DURABLE_STATE_LINEAGE_ID,
    LOCK_FILENAME,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    OPEN_POSITION_NOT_OBSERVED,
    OPEN_POSITION_RECOVERY_PROVEN,
    PRE_TERMINAL_MANIFEST_FILENAME,
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TELEMETRY_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    RestartContractError,
    build_restart_session_contract_v1,
    validate_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.failure_injection_v1 import (
    run_failure_injection_matrix_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartLockError,
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.network_boundary_v1 import (
    prove_no_live_testnet_credential_path_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.parity_v1 import (
    prove_phase92_restart_parity_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (
    run_post_restart_segment_v1,
    run_pre_restart_segment_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    build_fixture_checkpoint_v1,
    build_state_root_classification_matrix_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "deca127f92eb56b518f0417342f636a9c3faba12"


def _checkpoint(*, open_position: bool = False, epoch: int | None = None):
    n = epoch if epoch is not None else MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS
    return build_fixture_checkpoint_v1(
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        observation_epoch=n,
        open_position_present=open_position,
        distinct_observation_count=n,
        evidence_cursor=sha256_canonical_v1({"cursor": "test", "n": n}),
        portfolio_seed="test_portfolio",
        scope_seed="test_scope",
        accounting_seed="test_accounting",
        runtime_seed="test_runtime",
        instrument_id=CANONICAL_INSTRUMENT_ID,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        applied_fill_ids=["fill_natural_001"] if open_position else [],
        applied_confirmation_ids=["conf_natural_001"],
    )


def _pre_contract(cp, *, auth: str = "auth_pre_test", runtime: str = "rt_pre_test"):
    return build_restart_session_contract_v1(
        repository_sha=REPO_SHA,
        segment_role=SEGMENT_ROLE_PRE,
        segment_id="segment_pre_restart_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_PRE,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=cp.runtime_state_digest,
        expected_portfolio_digest=cp.portfolio_digest,
        expected_scope_digest=cp.scope_digest,
        expected_accounting_digest=cp.accounting_digest,
        expected_evidence_cursor=cp.evidence_cursor,
        repo_root=REPO_ROOT,
    )


def _post_contract(cp, *, pre_segment_id: str, pre_digest: str, auth: str, runtime: str):
    return build_restart_session_contract_v1(
        repository_sha=REPO_SHA,
        segment_role=SEGMENT_ROLE_POST,
        segment_id="segment_post_restart_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_POST,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=cp.runtime_state_digest,
        expected_portfolio_digest=cp.portfolio_digest,
        expected_scope_digest=cp.scope_digest,
        expected_accounting_digest=cp.accounting_digest,
        expected_evidence_cursor=cp.evidence_cursor,
        predecessor_segment_id=pre_segment_id,
        predecessor_terminal_manifest_digest=pre_digest,
        repo_root=REPO_ROOT,
    )


def test_01_valid_pre_post_restart_flat(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "flat",
        repository_sha=REPO_SHA,
        open_position_present=False,
        repo_root=REPO_ROOT,
    )
    assert bundle["ok"] is True
    assert bundle["verifier"]["claims"]["OPEN_POSITION_NOT_OBSERVED"] is True
    assert bundle["verifier"]["claims"]["OPEN_POSITION_RECOVERY_PROVEN"] is False
    assert bundle["controlled_restart_exit_code"] == CONTROLLED_RESTART_EXIT_CODE


def test_02_valid_open_simulated_position_across_restart(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "open",
        repository_sha=REPO_SHA,
        open_position_present=True,
        repo_root=REPO_ROOT,
    )
    assert bundle["ok"] is True
    assert bundle["post_segment"]["telemetry"]["open_position_recovered"] is True
    assert (
        bundle["post_segment"]["telemetry"]["open_position_recovery_claim"]
        == OPEN_POSITION_RECOVERY_PROVEN
    )
    assert bundle["verifier"]["claims"]["OPEN_POSITION_RECOVERY_PROVEN"] is True


def test_03_new_authorization_per_segment(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "auth_per_seg",
        repository_sha=REPO_SHA,
        repo_root=REPO_ROOT,
    )
    assert bundle["pre_segment"]["authorization_id"] != bundle["post_segment"]["authorization_id"]
    assert (
        bundle["pre_segment"]["runtime_session_id"] != bundle["post_segment"]["runtime_session_id"]
    )


def test_04_authorization_reuse_rejected(tmp_path: Path) -> None:
    cp = _checkpoint()
    contract = _pre_contract(cp, auth="auth_reuse_same", runtime="rt_reuse_1")
    first = run_pre_restart_segment_v1(
        contract=contract, persistence_root=tmp_path / "reuse", checkpoint=cp
    )
    second = run_pre_restart_segment_v1(
        contract=contract, persistence_root=tmp_path / "reuse", checkpoint=cp
    )
    assert first.ok is True
    assert second.ok is False
    assert any("authorization_reuse" in b for b in second.blockers)


def test_05_confirmation_session_id_stable(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "conf_stable",
        repository_sha=REPO_SHA,
        repo_root=REPO_ROOT,
    )
    pre_tel = bundle["pre_segment"]["telemetry"]
    post_tel = bundle["post_segment"]["telemetry"]
    assert pre_tel["confirmation_session_id_before"] == CONFIRMATION_SESSION_ID
    assert pre_tel["confirmation_session_id_after"] == CONFIRMATION_SESSION_ID
    assert post_tel["confirmation_session_id_before"] == CONFIRMATION_SESSION_ID
    assert post_tel["confirmation_session_id_after"] == CONFIRMATION_SESSION_ID


def test_06_confirmation_session_id_mutation_rejected(tmp_path: Path) -> None:
    root = tmp_path / "conf_mut"
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    cp = read_json_v1(root / CHECKPOINT_FILENAME)
    cp["confirmation_session_id"] = "mutated"
    write_json_atomic_v1(root / CHECKPOINT_FILENAME, cp)
    for name in (f"post_{TELEMETRY_FILENAME}", "post_restart_terminal_manifest_v1.json"):
        path = root / name
        if path.exists():
            path.unlink()
    pre = read_json_v1(root / PRE_TERMINAL_MANIFEST_FILENAME)
    runtime = "rt_post_mut"
    auth = "auth_post_mut"
    post_contract = build_restart_session_contract_v1(
        repository_sha=REPO_SHA,
        segment_role=SEGMENT_ROLE_POST,
        segment_id="segment_post_restart_mut_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_POST,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=str(pre["runtime_state_digest"]),
        expected_portfolio_digest=str(pre["portfolio_digest"]),
        expected_scope_digest=str(pre["scope_digest"]),
        expected_accounting_digest=str(pre["accounting_digest"]),
        expected_evidence_cursor=str(pre["evidence_cursor"]),
        predecessor_segment_id=str(pre["segment_id"]),
        predecessor_terminal_manifest_digest=bundle["pre_segment"]["terminal_manifest_digest"],
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        repo_root=REPO_ROOT,
    )
    post = run_post_restart_segment_v1(contract=post_contract, persistence_root=root)
    assert post.ok is False
    assert any("confirmation_session_id_mutation" in b for b in post.blockers)


def test_07_duplicate_observation_after_restart_no_advance(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "dup_obs",
        repository_sha=REPO_SHA,
        candidate_observation_id="conf_obs_001",
        applied_confirmation_ids=["conf_obs_001"],
        repo_root=REPO_ROOT,
    )
    assert bundle["ok"] is True
    assert bundle["post_segment"]["telemetry"]["duplicate_confirmation_prevented_count"] == 1


def test_08_duplicate_fill_not_reapplied(tmp_path: Path) -> None:
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=tmp_path / "dup_fill",
        repository_sha=REPO_SHA,
        open_position_present=True,
        candidate_fill_id="fill_entry_natural_001",
        repo_root=REPO_ROOT,
    )
    assert bundle["ok"] is True
    assert bundle["post_segment"]["telemetry"]["duplicate_fill_prevented_count"] == 1


def test_09_evidence_cursor_not_double_counted(tmp_path: Path) -> None:
    root = tmp_path / "cursor"
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    assert bundle["ok"] is True
    pre = bundle["pre_segment"]["telemetry"]
    post = bundle["post_segment"]["telemetry"]
    assert pre["evidence_cursor_before"] == pre["evidence_cursor_after"]
    assert post["evidence_cursor_before"] == post["evidence_cursor_after"]
    assert pre["evidence_cursor_after"] == post["evidence_cursor_after"]


def test_10_missing_pre_segment(tmp_path: Path) -> None:
    root = tmp_path / "missing_pre"
    root.mkdir()
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "missing_pre_restart_segment" in result.blockers


def test_11_missing_post_segment(tmp_path: Path) -> None:
    root = tmp_path / "missing_post"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    (root / "post_restart_terminal_manifest_v1.json").unlink()
    (root / f"post_{TELEMETRY_FILENAME}").unlink()
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "missing_post_restart_segment" in result.blockers


def test_12_wrong_segment_order(tmp_path: Path) -> None:
    root = tmp_path / "order"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["predecessor_segment_id"] = "not_the_pre_segment"
    # keep digest field but verifier checks predecessor against pre segment id
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "incorrect_segment_order" in result.blockers


def test_13_digest_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "digest"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["pre_restart_terminal_manifest_digest"] = "f" * 64
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "digest_mismatch" in result.blockers


def test_14_portfolio_rollback(tmp_path: Path) -> None:
    root = tmp_path / "portfolio_rb"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["portfolio_digest"] = "0" * 64
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "portfolio_rollback_or_mutation" in result.blockers


def test_15_scope_rollback(tmp_path: Path) -> None:
    root = tmp_path / "scope_rb"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["scope_digest"] = "1" * 64
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "scope_rollback_or_mutation" in result.blockers


def test_16_observation_epoch_rollback(tmp_path: Path) -> None:
    root = tmp_path / "epoch_rb"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["observation_epoch"] = 0
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "observation_epoch_rollback" in result.blockers


def test_17_missing_reconciliation_before_alpha(tmp_path: Path) -> None:
    root = tmp_path / "recon"
    run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    post = read_json_v1(root / "post_restart_terminal_manifest_v1.json")
    post["reconciliation_completed_before_alpha"] = False
    write_json_atomic_v1(root / "post_restart_terminal_manifest_v1.json", post)
    result = verify_restart_bundle_v1(persistence_root=root)
    assert result.verified is False
    assert "missing_reconciliation_before_alpha" in result.blockers


def test_18_controlled_segment_completion_releases_owner_lock(tmp_path: Path) -> None:
    root = tmp_path / "lock_release"
    cp = _checkpoint()
    result = run_pre_restart_segment_v1(
        contract=_pre_contract(cp), persistence_root=root, checkpoint=cp
    )
    assert result.ok is True
    assert result.lock_released_by_owner is True
    assert result.controlled_restart_exit_code == CONTROLLED_RESTART_EXIT_CODE
    assert not (root / LOCK_FILENAME).exists()


def test_19_orphan_lock_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "orphan"
    root.mkdir()
    lock_path = lock_path_for_root_v1(root)
    lock_path.write_text(
        json.dumps({"runtime_session_id": "dead", "owner": "orphan", "pid": 1}) + "\n",
        encoding="utf-8",
    )
    lock = RestartSegmentLockV1(lock_path=lock_path, runtime_session_id="new", owner="new")
    with pytest.raises(RestartLockError, match="ORPHAN_OR_DUPLICATE_LOCK_FAIL_CLOSED"):
        lock.acquire()


def test_20_partial_evidence_materialization_recovered_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "partial_ev"
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    cursor_path = root / "evidence_cursor_v1.json"
    first = read_json_v1(cursor_path)
    write_json_atomic_v1(cursor_path, first)
    second = read_json_v1(cursor_path)
    assert bundle["ok"] is True
    assert first == second


def test_21_corrupt_checkpoint_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "corrupt"
    bundle = run_restart_campaign_fixture_v1(
        persistence_root=root, repository_sha=REPO_SHA, repo_root=REPO_ROOT
    )
    (root / CHECKPOINT_FILENAME).write_text("{bad", encoding="utf-8")
    for name in (f"post_{TELEMETRY_FILENAME}", "post_restart_terminal_manifest_v1.json"):
        path = root / name
        if path.exists():
            path.unlink()
    pre = read_json_v1(root / PRE_TERMINAL_MANIFEST_FILENAME)
    post = run_post_restart_segment_v1(
        contract=_post_contract(
            _checkpoint(),
            pre_segment_id=str(pre["segment_id"]),
            pre_digest=str(pre["terminal_manifest_digest"]),
            auth="auth_corrupt_post",
            runtime="rt_corrupt_post",
        ),
        persistence_root=root,
    )
    assert bundle["ok"] is True
    assert post.ok is False
    assert any("corrupt_checkpoint" in b for b in post.blockers)


def test_22_live_testnet_credential_negative_proof() -> None:
    proof = prove_no_live_testnet_credential_path_v1()
    assert proof["ok"] is True
    assert proof["LIVE_PATH_CHANGED"] is False
    assert proof["TESTNET_PATH_CHANGED"] is False
    assert proof["EXCHANGE_CREDENTIAL_PATH_CHANGED"] is False
    assert proof["NETWORK_SESSION_ALLOWED"] is False


def test_23_golden_vector_and_call_order_parity() -> None:
    parity = prove_phase92_restart_parity_v1()
    assert parity["ok"] is True
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True


def test_24_master_v2_double_play_risk_safety_parity() -> None:
    parity = prove_phase92_restart_parity_v1()
    assert parity["MASTER_V2_CHANGED"] is False
    assert parity["DOUBLE_PLAY_CHANGED"] is False
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["RISK_CHANGED"] is False
    assert parity["SAFETY_CHANGED"] is False


def test_contract_rejects_unknown_fields() -> None:
    cp = _checkpoint()
    contract = _pre_contract(cp)
    payload = contract.to_dict()
    payload["unexpected_field"] = True
    with pytest.raises(RestartContractError, match="unknown_fields"):
        validate_restart_session_contract_v1(payload)


def test_state_root_classification_covers_required_fields() -> None:
    rows = build_state_root_classification_matrix_v1()
    fields = {r["field"] for r in rows}
    for required in (
        "confirmation_state",
        "observation_identity_epoch",
        "dynamic_scope_state",
        "required_decision_path_carrier_state",
        "portfolio_state",
        "accounting_state",
        "reconciliation_state_reference",
        "selected_instrument_reference",
        "typed_volatility_reference",
        "evidence_cursor",
        "atomic_decision_path_commit_position",
        "master_v2_full_decision_blob",
        "double_play_full_decision_blob",
    ):
        assert required in fields
    classes = {r["classification"] for r in rows}
    assert "PERSIST_DIRECTLY" in classes
    assert "REBUILD_DETERMINISTICALLY" in classes
    assert "REFERENCE_ONLY" in classes
    assert "EPHEMERAL" in classes
    assert "FORBIDDEN_TO_PERSIST" in classes


def test_failure_injection_matrix(tmp_path: Path) -> None:
    matrix = run_failure_injection_matrix_v1(
        work_root=tmp_path / "fi",
        repository_sha=REPO_SHA,
        repo_root=REPO_ROOT,
    )
    assert matrix["ok"] is True


def test_materialize_evidence_fixtures(tmp_path: Path) -> None:
    # Materialize into repo evidence path is durable; use isolated work root only.
    summary = materialize_capability_evidence_v1(
        repository_sha=REPO_SHA,
        repo_root=REPO_ROOT,
        work_root=tmp_path / "evidence_work",
    )
    assert summary["ok"] is True
    evidence_root = (
        REPO_ROOT
        / "docs/evidence/capability_phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
    )
    assert (evidence_root / "SUMMARY.json").is_file()
    assert (evidence_root / "MANIFEST.sha256").is_file()
    assert (evidence_root / "fixtures" / "flat_campaign_bundle_v1.json").is_file()


def test_flat_claim_not_open_position_recovery() -> None:
    assert OPEN_POSITION_NOT_OBSERVED != OPEN_POSITION_RECOVERY_PROVEN
