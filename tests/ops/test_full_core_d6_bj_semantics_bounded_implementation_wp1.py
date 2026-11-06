"""D6 BJ remaining-unknown kind semantics tests.

Typed status/reason layer. No GET. Empty KIND_SET remains fail-closed.
GATE_A and GATE_B are not executed.
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
    CANONICAL_PACK_RELPATH,
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FACT_F12,
    FACT_F13,
    FACT_F16,
    FACT_F17,
    FACT_F18,
    FACT_IDS,
    FACT_U05,
    KIND_SET_EMPTY,
    LAYER_HYPOTHESIS,
    OWNER_GO,
    REASON_CLAIMED_EXCLUDE_NOT_RATIFIED_NON_SOURCE,
    REASON_CLAIMED_INCLUDE_EMPTY_KIND_SET,
    REASON_CLAIMED_INCLUDE_UNRATIFIED_KIND,
    REASON_CONTRADICTORY_TYPED_CLAIMS,
    REASON_KIND_SET_EMPTY,
    REASON_MALFORMED_RECORD,
    REASON_MISSING_RECORD,
    REASON_NO_DECISION_CAPABLE_CLASS,
    REASON_PRECEDENCE,
    REASON_RESOLVED_INCLUDE_ADMISSIBLE,
    STATUS_CONTRADICTORY,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_RESOLVED,
    STATUS_UNRESOLVED,
    BjRemainingUnknownKindSemanticsError,
    attach_bj_semantics_to_d6_diagnostics_v1,
    evaluate_bj_remaining_unknown_kind_semantics_v1,
    execute_bj_remaining_unknown_kind_semantics_v1,
    reject_claimed_bj_semantics_authority_mutation_v1,
    select_precedent_reason_code_v1,
    select_precedent_status_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BJ_PACK_RELPATH,
    GATE_A_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION_WP1.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BJ_HEADING = "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE"
BK_HEADING = "11.2.1.BK FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION"
SEALED_BJ = REPO_ROOT / CANONICAL_BJ_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T06:15:00Z"


def _bk_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BK_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BL FULL_CORE_D6_BK_BOUNDED_IMPLEMENTATION",
            start,
        )
    ]


def _record(fact_id: str, **fields: str) -> dict[str, str]:
    payload = {"fact_id": fact_id, "claimed_decision": DECISION_REMAIN_UNKNOWN}
    payload.update(fields)
    return payload


def _all_unresolved(**overrides: dict[str, str]) -> list[dict[str, str]]:
    records = [_record(fact_id) for fact_id in FACT_IDS]
    by_id = {item["fact_id"]: item for item in records}
    for fact_id, fields in overrides.items():
        by_id[fact_id].update(fields)
    return [by_id[fact_id] for fact_id in FACT_IDS]


def _run(tmp_path: Path):
    return execute_bj_remaining_unknown_kind_semantics_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bj_pack=SEALED_BJ,
        evidence_root=tmp_path / "semantics",
        semantics_as_of=_AS_OF,
    )


def test_sealed_bj_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BJ) == 0


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_unresolved_remain_unknown(fact_id: str) -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(records=_all_unresolved())
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[fact_id].status == STATUS_UNRESOLVED
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN
    assert by_fact[fact_id].reason_code == REASON_NO_DECISION_CAPABLE_CLASS
    assert by_fact[fact_id].source_kind_admissible == "false"


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_missing(fact_id: str) -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=[_record(other) for other in FACT_IDS if other != fact_id]
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[fact_id].status == STATUS_MISSING
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN
    assert by_fact[fact_id].reason_code == REASON_MISSING_RECORD


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_malformed_status(fact_id: str) -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_all_unresolved(**{fact_id: {"claimed_status": "NOT_A_STATUS"}})
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[fact_id].status == STATUS_MALFORMED
    assert by_fact[fact_id].reason_code == REASON_MALFORMED_RECORD
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_contradictory_duplicate_claims(fact_id: str) -> None:
    records = _all_unresolved()
    records.append(_record(fact_id, claimed_decision=DECISION_INCLUDE))
    evaluated = evaluate_bj_remaining_unknown_kind_semantics_v1(records=records)
    by_fact = {item.fact_id: item for item in evaluated}
    assert by_fact[fact_id].status == STATUS_CONTRADICTORY
    assert by_fact[fact_id].reason_code == REASON_CONTRADICTORY_TYPED_CLAIMS
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_include_blocked_by_empty_kind_set(fact_id: str) -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_all_unresolved(**{fact_id: {"claimed_decision": DECISION_INCLUDE}})
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[fact_id].status == STATUS_CONTRADICTORY
    assert by_fact[fact_id].reason_code == REASON_CLAIMED_INCLUDE_EMPTY_KIND_SET
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN


@pytest.mark.parametrize("fact_id", FACT_IDS)
def test_each_fact_exclude_blocked_unless_ratified_non_source(fact_id: str) -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_all_unresolved(**{fact_id: {"claimed_decision": DECISION_EXCLUDE}})
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[fact_id].status == STATUS_CONTRADICTORY
    assert by_fact[fact_id].reason_code == REASON_CLAIMED_EXCLUDE_NOT_RATIFIED_NON_SOURCE
    assert by_fact[fact_id].decision == DECISION_REMAIN_UNKNOWN


def test_combination_f12_missing_f13_malformed_u05_contradictory() -> None:
    records = [
        _record(FACT_F13, claimed_status="NOT_A_STATUS"),
        _record(FACT_U05),
        _record(FACT_U05, claimed_decision=DECISION_INCLUDE),
        _record(FACT_F16),
        _record(FACT_F17),
        _record(FACT_F18),
    ]
    evaluated = evaluate_bj_remaining_unknown_kind_semantics_v1(records=records)
    by_fact = {item.fact_id: item for item in evaluated}
    assert by_fact[FACT_F12].status == STATUS_MISSING
    assert by_fact[FACT_F13].status == STATUS_MALFORMED
    assert by_fact[FACT_U05].status == STATUS_CONTRADICTORY
    assert by_fact[FACT_F16].status == STATUS_UNRESOLVED
    assert select_precedent_status_v1(tuple(item.status for item in evaluated)) == (
        STATUS_CONTRADICTORY
    )


def test_unratified_kind_blocks_include_even_if_kind_set_resolved_flag_true() -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_all_unresolved(**{FACT_F12: {"claimed_decision": DECISION_INCLUDE}}),
        kind_set="F12",
        kind_set_resolved=True,
        ratified_source_kinds=(),
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[FACT_F12].reason_code == REASON_CLAIMED_INCLUDE_UNRATIFIED_KIND
    assert by_fact[FACT_F12].decision == DECISION_REMAIN_UNKNOWN


def test_future_evidence_can_resolve_include_without_contract_break() -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_all_unresolved(
            **{
                FACT_F12: {
                    "claimed_decision": DECISION_INCLUDE,
                    "evidence_class": GATE_A_ID,
                }
            }
        ),
        kind_set="F12",
        kind_set_resolved=True,
        ratified_source_kinds=(FACT_F12,),
    )
    by_fact = {item.fact_id: item for item in records}
    assert by_fact[FACT_F12].status == STATUS_RESOLVED
    assert by_fact[FACT_F12].decision == DECISION_INCLUDE
    assert by_fact[FACT_F12].reason_code == REASON_RESOLVED_INCLUDE_ADMISSIBLE
    assert by_fact[FACT_F13].status == STATUS_UNRESOLVED
    assert by_fact[FACT_F13].decision == DECISION_REMAIN_UNKNOWN


def test_reason_precedence_is_fixed_and_deterministic() -> None:
    assert REASON_PRECEDENCE[0] == REASON_CONTRADICTORY_TYPED_CLAIMS
    assert (
        select_precedent_reason_code_v1(
            (REASON_KIND_SET_EMPTY, REASON_NO_DECISION_CAPABLE_CLASS, REASON_MISSING_RECORD)
        )
        == REASON_MISSING_RECORD
    )
    first = select_precedent_reason_code_v1(
        (REASON_NO_DECISION_CAPABLE_CLASS, REASON_MALFORMED_RECORD)
    )
    second = select_precedent_reason_code_v1(
        (REASON_MALFORMED_RECORD, REASON_NO_DECISION_CAPABLE_CLASS)
    )
    assert first == second == REASON_MALFORMED_RECORD


def test_replay_order_does_not_change_evaluation() -> None:
    forward = evaluate_bj_remaining_unknown_kind_semantics_v1(records=_all_unresolved())
    reversed_records = list(reversed(_all_unresolved()))
    backward = evaluate_bj_remaining_unknown_kind_semantics_v1(records=reversed_records)
    assert [item.fact_id for item in forward] == list(FACT_IDS)
    assert [item.status for item in forward] == [item.status for item in backward]
    assert [item.reason_code for item in forward] == [item.reason_code for item in backward]


def test_identical_duplicate_records_are_replay_stable() -> None:
    records = _all_unresolved() + [_record(FACT_F18)]
    evaluated = evaluate_bj_remaining_unknown_kind_semantics_v1(records=records)
    by_fact = {item.fact_id: item for item in evaluated}
    assert by_fact[FACT_F18].status == STATUS_UNRESOLVED
    assert by_fact[FACT_F18].decision == DECISION_REMAIN_UNKNOWN


def test_empty_kind_set_is_hard_invariant() -> None:
    with pytest.raises(
        BjRemainingUnknownKindSemanticsError, match="KIND_SET_EMPTY_CANNOT_BE_RESOLVED"
    ):
        evaluate_bj_remaining_unknown_kind_semantics_v1(
            records=_all_unresolved(),
            kind_set=KIND_SET_EMPTY,
            kind_set_resolved=True,
        )


def test_gate_execution_is_forbidden() -> None:
    with pytest.raises(
        BjRemainingUnknownKindSemanticsError,
        match="GATE_EXECUTION_FORBIDDEN_IN_THIS_LAYER",
    ):
        evaluate_bj_remaining_unknown_kind_semantics_v1(
            records=_all_unresolved(),
            gate_a_executed=True,
        )


def test_hypothesis_layer_is_not_authority() -> None:
    with pytest.raises(BjRemainingUnknownKindSemanticsError, match="FORBIDDEN_EVIDENCE_LAYER"):
        evaluate_bj_remaining_unknown_kind_semantics_v1(
            records=_all_unresolved(**{FACT_F16: {"layer": LAYER_HYPOTHESIS}})
        )


def test_diagnostics_attach_does_not_mutate_standing_d6_pins() -> None:
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(records=_all_unresolved())
    existing = {
        "KIND_SET_RESOLVED": "false",
        "D6_FULLY_CLOSED": "false",
        "D7_AUTHORIZED": "false",
        "MS2_AUTHORIZED": "false",
        "RAW_EQ_SOURCE_AUTHORITY": "false",
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
    }
    attached = attach_bj_semantics_to_d6_diagnostics_v1(
        existing=existing,
        records=records,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved="false",
        venue_get_count="0",
        gate_a_executed="false",
        gate_b_executed="false",
    )
    for key, value in existing.items():
        assert attached[key] == value
    assert attached["F12_STATUS"] == STATUS_UNRESOLVED
    assert attached["U05_STATUS"] == STATUS_UNRESOLVED
    assert attached["UNKNOWN_SEMANTICS_INVENTED"] == "false"


def test_reject_include_and_gate_execution_claims() -> None:
    with pytest.raises(BjRemainingUnknownKindSemanticsError, match="BJ_SEMANTICS_CANNOT_INCLUDE"):
        reject_claimed_bj_semantics_authority_mutation_v1(
            claimed_proof=DECISION_INCLUDE,
            fact_id=FACT_F12,
        )
    with pytest.raises(BjRemainingUnknownKindSemanticsError, match="EXECUTE_GATE_A"):
        reject_claimed_bj_semantics_authority_mutation_v1(
            claimed_proof="EXECUTE_GATE_A",
            fact_id=FACT_F13,
        )


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(BjRemainingUnknownKindSemanticsError, match="OWNER_GO_MISMATCH"):
        execute_bj_remaining_unknown_kind_semantics_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bj_pack=SEALED_BJ,
            evidence_root=tmp_path / "semantics",
            semantics_as_of=_AS_OF,
        )
    assert not (tmp_path / "semantics").exists()


def test_sealed_bj_persist_keeps_unknown_and_empty_kind_set(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.f12_status == STATUS_UNRESOLVED
    assert result.f13_status == STATUS_UNRESOLVED
    assert result.u05_status == STATUS_UNRESOLVED
    assert result.f16_status == STATUS_UNRESOLVED
    assert result.f17_status == STATUS_UNRESOLVED
    assert result.f18_status == STATUS_UNRESOLVED
    assert result.f12_decision == DECISION_REMAIN_UNKNOWN
    assert result.kind_set == KIND_SET_EMPTY
    assert result.kind_set_resolved == "false"
    assert result.venue_get_count == "0"
    assert result.gate_a_executed == "false"
    assert result.gate_b_executed == "false"
    assert result.unknown_semantics_invented == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert result.ms2_authorized == "false"
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["EXISTING_NON_SOURCE_AND_OTHER_DOMAIN_UNCHANGED"] == "true"
    assert claims["MASTER_V2_UNCHANGED"] == "true"


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
    assert claims["F12_STATUS"] == STATUS_UNRESOLVED
    assert claims["KIND_SET"] == KIND_SET_EMPTY
    assert claims["VENUE_GET_COUNT"] == "0"


def test_runbook_bk_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bj_section = RUNBOOK.read_text(encoding="utf-8")
    assert BJ_HEADING in bj_section
    bk_section = _bk_section()
    assert OWNER_GO in bk_section
    assert "THIS_SLICE=11.2.1.BK.FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION" in bk_section
    assert "F12_STATUS=UNRESOLVED" in bk_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in bk_section
    assert "KIND_SET_RESOLVED=false" in bk_section
    assert "GATE_A_EXECUTED=false" in bk_section
    assert "VENUE_GET_COUNT=0" in bk_section
    assert "D6_FULLY_CLOSED=false" in bk_section
    assert "DOCS_TOKEN_FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION_WP1" in spec
    assert "FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION_WP1.md" in mot
    assert "11.2.1.BK FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION" in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BK" in atlas
    assert "bj_remaining_unknown_kind_semantics_v1.py" in atlas
