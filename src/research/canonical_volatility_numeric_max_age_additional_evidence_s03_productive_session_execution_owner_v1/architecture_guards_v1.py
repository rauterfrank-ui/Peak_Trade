"""Architecture guards for S03 productive session execution owner v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    ARTIFICIAL_DELAY_FOR_AGE_CREATION,
    AUTH_V2_IS_SOLE_SESSION_AUTHORITY,
    AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY,
    BOUND_DURATION_SECONDS,
    CONSUME_BEFORE_SIDE_EFFECTS,
    CONTRACT_RELATIVE_PATH,
    CURRENT_AUTHORIZATION_REQUIRES_SEPARATE_REVOCATION_AND_REISSUANCE,
    EXISTING_CLI_OWNER,
    EXISTING_S01_S02_RUNNER_CLI_MODE,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    NO_SECOND_DECISION_AUTHORITY,
    NO_SECOND_EXECUTION_AUTHORITY,
    NUMERIC_MAX_AGE_SELECTED,
    PACKAGE_RELATIVE_DIR,
    POLICY_ENFORCEMENT_ADDED,
    PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY,
    READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION,
    REAL_NETWORK_IN_THIS_CAPABILITY,
    SPEC_RELATIVE_PATH,
    SYNTHETIC_TIMESTAMP_AGING,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / PACKAGE_RELATIVE_DIR
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
    imports_blob = "\n".join(import_lines)
    code_blob = "\n".join(code_parts)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")
    for side_effect in ("requests.get(", "urllib.request.urlopen", "socket.create_connection"):
        if side_effect in code_blob:
            raise RuntimeError(f"NETWORK_SIDE_EFFECT_FORBIDDEN:{side_effect}")

    if not NO_SECOND_EXECUTION_AUTHORITY:
        raise RuntimeError("SECOND_EXECUTION_AUTHORITY_FLAG_DRIFT")
    if not NO_SECOND_DECISION_AUTHORITY:
        raise RuntimeError("SECOND_DECISION_AUTHORITY_FLAG_DRIFT")
    if not AUTH_V2_IS_SOLE_SESSION_AUTHORITY:
        raise RuntimeError("AUTH_V2_SOLE_AUTHORITY_FLAG_DRIFT")
    if not CONSUME_BEFORE_SIDE_EFFECTS:
        raise RuntimeError("CONSUME_BEFORE_SIDE_EFFECTS_FLAG_DRIFT")
    if not PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY:
        raise RuntimeError("PRODUCTIVE_EXECUTION_NOT_ENABLED")
    if not REAL_NETWORK_IN_THIS_CAPABILITY:
        raise RuntimeError("REAL_NETWORK_NOT_ENABLED")
    if not AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY:
        raise RuntimeError("AUTHORIZATION_CONSUMPTION_NOT_ENABLED")
    if not READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION:
        raise RuntimeError("READY_FOR_EXECUTION_NOT_ENABLED")
    if NUMERIC_MAX_AGE_SELECTED or POLICY_ENFORCEMENT_ADDED:
        raise RuntimeError("POLICY_SELECTION_FLAG_DRIFT")
    if ARTIFICIAL_DELAY_FOR_AGE_CREATION or SYNTHETIC_TIMESTAMP_AGING:
        raise RuntimeError("ARTIFICIAL_AGING_FLAG_DRIFT")
    if int(BOUND_DURATION_SECONDS) != 10860:
        raise RuntimeError("DURATION_BINDING_DRIFT")
    if not HARD_STOP:
        raise RuntimeError("HARD_STOP_DRIFT")
    if not CURRENT_AUTHORIZATION_REQUIRES_SEPARATE_REVOCATION_AND_REISSUANCE:
        raise RuntimeError("CURRENT_AUTH_REISSUANCE_FLAG_DRIFT")

    # Existing S01/S02 runner remains the campaign-auth path; this owner is Auth-v2 S03 only.
    s01_runner = root / (
        "src/research/canonical_volatility_numeric_max_age_preregistered_"
        "productive_session_runner_v1/constants_v1.py"
    )
    if EXISTING_S01_S02_RUNNER_CLI_MODE not in s01_runner.read_text(encoding="utf-8"):
        raise RuntimeError("EXISTING_RUNNER_CLI_MODE_MISSING")

    orch = (package_dir / "orchestrator_v1.py").read_text(encoding="utf-8")
    if "consume_additional_evidence_session_authorization_v2" not in orch:
        raise RuntimeError("AUTH_V2_CONSUME_NOT_REUSED")
    if "consume_campaign_authorization_session_v1" in orch:
        raise RuntimeError("CAMPAIGN_AUTH_V1_CONSUME_USED_FORBIDDEN")
    if "read_confirm_token_interactively_v1" not in orch:
        raise RuntimeError("INTERACTIVE_CONFIRM_TOKEN_CHANNEL_MISSING")
    if "confirm_token_parameter_forbidden_on_real_path" not in orch:
        raise RuntimeError("REAL_PATH_TOKEN_PARAMETER_GUARD_MISSING")

    cli_path = root / EXISTING_CLI_OWNER
    cli_text = cli_path.read_text(encoding="utf-8")
    if "additional-evidence-s03-session-run" not in cli_text:
        raise RuntimeError("S03_CLI_MODE_MISSING")
    if "enable_real_s03_session_execution=True" not in cli_text:
        raise RuntimeError("CLI_REAL_PATH_NOT_ENABLED")
    if "offline_probe=False" not in cli_text:
        raise RuntimeError("CLI_OFFLINE_PROBE_DEFAULT_NOT_FALSE_FOR_REAL_PATH")
    if "--confirm-token" in cli_text:
        raise RuntimeError("CONFIRM_TOKEN_CLI_ARGUMENT_FORBIDDEN")

    token_mod = (package_dir / "confirm_token_stdin_v1.py").read_text(encoding="utf-8")
    if "getpass" not in token_mod:
        raise RuntimeError("GETPASS_TOKEN_CHANNEL_MISSING")

    artifact = root / CONTRACT_RELATIVE_PATH
    if not artifact.is_file():
        raise RuntimeError(f"CONTRACT_ARTIFACT_MISSING:{CONTRACT_RELATIVE_PATH}")
    contract_text = artifact.read_text(encoding="utf-8")
    for marker in (
        '"productive_session_execution_in_this_capability": true',
        '"real_network_in_this_capability": true',
        '"ready_for_s03_authorization_consumption_and_execution": true',
    ):
        if marker not in contract_text:
            raise RuntimeError(f"CONTRACT_ENABLEMENT_MARKER_MISSING:{marker}")

    spec = root / SPEC_RELATIVE_PATH
    if not spec.is_file():
        raise RuntimeError(f"SPEC_MISSING:{SPEC_RELATIVE_PATH}")
    spec_text = spec.read_text(encoding="utf-8")
    for marker in (
        "NO_SECOND_EXECUTION_AUTHORITY=true",
        "AUTH_V2_IS_SOLE_SESSION_AUTHORITY=true",
        "CONSUME_BEFORE_SIDE_EFFECTS=true",
        "REQUESTED_DURATION_SECONDS=10860",
        "MONOTONIC_DURATION_AUTHORITY=true",
        "PUBLIC_MARKET_DATA_ONLY=true",
        "COUNTERFACTUAL_RUNTIME_IS_NON_AUTHORITY=true",
        "PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY=true",
        "READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION=true",
        "CURRENT_AUTHORIZATION_REQUIRES_SEPARATE_REVOCATION_AND_REISSUANCE=true",
        "HARD_STOP=true",
    ):
        if marker not in spec_text:
            raise RuntimeError(f"SPEC_MARKER_MISSING:{marker}")

    return {
        "guards_pass": True,
        "no_second_execution_authority": True,
        "auth_v2_sole_session_authority": True,
        "consume_before_side_effects": True,
        "productive_execution_enabled": True,
        "cli_real_path_enabled": True,
        "confirm_token_cli_argument_absent": True,
        "hard_stop": True,
        "artifact_path": CONTRACT_RELATIVE_PATH,
        "spec_path": SPEC_RELATIVE_PATH,
    }
