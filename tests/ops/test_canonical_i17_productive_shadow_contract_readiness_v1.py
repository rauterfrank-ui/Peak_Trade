"""R4 I17 PRODUCTIVE_SHADOW contract/evidence readiness tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.contract_v1 import (
    bind_optional_r3_context_v1,
    bind_r2_strategy_identity_v1,
    build_evidence_pack_contract_v1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.models_v1 import (
    I17ShadowContractReadinessError,
    IdentityPlanesV1,
    ShadowMode,
    ShadowReadinessInputV1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.preflight_v1 import (
    run_shadow_readiness_preflight_v1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.verifier_v1 import (
    evaluate_r4_i17_shadow_contract_readiness_v1,
    validate_layer_config_v1,
)

_IDENTITY = "e860a5326ac1a58fe35b723f1c32b1aa1541cfd5367bb94ac00eaf3e46971ff3"
_ORIGIN = "9f09d6d18484e35e788f5e4eaada2c598926b77f"


def _identity(**overrides: str) -> IdentityPlanesV1:
    payload = {
        "experiment_identity_id": _IDENTITY,
        "run_id": "r4_readiness_run_offline",
        "campaign_id": "r4_readiness_campaign_offline",
        "session_id": "r4_readiness_session_offline",
        "evidence_ref": "r4_readiness_evidence_offline",
        "content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "legacy_alias_md5_12": "0123456789ab",
    }
    payload.update(overrides)
    return IdentityPlanesV1(**payload)


def _input(**overrides: object) -> ShadowReadinessInputV1:
    base: dict = {
        "mode": ShadowMode.PRODUCTIVE_SHADOW,
        "strategy_id": "ma_crossover",
        "identity": _identity(),
        "origin_main_sha": _ORIGIN,
        "regime_id": "trending",
    }
    base.update(overrides)
    return ShadowReadinessInputV1(**base)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_productive_shadow_distinct_from_paper_and_simulation() -> None:
    pack = build_evidence_pack_contract_v1(_input())
    assert pack["mode"] == ShadowMode.PRODUCTIVE_SHADOW.value
    with pytest.raises(I17ShadowContractReadinessError, match="i67_cannot_substitute_i17"):
        build_evidence_pack_contract_v1(_input(mode=ShadowMode.PAPER))
    with pytest.raises(I17ShadowContractReadinessError, match="i67_cannot_substitute_i17"):
        build_evidence_pack_contract_v1(_input(mode=ShadowMode.SIMULATION))


def test_i57_cannot_substitute_i17() -> None:
    with pytest.raises(I17ShadowContractReadinessError, match="i57_cannot_substitute_i17"):
        build_evidence_pack_contract_v1(_input(mode=ShadowMode.FORWARD_SIGNAL_ONLY))
    with pytest.raises(I17ShadowContractReadinessError, match="i57_cannot_substitute_i17"):
        build_evidence_pack_contract_v1(_input(i57_as_i17=True))


def test_i67_flag_cannot_substitute_i17() -> None:
    with pytest.raises(I17ShadowContractReadinessError, match="i67_cannot_substitute_i17"):
        build_evidence_pack_contract_v1(_input(i67_as_i17=True))


def test_canonical_r2_strategy_ids_only() -> None:
    bound = bind_r2_strategy_identity_v1("ma_crossover")
    assert bound["canonical_strategy_id"] == "ma_crossover"
    assert bound["trading_grant"] is False
    with pytest.raises(I17ShadowContractReadinessError, match="unknown_strategy"):
        bind_r2_strategy_identity_v1("not_a_strategy")


def test_r3_context_remains_non_authority() -> None:
    bound = bind_optional_r3_context_v1("trending")
    assert bound["authority"] == "NONE"
    assert bound["source_class"] == "REGIME_CONTEXT"
    absent = bind_optional_r3_context_v1(None)
    assert absent["present"] is False
    with pytest.raises(I17ShadowContractReadinessError, match="unknown_regime"):
        bind_optional_r3_context_v1("fed_pause")


def test_malformed_identity_and_md5_alias_fail_closed() -> None:
    with pytest.raises(I17ShadowContractReadinessError, match="malformed_identity"):
        build_evidence_pack_contract_v1(
            _input(identity=_identity(experiment_identity_id="0123456789ab"))
        )
    with pytest.raises(I17ShadowContractReadinessError, match="md5_alias_cannot_become_canonical"):
        build_evidence_pack_contract_v1(_input(md5_as_canonical_ref=True))
    with pytest.raises(
        I17ShadowContractReadinessError, match="missing_session_or_campaign_binding"
    ):
        build_evidence_pack_contract_v1(_input(identity=_identity(session_id="")))


def test_no_order_and_no_authority_from_preflight() -> None:
    result = run_shadow_readiness_preflight_v1(_input())
    assert result["ok"] is True
    assert result["order_effect"] == "NONE"
    assert result["order_capable_path_reachable_from_r4"] is False
    assert result["productive_shadow_executed"] is False
    assert result["promotion_eligible"] is False
    pack = result["evidence_pack"]
    assert pack["trading_authority"] is False
    assert pack["promotion_authority"] is False
    assert pack["zero_order_assertion"] is True
    with pytest.raises(I17ShadowContractReadinessError, match="order_submit_path_forbidden"):
        run_shadow_readiness_preflight_v1(_input(orders_enabled=True))
    with pytest.raises(
        I17ShadowContractReadinessError, match="productive_shadow_execute_forbidden"
    ):
        run_shadow_readiness_preflight_v1(_input(execute=True))
    with pytest.raises(I17ShadowContractReadinessError, match="promotion_authority_forbidden"):
        run_shadow_readiness_preflight_v1(_input(auto_promote=True))


def test_restart_recovery_and_evidence_seal_are_deterministic() -> None:
    first = build_evidence_pack_contract_v1(_input())
    second = build_evidence_pack_contract_v1(_input())
    assert first["pack_digest"] == second["pack_digest"]
    assert first["restart_recovery_evidence"] == "CONTRACT_PRESENT_NOT_EXECUTED"
    assert first["evidence_manifest_seal"] == "SCHEMA_READY_NO_PRODUCTIVE_SEAL"


def test_evaluate_pass_does_not_claim_productive_evidence() -> None:
    claims = evaluate_r4_i17_shadow_contract_readiness_v1()
    assert claims["verdict"] == "PASS_R4_I17_SHADOW_CONTRACT_READINESS_V1"
    assert claims["r4_contract_readiness"] == "CLOSED_PROVEN_FORENSIC"
    assert claims["eg_i17_shadow_status"] == "READY_BLOCKED_PENDING_SEPARATE_SHADOW_EXECUTE_GO"
    assert claims["productive_shadow_executed"] is False
    assert claims["productive_shadow_evidence_proven"] is False
    assert claims["owner_go_shadow_execute_required"] is True
    assert claims["trading_authority_from_r4"] is False
    assert claims["promotion_authority_from_r4"] is False
    assert claims["second_shadow_runner_risk"] == "NONE_R4_POINTER_ONLY"
    assert claims["second_identity_model_risk"] == "NONE_PACKAGE_N_SHA256_ONLY"
    assert claims["max_age_role"] == MAX_AGE_ROLE
    assert claims["max_age_enforcement_enabled"] is MAX_AGE_ENFORCEMENT_ENABLED
    assert claims["r1_verdict"] == "PASS_R1_UQ6_FEATURE_DATA_CONTRACT_LAYER_V1"
    assert claims["r2_verdict"] == "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1"
    assert claims["r3_verdict"] == "PASS_R3_REGIME_META_GATED_SELECTION_V1"
    assert claims["eg_alt_verdict"] == "PASS_EG_ALT_CONSUMER_BOUNDARY_V1"
    assert claims["i17_canonical_duration_seconds"] == 7200
    assert claims["i17_extended_soak_duration_seconds"] == 21600
    assert claims["i17_extended_soak_blocks_next_phase"] is False
    assert (
        claims["i17_duration_owner"]
        == "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1"
    )


def test_config_activation_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    with pytest.raises(I17ShadowContractReadinessError, match="activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["productive_shadow_executed"] = True
    with pytest.raises(I17ShadowContractReadinessError, match="productive_shadow_executed"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_role"] = "PRODUCTIVE_GATE"
    with pytest.raises(I17ShadowContractReadinessError, match="max_age_role"):
        validate_layer_config_v1(payload)
