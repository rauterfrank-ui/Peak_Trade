"""Architecture guards for additional evidence repository SHA semantics v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    ARTIFACT_RELATIVE_PATH,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    NETWORK_ACCESS_AUTHORIZED,
    PREREGISTRATION_RELATIVE_PATH,
    PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
    READY_FOR_AUTHORIZATION_ISSUANCE,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    REPOSITORY_BINDING_MODE,
    REVIEW_MODE_ID,
    SELF_COMMIT_SHA_EMBEDDING_REQUIRED,
    SESSION_PREREGISTRATION_CREATION_AUTHORIZED,
    SPEC_RELATIVE_PATH,
    TIP_OF_MAIN_EQUALITY_REQUIRED,
    V1_NEW_AUTHORIZATION_READINESS_ALLOWED,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    count_active_v2_preregistrations,
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.critical_surface_v2 import (
    verify_critical_surface_manifest_artifact_v2,
)


def assert_architecture_guards_v2(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / (
        "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
        "session_preregistration_contract_v2"
    )
    import_lines: list[str] = []
    code_parts: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name not in {"architecture_guards_v2.py", "constants_v2.py"}:
            code_parts.append(text)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append(stripped)
    code_blob = "\n".join(code_parts)
    imports_blob = "\n".join(import_lines)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    for side_effect in ("requests.get", "urllib.request", "socket."):
        if side_effect in code_blob:
            raise RuntimeError(f"NETWORK_SIDE_EFFECT_FORBIDDEN:{side_effect}")

    if TIP_OF_MAIN_EQUALITY_REQUIRED or SELF_COMMIT_SHA_EMBEDDING_REQUIRED:
        raise RuntimeError("TIP_SELF_BINDING_FORBIDDEN")
    if V1_NEW_AUTHORIZATION_READINESS_ALLOWED:
        raise RuntimeError("V1_NEW_AUTH_READINESS_FORBIDDEN")
    if (
        SESSION_PREREGISTRATION_CREATION_AUTHORIZED
        or AUTHORIZATION_ISSUANCE_AUTHORIZED
        or AUTHORIZATION_CONSUMPTION_AUTHORIZED
        or NETWORK_ACCESS_AUTHORIZED
        or PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED
        or READY_FOR_AUTHORIZATION_ISSUANCE
        or READY_FOR_PRODUCTIVE_SESSION_EXECUTION
        or not HARD_STOP
    ):
        raise RuntimeError("CAPABILITY_GUARD_DRIFT")

    if "TIP_OF_MAIN_EQUALITY_REQUIRED = True" in (package_dir / "constants_v2.py").read_text(
        encoding="utf-8"
    ):
        raise RuntimeError("TIP_EQUALITY_CONSTANT_DRIFT")

    verify_critical_surface_manifest_artifact_v2(repo_root=root)
    artifact = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    if artifact.get("repository_binding_mode") != REPOSITORY_BINDING_MODE:
        raise RuntimeError("BINDING_MODE_DRIFT")
    if count_active_v2_preregistrations(repo_root=root) != 1:
        raise RuntimeError("ACTIVE_V2_PREREGISTRATION_COUNT_DRIFT")

    spec_path = root / SPEC_RELATIVE_PATH
    if not spec_path.is_file():
        raise RuntimeError(f"SPEC_MISSING:{SPEC_RELATIVE_PATH}")
    spec_text = spec_path.read_text(encoding="utf-8")
    for marker in (
        "CODE_BASELINE_BINDING_MODE=IMMUTABLE_ANCESTOR_SHA",
        "TIP_OF_MAIN_EQUALITY_REQUIRED=false",
        "SELF_COMMIT_SHA_EMBEDDING_REQUIRED=false",
        "PR_5629_SUPERSEDED=true",
        "HARD_STOP=true",
    ):
        if marker not in spec_text:
            raise RuntimeError(f"SPEC_MARKER_MISSING:{marker}")

    return {
        "guards_pass": True,
        "review_mode": REVIEW_MODE_ID,
        "artifact_path": ARTIFACT_RELATIVE_PATH,
        "critical_surface_manifest_path": CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
        "preregistration_path": PREREGISTRATION_RELATIVE_PATH,
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "tip_of_main_equality_required": False,
        "self_commit_sha_embedding_required": False,
        "v1_new_authorization_readiness_allowed": False,
        "active_v2_preregistration_count": 1,
        "HARD_STOP": True,
    }
