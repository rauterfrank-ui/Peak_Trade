"""Production PIT universe manifest dataset/period/instrument binding contract v0.

Deterministic, fail-closed staging bindings for final_research_fleet_v0 candidates
(trend_following/v1, bollinger_bands/v1, momentum_1h/v1) wired to the production
materialized point-in-time OKX futures universe manifest from PR #4782.

Research-only, non-authorizing. No economic evaluation, no runtime or order effect.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.strategy_signal_binding_v1 import (
    collect_configured_strategy_params_v1,
    resolve_effective_strategy_params_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    ECONOMIC_POLICY_VERSION,
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
    compute_config_digest_v1,
    load_step31f_evaluation_config_v0,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    EVALUATION_PERIOD_BINDING,
    FUTURES_ONLY,
    ProductionManifestMaterializationEnvelopeV1,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
)
from src.research.pit_futures_universe_manifest_v1 import (
    PointInTimeFuturesUniverseManifestV1,
    compute_manifest_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
    manifest_from_dict,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict as ManifestValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import BAR_GRANULARITY, PANEL_DATASET_VERSION
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_DATASET_PERIOD_BINDING_V0=true"

SCHEMA_VERSION = "pit_futures_universe_manifest_dataset_period_binding.v0"
CONTRACT_ID = "pit_futures_universe_manifest_dataset_period_binding_v0"
CANONICAL_SERIALIZATION_VERSION = "research_binding_manifest_canonical_json_v1"
POLICY_CONFIG_REL_PATH = (
    "config/research/pit_futures_universe_manifest_dataset_period_binding_policy_v1.json"
)

CANDIDATE_BINDING_VERSION = "v0"
DATASET_BINDING_VERSION = "v0"
PERIOD_BINDING_VERSION = "v0"
INSTRUMENT_BINDING_VERSION = "v0"
FLEET_ID = "final_research_fleet_v0"
FLEET_VERSION = "v0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

DATASET_PROFILE = "cross_sectional_research_staging_v1"
INSTRUMENT_BINDING_MODE = "production_universe_manifest_cross_sectional"
INSTRUMENT_SELECTION_OWNER = "production_pit_universe_manifest_v1"

NOT_YET_MATERIALIZED = {"status": "NOT_YET_MATERIALIZED"}
BINDING_STATUS_NOT_READY = "NOT_READY"

FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")

REASON_UNKNOWN_STRATEGY = "UNKNOWN_STRATEGY"
REASON_WRONG_STRATEGY_VERSION = "WRONG_STRATEGY_VERSION"
REASON_MISSING_CANDIDATE = "MISSING_FLEET_CANDIDATE"
REASON_EXTRA_CANDIDATE = "EXTRA_FLEET_CANDIDATE"
REASON_DUPLICATE_CANDIDATE = "DUPLICATE_FLEET_CANDIDATE"
REASON_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
REASON_UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
REASON_MANIFEST_NOT_OBJECT = "CONTRACT_NOT_OBJECT"
REASON_EFFECT_NOT_NONE = "AUTHORITY_RUNTIME_ORDER_EFFECT_NOT_NONE"
REASON_WRONG_CONTRACT_DIGEST = "WRONG_CONTRACT_DIGEST"
REASON_NON_CANONICAL_SERIALIZATION = "NON_CANONICAL_SERIALIZATION"
REASON_BINDING_REPAIR_REJECTED = "BINDING_REPAIR_REJECTED"
REASON_SHARED_BINDING_MISMATCH = "SHARED_BINDING_MISMATCH"
REASON_PRODUCTION_MANIFEST_DIGEST_MISMATCH = "PRODUCTION_MANIFEST_DIGEST_MISMATCH"
REASON_PRODUCTION_MANIFEST_REF_MISMATCH = "PRODUCTION_MANIFEST_REF_MISMATCH"
REASON_UNKNOWN_UNIVERSE_POLICY = "UNKNOWN_UNIVERSE_POLICY"
REASON_UNKNOWN_UNIVERSE_POLICY_VERSION = "UNKNOWN_UNIVERSE_POLICY_VERSION"
REASON_BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
REASON_SPOT_BINDING = "SPOT_BINDING_REJECTED"
REASON_SYNTHETIC_SPOT_BINDING = "SYNTHETIC_SPOT_BINDING_REJECTED"
REASON_BITCOIN_DIRECTION_BINDING = "BITCOIN_DIRECTION_BINDING_REJECTED"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_MISSING_PERIOD_COVERAGE = "MISSING_PERIOD_COVERAGE"
REASON_INVALID_PERIOD_COVERAGE = "INVALID_PERIOD_COVERAGE"
REASON_MISSING_PANEL_DATASET_DIGEST = "MISSING_PANEL_DATASET_DIGEST"
REASON_MANIFEST_VALIDATION_FAILED = "PRODUCTION_MANIFEST_VALIDATION_FAILED"
REASON_MANIFEST_TAMPERED = "PRODUCTION_MANIFEST_TAMPERED"
REASON_ENVELOPE_MANIFEST_DIGEST_MISMATCH = "ENVELOPE_MANIFEST_DIGEST_MISMATCH"
REASON_WRONG_CONFIG_DIGEST = "WRONG_CONFIG_DIGEST"
REASON_WRONG_IMPLEMENTATION_DIGEST = "WRONG_IMPLEMENTATION_DIGEST"
REASON_WRONG_PARAMETER_BINDING = "WRONG_PARAMETER_BINDING"
REASON_ZERO_FEE = "ZERO_FEE_REJECTED"
REASON_ZERO_SLIPPAGE = "ZERO_SLIPPAGE_REJECTED"
REASON_DATA_DIGEST_NOT_MATERIALIZED = "DATA_DIGEST_NOT_YET_MATERIALIZED"
REASON_PERIOD_SPLIT_NOT_MATERIALIZED = "PERIOD_SPLIT_NOT_YET_MATERIALIZED"

CANDIDATE_REQUIRED_FIELDS = (
    "strategy_id",
    "strategy_version",
    "candidate_binding_version",
    "parameter_binding",
    "dataset_binding",
    "dataset_version",
    "period_binding",
    "training_period",
    "validation_period",
    "out_of_sample_period",
    "instrument_binding",
    "universe_policy_id",
    "universe_policy_version",
    "production_universe_manifest_ref",
    "production_universe_manifest_digest",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "binding_status",
    "reason_codes",
)

CONTRACT_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "fleet_id",
    "fleet_version",
    "candidate_binding_version",
    "dataset_binding_version",
    "period_binding_version",
    "instrument_binding_version",
    "production_universe_manifest_ref",
    "production_universe_manifest_digest",
    "shared_bindings",
    "candidates",
    "canonical_serialization_version",
    "contract_digest",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "config_digest",
    "implementation_digest",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class DatasetPeriodBindingValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "pit_futures_universe_manifest_dataset_period_binding_v0",
            "schema_version": SCHEMA_VERSION,
        }
    )


def compute_policy_config_digest_v0(repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / POLICY_CONFIG_REL_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":policy_config")
    return _stable_digest(payload)


def dumps_contract_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_contract_digest_v0(contract_body: Mapping[str, Any]) -> str:
    body = dict(contract_body)
    body.pop("contract_digest", None)
    return hashlib.sha256(dumps_contract_canonical_v1(body).encode("utf-8")).hexdigest()


def serialize_contract_canonical_v0(contract: Mapping[str, Any]) -> str:
    return dumps_contract_canonical_v1(contract) + "\n"


def envelope_from_dict(data: Mapping[str, Any]) -> ProductionManifestMaterializationEnvelopeV1:
    return ProductionManifestMaterializationEnvelopeV1(
        materialization_version=str(data["materialization_version"]),
        universe_policy_id=str(data["universe_policy_id"]),
        universe_policy_version=str(data["universe_policy_version"]),
        inclusion_policy_version=str(data["inclusion_policy_version"]),
        exclusion_policy_version=str(data["exclusion_policy_version"]),
        venue_id=str(data["venue_id"]),
        venue_family=str(data["venue_family"]),
        market_type=str(data["market_type"]),
        settlement_asset=str(data["settlement_asset"]),
        quote_asset=str(data["quote_asset"]),
        contract_type=str(data["contract_type"]),
        perpetual_only=bool(data["perpetual_only"]),
        linear_contract=bool(data["linear_contract"]),
        futures_only=bool(data["futures_only"]),
        bitcoin_direction_allowed=bool(data["bitcoin_direction_allowed"]),
        spot_allowed=bool(data["spot_allowed"]),
        synthetic_spot_allowed=bool(data["synthetic_spot_allowed"]),
        instrument_metadata_source_id=str(data["instrument_metadata_source_id"]),
        lifecycle_source_snapshot_ref=str(data["lifecycle_source_snapshot_ref"]),
        lifecycle_source_snapshot_digest=str(data["lifecycle_source_snapshot_digest"]),
        registry_reference=str(data["registry_reference"]),
        registry_snapshot_digest=str(data["registry_snapshot_digest"]),
        panel_dataset_ref=str(data["panel_dataset_ref"]),
        panel_dataset_digest=str(data["panel_dataset_digest"]),
        period_binding_ref=str(data["period_binding_ref"]),
        period_start_utc=str(data["period_start_utc"]),
        period_end_utc=str(data["period_end_utc"]),
        materialization_config_digest=str(data["materialization_config_digest"]),
        materialization_implementation_digest=str(data["materialization_implementation_digest"]),
        binding_implementation_digest=str(data["binding_implementation_digest"]),
        reproducibility_inputs_digest=str(data["reproducibility_inputs_digest"]),
        manifest_reference=data.get("manifest_reference"),
        manifest_digest=data.get("manifest_digest"),
        generated_at=str(data["generated_at"]),
        eligible_instrument_count=int(data["eligible_instrument_count"]),
        excluded_instrument_count=int(data["excluded_instrument_count"]),
        pit_semantics_enforced=bool(data["pit_semantics_enforced"]),
        non_authorizing=bool(data["non_authorizing"]),
        no_runtime_effect=bool(data["no_runtime_effect"]),
    )


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _reject_repair_keys(obj: Mapping[str, Any], *, path: str, reasons: list[str]) -> None:
    for key in obj:
        if key in {"repair", "fallback", "auto_fix", "default_if_missing"}:
            reasons.append(f"{REASON_BINDING_REPAIR_REJECTED}:{path}.{key}")


def _extract_parameter_binding(cfg: Mapping[str, Any], strategy_id: str) -> dict[str, Any]:
    params = collect_configured_strategy_params_v1(cfg, strategy_id)
    if not params:
        eval_section = cfg.get("economic_evaluation_v1")
        if isinstance(eval_section, Mapping):
            raw = eval_section.get("strategy_params")
            if isinstance(raw, Mapping):
                params = dict(raw)
    return dict(params)


def _extract_fee_model_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":fee_model_binding")
    return {
        "fee_bps": backtest.get("fee_bps"),
        "fee_model_version": str(backtest.get("fee_model_version", "")),
    }


def _extract_slippage_model_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":slippage_model_binding")
    return {
        "slippage_bps": backtest.get("slippage_bps"),
        "slippage_model_version": str(backtest.get("slippage_model_version", "")),
    }


def _extract_funding_model_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":funding_model_binding")
    funding = backtest.get("funding")
    if not isinstance(funding, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":funding_model_binding")
    return {
        "bind": bool(funding.get("bind")),
        "model_version": str(funding.get("model_version", "")),
    }


def _extract_execution_model_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    real = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(real, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":execution_model_binding")
    return {
        "execution_model_version": str(real.get("execution_model_version", "")),
        "roundtrip_cost_bps": real.get("roundtrip_cost_bps"),
    }


def _extract_economic_policy_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    eval_section = cfg.get("economic_evaluation_v1")
    version = ECONOMIC_POLICY_VERSION
    if isinstance(eval_section, Mapping):
        raw = eval_section.get("economic_validity_policy_version")
        if isinstance(raw, str) and raw.strip():
            version = raw
    return {"policy_version": version}


def _build_dataset_binding(
    envelope: ProductionManifestMaterializationEnvelopeV1,
) -> dict[str, Any]:
    return {
        "dataset_binding_version": DATASET_BINDING_VERSION,
        "dataset_version": PANEL_DATASET_VERSION,
        "dataset_profile": DATASET_PROFILE,
        "bar_granularity": BAR_GRANULARITY,
        "panel_dataset_ref": envelope.panel_dataset_ref.strip(),
        "panel_dataset_digest": envelope.panel_dataset_digest.strip().lower(),
        "instrument_metadata_source": INSTRUMENT_SELECTION_OWNER,
        "evaluation_period_binding": envelope.period_binding_ref.strip(),
    }


def _build_period_binding(
    envelope: ProductionManifestMaterializationEnvelopeV1,
) -> dict[str, Any]:
    return {
        "period_binding_version": PERIOD_BINDING_VERSION,
        "period_binding_ref": envelope.period_binding_ref.strip(),
        "coverage_period_start_utc": envelope.period_start_utc,
        "coverage_period_end_utc": envelope.period_end_utc,
    }


def _build_instrument_binding(
    *,
    production_manifest: PointInTimeFuturesUniverseManifestV1,
    envelope: ProductionManifestMaterializationEnvelopeV1,
) -> dict[str, Any]:
    if not production_manifest.epochs:
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":production_manifest.epochs")
    members = production_manifest.epochs[0].members
    eligible_instrument_ids = tuple(sorted(member.instrument_id for member in members))
    native_by_id = {member.instrument_id: member.venue_symbol for member in members}
    return {
        "instrument_binding_version": INSTRUMENT_BINDING_VERSION,
        "binding_mode": INSTRUMENT_BINDING_MODE,
        "instrument_selection_owner": INSTRUMENT_SELECTION_OWNER,
        "no_parallel_universe_ssot": True,
        "universe_policy_id": production_manifest.universe_policy_id,
        "universe_policy_version": production_manifest.universe_policy_version,
        "production_universe_manifest_ref": envelope.manifest_reference or "",
        "production_universe_manifest_digest": production_manifest.manifest_digest,
        "venue_id": envelope.venue_id,
        "eligible_instrument_ids": list(eligible_instrument_ids),
        "eligible_native_instrument_ids": [
            native_by_id[instrument_id] for instrument_id in eligible_instrument_ids
        ],
        "eligible_instrument_count": len(eligible_instrument_ids),
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
    }


def _build_data_digest(envelope: ProductionManifestMaterializationEnvelopeV1) -> dict[str, Any]:
    return {
        "status": "NOT_YET_MATERIALIZED",
        "bound_panel_dataset_digest": envelope.panel_dataset_digest.strip().lower(),
    }


def _build_reason_codes() -> list[str]:
    return sorted(
        [
            REASON_DATA_DIGEST_NOT_MATERIALIZED,
            REASON_PERIOD_SPLIT_NOT_MATERIALIZED,
        ]
    )


def _build_candidate_binding_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
    shared_dataset_binding: Mapping[str, Any],
    shared_period_binding: Mapping[str, Any],
    shared_instrument_binding: Mapping[str, Any],
    data_digest: Mapping[str, Any],
    envelope: ProductionManifestMaterializationEnvelopeV1,
    production_manifest: PointInTimeFuturesUniverseManifestV1,
) -> dict[str, Any]:
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":economic_evaluation_v1")
    if str(eval_section.get("strategy_id", "")) != strategy_id:
        raise ValueError(f"{REASON_UNKNOWN_STRATEGY}:{strategy_id}")
    if str(eval_section.get("strategy_version", "")) != strategy_version:
        raise ValueError(f"{REASON_WRONG_STRATEGY_VERSION}:{strategy_id}")

    resolution = resolve_strategy_id(strategy_id)
    if resolution.canonical_strategy_id != strategy_id:
        raise ValueError(f"{REASON_UNKNOWN_STRATEGY}:{strategy_id}")
    entry = get_strategy_registry_entry(strategy_id)
    if entry.strategy_version != strategy_version:
        raise ValueError(f"{REASON_WRONG_STRATEGY_VERSION}:{strategy_id}")

    parameter_binding = _extract_parameter_binding(cfg, strategy_id)
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        strategy_id,
        parameter_binding,
    )

    return {
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "candidate_binding_version": CANDIDATE_BINDING_VERSION,
        "parameter_binding": parameter_binding,
        "dataset_binding": dict(shared_dataset_binding),
        "dataset_version": PANEL_DATASET_VERSION,
        "period_binding": dict(shared_period_binding),
        "training_period": dict(NOT_YET_MATERIALIZED),
        "validation_period": dict(NOT_YET_MATERIALIZED),
        "out_of_sample_period": dict(NOT_YET_MATERIALIZED),
        "instrument_binding": dict(shared_instrument_binding),
        "universe_policy_id": production_manifest.universe_policy_id,
        "universe_policy_version": production_manifest.universe_policy_version,
        "production_universe_manifest_ref": envelope.manifest_reference or "",
        "production_universe_manifest_digest": production_manifest.manifest_digest,
        "fee_model_binding": _extract_fee_model_binding(cfg),
        "slippage_model_binding": _extract_slippage_model_binding(cfg),
        "funding_model_binding": _extract_funding_model_binding(cfg),
        "execution_model_binding": _extract_execution_model_binding(cfg),
        "economic_policy_binding": _extract_economic_policy_binding(cfg),
        "implementation_digest": entry.implementation_digest,
        "config_digest": compute_config_digest_v1(cfg),
        "data_digest": dict(data_digest),
        "strategy_params_digest": strategy_params_digest,
        "binding_status": BINDING_STATUS_NOT_READY,
        "reason_codes": _build_reason_codes(),
        "source_config_ref": STEP31F_CONFIG_PATHS[strategy_id],
    }


def materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
    *,
    repo_root: Path,
    production_manifest: PointInTimeFuturesUniverseManifestV1,
    production_envelope: ProductionManifestMaterializationEnvelopeV1,
) -> dict[str, Any]:
    """Materialize deterministic dataset/period/instrument binding contract."""
    manifest_validation = validate_pit_futures_universe_manifest_v1(production_manifest)
    if manifest_validation.verdict != ManifestValidationVerdict.ACCEPTED:
        raise ValueError(
            f"{REASON_MANIFEST_VALIDATION_FAILED}:{','.join(manifest_validation.reason_codes)}"
        )

    if production_manifest.manifest_digest != compute_manifest_digest(production_manifest):
        raise ValueError(REASON_MANIFEST_TAMPERED)

    if production_envelope.manifest_digest != production_manifest.manifest_digest:
        raise ValueError(REASON_ENVELOPE_MANIFEST_DIGEST_MISMATCH)

    if production_manifest.universe_policy_id != UNIVERSE_POLICY_ID:
        raise ValueError(REASON_UNKNOWN_UNIVERSE_POLICY)
    if production_manifest.universe_policy_version != UNIVERSE_POLICY_VERSION:
        raise ValueError(REASON_UNKNOWN_UNIVERSE_POLICY_VERSION)

    dataset_binding = _build_dataset_binding(production_envelope)
    period_binding = _build_period_binding(production_envelope)
    instrument_binding = _build_instrument_binding(
        production_manifest=production_manifest,
        envelope=production_envelope,
    )
    data_digest = _build_data_digest(production_envelope)

    candidates = [
        _build_candidate_binding_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            shared_dataset_binding=dataset_binding,
            shared_period_binding=period_binding,
            shared_instrument_binding=instrument_binding,
            data_digest=data_digest,
            envelope=production_envelope,
            production_manifest=production_manifest,
        )
        for strategy_id, strategy_version in FLEET_CANDIDATES
    ]
    candidates.sort(key=lambda item: item["strategy_id"])

    contract_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "candidate_binding_version": CANDIDATE_BINDING_VERSION,
        "dataset_binding_version": DATASET_BINDING_VERSION,
        "period_binding_version": PERIOD_BINDING_VERSION,
        "instrument_binding_version": INSTRUMENT_BINDING_VERSION,
        "production_universe_manifest_ref": production_envelope.manifest_reference or "",
        "production_universe_manifest_digest": production_manifest.manifest_digest,
        "shared_bindings": {
            "dataset_binding": dataset_binding,
            "period_binding": period_binding,
            "instrument_binding": instrument_binding,
        },
        "candidates": candidates,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "config_digest": compute_policy_config_digest_v0(repo_root),
        "implementation_digest": compute_implementation_digest_v0(),
        "evaluation_period_binding": EVALUATION_PERIOD_BINDING,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "non_authorizing": True,
        "no_runtime_effect": True,
        "no_economic_evaluation_execution": True,
    }
    contract_body["contract_digest"] = compute_contract_digest_v0(contract_body)
    return contract_body


def _validate_positive_cost(value: Any, *, field: str, reasons: list[str]) -> None:
    if not isinstance(value, (int, float)) or float(value) <= 0.0:
        reasons.append(f"{REASON_ZERO_FEE if 'fee' in field else REASON_ZERO_SLIPPAGE}:{field}")


def _validate_instrument_binding(binding: Mapping[str, Any], reasons: list[str]) -> None:
    if binding.get("futures_only") is not True:
        reasons.append(REASON_FUTURES_ONLY_VIOLATION)
    if binding.get("spot_allowed") is True:
        reasons.append(REASON_SPOT_BINDING)
    if binding.get("synthetic_spot_allowed") is True:
        reasons.append(REASON_SYNTHETIC_SPOT_BINDING)
    if binding.get("bitcoin_direction_allowed") is True:
        reasons.append(REASON_BITCOIN_DIRECTION_BINDING)
    for instrument_id in binding.get("eligible_instrument_ids", ()):
        if isinstance(instrument_id, str) and _contains_forbidden_token(instrument_id):
            reasons.append(f"{REASON_BITCOIN_INSTRUMENT_PRESENT}:{instrument_id}")


def _validate_period_binding(binding: Mapping[str, Any], reasons: list[str]) -> None:
    start = binding.get("coverage_period_start_utc")
    end = binding.get("coverage_period_end_utc")
    ref = binding.get("period_binding_ref")
    if not isinstance(ref, str) or not ref.strip():
        reasons.append(REASON_MISSING_PERIOD_COVERAGE + ":period_binding_ref")
    if not isinstance(start, str) or not start.strip():
        reasons.append(REASON_MISSING_PERIOD_COVERAGE + ":coverage_period_start_utc")
    elif not is_valid_rfc3339_utc(start):
        reasons.append(REASON_INVALID_PERIOD_COVERAGE + ":coverage_period_start_utc")
    if not isinstance(end, str) or not end.strip():
        reasons.append(REASON_MISSING_PERIOD_COVERAGE + ":coverage_period_end_utc")
    elif not is_valid_rfc3339_utc(end):
        reasons.append(REASON_INVALID_PERIOD_COVERAGE + ":coverage_period_end_utc")


def _validate_dataset_binding(binding: Mapping[str, Any], reasons: list[str]) -> None:
    digest = binding.get("panel_dataset_digest")
    ref = binding.get("panel_dataset_ref")
    if not isinstance(ref, str) or not ref.strip():
        reasons.append(REASON_MISSING_REQUIRED_FIELD + ":panel_dataset_ref")
    if not isinstance(digest, str) or not is_valid_digest(digest.strip().lower()):
        reasons.append(REASON_MISSING_PANEL_DATASET_DIGEST)


def _validate_deferred_period_field(field: Any, *, name: str, reasons: list[str]) -> None:
    if not isinstance(field, Mapping):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{name}")
        return
    if field.get("status") != "NOT_YET_MATERIALIZED":
        reasons.append(f"{REASON_PERIOD_SPLIT_NOT_MATERIALIZED}:{name}")


def _validate_data_digest(field: Any, reasons: list[str]) -> None:
    if not isinstance(field, Mapping):
        reasons.append(REASON_MISSING_REQUIRED_FIELD + ":data_digest")
        return
    if field.get("status") != "NOT_YET_MATERIALIZED":
        reasons.append(REASON_DATA_DIGEST_NOT_MATERIALIZED)
        return
    bound = field.get("bound_panel_dataset_digest")
    if not isinstance(bound, str) or not is_valid_digest(bound.strip().lower()):
        reasons.append(REASON_MISSING_PANEL_DATASET_DIGEST)


def _validate_shared_candidate_bindings(
    candidates: Sequence[Mapping[str, Any]],
    reasons: list[str],
) -> None:
    if len(candidates) < 2:
        return
    reference = candidates[0]
    for field in (
        "dataset_binding",
        "period_binding",
        "instrument_binding",
        "production_universe_manifest_ref",
        "production_universe_manifest_digest",
        "data_digest",
    ):
        ref_value = reference.get(field)
        for candidate in candidates[1:]:
            if candidate.get(field) != ref_value:
                reasons.append(
                    f"{REASON_SHARED_BINDING_MISMATCH}:{field}:{candidate.get('strategy_id')}"
                )


def validate_pit_futures_universe_manifest_dataset_period_binding_v0(
    contract: Any,
    *,
    repo_root: Path,
    expected_manifest: PointInTimeFuturesUniverseManifestV1 | None = None,
    expected_envelope: ProductionManifestMaterializationEnvelopeV1 | None = None,
    allow_recompute_digests: bool = True,
) -> DatasetPeriodBindingValidationResultV0:
    reasons: list[str] = []
    if not isinstance(contract, Mapping):
        return DatasetPeriodBindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=(REASON_MANIFEST_NOT_OBJECT,),
        )

    _reject_repair_keys(contract, path="$", reasons=reasons)

    if contract.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_UNKNOWN_SCHEMA_VERSION)

    for field in CONTRACT_REQUIRED_FIELDS:
        if field not in contract:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{field}")

    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if contract.get(effect_field) != expected:
            reasons.append(f"{REASON_EFFECT_NOT_NONE}:{effect_field}")

    manifest_ref = contract.get("production_universe_manifest_ref")
    manifest_digest = contract.get("production_universe_manifest_digest")
    if expected_envelope is not None:
        if manifest_ref != (expected_envelope.manifest_reference or ""):
            reasons.append(REASON_PRODUCTION_MANIFEST_REF_MISMATCH)
        if expected_envelope.manifest_digest != manifest_digest:
            reasons.append(REASON_PRODUCTION_MANIFEST_DIGEST_MISMATCH)
    if expected_manifest is not None:
        if expected_manifest.manifest_digest != manifest_digest:
            reasons.append(REASON_PRODUCTION_MANIFEST_DIGEST_MISMATCH)
        if expected_manifest.manifest_digest != compute_manifest_digest(expected_manifest):
            reasons.append(REASON_MANIFEST_TAMPERED)

    shared = contract.get("shared_bindings")
    if isinstance(shared, Mapping):
        dataset = shared.get("dataset_binding")
        period = shared.get("period_binding")
        instrument = shared.get("instrument_binding")
        if isinstance(dataset, Mapping):
            _validate_dataset_binding(dataset, reasons)
        else:
            reasons.append(REASON_MISSING_REQUIRED_FIELD + ":shared_bindings.dataset_binding")
        if isinstance(period, Mapping):
            _validate_period_binding(period, reasons)
        else:
            reasons.append(REASON_MISSING_REQUIRED_FIELD + ":shared_bindings.period_binding")
        if isinstance(instrument, Mapping):
            _validate_instrument_binding(instrument, reasons)
        else:
            reasons.append(REASON_MISSING_REQUIRED_FIELD + ":shared_bindings.instrument_binding")
    else:
        reasons.append(REASON_MISSING_REQUIRED_FIELD + ":shared_bindings")

    raw_candidates = contract.get("candidates")
    if not isinstance(raw_candidates, list):
        reasons.append(REASON_MISSING_REQUIRED_FIELD + ":candidates")
        raw_candidates = []

    expected_ids = {sid for sid, _ in FLEET_CANDIDATES}
    seen_ids: set[str] = set()
    parsed_candidates: list[Mapping[str, Any]] = []

    for index, candidate in enumerate(raw_candidates):
        path = f"candidates[{index}]"
        if not isinstance(candidate, Mapping):
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}")
            continue
        _reject_repair_keys(candidate, path=path, reasons=reasons)

        strategy_id = candidate.get("strategy_id")
        strategy_version = candidate.get("strategy_version")
        if not isinstance(strategy_id, str) or not isinstance(strategy_version, str):
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.strategy_identity")
            continue

        if (strategy_id, strategy_version) not in FLEET_CANDIDATES:
            if strategy_id in expected_ids:
                reasons.append(f"{REASON_WRONG_STRATEGY_VERSION}:{strategy_id}")
            else:
                reasons.append(f"{REASON_UNKNOWN_STRATEGY}:{strategy_id}")

        if strategy_id in seen_ids:
            reasons.append(f"{REASON_DUPLICATE_CANDIDATE}:{strategy_id}")
        seen_ids.add(strategy_id)

        for field in CANDIDATE_REQUIRED_FIELDS:
            if field not in candidate:
                reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.{field}")

        if candidate.get("binding_status") != BINDING_STATUS_NOT_READY:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.binding_status")

        _validate_deferred_period_field(
            candidate.get("training_period"), name="training_period", reasons=reasons
        )
        _validate_deferred_period_field(
            candidate.get("validation_period"), name="validation_period", reasons=reasons
        )
        _validate_deferred_period_field(
            candidate.get("out_of_sample_period"), name="out_of_sample_period", reasons=reasons
        )
        _validate_data_digest(candidate.get("data_digest"), reasons)

        if isinstance(candidate.get("dataset_binding"), Mapping):
            _validate_dataset_binding(candidate["dataset_binding"], reasons)
        if isinstance(candidate.get("period_binding"), Mapping):
            _validate_period_binding(candidate["period_binding"], reasons)
        if isinstance(candidate.get("instrument_binding"), Mapping):
            _validate_instrument_binding(candidate["instrument_binding"], reasons)

        fee = candidate.get("fee_model_binding")
        if isinstance(fee, Mapping):
            _validate_positive_cost(fee.get("fee_bps"), field="fee_bps", reasons=reasons)
        else:
            reasons.append(REASON_ZERO_FEE + f":{strategy_id}")

        slippage = candidate.get("slippage_model_binding")
        if isinstance(slippage, Mapping):
            _validate_positive_cost(
                slippage.get("slippage_bps"), field="slippage_bps", reasons=reasons
            )
        else:
            reasons.append(REASON_ZERO_SLIPPAGE + f":{strategy_id}")

        if allow_recompute_digests and strategy_id in STEP31F_CONFIG_PATHS:
            try:
                cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
                if candidate.get("config_digest") != compute_config_digest_v1(cfg):
                    reasons.append(f"{REASON_WRONG_CONFIG_DIGEST}:{strategy_id}")
                entry = get_strategy_registry_entry(strategy_id)
                if candidate.get("implementation_digest") != entry.implementation_digest:
                    reasons.append(f"{REASON_WRONG_IMPLEMENTATION_DIGEST}:{strategy_id}")
                expected_params = _extract_parameter_binding(cfg, strategy_id)
                if candidate.get("parameter_binding") != expected_params:
                    reasons.append(f"{REASON_WRONG_PARAMETER_BINDING}:{strategy_id}")
            except (FileNotFoundError, ValueError, KeyError) as exc:
                reasons.append(f"{REASON_WRONG_CONFIG_DIGEST}:{strategy_id}:{exc}")

        parsed_candidates.append(candidate)

    for strategy_id in sorted(expected_ids - seen_ids):
        reasons.append(f"{REASON_MISSING_CANDIDATE}:{strategy_id}")
    for strategy_id in sorted(seen_ids - expected_ids):
        reasons.append(f"{REASON_EXTRA_CANDIDATE}:{strategy_id}")

    _validate_shared_candidate_bindings(parsed_candidates, reasons)

    expected_contract_digest = compute_contract_digest_v0(contract)
    if contract.get("contract_digest") != expected_contract_digest:
        reasons.append(REASON_WRONG_CONTRACT_DIGEST)

    canonical = dumps_contract_canonical_v1(contract)
    if canonical != dumps_contract_canonical_v1(json.loads(canonical)):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION)
    if _ABSOLUTE_PATH_PATTERN.search(canonical):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION + ":absolute_path_in_contract")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return DatasetPeriodBindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
        )
    return DatasetPeriodBindingValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def clone_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(contract))


__all__ = [
    "AUTHORITY_EFFECT",
    "BINDING_STATUS_NOT_READY",
    "CANDIDATE_BINDING_VERSION",
    "CONTRACT_ID",
    "DATASET_BINDING_VERSION",
    "DatasetPeriodBindingValidationResultV0",
    "FLEET_CANDIDATES",
    "FLEET_ID",
    "INSTRUMENT_BINDING_VERSION",
    "NOT_YET_MATERIALIZED",
    "ORDER_EFFECT",
    "PERIOD_BINDING_VERSION",
    "POLICY_CONFIG_REL_PATH",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "UNIVERSE_POLICY_ID",
    "UNIVERSE_POLICY_VERSION",
    "ValidationVerdict",
    "clone_contract",
    "compute_contract_digest_v0",
    "compute_implementation_digest_v0",
    "compute_policy_config_digest_v0",
    "envelope_from_dict",
    "manifest_from_dict",
    "materialize_pit_futures_universe_manifest_dataset_period_binding_v0",
    "serialize_contract_canonical_v0",
    "validate_pit_futures_universe_manifest_dataset_period_binding_v0",
]
