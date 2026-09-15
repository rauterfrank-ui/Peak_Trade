"""NEW_CANONICAL_DEFINITION of live EQUITY_STOCK KIND_SET.

Persists eligibility and a deterministic membership evaluator. Historical
F12/F13/U05/F16/F17/F18 remain UNKNOWN. Today KIND_SET stays empty.
No GET. GATE_A and GATE_B are not executed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FACT_F12,
    FACT_IDS,
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_critical_path_next_blocker_bounded_wp1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BM_PACK_RELPATH,
    NEXT_OWNER_GO_REQUIRED as BM_NEXT_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANDIDATE_CLASSIFIED_EVENT_STREAM,
    CANDIDATE_GOVERNED_CHECKPOINT,
    CANDIDATE_P01,
    CANDIDATE_U04,
    CANDIDATE_VENUE_EQ,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    ELIGIBILITY_CRITERIA,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    LAYER_CANONICAL,
    LiveEquityStockKindCandidateV1,
    LiveEquityStockKindSetDefinitionError,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    REASON_ABSOLUTE_STOCK_ABSENT,
    REASON_AVAILABLE_CAPITAL,
    REASON_CHECKPOINT_CANNOT_MINT,
    REASON_CLAIMED_INCLUDE_FORBIDDEN,
    REASON_CONTRADICTORY_INPUT,
    REASON_DELTA_OR_FLOW,
    REASON_ELIGIBLE,
    REASON_HISTORICAL_UNKNOWN,
    REASON_MALFORMED_INPUT,
    REASON_MISSING_INPUT,
    REASON_PRECEDENCE,
    REASON_RECONCILIATION_TARGET,
    REASON_RISK_CAPITAL_REDUCTION,
    ROLE_EQUITY_STOCK_SOURCE,
    ROLE_RECONCILIATION_TARGET_ONLY,
    build_live_equity_stock_kind_set_definition_v1,
    evaluate_live_equity_stock_kind_membership_v1,
    evaluate_today_live_equity_stock_kind_set_v1,
    execute_live_equity_stock_kind_set_new_canonical_definition_v1,
    ratified_live_equity_stock_kind_set_v1,
    reason_precedence_index_v1,
    reject_claimed_live_kind_set_authority_mutation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BM_HEADING = "11.2.1.BM FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER"
BN_HEADING = "11.2.1.BN FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION"
SEALED_BM = REPO_ROOT / CANONICAL_BM_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T10:00:00Z"


def _bn_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BN_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _eligible_fixture() -> LiveEquityStockKindCandidateV1:
    return LiveEquityStockKindCandidateV1(
        candidate_id="FIXTURE_ELIGIBLE_NOT_RATIFIED",
        source_role=ROLE_EQUITY_STOCK_SOURCE,
        layer=LAYER_CANONICAL,
        input_status="PRESENT",
        claimed_proof="ELIGIBILITY_EVALUATOR_ONLY",
        is_historical_unknown=False,
        is_delta_or_flow=False,
        is_reconciliation_witness=False,
        is_available_capital=False,
        is_placement_capacity=False,
        is_risk_capital_reduction=False,
        is_checkpoint_non_minting=False,
        embedding_proven=True,
        identity_proven=True,
        time_sequence_proven=True,
        double_count_proven_safe=True,
        absolute_stock_value_present=True,
        option_d_start_capable=True,
        authority_ref="TEST_FIXTURE_ONLY",
    )


def _run(tmp_path: Path):
    return execute_live_equity_stock_kind_set_new_canonical_definition_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bm_pack=SEALED_BM,
        evidence_root=tmp_path / "live_kind_set",
        persist_as_of=_AS_OF,
    )


def test_sealed_bm_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BM) == 0
    assert BM_NEXT_OWNER_GO == OWNER_GO


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(LiveEquityStockKindSetDefinitionError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_kind_set_new_canonical_definition_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bm_pack=SEALED_BM,
            evidence_root=tmp_path / "live_kind_set",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(LiveEquityStockKindSetDefinitionError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_live_equity_stock_kind_set_new_canonical_definition_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bm_pack=SEALED_BM,
            evidence_root=tmp_path / "live_kind_set",
            persist_as_of=_AS_OF,
        )


def test_missing_and_malformed_bm_claims_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "empty_pack"
    missing.mkdir()
    lineage = missing / "LINEAGE.json"
    lineage.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(lineage.read_bytes()).hexdigest()
    (missing / "MANIFEST.sha256").write_text(f"{digest}  LINEAGE.json\n", encoding="utf-8")
    with pytest.raises(LiveEquityStockKindSetDefinitionError, match="BM_CLAIMS_MISSING"):
        execute_live_equity_stock_kind_set_new_canonical_definition_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bm_pack=missing,
            evidence_root=tmp_path / "live_kind_set",
            persist_as_of=_AS_OF,
        )
    malformed = tmp_path / "malformed_pack"
    malformed.mkdir()
    claims = malformed / "claims.json"
    claims.write_text("{not-json\n", encoding="utf-8")
    digest = hashlib.sha256(claims.read_bytes()).hexdigest()
    (malformed / "MANIFEST.sha256").write_text(f"{digest}  claims.json\n", encoding="utf-8")
    with pytest.raises(LiveEquityStockKindSetDefinitionError, match="BM_CLAIMS_MALFORMED"):
        execute_live_equity_stock_kind_set_new_canonical_definition_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bm_pack=malformed,
            evidence_root=tmp_path / "live_kind_set",
            persist_as_of=_AS_OF,
        )


@pytest.mark.parametrize(
    "claimed_proof",
    [
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_EQ_TO_SOURCE",
        "PROMOTE_U04_TO_EQUITY_STOCK",
        "PROMOTE_P01_TO_EQUITY_STOCK",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(LiveEquityStockKindSetDefinitionError, match="LIVE_KIND_SET_CANNOT_"):
        reject_claimed_live_kind_set_authority_mutation_v1(
            claimed_proof=claimed_proof,
            candidate_id=FACT_F12,
        )


def test_fixture_eligible_kind_is_positive_but_not_ratified() -> None:
    record = evaluate_live_equity_stock_kind_membership_v1(_eligible_fixture())
    assert record.member == "true"
    assert record.reason_code == REASON_ELIGIBLE
    assert record.eligibility_failures == ()
    assert ratified_live_equity_stock_kind_set_v1() == ()


def test_today_candidates_are_all_rejected() -> None:
    records = {item.candidate_id: item for item in evaluate_today_live_equity_stock_kind_set_v1()}
    for fact_id in FACT_IDS:
        assert records[fact_id].member == "false"
        assert records[fact_id].reason_code == REASON_HISTORICAL_UNKNOWN
    assert records[CANDIDATE_VENUE_EQ].source_role == ROLE_RECONCILIATION_TARGET_ONLY
    assert records[CANDIDATE_VENUE_EQ].reason_code == REASON_RECONCILIATION_TARGET
    assert records[CANDIDATE_U04].reason_code == REASON_AVAILABLE_CAPITAL
    assert records[CANDIDATE_P01].reason_code == REASON_RISK_CAPITAL_REDUCTION
    assert records[CANDIDATE_GOVERNED_CHECKPOINT].reason_code == REASON_CHECKPOINT_CANNOT_MINT
    assert records[CANDIDATE_CLASSIFIED_EVENT_STREAM].reason_code == REASON_DELTA_OR_FLOW
    definition = build_live_equity_stock_kind_set_definition_v1()
    assert definition.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert definition.kind_set_members == ()
    assert definition.legacy_semantics_reconstructed == "false"
    assert definition.new_canonical_definition == "true"


def test_stock_versus_flow_and_reconciliation_and_available_capital() -> None:
    flow = evaluate_live_equity_stock_kind_membership_v1(
        LiveEquityStockKindCandidateV1(
            candidate_id="FIXTURE_FLOW",
            source_role="EQUITY_FLOW_SOURCE",
            layer=LAYER_CANONICAL,
            input_status="PRESENT",
            claimed_proof="ELIGIBILITY_EVALUATOR_ONLY",
            is_historical_unknown=False,
            is_delta_or_flow=True,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=True,
            identity_proven=True,
            time_sequence_proven=True,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref="TEST_FIXTURE_ONLY",
        )
    )
    assert flow.reason_code == REASON_DELTA_OR_FLOW
    assert "NOT_DELTA_OR_FLOW" in flow.eligibility_failures
    recon = evaluate_live_equity_stock_kind_membership_v1(
        LiveEquityStockKindCandidateV1(
            candidate_id="FIXTURE_EQ",
            source_role=ROLE_RECONCILIATION_TARGET_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT",
            claimed_proof="ELIGIBILITY_EVALUATOR_ONLY",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=True,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=True,
            identity_proven=True,
            time_sequence_proven=True,
            double_count_proven_safe=True,
            absolute_stock_value_present=True,
            option_d_start_capable=False,
            authority_ref="TEST_FIXTURE_ONLY",
        )
    )
    assert recon.reason_code == REASON_RECONCILIATION_TARGET
    available = evaluate_live_equity_stock_kind_membership_v1(
        LiveEquityStockKindCandidateV1(
            candidate_id="FIXTURE_U04",
            source_role="AVAILABLE_CAPITAL_ONLY",
            layer=LAYER_CANONICAL,
            input_status="PRESENT",
            claimed_proof="ELIGIBILITY_EVALUATOR_ONLY",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=True,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=True,
            identity_proven=True,
            time_sequence_proven=True,
            double_count_proven_safe=True,
            absolute_stock_value_present=True,
            option_d_start_capable=False,
            authority_ref="TEST_FIXTURE_ONLY",
        )
    )
    assert available.reason_code == REASON_AVAILABLE_CAPITAL


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("MISSING", REASON_MISSING_INPUT),
        ("MALFORMED", REASON_MALFORMED_INPUT),
        ("CONTRADICTORY", REASON_CONTRADICTORY_INPUT),
    ],
)
def test_missing_malformed_contradictory_fail_closed(status: str, reason: str) -> None:
    fixture = _eligible_fixture()
    broken = LiveEquityStockKindCandidateV1(
        **{**fixture.__dict__, "input_status": status, "candidate_id": f"FIXTURE_{status}"}
    )
    record = evaluate_live_equity_stock_kind_membership_v1(broken)
    assert record.member == "false"
    assert record.reason_code == reason


def test_embedding_and_double_count_guards() -> None:
    fixture = _eligible_fixture()
    embedding = LiveEquityStockKindCandidateV1(
        **{
            **fixture.__dict__,
            "candidate_id": "FIXTURE_EMBEDDING",
            "embedding_proven": False,
        }
    )
    record = evaluate_live_equity_stock_kind_membership_v1(embedding)
    assert record.member == "false"
    assert "EMBEDDING_AND_LIABILITY_RULES_EXPLICIT" in record.eligibility_failures
    double = LiveEquityStockKindCandidateV1(
        **{
            **fixture.__dict__,
            "candidate_id": "FIXTURE_DOUBLE",
            "double_count_proven_safe": False,
        }
    )
    record = evaluate_live_equity_stock_kind_membership_v1(double)
    assert record.member == "false"
    assert "NO_DOUBLE_COUNT_WITH_CLASSIFIED_EVENT_STREAM" in record.eligibility_failures


def test_reason_precedence_is_deterministic() -> None:
    mixed = LiveEquityStockKindCandidateV1(
        candidate_id="FIXTURE_MIXED",
        source_role=ROLE_EQUITY_STOCK_SOURCE,
        layer=LAYER_CANONICAL,
        input_status="MALFORMED",
        claimed_proof=DECISION_INCLUDE,
        is_historical_unknown=True,
        is_delta_or_flow=True,
        is_reconciliation_witness=True,
        is_available_capital=True,
        is_placement_capacity=False,
        is_risk_capital_reduction=False,
        is_checkpoint_non_minting=False,
        embedding_proven=False,
        identity_proven=False,
        time_sequence_proven=False,
        double_count_proven_safe=False,
        absolute_stock_value_present=False,
        option_d_start_capable=False,
        authority_ref="TEST_FIXTURE_ONLY",
    )
    first = evaluate_live_equity_stock_kind_membership_v1(mixed)
    second = evaluate_live_equity_stock_kind_membership_v1(mixed)
    assert first == second
    assert first.reason_code == REASON_CLAIMED_INCLUDE_FORBIDDEN
    assert reason_precedence_index_v1(REASON_CLAIMED_INCLUDE_FORBIDDEN) < (
        reason_precedence_index_v1(REASON_MALFORMED_INPUT)
    )
    assert reason_precedence_index_v1(REASON_RECONCILIATION_TARGET) < (
        reason_precedence_index_v1(REASON_ABSOLUTE_STOCK_ABSENT)
    )
    assert REASON_PRECEDENCE[-1] == REASON_ELIGIBLE
    assert len(ELIGIBILITY_CRITERIA) == 10


def test_replay_order_determinism() -> None:
    first = tuple(
        (item.candidate_id, item.reason_code, item.member)
        for item in evaluate_today_live_equity_stock_kind_set_v1()
    )
    second = tuple(
        (item.candidate_id, item.reason_code, item.member)
        for item in evaluate_today_live_equity_stock_kind_set_v1()
    )
    assert first == second
    assert first == tuple(sorted(first, key=lambda item: item[0]))


def test_execute_persists_empty_kind_set_and_protected_surfaces(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.live_equity_stock_kind_set_resolved == "false"
    assert result.kind_set_members == "NONE"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert result.venue_get_count == "0"
    assert result.venue_post_count == "0"
    assert result.gate_a_executed == "false"
    assert result.gate_b_executed == "false"
    assert result.kinds_invented_this_go == "false"
    assert result.legacy_semantics_reconstructed == "false"
    assert result.d6_fully_closed == "false"
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BM_CONTRACT_REUSED"] == "true"
    assert claims["NEW_CANONICAL_DEFINITION"] == "true"
    assert claims["LEGACY_SEMANTICS_RECONSTRUCTED"] == "false"
    assert claims["F12_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["VENUE_EQ_ROLE"] == ROLE_RECONCILIATION_TARGET_ONLY
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    membership = json.loads((store / "membership_v1.json").read_text(encoding="utf-8"))
    assert membership[FACT_F12]["member"] == "false"
    assert membership[CANDIDATE_VENUE_EQ]["member"] == "false"


def test_canonical_pack_matches_executor_and_manifest() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_PACK / name).read_bytes()).hexdigest() == digest
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["NEW_CANONICAL_DEFINITION"] == "true"
    assert claims["LEGACY_SEMANTICS_RECONSTRUCTED"] == "false"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bn_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BM_HEADING in runbook
    bn_section = _bn_section()
    assert OWNER_GO in bn_section
    assert (
        "THIS_SLICE=11.2.1.BN.FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION"
        in bn_section
    )
    assert "NEW_CANONICAL_DEFINITION=true" in bn_section
    assert "LEGACY_SEMANTICS_RECONSTRUCTED=false" in bn_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bn_section
    assert "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED=false" in bn_section
    assert "KINDS_INVENTED_THIS_GO=false" in bn_section
    assert "GATE_A_EXECUTED=false" in bn_section
    assert "VENUE_GET_COUNT=0" in bn_section
    assert "D6_FULLY_CLOSED=false" in bn_section
    assert "BM_CONTRACT_REUSED=true" in bn_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bn_section
    assert LIVE_EQUITY_STOCK_KIND_SET_IDENTITY in bn_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION_WP1.md" in mot
    assert BN_HEADING in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BN" in atlas
    assert "live_equity_stock_kind_set_new_canonical_definition_v1.py" in atlas
