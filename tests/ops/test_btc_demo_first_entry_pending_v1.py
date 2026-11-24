"""Original signed Demo account inventory at the first-entry pending boundary."""

from dataclasses import replace
import json
import pytest
from tests.ops.test_btc_demo_entry_submit_v1 import entry_send as entry_send
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
    capture_current_post_pending_v1,
    inspect_current_post_pending_v1,
    CurrentPostPendingObservationError,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    futures_financial_pending_gets_v1,
)
from tests.ops.test_btc_testnet_original_execution_receipt_v1 import (
    original_testnet_entry as original_testnet_entry,
    demo_entry as demo_entry,
)
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def context(world):
    source = world["context"].account_inventory_source
    envelope = FinalOrderEnvelopeV1(
        **world["host"].owner.execution_links_v1()[world["rid"]]["envelope"]
    )
    return capture_current_post_pending_v1(
        envelope=envelope, source=source, execution_environment="TESTNET"
    )


def test_original_demo_inventory_reaches_explicit_pending_boundary(original_testnet_entry):
    world = original_testnet_entry
    pending = context(world)
    count = pending.source.transport.read_count
    proof = inspect_current_post_pending_v1(
        pending,
        envelope=pending.envelope,
        stage="OFFLINE_DEMO_FIRST_ENTRY",
        expected_account=world["host"].account,
        execution_environment="TESTNET",
    )
    assert proof["scope"] == "ORIGINAL_ACCOUNT_WIDE_FUTURES_ORDINARY_ALGO_AND_BOT_CUSTODY"
    assert proof["endpoints"] == ["/api/v5/account/config", *futures_financial_pending_gets_v1()]
    assert pending.source.transport.read_count == count
    with pytest.raises(CurrentPostPendingObservationError, match="ENVIRONMENT_MISMATCH"):
        inspect_current_post_pending_v1(pending, envelope=pending.envelope, stage="LIVE_DEFAULT")


@pytest.mark.parametrize(
    "fault", ["missing-bot", "nonempty-bot", "missing-algo", "stale", "copy", "product", "account"]
)
def test_incomplete_or_changed_original_demo_inventory_denies_entry(
    original_testnet_entry, monkeypatch, fault
):
    pending = context(original_testnet_entry)
    source = pending.source
    if fault in {"missing-bot", "nonempty-bot", "missing-algo"}:
        gets = json.loads(pending.observation.gets_json)
        key = next(
            k
            for k in gets
            if ("tradingBot" in k if "bot" in fault else "/trade/orders-algo-pending" in k)
        )
        if fault == "nonempty-bot":
            gets[key]["payload"]["data"] = [{"algoId": "unresolved"}]
        else:
            del gets[key]
        damaged = replace(pending.observation, gets_json=json.dumps(gets))
        monkeypatch.setattr(source, "_pending_observation", damaged)
        pending = replace(pending, observation=damaged)
    elif fault == "stale":
        monkeypatch.setattr(source, "clock", lambda: original_testnet_entry["now"].timestamp() + 6)
    elif fault == "copy":
        pending = replace(pending, observation=replace(pending.observation))
    elif fault == "product":
        monkeypatch.setattr(source, "inventory_inst_type", "SWAP")
    elif fault == "account":
        monkeypatch.setattr(source, "expected_account_identity", "different-account")
    count = source.transport.read_count
    with pytest.raises(CurrentPostPendingObservationError):
        inspect_current_post_pending_v1(
            pending,
            envelope=pending.envelope,
            stage="OFFLINE_DENY",
            execution_environment="TESTNET",
        )
    assert source.transport.read_count == count
