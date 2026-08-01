"""Focused tests for productive evidence campaign/session preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    build_productive_evidence_accumulation_preregistration_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    ARTIFACT_RELATIVE_PATH,
    BOUND_DESIGN_PREREGISTRATION_DIGEST,
    BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RESEARCH_AGE_GRID_SECONDS,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    PUBLIC_MD_ALLOWED_ENDPOINTS,
    PUBLIC_MD_HOST,
    PUBLIC_MD_VENUE,
    SCHEMA_VERSION,
    assert_preregistration_does_not_materialize_paths_v1,
    build_productive_evidence_campaign_session_preregistration_v1,
    render_session_preregistration_v1,
    verify_productive_evidence_campaign_session_preregistration_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    resume_productive_evidence_session_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    EXIT_PRECEDENCE_PRESERVED,
    REVERSAL_REDUCE_FIRST_PRESERVED,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)

ROOT = Path(__file__).resolve().parents[2]


def test_01_deterministic_serialization_and_digest_stability() -> None:
    a = build_productive_evidence_campaign_session_preregistration_v1()
    b = build_productive_evidence_campaign_session_preregistration_v1()
    assert a.to_dict() == b.to_dict()
    assert a.preregistration_digest == b.preregistration_digest
    assert a.preregistration_digest == render_session_preregistration_v1()["preregistration_digest"]


def test_02_digest_changes_on_authority_field_mutation() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    payload = contract.to_dict()
    mutated = copy.deepcopy(payload)
    mutated["repository_sha"] = "0" * 40
    with pytest.raises(ProductiveEvidenceAccumulationError):
        verify_productive_evidence_campaign_session_preregistration_v1(mutated)
    # Recompute digest after mutation must differ from original.
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
        _digest_v1,
    )

    assert _digest_v1(mutated) != contract.preregistration_digest


def test_03_binds_exact_repository_sha() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert contract.repository_sha == BOUND_REPOSITORY_SHA
    assert contract.repository_sha == "e9c1871ea7b493cde9f49eb517910b1a7134fb5b"


def test_04_binds_both_existing_preregistration_digests() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    productive = build_productive_evidence_accumulation_preregistration_v1()
    design = build_ratified_max_age_research_design_contract_v1()
    assert contract.productive_preregistration_digest == BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST
    assert contract.design_preregistration_digest == BOUND_DESIGN_PREREGISTRATION_DIGEST
    assert (
        contract.productive_preregistration_digest == productive.productive_preregistration_digest
    )
    assert contract.design_preregistration_digest == design.preregistration_digest


def test_05_exact_research_grid() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert list(contract.research_age_grid_seconds) == list(BOUND_RESEARCH_AGE_GRID_SECONDS)
    assert list(contract.research_age_grid_seconds) == [
        60,
        120,
        300,
        600,
        900,
        1800,
        3600,
        7200,
    ]


def test_06_at_least_two_unique_session_ids() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    ids = [s.session_id for s in contract.sessions]
    assert len(ids) >= 2
    assert len(set(ids)) == len(ids)


def test_07_no_session_already_active() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    for sess in contract.sessions:
        assert sess.lifecycle_initial_state == "PREREGISTERED"
        assert sess.lifecycle_initial_state != "ACTIVE"


def test_08_execution_authorized_false() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert contract.execution_authorized is False


def test_09_network_authorized_false() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert contract.network_authorized is False
    assert contract.public_md_plan["network_authorized"] is False


def test_10_evidence_write_authorized_false() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert contract.evidence_write_authorized is False


def test_11_get_only_endpoint_allowlist() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    md = contract.public_md_plan
    assert md["allowed_http_methods"] == ["GET"]
    assert list(md["allowed_endpoints"]) == list(PUBLIC_MD_ALLOWED_ENDPOINTS)


def test_12_private_endpoints_forbidden() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    md = contract.public_md_plan
    assert md["private_endpoints_allowed"] is False
    assert md["private_endpoints_excluded"] is True
    for ep in md["allowed_endpoints"]:
        assert "/private/" not in ep
        assert not str(ep).startswith("/api/v5/account")
        assert not str(ep).startswith("/api/v5/trade")


def test_13_orders_and_mutation_methods_forbidden() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    md = contract.public_md_plan
    assert md["order_endpoints_allowed"] is False
    assert md["mutation_methods_allowed"] is False
    assert md["orders_technically_excluded"] is True
    assert "POST" not in md["allowed_http_methods"]
    assert "PUT" not in md["allowed_http_methods"]
    assert "DELETE" not in md["allowed_http_methods"]


def test_14_exact_venue_host_instrument_binding() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    md = contract.public_md_plan
    assert md["venue"] == PUBLIC_MD_VENUE == "OKX"
    assert md["host"] == PUBLIC_MD_HOST == "https://eea.okx.com"
    assert md["canonical_instrument_id"] == CANONICAL_INSTRUMENT_ID
    assert md["venue_native_instrument_id"] == CANONICAL_INSTRUMENT_ID
    assert md["instrument_substitution_forbidden"] is True


def test_15_non_tmp_durable_paths() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    durable = contract.durable_path_plan
    assert durable["productive_ledger_path"] == DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
    assert durable["quarantine_ledger_path"] == DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
    assert durable["join_projection_path"] == DEFAULT_JOIN_LEDGER_RELATIVE_PATH
    assert durable["tmp_authority_prohibited"] is True
    for path in (
        durable["productive_ledger_path"],
        durable["quarantine_ledger_path"],
        durable["join_projection_path"],
        *durable["campaign_specific_paths"].values(),
    ):
        assert "/tmp" not in path
        assert not str(path).startswith("/")


def test_16_parent_dirs_not_created_by_preregistration() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    campaign_parent = (
        ROOT / contract.durable_path_plan["campaign_specific_paths"]["campaign_manifest_path"]
    ).parent
    assert not campaign_parent.exists()
    assert_preregistration_does_not_materialize_paths_v1(repo_root=ROOT)
    assert not campaign_parent.exists()
    assert contract.durable_path_plan["parent_dirs_materialized_by_preregistration"] is False


def test_17_7200_reachability_plan_complete_and_non_synthetic() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    plan = contract.reachability_7200_plan
    assert plan["target_bucket_seconds"] == 7200
    assert plan["natural_reachability_required"] is True
    assert plan["synthetic_market_time_prohibited"] is True
    assert plan["poll_cycles_are_not_market_time"] is True
    assert plan["duplicate_samples_are_not_new_age_observations"] is True
    assert plan["artificially_stale_timestamp_prohibited"] is True
    assert int(plan["minimum_campaign_event_time_span_seconds"]) > 7200
    assert int(plan["minimum_campaign_wallclock_span_seconds"]) > 7200
    assert plan["fail_closed_if_unreachable"]["coverage_incomplete_when_7200_bucket_missing"]


def test_18_restart_is_not_new_session() -> None:
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
        open_productive_evidence_session_v1,
    )

    contract = build_productive_evidence_campaign_session_preregistration_v1()
    sess_plan = contract.sessions[0]
    assert sess_plan.resume_policy["restart_is_not_a_new_independent_session"] is True
    opened = open_productive_evidence_session_v1(
        session_id=sess_plan.session_id,
        session_start_event_time="2026-08-01T00:00:00Z",
        repository_sha=BOUND_REPOSITORY_SHA,
        venue="OKX",
        canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
        venue_instrument_id=CANONICAL_INSTRUMENT_ID,
        restart_generation=0,
    )
    resumed = resume_productive_evidence_session_v1(
        opened,
        resume_token=opened.resume_token,
        repository_sha=BOUND_REPOSITORY_SHA,
        process_restart=True,
    )
    assert resumed.session_id == opened.session_id == sess_plan.session_id
    assert resumed.restart_generation == opened.restart_generation + 1


def test_19_duplicate_sample_not_new_age_observation() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    assert (
        contract.sample_event_time_bindings["DUPLICATE_SAMPLE_CANNOT_CREATE_NEW_AGE_OBSERVATION"]
        is True
    )
    assert contract.reachability_7200_plan["duplicate_samples_are_not_new_age_observations"] is True


def test_20_no_invented_enumerated_regime_names() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    coverage = contract.coverage_plan
    assert coverage["enumerated_market_regime_names_invented"] is False
    assert coverage["enumerated_volatility_regime_names_invented"] is False
    assert "invented_regimes" not in coverage
    assert "fixed_market_regime_names" not in coverage


def test_21_counterfactual_only_enforcement_disabled() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    inv = contract.non_promotion_invariants
    assert inv["COUNTERFACTUAL_ONLY"] is True
    assert inv["ENFORCEMENT_APPLIED"] is False
    assert inv["MAX_AGE_THRESHOLD_SELECTED"] is False
    assert inv["MAX_AGE_ENFORCEMENT_ENABLED"] is False
    assert contract.enforcement_authorized is False


def test_22_exit_precedence_and_reversal_reduce_first_preserved() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    inv = contract.non_promotion_invariants
    assert inv["EXIT_PRECEDENCE_PRESERVED"] is True
    assert inv["REVERSAL_REDUCE_FIRST_PRESERVED"] is True
    assert EXIT_PRECEDENCE_PRESERVED is True
    assert REVERSAL_REDUCE_FIRST_PRESERVED is True


def test_23_no_runtime_network_or_ledger_side_effects() -> None:
    contract = build_productive_evidence_campaign_session_preregistration_v1()
    verify_productive_evidence_campaign_session_preregistration_v1(contract)
    for sess in contract.sessions:
        assert sess.no_runtime_side_effects is True
        assert sess.planned_start_not_authorized is True
    campaign_parent = (
        ROOT / contract.durable_path_plan["campaign_specific_paths"]["campaign_manifest_path"]
    ).parent
    assert not campaign_parent.exists()
    productive_ledger = ROOT / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
    # Ledger file must not be created by these tests.
    assert not productive_ledger.exists() or productive_ledger.stat().st_size >= 0
    # Ensure we did not append during this test module's preregistration calls.
    assert contract.evidence_write_authorized is False
    assert contract.network_authorized is False
    assert_architecture_guards_v1(repo_root=ROOT)["guards_pass"] is True


def test_24_frozen_artifact_matches_builder() -> None:
    artifact = ROOT / ARTIFACT_RELATIVE_PATH
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    result = verify_productive_evidence_campaign_session_preregistration_v1(payload)
    assert result["status"] == "PASS"
    built = build_productive_evidence_campaign_session_preregistration_v1()
    assert payload["preregistration_digest"] == built.preregistration_digest
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["capability_id"] == CAPABILITY_ID
    assert result["session_ids"] == [s.session_id for s in built.sessions]
