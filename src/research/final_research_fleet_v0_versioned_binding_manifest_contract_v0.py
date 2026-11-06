"""Final Research Fleet v0 versioned binding manifest contract (v0).

Deterministic, fail-closed materialization and validation of operator-ratified
STEP31F fleet bindings for trend_following/v1, bollinger_bands/v1, and
momentum_1h/v1. No economic evaluation execution, no runtime or order effect.

Digest semantics (documented, single owner):
- config_digest: CANONICAL_PARSED_EVALUATION_CONFIG_v1 — SHA-256 over
  ``json.dumps(parsed_cfg, sort_keys=True, separators=(",", ":"), default=str)``
  aligned with ``compute_evaluation_config_digest_v1`` in step29m contracts.
  RAW_FILE_BYTES_SHA256 and OPERATOR_RATIFICATION_ARTIFACT_CONFIG_DIGEST_v0 are
  distinct historical semantics; operator-artifact digests are incompatible with
  current origin/main configs and must not be used for validation.
- implementation_digest: STRATEGY_REGISTRY_IMPLEMENTATION_REF_v1 — SHA-256 over
  ``{"implementation_ref": "<module.ClassName>"}`` from ``src/strategies/registry.py``.
- manifest_digest: MANIFEST_BODY_CANONICAL_JSON_v1 — SHA-256 over canonical JSON
  bytes of the manifest with ``manifest_digest`` omitted.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.backtest.strategy_signal_binding_v1 import (
    collect_configured_strategy_params_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

PACKAGE_MARKER = "FINAL_RESEARCH_FLEET_V0_VERSIONED_BINDING_MANIFEST_CONTRACT_V0=true"

SCHEMA_VERSION = "final_research_fleet_v0_versioned_binding_manifest.v0"
CANONICAL_SERIALIZATION_VERSION = "research_binding_manifest_canonical_json_v1"
FLEET_ID = "final_research_fleet_v0"
FLEET_VERSION = "v0"
MANIFEST_ID = "final_research_fleet_v0_versioned_binding_manifest_v0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

OPERATOR_RATIFICATION_REF = (
    "bounded_step31f_final_fleet_versioned_bindings_ratification_v0_20260703T000100Z"
)
ECONOMIC_EVALUATION_CLOSEOUT_REF = (
    "bounded_step31f_final_research_fleet_v0_offline_economic_validity_evaluation_"
    "closeout_v0_20260703T002500Z"
)

EXPECTED_DATASET_DIGEST = "39286384bb5baca27c93cae04716de9d8638ac62ab7d01a64c0a74c535e8d087"
EXPECTED_MANIFEST_DIGEST = "f250627c19f59b1c3245b0a5da69a646671210a1717609367f22b94d3a2a7059"
ECONOMIC_POLICY_VERSION = "economic_validity_policy_v1"

CANONICAL_INSTRUMENT_ID = "inst-eth-usdt-perp"
NATIVE_INSTRUMENT_ID = "ETH-USDT-SWAP"
SOURCE_VENUE = "OKX"

TRAINING_PERIOD = "2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00"
VALIDATION_PERIOD = "2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00"
OUT_OF_SAMPLE_PERIOD = "2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00"

FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)

FLEET_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("trend_following", "v1"),
    ("bollinger_bands", "v1"),
    ("momentum_1h", "v1"),
)

STEP31F_CONFIG_PATHS: dict[str, str] = {
    "trend_following": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
    ),
    "bollinger_bands": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json"
    ),
    "momentum_1h": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
    ),
}

ECONOMIC_EVALUATION_REFS: dict[str, str] = {
    "trend_following": (
        "bounded_step31f_trend_following_v1_offline_economic_validity_evaluation_v0_"
        "20260703T000300Z"
    ),
    "bollinger_bands": (
        "bounded_step31f_bollinger_bands_v1_offline_economic_validity_evaluation_v0_"
        "20260703T000300Z"
    ),
    "momentum_1h": (
        "bounded_step31f_momentum_1h_v1_offline_economic_validity_evaluation_v0_20260703T000300Z"
    ),
}

# Fail-closed reason codes (stable, testable).
REASON_UNKNOWN_STRATEGY = "UNKNOWN_STRATEGY"
REASON_WRONG_STRATEGY_VERSION = "WRONG_STRATEGY_VERSION"
REASON_MISSING_CANDIDATE = "MISSING_FLEET_CANDIDATE"
REASON_EXTRA_CANDIDATE = "EXTRA_FLEET_CANDIDATE"
REASON_DUPLICATE_CANDIDATE = "DUPLICATE_FLEET_CANDIDATE"
REASON_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
REASON_UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
REASON_NOT_RATIFIED = "CANDIDATE_NOT_RATIFIED"
REASON_RATIFICATION_REF_MISMATCH = "OPERATOR_RATIFICATION_REF_MISMATCH"
REASON_UNKNOWN_DATASET_VERSION = "UNKNOWN_DATASET_VERSION"
REASON_MISSING_INSTRUMENT_BINDING = "MISSING_INSTRUMENT_BINDING"
REASON_SPOT_BINDING = "SPOT_BINDING_REJECTED"
REASON_SYNTHETIC_SPOT_BINDING = "SYNTHETIC_SPOT_BINDING_REJECTED"
REASON_BITCOIN_DIRECTION_BINDING = "BITCOIN_DIRECTION_BINDING_REJECTED"
REASON_ZERO_FEE = "ZERO_FEE_REJECTED"
REASON_ZERO_SLIPPAGE = "ZERO_SLIPPAGE_REJECTED"
REASON_ECONOMIC_POLICY_MISMATCH = "ECONOMIC_POLICY_MISMATCH"
REASON_SHARED_BINDING_MISMATCH = "SHARED_BINDING_MISMATCH"
REASON_MISSING_IMPLEMENTATION_DIGEST = "MISSING_IMPLEMENTATION_DIGEST"
REASON_MISSING_DATA_DIGEST = "MISSING_DATA_DIGEST"
REASON_WRONG_CONFIG_DIGEST = "WRONG_CONFIG_DIGEST"
REASON_WRONG_IMPLEMENTATION_DIGEST = "WRONG_IMPLEMENTATION_DIGEST"
REASON_WRONG_DATA_DIGEST = "WRONG_DATA_DIGEST"
REASON_WRONG_MANIFEST_DIGEST = "WRONG_MANIFEST_DIGEST"
REASON_WRONG_STRATEGY_PARAMS_DIGEST = "WRONG_STRATEGY_PARAMS_DIGEST"
REASON_WRONG_PARAMETER_BINDING = "WRONG_PARAMETER_BINDING"
REASON_NON_CANONICAL_SERIALIZATION = "NON_CANONICAL_SERIALIZATION"
REASON_CORRUPT_JSON = "CORRUPT_JSON"
REASON_AMBIGUOUS_BINDING = "AMBIGUOUS_BINDING"
REASON_UNKNOWN_ECONOMIC_STATUS = "UNKNOWN_ECONOMIC_EVALUATION_STATUS"
REASON_ECONOMIC_STATUS_CHANGED = "ECONOMIC_EVALUATION_STATUS_CHANGED"
REASON_MISSING_EVALUATION_REF = "MISSING_ECONOMIC_EVALUATION_REF"
REASON_BINDING_REPAIR_REJECTED = "BINDING_REPAIR_REJECTED"
REASON_MANIFEST_NOT_OBJECT = "MANIFEST_NOT_OBJECT"
REASON_EFFECT_NOT_NONE = "AUTHORITY_RUNTIME_ORDER_EFFECT_NOT_NONE"
REASON_CONFIG_NOT_FOUND = "STEP31F_CONFIG_NOT_FOUND"
REASON_CONFIG_NOT_OBJECT = "STEP31F_CONFIG_NOT_OBJECT"

CANDIDATE_REQUIRED_FIELDS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "strategy_params_digest",
    "operator_ratification_ref",
    "ratified",
    "economic_evaluation_status",
    "economic_evaluation_ref",
)

MANIFEST_REQUIRED_FIELDS = (
    "schema_version",
    "manifest_id",
    "fleet_id",
    "fleet_version",
    "generated_from_config_refs",
    "candidates",
    "canonical_serialization_version",
    "manifest_digest",
    "authority_effect",
    "runtime_effect",
    "order_effect",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class FleetBindingManifestValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_config_digest_v1(cfg: Mapping[str, Any]) -> str:
    """CANONICAL_PARSED_EVALUATION_CONFIG_v1 — step29m-aligned config digest."""
    return _stable_digest(cfg)


def compute_raw_file_config_digest_v0(config_bytes: bytes) -> str:
    """RAW_FILE_BYTES_SHA256 — documented comparison semantic only."""
    return hashlib.sha256(config_bytes).hexdigest()


def compute_implementation_digest_v1(implementation_ref: str) -> str:
    """STRATEGY_REGISTRY_IMPLEMENTATION_REF_v1."""
    return _stable_digest({"implementation_ref": implementation_ref})


def dumps_manifest_canonical_v1(obj: Mapping[str, Any]) -> str:
    """Canonical JSON bytes for manifest digest (no trailing LF)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_manifest_digest_v1(manifest_body: Mapping[str, Any]) -> str:
    body = dict(manifest_body)
    body.pop("manifest_digest", None)
    return hashlib.sha256(dumps_manifest_canonical_v1(body).encode("utf-8")).hexdigest()


def serialize_manifest_canonical_v1(manifest: Mapping[str, Any]) -> str:
    """Canonical manifest serialization with trailing LF."""
    return dumps_manifest_canonical_v1(manifest) + "\n"


def _require_mapping(value: Any, *, path: str, reasons: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}")
        return None
    return value


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _reject_repair_keys(obj: Mapping[str, Any], *, path: str, reasons: list[str]) -> None:
    for key in obj:
        if key in {"repair", "fallback", "auto_fix", "default_if_missing"}:
            reasons.append(f"{REASON_BINDING_REPAIR_REJECTED}:{path}.{key}")


def load_step31f_evaluation_config_v0(repo_root: Path, strategy_id: str) -> dict[str, Any]:
    rel = STEP31F_CONFIG_PATHS[strategy_id]
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(f"{REASON_CONFIG_NOT_FOUND}:{rel}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{REASON_CONFIG_NOT_OBJECT}:{rel}")
    return payload


def _extract_parameter_binding(cfg: Mapping[str, Any], strategy_id: str) -> dict[str, Any]:
    params = collect_configured_strategy_params_v1(cfg, strategy_id)
    if not params:
        eval_section = cfg.get("economic_evaluation_v1")
        if isinstance(eval_section, Mapping):
            raw = eval_section.get("strategy_params")
            if isinstance(raw, Mapping):
                params = dict(raw)
    return dict(params)


def _extract_dataset_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    real = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(real, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":dataset_binding")
    admissibility = cfg.get("backtest", {})
    dataset_profile = "economic_research_v1"
    if isinstance(admissibility, Mapping):
        ds_adm = admissibility.get("dataset_admissibility")
        if isinstance(ds_adm, Mapping):
            profile = ds_adm.get("dataset_profile")
            if isinstance(profile, str):
                dataset_profile = profile
    return {
        "dataset_profile": dataset_profile,
        "instrument_metadata_source": "versioned_dataset_manifest_v1",
        "expected_manifest_digest": str(real.get("expected_manifest_digest", "")),
        "expected_dataset_digest": str(real.get("expected_dataset_digest", "")),
        "dataset_version": "v1",
        "pit_lifecycle_registry_bound": False,
    }


def _extract_period_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    real = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(real, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":period_binding")
    return {
        "training_period": str(real.get("training_period", "")),
        "validation_period": str(real.get("validation_period", "")),
        "out_of_sample_period": str(real.get("out_of_sample_period", "")),
    }


def _extract_instrument_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    real = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(real, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":instrument_binding")
    return {
        "canonical_instrument_id": str(real.get("canonical_instrument_id", "")),
        "native_instrument_id": str(real.get("native_instrument_id", "")),
        "venue": str(real.get("source_venue", "")),
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
    }


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


def _build_candidate_binding_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
) -> dict[str, Any]:
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        raise ValueError(REASON_MISSING_REQUIRED_FIELD + ":economic_evaluation_v1")
    cfg_strategy_id = str(eval_section.get("strategy_id", ""))
    cfg_strategy_version = str(eval_section.get("strategy_version", ""))
    if cfg_strategy_id != strategy_id:
        raise ValueError(f"{REASON_UNKNOWN_STRATEGY}:{cfg_strategy_id}")
    if cfg_strategy_version != strategy_version:
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
    config_digest = compute_config_digest_v1(cfg)
    implementation_digest = entry.implementation_digest
    data_digest = EXPECTED_DATASET_DIGEST

    ratification = cfg.get("step31f_final_fleet_policy_ratification_v1")
    if not isinstance(ratification, Mapping):
        raise ValueError(REASON_NOT_RATIFIED + f":{strategy_id}")

    return {
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "parameter_binding": parameter_binding,
        "dataset_binding": _extract_dataset_binding(cfg),
        "period_binding": _extract_period_binding(cfg),
        "instrument_binding": _extract_instrument_binding(cfg),
        "fee_model_binding": _extract_fee_model_binding(cfg),
        "slippage_model_binding": _extract_slippage_model_binding(cfg),
        "funding_model_binding": _extract_funding_model_binding(cfg),
        "execution_model_binding": _extract_execution_model_binding(cfg),
        "economic_policy_binding": _extract_economic_policy_binding(cfg),
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "data_digest": data_digest,
        "strategy_params_digest": strategy_params_digest,
        "operator_ratification_ref": OPERATOR_RATIFICATION_REF,
        "ratified": True,
        "economic_evaluation_status": "FAIL",
        "economic_evaluation_ref": ECONOMIC_EVALUATION_REFS[strategy_id],
        "source_config_ref": STEP31F_CONFIG_PATHS[strategy_id],
    }


def materialize_final_research_fleet_v0_versioned_binding_manifest_v0(
    repo_root: Path,
) -> dict[str, Any]:
    """Materialize deterministic fleet binding manifest from STEP31F configs."""
    candidates = [
        _build_candidate_binding_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
        )
        for strategy_id, strategy_version in FLEET_CANDIDATES
    ]
    candidates.sort(key=lambda item: item["strategy_id"])

    manifest_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_id": MANIFEST_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "generated_from_config_refs": [STEP31F_CONFIG_PATHS[sid] for sid, _ in FLEET_CANDIDATES],
        "candidates": candidates,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_closeout_ref": ECONOMIC_EVALUATION_CLOSEOUT_REF,
        "digest_semantics": {
            "config_digest": "CANONICAL_PARSED_EVALUATION_CONFIG_v1",
            "implementation_digest": "STRATEGY_REGISTRY_IMPLEMENTATION_REF_v1",
            "manifest_digest": "MANIFEST_BODY_CANONICAL_JSON_v1",
            "historical_operator_artifact_config_digest": (
                "OPERATOR_RATIFICATION_ARTIFACT_CONFIG_DIGEST_v0_INCOMPATIBLE"
            ),
            "raw_file_config_digest": "RAW_FILE_BYTES_SHA256_DOCUMENTATION_ONLY",
        },
        "pit_lifecycle_integration_status": "DEFERRED_FOLLOWUP_GAP",
    }
    manifest_body["manifest_digest"] = compute_manifest_digest_v1(manifest_body)
    return manifest_body


def _validate_positive_cost(value: Any, *, field: str, reasons: list[str]) -> None:
    if not isinstance(value, (int, float)) or float(value) <= 0.0:
        reasons.append(f"{REASON_ZERO_FEE if 'fee' in field else REASON_ZERO_SLIPPAGE}:{field}")


def _validate_instrument_binding(binding: Mapping[str, Any], reasons: list[str]) -> None:
    canonical = str(binding.get("canonical_instrument_id", ""))
    native = str(binding.get("native_instrument_id", ""))
    if not canonical or not native:
        reasons.append(REASON_MISSING_INSTRUMENT_BINDING)
    for token_value in (canonical, native):
        if _contains_forbidden_token(token_value):
            reasons.append(f"{REASON_BITCOIN_DIRECTION_BINDING}:{token_value}")
    if binding.get("spot_allowed") is True:
        reasons.append(REASON_SPOT_BINDING)
    if binding.get("synthetic_spot_allowed") is True:
        reasons.append(REASON_SYNTHETIC_SPOT_BINDING)
    if binding.get("bitcoin_direction_allowed") is True:
        reasons.append(REASON_BITCOIN_DIRECTION_BINDING)


def _validate_shared_candidate_bindings(
    candidates: list[Mapping[str, Any]],
    reasons: list[str],
) -> None:
    if len(candidates) < 2:
        return
    reference = candidates[0]
    ref_dataset = reference.get("dataset_binding")
    ref_period = reference.get("period_binding")
    ref_instrument = reference.get("instrument_binding")
    ref_economic = reference.get("economic_policy_binding")
    ref_data_digest = reference.get("data_digest")
    for candidate in candidates[1:]:
        if candidate.get("dataset_binding") != ref_dataset:
            reasons.append(
                f"{REASON_SHARED_BINDING_MISMATCH}:dataset_binding:{candidate.get('strategy_id')}"
            )
        if candidate.get("period_binding") != ref_period:
            reasons.append(
                f"{REASON_SHARED_BINDING_MISMATCH}:period_binding:{candidate.get('strategy_id')}"
            )
        if candidate.get("instrument_binding") != ref_instrument:
            reasons.append(
                f"{REASON_SHARED_BINDING_MISMATCH}:instrument_binding:{candidate.get('strategy_id')}"
            )
        if candidate.get("economic_policy_binding") != ref_economic:
            reasons.append(REASON_ECONOMIC_POLICY_MISMATCH)
        if candidate.get("data_digest") != ref_data_digest:
            reasons.append(
                f"{REASON_SHARED_BINDING_MISMATCH}:data_digest:{candidate.get('strategy_id')}"
            )


def validate_final_research_fleet_v0_versioned_binding_manifest_v0(
    manifest: Any,
    *,
    repo_root: Path,
    allow_recompute_digests: bool = True,
) -> FleetBindingManifestValidationResultV0:
    reasons: list[str] = []
    if not isinstance(manifest, Mapping):
        return FleetBindingManifestValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=(REASON_MANIFEST_NOT_OBJECT,),
        )

    _reject_repair_keys(manifest, path="$", reasons=reasons)

    if manifest.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_UNKNOWN_SCHEMA_VERSION)

    for field in MANIFEST_REQUIRED_FIELDS:
        if field not in manifest:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{field}")

    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if manifest.get(effect_field) != expected:
            reasons.append(f"{REASON_EFFECT_NOT_NONE}:{effect_field}")

    raw_candidates = manifest.get("candidates")
    if not isinstance(raw_candidates, list):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:candidates")
        raw_candidates = []

    expected_ids = {sid for sid, _ in FLEET_CANDIDATES}
    seen_ids: set[str] = set()
    parsed_candidates: list[Mapping[str, Any]] = []

    for index, candidate in enumerate(raw_candidates):
        path = f"candidates[{index}]"
        mapping = _require_mapping(candidate, path=path, reasons=reasons)
        if mapping is None:
            continue
        _reject_repair_keys(mapping, path=path, reasons=reasons)

        strategy_id = mapping.get("strategy_id")
        strategy_version = mapping.get("strategy_version")
        if not isinstance(strategy_id, str) or not isinstance(strategy_version, str):
            reasons.append(f"{REASON_AMBIGUOUS_BINDING}:{path}.strategy_identity")
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
            if field not in mapping:
                reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{path}.{field}")

        if mapping.get("ratified") is not True:
            reasons.append(f"{REASON_NOT_RATIFIED}:{strategy_id}")

        if mapping.get("operator_ratification_ref") != OPERATOR_RATIFICATION_REF:
            reasons.append(f"{REASON_RATIFICATION_REF_MISMATCH}:{strategy_id}")

        status = mapping.get("economic_evaluation_status")
        if status != "FAIL":
            if status in (None, "", "PASS", "INCONCLUSIVE", "UNKNOWN"):
                if status == "PASS":
                    reasons.append(f"{REASON_ECONOMIC_STATUS_CHANGED}:{strategy_id}")
                elif status in ("INCONCLUSIVE", "UNKNOWN"):
                    reasons.append(f"{REASON_ECONOMIC_STATUS_CHANGED}:{strategy_id}")
                else:
                    reasons.append(f"{REASON_UNKNOWN_ECONOMIC_STATUS}:{strategy_id}")
            else:
                reasons.append(f"{REASON_UNKNOWN_ECONOMIC_STATUS}:{strategy_id}")

        eval_ref = mapping.get("economic_evaluation_ref")
        if not isinstance(eval_ref, str) or not eval_ref.strip():
            reasons.append(f"{REASON_MISSING_EVALUATION_REF}:{strategy_id}")
        elif eval_ref != ECONOMIC_EVALUATION_REFS.get(strategy_id):
            reasons.append(f"{REASON_AMBIGUOUS_BINDING}:economic_evaluation_ref:{strategy_id}")

        instrument = mapping.get("instrument_binding")
        if isinstance(instrument, Mapping):
            _validate_instrument_binding(instrument, reasons)
        else:
            reasons.append(f"{REASON_MISSING_INSTRUMENT_BINDING}:{strategy_id}")

        fee = mapping.get("fee_model_binding")
        if isinstance(fee, Mapping):
            _validate_positive_cost(fee.get("fee_bps"), field="fee_bps", reasons=reasons)
        else:
            reasons.append(f"{REASON_ZERO_FEE}:{strategy_id}")

        slippage = mapping.get("slippage_model_binding")
        if isinstance(slippage, Mapping):
            _validate_positive_cost(
                slippage.get("slippage_bps"),
                field="slippage_bps",
                reasons=reasons,
            )
        else:
            reasons.append(f"{REASON_ZERO_SLIPPAGE}:{strategy_id}")

        dataset = mapping.get("dataset_binding")
        if isinstance(dataset, Mapping):
            if dataset.get("expected_dataset_digest") != EXPECTED_DATASET_DIGEST:
                reasons.append(f"{REASON_UNKNOWN_DATASET_VERSION}:{strategy_id}")
            if dataset.get("expected_manifest_digest") != EXPECTED_MANIFEST_DIGEST:
                reasons.append(f"{REASON_UNKNOWN_DATASET_VERSION}:{strategy_id}")
        else:
            reasons.append(f"{REASON_UNKNOWN_DATASET_VERSION}:{strategy_id}")

        if allow_recompute_digests and strategy_id in STEP31F_CONFIG_PATHS:
            try:
                cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
                expected_config_digest = compute_config_digest_v1(cfg)
                if mapping.get("config_digest") != expected_config_digest:
                    reasons.append(f"{REASON_WRONG_CONFIG_DIGEST}:{strategy_id}")

                entry = get_strategy_registry_entry(strategy_id)
                if mapping.get("implementation_digest") != entry.implementation_digest:
                    reasons.append(f"{REASON_WRONG_IMPLEMENTATION_DIGEST}:{strategy_id}")

                parameter_binding = _extract_parameter_binding(cfg, strategy_id)
                if mapping.get("parameter_binding") != parameter_binding:
                    reasons.append(f"{REASON_WRONG_PARAMETER_BINDING}:{strategy_id}")
                _, expected_params_digest = resolve_effective_strategy_params_v1(
                    strategy_id,
                    parameter_binding,
                )
                if mapping.get("strategy_params_digest") != expected_params_digest:
                    reasons.append(f"{REASON_WRONG_STRATEGY_PARAMS_DIGEST}:{strategy_id}")

                if mapping.get("data_digest") != EXPECTED_DATASET_DIGEST:
                    reasons.append(f"{REASON_WRONG_DATA_DIGEST}:{strategy_id}")
            except (FileNotFoundError, ValueError, KeyError) as exc:
                reasons.append(f"{REASON_CORRUPT_JSON}:{strategy_id}:{exc}")

        parsed_candidates.append(mapping)

    missing = sorted(expected_ids - seen_ids)
    for strategy_id in missing:
        reasons.append(f"{REASON_MISSING_CANDIDATE}:{strategy_id}")

    extra = sorted(seen_ids - expected_ids)
    for strategy_id in extra:
        reasons.append(f"{REASON_EXTRA_CANDIDATE}:{strategy_id}")

    _validate_shared_candidate_bindings(parsed_candidates, reasons)

    expected_manifest_digest = compute_manifest_digest_v1(manifest)
    if manifest.get("manifest_digest") != expected_manifest_digest:
        reasons.append(REASON_WRONG_MANIFEST_DIGEST)

    canonical = dumps_manifest_canonical_v1(manifest)
    if canonical != dumps_manifest_canonical_v1(json.loads(canonical)):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION)

    if re.search(r"/Users/[^\"]+", canonical):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION + ":absolute_path_in_manifest")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return FleetBindingManifestValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
        )
    return FleetBindingManifestValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def clone_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(manifest))
