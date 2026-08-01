"""Architecture guards for preregistered productive session runner capability."""

from __future__ import annotations

from pathlib import Path

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    CLI_MODE,
    CLI_REL_PATH,
    PACKAGE_MARKER,
    PRODUCTIVE_BRIDGE_ACCUMULATE_CLI_MODE,
    PUBLIC_MD_RATE_LIMIT_HARDENING_SPEC_REL_PATH,
    SPEC_REL_PATH,
)


def assert_preregistered_session_runner_architecture_v1(*, repo_root: Path) -> dict[str, bool]:
    root = Path(repo_root)
    package = (
        root
        / "src/research/canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1"
    )
    for name in (
        "__init__.py",
        "constants_v1.py",
        "models_v1.py",
        "preflight_v1.py",
        "public_md_source_v1.py",
        "public_md_rate_limit_policy_v1.py",
        "instrument_binding_v1.py",
        "runner_v1.py",
        "terminal_v1.py",
        "architecture_guards_v1.py",
    ):
        if not (package / name).is_file():
            raise RuntimeError(f"SESSION_RUNNER_MODULE_MISSING:{name}")

    constants = (package / "constants_v1.py").read_text(encoding="utf-8")
    if PACKAGE_MARKER.split("=")[0] not in constants:
        raise RuntimeError("SESSION_RUNNER_PACKAGE_MARKER_MISSING")
    if "PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY = False" not in constants:
        raise RuntimeError("SESSION_RUNNER_MUST_DECLARE_NO_EXECUTION_IN_CAPABILITY")

    runner = (package / "runner_v1.py").read_text(encoding="utf-8")
    if "consume_campaign_authorization_session_v1" not in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_USE_PRODUCTIVE_AUTH_CONSUMER")
    if "run_productive_bridge_accumulation_session_v1" not in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_USE_EXISTING_PRODUCTIVE_CONSUMER")
    if "deterministic_productive_mark_path_v1" in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_NOT_USE_OFFLINE_DETERMINISTIC_MARK_PATH")
    if "PREFLIGHT_PASS" not in runner or "AUTHORIZATION_CONSUMED" not in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_ORDER_PREFLIGHT_BEFORE_CONSUMPTION")
    if "resolve_preregistered_session_venue_instrument_v1" not in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_RESOLVE_VENUE_INSTRUMENT_BINDING")
    if "initialize_session_md_controls_v1" not in runner:
        raise RuntimeError("SESSION_RUNNER_MUST_INITIALIZE_REQUEST_PACING_BUDGET")

    policy = (package / "public_md_rate_limit_policy_v1.py").read_text(encoding="utf-8")
    if "PublicMdRequestPacingPolicyV1" not in policy:
        raise RuntimeError("SESSION_RUNNER_PACING_POLICY_MISSING")
    if "minimum_interval_seconds" not in policy:
        raise RuntimeError("SESSION_RUNNER_PACING_MINIMUM_INTERVAL_MISSING")

    cli = (root / CLI_REL_PATH).read_text(encoding="utf-8")
    if CLI_MODE not in cli:
        raise RuntimeError("CLI_MUST_EXPOSE_PREREGISTERED_SESSION_RUN_MODE")
    if PRODUCTIVE_BRIDGE_ACCUMULATE_CLI_MODE not in cli:
        raise RuntimeError("CLI_MUST_RETAIN_PRODUCTIVE_BRIDGE_ACCUMULATE_MODE")

    if not (root / SPEC_REL_PATH).is_file():
        raise RuntimeError("SESSION_RUNNER_SPEC_MISSING")
    if not (root / PUBLIC_MD_RATE_LIMIT_HARDENING_SPEC_REL_PATH).is_file():
        raise RuntimeError("SESSION_RUNNER_RATE_LIMIT_HARDENING_SPEC_MISSING")

    return {
        "package_present": True,
        "cli_mode_present": True,
        "consume_before_side_effects": True,
        "offline_mark_path_absent": True,
        "spec_present": True,
        "rate_limit_hardening_spec_present": True,
    }
