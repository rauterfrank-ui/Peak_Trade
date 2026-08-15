"""R6 S3 Phase-8.2 runtime architecture tests (offline, unauthorized, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.verifier_v1 import (
    evaluate_r6_phase_8_1_policy_precondition_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.arbitration_v1 import (
    arbitrate_intents_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
    CONTRACT_CONFIG_REL_PATH,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.instrument_context_v1 import (
    isolate_instrument_contexts_v1,
    mutate_isolated_state_copy_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    IntentV1,
    Phase82GraphRequestV1,
    RankingCandidateV1,
    R6S3RuntimeArchitectureError,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.restart_v1 import (
    reconstruct_contexts_v1,
    snapshot_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    evaluate_r6_s3_multi_future_runtime_architecture_v1,
    validate_layer_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23


def _entry_context(
    instrument_id: str,
    *,
    recon: str = "RECONCILED",
    qty: str = "2",
    state: dict[str, str] | None = None,
) -> InstrumentContextV1:
    return InstrumentContextV1(
        instrument_id=instrument_id,
        directional_side="FLAT",
        intended_action="ENTRY",
        intended_side="LONG",
        intended_qty=qty,
        reconciliation_status=recon,
        single_use_permission=True,
        isolated_state=state or {"marker": instrument_id},
    )


def _request(
    *contexts: InstrumentContextV1,
    selected: str = "AAA-FUT",
    extra: tuple[str, ...] = ("BBB-FUT", "CCC-FUT"),
    kill: bool = False,
    snapshot: dict | None = None,
) -> Phase82GraphRequestV1:
    candidates = [RankingCandidateV1(selected, 1)]
    candidates.extend(RankingCandidateV1(name, index + 2) for index, name in enumerate(extra))
    return Phase82GraphRequestV1(
        selected_future_id=selected,
        ranking_candidates=tuple(candidates),
        instrument_contexts=contexts,
        global_kill_switch=kill,
        restart_snapshot=snapshot,
        economic_evidence_pass=True,
        research_signal_pass=True,
    )


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_authorization_fail_closed_implemented_true_authorized_false() -> None:
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is True
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    result = evaluate_phase_82_graph_v1(
        _request(_entry_context("AAA-FUT"), _entry_context("BBB-FUT"))
    )
    assert result.implemented is True
    assert result.authorized is False
    assert result.effective_runtime_mode == CURRENT_EFFECTIVE_RUNTIME_MODE
    assert result.max_positions_effective == 1
    assert len(result.effective_active_ids) == 1
    assert result.effective_active_ids == ("AAA-FUT",)
    assert result.submit_unlocked is False
    assert result.writer_bundle.submit_unlocked is False
    assert result.live_authorized is False
    assert result.testnet_authorized is False
    assert result.canary_authorized is False
    assert result.order_effect == "NONE"


def test_requested_authorized_true_is_rejected() -> None:
    request = default_single_future_request_v1("AAA-FUT")
    with pytest.raises(R6S3RuntimeArchitectureError, match="authorized_rejected"):
        evaluate_phase_82_graph_v1(
            Phase82GraphRequestV1(
                selected_future_id=request.selected_future_id,
                ranking_candidates=request.ranking_candidates,
                instrument_contexts=request.instrument_contexts,
                requested_authorized=True,
            )
        )


def test_per_instrument_isolation_and_recon_block_is_local() -> None:
    isolated = isolate_instrument_contexts_v1(
        (
            _entry_context("AAA-FUT", recon="UNRESOLVED", state={"k": "a"}),
            _entry_context("BBB-FUT", recon="RECONCILED", state={"k": "b"}),
        )
    )
    patched = mutate_isolated_state_copy_v1(isolated, "AAA-FUT", {"k": "patched-a"})
    assert patched["AAA-FUT"].isolated_state["k"] == "patched-a"
    assert patched["BBB-FUT"].isolated_state["k"] == "b"
    assert isolated["AAA-FUT"].isolated_state["k"] == "a"
    result = evaluate_phase_82_graph_v1(
        _request(
            _entry_context("AAA-FUT", recon="UNRESOLVED"),
            _entry_context("BBB-FUT", recon="RECONCILED"),
        )
    )
    by_id = {intent.instrument_id: intent for intent in result.arbitrated_intents}
    assert by_id["AAA-FUT"].blocked is True
    assert "NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION" in by_id["AAA-FUT"].block_reasons
    assert by_id["BBB-FUT"].blocked is False
    assert result.isolated_contexts["AAA-FUT"]["isolated_state"]["marker"] == "AAA-FUT"
    assert result.isolated_contexts["BBB-FUT"]["isolated_state"]["marker"] == "BBB-FUT"


def test_deterministic_arbitration_identical_input_identical_order() -> None:
    intents = (
        IntentV1("BBB-FUT", "ENTRY", "LONG", "1", sequence=2),
        IntentV1("AAA-FUT", "EXIT", "LONG", "1", sequence=9),
        IntentV1("CCC-FUT", "REDUCE", "SHORT", "1", sequence=1),
    )
    first = [row.to_mapping() for row in arbitrate_intents_v1(intents)]
    second = [row.to_mapping() for row in arbitrate_intents_v1(tuple(reversed(intents)))]
    assert first == second
    assert [row["instrument_id"] for row in first] == ["AAA-FUT", "BBB-FUT", "CCC-FUT"]
    with pytest.raises(R6S3RuntimeArchitectureError, match="conflict"):
        arbitrate_intents_v1(
            (
                IntentV1("AAA-FUT", "ENTRY", "LONG", "1", sequence=1),
                IntentV1("AAA-FUT", "EXIT", "SHORT", "1", sequence=2),
            )
        )


def test_portfolio_risk_consumes_s2_and_can_only_restrict() -> None:
    result = evaluate_phase_82_graph_v1(
        _request(_entry_context("AAA-FUT", qty="5"), _entry_context("BBB-FUT", qty="5")),
        portfolio_reduce_entry_qty_to="1",
    )
    s2 = evaluate_r6_s2_portfolio_risk_contracts_v1()
    assert s2["verdict"] == "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1"
    assert s2["multi_future_runtime_authorized"] is False
    for intent in result.portfolio_intents:
        assert intent.qty == "1"
        assert "PORTFOLIO_RISK_REDUCED" in intent.block_reasons
        assert intent.blocked is False
    assert result.submit_unlocked is False
    assert result.claims["PORTFOLIO_CREATED_ORDER_AUTHORITY"] is False


def test_global_safety_follows_portfolio_and_can_only_restrict_or_block() -> None:
    reduced = evaluate_phase_82_graph_v1(
        _request(_entry_context("AAA-FUT", qty="4"), _entry_context("BBB-FUT", qty="4")),
        portfolio_reduce_entry_qty_to="2",
    )
    killed = evaluate_phase_82_graph_v1(
        _request(
            _entry_context("AAA-FUT", qty="4"),
            _entry_context("BBB-FUT", qty="4"),
            kill=True,
        ),
        portfolio_reduce_entry_qty_to="2",
    )
    assert reduced.stage_order.index("global_portfolio_risk") < reduced.stage_order.index(
        "global_safety"
    )
    for intent in reduced.safety_intents:
        assert intent.qty == "2"
        assert intent.blocked is False
    for intent in killed.safety_intents:
        assert intent.blocked is True
        assert "GLOBAL_KILL_SWITCH" in intent.block_reasons
        assert intent.qty == "0"


def test_single_writer_boundary_is_canonical_and_unique() -> None:
    result = evaluate_phase_82_graph_v1(
        _request(_entry_context("AAA-FUT"), _entry_context("BBB-FUT"))
    )
    bundle = result.writer_bundle
    assert bundle.execution_writer_identity == CANONICAL_EXECUTION_WRITER_IDENTITY
    assert bundle.accounting_writer_identity == CANONICAL_ACCOUNTING_WRITER_IDENTITY
    assert len(bundle.intents) == 2
    mapping = bundle.to_mapping()
    assert mapping["execution_writer_count"] == 1
    assert mapping["accounting_writer_count"] == 1
    assert mapping["submit_unlocked"] is False
    assert mapping["durable_before_submit"] is True


def test_reconciliation_unresolved_does_not_merge_globally() -> None:
    result = evaluate_phase_82_graph_v1(
        _request(
            _entry_context("AAA-FUT", recon="UNRESOLVED"),
            InstrumentContextV1(
                instrument_id="BBB-FUT",
                directional_side="LONG",
                intended_action="HOLD",
                intended_side="LONG",
                intended_qty="0",
                reconciliation_status="RECONCILED",
                isolated_state={"k": "b"},
            ),
        )
    )
    by_id = {intent.instrument_id: intent for intent in result.arbitrated_intents}
    assert by_id["AAA-FUT"].blocked is True
    assert by_id["BBB-FUT"].blocked is False
    assert by_id["BBB-FUT"].action == "HOLD"
    assert result.isolated_contexts["BBB-FUT"]["reconciliation_status"] == "RECONCILED"


def test_restart_reconstructs_deterministically_and_cannot_authorize() -> None:
    original = (
        _entry_context("AAA-FUT", recon="RECONCILED"),
        _entry_context("BBB-FUT", recon="UNKNOWN"),
    )
    snapshot = dict(snapshot_contexts_v1(original))
    reconstructed = reconstruct_contexts_v1(snapshot, authorized_after_restart=False)
    assert [row.instrument_id for row in reconstructed] == ["AAA-FUT", "BBB-FUT"]
    assert reconstructed[1].reconciliation_status == "UNKNOWN"
    assert reconstructed[1].stale is True
    with pytest.raises(R6S3RuntimeArchitectureError, match="restart_cannot_create_authorization"):
        reconstruct_contexts_v1(snapshot, authorized_after_restart=True)
    result = evaluate_phase_82_graph_v1(_request(*original, snapshot=snapshot))
    assert result.authorized is False
    assert result.submit_unlocked is False
    unknown = {intent.instrument_id: intent for intent in result.arbitrated_intents}["BBB-FUT"]
    assert unknown.blocked is True


def test_backward_compatible_single_selected_future_semantics() -> None:
    result = evaluate_phase_82_graph_v1(
        default_single_future_request_v1("BTC-USDT-SWAP", extra_candidates=("ETH-USDT-SWAP",))
    )
    assert result.effective_active_ids == ("BTC-USDT-SWAP",)
    assert result.max_positions_effective == 1
    assert cap23.MAX_POSITIONS_EFFECTIVE == 1
    assert cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert getattr(cap72, "MULTI_FUTURE_RUNTIME_IMPLEMENTED", False) is False
    s1 = evaluate_r6_phase_8_1_policy_precondition_v1()
    s2 = evaluate_r6_s2_portfolio_risk_contracts_v1()
    assert s1["verdict"] == "PASS_R6_PHASE_8_1_POLICY_PRECONDITION_V1"
    assert s1["multi_future_runtime_authorized"] is False
    assert s1["multi_future_runtime_implemented"] is False
    assert s2["verdict"] == "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1"
    assert s2["max_positions_effective"] == 1


def test_no_authority_claim_from_implementation_objects() -> None:
    claims = evaluate_r6_s3_multi_future_runtime_architecture_v1()
    assert claims["verdict"] == "PASS_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1"
    assert claims["multi_future_runtime_implemented"] is True
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["live_authorized"] is False
    assert claims["testnet_authorized"] is False
    assert claims["canary_authorized"] is False
    assert claims["order_effect"] == "NONE"
    assert claims["submit_unlocked"] is False
    assert claims["second_execution_authority_created"] is False
    assert claims["second_accounting_authority_created"] is False
    assert claims["trading_authority_expanded"] is False
    assert claims["g13_unchanged"] is True
    assert claims["next_stage_automatically_authorized"] is False


def test_config_cannot_authorize_or_raise_positions() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    with pytest.raises(R6S3RuntimeArchitectureError, match="multi_future_runtime_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    with pytest.raises(R6S3RuntimeArchitectureError, match="max_positions_effective"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["submit_unlocked"] = True
    with pytest.raises(R6S3RuntimeArchitectureError, match="submit_unlocked"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_implemented"] = False
    with pytest.raises(R6S3RuntimeArchitectureError, match="multi_future_runtime_implemented"):
        validate_layer_config_v1(payload)
