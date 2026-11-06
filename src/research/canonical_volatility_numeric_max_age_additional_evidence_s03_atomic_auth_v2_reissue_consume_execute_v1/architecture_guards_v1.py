"""Architecture guards for the S03 atomic Auth-v2 orchestration owner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    AUTHORIZATION_REMAINS_SINGLE_USE,
    CANONICAL_ATOMIC_OWNER_SYMBOL,
    CANONICAL_AUTH_CONSUMER,
    CANONICAL_AUTH_ISSUER,
    CANONICAL_AUTH_REVOKER,
    CANONICAL_S03_EXECUTION_OWNER,
    CANONICAL_TOKEN_GENERATOR,
    CONSUMPTION_BEFORE_SIDE_EFFECTS,
    FAIL_CLOSED,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    ISSUE_AND_CONSUME_MUST_SHARE_PROCESS_LIFETIME,
    NO_SECOND_AUTHORIZATION_AUTHORITY,
    NO_SECOND_CONSUMPTION_AUTHORITY,
    NO_SECOND_EXECUTION_AUTHORITY,
    ORCHESTRATION_LIFECYCLE_AUTHORITY_ONLY,
    PACKAGE_MARKER,
    PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT,
    SPEC_RELATIVE_PATH,
    TOKEN_LIFETIME_ENDS_AFTER_SUCCESSFUL_CONSUMPTION,
    TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    package_dir = Path(__file__).resolve().parent

    if not PACKAGE_MARKER.endswith("=true"):
        raise RuntimeError("PACKAGE_MARKER_INVALID")
    if not ISSUE_AND_CONSUME_MUST_SHARE_PROCESS_LIFETIME:
        raise RuntimeError("ISSUE_CONSUME_PROCESS_LIFETIME_DISABLED")
    if not TOKEN_LIFETIME_ENDS_AFTER_SUCCESSFUL_CONSUMPTION:
        raise RuntimeError("TOKEN_LIFETIME_INVARIANT_DISABLED")
    if not TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY:
        raise RuntimeError("TOKEN_PROCESS_BOUNDARY_INVARIANT_DISABLED")
    if not AUTHORIZATION_REMAINS_SINGLE_USE:
        raise RuntimeError("SINGLE_USE_INVARIANT_DISABLED")
    if not CONSUMPTION_BEFORE_SIDE_EFFECTS:
        raise RuntimeError("CONSUME_BEFORE_SIDE_EFFECTS_DISABLED")
    if not FAIL_CLOSED:
        raise RuntimeError("FAIL_CLOSED_DISABLED")
    if not (
        NO_SECOND_AUTHORIZATION_AUTHORITY
        and NO_SECOND_CONSUMPTION_AUTHORITY
        and NO_SECOND_EXECUTION_AUTHORITY
        and ORCHESTRATION_LIFECYCLE_AUTHORITY_ONLY
    ):
        raise RuntimeError("SECOND_AUTHORITY_OR_NON_ORCHESTRATION_OWNER")
    if PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT:
        raise RuntimeError("DEFAULT_IMPORT_MUST_NOT_EXECUTE_PRODUCTIVE_ATOMIC_PATH")

    orch = (package_dir / "orchestrator_v1.py").read_text(encoding="utf-8")
    token_mod = (package_dir / "ephemeral_token_v1.py").read_text(encoding="utf-8")
    for required in (
        CANONICAL_AUTH_ISSUER,
        CANONICAL_AUTH_REVOKER,
        CANONICAL_S03_EXECUTION_OWNER,
        "EphemeralConfirmTokenHandleV1",
        "clear_v1",
        CANONICAL_ATOMIC_OWNER_SYMBOL,
    ):
        if required not in orch:
            raise RuntimeError(f"orchestrator_missing_reuse:{required}")
    if CANONICAL_TOKEN_GENERATOR not in token_mod:
        raise RuntimeError("ephemeral_token_missing_canonical_generator")
    if CANONICAL_AUTH_CONSUMER not in orch and "authorization_consumed" not in orch:
        raise RuntimeError("orchestrator_missing_consumption_path")
    # Must not invent a second issuer/consumer implementation.
    if "def issue_additional_evidence_session_authorization_v2" in orch:
        raise RuntimeError("second_issuance_authority_forbidden")
    if "def consume_additional_evidence_session_authorization_v2" in orch:
        raise RuntimeError("second_consumption_authority_forbidden")

    for path in package_dir.glob("*.py"):
        if path.name == "constants_v1.py":
            # constants declare the forbidden substrings; skip self-match.
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IMPORT_SUBSTRINGS:
            if forbidden in text:
                raise RuntimeError(f"forbidden_import:{path.name}:{forbidden}")

    artifact = root / ARTIFACT_RELATIVE_PATH
    spec = root / SPEC_RELATIVE_PATH
    if not artifact.is_file():
        raise RuntimeError("contract_artifact_missing")
    if not spec.is_file():
        raise RuntimeError("spec_missing")

    return {
        "guards_pass": True,
        "issue_and_consume_same_process": True,
        "token_process_boundary_forbidden": True,
        "orchestration_lifecycle_authority_only": True,
        "no_second_authorization_authority": True,
        "no_second_consumption_authority": True,
        "no_second_execution_authority": True,
        "canonical_token_generator": CANONICAL_TOKEN_GENERATOR,
        "canonical_auth_issuer": CANONICAL_AUTH_ISSUER,
        "canonical_auth_revoker": CANONICAL_AUTH_REVOKER,
        "canonical_s03_execution_owner": CANONICAL_S03_EXECUTION_OWNER,
        "artifact_path": ARTIFACT_RELATIVE_PATH,
        "spec_path": SPEC_RELATIVE_PATH,
        "hard_stop": True,
    }
