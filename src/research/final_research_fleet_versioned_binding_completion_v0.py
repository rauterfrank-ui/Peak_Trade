"""Final Research Fleet versioned binding completion v0.

Deterministic, fail-closed materialization and validation of complete versioned
bindings for trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 wired
to PIT cross-sectional dataset/period/instrument owners from PRs #4782–#4784.

Research-only. No economic evaluation execution, no runtime or order effect.
ECONOMIC_EVALUATION_AUTHORIZED=false for all candidates in this scope.
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

from src.backtest.strategy_signal_binding_v1 import resolve_effective_strategy_params_v1
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    OPERATOR_RATIFICATION_REF,
    STEP31F_CONFIG_PATHS,
    compute_config_digest_v1,
    load_step31f_evaluation_config_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    MaterializationStatus,
    dataset_envelope_to_dict,
    materialize_cross_sectional_research_data_digest_and_period_split_v0,
    period_split_to_dict,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (
    BINDING_STATUS_BLOCKED,
    BINDING_STATUS_NOT_READY,
    BINDING_STATUS_READY,
    materialize_pit_futures_universe_manifest_dataset_period_binding_v0,
    materialize_pit_futures_universe_manifest_dataset_period_binding_with_research_materialization_v0,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    ProductionManifestMaterializationEnvelopeV1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    PointInTimeFuturesUniverseManifestV1,
    is_valid_digest,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

PACKAGE_MARKER = "FINAL_RESEARCH_FLEET_VERSIONED_BINDING_COMPLETION_V0=true"

SCHEMA_VERSION = "final_research_fleet_versioned_binding_completion.v0"
COMPLETION_ID = "final_research_fleet_versioned_binding_completion_v0"
CONFIG_REL_PATH = "config/research/final_research_fleet_versioned_binding_completion_v0.json"
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"
CANONICAL_TRADING_LOGIC_BINDING_VERSION = "strategy_signal_binding_v1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS = False
RUNTIME_REWIRE_ADMISSIBLE = False

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

BINDING_STATUS_INCOMPLETE = "BINDING_INCOMPLETE"
BINDING_STATUS_VALID = "BINDING_VALID"
BINDING_STATUS_READY_FOR_EVAL_RATIFICATION = "READY_FOR_SEPARATE_OFFLINE_EVALUATION_RATIFICATION"

FAILED_HISTORICAL_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("macd", "v1"),
    ("macd", "v2"),
    ("macd", "v3"),
    ("breakout_donchian", "v1"),
    ("ma_crossover", "v1"),
    ("rsi_reversion", "step30a"),
    ("composite_breakout_confirmation_vol_gated_donchian_v1", "v1"),
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")

REASON_UNKNOWN_STRATEGY = "UNKNOWN_STRATEGY"
REASON_WRONG_STRATEGY_VERSION = "WRONG_STRATEGY_VERSION"
REASON_FAILED_HISTORICAL_CANDIDATE = "FAILED_HISTORICAL_CANDIDATE_EXCLUDED"
REASON_MISSING_CANDIDATE = "MISSING_FLEET_CANDIDATE"
REASON_EXTRA_CANDIDATE = "EXTRA_FLEET_CANDIDATE"
REASON_DUPLICATE_CANDIDATE = "DUPLICATE_FLEET_CANDIDATE"
REASON_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
REASON_UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
REASON_COMPLETION_NOT_OBJECT = "COMPLETION_NOT_OBJECT"
REASON_EFFECT_NOT_NONE = "AUTHORITY_RUNTIME_ORDER_EFFECT_NOT_NONE"
REASON_BINDING_REPAIR_REJECTED = "BINDING_REPAIR_REJECTED"
REASON_SHARED_BINDING_MISMATCH = "SHARED_BINDING_MISMATCH"
REASON_ECONOMIC_POLICY_MISMATCH = "ECONOMIC_POLICY_MISMATCH"
REASON_ECONOMIC_EVALUATION_AUTHORIZED = "ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE"
REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_BINDING_NOT_VALID = "BINDING_NOT_VALID"
REASON_BINDING_NOT_READY_FOR_EVAL = "BINDING_NOT_READY_FOR_EVALUATION_RATIFICATION"
REASON_WRONG_COMPLETION_DIGEST = "WRONG_COMPLETION_DIGEST"
REASON_WRONG_BINDING_SEMANTIC_DIGEST = "WRONG_BINDING_SEMANTIC_DIGEST"
REASON_WRONG_CONFIG_DIGEST = "WRONG_CONFIG_DIGEST"
REASON_WRONG_IMPLEMENTATION_DIGEST = "WRONG_IMPLEMENTATION_DIGEST"
REASON_WRONG_DATA_DIGEST = "WRONG_DATA_DIGEST"
REASON_WRONG_PARAMETER_BINDING = "WRONG_PARAMETER_BINDING"
REASON_WRONG_STRATEGY_PARAMS_DIGEST = "WRONG_STRATEGY_PARAMS_DIGEST"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_SPOT_BINDING = "SPOT_BINDING_REJECTED"
REASON_SYNTHETIC_SPOT_BINDING = "SYNTHETIC_SPOT_BINDING_REJECTED"
REASON_BITCOIN_DIRECTION_BINDING = "BITCOIN_DIRECTION_BINDING_REJECTED"
REASON_BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
REASON_ZERO_FEE = "ZERO_FEE_REJECTED"
REASON_ZERO_SLIPPAGE = "ZERO_SLIPPAGE_REJECTED"
REASON_DATASET_PERIOD_CONTRACT_INVALID = "DATASET_PERIOD_CONTRACT_INVALID"
REASON_NON_CANONICAL_SERIALIZATION = "NON_CANONICAL_SERIALIZATION"
REASON_AMBIGUOUS_BINDING = "AMBIGUOUS_BINDING"
REASON_NOT_RATIFIED = "CANDIDATE_NOT_RATIFIED"
REASON_RATIFICATION_REF_MISMATCH = "OPERATOR_RATIFICATION_REF_MISMATCH"

CANDIDATE_REQUIRED_FIELDS = (
    "canonical_candidate_identifier",
    "strategy_id",
    "strategy_version",
    "parameter_schema_version",
    "parameter_binding",
    "dataset_binding",
    "dataset_version",
    "dataset_provenance",
    "period_binding",
    "training_period",
    "validation_period",
    "out_of_sample_period",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "canonical_trading_logic_version",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "binding_semantic_digest",
    "reproducibility_metadata",
    "binding_status",
    "economic_evaluation_authorized",
    "operator_ratification_ref",
    "ratified",
    "strategy_params_digest",
    "source_config_ref",
)

COMPLETION_REQUIRED_FIELDS = (
    "schema_version",
    "completion_id",
    "fleet_id",
    "fleet_version",
    "candidates",
    "shared_bindings",
    "excluded_failed_historical_candidates",
    "canonical_serialization_version",
    "completion_digest",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "economic_evaluation_authorized",
    "economic_validity_offline_gate_pass",
    "runtime_rewire_admissible",
    "futures_only",
    "bitcoin_direction_allowed",
    "spot_allowed",
    "synthetic_spot_allowed",
    "dataset_period_binding_contract_digest",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BindingCompletionValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "final_research_fleet_versioned_binding_completion_v0",
            "schema_version": SCHEMA_VERSION,
        }
    )


def dumps_completion_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_completion_digest_v0(completion_body: Mapping[str, Any]) -> str:
    body = dict(completion_body)
    body.pop("completion_digest", None)
    return hashlib.sha256(dumps_completion_canonical_v1(body).encode("utf-8")).hexdigest()


def serialize_completion_canonical_v0(completion: Mapping[str, Any]) -> str:
    return dumps_completion_canonical_v1(completion) + "\n"


def canonical_candidate_identifier(strategy_id: str, strategy_version: str) -> str:
    return f"{strategy_id}/{strategy_version}"


def _reject_repair_keys(obj: Mapping[str, Any], *, path: str, reasons: list[str]) -> None:
    for key in obj:
        if key in {"repair", "fallback", "auto_fix", "default_if_missing"}:
            reasons.append(f"{REASON_BINDING_REPAIR_REJECTED}:{path}.{key}")


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _build_dataset_provenance(
    *,
    dataset_binding: Mapping[str, Any],
    dataset_envelope: Mapping[str, Any] | None,
) -> dict[str, Any]:
    provenance: dict[str, Any] = {
        "dataset_profile": dataset_binding.get("dataset_profile"),
        "instrument_metadata_source": dataset_binding.get("instrument_metadata_source"),
        "panel_dataset_ref": dataset_binding.get("panel_dataset_ref"),
        "panel_dataset_digest": dataset_binding.get("panel_dataset_digest"),
        "evaluation_period_binding": dataset_binding.get("evaluation_period_binding"),
        "pit_safe": True,
        "cross_branch_evidence_forbidden": True,
    }
    if dataset_envelope is not None:
        provenance.update(
            {
                "dataset_id": dataset_envelope.get("dataset_id"),
                "source_registration_ref": dataset_envelope.get("source_registration_ref"),
                "source_registration_digest": dataset_envelope.get("source_registration_digest"),
                "universe_manifest_ref": dataset_envelope.get("universe_manifest_ref"),
                "universe_manifest_digest": dataset_envelope.get("universe_manifest_digest"),
                "ingestion_contract_version": dataset_envelope.get("ingestion_contract_version"),
            }
        )
    return provenance


def _build_reproducibility_metadata(
    *,
    repo_root: Path,
    dataset_period_contract: Mapping[str, Any],
    dataset_envelope: Mapping[str, Any] | None,
    period_split: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "repo_root_relative": True,
        "materialization_module": "final_research_fleet_versioned_binding_completion_v0",
        "dataset_period_binding_schema": dataset_period_contract.get("schema_version"),
        "dataset_period_binding_contract_digest": dataset_period_contract.get("contract_digest"),
        "research_materialization_version": dataset_period_contract.get(
            "research_materialization_version"
        ),
        "policy_config_refs": [
            "config/research/pit_futures_universe_manifest_dataset_period_binding_policy_v1.json",
            "config/research/pit_cross_sectional_research_data_digest_period_split_policy_v1.json",
        ],
        "step31f_config_refs": [STEP31F_CONFIG_PATHS[sid] for sid, _ in FLEET_CANDIDATES],
        "data_digest_materialization_rule": (
            "pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0."
            "compute_semantic_data_digest_v0"
        ),
        "binding_semantic_digest_rule": (
            "SHA-256 over canonical JSON of semantic binding payload excluding "
            "binding_semantic_digest and completion_digest"
        ),
        "dataset_envelope_digest": (
            dataset_envelope.get("data_digest") if dataset_envelope is not None else None
        ),
        "period_split_digest": period_split.get("period_digest")
        if period_split is not None
        else None,
        "implementation_digest": compute_implementation_digest_v0(),
        "repo_root_marker": str(repo_root.name),
    }


def compute_binding_semantic_digest_v0(candidate: Mapping[str, Any]) -> str:
    payload = {
        "canonical_candidate_identifier": candidate.get("canonical_candidate_identifier"),
        "strategy_id": candidate.get("strategy_id"),
        "strategy_version": candidate.get("strategy_version"),
        "parameter_schema_version": candidate.get("parameter_schema_version"),
        "parameter_binding": candidate.get("parameter_binding"),
        "dataset_binding": candidate.get("dataset_binding"),
        "dataset_version": candidate.get("dataset_version"),
        "dataset_provenance": candidate.get("dataset_provenance"),
        "period_binding": candidate.get("period_binding"),
        "training_period": candidate.get("training_period"),
        "validation_period": candidate.get("validation_period"),
        "out_of_sample_period": candidate.get("out_of_sample_period"),
        "instrument_binding": candidate.get("instrument_binding"),
        "fee_model_binding": candidate.get("fee_model_binding"),
        "slippage_model_binding": candidate.get("slippage_model_binding"),
        "funding_model_binding": candidate.get("funding_model_binding"),
        "execution_model_binding": candidate.get("execution_model_binding"),
        "economic_policy_binding": candidate.get("economic_policy_binding"),
        "canonical_trading_logic_version": candidate.get("canonical_trading_logic_version"),
        "implementation_digest": candidate.get("implementation_digest"),
        "config_digest": candidate.get("config_digest"),
        "data_digest": candidate.get("data_digest"),
        "strategy_params_digest": candidate.get("strategy_params_digest"),
        "economic_evaluation_authorized": candidate.get("economic_evaluation_authorized"),
    }
    return _stable_digest(payload)


def _resolve_binding_status(
    *,
    dataset_period_status: str,
    research_success: bool,
) -> str:
    if dataset_period_status == BINDING_STATUS_BLOCKED:
        return BINDING_STATUS_INCOMPLETE
    if dataset_period_status == BINDING_STATUS_NOT_READY:
        return BINDING_STATUS_INCOMPLETE
    if dataset_period_status == BINDING_STATUS_READY and research_success:
        return BINDING_STATUS_READY_FOR_EVAL_RATIFICATION
    if dataset_period_status == BINDING_STATUS_READY:
        return BINDING_STATUS_VALID
    return BINDING_STATUS_INCOMPLETE


def _build_candidate_from_dataset_period(
    *,
    repo_root: Path,
    dataset_candidate: Mapping[str, Any],
    dataset_envelope: Mapping[str, Any] | None,
    period_split: Mapping[str, Any] | None,
    binding_status: str,
) -> dict[str, Any]:
    strategy_id = str(dataset_candidate["strategy_id"])
    strategy_version = str(dataset_candidate["strategy_version"])
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    entry = get_strategy_registry_entry(strategy_id)
    parameter_binding = dict(dataset_candidate["parameter_binding"])
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        strategy_id,
        parameter_binding,
    )
    dataset_binding = dict(dataset_candidate["dataset_binding"])
    dataset_provenance = _build_dataset_provenance(
        dataset_binding=dataset_binding,
        dataset_envelope=dataset_envelope,
    )
    data_digest_value = dataset_candidate.get("data_digest")
    if isinstance(data_digest_value, Mapping) and data_digest_value.get("status") == "MATERIALIZED":
        data_digest = str(data_digest_value["value"])
    elif isinstance(data_digest_value, str):
        data_digest = data_digest_value
    else:
        data_digest = ""

    candidate: dict[str, Any] = {
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, strategy_version
        ),
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "parameter_schema_version": str(cfg.get("config_schema_version", "")),
        "parameter_binding": parameter_binding,
        "dataset_binding": dataset_binding,
        "dataset_version": str(dataset_candidate.get("dataset_version", "")),
        "dataset_provenance": dataset_provenance,
        "period_binding": dict(dataset_candidate["period_binding"]),
        "training_period": dict(dataset_candidate["training_period"]),
        "validation_period": dict(dataset_candidate["validation_period"]),
        "out_of_sample_period": dict(dataset_candidate["out_of_sample_period"]),
        "instrument_binding": dict(dataset_candidate["instrument_binding"]),
        "fee_model_binding": dict(dataset_candidate["fee_model_binding"]),
        "slippage_model_binding": dict(dataset_candidate["slippage_model_binding"]),
        "funding_model_binding": dict(dataset_candidate["funding_model_binding"]),
        "execution_model_binding": dict(dataset_candidate["execution_model_binding"]),
        "economic_policy_binding": dict(dataset_candidate["economic_policy_binding"]),
        "canonical_trading_logic_version": entry.semantic_digest,
        "canonical_trading_logic_binding_version": CANONICAL_TRADING_LOGIC_BINDING_VERSION,
        "implementation_digest": str(dataset_candidate["implementation_digest"]),
        "config_digest": str(dataset_candidate["config_digest"]),
        "data_digest": data_digest,
        "strategy_params_digest": strategy_params_digest,
        "reproducibility_metadata": _build_reproducibility_metadata(
            repo_root=repo_root,
            dataset_period_contract={},
            dataset_envelope=dataset_envelope,
            period_split=period_split,
        ),
        "binding_status": binding_status,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "operator_ratification_ref": OPERATOR_RATIFICATION_REF,
        "ratified": True,
        "source_config_ref": STEP31F_CONFIG_PATHS[strategy_id],
        "period_digest": dataset_candidate.get("period_digest"),
        "reason_codes": list(dataset_candidate.get("reason_codes") or []),
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_final_research_fleet_versioned_binding_completion_v0(
    *,
    repo_root: Path,
    production_manifest: PointInTimeFuturesUniverseManifestV1 | None = None,
    production_envelope: ProductionManifestMaterializationEnvelopeV1 | None = None,
    panel_series: Sequence[InstrumentPanelSeriesV1] | None = None,
    source_registration_ref: str = "",
    source_registration_digest: str = "",
) -> dict[str, Any]:
    """Materialize fleet binding completion from PIT owners and STEP31F configs."""
    research_success = False
    dataset_envelope_dict: dict[str, Any] | None = None
    period_split_dict: dict[str, Any] | None = None

    if (
        production_manifest is not None
        and production_envelope is not None
        and panel_series is not None
        and source_registration_ref
        and source_registration_digest
    ):
        research_result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
            repo_root=repo_root,
            production_manifest=production_manifest,
            production_envelope=production_envelope,
            panel_series=panel_series,
            source_registration_ref=source_registration_ref,
            source_registration_digest=source_registration_digest,
        )
        research_success = research_result.success
        if research_result.dataset_envelope is not None:
            dataset_envelope_dict = dataset_envelope_to_dict(research_result.dataset_envelope)
        if research_result.period_split is not None:
            period_split_dict = period_split_to_dict(research_result.period_split)
        dataset_period_contract = materialize_pit_futures_universe_manifest_dataset_period_binding_with_research_materialization_v0(
            repo_root=repo_root,
            production_manifest=production_manifest,
            production_envelope=production_envelope,
            research_materialization_result=research_result,
        )
    elif production_manifest is not None and production_envelope is not None:
        dataset_period_contract = (
            materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
                repo_root=repo_root,
                production_manifest=production_manifest,
                production_envelope=production_envelope,
            )
        )
    else:
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":production_manifest_and_envelope")

    dataset_period_status = str(
        dataset_period_contract.get("binding_materialization_status", BINDING_STATUS_NOT_READY)
    )
    overall_binding_status = _resolve_binding_status(
        dataset_period_status=dataset_period_status,
        research_success=research_success,
    )

    shared_bindings = dict(dataset_period_contract.get("shared_bindings") or {})
    if dataset_envelope_dict is not None:
        shared_bindings["dataset_envelope"] = dataset_envelope_dict
    if period_split_dict is not None:
        shared_bindings["period_split"] = period_split_dict

    candidates = [
        _build_candidate_from_dataset_period(
            repo_root=repo_root,
            dataset_candidate=candidate,
            dataset_envelope=dataset_envelope_dict,
            period_split=period_split_dict,
            binding_status=overall_binding_status,
        )
        for candidate in dataset_period_contract["candidates"]
    ]
    for candidate in candidates:
        candidate["reproducibility_metadata"] = _build_reproducibility_metadata(
            repo_root=repo_root,
            dataset_period_contract=dataset_period_contract,
            dataset_envelope=dataset_envelope_dict,
            period_split=period_split_dict,
        )
        candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)

    completion_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "completion_id": COMPLETION_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "candidates": candidates,
        "shared_bindings": shared_bindings,
        "excluded_failed_historical_candidates": [
            {"strategy_id": sid, "strategy_version": ver, "retry_forbidden": True}
            for sid, ver in FAILED_HISTORICAL_CANDIDATES
        ],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_validity_offline_gate_pass": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "dataset_period_binding_contract_digest": dataset_period_contract.get("contract_digest"),
        "dataset_period_binding_schema_version": dataset_period_contract.get("schema_version"),
        "binding_materialization_status": overall_binding_status,
        "research_materialization_success": research_success,
        "implementation_digest": compute_implementation_digest_v0(),
        "digest_semantics": {
            "completion_digest": "COMPLETION_BODY_CANONICAL_JSON_v0",
            "binding_semantic_digest": "CANDIDATE_SEMANTIC_BINDING_PAYLOAD_v0",
            "config_digest": "CANONICAL_PARSED_EVALUATION_CONFIG_v1",
            "implementation_digest": "STRATEGY_REGISTRY_IMPLEMENTATION_REF_v1",
            "data_digest": "PIT_CROSS_SECTIONAL_SEMANTIC_DATA_DIGEST_v0",
        },
    }
    completion_body["completion_digest"] = compute_completion_digest_v0(completion_body)
    return completion_body


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


def _validate_materialized_period(field: Any, *, name: str, reasons: list[str]) -> None:
    if not isinstance(field, Mapping):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{name}")
        return
    if field.get("status") != "MATERIALIZED":
        reasons.append(f"{REASON_BINDING_INCOMPLETE}:{name}")
        return
    for key in ("start", "end"):
        raw = field.get(key)
        if not isinstance(raw, str) or not raw.strip():
            reasons.append(f"{REASON_BINDING_INCOMPLETE}:{name}.{key}")


def validate_final_research_fleet_versioned_binding_completion_v0(
    completion: Any,
    *,
    repo_root: Path,
    require_ready_for_eval: bool = True,
    allow_recompute_digests: bool = True,
) -> BindingCompletionValidationResultV0:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return BindingCompletionValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=(REASON_COMPLETION_NOT_OBJECT,),
        )

    _reject_repair_keys(completion, path="$", reasons=reasons)

    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_UNKNOWN_SCHEMA_VERSION)

    for field in COMPLETION_REQUIRED_FIELDS:
        if field not in completion:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{field}")

    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if completion.get(effect_field) != expected:
            reasons.append(f"{REASON_EFFECT_NOT_NONE}:{effect_field}")

    if completion.get("economic_evaluation_authorized") is not False:
        reasons.append(REASON_ECONOMIC_EVALUATION_AUTHORIZED)
    if completion.get("futures_only") is not True:
        reasons.append(REASON_FUTURES_ONLY_VIOLATION)
    if completion.get("bitcoin_direction_allowed") is not False:
        reasons.append(REASON_BITCOIN_DIRECTION_BINDING)
    if completion.get("spot_allowed") is not False:
        reasons.append(REASON_SPOT_BINDING)
    if completion.get("synthetic_spot_allowed") is not False:
        reasons.append(REASON_SYNTHETIC_SPOT_BINDING)

    excluded = completion.get("excluded_failed_historical_candidates")
    if isinstance(excluded, list):
        excluded_pairs = {
            (item.get("strategy_id"), item.get("strategy_version"))
            for item in excluded
            if isinstance(item, Mapping)
        }
        for pair in FAILED_HISTORICAL_CANDIDATES:
            if pair not in excluded_pairs:
                reasons.append(f"{REASON_FAILED_HISTORICAL_CANDIDATE}:{pair[0]}")

    raw_candidates = completion.get("candidates")
    if not isinstance(raw_candidates, list):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:candidates")
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
            reasons.append(f"{REASON_AMBIGUOUS_BINDING}:{path}.strategy_identity")
            continue

        if (strategy_id, strategy_version) in FAILED_HISTORICAL_CANDIDATES:
            reasons.append(f"{REASON_FAILED_HISTORICAL_CANDIDATE}:{strategy_id}")

        if (strategy_id, strategy_version) not in FLEET_CANDIDATES:
            if strategy_id in expected_ids:
                reasons.append(f"{REASON_WRONG_STRATEGY_VERSION}:{strategy_id}")
            else:
                reasons.append(f"{REASON_UNKNOWN_STRATEGY}:{strategy_id}")

        expected_identifier = canonical_candidate_identifier(strategy_id, strategy_version)
        if candidate.get("canonical_candidate_identifier") != expected_identifier:
            reasons.append(
                f"{REASON_AMBIGUOUS_BINDING}:canonical_candidate_identifier:{strategy_id}"
            )

        if strategy_id in seen_ids:
            reasons.append(f"{REASON_DUPLICATE_CANDIDATE}:{strategy_id}")
        seen_ids.add(strategy_id)

        for field in CANDIDATE_REQUIRED_FIELDS:
            if field not in candidate:
                reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.{field}")

        if candidate.get("economic_evaluation_authorized") is not False:
            reasons.append(f"{REASON_ECONOMIC_EVALUATION_AUTHORIZED}:{strategy_id}")

        if candidate.get("ratified") is not True:
            reasons.append(f"{REASON_NOT_RATIFIED}:{strategy_id}")
        if candidate.get("operator_ratification_ref") != OPERATOR_RATIFICATION_REF:
            reasons.append(f"{REASON_RATIFICATION_REF_MISMATCH}:{strategy_id}")

        binding_status = candidate.get("binding_status")
        if require_ready_for_eval:
            if binding_status != BINDING_STATUS_READY_FOR_EVAL_RATIFICATION:
                reasons.append(
                    f"{REASON_BINDING_NOT_READY_FOR_EVAL}:{strategy_id}:{binding_status}"
                )
        elif binding_status == BINDING_STATUS_INCOMPLETE:
            reasons.append(f"{REASON_BINDING_INCOMPLETE}:{strategy_id}")

        instrument = candidate.get("instrument_binding")
        if isinstance(instrument, Mapping):
            _validate_instrument_binding(instrument, reasons)
        else:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.instrument_binding")

        fee = candidate.get("fee_model_binding")
        if isinstance(fee, Mapping):
            _validate_positive_cost(fee.get("fee_bps"), field="fee_bps", reasons=reasons)
        else:
            reasons.append(f"{REASON_ZERO_FEE}:{strategy_id}")

        slippage = candidate.get("slippage_model_binding")
        if isinstance(slippage, Mapping):
            _validate_positive_cost(
                slippage.get("slippage_bps"), field="slippage_bps", reasons=reasons
            )
        else:
            reasons.append(f"{REASON_ZERO_SLIPPAGE}:{strategy_id}")

        if binding_status in (
            BINDING_STATUS_VALID,
            BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        ):
            _validate_materialized_period(
                candidate.get("training_period"), name="training_period", reasons=reasons
            )
            _validate_materialized_period(
                candidate.get("validation_period"), name="validation_period", reasons=reasons
            )
            _validate_materialized_period(
                candidate.get("out_of_sample_period"),
                name="out_of_sample_period",
                reasons=reasons,
            )
            data_digest = candidate.get("data_digest")
            if not isinstance(data_digest, str) or not is_valid_digest(data_digest.strip().lower()):
                reasons.append(f"{REASON_WRONG_DATA_DIGEST}:{strategy_id}")
            shared = completion.get("shared_bindings")
            if isinstance(shared, Mapping):
                envelope = shared.get("dataset_envelope")
                if isinstance(envelope, Mapping):
                    expected_data_digest = envelope.get("data_digest")
                    if (
                        isinstance(expected_data_digest, str)
                        and data_digest != expected_data_digest
                    ):
                        reasons.append(f"{REASON_WRONG_DATA_DIGEST}:{strategy_id}")

        if allow_recompute_digests and strategy_id in STEP31F_CONFIG_PATHS:
            try:
                cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
                if candidate.get("config_digest") != compute_config_digest_v1(cfg):
                    reasons.append(f"{REASON_WRONG_CONFIG_DIGEST}:{strategy_id}")
                entry = get_strategy_registry_entry(strategy_id)
                if candidate.get("implementation_digest") != entry.implementation_digest:
                    reasons.append(f"{REASON_WRONG_IMPLEMENTATION_DIGEST}:{strategy_id}")
                resolution = resolve_strategy_id(strategy_id)
                if resolution.canonical_strategy_id != strategy_id:
                    reasons.append(f"{REASON_UNKNOWN_STRATEGY}:{strategy_id}")
                expected_semantic = compute_binding_semantic_digest_v0(candidate)
                if candidate.get("binding_semantic_digest") != expected_semantic:
                    reasons.append(f"{REASON_WRONG_BINDING_SEMANTIC_DIGEST}:{strategy_id}")
            except (FileNotFoundError, ValueError, KeyError) as exc:
                reasons.append(f"{REASON_AMBIGUOUS_BINDING}:{strategy_id}:{exc}")

        parsed_candidates.append(candidate)

    missing = sorted(expected_ids - seen_ids)
    for strategy_id in missing:
        reasons.append(f"{REASON_MISSING_CANDIDATE}:{strategy_id}")
    for strategy_id in sorted(seen_ids - expected_ids):
        reasons.append(f"{REASON_EXTRA_CANDIDATE}:{strategy_id}")

    if len(parsed_candidates) >= 2:
        reference = parsed_candidates[0]
        for field in (
            "dataset_binding",
            "period_binding",
            "instrument_binding",
            "economic_policy_binding",
            "data_digest",
        ):
            ref_value = reference.get(field)
            for candidate in parsed_candidates[1:]:
                if candidate.get(field) != ref_value:
                    if field == "economic_policy_binding":
                        reasons.append(REASON_ECONOMIC_POLICY_MISMATCH)
                    else:
                        reasons.append(
                            f"{REASON_SHARED_BINDING_MISMATCH}:{field}:{candidate.get('strategy_id')}"
                        )

    expected_completion_digest = compute_completion_digest_v0(completion)
    if completion.get("completion_digest") != expected_completion_digest:
        reasons.append(REASON_WRONG_COMPLETION_DIGEST)

    canonical = dumps_completion_canonical_v1(completion)
    if canonical != dumps_completion_canonical_v1(json.loads(canonical)):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION)
    if _ABSOLUTE_PATH_PATTERN.search(canonical):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION + ":absolute_path_in_completion")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return BindingCompletionValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
        )
    return BindingCompletionValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def clone_completion(completion: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(completion))


def serialize_completion_artifact_json_v0(completion: Mapping[str, Any]) -> str:
    return json.dumps(dict(completion), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_binding_completion_artifact_v0(
    repo_root: Path,
    *,
    completion: Mapping[str, Any],
) -> Path:
    validation = validate_final_research_fleet_versioned_binding_completion_v0(
        completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        raise ValueError(f"binding_completion_validation_failed:{validation.fail_reasons}")
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(serialize_completion_artifact_json_v0(completion), encoding="utf-8")
    return config_path


__all__ = [
    "AUTHORITY_EFFECT",
    "BINDING_STATUS_INCOMPLETE",
    "BINDING_STATUS_READY_FOR_EVAL_RATIFICATION",
    "BINDING_STATUS_VALID",
    "BindingCompletionValidationResultV0",
    "CANONICAL_SERIALIZATION_VERSION",
    "COMPLETION_ID",
    "CONFIG_REL_PATH",
    "ECONOMIC_EVALUATION_AUTHORIZED",
    "FAILED_HISTORICAL_CANDIDATES",
    "FLEET_CANDIDATES",
    "FLEET_ID",
    "FUTURES_ONLY",
    "ORDER_EFFECT",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "ValidationVerdict",
    "canonical_candidate_identifier",
    "clone_completion",
    "compute_binding_semantic_digest_v0",
    "compute_completion_digest_v0",
    "materialize_final_research_fleet_versioned_binding_completion_v0",
    "serialize_completion_artifact_json_v0",
    "serialize_completion_canonical_v0",
    "validate_final_research_fleet_versioned_binding_completion_v0",
    "write_binding_completion_artifact_v0",
]
