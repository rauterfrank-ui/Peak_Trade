"""Fail-closed models for R3 Regime/Meta gated selection v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple


class RegimeMetaGatedSelectionError(ValueError):
    """Fail-closed R3 gated-selection contract error."""


class SourceClass(str, Enum):
    MARKET_STATE = "MARKET_STATE"
    REGIME_CONTEXT = "REGIME_CONTEXT"
    META_DECISION_INPUT = "META_DECISION_INPUT"
    ADVISORY_LLM_CONTEXT = "ADVISORY_LLM_CONTEXT"
    STRATEGY_ELIGIBILITY = "STRATEGY_ELIGIBILITY"
    DETERMINISTIC_SELECTION = "DETERMINISTIC_SELECTION"
    TRADING_AUTHORITY = "TRADING_AUTHORITY"


class GateIntent(str, Enum):
    APPLY_GATED_CONTEXT = "APPLY_GATED_CONTEXT"
    ADVISORY_RECORD_ONLY = "ADVISORY_RECORD_ONLY"
    EMIT_INTENT = "EMIT_INTENT"
    SUBMIT_ORDER = "SUBMIT_ORDER"
    PROMOTE = "PROMOTE"
    MUTATE_THRESHOLD = "MUTATE_THRESHOLD"
    ACTIVATE_RUNTIME = "ACTIVATE_RUNTIME"


@dataclass(frozen=True)
class RegimeMetaGateInputV1:
    candidate_ids: Tuple[str, ...]
    regime_id: str
    source_class: SourceClass
    intent: GateIntent
    meta_context: Mapping[str, Any]
    mapping_version: str


@dataclass(frozen=True)
class RegimeMetaGateResultV1:
    regime_id: str
    source_class: SourceClass
    candidates_before: Tuple[str, ...]
    candidates_after: Tuple[str, ...]
    selected_strategy_id: str | None
    adjustment_applied: bool
    identity_digest: str
    mapping_digest: str
    result_digest: str
    authority_effect: str
    runtime_authority_impact: str
    trading_grant: bool
    promotion_authority: bool
    raw_llm_trading_authority: str
    max_age_consulted: bool
    silent_threshold_mutation: bool
    reason_codes: Tuple[str, ...]

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "adjustment_applied": self.adjustment_applied,
                "authority_effect": self.authority_effect,
                "candidates_after": list(self.candidates_after),
                "candidates_before": list(self.candidates_before),
                "identity_digest": self.identity_digest,
                "mapping_digest": self.mapping_digest,
                "max_age_consulted": self.max_age_consulted,
                "promotion_authority": self.promotion_authority,
                "raw_llm_trading_authority": self.raw_llm_trading_authority,
                "reason_codes": list(self.reason_codes),
                "regime_id": self.regime_id,
                "result_digest": self.result_digest,
                "runtime_authority_impact": self.runtime_authority_impact,
                "selected_strategy_id": self.selected_strategy_id,
                "silent_threshold_mutation": self.silent_threshold_mutation,
                "source_class": self.source_class.value,
                "trading_grant": self.trading_grant,
            }
        )
