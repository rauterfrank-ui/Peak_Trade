"""Architecture guards for additional evidence session preregistration contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    BINDING_VALUE_NORMALIZATION_FORBIDDEN,
    CANDIDATE_SCHEMA_CLOSED_WORLD,
    CANDIDATE_SCHEMA_VERSION,
    CANDIDATE_SCHEMA_VERSION_EXACT_MATCH,
    DOUBLE_PLAY_LOGIC_CHANGED,
    ENTRY_EXIT_PRECEDENCE_CHANGED,
    EXISTING_EXHAUSTED_SESSION_IDS,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARDENING_CAPABILITY_ID,
    HARDENING_SPEC_RELATIVE_PATH,
    HARD_STOP,
    INSTRUMENT_VALUE_EXACT_MATCH,
    MASTER_V2_LOGIC_CHANGED,
    NESTED_OBJECTS_PRESENT,
    NETWORK_ACCESS_AUTHORIZED,
    NETWORK_SCOPE_VALUE_EXACT_MATCH,
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
    SESSION_SCOPE_VALUE_EXACT_MATCH,
    SPEC_RELATIVE_PATH,
    UNKNOWN_AUTHORITY_FIELDS_REJECTED,
    UNKNOWN_FIELDS_REJECTED,
    VENUE_VALUE_EXACT_MATCH,
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
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    validate_text = (package_dir / "validate_v1.py").read_text(encoding="utf-8")
    contract_text = (package_dir / "contract_v1.py").read_text(encoding="utf-8")
    for side_effect in ("write_text", "write_bytes", "requests.get", "urllib.request", "socket."):
        if side_effect in validate_text:
            raise RuntimeError(f"VALIDATOR_SIDE_EFFECT_FORBIDDEN:{side_effect}")
        if side_effect in contract_text and side_effect != "read_text":
            if side_effect.startswith("write") or side_effect in {
                "requests.get",
                "urllib.request",
                "socket.",
            }:
                raise RuntimeError(f"BUILDER_SIDE_EFFECT_FORBIDDEN:{side_effect}")

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
        "CANDIDATE_SCHEMA_CLOSED_WORLD = False",
        "UNKNOWN_FIELDS_REJECTED = False",
        "UNKNOWN_AUTHORITY_FIELDS_REJECTED = False",
        "BINDING_VALUE_NORMALIZATION_FORBIDDEN = False",
    )
    constants_text = (package_dir / "constants_v1.py").read_text(encoding="utf-8")
    for token in forbidden_true:
        if token in code_blob or token in constants_text:
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
        or not CANDIDATE_SCHEMA_CLOSED_WORLD
        or not UNKNOWN_FIELDS_REJECTED
        or not UNKNOWN_AUTHORITY_FIELDS_REJECTED
        or not CANDIDATE_SCHEMA_VERSION_EXACT_MATCH
        or not VENUE_VALUE_EXACT_MATCH
        or not INSTRUMENT_VALUE_EXACT_MATCH
        or not NETWORK_SCOPE_VALUE_EXACT_MATCH
        or not SESSION_SCOPE_VALUE_EXACT_MATCH
        or not BINDING_VALUE_NORMALIZATION_FORBIDDEN
        or not NESTED_OBJECTS_PRESENT
    ):
        raise RuntimeError("CAPABILITY_GUARD_DRIFT")

    for required_token in (
        "unknown_candidate_fields",
        "candidate_schema_version_mismatch",
        "venue_binding_mismatch",
        "instrument_binding_mismatch",
        "network_scope_binding_mismatch",
        "session_scope_binding_mismatch",
        "CANDIDATE_SCHEMA_VERSION",
        "EXPECTED_VENUE",
        "EXPECTED_INSTRUMENT",
        "EXPECTED_NETWORK_SCOPE",
        "EXPECTED_SESSION_SCOPE",
        "_ALLOWED_TOP_LEVEL",
    ):
        if required_token not in validate_text:
            raise RuntimeError(f"VALIDATOR_HARDENING_TOKEN_MISSING:{required_token}")

    if len(EXISTING_EXHAUSTED_SESSION_IDS) != 2:
        raise RuntimeError("EXHAUSTED_SESSION_ID_COUNT_DRIFT")

    artifact = verify_additional_evidence_session_preregistration_contract_artifact_v1(
        repo_root=root
    )
    if artifact.get("candidate_schema_version") != CANDIDATE_SCHEMA_VERSION:
        raise RuntimeError("ARTIFACT_CANDIDATE_SCHEMA_VERSION_DRIFT")
    if artifact.get("expected_venue") != EXPECTED_VENUE:
        raise RuntimeError("ARTIFACT_VENUE_BINDING_DRIFT")
    if artifact.get("expected_instrument") != EXPECTED_INSTRUMENT:
        raise RuntimeError("ARTIFACT_INSTRUMENT_BINDING_DRIFT")
    if artifact.get("expected_network_scope") != EXPECTED_NETWORK_SCOPE:
        raise RuntimeError("ARTIFACT_NETWORK_SCOPE_BINDING_DRIFT")
    if artifact.get("expected_session_scope") != EXPECTED_SESSION_SCOPE:
        raise RuntimeError("ARTIFACT_SESSION_SCOPE_BINDING_DRIFT")
    if artifact.get("candidate_schema_closed_world") is not True:
        raise RuntimeError("ARTIFACT_CLOSED_WORLD_DRIFT")
    if artifact.get("hardening_capability_id") != HARDENING_CAPABILITY_ID:
        raise RuntimeError("ARTIFACT_HARDENING_CAPABILITY_DRIFT")

    for rel in (SPEC_RELATIVE_PATH, HARDENING_SPEC_RELATIVE_PATH):
        spec_path = root / rel
        if not spec_path.is_file():
            raise RuntimeError(f"SPEC_MISSING:{rel}")
        spec_text = spec_path.read_text(encoding="utf-8")
        if rel == SPEC_RELATIVE_PATH:
            if "CONTRACT_CAPABILITY_MERGE" not in spec_text:
                raise RuntimeError("OPERATOR_WORKFLOW_MISSING_FROM_SPEC")
            if "CREATE_ADDITIONAL_SESSION_PREREGISTRATION" not in spec_text:
                raise RuntimeError("OPERATOR_WORKFLOW_INCOMPLETE")
        if rel == HARDENING_SPEC_RELATIVE_PATH:
            for marker in (
                "VALIDATOR_POLICY=FAIL_CLOSED",
                "CANDIDATE_SCHEMA_POLICY=CLOSED_WORLD",
                "UNKNOWN_FIELDS_REJECTED=true",
                "UNKNOWN_AUTHORITY_FIELDS_REJECTED=true",
                "CANDIDATE_SCHEMA_VERSION_EXACT_MATCH=true",
                "VENUE_VALUE_EXACT_MATCH=true",
                "INSTRUMENT_VALUE_EXACT_MATCH=true",
                "NETWORK_SCOPE_VALUE_EXACT_MATCH=true",
                "SESSION_SCOPE_VALUE_EXACT_MATCH=true",
                "NORMALIZATION_OF_BINDING_VALUES_FORBIDDEN=true",
                "HARD_STOP=true",
            ):
                if marker not in spec_text:
                    raise RuntimeError(f"HARDENING_SPEC_MARKER_MISSING:{marker}")

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
        "hardening_capability_id": HARDENING_CAPABILITY_ID,
        "artifact_path": ARTIFACT_RELATIVE_PATH,
        "contract_digest": artifact.get("contract_digest"),
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_schema_closed_world": True,
        "nested_objects_present": True,
        "unknown_fields_rejected": True,
        "unknown_authority_fields_rejected": True,
        "SESSION_PREREGISTRATION_CREATION_AUTHORIZED": False,
        "AUTHORIZATION_ISSUANCE_AUTHORIZED": False,
        "PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED": False,
        "SECOND_AGE_AUTHORITY_PRESENT": False,
        "SECOND_DECISION_AUTHORITY_PRESENT": False,
        "HARD_STOP": True,
    }
