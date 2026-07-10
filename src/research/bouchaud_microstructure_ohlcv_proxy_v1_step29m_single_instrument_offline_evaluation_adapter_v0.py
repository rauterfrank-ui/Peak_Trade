"""Bouchaud microstructure OHLCV proxy v1 STEP29M single-instrument offline adapter v0.

Thin scope-specific adapter wiring. Reuses canonical STEP29M owners without
duplicating strategy, signal, sizing, cost, dataset, digest, or backtest logic.
No economic evaluation execution in the implementation slice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"
HYPOTHESIS_ID = "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1"
REGISTRY_STRATEGY_ID = "bouchaud_microstructure"
STRATEGY_VERSION = "v1"
STRATEGY_OWNER = (
    "src.strategies.bouchaud.bouchaud_microstructure_strategy.BouchaudMicrostructureStrategy"
)

DATA_CLASS = "FINALIZED_OHLCV_BARS"
PROXY_SEMANTICS = True
PROXY_DESCRIPTION = "BAR_LEVEL_PRESSURE_AND_IMPACT_PROXY_USING_FINALIZED_OHLCV_FEATURES"
TRUE_TICK_L2_MICROSTRUCTURE = False
TICK_DATA_REQUIRED = False
ORDERBOOK_DATA_REQUIRED = False
DEPTH_DATA_REQUIRED = False
L2_DATA_REQUIRED = False

RESERVED_TICK_L2_SCOPE = "bouchaud_microstructure_tick_l2/v1"
RESERVED_TICK_L2_STATUS = "NOT_IMPLEMENTED_DATA_CAPABILITY_MISSING"

IMPLEMENTATION_GO_TOKEN = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_STEP29M_SINGLE_INSTRUMENT_"
    "OFFLINE_EVALUATION_ADAPTER_IMPLEMENTATION_V0"
)
EVALUATION_GO_TOKEN = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0"
)

ALLOWED_IMPLEMENTATION_GO_TOKENS = frozenset({IMPLEMENTATION_GO_TOKEN})
ALLOWED_EVALUATION_GO_TOKENS = frozenset({EVALUATION_GO_TOKEN})

DEFAULT_EVALUATION_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_bouchaud_microstructure_ohlcv_proxy_v1_"
    "economic_evaluation_v1.json"
)
VERSIONED_BINDING_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
SCOPE_SEPARATION_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_scope_separation_contract_v0.json"
)
MATERIAL_DIFFERENCE_PATH = "config/research/bouchaud_microstructure_ohlcv_proxy_v1_material_difference_and_non_claim_contract_v0.json"

ADAPTER_OWNER = (
    "research.bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_"
    "offline_evaluation_adapter_v0"
)
ADAPTER_VERSION = "v0"
SCHEMA_VERSION = (
    "bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter.v0"
)

SAFETY_FLAGS: dict[str, Any] = {
    "futures_only": True,
    "bitcoin_direction_allowed": False,
    "spot_allowed": False,
    "synthetic_spot_allowed": False,
    "offline_only": True,
    "economic_evaluation_executed": False,
    "runtime_effect": "NONE",
    "authority_effect": "NONE",
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "proxy_semantics": True,
    "true_tick_l2_microstructure": False,
}


class GoTokenClassification(str, Enum):
    IMPLEMENTATION = "IMPLEMENTATION"
    EVALUATION = "EVALUATION"
    REJECTED = "REJECTED"


class AdapterExecutionMode(str, Enum):
    IMPLEMENTATION_ONLY = "IMPLEMENTATION_ONLY"
    EVALUATION_BLOCKED = "EVALUATION_BLOCKED"


@dataclass(frozen=True)
class GoTokenValidationResultV0:
    classification: GoTokenClassification
    accepted_for_validation_only: bool
    execution_mode: AdapterExecutionMode
    blocking_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "accepted_for_validation_only": self.accepted_for_validation_only,
            "execution_mode": self.execution_mode.value,
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass(frozen=True)
class AdapterMaterializationResultV0:
    verdict: str
    research_scope: str
    hypothesis_id: str
    config_digest: str
    implementation_digest: str
    strategy_params_digest: str
    admissibility_result: str
    blocking_reasons: tuple[str, ...]
    economic_evaluation_executed: bool
    runtime_effect: str
    authority_effect: str
    go_token_classification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "research_scope": self.research_scope,
            "hypothesis_id": self.hypothesis_id,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "strategy_params_digest": self.strategy_params_digest,
            "admissibility_result": self.admissibility_result,
            "blocking_reasons": list(self.blocking_reasons),
            "economic_evaluation_executed": self.economic_evaluation_executed,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
            "go_token_classification": self.go_token_classification,
        }


def classify_go_token_v0(operator_go: str) -> GoTokenValidationResultV0:
    if operator_go in ALLOWED_IMPLEMENTATION_GO_TOKENS:
        return GoTokenValidationResultV0(
            classification=GoTokenClassification.IMPLEMENTATION,
            accepted_for_validation_only=True,
            execution_mode=AdapterExecutionMode.IMPLEMENTATION_ONLY,
            blocking_reasons=(),
        )
    if operator_go in ALLOWED_EVALUATION_GO_TOKENS:
        return GoTokenValidationResultV0(
            classification=GoTokenClassification.EVALUATION,
            accepted_for_validation_only=True,
            execution_mode=AdapterExecutionMode.EVALUATION_BLOCKED,
            blocking_reasons=("evaluation_go_blocked_in_implementation_slice",),
        )
    return GoTokenValidationResultV0(
        classification=GoTokenClassification.REJECTED,
        accepted_for_validation_only=False,
        execution_mode=AdapterExecutionMode.EVALUATION_BLOCKED,
        blocking_reasons=(f"invalid_go_token:{operator_go}",),
    )


def load_scope_separation_contract_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SCOPE_SEPARATION_PATH
    if not path.is_file():
        raise FileNotFoundError(f"scope_separation_contract_not_found:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scope_separation_contract_not_object")
    return payload


def verify_scope_separation_contract_v0(contract: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if contract.get("research_scope") != RESEARCH_SCOPE:
        reasons.append("scope_separation_research_scope_mismatch")
    if contract.get("hypothesis_id") != HYPOTHESIS_ID:
        reasons.append("scope_separation_hypothesis_id_mismatch")
    if contract.get("proxy_semantics") is not True:
        reasons.append("scope_separation_proxy_semantics_not_true")
    if contract.get("true_tick_l2_microstructure") is not False:
        reasons.append("scope_separation_true_tick_l2_not_false")
    if contract.get("data_class") != DATA_CLASS:
        reasons.append("scope_separation_data_class_mismatch")
    for flag, expected in (
        ("tick_data_required", False),
        ("orderbook_data_required", False),
        ("depth_data_required", False),
        ("l2_data_required", False),
    ):
        if contract.get(flag) is not expected:
            reasons.append(f"scope_separation_{flag}_mismatch")
    reserved = contract.get("reserved_non_implemented_scopes")
    if not isinstance(reserved, list) or not reserved:
        reasons.append("reserved_tick_l2_scope_missing")
    else:
        tick_l2 = reserved[0]
        if not isinstance(tick_l2, Mapping):
            reasons.append("reserved_tick_l2_scope_not_object")
        else:
            if tick_l2.get("research_scope") != RESERVED_TICK_L2_SCOPE:
                reasons.append("reserved_tick_l2_scope_id_mismatch")
            if tick_l2.get("status") != RESERVED_TICK_L2_STATUS:
                reasons.append("reserved_tick_l2_status_mismatch")
            if tick_l2.get("evaluation_admissible") is not False:
                reasons.append("reserved_tick_l2_evaluation_admissible_not_false")
    return tuple(reasons)


def verify_tick_l2_scope_rejected_v0(research_scope: str) -> tuple[str, ...]:
    if research_scope == RESERVED_TICK_L2_SCOPE:
        return ("tick_l2_scope_not_implemented",)
    return ()


def run_adapter_implementation_v0(
    *,
    repo_root: Path,
    confirm_operator_go: str,
) -> AdapterMaterializationResultV0:
    from src.backtest.step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 import (
        evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1,
    )
    from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (
        compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0,
    )

    go_result = classify_go_token_v0(confirm_operator_go)
    if go_result.classification is GoTokenClassification.REJECTED:
        raise SystemExit(f"ERR: {go_result.blocking_reasons[0]}")

    if go_result.classification is GoTokenClassification.EVALUATION:
        raise SystemExit("ERR: evaluation_go_blocked_in_implementation_slice")

    scope_contract = load_scope_separation_contract_v0(repo_root)
    scope_reasons = verify_scope_separation_contract_v0(scope_contract)
    if scope_reasons:
        raise SystemExit(f"ERR: scope_separation_blocked:{scope_reasons}")

    admissibility = evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=repo_root,
    )
    implementation_digest = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(repo_root)

    verdict = (
        "PASS_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_STEP29M_SINGLE_INSTRUMENT_"
        "OFFLINE_EVALUATION_ADAPTER_IMPLEMENTATION_V0"
        if admissibility.admissibility_result.value == "PASS"
        else "BLOCKED_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_ADAPTER_IMPLEMENTATION_V0"
    )

    return AdapterMaterializationResultV0(
        verdict=verdict,
        research_scope=RESEARCH_SCOPE,
        hypothesis_id=HYPOTHESIS_ID,
        config_digest=admissibility.config_digest,
        implementation_digest=implementation_digest,
        strategy_params_digest=admissibility.strategy_params_digest,
        admissibility_result=admissibility.admissibility_result.value,
        blocking_reasons=admissibility.blocking_reasons,
        economic_evaluation_executed=False,
        runtime_effect="NONE",
        authority_effect="NONE",
        go_token_classification=go_result.classification.value,
    )
