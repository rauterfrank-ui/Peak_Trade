"""Semantic enforcement for OD-29P-NORMATIVE-PACK-V1 (non-authorizing evidence)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.od_29p_normative_pack_v1 import (
    ADJUDICATION_CONFIG,
    DL_SEAL_KEYS,
    build_adjudication_report_v1,
    load_adjudication_v1,
    validate_adjudication_against_repo_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    evaluate_external_effect_v1,
)

REPO = Path(__file__).resolve().parents[2]
PRODUCER = (
    REPO / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_available_for_sizing_producer_v1.py"
)
TREASURY = (
    REPO / "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_treasury_single_source_capital_handoff_v1.py"
)
PRE_EXTERNAL = REPO / "src/ops/pre_external_to_external_effect_boundary_bounded_wp_v1/proof_v1.py"


def test_od_29p_normative_pack_loads_and_validates() -> None:
    adj = load_adjudication_v1(REPO)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=REPO, adjudication=adj)
    assert ok, reasons
    report = build_adjudication_report_v1(repo_root=REPO)
    assert report["VALIDATION_OK"] is True
    assert report["29P_NORMATIVE_PACK_COMPLETE"] is True


def test_dl_seal_laws_ratified() -> None:
    laws = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))["domain_laws"]
    assert set(laws) == set(DL_SEAL_KEYS)
    assert all(laws[k] == "RATIFIED_CURRENT" for k in DL_SEAL_KEYS)


def test_a_common_decision_epoch_alignment_required() -> None:
    producer = PRODUCER.read_text(encoding="utf-8")
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert payload["normative_epoch"]["join_decision_epoch_alignment_status"] == "PROVEN_CURRENT"
    assert "ELIGIBILITY_SCOPE_OR_EPOCH_MISMATCH" in producer
    assert "decision_epoch" in producer


def test_b_decision_epoch_not_equated_with_observation_clocks_in_contract() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    epoch = payload["normative_epoch"]
    assert epoch["second_independent_clock_introduced"] is False
    assert "observed_at_as_of" in epoch["decision_epoch_is_not"]
    assert "uTime" in epoch["decision_epoch_is_not"]
    producer = PRODUCER.read_text(encoding="utf-8")
    assert "observed_at_as_of" in producer


def test_c_venue_account_identity_without_venue_ordinal() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    venue = payload["venue_account_binding"]
    assert venue["arbitrary_venue_ordinal_introduced"] is False
    assert venue["unk_sealed_venue_number_29p_status"] != "UNKNOWN_CURRENT"
    producer = PRODUCER.read_text(encoding="utf-8")
    assert "bound_venue_identity" in producer
    assert "bound_account_identity" in producer
    assert "venue_number" not in producer.lower()


def test_d_cap24_instrument_binding_referenced() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert "CAP24_INSTRUMENT_WHERE_APPLICABLE" in payload["pack_identity"]["required_bindings"]
    live_scope = (
        REPO / "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "current_productive_29p_live_account_bound_and_instrument_scope_v1.py"
    ).read_text(encoding="utf-8")
    assert "BoundInstrument" in live_scope or "bound_instrument" in live_scope.lower()


def test_e_u01_p01_b05_provenance_in_pack_and_u01_p01_od() -> None:
    u01_p01 = json.loads(
        (
            REPO / "config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json"
        ).read_text(encoding="utf-8")
    )
    required = u01_p01["mint_join"]["required_inputs"]
    assert "U01_ELIGIBLE_ACCOUNT_MODE_FACT" in required
    assert "P01_APPLICABILITY_KNOWN_FACT" in required
    assert "SHARED_DECISION_EPOCH" in required


def test_f_missing_binding_fail_closed() -> None:
    producer = PRODUCER.read_text(encoding="utf-8")
    for token in ("BASE_FACT_MISSING", "ELIGIBILITY_FACT_MISSING", "P01_FACT_MISSING"):
        assert token in producer
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert payload["pack_identity"]["missing_mismatch_fail_closed"] is True


def test_g_pack_identity_cannot_mint_foreign_authority() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    pack = payload["pack_identity"]
    assert pack["foreign_authority_minted"] is False
    assert pack["new_pack_id_digest_uuid_introduced"] is False
    assert payload["authority_effect"] == "NONE"


def test_h_replay_cannot_mint_fresh_29p() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    replay = payload["replay"]
    assert replay["replay_can_mint_29p_current"] is False
    assert replay["replay_can_mint_sealed_pack_identity"] is False
    u01_p01 = json.loads(
        (
            REPO / "config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert u01_p01["replay"]["replay_can_mint_29p_current"] is False


def test_i_treasury_cannot_mint_risk_admissible() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert (
        payload["treasury_to_admission_representation"]["treasury_mints_risk_admissible"] is False
    )
    treasury = TREASURY.read_text(encoding="utf-8")
    assert "evaluate_step_29p_capital_risk_admissibility_v1" in treasury


def test_j_pre_external_terminal_standing_post_false() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert payload["post_allowed"] is False
    assert payload["external_effect_authorized"] is False
    standing = evaluate_external_effect_v1()
    assert standing.external_effect_authorized is not True
    assert standing.venue_mutation_performed is not True
    pre = PRE_EXTERNAL.read_text(encoding="utf-8")
    assert "pre_external" in pre.lower() or "PRE_EXTERNAL" in pre
    assert "prove_pre_external_to_external_effect_boundary_v1" in pre
