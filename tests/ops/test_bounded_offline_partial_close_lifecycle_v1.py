"""Two original N1 closes with a partial simulated fill and retained obligation."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import os

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.profile_v1 import open_e1_offline_session_v1
from src.ops.bounded_peaktrade_system_composition_v1.readiness_v1 import (
    OfflineProcessObservationV1,
    run_readiness_checked_offline_cycle_v1,
)
from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import purpose_profile_digest_v1
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    _load_source,
    bind_simulated_accounting_episode_identity_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
    create_successor_after_sealed_simulated_episode_v1,
)
from tests.ops import test_adverse_time_exit_consumer_semantics_v1 as scenario
from tests.ops.test_bounded_offline_episode_session_v1 import _manifest
from tests.ops.test_bounded_offline_all_purpose_consumers_v1 import _profiles
from tests.ops.test_simulated_accounting_entry_source_v1 import _args
from tests.ops.test_simulated_accounting_episode_close_v1 import _observation
from tests.ops.test_position_episode_exit_continuity_v1 import _natural_entry
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)


@pytest.mark.parametrize("direction", [1, -1])
def test_partial_fill_reopen_remaining_close_flat_and_successor_keep_original_owners(
    tmp_path, monkeypatch, direction
):
    old_args = scenario._args
    monkeypatch.setattr(scenario, "_args", lambda *a: {**old_args(*a), "repository_sha": "a" * 40})
    context, accounting, recover, invoke = scenario._scenario(tmp_path, direction)
    source = Path(context.entry_source_ref.split(":", 2)[2])
    _, _, payload = _load_source(source, context.identity, include_payload=True)
    from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
        SimulatedFillInputV1,
    )

    numeric = {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
    fills = [
        SimulatedFillInputV1(**{k: Decimal(v) if k in numeric else v for k, v in row.items()})
        for row in payload["fills"]
    ]
    old_obligation = context.binding.pending_exit_identity
    observed = []

    def consume(pairs, **kwargs):
        kwargs.pop("position_episode_bindings")
        kwargs.pop("position_episode_scope")
        native = context.identity.venue_native_id
        now = int(kwargs["observed_unix"] * 1000)
        profiles = _profiles(
            tmp_path / "facts",
            canonical=context.identity.instrument_id,
            native=native,
            now_ms=now,
            last_ms=now // 60000 * 60000,
            direction=direction,
        )
        manifest = replace(
            _manifest(
                context, source, Path(pairs["LANE_1"][0].lane_state_root), pairs["LANE_1"][1]
            ),
            data_profile_digest=purpose_profile_digest_v1(profiles),
            host_completion_required=True,
        )
        kwargs.update(origin_main_sha="b" * 40, candles_payload=None)
        root = tmp_path / "session"
        original_ledger = None
        for n, quantity in enumerate((Decimal("0.1"), Decimal("0.3"))):
            if n:
                kwargs = {**kwargs, "occupancy_payloads": deepcopy(kwargs["occupancy_payloads"])}
                kwargs.update(
                    observed_unix=kwargs["observed_unix"] + 120,
                    cycle_id_prefix="after-partial-fill",
                )
                kwargs["occupancy_payloads"]["POSITIONS"]["data"][0]["pos"] = "0.3"
                paths = default_store_paths_v1(tmp_path / "facts")
                last = max(
                    (
                        f
                        for f in load_all_facts_v1(paths)
                        if f["fact_kind"] == "OhlcvIntervalFactV1"
                    ),
                    key=lambda f: f["interval_start_ms"],
                )
                for step in (1, 2):
                    row = deepcopy(last)
                    row["interval_start_ms"] += step * 60000
                    row["timestamps"].update(
                        venue_event_time_ms=row["interval_start_ms"],
                        captured_at=datetime.fromtimestamp(
                            kwargs["observed_unix"], timezone.utc
                        ).isoformat(),
                    )
                    append_fact_v1(paths, row)
            with open_e1_offline_session_v1(
                manifest=manifest,
                state_root=root,
                mode="create" if n == 0 else "recover",
                data_sources=profiles,
            ) as opened:
                if n:
                    assert (
                        opened._episodes["LANE_1"].binding.pending_exit_identity == old_obligation
                    )
                    assert accounting.position.qty == Decimal("0.3")
                process = OfflineProcessObservationV1(
                    manifest.session_id, manifest.digest(), os.getpid(), 1000.0, True
                )
                results = run_readiness_checked_offline_cycle_v1(
                    opened,
                    pairs,
                    process=process,
                    now_unix=1000.0,
                    maximum_heartbeat_age_seconds=5,
                    **kwargs,
                )
                result = results["LANE_1"]
                envelope = result.governed_cycle_result.final_order_envelope
                assert Decimal(envelope.quantity) == (Decimal("0.4") if n == 0 else Decimal("0.3"))
                assert envelope.reduce_only and result.governed_cycle_result.post_count == 0
                ledger = Path(result.evidence_root) / "governed_cycle_orchestrator_ledger_v1.json"
                if n == 0:
                    original_ledger = (ledger, ledger.read_bytes())
                else:
                    assert original_ledger[0].read_bytes() == original_ledger[1]
                event = kwargs["observed_unix"] + 1
                fill = build_simulated_fill_v1(
                    fill_id="offline-envelope-fragment:" + envelope.envelope_id,
                    instrument_id=native,
                    side=envelope.side.upper(),
                    quantity=quantity,
                    mark_price=str(kwargs["mark_px"]),
                    contract=accounting.contract,
                    reduce_only=True,
                    event_time_unix=event,
                )
                assert quantity <= Decimal(envelope.quantity)
                accounting.apply_fill(fill)
                fills.append(fill)
                if n == 0:
                    opened.advance_accounting_episode_v1(
                        lane_id="LANE_1", accounting_session=accounting, fills=tuple(fills)
                    )
                    assert (
                        opened._episodes["LANE_1"].binding.pending_exit_identity == old_obligation
                    )
                    assert opened.state["attempts_used"] == 1
                else:
                    observation = _observation(context.identity)
                    observation["observed_portfolio"] = replace(
                        observation["observed_portfolio"],
                        event_time_unix=event + 1,
                        wall_time_unix=event + 1,
                    )
                    observation["observed_unix"] = event + 2
                    sealed = opened.seal_flat_episode_v1(
                        pairs, accounting_session=accounting, fills=tuple(fills), **observation
                    )
                    assert opened.state["status"] == "SEALED" and opened.state["attempts_used"] == 2
                    observed.append(sealed)
        assert accounting.position is None
        with open_e1_offline_session_v1(
            manifest=manifest, state_root=root, mode="recover", data_sources=profiles
        ) as sealed_session:
            assert sealed_session.state["status"] == "SEALED"
        # A later separately observed fill starts a new episode; it is not an
        # Entry decision or a capital/slot release inferred from local flat.
        new_fill = build_simulated_fill_v1(
            fill_id="separately-observed-successor-fill",
            instrument_id=native,
            side="BUY" if direction == 1 else "SELL",
            quantity="0.1",
            mark_price=str(kwargs["mark_px"]),
            contract=accounting.contract,
            reduce_only=False,
            event_time_unix=event + 60,
        )
        accounting.apply_fill(new_fill)
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=context.identity, opening_fill=new_fill
        )
        args = _args(tmp_path / "successor", identity)
        args["repository_sha"] = "a" * 40
        successor = create_successor_after_sealed_simulated_episode_v1(
            prior_identity=context.identity,
            prior_state_root=Path(context.binding.state_root),
            prior_repository_sha=context.binding.repository_sha,
            prior_config_digest=context.binding.config_digest,
            prior_initial_source_ref=context.entry_source_ref,
            accounting_session=accounting,
            fills=(*fills, new_fill),
            **args,
        )
        assert successor.identity.episode_id != context.identity.episode_id
        assert not successor.binding.pending_exit_identity
        cursor_root = tmp_path / "successor" / "cursor"
        cursor = _natural_entry(cursor_root, direction, event_time_base=event + 60)
        persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=cursor_root)
        assert cursor_root != Path(pairs["LANE_1"][0].lane_state_root)
        return results

    original = scenario.consumer

    class Proxy:
        def __getattr__(self, name):
            return getattr(original, name)

        invoke_occupied_lane_governed_cycle_n1_consumer_v1 = staticmethod(consume)

    monkeypatch.setattr(scenario, "consumer", Proxy())
    invoke(recover(), 65, 1000 + direction * 94.4)
    assert len(observed) == 1


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("wrong_quantity", ["0.3", "0.8"])
def test_original_initial_source_quantity_rejects_before_governed_authorization(
    tmp_path, monkeypatch, direction, wrong_quantity
):
    context, accounting, recover, invoke = scenario._scenario(tmp_path, direction)
    original = scenario.consumer
    calls = []

    def consume(pairs, **kwargs):
        before = context.binding.to_canonical_state().digest()
        altered = {**kwargs, "occupancy_payloads": deepcopy(kwargs["occupancy_payloads"])}
        altered["occupancy_payloads"]["POSITIONS"]["data"][0]["pos"] = wrong_quantity
        with pytest.raises(ValueError, match="INITIAL_POSITION_QUANTITY_MISMATCH"):
            original.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **altered)
        assert context.binding.to_canonical_state().digest() == before
        assert not list(tmp_path.rglob("governed_cycle_orchestrator_ledger_v1.json"))
        calls.append(True)
        return original.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)

    class Proxy:
        def __getattr__(self, name):
            return getattr(original, name)

        invoke_occupied_lane_governed_cycle_n1_consumer_v1 = staticmethod(consume)

    monkeypatch.setattr(scenario, "consumer", Proxy())
    result = invoke(recover(), 65, 1000 + direction * 94.4)
    assert len(calls) == 1 and Decimal(
        result.governed_cycle_result.final_order_envelope.quantity
    ) == Decimal("0.4")
