"""R5 realistic sim/replay semantics tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_realistic_sim_replay_semantics_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    I67_ROLE,
    I79_ROLE,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
    REQUIRED_OWNER_RELPATHS,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.matrix_v1 import (
    MODE_CLASS_ROWS,
    REQUIRED_DIMENSIONS,
    SEMANTICS_MATRIX,
    require_dimension,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.models_v1 import (
    EquivalenceClass,
    ModeClass,
    RealisticSimReplaySemanticsError,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.verifier_v1 import (
    evaluate_r5_realistic_sim_replay_v1,
    reject_equivalence_claim_v1,
    validate_layer_config_v1,
)
from src.sim.paper.simulator import PaperTradingSimulator


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_required_owners_exist() -> None:
    root = repo_root()
    for rel in REQUIRED_OWNER_RELPATHS:
        path = root / rel
        if rel.endswith("/"):
            assert path.is_dir(), rel
        else:
            assert path.is_file(), rel


def test_matrix_covers_required_dimensions_with_distinct_cells() -> None:
    assert tuple(row.dimension for row in SEMANTICS_MATRIX) == REQUIRED_DIMENSIONS
    for row in SEMANTICS_MATRIX:
        assert row.equivalence is EquivalenceClass.DISTINCT
        cells = {
            row.cap7_internal_sim,
            row.cap7_offline_md_replay,
            row.i67_paper_sim,
            row.i79_replay_pack,
            row.i17_productive_shadow,
        }
        assert len(cells) == 5, row.dimension
    assert require_dimension("promotion_eligibility").i67_paper_sim.endswith("promotion_substitute")


def test_mode_classes_are_non_authoritative_and_include_paper_exchange_forbid() -> None:
    modes = [row.mode for row in MODE_CLASS_ROWS]
    assert ModeClass.SIMULATION in modes
    assert ModeClass.PAPER in modes
    assert ModeClass.REPLAY in modes
    assert ModeClass.SHADOW in modes
    assert ModeClass.PRODUCTIVE_SHADOW in modes
    assert ModeClass.PAPER_EXCHANGE in modes
    for row in MODE_CLASS_ROWS:
        assert row.promotion_eligible is False
        assert row.order_effect == "NONE"
        assert row.authority_effect == "NONE"
    paper_exchange = next(row for row in MODE_CLASS_ROWS if row.mode is ModeClass.PAPER_EXCHANGE)
    assert paper_exchange.canonical_surface == "FORBIDDEN_THIS_PASS"


def test_i67_owner_is_local_paper_simulator() -> None:
    assert PaperTradingSimulator.__module__ == "src.sim.paper.simulator"
    assert I67_ROLE == "GOVERNED_SUPPORTING_SIMULATION"
    assert I79_ROLE == "GOVERNED_SUPPORTING_NON_AUTHORITATIVE_REPLAY"


def test_equivalence_claims_fail_closed() -> None:
    reject_equivalence_claim_v1(left="I67", right="CAP7", claimed_equivalent=False)
    with pytest.raises(RealisticSimReplaySemanticsError, match="equivalence_unproven:I67:I17"):
        reject_equivalence_claim_v1(left="I67", right="I17", claimed_equivalent=True)
    with pytest.raises(RealisticSimReplaySemanticsError, match="self_equivalence_forbidden"):
        reject_equivalence_claim_v1(left="I79", right="I79", claimed_equivalent=False)


def test_evaluate_pass_does_not_create_second_authority() -> None:
    claims = evaluate_r5_realistic_sim_replay_v1()
    assert claims["verdict"] == "PASS_R5_REALISTIC_SIM_REPLAY_SEMANTICS_V1"
    assert claims["r5_canonical_closeout_status"] == "CLOSED_PROVEN_FORENSIC"
    assert claims["i67_role_status"] == "GOVERNED_SUPPORTING_SIMULATION"
    assert claims["i67_cap7_equivalence_status"] == "NOT_PROVEN_DISTINCT"
    assert claims["i67_i17_equivalence_status"] == "NOT_PROVEN_DISTINCT"
    assert (
        claims["i79_replay_status"]
        == "CLOSED_PROVEN_FORENSIC_EXISTING_V1_V2_PACK_BOUND_NON_AUTHORITATIVE"
    )
    assert claims["simulation_paper_replay_shadow_semantics_status"] == "ATTESTED_DISTINCT"
    assert claims["duplicate_execution_authority_found"] is False
    assert claims["duplicate_promotion_authority_found"] is False
    assert claims["new_execution_pipeline"] is False
    assert claims["new_replay_engine"] is False
    assert claims["mode_semantics_attested"] is True
    assert claims["i17_canonical_closeout_status"] == "CLOSED_PROVEN_PASS"
    assert claims["i17_rerun_authorized"] is False
    assert claims["canary_execute"] is False
    assert claims["r6_multi_future_authorized"] is False
    assert claims["order_effect"] == "NONE"
    assert claims["trading_grant"] is False
    assert claims["promotion_authority"] is False
    assert claims["max_age_role"] == MAX_AGE_ROLE
    assert claims["max_age_enforcement_enabled"] is MAX_AGE_ENFORCEMENT_ENABLED
    assert claims["r4_verdict"] == "PASS_R4_I17_SHADOW_CONTRACT_READINESS_V1"
    assert claims["eg_i67_cap7_status"] == (
        "CLOSED_PROVEN_FORENSIC_KEEP_GOVERNED_SUPPORTING_DISTINCT"
    )
    assert claims["i79_contract_v1"] == "1"
    assert claims["i79_contract_v2"] == "2"


def test_config_activation_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    with pytest.raises(RealisticSimReplaySemanticsError, match="activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["i67_cap7_equivalence"] = True
    with pytest.raises(RealisticSimReplaySemanticsError, match="i67_cap7_equivalence"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["new_execution_pipeline"] = True
    with pytest.raises(RealisticSimReplaySemanticsError, match="new_execution_pipeline"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["r6_multi_future_authorized"] = True
    with pytest.raises(RealisticSimReplaySemanticsError, match="r6_multi_future_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["canary_execute"] = True
    with pytest.raises(RealisticSimReplaySemanticsError, match="canary_execute"):
        validate_layer_config_v1(payload)
