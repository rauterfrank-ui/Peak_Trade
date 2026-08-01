"""Architecture guards for additional evidence session preregistration contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    DOUBLE_PLAY_LOGIC_CHANGED,
    ENTRY_EXIT_PRECEDENCE_CHANGED,
    EXISTING_EXHAUSTED_SESSION_IDS,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    MASTER_V2_LOGIC_CHANGED,
    NETWORK_ACCESS_AUTHORIZED,
    NUMERIC_MAX_AGE_ENFORCING,
    NUMERIC_MAX_AGE_SELECTED,
    PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
    READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION,
    READY_FOR_AUTHORIZATION_ISSUANCE,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    REVIEW_MODE_ID,
    RISK_SAFETY_SEMANTICS_CHANGED,
    SECOND_AGE_AUTHORITY_PRESENT,
    SECOND_DECISION_AUTHORITY_PRESENT,
    SESSION_PREREGISTRATION_CREATION_AUTHORIZED,
    SPEC_RELATIVE_PATH,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.contract_v1 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v1,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / (
        "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
        "session_preregistration_contract_v1"
    )
    import_lines: list[str] = []
    code_parts: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name not in {"architecture_guards_v1.py", "constants_v1.py"}:
            code_parts.append(text)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append(stripped)
    code_blob = "\n".join(code_parts)
    imports_blob = "\n".join(import_lines)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob or token in code_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    forbidden_true = (
        "SESSION_PREREGISTRATION_CREATION_AUTHORIZED = True",
        "AUTHORIZATION_ISSUANCE_AUTHORIZED = True",
        "AUTHORIZATION_CONSUMPTION_AUTHORIZED = True",
        "NETWORK_ACCESS_AUTHORIZED = True",
        "PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED = True",
        "NUMERIC_MAX_AGE_SELECTED = True",
        "NUMERIC_MAX_AGE_ENFORCING = True",
        "MASTER_V2_LOGIC_CHANGED = True",
        "DOUBLE_PLAY_LOGIC_CHANGED = True",
        "ENTRY_EXIT_PRECEDENCE_CHANGED = True",
        "RISK_SAFETY_SEMANTICS_CHANGED = True",
        "SECOND_AGE_AUTHORITY_PRESENT = True",
        "SECOND_DECISION_AUTHORITY_PRESENT = True",
        "READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION = True",
        "READY_FOR_AUTHORIZATION_ISSUANCE = True",
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION = True",
        "ARTIFICIAL_DELAY_INJECTION = True",
        "SYNTHETIC_EVENT_TIME_ADVANCE = True",
        "AGE_OVERRIDE = True",
        "AS_OF_OVERRIDE = True",
        "RECOMPUTE_FORCE_FLAG = True",
        "LIFECYCLE_STATE_EDIT = True",
        "EVIDENCE_BACKFILL = True",
    )
    for token in forbidden_true:
        if token in code_blob or token in (package_dir / "constants_v1.py").read_text(
            encoding="utf-8"
        ):
            # constants intentionally keep = False; only True forms are forbidden.
            if token.endswith("= True") and token in (package_dir / "constants_v1.py").read_text(
                encoding="utf-8"
            ):
                raise RuntimeError(f"FORBIDDEN_AUTHORITY_FLAG:{token}")
            if token in code_blob:
                raise RuntimeError(f"FORBIDDEN_AUTHORITY_FLAG:{token}")

    if "time.sleep" in code_blob or "asyncio.sleep" in code_blob:
        raise RuntimeError("SLEEP_BASED_AGE_SYNTHESIS_FORBIDDEN")

    if (
        SESSION_PREREGISTRATION_CREATION_AUTHORIZED
        or AUTHORIZATION_ISSUANCE_AUTHORIZED
        or AUTHORIZATION_CONSUMPTION_AUTHORIZED
        or NETWORK_ACCESS_AUTHORIZED
        or PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED
        or NUMERIC_MAX_AGE_SELECTED
        or NUMERIC_MAX_AGE_ENFORCING
        or MASTER_V2_LOGIC_CHANGED
        or DOUBLE_PLAY_LOGIC_CHANGED
        or ENTRY_EXIT_PRECEDENCE_CHANGED
        or RISK_SAFETY_SEMANTICS_CHANGED
        or SECOND_AGE_AUTHORITY_PRESENT
        or SECOND_DECISION_AUTHORITY_PRESENT
        or READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION
        or READY_FOR_AUTHORIZATION_ISSUANCE
        or READY_FOR_PRODUCTIVE_SESSION_EXECUTION
        or not HARD_STOP
    ):
        raise RuntimeError("CAPABILITY_GUARD_DRIFT")

    if len(EXISTING_EXHAUSTED_SESSION_IDS) != 2:
        raise RuntimeError("EXHAUSTED_SESSION_ID_COUNT_DRIFT")

    artifact = verify_additional_evidence_session_preregistration_contract_artifact_v1(
        repo_root=root
    )
    spec_path = root / SPEC_RELATIVE_PATH
    if not spec_path.is_file():
        raise RuntimeError("SPEC_MISSING")
    spec_text = spec_path.read_text(encoding="utf-8")
    if "CONTRACT_CAPABILITY_MERGE" not in spec_text:
        raise RuntimeError("OPERATOR_WORKFLOW_MISSING_FROM_SPEC")
    if "CREATE_ADDITIONAL_SESSION_PREREGISTRATION" not in spec_text:
        raise RuntimeError("OPERATOR_WORKFLOW_INCOMPLETE")

    # Existing s01/s02 preregistration artifact must remain byte-present and untouched
    # by this capability (path existence guard only; no rewrite).
    existing = root / (
        "config/research/"
        "canonical_volatility_numeric_max_age_productive_evidence_"
        "session_preregistration_v1.json"
    )
    if not existing.is_file():
        raise RuntimeError("EXISTING_S01_S02_PREREGISTRATION_MISSING")

    return {
        "guards_pass": True,
        "review_mode": REVIEW_MODE_ID,
        "artifact_path": ARTIFACT_RELATIVE_PATH,
        "contract_digest": artifact.get("contract_digest"),
        "SESSION_PREREGISTRATION_CREATION_AUTHORIZED": False,
        "AUTHORIZATION_ISSUANCE_AUTHORIZED": False,
        "PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED": False,
        "SECOND_AGE_AUTHORITY_PRESENT": False,
        "SECOND_DECISION_AUTHORITY_PRESENT": False,
        "HARD_STOP": True,
    }
