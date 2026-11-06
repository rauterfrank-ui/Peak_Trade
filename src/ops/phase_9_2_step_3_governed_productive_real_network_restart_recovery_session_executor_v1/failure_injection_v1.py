"""Offline failure-injection matrix for Step-3 executor (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    write_json_atomic_v1 as write_sgo_json_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    CAPABILITY_ID,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.governed_executor_execution_v1 import (
    execute_governed_step3_executor_session_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.hidden_pty_handoff_v1 import (
    fingerprint_only_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.session_lock_gate_v1 import (
    prove_second_writer_rejected_v1,
)


def _token() -> str:
    return "PTCONFIRMv1_STEP3EXEC" + ("Z" * 20)


def _issue_sgo(path: Path, *, sha: str, cfg: str, now: float) -> None:
    authority = build_session_go_authority_v1(
        session_go_id="sgo_step3_executor_fi_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600.0,
        activation_status=ACTIVATION_STATUS_ACTIVE,
        max_session_duration_seconds=3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
        notes=("TEST_EPHEMERAL_SESSION_GO",),
    )
    write_sgo_json_v1(path, authority.to_dict())


def run_step3_executor_failure_injection_v1(
    *,
    repository_sha: str,
    config_digest: str,
    persistence_root: Path,
    repo_root: Path | None = None,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    persistence_root = Path(persistence_root)
    persistence_root.mkdir(parents=True, exist_ok=True)
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    token = _token()
    fp = fingerprint_only_v1(token)
    auth_id = "auth_step3_exec_fi_v1"
    auth_digest = sha256_canonical_v1({"authorization_id": auth_id, "sha": repository_sha})
    sgo = persistence_root / "sgo.json"
    _issue_sgo(sgo, sha=repository_sha, cfg=config_digest, now=now_unix)

    def _base(**overrides: Any) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "expected_repository_sha": repository_sha,
            "expected_config_digest": config_digest,
            "expected_session_contract_digest": bundle["session_contract_digest"],
            "expected_binding_config_digest": bundle["binding_config_digest"],
            "authorization_id": auth_id,
            "authorization_digest": auth_digest,
            "confirm_token_binding_sha256": fp,
            "persistence_root": persistence_root / "base",
            "evidence_root": persistence_root / "evidence",
            "session_go_path": sgo,
            "now_unix": now_unix,
            "authorization_expires_at": now_unix + 3600.0,
            "confirm_token_expires_at": now_unix + 3600.0,
            "confirm_token_plaintext": token,
            "authorization_capability_id": CAPABILITY_ID,
            "authorization_scope": SESSION_SCOPE,
            "authorization_session_id": TARGET_SESSION_ID,
            "owner_go": True,
            "operator_authorization_explicit": True,
            "network_session_go": True,
            "repo_root": repo_root,
        }
        kwargs.update(overrides)
        # Isolate persistence per case when provided
        if "persistence_root" in overrides:
            kwargs["persistence_root"] = overrides["persistence_root"]
        result = execute_governed_step3_executor_session_v1(**kwargs)
        return {
            "ok": result.ok,
            "blockers": list(result.blockers),
            "terminal_class": result.terminal_class,
            "network_session_started": result.network_session_started,
            "authorization_consumed": result.authorization_consumed,
            "confirm_token_consumed": result.confirm_token_consumed,
            "claims": dict(result.claims),
            "executor_result": result.executor_result,
        }

    cases: dict[str, Any] = {}

    req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        repo_root=repo_root,
    )
    cases["request_real_network_fail_closed"] = {
        "ok": (not req.ok) and "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY" in req.blockers,
        "blockers": list(req.blockers),
    }

    cases["without_owner_go"] = _base(
        owner_go=False,
        persistence_root=persistence_root / "no_owner",
    )
    cases["without_operator"] = _base(
        operator_authorization_explicit=False,
        persistence_root=persistence_root / "no_op",
    )
    cases["without_network_go"] = _base(
        network_session_go=False,
        persistence_root=persistence_root / "no_net",
    )
    cases["missing_authorization"] = _base(
        authorization_id="",
        authorization_digest="",
        persistence_root=persistence_root / "no_auth",
    )
    cases["wrong_sha"] = _base(
        authorization_repository_sha="0" * 40,
        persistence_root=persistence_root / "wrong_sha",
    )
    cases["wrong_contract_digest"] = _base(
        expected_session_contract_digest="0" * 64,
        persistence_root=persistence_root / "wrong_contract",
    )
    cases["wrong_binding_digest"] = _base(
        expected_binding_config_digest="0" * 64,
        persistence_root=persistence_root / "wrong_binding",
    )
    cases["wrong_capability"] = _base(
        authorization_capability_id="WRONG_CAPABILITY",
        persistence_root=persistence_root / "wrong_cap",
    )
    cases["expired_authorization"] = _base(
        authorization_expires_at=now_unix - 1,
        persistence_root=persistence_root / "expired_auth",
    )
    cases["wrong_token_digest"] = _base(
        confirm_token_binding_sha256="0" * 64,
        persistence_root=persistence_root / "wrong_token",
    )
    cases["missing_token"] = _base(
        confirm_token_plaintext="",
        persistence_root=persistence_root / "missing_token",
    )

    def _campaign(*, root: str, **fi: Any) -> dict[str, Any]:
        return _base(
            invoke_executor=True,
            allow_real_network_side_effects=False,
            persistence_root=persistence_root / root,
            **fi,
        )

    cases["crash_before_pre_commit"] = _campaign(
        root="crash_before",
        force_crash_before_pre_commit=True,
    )
    cases["crash_after_pre_commit"] = _campaign(
        root="crash_after",
        force_crash_after_pre_commit=True,
    )
    cases["crash_during_handoff"] = _campaign(
        root="crash_handoff",
        force_crash_during_handoff=True,
    )
    cases["recovery_start_fail"] = _campaign(
        root="recovery_fail",
        force_recovery_start_fail=True,
    )
    cases["double_recovery"] = _campaign(
        root="double_recovery",
        force_double_recovery=True,
    )
    cases["reconciliation_missing"] = _campaign(
        root="no_recon",
        force_skip_reconciliation=True,
    )
    cases["state_divergence"] = _campaign(
        root="divergence",
        force_state_divergence=True,
    )
    cases["confirmation_id_drift"] = _campaign(
        root="conf_drift",
        force_confirmation_session_drift=True,
    )
    cases["instrument_drift"] = _campaign(
        root="instr_drift",
        force_instrument_drift=True,
    )
    cases["duplicate_confirmation"] = _campaign(
        root="dup_conf",
        force_duplicate_confirmation_id="dup_conf_1",
    )
    cases["duplicate_intent"] = _campaign(
        root="dup_intent",
        force_duplicate_intent_id="dup_intent_1",
    )
    cases["duplicate_fill"] = _campaign(
        root="dup_fill",
        force_duplicate_fill_id="dup_fill_1",
    )
    cases["lost_scope"] = _campaign(
        root="lost_scope",
        force_lost_scope=True,
    )
    cases["evidence_write_error"] = _campaign(
        root="ev_write",
        force_evidence_write_error=True,
    )

    writer = prove_second_writer_rejected_v1(persistence_root=persistence_root / "writer")
    cases["writer_conflict"] = {
        "ok": bool(writer.get("ok")),
        "blockers": list(writer.get("second_blockers") or []),
    }

    private = prove_public_md_get_only_boundary_v1(path="/api/v5/private/account")
    cases["private_endpoint"] = {
        "ok": (not private.get("ok"))
        and "PRIVATE_ENDPOINT_FORBIDDEN" in private.get("blockers", []),
        "blockers": list(private.get("blockers") or []),
    }
    auth_hdr = prove_public_md_get_only_boundary_v1(auth_header_present=True)
    cases["auth_header"] = {
        "ok": (not auth_hdr.get("ok")) and "AUTH_HEADER_FORBIDDEN" in auth_hdr.get("blockers", []),
        "blockers": list(auth_hdr.get("blockers") or []),
    }
    post_method = prove_public_md_get_only_boundary_v1(method="POST")
    cases["post_method"] = {
        "ok": (not post_method.get("ok")),
        "blockers": list(post_method.get("blockers") or []),
    }

    # Happy offline path still must not claim productive network start
    happy = _campaign(root="happy_offline")
    cases["offline_campaign_no_network_claim"] = {
        "ok": (not happy.get("network_session_started"))
        and bool(
            (happy.get("claims") or {}).get("OFFLINE_INJECTED_EXECUTOR_OBSERVED")
            or happy.get("executor_result")
        ),
        "network_session_started": happy.get("network_session_started"),
        "blockers": list(happy.get("blockers") or []),
    }

    required = [
        "request_real_network_fail_closed",
        "without_owner_go",
        "without_operator",
        "without_network_go",
        "missing_authorization",
        "wrong_sha",
        "wrong_contract_digest",
        "wrong_binding_digest",
        "wrong_capability",
        "expired_authorization",
        "wrong_token_digest",
        "missing_token",
        "crash_before_pre_commit",
        "crash_after_pre_commit",
        "crash_during_handoff",
        "recovery_start_fail",
        "double_recovery",
        "reconciliation_missing",
        "state_divergence",
        "confirmation_id_drift",
        "instrument_drift",
        "duplicate_confirmation",
        "duplicate_intent",
        "duplicate_fill",
        "lost_scope",
        "evidence_write_error",
        "writer_conflict",
        "private_endpoint",
        "auth_header",
        "post_method",
        "offline_campaign_no_network_claim",
    ]
    # Gate negatives should fail closed (ok=False) except writer/private/auth/post/request which use ok=true for "case passed"
    gate_negatives = {
        "without_owner_go",
        "without_operator",
        "without_network_go",
        "missing_authorization",
        "wrong_sha",
        "wrong_contract_digest",
        "wrong_binding_digest",
        "wrong_capability",
        "expired_authorization",
        "wrong_token_digest",
        "missing_token",
        "crash_before_pre_commit",
        "crash_after_pre_commit",
        "crash_during_handoff",
        "recovery_start_fail",
        "double_recovery",
        "reconciliation_missing",
        "state_divergence",
        "confirmation_id_drift",
        "instrument_drift",
        "duplicate_confirmation",
        "duplicate_intent",
        "duplicate_fill",
        "lost_scope",
        "evidence_write_error",
    }
    for name in gate_negatives:
        # Normalize: case passes when execution is fail-closed
        row = cases[name]
        cases[name] = {
            "ok": (not row.get("ok")) or bool(row.get("blockers")),
            "blockers": list(row.get("blockers") or []),
            "network_session_started": row.get("network_session_started"),
        }

    all_ok = all(bool(cases[n].get("ok")) for n in required)
    return {
        "ok": all_ok,
        "capability_id": CAPABILITY_ID,
        "cases": cases,
        "required_cases": required,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
