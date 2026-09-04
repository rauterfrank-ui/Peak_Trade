"""Offline contract tests for the §11.14 evidence-ladder surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.assemble_v1 import (
    assemble_offline_surface_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_BASE_SHA,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    LADDER_FIELD_COUNT,
    LADDER_FIELD_DEFAULTS,
    LADDER_FIELDS,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    MANDATORY_LIVE_METRIC_COUNT,
    MANDATORY_LIVE_METRICS,
    METRIC_COUNT_DISCREPANCY_VS_PRIOR_CENSUS,
    OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE,
    OWNER_GO,
    PRIOR_CENSUS_REPORTED_METRIC_COUNT,
    SECTION_11_14_AUTHORIZED,
    SECTION_11_14_COMPLETE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.evidence_schema_v1 import (
    EVIDENCE_RECORD_KEYS,
    build_evidence_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.ladder_order_v1 import (
    assert_ladder_order_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.metrics_schema_v1 import (
    build_mandatory_live_metrics_schema_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_alias_promotion_v1,
    refuse_forbidden_live_source_v1,
    refuse_live_field_true_claim_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    persist_offline_surface_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reuse_vs_fresh_v1 import (
    build_reuse_vs_fresh_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_field_adjudication_v1 import (
    adjudicate_static_fields_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.traceability_v1 import (
    build_traceability_matrix_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _true_from(field_name: str) -> dict[str, bool]:
    values = {name: False for name in LADDER_FIELDS}
    values[field_name] = True
    return values


def test_contract_invariants_remain_fail_closed() -> None:
    assert_contract_invariants_v1()
    assert SECTION_11_14_AUTHORIZED is False
    assert SECTION_11_14_COMPLETE is False
    assert LIVE_EXECUTION_CODE_EXISTS is True
    assert LIVE_EXECUTION_PATH_REACHABLE is True
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is True
    assert LIVE_ORDER_PLAN_OBSERVED is True
    for field_name in OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE:
        assert LADDER_FIELD_DEFAULTS[field_name] is False
    assert len(LADDER_FIELDS) == LADDER_FIELD_COUNT == 12
    assert len(MANDATORY_LIVE_METRICS) == MANDATORY_LIVE_METRIC_COUNT == 20
    assert PRIOR_CENSUS_REPORTED_METRIC_COUNT == 19
    assert METRIC_COUNT_DISCREPANCY_VS_PRIOR_CENSUS is True
    assert OWNER_GO.startswith("PEAK_TRADE_OWNER_GO_SECTION_11_14_")


def test_ladder_order_rejects_ack_before_order_plan() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_SUBMIT_ACK_OBSERVED"))


def test_ladder_order_rejects_fill_before_ack() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_FILL_OBSERVED"))


def test_ladder_order_rejects_fee_before_fill() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_FEE_OBSERVED"))


def test_ladder_order_rejects_position_before_execution_evidence() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_POSITION_RECONCILED"))


def test_ladder_order_rejects_accounting_before_fill_fee_recon() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_ACCOUNTING_RECONSTRUCTED"))


def test_ladder_order_rejects_restart_before_prerequisites() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_RESTART_RECONSTRUCTED"))


def test_ladder_order_rejects_autonomous_recovery_before_restart() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_AUTONOMOUS_RECOVERY_OBSERVED"))


def test_ladder_order_rejects_end_to_end_before_predecessors() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="LADDER_ORDER_VIOLATION"):
        assert_ladder_order_v1(_true_from("LIVE_END_TO_END_EVIDENCE_PROVEN"))


def test_ladder_order_accepts_code_exists_only() -> None:
    values = _true_from("LIVE_EXECUTION_CODE_EXISTS")
    assert_ladder_order_v1(values)


def test_ladder_order_accepts_all_false() -> None:
    all_false = {name: False for name in LADDER_FIELDS}
    assert_ladder_order_v1(all_false)


def test_overclaim_guards_forbid_fixture_sim_testnet_shadow() -> None:
    for source in ("FIXTURE", "SIMULATION", "TESTNET", "PAPER", "SHADOW"):
        with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
            refuse_forbidden_live_source_v1(
                field_name="LIVE_FILL_OBSERVED",
                source_kind=source,
            )
        with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
            refuse_live_field_true_claim_v1(
                field_name="LIVE_FILL_OBSERVED",
                source_kind=source,
            )


def test_overclaim_guards_forbid_alias_promotions() -> None:
    for alias in (
        "G12_CLOSURE_AUTHORIZES_SECTION_11_14",
        "G12_SATISFIES_SECTION_11_14_OBSERVED_FIELDS",
        "LIVE_RECONCILIATION_PROVEN_EQUALS_LIVE_POSITION_RECONCILED",
        "CURRENTLY_REACHABLE_EQUALS_LIVE_EXECUTION_PATH_REACHABLE",
        "FIELD_NAME_SIMILARITY_EQUALS_SEMANTIC_IDENTITY",
        "HISTORICAL_EVIDENCE_EQUALS_CURRENT_TRUTH",
        "CODE_PRESENCE_EQUALS_LIVE_EXECUTION_CODE_EXISTS",
    ):
        with pytest.raises(Section1114OfflineSurfaceError, match="ALIAS_PROMOTION_FORBIDDEN"):
            refuse_alias_promotion_v1(claimed_alias=alias)


def test_static_fields_bind_code_exists_without_reachability_or_later_fields() -> None:
    proof = adjudicate_static_fields_v1(repo_root=REPO_ROOT)
    assert proof["LIVE_EXECUTION_CODE_EXISTS_VALUE"] is True
    assert proof["LIVE_EXECUTION_PATH_REACHABLE_VALUE"] is False
    code = proof["LIVE_EXECUTION_CODE_EXISTS"]
    path = proof["LIVE_EXECUTION_PATH_REACHABLE"]
    for record in (code, path):
        for key in (
            "canonical_definition",
            "observed_repo_fact",
            "admissibility_rule",
            "evidence_paths",
            "contradiction_check",
            "adjudicated_value",
            "reason",
        ):
            assert key in record
    assert "CODE_PRESENCE_ALONE_INADMISSIBLE" in code["reason"]
    assert "PATH_REACHABLE_NOT_INFERRED" in code["reason"]
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in code["reason"]
    assert path["adjudicated_value"] is False
    assert "UNOBSERVED_REQUIRED_CONSTITUENT" in path["reason"]
    assert "CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE" in path["contradiction_check"]
    assert path["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert "FILE_PRESENCE_ALONE=true" in code["observed_repo_fact"]
    assert "FILE_PRESENCE_ADMISSIBLE=false" in code["observed_repo_fact"]


def test_reuse_matrix_never_promotes_predecessor_facts() -> None:
    matrix = build_reuse_vs_fresh_matrix_v1()
    assert matrix["promotion_authorized_by_this_go"] is False
    assert matrix["row_count"] >= 10
    for row in matrix["rows"]:
        assert row["reusable_as_identical_11_14_fact"] is False
        assert row["promotion_authorized_by_this_go"] is False
        assert row["classification"] != "REUSABLE_AS_IDENTICAL_11_14_FACT"
    names = {row["candidate"] for row in matrix["rows"]}
    assert "SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_PROVEN" in names
    assert "SECTION_11_13_5_E_LIVE_RECONCILIATION_PROVEN" in names
    assert "G12_CANONICAL_CLOSEOUT" in names
    recon = next(
        row
        for row in matrix["rows"]
        if row["candidate"] == "SECTION_11_13_5_E_LIVE_RECONCILIATION_PROVEN"
    )
    assert recon["classification"] == "SEMANTICALLY_DIFFERENT"
    assert recon["target_11_14_field"] == "LIVE_POSITION_RECONCILED"


def test_metrics_schema_is_uncollected_and_preserves_ssot_cardinality() -> None:
    schema = build_mandatory_live_metrics_schema_v1()
    assert schema["canonical_cardinality"] == 20
    assert schema["prior_census_reported_cardinality"] == 19
    assert schema["cardinality_discrepancy_vs_prior_census"] is True
    assert schema["collector_activated"] is False
    assert schema["names"] == list(MANDATORY_LIVE_METRICS)
    for metric in schema["metrics"]:
        assert metric["live_value"] is None
        assert metric["collection_status"] == "NOT_COLLECTED"
        assert metric["paper_testnet_fixture_sim_inadmissible"] is True
        assert metric["collector_activated"] is False


def test_evidence_record_has_required_keys_and_refuses_true_claim() -> None:
    record = build_evidence_record_v1(
        ladder_stage="LIVE_FILL_OBSERVED",
        claim_name="LIVE_FILL_OBSERVED",
        claim_value=False,
        evidence_class="3_ALREADY_ADJUDICATED_CONCLUSION",
        source_kind="GOVERNED_OFFLINE_CONTRACT",
        source_path_or_runtime_source="offline",
        observed_at=None,
        predecessor_claims=["G12"],
        provenance=OWNER_GO,
        adjudication_status="FALSE_FAIL_CLOSED",
        contradiction_status="NONE",
        authority_scope="R1",
    )
    for key in EVIDENCE_RECORD_KEYS:
        assert key in record
    assert record["content_hash"]
    with pytest.raises(Section1114OfflineSurfaceError, match="TRUE_FORBIDDEN"):
        build_evidence_record_v1(
            ladder_stage="LIVE_FILL_OBSERVED",
            claim_name="LIVE_FILL_OBSERVED",
            claim_value=True,
            evidence_class="2",
            source_kind="GOVERNED_OFFLINE_CONTRACT",
            source_path_or_runtime_source="offline",
            observed_at=None,
            predecessor_claims=[],
            provenance=OWNER_GO,
            adjudication_status="TRUE",
            contradiction_status="NONE",
            authority_scope="R1",
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        build_evidence_record_v1(
            ladder_stage="LIVE_FILL_OBSERVED",
            claim_name="LIVE_FILL_OBSERVED",
            claim_value=False,
            evidence_class="2",
            source_kind="FIXTURE",
            source_path_or_runtime_source="tests",
            observed_at=None,
            predecessor_claims=[],
            provenance=OWNER_GO,
            adjudication_status="FALSE",
            contradiction_status="NONE",
            authority_scope="R1",
        )
    allowed = build_evidence_record_v1(
        ladder_stage="LIVE_EXECUTION_CODE_EXISTS",
        claim_name="LIVE_EXECUTION_CODE_EXISTS",
        claim_value=True,
        evidence_class="3_ALREADY_ADJUDICATED_CONCLUSION",
        source_kind="REPOSITORY_IMPLEMENTATION",
        source_path_or_runtime_source="src/ops/",
        observed_at=None,
        predecessor_claims=[],
        provenance=OWNER_GO,
        adjudication_status="TRUE_STATIC_INTEGRATED_PRODUCTIVE_PATH",
        contradiction_status="NONE",
        authority_scope="R1",
    )
    assert allowed["claim_value"] is True
    with pytest.raises(
        Section1114OfflineSurfaceError, match="PATH_REACHABLE_TRUE_SOURCE_NOT_ADMISSIBLE"
    ):
        build_evidence_record_v1(
            ladder_stage="LIVE_EXECUTION_PATH_REACHABLE",
            claim_name="LIVE_EXECUTION_PATH_REACHABLE",
            claim_value=True,
            evidence_class="3",
            source_kind="REPOSITORY_IMPLEMENTATION",
            source_path_or_runtime_source="src/ops/",
            observed_at=None,
            predecessor_claims=[],
            provenance=OWNER_GO,
            adjudication_status="TRUE",
            contradiction_status="NONE",
            authority_scope="R1",
        )


def test_traceability_has_each_ladder_field_and_metric_once() -> None:
    matrix = build_traceability_matrix_v1(
        ladder_values=LADDER_FIELD_DEFAULTS,
        metrics_schema=build_mandatory_live_metrics_schema_v1(),
    )
    names = [row["CANONICAL_REQUIREMENT"] for row in matrix["rows"]]
    assert names == list(LADDER_FIELDS) + list(MANDATORY_LIVE_METRICS)
    assert matrix["primary_row_count"] == 32
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "LIVE_SUBMIT_ACK_OBSERVED"


def _successful_read_only_evidence() -> dict[str, object]:
    return {
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": True,
        "AUTHENTICATION_PATH_FUNCTIONAL": True,
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": True,
        "CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0": True,
        "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0": True,
        "BOTH_METHODS_GET": True,
        "NO_POST": True,
        "PARSEABLE_ACCOUNT_CONFIG_DATA": True,
        "PARSEABLE_ACCOUNT_BALANCE_DATA": True,
        "NO_REDIRECT": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "POST_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": True,
        "VENUE_REQUESTS": 2,
        "METHOD": "GET",
        "RESPONSE_TIME_UTC": "2026-09-04T13:32:00Z",
    }


def _successful_order_plan_evidence() -> dict[str, object]:
    return {
        "LIVE_EXECUTION_CODE_EXISTS": True,
        "LIVE_EXECUTION_PATH_REACHABLE": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "PRODUCED_ON_CANONICAL_SUBMIT_PATH": True,
        "AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS": True,
        "CURRENT_VENUE_DERIVED_INPUTS": True,
        "ORDER_PLAN_ARTIFACT_PRESENT": True,
        "NOT_BLOCKED_DRY_RUN": True,
        "NOT_DIRECT_BUILDER_INVOCATION": True,
        "NO_POST_REQUIRED": True,
        "POST_USED": False,
        "PUBLIC_GET_USED": True,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": True,
        "LIVE_GATE_ACTIVATION_USED": True,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "VENUE_REQUESTS": 9,
        "RESPONSE_TIME_UTC": "2026-09-04T14:05:00Z",
    }


def test_assemble_and_persist_offline_pack(tmp_path: Path) -> None:
    documents = assemble_offline_surface_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        private_read_only_evidence=_successful_read_only_evidence(),
        order_plan_evidence=_successful_order_plan_evidence(),
    )
    verified = persist_offline_surface_pack_v1(
        pack=tmp_path,
        origin_main_sha=CANONICAL_BASE_SHA,
        documents=documents,
    )
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    assert documents["SUMMARY.json"]["LIVE_EXECUTION_CODE_EXISTS"] is True
    assert documents["SUMMARY.json"]["LIVE_EXECUTION_PATH_REACHABLE"] is True
    assert documents["SUMMARY.json"]["LIVE_PRIVATE_READ_ONLY_PROVEN"] is True
    assert documents["SUMMARY.json"]["LIVE_ORDER_PLAN_OBSERVED"] is True
    assert documents["SUMMARY.json"]["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert documents["SUMMARY.json"]["SECTION_11_14_COMPLETE"] is False
    assert documents["SUMMARY.json"]["CASE_ADJUDICATION"] == (
        "CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO"
    )
    assert documents["SUMMARY.json"]["GET_USED"] is False
    assert documents["SUMMARY.json"]["CREDENTIAL_USE"] is False
    assert documents["MUTATION_BOUNDARY.json"]["POST"] is False
    assert documents["MUTATION_BOUNDARY.json"]["THIS_GO_GET"] is False
    assert documents["MUTATION_BOUNDARY.json"]["PREDECESSOR_ORDER_PLAN_ATTACHED"] is True
    assert (
        documents["SUBMIT_ACK_ADJUDICATION.json"]["CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO"]
        is True
    )
    assert documents["SUBMIT_ACK_ADJUDICATION.json"]["CASE_C_CANONICAL_SEMANTIC_GAP"] is False
    assert documents["SUBMIT_ACK_ADJUDICATION.json"]["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert (
        documents["SUBMIT_ACK_PROOF_CRITERION.json"]["LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND"]
        is True
    )
    assert documents["SUBMIT_ACK_OBSERVED_ADJUDICATION.json"]["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert documents["SUBMIT_ACK_OBSERVED_ADJUDICATION.json"]["LIVE_FILL_OBSERVED"] is False
    assert documents["EXACT_MUTATION_CONTRACT.json"]["endpoint"] == "/api/v5/trade/order"
    assert documents["EXACT_MUTATION_CONTRACT.json"]["http_method"] == "POST"
    assert documents["PRIVATE_GET_BINDING.json"]["METHOD"] == "GET"
    assert documents["PRIVATE_GET_BINDING.json"]["POST"] is False
    with pytest.raises(RuntimeError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        assemble_offline_surface_v1(repo_root=REPO_ROOT, origin_main_sha="deadbeef")
