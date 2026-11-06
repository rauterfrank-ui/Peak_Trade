from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONFIG_PATH = Path(
    "config/research/post_pr4909_terminal_failure_next_evidence_scope_definition_v0.json"
)
DOC_PATH = Path("docs/governance/POST_PR4909_TERMINAL_FAILURE_NEXT_EVIDENCE_SCOPE_DEFINITION_V0.md")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_scope_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def validate_scope_config(config: dict) -> list[str]:
    errors: list[str] = []

    if config.get("scope_id") != "POST_PR4909_TERMINAL_FAILURE_NEXT_EVIDENCE_SCOPE_DEFINITION_V0":
        errors.append("unexpected scope_id")

    if (
        config.get("next_scope_definition", {}).get("recommended_scope_class")
        != "OFFLINE_ONLY_SOURCE_EVIDENCE_INSTRUMENTATION_OR_ADMISSIBILITY_GAP_DEFINITION_V0"
    ):
        errors.append("unexpected recommended_scope_class")

    flags = config.get("authority_flags", {})
    for key, value in flags.items():
        if value is not False:
            errors.append(f"authority flag must be false: {key}")

    forbidden = set(
        config.get("next_scope_definition", {}).get("explicitly_not_authorized_in_this_scope", [])
    )
    required_forbidden = {
        "economic_evaluation_execution",
        "binding_retry",
        "parameter_optimization",
        "threshold_lowering",
        "historical_failure_reclassification",
        "runtime_rewire",
        "shadow",
        "paper",
        "testnet",
        "scheduler",
        "adapter_submission",
        "orders",
        "credentials",
        "arming",
        "canary",
        "live",
    }
    missing = sorted(required_forbidden - forbidden)
    if missing:
        errors.append(f"missing forbidden actions: {missing}")

    missing_source = config.get("terminal_failure_materialization_summary", {}).get(
        "missing_source_evidence", []
    )
    if len(missing_source) != 7:
        errors.append("expected seven missing source evidence entries")

    if (
        config.get("terminal_failure_materialization_summary", {}).get(
            "failed_evidence_is_terminal"
        )
        is not True
    ):
        errors.append("failed_evidence_is_terminal must be true")

    return errors


def main() -> int:
    config = load_scope_config()
    errors = validate_scope_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("VERDICT=SCOPE_DEFINED_NOT_EXECUTED")
    print(f"CONFIG_SHA256={sha256_path(CONFIG_PATH)}")
    print(f"DOC_SHA256={sha256_path(DOC_PATH)}")
    print(f"NEXT_STEP={config['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
