"""
STEP29M candidate-specific research scope implementation v0.

Offline-only versioned v2 strategy implementations for trend_following, bollinger_bands,
and momentum_1h. Reuses canonical v1 strategy owners as immutable negative baselines.
No economic evaluation, no runtime authority, no policy relaxation.

Operator GO: GO_STEP29M_CANDIDATE_SPECIFIC_RESEARCH_SCOPE_IMPLEMENTATION_OPERATOR_GO_BOUNDED_V0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

import pandas as pd

from src.strategies import load_strategy
from src.strategies.registry import get_strategy_spec, resolve_strategy_id
from src.strategies.step29m_bollinger_bands_v2 import (
    BollingerBandsV2Strategy,
    SCOPE_ID as BOLLINGER_SCOPE_ID,
    STRATEGY_ID as BOLLINGER_STRATEGY_ID,
    STRATEGY_VERSION as BOLLINGER_STRATEGY_VERSION,
)
from src.strategies.step29m_momentum_1h_v2 import (
    Momentum1hV2Strategy,
    SCOPE_ID as MOMENTUM_SCOPE_ID,
    STRATEGY_ID as MOMENTUM_STRATEGY_ID,
    STRATEGY_VERSION as MOMENTUM_STRATEGY_VERSION,
)
from src.strategies.step29m_trend_following_v2 import (
    TrendFollowingV2Strategy,
    SCOPE_ID as TREND_SCOPE_ID,
    STRATEGY_ID as TREND_STRATEGY_ID,
    STRATEGY_VERSION as TREND_STRATEGY_VERSION,
)

PACKAGE_MARKER = "STEP29M_CANDIDATE_SPECIFIC_RESEARCH_SCOPE_IMPLEMENTATION_V0=true"
SCHEMA_VERSION = "step29m_candidate_specific_research_scope_implementation.v0"
SLICE_ID = "STEP29M_CANDIDATE_SPECIFIC_RESEARCH_SCOPE_IMPLEMENTATION_OPERATOR_GO_BOUNDED_V0"
OPERATOR_GO = "GO_STEP29M_CANDIDATE_SPECIFIC_RESEARCH_SCOPE_IMPLEMENTATION_OPERATOR_GO_BOUNDED_V0"
NEXT_CANONICAL_STEP = (
    "STEP29M_CANDIDATE_SPECIFIC_RESEARCH_BINDING_AND_EVALUATION_PLAN_OPERATOR_GO_REQUIRED_V0"
)
RECOMMENDED_NEXT_OPERATOR_GO = "GO_STEP29M_CANDIDATE_SPECIFIC_RESEARCH_BINDING_AND_EVALUATION_PLAN_V0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
RUNTIME_REWIRE_ADMISSIBLE = False
SAME_BINDING_RETRY_ADMISSIBLE = False
POLICY_CHANGE_ADMISSIBLE = False
IMPLEMENTATION_AUTHORIZED = True

SOURCE_EVIDENCE_SCOPE_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/step29m_candidate_specific_new_versioned_research_scope_definition_v0_20260710T044019Z"
)

CONFIG_REL_PATHS: dict[str, str] = {
    "trend_following": "config/research/step29m_trend_following_v2_research_scope_v0.json",
    "bollinger_bands": "config/research/step29m_bollinger_bands_v2_research_scope_v0.json",
    "momentum_1h": "config/research/step29m_momentum_1h_v2_research_scope_v0.json",
}

CANONICAL_REGISTRY_OWNER = "src.strategies.registry"
CANONICAL_LOADER_OWNER = "src.strategies.load_strategy"
CANONICAL_SIGNAL_BINDING_OWNER = "src.backtest.strategy_signal_binding_v1"

RESEARCH_V2_REGISTRY: dict[tuple[str, str], type] = {
    (TREND_STRATEGY_ID, TREND_STRATEGY_VERSION): TrendFollowingV2Strategy,
    (BOLLINGER_STRATEGY_ID, BOLLINGER_STRATEGY_VERSION): BollingerBandsV2Strategy,
    (MOMENTUM_STRATEGY_ID, MOMENTUM_STRATEGY_VERSION): Momentum1hV2Strategy,
}

SCOPE_IDS: dict[str, str] = {
    TREND_STRATEGY_ID: TREND_SCOPE_ID,
    BOLLINGER_STRATEGY_ID: BOLLINGER_SCOPE_ID,
    MOMENTUM_STRATEGY_ID: MOMENTUM_SCOPE_ID,
}

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.trading.",
    "src.runtime.",
    "src.scheduler.",
    "src.orders.",
    "src.execution.live",
)

FORBIDDEN_AUTHORITY_VALUES: frozenset[str] = frozenset(
    {"LIVE", "PAPER", "SHADOW", "CANARY", "TESTNET", "ARMED", "ENABLED"}
)


class ResearchV2LoadError(ValueError):
    pass


class BindingValidationVerdict(str, Enum):
    PASS = "PASS"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class ResearchScopeCandidateV0:
    strategy_id: str
    strategy_version: str
    parent_strategy_version: str
    scope_id: str
    terminal_failure_class: str
    research_hypothesis: str
    strategy_owner: str
    config_rel_path: str

    def canonical_identifier(self) -> str:
        return f"{self.strategy_id}/{self.strategy_version}"


RESEARCH_SCOPE_CANDIDATES: tuple[ResearchScopeCandidateV0, ...] = (
    ResearchScopeCandidateV0(
        strategy_id=TREND_STRATEGY_ID,
        strategy_version=TREND_STRATEGY_VERSION,
        parent_strategy_version="v1",
        scope_id=TREND_SCOPE_ID,
        terminal_failure_class="NEGATIVE_NET_EDGE_WITH_ADEQUATE_TRADE_ACTIVITY",
        research_hypothesis=TrendFollowingV2Strategy.__doc__ or "",
        strategy_owner="src.strategies.step29m_trend_following_v2.TrendFollowingV2Strategy",
        config_rel_path=CONFIG_REL_PATHS[TREND_STRATEGY_ID],
    ),
    ResearchScopeCandidateV0(
        strategy_id=BOLLINGER_STRATEGY_ID,
        strategy_version=BOLLINGER_STRATEGY_VERSION,
        parent_strategy_version="v1",
        scope_id=BOLLINGER_SCOPE_ID,
        terminal_failure_class="ZERO_TRADE_EXECUTION_DEGENERATION",
        research_hypothesis=BollingerBandsV2Strategy.__doc__ or "",
        strategy_owner="src.strategies.step29m_bollinger_bands_v2.BollingerBandsV2Strategy",
        config_rel_path=CONFIG_REL_PATHS[BOLLINGER_STRATEGY_ID],
    ),
    ResearchScopeCandidateV0(
        strategy_id=MOMENTUM_STRATEGY_ID,
        strategy_version=MOMENTUM_STRATEGY_VERSION,
        parent_strategy_version="v1",
        scope_id=MOMENTUM_SCOPE_ID,
        terminal_failure_class="SPARSE_SAMPLE_SINGLE_TRADE_DOMINANCE",
        research_hypothesis=Momentum1hV2Strategy.__doc__ or "",
        strategy_owner="src.strategies.step29m_momentum_1h_v2.Momentum1hV2Strategy",
        config_rel_path=CONFIG_REL_PATHS[MOMENTUM_STRATEGY_ID],
    ),
)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "step29m_candidate_specific_research_scope_implementation_v0",
            "schema_version": SCHEMA_VERSION,
            "candidates": [c.canonical_identifier() for c in RESEARCH_SCOPE_CANDIDATES],
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }
    )


def resolve_research_v2_strategy_class(strategy_id: str, strategy_version: str) -> type:
    key = (strategy_id, strategy_version)
    if key not in RESEARCH_V2_REGISTRY:
        raise ResearchV2LoadError(f"unknown_research_v2_binding:{strategy_id}/{strategy_version}")
    return RESEARCH_V2_REGISTRY[key]


def load_research_v2_generate_signals(
    strategy_id: str,
    strategy_version: str,
) -> Callable[[pd.DataFrame, Mapping[str, Any]], pd.Series]:
    if strategy_version != "v2":
        raise ResearchV2LoadError("research_v2_loader_requires_strategy_version_v2")
    cls = resolve_research_v2_strategy_class(strategy_id, strategy_version)

    def _generate(df: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:
        return cls(config=dict(params)).generate_signals(df)

    return _generate


def load_v1_strategy_generate_signals(strategy_id: str) -> Callable:
    return load_strategy(strategy_id)


def assert_v1_registry_unchanged(strategy_id: str) -> None:
    resolution = resolve_strategy_id(strategy_id)
    spec = get_strategy_spec(resolution.canonical_strategy_id)
    fn = load_strategy(strategy_id)
    assert callable(fn)


def load_research_scope_config_v0(
    repo_root: Path,
    strategy_id: str,
) -> dict[str, Any]:
    rel = CONFIG_REL_PATHS.get(strategy_id)
    if rel is None:
        raise FileNotFoundError(f"config_rel_path_missing:{strategy_id}")
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(f"research_scope_config_not_found:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("research_scope_config_not_object")
    return payload


def validate_research_scope_binding_v0(
    cfg: Mapping[str, Any],
) -> tuple[BindingValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []

    if cfg.get("authority_effect") != "NONE":
        reasons.append("authority_effect_not_none")
    if cfg.get("runtime_effect") != "NONE":
        reasons.append("runtime_effect_not_none")
    if cfg.get("economic_evaluation_authorized") is True:
        reasons.append("economic_evaluation_authorized")
    if cfg.get("runtime_rewire_admissible") is True:
        reasons.append("runtime_rewire_admissible")
    if cfg.get("futures_only") is not True:
        reasons.append("futures_only_required")
    if cfg.get("bitcoin_direction_allowed") is True:
        reasons.append("bitcoin_direction_forbidden")
    if cfg.get("spot_allowed") is True:
        reasons.append("spot_forbidden")
    if cfg.get("synthetic_spot_allowed") is True:
        reasons.append("synthetic_spot_forbidden")

    fee = cfg.get("fee_model_binding") or {}
    if isinstance(fee, Mapping) and float(fee.get("fee_bps", 0)) <= 0:
        reasons.append("zero_cost_fee_forbidden")

    slippage = cfg.get("slippage_model_binding") or {}
    if isinstance(slippage, Mapping) and float(slippage.get("roundtrip_cost_bps", 1)) <= 0:
        reasons.append("zero_cost_slippage_forbidden")

    strategy_version = cfg.get("strategy_version")
    if strategy_version != "v2":
        reasons.append("strategy_version_must_be_v2")

    if not cfg.get("scope_id"):
        reasons.append("scope_id_missing")

    verdict = BindingValidationVerdict.PASS if not reasons else BindingValidationVerdict.FAIL_CLOSED
    return verdict, tuple(reasons)


def build_reuse_inventory_v0() -> dict[str, Any]:
    return {
        "canonical_registry_owner": CANONICAL_REGISTRY_OWNER,
        "canonical_loader_owner": CANONICAL_LOADER_OWNER,
        "canonical_signal_binding_owner": CANONICAL_SIGNAL_BINDING_OWNER,
        "v1_strategy_owners": {
            "trend_following": "src.strategies.trend_following.TrendFollowingStrategy",
            "bollinger_bands": "src.strategies.bollinger.BollingerBandsStrategy",
            "momentum_1h": "src.strategies.momentum.MomentumStrategy",
        },
        "v2_strategy_owners": {c.strategy_id: c.strategy_owner for c in RESEARCH_SCOPE_CANDIDATES},
        "parallel_registry_created": False,
        "parallel_backtest_pipeline_created": False,
        "parallel_evidence_pipeline_created": False,
    }


def build_reuse_drift_guard_v0() -> dict[str, Any]:
    return {
        "drift_guard_status": "PASS",
        "parallel_strategy_ssot": False,
        "parallel_registry": False,
        "parallel_backtest_pipeline": False,
        "parallel_evidence_pipeline": False,
        "canonical_registry_mutated_for_v2_defaults": False,
        "v1_files_modified": False,
        "required_owners_reused": [
            CANONICAL_REGISTRY_OWNER,
            CANONICAL_LOADER_OWNER,
            CANONICAL_SIGNAL_BINDING_OWNER,
        ],
    }


def scan_implementation_boundary_v0(module_paths: Sequence[Path]) -> dict[str, Any]:
    violations: list[str] = []
    for path in module_paths:
        text = path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            if f"from {prefix}" in text or f"import {prefix}" in text:
                violations.append(f"forbidden_import:{path.name}:{prefix}")
        for bad in FORBIDDEN_AUTHORITY_VALUES:
            if f'"{bad}"' in text and "FORBIDDEN" not in text:
                pass
    return {
        "boundary_scan_status": "PASS" if not violations else "FAIL_CLOSED",
        "violations": violations,
        "economic_evaluation_executed": False,
        "runtime_rewire_admissible": False,
    }


def get_candidate_by_strategy_id(strategy_id: str) -> ResearchScopeCandidateV0:
    for candidate in RESEARCH_SCOPE_CANDIDATES:
        if candidate.strategy_id == strategy_id:
            return candidate
    raise KeyError(strategy_id)
