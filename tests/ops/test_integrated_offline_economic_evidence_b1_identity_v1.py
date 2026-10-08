"""B1 canonical identity binding verifier tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

import pytest

from src.ops.integrated_offline_economic_evidence_v1.canonical_identity_verifier_v1 import (
    verify_canonical_identity_binding_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    CRS_BINDING_PRODUCTIVE_BOUNDARY,
    CRS_BINDING_RESEARCH_FIXTURE,
    DECISION_EQUIVALENCE_CLASS_FIXTURE,
    DECISION_EQUIVALENCE_CLASS_PRODUCTIVE,
    DOUBLE_PLAY_STRATEGY_INTENT_OWNER,
    EVIDENCE_SCOPE_PRODUCTIVE_CURRENT,
    EXECUTION_MODEL_ANALYTICAL_OBSERVATION_ONLY,
    EXECUTION_MODEL_MV2_BACKTEST_ENGINE,
    EXECUTION_MODEL_SIMULATED_ECONOMICS_BRIDGE,
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    MD_BRIDGE_CONTRACT_ID,
    PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_CAPABILITY_ID,
    RESIDENCY_APPLICABILITY_NOT_ENABLED,
    SIMULATED_ECONOMICS_BRIDGE_OWNER,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SHA = "a" * 40


def _d(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _minimal_productive_index(*, cap23_enabled: bool = False) -> dict[str, Any]:
    residency: dict[str, Any] = {
        "universe_snapshot_id": "uni-snap-1",
        "ranking_snapshot_id": "rank-snap-1",
        "selection_integrity_digest_sha256": _d("sel"),
        "universe_scope_class": "SINGLE_SELECTED_FUTURE",
    }
    if cap23_enabled:
        residency["residency_epoch_id"] = "epoch-1"
        residency["residency_witness_digest_sha256"] = _d("witness")
    else:
        residency["residency_applicability"] = RESIDENCY_APPLICABILITY_NOT_ENABLED

    return {
        "evidence_scope_class": EVIDENCE_SCOPE_PRODUCTIVE_CURRENT,
        "proven_source_sha": EXPECTED_SHA,
        "canonical_identity_binding_v1": {
            "trading_logic_identity_v1": {
                "replay_owner": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
                "replay_layer_version": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
                "productive_cycle_capability_id": PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_CAPABILITY_ID,
                "canonical_decision_config_digest_sha256": _d("decision_cfg"),
                "component_versions_digest_sha256": _d("components"),
                "policy_versions_digest_sha256": _d("policies"),
                "trading_logic_implementation_binding_digest_sha256": _d("impl_bind"),
            },
            "strategy_selection_identity_v1": {
                "strategy_intent_owner": DOUBLE_PLAY_STRATEGY_INTENT_OWNER,
                "suitability_registry_snapshot_digest_sha256": _d("registry"),
                "per_decision_selected_strategy_binding_ref": "decision_equivalence_rows_v1",
            },
            "instrument_identity_v1": {
                "canonical_instrument_id": "ETH-USD_UM_XPERP-310404",
                "venue": "okx_eea",
                "venue_native_id": "ETH-USD_UM_XPERP-310404",
                "market_type": "linear_perpetual",
                "contract_type": "um_xperp",
                "instrument_mapping_digest_sha256": _d("map"),
            },
            "universe_identity_v1": residency,
            "market_data_lineage_v1": {
                "md_lineage_class": "admissible_versioned_futures_offline",
                "dataset_content_digest_sha256": _d("dataset"),
                "bridge_contract_id": MD_BRIDGE_CONTRACT_ID,
                "equivalence_attestation_ref": {
                    "artifact_relpath": "attestation/md_bridge_attestation_v1.json",
                    "artifact_digest_sha256": _d("attest"),
                },
            },
            "productive_gate_binding_v1": {
                "g17_typed_volatility_binding_mode": "MUST_RECONSTRUCT",
                "cap61_observation_acceptance_binding_mode": "MUST_REPLAY",
                "confirmation_progression_binding_mode": "MUST_REPLAY",
            },
            "decision_equivalence_ref": {
                "artifact_relpath": "decision_equivalence/CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1.json",
                "artifact_digest_sha256": _d("de"),
                "equivalence_class": DECISION_EQUIVALENCE_CLASS_PRODUCTIVE,
            },
            "economic_execution_model_identity_v1": {
                "execution_model_class": EXECUTION_MODEL_SIMULATED_ECONOMICS_BRIDGE,
                "owner": SIMULATED_ECONOMICS_BRIDGE_OWNER,
                "execution_model_binding_digest_sha256": _d("exec"),
            },
            "risk_sizing_identity_v1": {
                "crs_binding_mode": CRS_BINDING_PRODUCTIVE_BOUNDARY,
                "capital_context_digest_sha256": _d("capital"),
            },
            "economic_policy_reference_v1": {
                "policy_id": "integrated_offline_economic_policy_ref",
                "policy_version": "v1",
                "policy_digest_sha256": _d("policy"),
            },
        },
    }


def test_productive_identity_minimal_pass() -> None:
    doc = _minimal_productive_index()
    result = verify_canonical_identity_binding_v1(
        index_document=doc,
        expected_proven_source_sha=EXPECTED_SHA,
        expected_canonical_decision_config_digest_sha256=_d("decision_cfg"),
        expected_component_versions_digest_sha256=_d("components"),
        expected_policy_versions_digest_sha256=_d("policies"),
        expected_trading_logic_implementation_binding_digest_sha256=_d("impl_bind"),
        expected_suitability_registry_snapshot_digest_sha256=_d("registry"),
        cap23_residency_gate_enabled=False,
    )
    assert result.verified is True


def test_productive_integrated_never_verifies_without_domains() -> None:
    doc = _minimal_productive_index()
    result = verify_integrated_offline_economic_evidence_v1(
        repo_root=REPO_ROOT,
        index_document=doc,
        expected_proven_source_sha=EXPECTED_SHA,
    )
    assert result.verified is False
    assert result.canonical_identity_verified is True


@pytest.mark.parametrize(
    "mutator,needle",
    [
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].update(
                {"universe_scope_class": "STEP29M_FLEET"}
            ),
            "FORBIDDEN_STEP29M",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["strategy_selection_identity_v1"].update(
                {
                    "strategy_id": "backtest.economic_viability_evidence_v1.foo",
                    "step29m_strategy_id_only": True,
                }
            ),
            "STEP29M",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["instrument_identity_v1"].update(
                {
                    "canonical_instrument_id": "ETH",
                    "display_symbol": "ETH",
                    "venue_native_id": "",
                }
            ),
            "DISPLAY_SYMBOL",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].pop(
                "universe_snapshot_id"
            ),
            "UNIVERSE_SNAPSHOT",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].pop(
                "selection_integrity_digest_sha256"
            ),
            "SELECTION_INTEGRITY",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].update(
                {"residency_applicability": RESIDENCY_APPLICABILITY_NOT_ENABLED}
            ),
            "RESIDENCY_EPOCH",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].update(
                {
                    "residency_epoch_id": "x",
                    "residency_applicability": RESIDENCY_APPLICABILITY_NOT_ENABLED,
                }
            ),
            "RESIDENCY_WITNESS",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["universe_identity_v1"].pop(
                "residency_applicability", None
            ),
            "RESIDENCY_APPLICABILITY",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["market_data_lineage_v1"].pop(
                "equivalence_attestation_ref"
            ),
            "EQUIVALENCE_ATTESTATION",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["market_data_lineage_v1"].update(
                {"raw_bar_loop_without_productive_gates": True}
            ),
            "RAW_BAR_LOOP",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["decision_equivalence_ref"].update(
                {
                    "equivalence_class": DECISION_EQUIVALENCE_CLASS_FIXTURE,
                    "head_bound_fixture_only": True,
                }
            ),
            "FIXTURE",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"][
                "economic_execution_model_identity_v1"
            ].update({"execution_model_class": EXECUTION_MODEL_ANALYTICAL_OBSERVATION_ONLY}),
            "ANALYTICAL",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"][
                "economic_execution_model_identity_v1"
            ].update(
                {
                    "execution_model_class": EXECUTION_MODEL_MV2_BACKTEST_ENGINE,
                    "lineage_relpath": "evidence/ops/current_6h_paper_shadow_soak_v1/x",
                }
            ),
            "MV2_BACKTEST",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["risk_sizing_identity_v1"].update(
                {"crs_binding_mode": CRS_BINDING_RESEARCH_FIXTURE}
            ),
            "RESEARCH_FIXTURE",
        ),
        (
            lambda d: d.update({"proven_source_sha": "b" * 40}),
            "PROVEN_SOURCE_SHA_MISMATCH",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["trading_logic_identity_v1"].update(
                {"canonical_decision_config_digest_sha256": _d("wrong")}
            ),
            "DECISION_CONFIG_DIGEST_MISMATCH",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["strategy_selection_identity_v1"].update(
                {"suitability_registry_snapshot_digest_sha256": _d("wrong")}
            ),
            "REGISTRY_DIGEST_MISMATCH",
        ),
        (
            lambda d: d["canonical_identity_binding_v1"]["trading_logic_identity_v1"].update(
                {"trading_logic_implementation_binding_digest_sha256": _d("wrong")}
            ),
            "IMPLEMENTATION_BINDING_DIGEST_MISMATCH",
        ),
        (
            lambda d: d.update({"offline_economic_evidence_complete": True}),
            "OFFLINE_COMPLETE",
        ),
    ],
)
def test_productive_identity_substitution_rejected(
    mutator: Callable[[dict[str, Any]], None], needle: str
) -> None:
    doc = _minimal_productive_index()
    mutator(doc)
    if needle == "RESIDENCY_EPOCH":
        result = verify_canonical_identity_binding_v1(
            index_document=doc,
            expected_proven_source_sha=EXPECTED_SHA,
            cap23_residency_gate_enabled=True,
        )
    else:
        result = verify_canonical_identity_binding_v1(
            index_document=doc,
            expected_proven_source_sha=EXPECTED_SHA,
            expected_canonical_decision_config_digest_sha256=_d("decision_cfg"),
            expected_suitability_registry_snapshot_digest_sha256=_d("registry"),
            expected_trading_logic_implementation_binding_digest_sha256=_d("impl_bind"),
            cap23_residency_gate_enabled=False,
        )
    assert result.verified is False
    joined = " ".join(result.blockers)
    assert needle.split("_")[0] in joined or needle in joined


def test_missing_expected_proven_source_sha_fail_closed() -> None:
    doc = _minimal_productive_index()
    result = verify_canonical_identity_binding_v1(index_document=doc)
    assert result.verified is False
    assert any("EXPECTED_PROVEN_SOURCE_SHA" in b for b in result.blockers)


def test_cap23_enabled_requires_residency_witness() -> None:
    doc = _minimal_productive_index()
    result = verify_canonical_identity_binding_v1(
        index_document=doc,
        expected_proven_source_sha=EXPECTED_SHA,
        cap23_residency_gate_enabled=True,
    )
    assert result.verified is False
    assert any("RESIDENCY" in b for b in result.blockers)
