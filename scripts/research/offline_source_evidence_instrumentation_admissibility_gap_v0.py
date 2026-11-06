from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONFIG_PATH = Path(
    "config/research/offline_source_evidence_instrumentation_admissibility_gap_v0.json"
)
DOC_PATH = Path("docs/governance/OFFLINE_SOURCE_EVIDENCE_INSTRUMENTATION_ADMISSIBILITY_GAP_V0.md")


REQUIRED_CONTRACTS = {
    "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
    "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
    "TURNOVER_COST_DRAG_TIMESERIES_V0",
    "INSTRUMENT_CONCENTRATION_DETAIL_V0",
}

FORBIDDEN_ACTIONS = {
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


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []

    if (
        config.get("scope_id")
        != "OFFLINE_SOURCE_EVIDENCE_INSTRUMENTATION_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_V0"
    ):
        errors.append("unexpected scope_id")

    contracts = {item.get("contract_id") for item in config.get("source_evidence_contracts", [])}
    missing_contracts = sorted(REQUIRED_CONTRACTS - contracts)
    if missing_contracts:
        errors.append(f"missing contracts: {missing_contracts}")

    for item in config.get("source_evidence_contracts", []):
        fields = item.get("required_fields", [])
        if "manifest_ref" not in fields:
            errors.append(f"manifest_ref missing from {item.get('contract_id')}")
        if len(fields) < 10:
            errors.append(f"contract has too few required fields: {item.get('contract_id')}")

    admissibility = config.get("future_evaluation_admissibility_requirements", {})
    for key in [
        "economic_claim_requires_all_contracts_present",
        "missing_contract_blocks_promotion_claim",
        "missing_contract_does_not_reclassify_historical_terminal_failure",
        "failed_evidence_is_terminal",
        "manifest_sha256_required",
        "config_digest_required",
        "implementation_digest_required",
        "data_digest_required",
    ]:
        if admissibility.get(key) is not True:
            errors.append(f"admissibility requirement must be true: {key}")

    forbidden = set(config.get("explicitly_not_authorized", []))
    missing_forbidden = sorted(FORBIDDEN_ACTIONS - forbidden)
    if missing_forbidden:
        errors.append(f"missing forbidden actions: {missing_forbidden}")

    flags = config.get("authority_flags", {})
    for key, value in flags.items():
        if value is not False:
            errors.append(f"authority flag must be false: {key}")

    return errors


def main() -> int:
    config = load_config()
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "VERDICT=OFFLINE_SOURCE_EVIDENCE_INSTRUMENTATION_ADMISSIBILITY_GAP_DEFINITION_EXECUTED_V0"
    )
    print(f"CONFIG_SHA256={sha256_path(CONFIG_PATH)}")
    print(f"DOC_SHA256={sha256_path(DOC_PATH)}")
    print(f"NEXT_STEP={config['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
