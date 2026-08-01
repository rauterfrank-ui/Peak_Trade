"""Architecture guards for additional-evidence authorization v2 authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    ADDITIONAL_EVIDENCE_AUTHORIZATION_V2_SOLE_ISSUANCE_AUTHORITY,
    ARTIFACT_RELATIVE_PATH,
    CAMPAIGN_AUTHORIZATION_V1_UNCHANGED,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    NO_SECOND_ISSUANCE_AUTHORITY,
    READY_FOR_AUTHORIZATION_ISSUANCE_CONSTANT,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    SPEC_RELATIVE_PATH,
    WALLCLOCK_AUTHORIZATION_WRITER_UNCHANGED,
)


def assert_architecture_guards_v2(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / (
        "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
        "session_authorization_v2"
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
    imports_blob = "\n".join(import_lines)
    code_blob = "\n".join(code_parts)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")
    for side_effect in ("requests.get", "urllib.request", "socket."):
        if side_effect in code_blob:
            raise RuntimeError(f"NETWORK_SIDE_EFFECT_FORBIDDEN:{side_effect}")

    if not ADDITIONAL_EVIDENCE_AUTHORIZATION_V2_SOLE_ISSUANCE_AUTHORITY:
        raise RuntimeError("SOLE_AUTHORITY_DRIFT")
    if not WALLCLOCK_AUTHORIZATION_WRITER_UNCHANGED:
        raise RuntimeError("WALLCLOCK_WRITER_MUTATION_FLAG_DRIFT")
    if not CAMPAIGN_AUTHORIZATION_V1_UNCHANGED:
        raise RuntimeError("CAMPAIGN_V1_MUTATION_FLAG_DRIFT")
    if not NO_SECOND_ISSUANCE_AUTHORITY:
        raise RuntimeError("SECOND_AUTHORITY_FLAG_DRIFT")
    if READY_FOR_AUTHORIZATION_ISSUANCE_CONSTANT or READY_FOR_PRODUCTIVE_SESSION_EXECUTION:
        raise RuntimeError("CAPABILITY_READY_FLAG_DRIFT")
    if not HARD_STOP:
        raise RuntimeError("HARD_STOP_DRIFT")

    # Ensure wallclock writer constants remain strict.
    from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
        AUTHORIZED_NETWORK_SCOPE,
        REQUIRED_SESSION_DURATION_SECONDS,
    )

    if AUTHORIZED_NETWORK_SCOPE != "PUBLIC_MARKET_DATA_ONLY":
        raise RuntimeError("WALLCLOCK_NETWORK_SCOPE_DRIFT")
    if REQUIRED_SESSION_DURATION_SECONDS != 3600:
        raise RuntimeError("WALLCLOCK_DURATION_DRIFT")

    from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
        PRODUCTIVE_ISSUANCE_IN_THIS_CAPABILITY,
        SCHEMA_VERSION as CAMPAIGN_SCHEMA,
    )

    if PRODUCTIVE_ISSUANCE_IN_THIS_CAPABILITY is not False:
        raise RuntimeError("CAMPAIGN_V1_ISSUANCE_REACTIVATED")
    if not str(CAMPAIGN_SCHEMA).endswith("/v1"):
        raise RuntimeError("CAMPAIGN_SCHEMA_DRIFT")

    artifact = root / ARTIFACT_RELATIVE_PATH
    if not artifact.is_file():
        raise RuntimeError(f"CONTRACT_ARTIFACT_MISSING:{ARTIFACT_RELATIVE_PATH}")
    spec = root / SPEC_RELATIVE_PATH
    if not spec.is_file():
        raise RuntimeError(f"SPEC_MISSING:{SPEC_RELATIVE_PATH}")
    for marker in (
        "ADDITIONAL_EVIDENCE_AUTHORIZATION_V2_SOLE_ISSUANCE_AUTHORITY=true",
        "WALLCLOCK_AUTHORIZATION_WRITER_UNCHANGED=true",
        "CAMPAIGN_AUTHORIZATION_V1_UNCHANGED=true",
        "CONSUME_BEFORE_SESSION_LOCK=true",
        "REQUIRED_DURATION_SECONDS=10860",
        "REQUIRED_NETWORK_SCOPE=OKX_EEA_FUTURES_PUBLIC_MARKET_DATA_READ_ONLY",
        "HARD_STOP=true",
        "AUTHORIZATION_ISSUED=false",
    ):
        if marker not in spec.read_text(encoding="utf-8"):
            raise RuntimeError(f"SPEC_MARKER_MISSING:{marker}")

    return {
        "guards_pass": True,
        "sole_issuance_authority": True,
        "wallclock_writer_unchanged": True,
        "campaign_v1_unchanged": True,
        "hard_stop": True,
        "artifact_path": ARTIFACT_RELATIVE_PATH,
        "spec_path": SPEC_RELATIVE_PATH,
    }
