#!/usr/bin/env python3
"""Validate Pure-Stack Stage-2 numeric policy Evidence packs (fail-closed).

Read-only validator for scaffolding and later shadow calibration Evidence packs.
Does not authorize INPUT_AUTHORITY_*, productive numbers, runtime binding,
orders, Live, Testnet, dashboard authority, or archive mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

VALIDATOR_CONTRACT = "productive_pure_stack_numeric_policy_evidence_pack_validator_v1"
SCHEMA_VERSION = "productive_pure_stack_numeric_policy_evidence_pack/v1"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"

STAGE1_MANIFEST_REL = Path(
    "docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json"
)
CALIBRATION_PROTOCOL_REL = Path(
    "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md"
)

STAGE2_TOKENS: tuple[str, ...] = (
    "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS",
    "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT",
    "OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE",
    "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE",
    "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE",
)

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "campaign_id",
    "campaign_status",
    "origin_main_sha",
    "stage1_manifest_digest",
    "calibration_protocol_digest",
    "sole_trading_authority_symbol",
    "observation_identity",
    "producer_identity",
    "dataset_manifest",
    "train_calibration_validation_partition_manifest",
    "walk_forward_manifest",
    "bootstrap_monte_carlo_manifest",
    "stress_pack_manifest",
    "metric_definition_digests",
    "per_token_evidence",
    "acceptance_gate_results",
    "rejection_reasons",
    "owner_ratification_status",
    "productive_numeric_values_set",
    "evidence_complete",
    "owner_ratified",
    "input_authority",
    "runtime_implemented",
    "dashboard_role",
    "forbidden_authority_declarations",
)

PARTITION_KEYS = (
    "train_calibration_validation_partition_manifest",
    "walk_forward_manifest",
    "bootstrap_monte_carlo_manifest",
    "stress_pack_manifest",
    "dataset_manifest",
)

FORBIDDEN_AUTHORITY_MARKERS = (
    "fixture",
    "scenario",
    "webui",
    "dashboard",
    "cmc.volatility_estimate",
    "cmc_volatility_estimate",
    "survivalresultv1",
    "suitabilityresultv1",
    "archive_authority",
)

FORBIDDEN_DECLARATION_KEYS = (
    "fixture_scenario_webui_as_authority",
    "cmc_volatility_estimate_as_realized_volatility",
    "survival_result_v1_as_numeric_authority",
    "suitability_result_v1_as_numeric_authority",
    "dashboard_as_authority",
    "archive_as_authority",
    "reinvest_fraction_independent_numeric",
    "capital_slot_time_quantum_wallclock_seconds",
    "initial_slot_base_from_account_equity",
)


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _contains_forbidden_authority(text: str) -> str | None:
    lowered = text.lower()
    for marker in FORBIDDEN_AUTHORITY_MARKERS:
        if marker in lowered:
            return marker
    return None


def _manifest_incomplete(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return True
    status = manifest.get("status")
    populated = manifest.get("populated")
    entries = manifest.get("entries")
    if status not in {"EMPTY_SCAFFOLD", "DECLARED", "COMPLETE"}:
        return True
    if not isinstance(entries, list):
        return True
    if status == "EMPTY_SCAFFOLD":
        return populated is not False or len(entries) != 0
    if status == "DECLARED":
        return populated is not True or len(entries) == 0
    if status == "COMPLETE":
        return populated is not True or len(entries) == 0 or not manifest.get("digest")
    return True


def validate_pack(
    pack: dict[str, Any],
    *,
    repo_root: Path | None = None,
    expected_origin_main_sha: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    root = repo_root or repo_root_from_here()

    if not isinstance(pack, dict):
        return {
            "contract": VALIDATOR_CONTRACT,
            "ok": False,
            "errors": ["pack_must_be_object"],
            "token_count": 0,
            "productive_numeric_values_set": None,
            "input_authority": None,
            "runtime_implemented": None,
            "non_authorizing": True,
        }

    for key in REQUIRED_TOP_LEVEL:
        if key not in pack:
            errors.append(f"missing_top_level:{key}")

    if pack.get("schema_version") != SCHEMA_VERSION:
        errors.append("invalid_schema_version")

    if pack.get("sole_trading_authority_symbol") != SOLE_TRADING_AUTHORITY:
        errors.append("invalid_sole_trading_authority_symbol")

    if pack.get("dashboard_role") != "READ_ONLY_CONSUMER":
        errors.append("dashboard_must_be_read_only_consumer")

    if pack.get("input_authority") is not False:
        errors.append("input_authority_must_be_false")

    if pack.get("runtime_implemented") is not False:
        errors.append("runtime_implemented_must_be_false")

    if pack.get("productive_numeric_values_set") != 0:
        errors.append("productive_numeric_values_set_must_be_0")

    if pack.get("evidence_complete") is not False and pack.get("campaign_status") == "NOT_STARTED":
        errors.append("not_started_must_have_evidence_complete_false")

    if pack.get("owner_ratified") is not False and pack.get("campaign_status") == "NOT_STARTED":
        errors.append("not_started_must_have_owner_ratified_false")

    stage1_path = root / STAGE1_MANIFEST_REL
    protocol_path = root / CALIBRATION_PROTOCOL_REL
    if not stage1_path.is_file():
        errors.append("missing_stage1_manifest_file")
    if not protocol_path.is_file():
        errors.append("missing_calibration_protocol_file")

    stage1_digest = pack.get("stage1_manifest_digest")
    protocol_digest = pack.get("calibration_protocol_digest")
    if not isinstance(stage1_digest, str) or len(stage1_digest) != 64:
        errors.append("missing_or_invalid_stage1_manifest_digest")
    elif stage1_path.is_file() and stage1_digest != sha256_file(stage1_path):
        errors.append("stage1_manifest_digest_mismatch")

    if not isinstance(protocol_digest, str) or len(protocol_digest) != 64:
        errors.append("missing_or_invalid_calibration_protocol_digest")
    elif protocol_path.is_file() and protocol_digest != sha256_file(protocol_path):
        errors.append("calibration_protocol_digest_mismatch")

    if expected_origin_main_sha is not None:
        if pack.get("origin_main_sha") != expected_origin_main_sha:
            errors.append("origin_main_sha_mismatch")

    decls = pack.get("forbidden_authority_declarations")
    if not isinstance(decls, dict):
        errors.append("missing_forbidden_authority_declarations")
    else:
        for key in FORBIDDEN_DECLARATION_KEYS:
            if decls.get(key) is not False:
                errors.append(f"forbidden_authority_declaration_not_false:{key}")

    # Completeness: empty scaffold OK for NOT_STARTED; otherwise reject incomplete.
    campaign_status = pack.get("campaign_status")
    completeness_required = campaign_status not in {"NOT_STARTED", "REJECTED_FAIL_CLOSED"} or bool(
        pack.get("evidence_complete")
    )
    for key in PARTITION_KEYS:
        manifest = pack.get(key)
        incomplete = _manifest_incomplete(manifest)
        if completeness_required and incomplete:
            errors.append(f"incomplete_manifest:{key}")
        if campaign_status == "NOT_STARTED":
            if not isinstance(manifest, dict):
                errors.append(f"incomplete_manifest:{key}")
            elif (
                manifest.get("status") != "EMPTY_SCAFFOLD" or manifest.get("populated") is not False
            ):
                # NOT_STARTED may only carry empty scaffolds.
                if incomplete:
                    errors.append(f"incomplete_manifest:{key}")

    if pack.get("evidence_complete") is True:
        for key in PARTITION_KEYS:
            if _manifest_incomplete(pack.get(key)) or (
                isinstance(pack.get(key), dict) and pack[key].get("status") != "COMPLETE"
            ):
                errors.append(f"incomplete_manifest:{key}")

    rows = pack.get("per_token_evidence")
    if not isinstance(rows, list):
        errors.append("per_token_evidence_must_be_list")
        rows = []

    tokens = [row.get("token") for row in rows if isinstance(row, dict)]
    token_set = {t for t in tokens if isinstance(t, str)}
    expected = set(STAGE2_TOKENS)

    if len(rows) != 18 or token_set != expected:
        missing = sorted(expected - token_set)
        unknown = sorted(token_set - expected)
        if missing:
            errors.append("missing_tokens:" + ",".join(missing))
        if unknown:
            errors.append("unknown_tokens:" + ",".join(unknown))
        if len(rows) != 18:
            errors.append(f"token_count_must_be_18_got_{len(rows)}")

    if "OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION" in token_set:
        errors.append("independent_reinvest_fraction_token_forbidden")

    productive_set_count = 0
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"per_token_row_not_object:{idx}")
            continue

        token = row.get("token")
        if row.get("productive_numeric_value") is not None:
            errors.append(f"productive_numeric_value_must_be_null:{token}")
            productive_set_count += 1

        if row.get("input_authority") is not False:
            errors.append(f"input_authority_must_be_false:{token}")

        if row.get("runtime_implemented") is not False:
            errors.append(f"runtime_implemented_must_be_false:{token}")

        for field in ("authority_source", "derivation_source"):
            marker = _contains_forbidden_authority(_norm(row.get(field)))
            if marker:
                if marker in {"fixture", "scenario", "webui", "dashboard"}:
                    errors.append(
                        f"forbidden_fixture_webui_cmc_dashboard_authority:{token}:{field}"
                    )
                if marker in {"cmc.volatility_estimate", "cmc_volatility_estimate"}:
                    errors.append(f"cmc_volatility_estimate_as_realized_volatility:{token}")
                if marker == "survivalresultv1":
                    errors.append(f"survival_result_v1_as_numeric_authority:{token}")
                if marker == "suitabilityresultv1":
                    errors.append(f"suitability_result_v1_as_numeric_authority:{token}")

        authority_blob = " ".join(
            [
                _norm(row.get("authority_source")),
                _norm(row.get("derivation_source")),
            ]
        )
        if (
            (
                "cmc.volatility_estimate" in authority_blob
                or "cmc_volatility_estimate" in authority_blob
            )
            and "realized" in authority_blob
            and " not " not in f" {authority_blob} "
        ):
            errors.append(f"cmc_volatility_estimate_as_realized_volatility:{token}")
        compact = authority_blob.replace("_", "").replace(" ", "")
        if "survivalresultv1" in compact:
            errors.append(f"survival_result_v1_as_numeric_authority:{token}")
        if "suitabilityresultv1" in compact:
            errors.append(f"suitability_result_v1_as_numeric_authority:{token}")

        if token == "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP":
            quantum_blob = " ".join(
                [
                    _norm(row.get("derivation_source")),
                    _norm(row.get("authority_source")),
                    _norm(row.get("allowed_calibration_output_type")),
                ]
            )
            if "wallclock" in quantum_blob or "wall_clock" in quantum_blob:
                errors.append("capital_slot_time_quantum_wallclock_seconds")
            if row.get("allowed_calibration_output_type") == "THRESHOLD_SECONDS":
                errors.append("capital_slot_time_quantum_wallclock_seconds")

        if token == "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE":
            derive = _norm(row.get("derivation_source"))
            if "account_equity" in derive or "account-equity" in derive:
                errors.append("initial_slot_base_from_account_equity")

        if token == "OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION":
            if _norm(row.get("derivation_source")) in {
                "independent_reinvest_fraction",
                "reinvest_fraction_independent",
            }:
                errors.append("independent_reinvest_fraction_value")
            if row.get("productive_numeric_value") is not None and (
                "reinvest" in _norm(row.get("authority_source"))
            ):
                errors.append("independent_reinvest_fraction_value")

    # Pack-level independent REINVEST / quantum / equity claims via declarations.
    # Mentioning the mechanical-coupling token as a dependency is allowed.
    if decls and decls.get("reinvest_fraction_independent_numeric") is True:
        errors.append("independent_reinvest_fraction_value")
    if decls and decls.get("capital_slot_time_quantum_wallclock_seconds") is True:
        errors.append("capital_slot_time_quantum_wallclock_seconds")
    if decls and decls.get("initial_slot_base_from_account_equity") is True:
        errors.append("initial_slot_base_from_account_equity")

    # Observation identity must stay Sole-Trading-Authority bound
    obs = pack.get("observation_identity")
    if isinstance(obs, dict):
        if obs.get("sole_consumer_authority") != SOLE_TRADING_AUTHORITY:
            errors.append("observation_identity_sole_consumer_mismatch")

    producer = pack.get("producer_identity")
    if isinstance(producer, dict) and producer.get("productive_activation") is not False:
        errors.append("producer_productive_activation_must_be_false")

    unique_errors = sorted(set(errors))
    return {
        "contract": VALIDATOR_CONTRACT,
        "ok": not unique_errors,
        "errors": unique_errors,
        "token_count": len(token_set),
        "expected_token_count": 18,
        "productive_numeric_values_set": productive_set_count,
        "input_authority": pack.get("input_authority"),
        "runtime_implemented": pack.get("runtime_implemented"),
        "campaign_status": pack.get("campaign_status"),
        "non_authorizing": True,
    }


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("json_root_must_be_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed validator for Pure-Stack Stage-2 numeric policy Evidence packs. "
            "Non-authorizing. No runtime/archive/dashboard mutation."
        )
    )
    parser.add_argument(
        "--pack-json",
        type=Path,
        required=True,
        help="Path to Evidence pack / campaign manifest JSON",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root for Stage-1/protocol digest checks",
    )
    parser.add_argument(
        "--expected-origin-main-sha",
        type=str,
        default=None,
        help="Optional exact origin/main SHA pin",
    )
    args = parser.parse_args(argv)

    try:
        pack = load_json(args.pack_json)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        payload = {
            "contract": VALIDATOR_CONTRACT,
            "ok": False,
            "errors": [f"pack_load_error:{exc}"],
            "non_authorizing": True,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    result = validate_pack(
        pack,
        repo_root=args.repo_root or repo_root_from_here(),
        expected_origin_main_sha=args.expected_origin_main_sha,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
