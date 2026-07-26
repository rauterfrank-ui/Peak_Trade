"""Definition-only SSOT validator for Momentum V2 vol-scaled continuation program v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1=true"
)
PROGRAM_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_"
    "research_program_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_"
    "RESEARCH_PROGRAM_V1.md"
)
REQUIRED_PROGRAM_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1"
REQUIRED_STATUS = "DEFINITION_ONLY"
REQUIRED_SIGNAL_FAMILY = "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM"
REQUIRED_TARGET = "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM_CONTINUATION"
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
REQUIRED_TREATMENT = "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM_CONTINUATION_ADMISSION"
CLOSED_CS_MOM = "config/research/material_different_cross_sectional_momentum_program_v1.json"


class ProgramValidationError(ValueError):
    """Fail-closed program SSOT validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ProgramValidationError(code)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_program_contract(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("program_family") == REQUIRED_SIGNAL_FAMILY, "FAMILY")
    _require(
        payload.get("slice_class") == "DEFINITION_ONLY_GOVERNANCE",
        "SLICE_NOT_DEFINITION_ONLY_GOVERNANCE",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("treatment_type") == REQUIRED_TREATMENT, "TREATMENT_TYPE")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(
        payload.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(
        payload.get("development_evaluation_executed") is False,
        "DEVELOPMENT_EVALUATION_EXECUTED",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("development_run_limit") == 1, "DEVELOPMENT_RUN_LIMIT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(payload.get("implementation_authorized") is True, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    causal = payload.get("causal_independence") or {}
    _require(
        causal.get("independent_from_closed_cross_sectional_momentum_lane") is True,
        "CS_MOMENTUM_DEPENDENCY",
    )
    _require(
        causal.get("independent_from_pending_momentum_1h_v2_raw_binding_evaluation") is True,
        "MOMENTUM_1H_V2_DEPENDENCY",
    )
    _require(causal.get("not_a_registry_second_truth") is True, "REGISTRY_SECOND_TRUTH")
    universe = payload.get("universe_scope") or {}
    _require(universe.get("bitcoin_excluded") is True, "BTC_EXCLUDED")
    _require(universe.get("spot_excluded") is True, "SPOT_EXCLUDED")
    if repo_root is not None:
        _require((repo_root / GOVERNANCE_REL_PATH).is_file(), "GOVERNANCE_DOC_MISSING")
        _require((repo_root / CLOSED_CS_MOM).is_file(), "CLOSED_CS_MOM_MISSING")
        closed = load_json(repo_root / CLOSED_CS_MOM)
        _require(
            closed.get("status") == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH",
            "CLOSED_CS_MOM_NOT_CLOSED",
        )
        _require(closed.get("reopen_allowed") is False, "CLOSED_CS_MOM_REOPEN_ALLOWED")
    return {
        "valid": True,
        "definition_only": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "implementation_authorized": True,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / PROGRAM_REL_PATH)
    return validate_program_contract(payload, repo_root=repo_root)
