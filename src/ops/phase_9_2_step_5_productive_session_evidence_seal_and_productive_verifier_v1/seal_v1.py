"""Deterministic, idempotent seal for productive Step-5 session evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.constants_v1 import (
    CANONICAL_SESSION_RELATIVE_PATH,
    CAPABILITY_ID,
    EXPECTED_HEARTBEAT_COUNT,
    EXPECTED_PUBLIC_MD_REQUEST_COUNT,
    NEXT_OPEN_PHASE_9_2_STEP,
    NEXT_RECOMMENDED_CAPABILITY_ID,
    NEXT_RECOMMENDED_CAPABILITY_TITLE,
    OFFLINE_VERIFIER_DOMAIN,
    OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION,
    PHASE_9_2_STEP_3_STATUS,
    PHASE_9_2_STEP_4_STATUS,
    PHASE_9_2_STEP_5_STATUS,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER,
    PRODUCTIVE_VERIFIER_DOMAIN,
    REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED,
    SEAL_SCHEMA,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.digest_v1 import (
    sha256_canonical_v1,
    sha256_file_bytes_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.productive_session_verifier_v1 import (
    verify_productive_session_evidence_v1,
)


def _immutable_binding(session_root: Path) -> dict[str, Any]:
    files = {
        "operator_public_result.json": session_root / "operator_public_result.json",
        "evidence/session_terminal_manifest_v1.json": (
            session_root / "evidence" / "session_terminal_manifest_v1.json"
        ),
        "evidence/session_events.jsonl": session_root / "evidence" / "session_events.jsonl",
        "evidence/executor_summary.json": session_root / "evidence" / "executor_summary.json",
        "progress.json": session_root / "progress.json",
        "persistence/step5_authorization_consumption_ledger_v1.jsonl": (
            session_root / "persistence" / "step5_authorization_consumption_ledger_v1.jsonl"
        ),
        "issuance/confirm_token_public.json": session_root
        / "issuance"
        / "confirm_token_public.json",
        "issuance/grant_public.json": session_root / "issuance" / "grant_public.json",
    }
    digests: dict[str, str] = {}
    for rel, path in files.items():
        if path.is_file():
            digests[rel] = sha256_file_bytes_v1(path)
    return {
        "raw_session_evidence_changed": False,
        "immutable_reference_only": True,
        "file_sha256": digests,
    }


def seal_productive_session_evidence_v1(
    *,
    session_root: Path,
    expected_repository_sha: str,
    seal_output_path: Path,
    repo_root: Path | None = None,
    residual_process_found: bool = False,
) -> dict[str, Any]:
    """Write a seal artifact that references (does not rewrite) raw session evidence."""
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    session_root = Path(session_root)
    verified = verify_productive_session_evidence_v1(
        session_root,
        expected_repository_sha=expected_repository_sha,
        expected_public_md_request_count=EXPECTED_PUBLIC_MD_REQUEST_COUNT,
        expected_heartbeat_count=EXPECTED_HEARTBEAT_COUNT,
        repo_root=root,
        residual_process_found=residual_process_found,
    )
    try:
        session_rel = str(session_root.resolve().relative_to(root.resolve()))
    except ValueError:
        session_rel = str(session_root)

    claims = {
        "PHASE_9_2_STEP_3_STATUS": PHASE_9_2_STEP_3_STATUS,
        "PHASE_9_2_STEP_4_STATUS": PHASE_9_2_STEP_4_STATUS,
        "PHASE_9_2_STEP_5_STATUS": PHASE_9_2_STEP_5_STATUS,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "STEP5_PRODUCTIVE_SESSION_PASS": bool(verified.get("ok")),
        "STEP5_PRODUCTIVE_EVIDENCE_VERIFIED": bool(verified.get("ok")),
        "STEP5_SESSION_LADDER_STEP_CLOSED": bool(verified.get("ok")),
        "STEP5_CAPABILITY_CLOSED": bool(verified.get("ok")),
        "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED,
        "NEXT_OPEN_PHASE_9_2_STEP": NEXT_OPEN_PHASE_9_2_STEP,
        "NEXT_RECOMMENDED_CAPABILITY_ID": NEXT_RECOMMENDED_CAPABILITY_ID,
        "NEXT_RECOMMENDED_CAPABILITY_TITLE": NEXT_RECOMMENDED_CAPABILITY_TITLE,
        "OFFLINE_VERIFIER_DOMAIN": OFFLINE_VERIFIER_DOMAIN,
        "PRODUCTIVE_VERIFIER_DOMAIN": PRODUCTIVE_VERIFIER_DOMAIN,
        "OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION": (
            OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION
        ),
        "PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER": (
            PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER
        ),
        "RAW_SESSION_EVIDENCE_CHANGED": False,
        "CORE_LOGIC_CHANGED": False,
        "NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY": False,
        "AUTHORIZATION_ISSUED_BY_THIS_CAPABILITY": False,
        "AUTHORIZATION_CONSUMED_BY_THIS_CAPABILITY": False,
        "CONFIRM_TOKEN_CONSUMED_BY_THIS_CAPABILITY": False,
        "CANONICAL_SESSION_RELATIVE_PATH": CANONICAL_SESSION_RELATIVE_PATH,
        "SESSION_EVIDENCE_PATH": session_rel,
    }

    seal: dict[str, Any] = {
        "schema": SEAL_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "session_evidence_path": session_rel,
        "canonical_session_relative_path": CANONICAL_SESSION_RELATIVE_PATH,
        "repository_sha": verified.get("repository_sha"),
        "expected_repository_sha": expected_repository_sha,
        "config_digest": verified.get("config_digest"),
        "session_contract_digest": verified.get("session_contract_digest"),
        "binding_config_digest": verified.get("binding_config_digest"),
        "immutable_session_binding": _immutable_binding(session_root),
        "productive_verifier_result": verified,
        "domain_separation": {
            "offline_verifier_domain": OFFLINE_VERIFIER_DOMAIN,
            "productive_verifier_domain": PRODUCTIVE_VERIFIER_DOMAIN,
            "offline_verifier_expected_false_for_productive_session": (
                OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION
            ),
            "productive_session_invalidated_by_offline_verifier": (
                PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER
            ),
        },
        "claims": claims,
        "PRODUCTIVE_VERIFIER_RESULT": verified.get("VERIFIER_RESULT"),
        "PRODUCTIVE_EVIDENCE_SEALED": bool(verified.get("ok")),
    }
    seal["seal_digest"] = sha256_canonical_v1({k: v for k, v in seal.items() if k != "seal_digest"})
    write_json_atomic_v1(Path(seal_output_path), seal)
    # Idempotent rewrite with identical digest
    write_json_atomic_v1(Path(seal_output_path), seal)
    return seal
