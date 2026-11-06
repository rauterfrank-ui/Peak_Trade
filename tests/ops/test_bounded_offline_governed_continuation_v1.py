"""Two real N1 cycles, retained owners/ledgers and durable session bounds."""

from pathlib import Path
from dataclasses import replace
import json

import pytest

from src.ops.bounded_peaktrade_system_composition_v1 import session_v1 as sessions
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedCycleOrchestratorError,
)
from tests.ops import test_adverse_time_exit_consumer_semantics_v1 as scenario
from tests.ops.test_bounded_offline_episode_session_v1 import _manifest, _session


@pytest.mark.parametrize("direction", [1, -1])
def test_two_actual_cycles_across_restart_keep_owners_and_original_ledgers(
    tmp_path, monkeypatch, direction
):
    original_args = scenario._args

    def pinned(*args):
        return {**original_args(*args), "repository_sha": "a" * 40}

    monkeypatch.setattr(scenario, "_args", pinned)
    context, accounting, recover, invoke = scenario._scenario(tmp_path, direction)
    manifest = None
    calls = []
    prior_ledger = None
    original_n1 = scenario.consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1
    root = tmp_path / "session"

    def in_session(pairs, **kwargs):
        nonlocal manifest, prior_ledger
        kwargs.pop("position_episode_bindings")
        kwargs.pop("position_episode_scope")
        kwargs["origin_main_sha"] = "b" * 40
        if manifest is None:
            manifest = _manifest(
                context,
                Path(context.entry_source_ref.split(":", 2)[2]),
                Path(pairs["LANE_1"][0].lane_state_root),
                pairs["LANE_1"][1],
                2,
            )
            manifest = replace(manifest, host_completion_required=True)
        with _session(manifest, root, "recover" if calls else "create") as opened:
            before = len(calls)
            result = opened.run_occupied_cycle_v1(pairs, **kwargs)
            assert opened.state["attempts_used"] == before + 1
            assert opened.state["status"] == "READY"
            assert opened.last_completion_result.productive_runtime_cardinality == "1_JOINED"
            with pytest.raises(ValueError, match="EXHAUSTED|PREFIX_INVALID"):
                opened.run_occupied_cycle_v1(pairs, **kwargs)
            return result

    def actual(pairs, **kwargs):
        nonlocal prior_ledger
        attempt = kwargs["offline_governed_attempt"]
        for changed, reason in [
            ({"cycle_id_prefix": "foreign"}, "PREFIX_MISMATCH"),
            ({"observed_unix": kwargs["observed_unix"] + 1}, "CHARGED_RECEIPT_REQUIRED"),
            (
                {"offline_governed_attempt": replace(attempt, charged_receipt_digest="0" * 64)},
                "CHARGED_RECEIPT_REQUIRED",
            ),
            (
                {
                    "position_episode_scope": replace(
                        kwargs["position_episode_scope"], account_identity="foreign"
                    )
                },
                "MANIFEST_MISMATCH",
            ),
        ]:
            with pytest.raises(ValueError, match=reason):
                original_n1(pairs, **{**kwargs, **changed})
        result = original_n1(pairs, **kwargs)
        row = result["LANE_1"]
        ledger = Path(row.evidence_root) / "governed_cycle_orchestrator_ledger_v1.json"
        assert ledger.is_file()
        if prior_ledger:
            assert prior_ledger[0].read_bytes() == prior_ledger[1]
        prior_ledger = (ledger, ledger.read_bytes())
        with pytest.raises(
            CurrentProductiveGovernedCycleOrchestratorError, match="CYCLE_AUTHORIZATION_REPLAY"
        ):
            original_n1(pairs, **kwargs)
        calls.append(row)
        return result

    original_consumer = scenario.consumer

    class ConsumerProxy:
        def __getattr__(self, name):
            return getattr(original_consumer, name)

        invoke_occupied_lane_governed_cycle_n1_consumer_v1 = staticmethod(in_session)

    monkeypatch.setattr(scenario, "consumer", ConsumerProxy())
    monkeypatch.setattr(sessions, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", actual)
    first = invoke(recover(), 64, 1000.0 + direction * (20 + 1.2 * 62))
    obligation = recover().binding.pending_exit_identity
    second = invoke(recover(), 65, 1000.0 + direction * (20 + 1.2 * 62))
    assert len(calls) == 2
    assert first.cursor_store_root == second.cursor_store_root
    assert first.lock_root == second.lock_root
    assert first.evidence_root != second.evidence_root
    assert recover().binding.pending_exit_identity == obligation
    assert str(accounting.position.qty) == "0.4"
    for row in calls:
        envelope = row.governed_cycle_result.final_order_envelope
        assert envelope.quantity == "0.4" and envelope.reduce_only
        assert (
            not row.governed_cycle_result.permit_created
            and row.governed_cycle_result.post_count == 0
        )
    with _session(manifest, root, "recover") as opened:
        assert opened.state["attempts_used"] == 2
        with pytest.raises(ValueError, match="ATTEMPTS_EXHAUSTED"):
            opened.run_occupied_cycle_v1({})
    receipt = json.loads((root / sessions.RECEIPT).read_text())
    assert len(receipt["cycle_namespaces"]) == 2
