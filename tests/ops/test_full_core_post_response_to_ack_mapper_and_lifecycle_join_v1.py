"""Offline Full-Core POST-result → Cap-11.1 lifecycle join tests.

Non-networking fixtures only. REAL_POST_COUNT=0. No venue POST.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.submission_semantics_v1 import (
    UnknownSubmitSemanticsV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_SUBMIT_RECON,
    REAL_VENUE_POST_ALLOWED,
    UNKNOWN_OUTCOME_RECON,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    attempt_envelope_bound_external_effect_send_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    ACKNOWLEDGED,
    FULL_CORE_POST_RESPONSE_TO_ACK_MAPPER_IMPLEMENTED,
    FULL_CORE_POST_SUBMIT_LIFECYCLE_JOIN_ACTIVATED,
    REJECTED,
    UNKNOWN,
    classify_full_core_post_result_v1,
    join_full_core_post_result_to_lifecycle_v1,
    prove_unknown_blocks_blind_resubmit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN_V1.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
MAPPER_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1/full_core_post_response_to_ack_mapper_v1.py"
)
SEND_SEAM_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py"
)
DW_HEADING = "### 11.2.1.DW FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)
PROTECTED_AUTHORITY_FILES = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_gate_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/durable_filegate_join_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/step_29p_capital_risk_admissibility_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/live_admission_gap_dag_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/constants_v1.py",
    "src/governance/canonical_order_intent_v1.py",
    "src/ops/capability_11_1_execution_domain_and_order_lifecycle_contracts_v1/order_lifecycle_state_machine_v1.py",
    "src/ops/capability_11_1_execution_domain_and_order_lifecycle_contracts_v1/submission_semantics_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py",
)
SENT_CLORDID = "pt-fc-post-submit-join-ack-v1"
VENUE_ORD_ID = "3926112627662393999"
FORBIDDEN_IMPORT_TOKENS = (
    "section_11_14_live_order_and_economic_evidence_ladder_v1",
    "adjudicate_live_submit_ack_observed_v1",
    "LIVE_SUBMIT_ACK_OBSERVED",
    "integrated_offline_trading_logic_replay_v1",
    "unknown_execution_outcome_recovery_v1",
    "governed_futures_universe_producer_v1",
    "productive_futures_ranking_producer_v1",
    "single_selected_future_policy_v1",
)


def _ack_payload(*, clordid: str = SENT_CLORDID) -> dict[str, Any]:
    return {
        "code": "0",
        "data": [
            {
                "sCode": "0",
                "ordId": VENUE_ORD_ID,
                "clOrdId": clordid,
            }
        ],
    }


def _post_result(
    *,
    payload: Mapping[str, Any],
    http_status: int = 200,
    unknown_outcome: bool = False,
    post_attempted: bool = True,
) -> FullCoreTradeOrderPostResultV1:
    return FullCoreTradeOrderPostResultV1(
        post_attempted=post_attempted,
        venue_live_contact=False,
        method="POST",
        endpoint="/api/v5/trade/order",
        http_status=http_status,
        payload=payload,
        transport_class="FULL_CORE_NON_NETWORKING_TEST_POST_V1",
        unknown_outcome=unknown_outcome,
    )


@dataclass
class FixturePostTransportV1:
    result: Optional[FullCoreTradeOrderPostResultV1] = None
    error: Optional[Exception] = None
    post_count: int = 0
    methods_used: list[str] = field(default_factory=list)

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1:
        del payload, permit_id, envelope_id, envelope_digest, one_shot_real_post
        self.post_count += 1
        self.methods_used.append("POST")
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise FullCoreProductiveHttpPostError("UNKNOWN_OUTCOME")
        return self.result


def _plan(*, clordid: str = SENT_CLORDID) -> VenuePlanCandidateV1:
    return VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid=clordid,
        venue_native_payload={
            "instId": "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )


def _send(*, transport: FixturePostTransportV1, tmp_path: Path):
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        _plan(),
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-16T06:00:00Z",
    )
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref="BOUNDED_FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN_V1",
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-post-submit-join-handle",
        bound=True,
    )
    return attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=tmp_path,
        transport=transport,
        handle=handle,
    )


def test_mapper_flags_are_activated() -> None:
    assert FULL_CORE_POST_RESPONSE_TO_ACK_MAPPER_IMPLEMENTED is True
    assert FULL_CORE_POST_SUBMIT_LIFECYCLE_JOIN_ACTIVATED is True


def test_accepted_ack_is_not_fill() -> None:
    result = _post_result(payload=_ack_payload())
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
        submit_count=1,
    )
    assert joined.typed_outcome == ACKNOWLEDGED
    assert joined.lifecycle_state == ACKNOWLEDGED
    assert joined.recon_class == POST_SUBMIT_RECON
    assert joined.fill_observed is False
    assert joined.ack_is_not_fill is True
    assert joined.http_success_is_not_ack is True
    assert joined.venue_order_id == VENUE_ORD_ID
    assert joined.restart_blocked is False
    assert joined.resubmit_allowed is False
    assert joined.real_post_count == 0
    assert joined.section_11_14_promoted is False


def test_http_200_alone_is_not_ack() -> None:
    result = _post_result(payload={"code": "0"}, http_status=200)
    classified = classify_full_core_post_result_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
    )
    assert classified["classification"] == UNKNOWN
    assert classified["reason"] == "DATA_CARDINALITY_NOT_EXACTLY_ONE"


def test_explicit_top_level_reject() -> None:
    result = _post_result(payload={"code": "1", "msg": "rejected"})
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
    )
    assert joined.typed_outcome == REJECTED
    assert joined.lifecycle_state == REJECTED
    assert joined.recon_class == POST_SUBMIT_RECON
    assert joined.fill_observed is False
    assert joined.resubmit_allowed is False
    assert joined.restart_blocked is False


def test_explicit_scode_reject() -> None:
    result = _post_result(
        payload={
            "code": "0",
            "data": [{"sCode": "51000", "sMsg": "rejected", "clOrdId": SENT_CLORDID}],
        }
    )
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
    )
    assert joined.typed_outcome == REJECTED
    assert joined.reason == "SCODE_NOT_ZERO"
    assert joined.fill_observed is False


def test_malformed_response_is_unknown() -> None:
    result = _post_result(payload={"raw": True})
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.recon_class == UNKNOWN_OUTCOME_RECON
    assert joined.restart_blocked is True
    assert prove_unknown_blocks_blind_resubmit_v1(joined) is True


def test_timeout_exception_is_unknown() -> None:
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=SENT_CLORDID,
        transport_error="UNKNOWN_OUTCOME",
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.post_attempted is True
    assert joined.recon_class == UNKNOWN_OUTCOME_RECON
    assert joined.restart_blocked is True
    assert joined.resubmit_allowed is False


def test_timeout_token_is_unknown() -> None:
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=SENT_CLORDID,
        transport_error="TimeoutError",
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.reason == "TIMEOUT_AFTER_POSSIBLE_SEND"


def test_clordid_mismatch_is_unknown_not_ack_or_reject() -> None:
    result = _post_result(payload=_ack_payload(clordid="other-id"))
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.reason == "CLORDID_IDENTITY_MISMATCH"


def test_ambiguous_second_submit_count_is_unknown_and_no_resubmit() -> None:
    result = _post_result(payload=_ack_payload())
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT_CLORDID,
        submit_count=2,
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.resubmit_allowed is False
    assert prove_unknown_blocks_blind_resubmit_v1(joined) is True


def test_unresolved_unknown_blocks_restart_and_blind_retry() -> None:
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=_post_result(payload={"code": "0"}),
        sent_clordid=SENT_CLORDID,
    )
    assert joined.typed_outcome == UNKNOWN
    assert joined.restart_blocked is True
    assert joined.exchange_query_before_retry_required is True
    machine = OrderLifecycleStateMachineV1(
        current_state=UNKNOWN,
        history=["SUBMIT_ATTEMPTED", UNKNOWN],
    )
    with pytest.raises(OrderLifecycleTransitionError) as exc:
        machine.transition(ACKNOWLEDGED, exchange_query_completed=False)
    assert exc.value.code == "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY"
    unknown = UnknownSubmitSemanticsV1()
    blind = unknown.evaluate_retry_admissibility(
        exchange_query_completed=False,
        blind_retry=True,
    )
    assert blind["admissible"] is False


def test_ack_without_fill_and_no_second_submit(tmp_path: Path) -> None:
    transport = FixturePostTransportV1(result=_post_result(payload=_ack_payload()))
    sent = _send(transport=transport, tmp_path=tmp_path)
    assert sent.real_post_count == 0
    assert sent.venue_live_contact is False
    assert sent.post_submit_join is not None
    assert sent.post_submit_join.typed_outcome == ACKNOWLEDGED
    assert sent.post_submit_join.fill_observed is False
    assert sent.post_submit_join.resubmit_allowed is False
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError) as exc:
        _send(transport=transport, tmp_path=tmp_path)
    assert str(exc.value) in {
        "CONSUMED_PERMIT",
        "REPLAYED_PERMIT",
        "FOLLOW_ON_SUBMIT_DENIED",
    }


def test_send_seam_timeout_stays_unknown_and_does_not_resubmit(tmp_path: Path) -> None:
    transport = FixturePostTransportV1(error=FullCoreProductiveHttpPostError("UNKNOWN_OUTCOME"))
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError) as exc:
        _send(transport=transport, tmp_path=tmp_path)
    assert str(exc.value) == "UNKNOWN_OUTCOME"
    joined = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=SENT_CLORDID,
        transport_error=str(exc.value),
    )
    assert joined.typed_outcome == UNKNOWN
    assert prove_unknown_blocks_blind_resubmit_v1(joined) is True
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError) as second:
        _send(transport=transport, tmp_path=tmp_path)
    assert str(second.value) in {
        "CONSUMED_PERMIT",
        "REPLAYED_PERMIT",
        "FOLLOW_ON_SUBMIT_DENIED",
    }


def test_send_seam_explicit_reject_is_not_fill(tmp_path: Path) -> None:
    transport = FixturePostTransportV1(
        result=_post_result(payload={"code": "1", "msg": "rejected"})
    )
    sent = _send(transport=transport, tmp_path=tmp_path)
    assert sent.post_submit_join is not None
    assert sent.post_submit_join.typed_outcome == REJECTED
    assert sent.post_submit_join.fill_observed is False
    assert sent.real_post_count == 0


def test_standing_gates_remain_fail_closed() -> None:
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"


def test_mapper_does_not_import_frozen_or_historical_authority() -> None:
    source = MAPPER_PATH.read_text(encoding="utf-8")
    import_lines = [
        line
        for line in source.splitlines()
        if line.lstrip().startswith("import ") or line.lstrip().startswith("from ")
    ]
    joined = "\n".join(import_lines)
    for token in FORBIDDEN_IMPORT_TOKENS:
        assert token not in joined


def test_send_seam_admission_predicates_remain_before_post() -> None:
    source = SEND_SEAM_PATH.read_text(encoding="utf-8")
    assert "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE" in source
    assert "DIRECT_STEP_29Q_SUBMISSION_FORBIDDEN" in source
    assert "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" in source
    post_idx = source.index("transport.post_trade_order")
    join_call_idx = source.index("post_submit_join = join_full_core_post_result_to_lifecycle_v1")
    assert post_idx < join_call_idx


def test_protected_surfaces_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            *PROTECTED_ALGORITHM_FILES,
            *PROTECTED_AUTHORITY_FILES,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert DW_HEADING in runbook
    assert "FULL_CORE_POST_RESPONSE_TO_ACK_MAPPER" in runbook
    assert "ACKNOWLEDGED | REJECTED | UNKNOWN" in runbook
    assert "UNKNOWN_SUBMIT_RESULT_NEVER_BLINDLY_RETRIED=true" in runbook
    dw_section = runbook[runbook.index(DW_HEADING) : runbook.index("## 11.3 Autonomy state model")]
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in dw_section
    assert "REAL_VENUE_POST_ALLOWED=false" in dw_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in dw_section
    assert "POST_COUNT=0" in dw_section
    assert "SECTION_11_14_PROMOTED=false" in dw_section
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN_V1" in spec
    assert "11.2.1.DW" in atlas
    assert "full_core_post_response_to_ack_mapper_v1.py" in atlas
