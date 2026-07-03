"""Final Research Fleet OKX full-panel versioned binding and offline economic evaluation v0.

Deterministic, fail-closed materialization of immutable fleet bindings for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 bound to the promoted
okx_full_panel_historical_funding_archive_v0 dataset, followed by bounded offline
economic evaluation using canonical STEP29M/STEP31F owners.

Research-only. No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_VERSION,
    EconomicValidityEvaluationStatus,
)
from src.backtest.strategy_signal_binding_v1 import resolve_effective_strategy_params_v1
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    FleetTerminalStatus,
    resolve_fleet_terminal_status_v0,
    run_candidate_economic_evaluation_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    CANONICAL_INSTRUMENT_ID,
    NATIVE_INSTRUMENT_ID,
    SOURCE_VENUE,
    compute_config_digest_v1,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    CANONICAL_TRADING_LOGIC_BINDING_VERSION,
    ECONOMIC_EVALUATION_AUTHORIZED as BINDING_ECONOMIC_EVALUATION_AUTHORIZED,
    FAILED_HISTORICAL_CANDIDATES,
    FORBIDDEN_INSTRUMENT_TOKENS,
    ValidationVerdict as BindingValidationVerdict,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
    dumps_completion_canonical_v1,
)
from src.research.okx_full_panel_dataset_promotion_decision_and_binding_v0 import (
    DATASET_ID,
    DATASET_SCHEMA_VERSION,
    DATASET_VERSION,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    REGISTRY_CONFIG_REL,
)
from src.strategies.registry import get_strategy_registry_entry

PACKAGE_MARKER = (
    "FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_VERSIONED_BINDING_AND_OFFLINE_ECONOMIC_EVALUATION_V0=true"
)

SCHEMA_VERSION = (
    "final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation.v0"
)
COMPLETION_ID = "final_research_fleet_okx_full_panel_versioned_binding_completion_v0"
SCOPE_RATIFICATION_ID = (
    "final_research_fleet_okx_full_panel_offline_economic_evaluation_scope_ratification_v0"
)
EXECUTION_ID = "final_research_fleet_okx_full_panel_offline_economic_evaluation_execution_v0"
CONFIG_REL_PATH = (
    "config/research/final_research_fleet_okx_full_panel_versioned_binding_completion_v0.json"
)
SCOPE_CONFIG_REL_PATH = "config/research/final_research_fleet_okx_full_panel_offline_economic_evaluation_scope_ratification_v0.json"
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

GO_TOKEN = (
    "GO_BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
EXPECTED_ORIGIN_MAIN_SHA = "b60573f8ccfb165e3e8706912c84a99326104c5c"
OPERATOR_SCOPE_RATIFICATION_REF = (
    "bounded_versioned_final_research_fleet_bindings_and_offline_economic_evaluation_"
    "scope_v0_20260703T193500Z"
)
OPERATOR_FLEET_BINDING_RATIFICATION_REF = (
    "bounded_versioned_final_research_fleet_okx_full_panel_bindings_ratification_v0_"
    "20260703T193500Z"
)

DATASET_CONTENT_DIGEST = "0bfa4df4221a2ec27625c50e3675302ffa51e4b54cddcf81ca5ad13cc15cf8b7"
PROMOTED_DATASET_REL = f"datasets/admissible_futures/{DATASET_ID}/{DATASET_VERSION}"
PERIOD_POLICY_REL = (
    "config/research/pit_cross_sectional_research_data_digest_period_split_policy_v1.json"
)
EVALUATION_PRICE_ADAPTER_DATASET_ID = "inst-eth-usdt-perp"
EVALUATION_PRICE_ADAPTER_DATASET_VERSION = "v1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
ROUNDTRIP_COST_BPS = 40.0

STEP31F_OKX_FULL_PANEL_CONFIG_PATHS: dict[str, str] = {
    "trend_following": (
        "config/ops/step31f_okx_full_panel_eth_usdt_perp_trend_following_v1_"
        "economic_evaluation_v1.json"
    ),
    "bollinger_bands": (
        "config/ops/step31f_okx_full_panel_eth_usdt_perp_bollinger_bands_v1_"
        "economic_evaluation_v1.json"
    ),
    "momentum_1h": (
        "config/ops/step31f_okx_full_panel_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
    ),
}

REASON_REGISTRY_MISSING = "PROMOTION_REGISTRY_MISSING"
REASON_REGISTRY_DIGEST_MISMATCH = "DATASET_CONTENT_DIGEST_MISMATCH"
REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_ORIGIN_MAIN_MISMATCH = "ORIGIN_MAIN_SHA_MISMATCH"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_FAILED_HISTORICAL_CANDIDATE = "FAILED_HISTORICAL_CANDIDATE_EXCLUDED"
REASON_ALIAS_SOLE_BINDING = "ALIAS_IS_SOLE_BINDING"
REASON_IMPLICIT_ZERO_COST = "IMPLICIT_ZERO_COST"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
REASON_WRONG_COMPLETION_DIGEST = "WRONG_COMPLETION_DIGEST"
REASON_WRONG_BINDING_SEMANTIC_DIGEST = "WRONG_BINDING_SEMANTIC_DIGEST"
REASON_ECONOMIC_POLICY_MISMATCH = "ECONOMIC_POLICY_MISMATCH"
REASON_SHARED_BINDING_MISMATCH = "SHARED_BINDING_MISMATCH"

_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class IdempotentBindingStatus(str, Enum):
    NO_OP_SUCCESS = "NO_OP_SUCCESS"
    NEW_BINDING = "NEW_BINDING"
    CONFLICT_BLOCKED = "CONFLICT_BLOCKED"


@dataclass(frozen=True)
class BindingValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    idempotent_binding_status: IdempotentBindingStatus
    manifest_verify_rc: int


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0",
            "schema_version": SCHEMA_VERSION,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
        }
    )


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _native_from_canonical_instrument_id(instrument_id: str) -> str:
    parts = instrument_id.split(":")
    if len(parts) >= 4:
        return f"{parts[3]}-USDT-SWAP"
    return instrument_id


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def load_promotion_registry_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / REGISTRY_CONFIG_REL
    if not path.is_file():
        raise FileNotFoundError(f"{REASON_REGISTRY_MISSING}:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{REASON_REGISTRY_MISSING}:not_object")
    if payload.get("dataset_content_digest") != DATASET_CONTENT_DIGEST:
        raise ValueError(
            f"{REASON_REGISTRY_DIGEST_MISMATCH}:{payload.get('dataset_content_digest')}"
        )
    if payload.get("dataset_id") != DATASET_ID:
        raise ValueError(f"DATASET_ID_MISMATCH:{payload.get('dataset_id')}")
    if payload.get("dataset_version") != DATASET_VERSION:
        raise ValueError(f"DATASET_VERSION_MISMATCH:{payload.get('dataset_version')}")
    if payload.get("alias_is_not_sole_binding") is not True:
        raise ValueError(REASON_ALIAS_SOLE_BINDING)
    return payload


def load_promotion_binding_v0(
    *,
    durable_archive_root: Path,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    promoted_root = Path(str(registry["promoted_dataset_root"]))
    binding_path = promoted_root / "promotion_binding.json"
    if not binding_path.is_file():
        alt = durable_archive_root / str(registry["promotion_binding_ref"])
        binding_path = alt
    if not binding_path.is_file():
        raise FileNotFoundError(f"missing_promotion_binding:{binding_path}")
    payload = json.loads(binding_path.read_text(encoding="utf-8"))
    if payload.get("dataset_content_digest") != DATASET_CONTENT_DIGEST:
        raise ValueError(REASON_REGISTRY_DIGEST_MISMATCH)
    return payload


def _load_period_policy(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PERIOD_POLICY_REL
    return json.loads(path.read_text(encoding="utf-8"))


def _build_shared_bindings(
    *,
    promotion_binding: Mapping[str, Any],
    period_policy: Mapping[str, Any],
) -> dict[str, Any]:
    instrument_binding_src = dict(promotion_binding["instrument_binding"])
    instrument_ids = list(instrument_binding_src.get("instrument_ids", ()))
    native_ids = [_native_from_canonical_instrument_id(inst_id) for inst_id in instrument_ids]
    eth_native = NATIVE_INSTRUMENT_ID
    dataset_binding = {
        "dataset_binding_active": True,
        "dataset_binding_version": DATASET_VERSION,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "dataset_id": DATASET_ID,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "dataset_version": DATASET_VERSION,
        "promoted_dataset_ref": PROMOTED_DATASET_REL,
        "promotion_binding_ref": f"{PROMOTED_DATASET_REL}/promotion_binding.json",
        "registry_entry_ref": f"{PROMOTED_DATASET_REL}/registry_entry.json",
        "alias_ref": f"{PROMOTED_DATASET_REL}/alias/current.json",
        "alias_is_not_sole_binding": True,
        "coverage_period_start_utc": promotion_binding["period_binding"]["requested_start_time"],
        "coverage_period_end_utc": promotion_binding["period_binding"]["requested_end_time"],
        "evaluation_price_data_adapter": {
            "adapter_kind": "NARROW_ADAPTER_INST_ETH_USDT_PERP_ECONOMIC_RESEARCH_v1",
            "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
            "dataset_id": EVALUATION_PRICE_ADAPTER_DATASET_ID,
            "dataset_version": EVALUATION_PRICE_ADAPTER_DATASET_VERSION,
            "native_instrument_id": eth_native,
            "source_venue": SOURCE_VENUE,
        },
    }
    period_binding = {
        "coverage_period_end_utc": period_policy["out_of_sample_end"],
        "coverage_period_start_utc": period_policy.get(
            "coverage_period_start_utc", "2024-05-25T00:00:00Z"
        ),
        "embargo_duration": period_policy["embargo_duration"],
        "period_binding_id": period_policy["period_binding_id"],
        "period_binding_ref": f"{period_policy['period_binding_id']}:{period_policy['period_binding_version']}",
        "period_binding_version": period_policy["period_binding_version"],
        "period_digest": _stable_digest(
            {
                "dataset_id": DATASET_ID,
                "dataset_version": DATASET_VERSION,
                "dataset_content_digest": DATASET_CONTENT_DIGEST,
                "period_policy_rel": PERIOD_POLICY_REL,
            }
        ),
        "purge_duration": period_policy["purge_duration"],
        "split_policy_id": period_policy["split_policy_id"],
        "split_policy_version": period_policy["split_policy_version"],
    }
    instrument_binding = {
        "binding_mode": instrument_binding_src.get("binding_mode"),
        "bitcoin_direction_allowed": False,
        "eligible_instrument_count": len(instrument_ids),
        "eligible_instrument_ids": instrument_ids,
        "eligible_native_instrument_ids": native_ids,
        "evaluation_instrument_id": CANONICAL_INSTRUMENT_ID,
        "evaluation_native_instrument_id": eth_native,
        "futures_only": True,
        "instrument_binding_version": DATASET_VERSION,
        "instrument_selection_owner": "okx_full_panel_dataset_promotion_decision_and_binding_v0",
        "no_parallel_universe_ssot": True,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "venue_id": "okx",
    }
    return {
        "dataset_binding": dataset_binding,
        "instrument_binding": instrument_binding,
        "period_binding": period_binding,
        "period_split": {
            "boundary_semantics": period_policy["boundary_semantics"],
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "embargo_duration": period_policy["embargo_duration"],
            "out_of_sample_end": period_policy["out_of_sample_end"],
            "out_of_sample_start": period_policy["out_of_sample_start"],
            "period_binding_id": period_policy["period_binding_id"],
            "period_binding_version": period_policy["period_binding_version"],
            "period_digest": period_binding["period_digest"],
            "purge_duration": period_policy["purge_duration"],
            "split_policy_id": period_policy["split_policy_id"],
            "split_policy_version": period_policy["split_policy_version"],
            "split_timezone": period_policy["split_timezone"],
            "status": "MATERIALIZED",
            "training_end": period_policy["training_end"],
            "training_start": period_policy["training_start"],
            "validation_end": period_policy["validation_end"],
            "validation_start": period_policy["validation_start"],
        },
        "promotion_binding_ref": promotion_binding,
    }


def _build_cost_bindings(step31f_cfg: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    backtest = step31f_cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        backtest = {}
    fee_bps = float(backtest.get("fee_bps", FEE_BPS))
    slippage_bps = float(backtest.get("slippage_bps", SLIPPAGE_BPS))
    if fee_bps <= 0.0 or slippage_bps <= 0.0:
        raise ValueError(REASON_IMPLICIT_ZERO_COST)
    return {
        "fee_model_binding": {
            "fee_bps": fee_bps,
            "fee_model_version": str(
                backtest.get("fee_model_version", "backtest_fee_taker_symmetric_v0")
            ),
        },
        "slippage_model_binding": {
            "slippage_bps": slippage_bps,
            "slippage_model_version": str(
                backtest.get("slippage_model_version", "backtest_slippage_symmetric_v0")
            ),
        },
        "funding_model_binding": {
            "bind": True,
            "model_version": str(
                (backtest.get("funding") or {}).get(
                    "model_version", "backtest_funding_perpetual_interval_v1"
                )
            ),
        },
        "execution_model_binding": {
            "execution_model_version": "backtest_execution_v0",
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        },
        "economic_policy_binding": {
            "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        },
    }


def _build_candidate(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
    shared_bindings: Mapping[str, Any],
    period_policy: Mapping[str, Any],
) -> dict[str, Any]:
    step31f_path = STEP31F_OKX_FULL_PANEL_CONFIG_PATHS[strategy_id]
    if not (repo_root / step31f_path).is_file():
        raise FileNotFoundError(f"missing_step31f_config:{step31f_path}")
    cfg = json.loads((repo_root / step31f_path).read_text(encoding="utf-8"))
    entry = get_strategy_registry_entry(strategy_id)
    parameter_binding = dict(cfg["economic_evaluation_v1"]["strategy_params"])
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        strategy_id,
        parameter_binding,
    )
    cost_bindings = _build_cost_bindings(cfg)
    candidate = {
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, strategy_version
        ),
        "canonical_trading_logic_binding_version": CANONICAL_TRADING_LOGIC_BINDING_VERSION,
        "canonical_trading_logic_version": entry.semantic_digest,
        "config_digest": compute_config_digest_v1(cfg),
        "data_digest": DATASET_CONTENT_DIGEST,
        "dataset_binding": dict(shared_bindings["dataset_binding"]),
        "dataset_provenance": {
            "cross_branch_evidence_forbidden": True,
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "promoted_dataset_root": str(
                shared_bindings["dataset_binding"].get("promoted_dataset_ref")
            ),
            "promotion_binding_ref": shared_bindings["dataset_binding"]["promotion_binding_ref"],
            "pit_safe": True,
        },
        "dataset_version": DATASET_VERSION,
        "economic_evaluation_authorized": True,
        "implementation_digest": entry.implementation_digest,
        "instrument_binding": dict(shared_bindings["instrument_binding"]),
        "operator_ratification_ref": OPERATOR_FLEET_BINDING_RATIFICATION_REF,
        "out_of_sample_period": {
            "end": period_policy["out_of_sample_end"],
            "start": period_policy["out_of_sample_start"],
            "status": "MATERIALIZED",
        },
        "parameter_binding": parameter_binding,
        "parameter_schema_version": str(cfg.get("config_schema_version", "")),
        "period_binding": dict(shared_bindings["period_binding"]),
        "period_digest": shared_bindings["period_binding"]["period_digest"],
        "ratified": True,
        "reason_codes": [],
        "reproducibility_metadata": {
            "binding_semantic_digest_rule": (
                "SHA-256 over canonical JSON of semantic binding payload excluding "
                "binding_semantic_digest and completion_digest"
            ),
            "data_digest_materialization_rule": "OKX_FULL_PANEL_PROMOTED_DATASET_CONTENT_DIGEST_v0",
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "evaluation_price_data_adapter": shared_bindings["dataset_binding"][
                "evaluation_price_data_adapter"
            ],
            "materialization_module": (
                "final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0"
            ),
            "period_policy_ref": PERIOD_POLICY_REL,
            "step31f_config_ref": step31f_path,
        },
        "source_config_ref": step31f_path,
        "strategy_id": strategy_id,
        "strategy_params_digest": strategy_params_digest,
        "strategy_version": strategy_version,
        "training_period": {
            "end": period_policy["training_end"],
            "start": period_policy["training_start"],
            "status": "MATERIALIZED",
        },
        "validation_period": {
            "end": period_policy["validation_end"],
            "start": period_policy["validation_start"],
            "status": "MATERIALIZED",
        },
        **cost_bindings,
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_binding_completion_v0(
    *,
    repo_root: Path,
    durable_archive_root: Path | None = None,
) -> dict[str, Any]:
    archive_root = durable_archive_root or DEFAULT_DURABLE_ARCHIVE_ROOT
    registry = load_promotion_registry_v0(repo_root)
    promotion_binding = load_promotion_binding_v0(
        durable_archive_root=archive_root,
        registry=registry,
    )
    period_policy = _load_period_policy(repo_root)
    shared_bindings = _build_shared_bindings(
        promotion_binding=promotion_binding,
        period_policy=period_policy,
    )
    candidates = [
        _build_candidate(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            shared_bindings=shared_bindings,
            period_policy=period_policy,
        )
        for strategy_id, strategy_version in FLEET_CANDIDATES
    ]
    completion_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "completion_id": COMPLETION_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "candidates": candidates,
        "shared_bindings": {
            "dataset_binding": shared_bindings["dataset_binding"],
            "instrument_binding": shared_bindings["instrument_binding"],
            "period_binding": shared_bindings["period_binding"],
            "period_split": shared_bindings["period_split"],
        },
        "excluded_failed_historical_candidates": [
            {"strategy_id": sid, "strategy_version": ver, "retry_forbidden": True}
            for sid, ver in FAILED_HISTORICAL_CANDIDATES
        ],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_authorized": True,
        "economic_validity_offline_gate_pass": False,
        "runtime_rewire_admissible": False,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "dataset_binding_active": True,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "binding_materialization_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "implementation_digest": compute_implementation_digest_v0(),
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": GO_TOKEN,
        "digest_semantics": {
            "completion_digest": "COMPLETION_BODY_CANONICAL_JSON_v0",
            "binding_semantic_digest": "CANDIDATE_SEMANTIC_BINDING_PAYLOAD_v0",
            "config_digest": "CANONICAL_PARSED_EVALUATION_CONFIG_v1",
            "data_digest": "OKX_FULL_PANEL_DATASET_CONTENT_DIGEST_v0",
            "implementation_digest": "MODULE_IMPLEMENTATION_REF_v0",
        },
    }
    completion_body["completion_digest"] = compute_completion_digest_v0(completion_body)
    return completion_body


def validate_binding_completion_v0(
    completion: Any,
    *,
    repo_root: Path,
    allow_recompute_digests: bool = True,
) -> BindingValidationResultV0:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=("COMPLETION_NOT_OBJECT",),
        )
    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if completion.get("dataset_content_digest") != DATASET_CONTENT_DIGEST:
        reasons.append(REASON_REGISTRY_DIGEST_MISMATCH)
    if completion.get("dataset_binding_active") is not True:
        reasons.append(REASON_BINDING_INCOMPLETE)
    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if completion.get(effect_field) != expected:
            reasons.append(f"AUTHORITY_RUNTIME_ORDER_EFFECT_NOT_NONE:{effect_field}")
    expected_ids = {canonical_candidate_identifier(sid, ver) for sid, ver in FLEET_CANDIDATES}
    seen: set[str] = set()
    candidates = completion.get("candidates")
    if not isinstance(candidates, list):
        reasons.append("MISSING_CANDIDATES")
        candidates = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            reasons.append("CANDIDATE_NOT_OBJECT")
            continue
        ref = str(candidate.get("canonical_candidate_identifier", ""))
        seen.add(ref)
        pair = (str(candidate.get("strategy_id", "")), str(candidate.get("strategy_version", "")))
        if pair in FAILED_HISTORICAL_CANDIDATES:
            reasons.append(f"{REASON_FAILED_HISTORICAL_CANDIDATE}:{ref}")
        ds_binding = candidate.get("dataset_binding")
        if not isinstance(ds_binding, Mapping):
            reasons.append(f"MISSING_DATASET_BINDING:{ref}")
        else:
            if ds_binding.get("dataset_id") != DATASET_ID:
                reasons.append(f"WRONG_DATASET_ID:{ref}")
            if ds_binding.get("dataset_content_digest") != DATASET_CONTENT_DIGEST:
                reasons.append(f"WRONG_DATASET_CONTENT_DIGEST:{ref}")
            if ds_binding.get("alias_is_not_sole_binding") is not True:
                reasons.append(f"{REASON_ALIAS_SOLE_BINDING}:{ref}")
        inst = candidate.get("instrument_binding")
        if isinstance(inst, Mapping):
            if inst.get("futures_only") is not True:
                reasons.append(f"{REASON_FUTURES_ONLY_VIOLATION}:{ref}")
            for instrument_id in inst.get("eligible_instrument_ids", ()):
                if isinstance(instrument_id, str) and _contains_forbidden_token(instrument_id):
                    reasons.append(f"{REASON_BITCOIN_INSTRUMENT_PRESENT}:{instrument_id}")
        fee = candidate.get("fee_model_binding")
        slip = candidate.get("slippage_model_binding")
        if isinstance(fee, Mapping) and float(fee.get("fee_bps", 0.0)) <= 0.0:
            reasons.append(f"{REASON_IMPLICIT_ZERO_COST}:fee:{ref}")
        if isinstance(slip, Mapping) and float(slip.get("slippage_bps", 0.0)) <= 0.0:
            reasons.append(f"{REASON_IMPLICIT_ZERO_COST}:slippage:{ref}")
        policy = candidate.get("economic_policy_binding")
        if (
            not isinstance(policy, Mapping)
            or policy.get("policy_version") != ECONOMIC_VALIDITY_POLICY_VERSION
        ):
            reasons.append(f"{REASON_ECONOMIC_POLICY_MISMATCH}:{ref}")
        expected_digest = compute_binding_semantic_digest_v0(candidate)
        actual_digest = str(candidate.get("binding_semantic_digest", ""))
        if actual_digest != expected_digest:
            if allow_recompute_digests:
                reasons.append(f"{REASON_WRONG_BINDING_SEMANTIC_DIGEST}:{ref}")
            else:
                reasons.append(f"{REASON_WRONG_BINDING_SEMANTIC_DIGEST}:{ref}")
    if seen != expected_ids:
        reasons.extend(sorted(expected_ids - seen))
        reasons.extend(sorted(seen - expected_ids))
    if len(candidates) >= 2:
        reference = candidates[0]
        for field in (
            "dataset_binding",
            "period_binding",
            "instrument_binding",
            "fee_model_binding",
            "slippage_model_binding",
            "funding_model_binding",
            "execution_model_binding",
            "economic_policy_binding",
        ):
            ref_val = reference.get(field)
            for candidate in candidates[1:]:
                if candidate.get(field) != ref_val:
                    reasons.append(
                        f"{REASON_SHARED_BINDING_MISMATCH}:{field}:{candidate.get('strategy_id')}"
                    )
    expected_completion_digest = compute_completion_digest_v0(completion)
    if str(completion.get("completion_digest", "")) != expected_completion_digest:
        reasons.append(REASON_WRONG_COMPLETION_DIGEST)
    verdict = ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED
    return BindingValidationResultV0(
        verdict=verdict,
        valid=verdict is ValidationVerdict.ACCEPTED,
        fail_reasons=tuple(reasons),
    )


def materialize_scope_ratification_v0(
    *,
    binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = list(binding_completion["candidates"])
    first = candidates[0]
    ratification = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": SCOPE_RATIFICATION_ID,
        "ratification_version": "v0",
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": GO_TOKEN,
        "fleet_binding_ref": {
            "completion_id": COMPLETION_ID,
            "completion_digest": binding_completion["completion_digest"],
            "fleet_id": FLEET_ID,
            "fleet_version": FLEET_VERSION,
        },
        "fleet_binding_digest": binding_completion["completion_digest"],
        "candidate_refs": [str(c["canonical_candidate_identifier"]) for c in candidates],
        "candidate_binding_digests": {
            str(c["canonical_candidate_identifier"]): str(c["binding_semantic_digest"])
            for c in candidates
        },
        "common_dataset_policy_ref": dict(first["dataset_binding"]),
        "common_period_policy_ref": dict(first["period_binding"]),
        "common_instrument_policy_ref": dict(first["instrument_binding"]),
        "fee_model_binding": dict(first["fee_model_binding"]),
        "slippage_model_binding": dict(first["slippage_model_binding"]),
        "funding_model_binding": dict(first["funding_model_binding"]),
        "execution_model_binding": dict(first["execution_model_binding"]),
        "economic_policy_binding": dict(first["economic_policy_binding"]),
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "dataset_binding_active": True,
        "economic_evaluation_authorized": True,
        "economic_evaluation_executed": False,
        "economic_validity_offline_gate_pass": False,
        "runtime_rewire_admissible": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "operator_scope_ratification_ref": OPERATOR_SCOPE_RATIFICATION_REF,
        "implementation_digest": compute_implementation_digest_v0(),
        "ratification_digest": _stable_digest(
            {
                "completion_digest": binding_completion["completion_digest"],
                "scope_classification": SCOPE_CLASSIFICATION,
                "go_token": GO_TOKEN,
            }
        ),
    }
    return ratification


def detect_idempotent_binding_status_v0(
    *,
    repo_root: Path,
    new_completion: Mapping[str, Any],
) -> IdempotentBindingStatus:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return IdempotentBindingStatus.NEW_BINDING
    existing = json.loads(path.read_text(encoding="utf-8"))
    if existing.get("completion_digest") == new_completion.get("completion_digest"):
        return IdempotentBindingStatus.NO_OP_SUCCESS
    if existing.get("dataset_content_digest") == DATASET_CONTENT_DIGEST:
        return IdempotentBindingStatus.CONFLICT_BLOCKED
    return IdempotentBindingStatus.NEW_BINDING


def write_binding_artifacts_v0(
    *,
    repo_root: Path,
    binding_completion: Mapping[str, Any],
    scope_ratification: Mapping[str, Any],
) -> tuple[Path, Path]:
    binding_path = repo_root / CONFIG_REL_PATH
    scope_path = repo_root / SCOPE_CONFIG_REL_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(
        json.dumps(binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    scope_path.write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return binding_path, scope_path


def verify_preconditions_v0(
    *,
    repo_root: Path,
    confirm: str,
    origin_main_sha: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if confirm != GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)
    resolved = origin_main_sha or _resolve_origin_main_sha(repo_root)
    if resolved != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{resolved}")
    return not reasons, tuple(reasons)


def run_offline_economic_evaluation_v0(
    *,
    repo_root: Path,
    binding_completion: Mapping[str, Any],
    evidence_root: Path,
    skip_candidate_runs: bool = False,
) -> tuple[tuple[CandidateExecutionResultV0, ...], FleetTerminalStatus, bool]:
    candidate_results: list[CandidateExecutionResultV0] = []
    if skip_candidate_runs:
        return tuple(candidate_results), FleetTerminalStatus.INCONCLUSIVE, False
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        config_rel = STEP31F_OKX_FULL_PANEL_CONFIG_PATHS[strategy_id]
        config_path = repo_root / config_rel
        output_dir = evidence_root / "candidates" / f"{strategy_id}_{strategy_version}"
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        result = run_candidate_economic_evaluation_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=output_dir,
        )
        candidate_results.append(result)
    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    gate_pass = fleet_status is FleetTerminalStatus.PASS and all(
        r.economic_validity_offline_gate_pass for r in candidate_results
    )
    return tuple(candidate_results), fleet_status, gate_pass


def resolve_promotion_decisions_v0(
    candidate_results: Sequence[CandidateExecutionResultV0],
) -> dict[str, dict[str, bool | str]]:
    decisions: dict[str, dict[str, bool | str]] = {}
    for result in candidate_results:
        economic_validity_pass = (
            result.terminal_status.value == "PASS" and result.economic_validity_offline_gate_pass
        )
        robustness_pass = "ROBUSTNESS_FAILED" not in result.reason_codes and (
            result.terminal_status.value == "PASS"
            or result.economic_validity_result == EconomicValidityEvaluationStatus.FAIL.value
        )
        evidence_admissible = result.manifest_verify_rc == 0 and result.runner_execution_success
        promotion_eligible = (
            economic_validity_pass
            and robustness_pass
            and evidence_admissible
            and result.terminal_status.value == "PASS"
        )
        decisions[result.strategy_id] = {
            "status": result.terminal_status.value,
            "economic_validity_pass": economic_validity_pass,
            "robustness_pass": robustness_pass,
            "evidence_admissible": evidence_admissible,
            "promotion_candidate_eligible": promotion_eligible,
            "reason_codes": list(result.reason_codes),
        }
    return decisions


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    skip_candidate_runs: bool = False,
    write_repo_configs: bool = True,
) -> ScopeExecutionResultV0:
    ok, reasons = verify_preconditions_v0(repo_root=repo_root, confirm=confirm)
    if not ok:
        raise ValueError(f"PRECONDITION_FAILED:{reasons}")

    binding_completion = materialize_binding_completion_v0(
        repo_root=repo_root,
        durable_archive_root=durable_evidence_root,
    )
    validation = validate_binding_completion_v0(binding_completion, repo_root=repo_root)
    if validation.verdict is not ValidationVerdict.ACCEPTED:
        raise ValueError(f"BINDING_VALIDATION_FAILED:{validation.fail_reasons}")

    idempotent_status = detect_idempotent_binding_status_v0(
        repo_root=repo_root,
        new_completion=binding_completion,
    )
    if idempotent_status is IdempotentBindingStatus.CONFLICT_BLOCKED:
        raise ValueError("IDEMPOTENT_BINDING_CONFLICT_BLOCKED")

    scope_ratification = materialize_scope_ratification_v0(binding_completion=binding_completion)
    if write_repo_configs and idempotent_status is not IdempotentBindingStatus.NO_OP_SUCCESS:
        write_binding_artifacts_v0(
            repo_root=repo_root,
            binding_completion=binding_completion,
            scope_ratification=scope_ratification,
        )

    from datetime import datetime, timezone

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / "implementation"
        / f"bounded_versioned_final_research_fleet_bindings_and_offline_economic_evaluation_v0_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "binding_completion_v0.json").write_text(
        json.dumps(binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "scope_ratification_v0.json").write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    candidate_results, fleet_status, gate_pass = run_offline_economic_evaluation_v0(
        repo_root=repo_root,
        binding_completion=binding_completion,
        evidence_root=evidence_root,
        skip_candidate_runs=skip_candidate_runs,
    )
    promotion_decisions = resolve_promotion_decisions_v0(candidate_results)
    from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
        materialize_fleet_evaluation_summary_v0,
    )

    summary = materialize_fleet_evaluation_summary_v0(
        ratification=scope_ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=_resolve_origin_main_sha(repo_root),
    )
    summary["scope_classification"] = SCOPE_CLASSIFICATION
    summary["go_token_consumed"] = GO_TOKEN
    summary["dataset_id"] = DATASET_ID
    summary["dataset_version"] = DATASET_VERSION
    summary["dataset_content_digest"] = DATASET_CONTENT_DIGEST
    summary["promotion_decisions"] = promotion_decisions
    summary["idempotent_binding_status"] = idempotent_status.value
    (evidence_root / "fleet_evaluation_summary_v0.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)
    return ScopeExecutionResultV0(
        binding_completion=binding_completion,
        scope_ratification=scope_ratification,
        candidate_results=candidate_results,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        idempotent_binding_status=idempotent_status,
        manifest_verify_rc=rc,
    )


__all__ = [
    "GO_TOKEN",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "DATASET_ID",
    "DATASET_VERSION",
    "DATASET_CONTENT_DIGEST",
    "materialize_binding_completion_v0",
    "validate_binding_completion_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
    "ValidationVerdict",
    "IdempotentBindingStatus",
]
