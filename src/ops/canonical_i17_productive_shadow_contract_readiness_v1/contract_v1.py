"""Non-activating I17 PRODUCTIVE_SHADOW contract bindings (reuse existing owners)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_v1 import is_package_n_sha256_canonical_id
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    EVIDENCE_PACK_REQUIRED_FIELDS,
    ORDER_EFFECT,
    ORDER_PERMISSION_STATE,
    PROMOTION_AUTHORITY,
    PROMOTION_ELIGIBLE_DEFAULT,
    TRADING_GRANT,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.lineage_v1 import (
    digest_mapping,
    envelope_digest,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.models_v1 import (
    I17_ADMISSIBLE_MODES,
    SUBSTITUTE_MODES,
    I17ShadowContractReadinessError,
    IdentityPlanesV1,
    ShadowMode,
    ShadowReadinessInputV1,
    TerminalState,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_named_lane_identity_join_v1 import (
    is_i17_named_lane_identity_join_registered,
)
from src.regime.canonical_regime_meta_gated_selection_v1.constants_v1 import (
    KNOWN_REGIME_LABELS,
    RAW_LLM_TRADING_AUTHORITY,
)
from src.regime.canonical_regime_meta_gated_selection_v1.models_v1 import SourceClass
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    StrategyRegistrySuitabilitySelectionError,
)

CONTRACT_CODE_MARKER = "ops.canonical_i17_productive_shadow_contract_readiness_v1"


def _reject(message: str) -> None:
    raise I17ShadowContractReadinessError(message)


def assert_mode_is_i17_ladder_v1(inp: ShadowReadinessInputV1) -> None:
    if inp.i57_as_i17 or inp.mode is ShadowMode.FORWARD_SIGNAL_ONLY:
        _reject("i57_cannot_substitute_i17")
    if inp.i67_as_i17 or inp.mode in {ShadowMode.PAPER, ShadowMode.SIMULATION}:
        _reject("i67_cannot_substitute_i17")
    if inp.mode is ShadowMode.SHADOW:
        _reject("generic_shadow_is_not_productive_shadow")
    if inp.mode in {ShadowMode.TESTNET, ShadowMode.LIVE, ShadowMode.CANARY}:
        _reject(f"mode_not_i17:{inp.mode.value}")
    if inp.claim_i17 and inp.mode not in I17_ADMISSIBLE_MODES:
        _reject(f"i17_claim_requires_admissible_mode:{inp.mode.value}")
    if inp.mode in SUBSTITUTE_MODES:
        _reject(f"substitute_mode_forbidden:{inp.mode.value}")


def bind_identity_planes_v1(
    identity: IdentityPlanesV1, *, md5_as_canonical_ref: bool
) -> Mapping[str, Any]:
    if md5_as_canonical_ref:
        _reject("md5_alias_cannot_become_canonical_ref_id")
    if not is_package_n_sha256_canonical_id(identity.experiment_identity_id):
        _reject("malformed_identity:experiment_identity_id")
    if identity.legacy_alias_md5_12 is not None:
        alias = identity.legacy_alias_md5_12.strip().lower()
        if len(alias) != 12 or any(ch not in "0123456789abcdef" for ch in alias):
            _reject("malformed_identity:legacy_alias_md5_12")
        if alias == identity.experiment_identity_id:
            _reject("md5_alias_cannot_become_canonical_ref_id")
    for field_name, value in (
        ("run_id", identity.run_id),
        ("campaign_id", identity.campaign_id),
        ("session_id", identity.session_id),
        ("evidence_ref", identity.evidence_ref),
        ("content_sha256", identity.content_sha256),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"missing_session_or_campaign_binding:{field_name}")
    distinct = (
        identity.experiment_identity_id,
        identity.run_id,
        identity.campaign_id,
        identity.session_id,
        identity.evidence_ref,
        identity.content_sha256,
    )
    if len(set(distinct)) != len(distinct):
        _reject("identity_plane_collision")
    if not is_i17_named_lane_identity_join_registered():
        _reject("i17_named_lane_identity_join_unregistered")
    return MappingProxyType(
        {
            "canonical_join_key": "package_n_sha256",
            "identity": dict(identity.to_mapping()),
            "md5_12_role": "ALIAS_ONLY",
            "planes_distinct": True,
        }
    )


def bind_r2_strategy_identity_v1(strategy_id: str) -> Mapping[str, Any]:
    try:
        record = resolve_canonical_identity_v1(strategy_id)
    except StrategyRegistrySuitabilitySelectionError as exc:
        _reject(f"unknown_strategy:{strategy_id}:{exc}")
    if record.canonical_strategy_id != strategy_id and not record.alias_applied:
        _reject(f"strategy_identity_not_canonical:{strategy_id}")
    return MappingProxyType(
        {
            "alias_applied": record.alias_applied,
            "canonical_strategy_id": record.canonical_strategy_id,
            "identity_digest": record.identity_digest,
            "trading_grant": False,
        }
    )


def bind_optional_r3_context_v1(regime_id: str | None) -> Mapping[str, Any]:
    if regime_id is None:
        return MappingProxyType(
            {
                "present": False,
                "authority": "NONE",
                "raw_llm_trading_authority": RAW_LLM_TRADING_AUTHORITY,
                "source_class_forbidden": SourceClass.TRADING_AUTHORITY.value,
            }
        )
    if regime_id not in KNOWN_REGIME_LABELS:
        _reject(f"unknown_regime:{regime_id}")
    return MappingProxyType(
        {
            "present": True,
            "regime_id": regime_id,
            "authority": "NONE",
            "source_class": SourceClass.REGIME_CONTEXT.value,
            "raw_llm_trading_authority": RAW_LLM_TRADING_AUTHORITY,
        }
    )


def build_evidence_pack_contract_v1(inp: ShadowReadinessInputV1) -> Mapping[str, Any]:
    assert_mode_is_i17_ladder_v1(inp)
    identity = bind_identity_planes_v1(inp.identity, md5_as_canonical_ref=inp.md5_as_canonical_ref)
    strategy = bind_r2_strategy_identity_v1(inp.strategy_id)
    regime = bind_optional_r3_context_v1(inp.regime_id)
    pack = {
        "mode": inp.mode.value,
        "run_id": inp.identity.run_id,
        "campaign_id": inp.identity.campaign_id,
        "session_id": inp.identity.session_id,
        "experiment_identity_id": inp.identity.experiment_identity_id,
        "legacy_alias_md5_12": inp.identity.legacy_alias_md5_12,
        "origin_main_sha": inp.origin_main_sha,
        "config_digest": digest_mapping({"mode": inp.mode.value, "origin": inp.origin_main_sha}),
        "code_identity": CONTRACT_CODE_MARKER,
        "canonical_strategy_id": strategy["canonical_strategy_id"],
        "regime_meta_provenance": dict(regime),
        "timestamps": {"contract_evaluated": True, "session_started": False},
        "market_data_provenance": "NOT_CAPTURED_READINESS_ONLY",
        "decision_outputs": "NOT_CAPTURED_READINESS_ONLY",
        "risk_safety_outcomes": "NOT_CAPTURED_READINESS_ONLY",
        "zero_order_assertion": True,
        "restart_recovery_evidence": "CONTRACT_PRESENT_NOT_EXECUTED",
        "reconciliation_economic_outputs": "EVALUATOR_PRESENT_NOT_EXECUTED",
        "evidence_manifest_seal": "SCHEMA_READY_NO_PRODUCTIVE_SEAL",
        "verifier_result": "READY_BLOCKED_PENDING_SEPARATE_SHADOW_EXECUTE_GO",
        "promotion_eligible": PROMOTION_ELIGIBLE_DEFAULT,
        "promotion_eligible_reason": "NO_PRODUCTIVE_SHADOW_EVIDENCE",
        "authorization_state": "NOT_ARMED_THIS_PASS",
        "preflight_result": "PENDING_PREFLIGHT",
        "network_permission_state": False,
        "order_permission_state": ORDER_PERMISSION_STATE,
        "trading_authority": TRADING_GRANT,
        "promotion_authority": PROMOTION_AUTHORITY,
        "terminal_state": TerminalState.BLOCKED_PENDING_SHADOW_EXECUTE_GO.value,
        "identity_binding": dict(identity),
        "order_effect": ORDER_EFFECT,
    }
    missing = [field for field in EVIDENCE_PACK_REQUIRED_FIELDS if field not in pack]
    if missing:
        _reject(f"evidence_pack_missing_fields:{missing}")
    pack["pack_digest"] = envelope_digest(kind="i17_evidence_pack_contract_v1", payload=pack)
    return MappingProxyType(pack)
