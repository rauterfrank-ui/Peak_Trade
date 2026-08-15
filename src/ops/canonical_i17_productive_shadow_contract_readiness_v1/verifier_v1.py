"""Fail-closed verifier for R4 I17 PRODUCTIVE_SHADOW contract readiness v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.features.canonical_alt_data_consumer_boundary_v1.verifier_v1 import (
    evaluate_eg_alt_consumer_v1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CANONICAL_SHADOW_CONTRACT_OWNER,
    CANONICAL_SHADOW_EVIDENCE_OWNER,
    CANONICAL_SHADOW_IDENTITY_BINDING,
    CANONICAL_SHADOW_PROMOTION_CONSUMER,
    CANONICAL_SHADOW_RUNNER_OWNER,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CURRENT_ROLE,
    CURRENT_STATE,
    DONE_CRITERION,
    I57_CLASSIFICATION,
    I67_CLASSIFICATION,
    LIVE_AUTHORIZED,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
    ORDER_EFFECT,
    I17_CANONICAL_DURATION_SECONDS,
    I17_DURATION_OWNER_FAMILY,
    I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE,
    I17_EXTENDED_SOAK_DURATION_SECONDS,
    OWNER_GO_SHADOW_EXECUTE_REQUIRED,
    PACKAGE_MARKER,
    PRODUCTIVE_SHADOW_EVIDENCE_PROVEN,
    PRODUCTIVE_SHADOW_EXECUTED,
    PROMOTION_AUTHORITY,
    REMEDIATION_ID,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_EFFECT,
    SOURCE_GAP_IDS,
    SOURCE_INTENT,
    TARGET,
    TESTNET_AUTHORIZED,
    TRADING_GRANT,
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
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    ORDER_EFFECT_NONE as IPSO_ORDER_EFFECT_NONE,
    WALLCLOCK_SESSION_EXECUTION_ALLOWED,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ORDER_EFFECT_NONE as WALLCLOCK_ORDER_EFFECT_NONE,
)

_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.broker",
        "src.live",
        "src.execution.live",
        "src.sim.paper",
        "src.forward",
    }
)
_PACKAGE_REL = Path("src") / "ops" / "canonical_i17_productive_shadow_contract_readiness_v1"
_EXPECTED_ORIGIN = "9f09d6d18484e35e788f5e4eaada2c598926b77f"
_FIXTURE_IDENTITY = "e860a5326ac1a58fe35b723f1c32b1aa1541cfd5367bb94ac00eaf3e46971ff3"


def _reject(message: str) -> None:
    raise I17ShadowContractReadinessError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def assert_package_has_no_order_or_substitute_imports_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                    if name == forbidden or name.startswith(f"{forbidden}."):
                        _reject(f"forbidden_import:{path.name}:{name}")
                if "productive_run_entrypoint_v1" in name:
                    _reject(f"productive_run_import:{path.name}:{name}")
                if "eea_public_md_transport_v1" in name:
                    _reject(f"network_transport_import:{path.name}:{name}")


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "current_role", CURRENT_ROLE)
    _require(payload, "current_state", CURRENT_STATE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "i57_classification", I57_CLASSIFICATION)
    _require(payload, "i67_classification", I67_CLASSIFICATION)
    _require(payload, "live_authorized", False)
    _require(payload, "max_age_enforcement_enabled", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "i17_canonical_duration_seconds", I17_CANONICAL_DURATION_SECONDS)
    _require(payload, "i17_duration_owner", I17_DURATION_OWNER_FAMILY)
    _require(payload, "i17_extended_soak_blocks_next_phase", I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE)
    _require(payload, "i17_extended_soak_duration_seconds", I17_EXTENDED_SOAK_DURATION_SECONDS)
    _require(payload, "owner_go_shadow_execute_required", True)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_shadow_evidence_proven", False)
    _require(payload, "productive_shadow_executed", False)
    _require(payload, "promotion_authority", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_authority_impact", RUNTIME_AUTHORITY_IMPACT)
    _require(payload, "runtime_effect", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "source_intent", SOURCE_INTENT)
    _require(payload, "target", TARGET)
    _require(payload, "testnet_authorized", False)
    _require(payload, "trading_grant", False)
    _require(payload, "canonical_shadow_contract_owner", CANONICAL_SHADOW_CONTRACT_OWNER)
    _require(payload, "canonical_shadow_runner_owner", CANONICAL_SHADOW_RUNNER_OWNER)
    _require(payload, "canonical_shadow_evidence_owner", CANONICAL_SHADOW_EVIDENCE_OWNER)
    _require(payload, "canonical_shadow_identity_binding", CANONICAL_SHADOW_IDENTITY_BINDING)
    _require(payload, "canonical_shadow_promotion_consumer", CANONICAL_SHADOW_PROMOTION_CONSUMER)


def _fixture_input() -> ShadowReadinessInputV1:
    return ShadowReadinessInputV1(
        mode=ShadowMode.PRODUCTIVE_SHADOW,
        strategy_id="ma_crossover",
        identity=IdentityPlanesV1(
            experiment_identity_id=_FIXTURE_IDENTITY,
            run_id="r4_readiness_run_offline",
            campaign_id="r4_readiness_campaign_offline",
            session_id="r4_readiness_session_offline",
            evidence_ref="r4_readiness_evidence_offline",
            content_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            legacy_alias_md5_12="0123456789ab",
        ),
        origin_main_sha=_EXPECTED_ORIGIN,
        regime_id="trending",
    )


def evaluate_r4_i17_shadow_contract_readiness_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_has_no_order_or_substitute_imports_v1(root)
    if WALLCLOCK_SESSION_EXECUTION_ALLOWED is not False:
        _reject("ipso_wallclock_execution_allowed")
    if IPSO_ORDER_EFFECT_NONE != "NONE" or WALLCLOCK_ORDER_EFFECT_NONE != "NONE":
        _reject("existing_i17_order_effect_not_none")
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_SHADOW_EXECUTED,
            PRODUCTIVE_SHADOW_EVIDENCE_PROVEN,
            TRADING_GRANT,
            PROMOTION_AUTHORITY,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_EXECUTE,
            MAX_AGE_ENFORCEMENT_ENABLED,
        )
    ):
        _reject("authority_or_execution_flag_raised")
    preflight = run_shadow_readiness_preflight_v1(_fixture_input(), root=root)
    alt = evaluate_eg_alt_consumer_v1(root=root)
    if alt["verdict"] != "PASS_EG_ALT_CONSUMER_BOUNDARY_V1":
        _reject(f"eg_alt_regression:{alt['verdict']}")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "canonical_shadow_contract_owner": CANONICAL_SHADOW_CONTRACT_OWNER,
        "canonical_shadow_evidence_owner": CANONICAL_SHADOW_EVIDENCE_OWNER,
        "canonical_shadow_identity_binding": CANONICAL_SHADOW_IDENTITY_BINDING,
        "canonical_shadow_promotion_consumer": CANONICAL_SHADOW_PROMOTION_CONSUMER,
        "canonical_shadow_runner_owner": CANONICAL_SHADOW_RUNNER_OWNER,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "eg_alt_verdict": alt["verdict"],
        "eg_i17_shadow_status": "READY_BLOCKED_PENDING_SEPARATE_SHADOW_EXECUTE_GO",
        "i17_canonical_duration_seconds": I17_CANONICAL_DURATION_SECONDS,
        "i17_duration_owner": I17_DURATION_OWNER_FAMILY,
        "i17_extended_soak_blocks_next_phase": I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE,
        "i17_extended_soak_duration_seconds": I17_EXTENDED_SOAK_DURATION_SECONDS,
        "i57_classification": I57_CLASSIFICATION,
        "i67_classification": I67_CLASSIFICATION,
        "live_authorized": LIVE_AUTHORIZED,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_role": MAX_AGE_ROLE,
        "network_capable_path_present_but_not_executed": True,
        "order_capable_path_reachable_from_r4": False,
        "order_effect": ORDER_EFFECT,
        "owner_go_shadow_execute_required": OWNER_GO_SHADOW_EXECUTE_REQUIRED,
        "package_marker": PACKAGE_MARKER,
        "preflight_ok": bool(preflight["ok"]),
        "productive_shadow_evidence_proven": False,
        "productive_shadow_executed": False,
        "promotion_authority_from_r4": False,
        "r1_verdict": alt["r1_verdict"],
        "r2_verdict": alt["r2_verdict"],
        "r3_verdict": alt["r3_verdict"],
        "r4_contract_readiness": "CLOSED_PROVEN_FORENSIC",
        "remediation_id": REMEDIATION_ID,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "second_identity_model_risk": "NONE_PACKAGE_N_SHA256_ONLY",
        "second_promotion_path_risk": "NONE_I16_EVIDENCE_CLASS_NOT_AUTO_GRANT",
        "second_shadow_evidence_owner_risk": "NONE_IPSO_EVIDENCE_OWNER",
        "second_shadow_runner_risk": "NONE_R4_POINTER_ONLY",
        "trading_authority_from_r4": False,
        "verdict": "PASS_R4_I17_SHADOW_CONTRACT_READINESS_V1",
    }
    return MappingProxyType(claims)
