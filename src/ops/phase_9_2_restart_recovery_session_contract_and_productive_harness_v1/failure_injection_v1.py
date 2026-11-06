"""Controlled failure-injection scenarios for Phase 9.2 restart harness."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

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
    DURABLE_STATE_LINEAGE_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    PRE_TERMINAL_MANIFEST_FILENAME,
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TELEMETRY_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartLockError,
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (
    run_post_restart_segment_v1,
    run_pre_restart_segment_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    build_fixture_checkpoint_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)


def _base_checkpoint(*, open_position: bool = False):
    return build_fixture_checkpoint_v1(
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        observation_epoch=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
        open_position_present=open_position,
        distinct_observation_count=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
        evidence_cursor=sha256_canonical_v1({"cursor": "fi"}),
        portfolio_seed="p",
        scope_seed="s",
        accounting_seed="a",
        runtime_seed="r",
        instrument_id=CANONICAL_INSTRUMENT_ID,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        applied_fill_ids=["fill_x"] if open_position else [],
        applied_confirmation_ids=["conf_x"],
    )


def run_failure_injection_matrix_v1(
    *,
    work_root: Path,
    repository_sha: str,
    repo_root: Path,
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    def _case(name: str, fn: Callable[[], dict[str, Any]]) -> None:
        case_root = work_root / name
        if case_root.exists():
            shutil.rmtree(case_root)
        case_root.mkdir(parents=True)
        try:
            results[name] = fn()
        except Exception as exc:  # noqa: BLE001 - capture fail-closed outcomes
            results[name] = {"ok": False, "error": str(exc), "expected_fail_closed": True}

    def auth_reuse() -> dict[str, Any]:
        cp = _base_checkpoint()
        runtime = "rt_reuse"
        auth = "auth_reuse_once"
        digest = authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_PRE,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        )
        contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id="seg_reuse",
            runtime_session_id=runtime,
            authorization_id=auth,
            authorization_digest=digest,
            expected_runtime_state_digest=cp.runtime_state_digest,
            expected_portfolio_digest=cp.portfolio_digest,
            expected_scope_digest=cp.scope_digest,
            expected_accounting_digest=cp.accounting_digest,
            expected_evidence_cursor=cp.evidence_cursor,
            repo_root=repo_root,
        )
        first = run_pre_restart_segment_v1(
            contract=contract,
            persistence_root=work_root / "auth_reuse",
            checkpoint=cp,
        )
        second = run_pre_restart_segment_v1(
            contract=contract,
            persistence_root=work_root / "auth_reuse",
            checkpoint=cp,
        )
        return {
            "ok": first.ok
            and (not second.ok)
            and any("authorization_reuse" in b for b in second.blockers),
            "first_ok": first.ok,
            "second_blockers": second.blockers,
        }

    def confirmation_mutation() -> dict[str, Any]:
        bundle_root = work_root / "confirmation_mutation"
        good = run_restart_campaign_fixture_v1(
            persistence_root=bundle_root,
            repository_sha=repository_sha,
            repo_root=repo_root,
        )
        cp = read_json_v1(bundle_root / CHECKPOINT_FILENAME)
        cp["confirmation_session_id"] = "mutated_confirmation_session"
        write_json_atomic_v1(bundle_root / CHECKPOINT_FILENAME, cp)
        # Remove post artifacts and re-run post with mutated checkpoint.
        for name in (f"post_{TELEMETRY_FILENAME}", "post_restart_terminal_manifest_v1.json"):
            path = bundle_root / name
            if path.exists():
                path.unlink()
        post_runtime = "phase92_restart_post_runtime_session_mut"
        post_auth = "phase92_restart_post_auth_mut"
        post_contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_POST,
            segment_id="segment_post_restart_mut",
            runtime_session_id=post_runtime,
            authorization_id=post_auth,
            authorization_digest=authorization_digest_v1(
                authorization_id=post_auth,
                segment_role=SEGMENT_ROLE_POST,
                restart_campaign_id=RESTART_CAMPAIGN_ID,
                runtime_session_id=post_runtime,
            ),
            expected_runtime_state_digest=str(cp["runtime_state_digest"]),
            expected_portfolio_digest=str(cp["portfolio_digest"]),
            expected_scope_digest=str(cp["scope_digest"]),
            expected_accounting_digest=str(cp["accounting_digest"]),
            expected_evidence_cursor=str(cp["evidence_cursor"]),
            predecessor_segment_id="segment_pre_restart_v1",
            predecessor_terminal_manifest_digest=good["pre_segment"]["terminal_manifest_digest"],
            confirmation_session_id=CONFIRMATION_SESSION_ID,
            repo_root=repo_root,
        )
        post = run_post_restart_segment_v1(
            contract=post_contract,
            persistence_root=bundle_root,
        )
        return {
            "ok": (not post.ok)
            and any("confirmation_session_id_mutation" in b for b in post.blockers),
            "blockers": post.blockers,
        }

    def orphan_lock() -> dict[str, Any]:
        case = work_root / "orphan_lock"
        case.mkdir(parents=True, exist_ok=True)
        lock_path = lock_path_for_root_v1(case)
        lock_path.write_text(
            json.dumps({"runtime_session_id": "dead", "owner": "orphan", "pid": 1}) + "\n",
            encoding="utf-8",
        )
        lock = RestartSegmentLockV1(
            lock_path=lock_path,
            runtime_session_id="new",
            owner="new_owner",
        )
        try:
            lock.acquire()
            acquired = True
        except RestartLockError as exc:
            acquired = False
            err = str(exc)
        else:
            err = ""
        return {
            "ok": (not acquired) and "ORPHAN_OR_DUPLICATE_LOCK_FAIL_CLOSED" in err,
            "error": err,
            "lock_still_present": lock_path.exists(),
        }

    def missing_pre() -> dict[str, Any]:
        case = work_root / "missing_pre"
        case.mkdir(parents=True, exist_ok=True)
        write_json_atomic_v1(
            case / f"post_{TELEMETRY_FILENAME}",
            {k: 0 for k in ("restart_campaign_id",)},
        )
        result = verify_restart_bundle_v1(persistence_root=case)
        return {
            "ok": (not result.verified) and "missing_pre_restart_segment" in result.blockers,
            "blockers": result.blockers,
        }

    def missing_post() -> dict[str, Any]:
        case = work_root / "missing_post"
        run_restart_campaign_fixture_v1(
            persistence_root=case,
            repository_sha=repository_sha,
            repo_root=repo_root,
        )
        post_manifest = case / "post_restart_terminal_manifest_v1.json"
        post_tel = case / f"post_{TELEMETRY_FILENAME}"
        if post_manifest.exists():
            post_manifest.unlink()
        if post_tel.exists():
            post_tel.unlink()
        result = verify_restart_bundle_v1(persistence_root=case)
        return {
            "ok": (not result.verified) and "missing_post_restart_segment" in result.blockers,
            "blockers": result.blockers,
        }

    def digest_mismatch() -> dict[str, Any]:
        case = work_root / "digest_mismatch"
        run_restart_campaign_fixture_v1(
            persistence_root=case,
            repository_sha=repository_sha,
            repo_root=repo_root,
        )
        post = read_json_v1(case / "post_restart_terminal_manifest_v1.json")
        post["pre_restart_terminal_manifest_digest"] = "0" * 64
        write_json_atomic_v1(case / "post_restart_terminal_manifest_v1.json", post)
        result = verify_restart_bundle_v1(persistence_root=case)
        return {
            "ok": (not result.verified) and "digest_mismatch" in result.blockers,
            "blockers": result.blockers,
        }

    def corrupt_checkpoint() -> dict[str, Any]:
        case = work_root / "corrupt_checkpoint"
        good = run_restart_campaign_fixture_v1(
            persistence_root=case,
            repository_sha=repository_sha,
            repo_root=repo_root,
        )
        (case / CHECKPOINT_FILENAME).write_text("{not-json", encoding="utf-8")
        for name in (f"post_{TELEMETRY_FILENAME}", "post_restart_terminal_manifest_v1.json"):
            path = case / name
            if path.exists():
                path.unlink()
        # consume already used post auth from campaign; use new auth
        post_runtime = "rt_corrupt"
        post_auth = "auth_corrupt_post"
        pre_digest = good["pre_segment"]["terminal_manifest_digest"]
        # Restore a minimal expected digest surface via fake contract fields from pre manifest
        pre = read_json_v1(case / PRE_TERMINAL_MANIFEST_FILENAME)
        post_contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_POST,
            segment_id="segment_post_corrupt",
            runtime_session_id=post_runtime,
            authorization_id=post_auth,
            authorization_digest=authorization_digest_v1(
                authorization_id=post_auth,
                segment_role=SEGMENT_ROLE_POST,
                restart_campaign_id=RESTART_CAMPAIGN_ID,
                runtime_session_id=post_runtime,
            ),
            expected_runtime_state_digest=str(pre["runtime_state_digest"]),
            expected_portfolio_digest=str(pre["portfolio_digest"]),
            expected_scope_digest=str(pre["scope_digest"]),
            expected_accounting_digest=str(pre["accounting_digest"]),
            expected_evidence_cursor=str(pre["evidence_cursor"]),
            predecessor_segment_id=str(pre["segment_id"]),
            predecessor_terminal_manifest_digest=pre_digest,
            repo_root=repo_root,
        )
        post = run_post_restart_segment_v1(contract=post_contract, persistence_root=case)
        return {
            "ok": (not post.ok) and any("corrupt_checkpoint" in b for b in post.blockers),
            "blockers": post.blockers,
        }

    def partial_evidence_idempotent() -> dict[str, Any]:
        case = work_root / "partial_evidence"
        bundle = run_restart_campaign_fixture_v1(
            persistence_root=case,
            repository_sha=repository_sha,
            repo_root=repo_root,
        )
        cursor_path = case / "evidence_cursor_v1.json"
        first = read_json_v1(cursor_path)
        write_json_atomic_v1(cursor_path, first)
        second = read_json_v1(cursor_path)
        return {
            "ok": bool(bundle["ok"]) and first == second,
            "cursor": second,
        }

    _case("auth_reuse", auth_reuse)
    _case("confirmation_mutation", confirmation_mutation)
    _case("orphan_lock", orphan_lock)
    _case("missing_pre", missing_pre)
    _case("missing_post", missing_post)
    _case("digest_mismatch", digest_mismatch)
    _case("corrupt_checkpoint", corrupt_checkpoint)
    _case("partial_evidence_idempotent", partial_evidence_idempotent)

    all_ok = all(bool(v.get("ok")) for v in results.values())
    return {"ok": all_ok, "cases": results}
