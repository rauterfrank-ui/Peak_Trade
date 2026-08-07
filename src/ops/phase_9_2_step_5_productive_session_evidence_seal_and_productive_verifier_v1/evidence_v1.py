"""Evidence materialization for productive session seal + verifier capability."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.constants_v1 import (
    CANONICAL_SESSION_RELATIVE_PATH,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    OFFLINE_VERIFIER_DOMAIN,
    OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER,
    PRODUCTIVE_VERIFIER_DOMAIN,
    SCHEMA_VERSION,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.seal_v1 import (
    seal_productive_session_evidence_v1,
)


def materialize_seal_evidence_v1(
    *,
    repository_sha: str,
    session_root: Path | None = None,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    session = (
        Path(session_root) if session_root is not None else root / CANONICAL_SESSION_RELATIVE_PATH
    )
    seal_path = fixtures / "productive_session_evidence_seal_v1.json"
    seal = seal_productive_session_evidence_v1(
        session_root=session,
        expected_repository_sha=repository_sha,
        seal_output_path=seal_path,
        repo_root=root,
    )
    write_json_atomic_v1(
        fixtures / "productive_verifier_result_v1.json",
        dict(seal.get("productive_verifier_result") or {}),
    )
    domain = {
        "offline_verifier_domain": OFFLINE_VERIFIER_DOMAIN,
        "productive_verifier_domain": PRODUCTIVE_VERIFIER_DOMAIN,
        "offline_verifier_expected_false_for_productive_session": (
            OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION
        ),
        "productive_session_invalidated_by_offline_verifier": (
            PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER
        ),
        "offline_verifier_semantics_changed": False,
        "raw_session_evidence_changed": False,
    }
    write_json_atomic_v1(fixtures / "domain_separation_v1.json", domain)
    write_json_atomic_v1(
        fixtures / "structural_proof_v1.json",
        {
            "capability_id": CAPABILITY_ID,
            "schema_version": SCHEMA_VERSION,
            "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
            "canonical_session_relative_path": CANONICAL_SESSION_RELATIVE_PATH,
            "network_session_started_by_this_capability": False,
            "authorization_consumed_by_this_capability": False,
            "confirm_token_consumed_by_this_capability": False,
            "core_logic_changed": False,
        },
    )
    (fixtures / "focused_tests.txt").write_text(
        "tests/ops/test_phase_9_2_step_5_productive_session_evidence_seal_"
        "and_productive_verifier_v1.py\n",
        encoding="utf-8",
    )

    claims = dict(seal.get("claims") or {})
    claims.update(
        {
            "EVIDENCE_CREATED": True,
            "PRODUCTIVE_EVIDENCE_SEALED": bool(seal.get("PRODUCTIVE_EVIDENCE_SEALED")),
            "PRODUCTIVE_VERIFIER_RESULT": seal.get("PRODUCTIVE_VERIFIER_RESULT"),
            "SEAL_DIGEST": seal.get("seal_digest"),
        }
    )
    summary = {
        "ok": bool(seal.get("PRODUCTIVE_EVIDENCE_SEALED")),
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "session_evidence_path": str(session),
        "productive_evidence_seal_path": str(seal_path),
        "productive_evidence_seal_digest": seal.get("seal_digest"),
        "claims": claims,
        "domain_separation": domain,
        "productive_verifier_result": seal.get("PRODUCTIVE_VERIFIER_RESULT"),
        "raw_session_evidence_changed": False,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "core_logic_changed": False,
        "evidence_root": str(out),
        "claims_match_evidence": bool(seal.get("PRODUCTIVE_EVIDENCE_SEALED")),
    }
    summary["summary_digest"] = sha256_canonical_v1(
        {k: v for k, v in summary.items() if k != "summary_digest"}
    )
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    digest_lines: list[str] = []
    for path in sorted(fixtures.rglob("*")):
        if path.is_file():
            digest_lines.append(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
                f"fixtures/{path.relative_to(fixtures)}"
            )
    digest_lines.append(
        f"{hashlib.sha256((out / 'SUMMARY.json').read_bytes()).hexdigest()}  SUMMARY.json"
    )
    (out / "MANIFEST.sha256").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return summary
