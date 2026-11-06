"""CURRENT_PRODUCTIVE envelope-bound single-use External-Effect send-seam tests.

Offline. Non-networking transport only. REAL_POST_COUNT=0.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXACT_ENVELOPE_REQUIRED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FOLLOW_ON_SUBMIT_ISOLATED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    REPLAY_PROTECTION_DURABLE,
    REPLAY_PROTECTION_PRESENT,
    SINGLE_USE_EXTERNAL_EFFECT_PERMIT,
    SUBMISSION_AUTHORIZED,
    SUBMIT_UNLOCKED,
    SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    attempt_envelope_bound_external_effect_send_v1,
    prove_follow_on_submit_isolated_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    persist_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    FullCoreExternalEffectPermitError,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FullCoreFinalOrderEnvelopeError,
    bind_final_order_envelope_from_venue_plan_v1,
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveEnvelopeBoundSendSeamError,
    execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED as CANARY_LIVE_ARMED,
    LIVE_ORDER_AUTHORIZED as CANARY_LIVE_ORDER_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED as SECTION_11_14_LIVE_ARMED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DI_HEADING = (
    "### 11.2.1.DI FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM"
)
NEXT_BLOCKER = "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)
AUTHORITY_REF = OWNER_GO


def _plan(*, clordid: str = "pt-fc-envelope-bound-seam-test-v1") -> VenuePlanCandidateV1:
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
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )


def _envelope(*, clordid: str = "pt-fc-envelope-bound-seam-test-v1"):
    return bind_final_order_envelope_from_venue_plan_v1(
        _plan(clordid=clordid),
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-15T21:20:00Z",
    )


def _permit(envelope):
    return issue_external_effect_permit_v1(
        envelope,
        authority_ref=AUTHORITY_REF,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )


def _handle() -> FullCoreSendCredentialHandleV1:
    return FullCoreSendCredentialHandleV1(handle_id="full-core-envelope-bound-handle", bound=True)


def _intent(*, execution_eligible: bool = True) -> CanonicalOrderIntentV1:
    return CanonicalOrderIntentV1(
        intent_id="step-29q-plan-only",
        intent_version="v1",
        decision_id="step-29q-plan-only",
        instrument_id="fixture-not-live",
        trading_epoch="fixture",
        canonical_trading_logic_version="v1",
        capital_envelope_ref="fixture",
        pre_sizing_risk_ref="fixture",
        sizing_result_ref="fixture",
        post_sizing_risk_ref="fixture",
        policy_digest="fixture",
        config_digest="fixture",
        implementation_digest="fixture",
        provenance_digest="fixture",
        side="buy",
        intent_action="PLAN_ONLY",
        quantity=Decimal("1"),
        quantity_unit="CONTRACTS",
        quantity_provenance="fixture",
        reduce_only=False,
        position_effect="OPEN",
        order_type_policy="market",
        price_policy="none",
        time_in_force_policy="GTC",
        max_slippage_policy="none",
        expected_position_side="net",
        instrument_metadata_ref="fixture",
        execution_eligible=execution_eligible,
        submission_authorized=False,
    )


class _TimeoutTransport:
    transport_class = "TIMEOUT_TEST_DOUBLE"
    post_count = 0

    def post_trade_order(self, **kwargs: object) -> FullCoreTradeOrderPostResultV1:
        del kwargs
        raise TimeoutError("simulated-client-timeout")


def test_standing_flags_close_without_real_external_effect() -> None:
    assert CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_CREATED is True
    assert ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is True
    assert EXACT_ENVELOPE_REQUIRED is True
    assert SINGLE_USE_EXTERNAL_EFFECT_PERMIT is True
    assert MAX_EXTERNAL_EFFECT_POST_COUNT == 1
    assert REPLAY_PROTECTION_PRESENT is True
    assert REPLAY_PROTECTION_DURABLE is True
    assert FOLLOW_ON_SUBMIT_ISOLATED is True
    assert FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is True
    assert SUBMIT_UNLOCKED is False
    assert SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert SUBMISSION_AUTHORIZED is True
    assert LIVE_AUTHORIZED is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert CANARY_LIVE_ARMED is False
    assert CANARY_LIVE_ORDER_AUTHORIZED is False
    assert SECTION_11_14_LIVE_ARMED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "836a89b4d4ff1eace55ad320a2d7c24b5227d155"
    assert current_productive_first_real_blocker_v1() == NEXT_BLOCKER
    assert gap_node_v1("EXTERNAL_EFFECT").implementation_status == (
        "ENVELOPE_BOUND_SINGLE_USE_SEAM_IMPLEMENTED_STANDING_FALSE"
    )


def test_happy_path_exactly_one_mocked_post(tmp_path: Path) -> None:
    envelope = _envelope()
    permit = _permit(envelope)
    transport = FullCoreNonNetworkingTestPostTransportV1()
    result = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=tmp_path / "happy",
        transport=transport,
        handle=_handle(),
    )
    assert result.mocked_post_count == 1
    assert result.real_post_count == 0
    assert result.venue_live_contact is False
    assert result.durable_consumed is True
    assert result.follow_on_submit_isolated is True
    assert transport.post_count == 1
    assert transport.venue_live_contact is False


def test_fail_closed_no_permit_wrong_permit_wrong_envelope(tmp_path: Path) -> None:
    envelope_a = _envelope(clordid="pt-fc-envelope-a")
    envelope_b = _envelope(clordid="pt-fc-envelope-b")
    permit_a = _permit(envelope_a)
    handle = _handle()
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="NO_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope_a,
            permit=None,
            store_root=tmp_path / "no-permit",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
        )
    wrong = replace(permit_a, permit_id="eep-not-the-canonical-permit-id")
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="WRONG_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope_a,
            permit=wrong,
            store_root=tmp_path / "wrong-permit",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
        )
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="WRONG_ENVELOPE"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope_b,
            permit=permit_a,
            store_root=tmp_path / "wrong-envelope",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
        )


def test_fail_closed_digest_mismatch_and_malformed_envelope() -> None:
    envelope = _envelope()
    mutated = replace(envelope, envelope_digest="0" * 64)
    with pytest.raises(FullCoreFinalOrderEnvelopeError, match="ENVELOPE_DIGEST_MISMATCH"):
        issue_external_effect_permit_v1(mutated, authority_ref=AUTHORITY_REF)
    with pytest.raises(FullCoreFinalOrderEnvelopeError, match="INSTRUMENT_ID_MISSING"):
        build_final_order_envelope_v1(
            instrument_id=" ",
            side="buy",
            order_type="market",
            quantity="1",
            quantity_unit="CONTRACTS",
            td_mode="cross",
            reduce_only=False,
            client_order_id="pt-malformed",
            path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
            venue_plan_clordid="pt-malformed",
            quantity_source="TEST",
            side_source="TEST",
            instrument_source="TEST",
            admission_ref="TEST",
            provenance_ref="TEST",
            creation_epoch="2026-09-15T21:20:00Z",
        )


def test_fail_closed_consumed_replay_second_submit(tmp_path: Path) -> None:
    envelope = _envelope()
    permit = _permit(envelope)
    handle = _handle()
    transport = FullCoreNonNetworkingTestPostTransportV1()
    store = tmp_path / "consumed"
    attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=store,
        transport=transport,
        handle=handle,
    )
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CONSUMED_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=store,
            transport=transport,
            handle=handle,
        )
    assert transport.post_count == 1
    other = _envelope(clordid="pt-fc-envelope-follow-on")
    other_permit = _permit(other)
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="FOLLOW_ON_SUBMIT_DENIED"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=other,
            permit=other_permit,
            store_root=store,
            transport=transport,
            handle=handle,
        )
    assert prove_follow_on_submit_isolated_v1(
        envelope=envelope,
        permit=permit,
        store_root=store,
        transport=transport,
        handle=handle,
    )
    replay_store = tmp_path / "replay"
    persist_external_effect_durable_consume_v1(
        store_root=replay_store,
        permit=permit,
        envelope=envelope,
        durable_state=DURABLE_STATE_SENT_INITIATED,
        post_count=1,
        outcome="SENT_INITIATED_UNKNOWN_UNTIL_TRANSPORT",
    )
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CONSUMED_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=replay_store,
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
        )


def test_fail_closed_standing_gates_kill_switch_filegate() -> None:
    envelope = _envelope()
    with pytest.raises(FullCoreExternalEffectPermitError, match="SUBMISSION_AUTHORIZED_FALSE"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            submission_authorized=False,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="LIVE_AUTHORIZED_FALSE"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            live_authorized=False,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="LIVE_ARMED_FALSE"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            live_armed=False,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="WIRE_SEND_NOT_PERMITTED"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            wire_send_permitted=False,
        )
    with pytest.raises(
        FullCoreExternalEffectPermitError, match="PRODUCTIVE_WIRE_SEND_NOT_REACHABLE"
    ):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            productive_wire_send_reachable=False,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="KILL_SWITCH_BLOCKED"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            kill_switch_blocked=True,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="KILL_SWITCH_EVIDENCE_NOT_TRUSTED"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            durable_kill_switch_evidence_status=(DurableKillSwitchEvidenceStatusV1.MISSING.value),
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="FILEGATE_DENY"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            filegate_denied=True,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="STEP_29Q_MUST_REMAIN_PLAN_ONLY"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            step_29q_status="ELIGIBLE",
        )


def test_fail_closed_missing_credentials_transport_direct_29q_unknown_outcome(
    tmp_path: Path,
) -> None:
    envelope = _envelope()
    permit = _permit(envelope)
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CREDENTIAL_HANDLE_MISSING"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=tmp_path / "no-handle",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=None,
        )
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="TRANSPORT_MISSING"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=tmp_path / "no-transport",
            transport=None,
            handle=_handle(),
        )
    with pytest.raises(
        FullCoreEnvelopeBoundSendSeamError,
        match="DIRECT_STEP_29Q_SUBMISSION_FORBIDDEN",
    ):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=tmp_path / "direct-29q",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=_handle(),
            canonical_intent=_intent(),
        )
    timeout_store = tmp_path / "timeout"
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="UNKNOWN_OUTCOME"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=timeout_store,
            transport=_TimeoutTransport(),  # type: ignore[arg-type]
            handle=_handle(),
        )
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CONSUMED_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=timeout_store,
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=_handle(),
        )


def test_productive_http_transport_never_opens_socket() -> None:
    handle = _handle()
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=handle)
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0
    assert transport.venue_live_contact is False


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveEnvelopeBoundSendSeamError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
        )
    with pytest.raises(
        CurrentProductiveEnvelopeBoundSendSeamError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
        )


def test_evaluate_closes_seam_without_real_post(tmp_path: Path) -> None:
    result = execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
    )
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.envelope_bound_single_use_external_effect_seam == "true"
    assert result.exact_envelope_required == "true"
    assert result.single_use == "true"
    assert result.max_post_count == "1"
    assert result.replay_protection_durable == "true"
    assert result.follow_on_submit_isolated == "true"
    assert result.full_core_actual_http_post_seam_implemented == "true"
    assert result.external_effect_authorized == "false"
    assert result.real_external_effect_authorized == "false"
    assert result.step_29q_status == "PLAN_ONLY"
    assert result.mocked_post_count == "1"
    assert result.real_post_count == "0"
    assert result.post_count == "0"
    assert result.first_real_blocker == NEXT_BLOCKER
    assert result.blocker_class == "E"
    assert result.manifest_verify_rc == 0
    assert claims["POST_COUNT"] == "0"
    assert claims["ACTUAL_ORDER_SUBMIT_PERFORMED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert claims["AUTONOMOUS_FOLLOW_ON_EXECUTION_ALLOWED"] == "false"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["PROTECTED_SURFACES_CHANGED"] == "false"
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
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
    assert DI_HEADING in runbook
    assert THIS_SLICE in runbook
    di_section = runbook[
        runbook.index(
            "11.2.1.DI FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM"
        ) : runbook.index("## 11.3 Autonomy state model")
    ]
    assert "ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM=true" in di_section
    assert "SINGLE_USE=true" in di_section
    assert "MAX_POST_COUNT=1" in di_section
    assert "REPLAY_PROTECTION_DURABLE=true" in di_section
    assert "FOLLOW_ON_SUBMIT_ISOLATED=true" in di_section
    assert "FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED=true" in di_section
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in di_section
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in di_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in di_section
    assert "POST_COUNT=0" in di_section
    assert f"FIRST_DEFINITIVE_BLOCK={NEXT_BLOCKER}" in di_section
    dh_section = runbook[
        runbook.index(
            "11.2.1.DH FULL_CORE_CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER"
        ) : runbook.index(
            "11.2.1.DI FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM"
        )
    ]
    assert "LIVE_AUTHORIZED=true" in dh_section
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in dh_section
    assert "FIRST_DEFINITIVE_BLOCK=EXTERNAL_EFFECT_NOT_AUTHORIZED" in dh_section
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_V1"
        in spec
    )
    assert "11.2.1.DI" in atlas
    assert "current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM"] == "true"
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["FIRST_REAL_BLOCKER"] == NEXT_BLOCKER
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["MOCKED_POST_COUNT"] == "1"
    assert claims["REAL_POST_COUNT"] == "0"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
