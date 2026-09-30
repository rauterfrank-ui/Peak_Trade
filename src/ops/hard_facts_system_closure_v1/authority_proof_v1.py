"""Static authority / boundary proof for hard-facts closure."""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    CAP22_RANKING_CONTEXT_ONLY,
    CAP23_SOLE_SELECTION_AUTHORITY,
    CAP24_BIND_ONLY,
    CASE_SWITCH_CANONICAL_OWNER,
    CASE_SWITCH_MODEL,
    DOUBLE_PLAY_TRADING_DECISION_SEMANTICS,
    EXTERNAL_EFFECT_AUTHORIZED,
    INTELLIGENCE_ZERO_TRADING_DECISION_AUTHORITY,
    MASTER_V2_ORCHESTRATION_ONLY,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    POST_ALLOWED,
    PRE_EXTERNAL_TERMINAL,
    SUPERVISOR_ZERO_ECONOMIC_AUTHORITY,
)


@dataclass(frozen=True)
class HardFactsAuthorityProofResultV1:
    ok: bool
    authority_matrix: dict[str, bool]
    safety_flags: dict[str, bool]


def prove_hard_facts_authority_invariants_v1() -> HardFactsAuthorityProofResultV1:
    matrix = {
        "case_switch_model": CASE_SWITCH_MODEL == "COMPOSED_OWNER_CHAIN",
        "case_switch_canonical_owner_none": CASE_SWITCH_CANONICAL_OWNER == "NONE",
        "cap22_ranking_context_only": CAP22_RANKING_CONTEXT_ONLY,
        "cap23_sole_selection_authority": CAP23_SOLE_SELECTION_AUTHORITY,
        "cap24_bind_only": CAP24_BIND_ONLY,
        "master_v2_orchestration_only": MASTER_V2_ORCHESTRATION_ONLY,
        "double_play_trading_decision_semantics": DOUBLE_PLAY_TRADING_DECISION_SEMANTICS,
        "intelligence_zero_trading_decision_authority": INTELLIGENCE_ZERO_TRADING_DECISION_AUTHORITY,
        "supervisor_zero_economic_authority": SUPERVISOR_ZERO_ECONOMIC_AUTHORITY,
        "pre_external_terminal": PRE_EXTERNAL_TERMINAL,
    }
    safety = {
        "post_allowed": POST_ALLOWED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "n_gt_1_enabled": N_GT_1_ENABLED,
        "max_positions_effective": int(MAX_POSITIONS_EFFECTIVE) == 1,
    }
    ok = (
        all(matrix.values())
        and not safety["post_allowed"]
        and not safety["external_effect_authorized"]
    )
    return HardFactsAuthorityProofResultV1(ok=ok, authority_matrix=matrix, safety_flags=safety)
