"""Original N1 → quantity → reservation → late consumer, synthetic sources only."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.constants_v1 import MARK_ENDPOINT_PATH, MARK_SOURCE_CLASS
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInstrumentRawInputV1,
    FinalizedPt1mMarkObservationV1,
    UnresolvedValidityDimensionsV1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import absolute_movement_cost_v1 as movement
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    parse_slot_entry_budget_v1,
)
from tests.ops import _opening_execution_cost_fixture_v1 as fixture
from tests.ops import test_native_cost_cover_v1 as cover
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    # Explicit USDT compatibility fixture; the user's current file requires
    # USDC. Actual X-Perp settlement admission is tested separately.
    current = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V11.json"
    )
    return replace(
        current,
        policy_id="offline-usdt-movement-compatibility-fixture",
        require_usdc_settlement=False,
    )


def raw_input(kwargs, *, magnitude="0.04", fault=None):
    bound, epoch = kwargs["bound_instrument"], kwargs["decision_epoch"]
    current_ms = int(datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp() * 1000)
    end = current_ms // 60_000 * 60_000 - 60_000
    reference = Decimal(str(kwargs["replay"].intermediate.market_context.mark_price))
    marks = tuple(
        FinalizedPt1mMarkObservationV1(
            mark_px=str(reference * (1 + Decimal(magnitude) * (i % 2))),
            event_timestamp=str(end - (60 - i) * 60_000),
            receive_or_capture_timestamp=epoch,
            finalization_status="FINALIZED",
            source_class=MARK_SOURCE_CLASS,
            source_endpoint=MARK_ENDPOINT_PATH,
        )
        for i in range(61)
    )
    canonical, native = bound.instrument_id, bound.venue_native_id
    if fault == "wrong-instrument":
        canonical = "foreign"
    elif fault == "wrong-native":
        native = "SOL-USDT-SWAP"
    elif fault == "gap":
        marks = (
            *marks[:30],
            replace(marks[30], event_timestamp=str(int(marks[30].event_timestamp) - 1)),
            *marks[31:],
        )
    elif fault == "unfinished":
        marks = (*marks[:-1], replace(marks[-1], finalization_status="IN_PROGRESS"))
    elif fault == "future-capture":
        marks = (
            *marks[:-1],
            replace(marks[-1], receive_or_capture_timestamp=str(current_ms + 1000)),
        )
    elif fault == "before-finality":
        marks = (
            *marks[:-1],
            replace(marks[-1], receive_or_capture_timestamp=marks[-1].event_timestamp),
        )
    elif fault in {"stale-window", "future-window"}:
        shift = -60_000 if fault == "stale-window" else 60_000
        marks = tuple(
            replace(row, event_timestamp=str(int(row.event_timestamp) + shift)) for row in marks
        )
    elif fault == "last-as-mark":
        marks = tuple(
            replace(row, source_class="TradeFactV1", source_endpoint="trades") for row in marks
        )
    elif fault == "nonfinite":
        marks = (*marks[:-1], replace(marks[-1], mark_px="NaN"))
    raw = EconomicMdInstrumentRawInputV1(
        canonical_instrument_id=canonical,
        venue_native_id=native,
        raw_input_eligible=True,
        exclusion_reason_codes=(),
        finalized_pt1m_marks=marks,
        ticker=None,
        unresolved_validity_dimensions=UnresolvedValidityDimensionsV1("", "", "", ""),
        raw_input_digest="",
        provenance={"fixture": "explicit-offline-only"},
    ).with_raw_input_digest()
    return replace(raw, raw_input_digest="0" * 64) if fault == "tampered-input" else raw


def setup(monkeypatch, *, magnitude="0.04", fault=None):
    monkeypatch.setattr(cover, "policy", policy)
    captures, clock = cover.setup(monkeypatch)
    original = fixture.attach_costs

    def observe(kwargs, **options):
        opening = original(kwargs, **options)
        observation = movement.AbsoluteMovementCostObservationV1.capture_v1(
            instrument_raw_input=raw_input(kwargs, magnitude=magnitude, fault=fault),
            opening_observation=opening,
            evaluated_at_utc=kwargs["decision_epoch"],
        )
        if fault == "wrong-cost-parent":
            observation = replace(observation, opening_observation_digest="0" * 64)
        if fault != "missing":
            kwargs["injected"] = replace(
                kwargs["injected"], absolute_movement_cost_observation=observation
            )
        return opening

    monkeypatch.setattr(fixture, "attach_costs", observe)
    return captures, clock


@pytest.mark.parametrize("short", [False, True])
def test_measured_volatility_and_amplitude_reach_original_quantity_and_hold(
    tmp_path, monkeypatch, short
):
    captures, _ = setup(monkeypatch)
    result = cover.native._run_layered_entry_supervisor_v1(tmp_path, short=short)
    kwargs, admitted, snapshot = captures[0]
    assert admitted.status == "PASS", admitted.reason_codes
    (serialized,) = snapshot["state"]["sizing_bindings"].values()
    binding = ReservationSizingBindingV1.from_dict_v1(serialized)
    binding.validate_v1(
        amount=binding.decision.canonical_position_sizing.resulting_notional,
        decision_id=binding.applied_input.decision_id,
    )
    receipt = json.loads(binding.absolute_movement_cost_binding.receipt_json)
    assert serialized["schema"] == "reservation_sizing_binding.v8"
    assert receipt["final_native_quantity"] == str(binding.decision.final_quantity)
    assert (
        Decimal(receipt["original_volatility"]) > 0
        and Decimal(receipt["original_relative_amplitude"]) > 0
    )
    assert receipt["side"] == ("SHORT" if short else "LONG")
    assert not receipt["expected_profit_forecast"] and not receipt["survival_ratio_mapping"]
    assert result.policy_result.orchestrator_result.post_count == 0
    assert kwargs["injected"].absolute_movement_cost_observation is not None


@pytest.mark.parametrize("magnitude", ["0", "0.0000001"])
def test_flat_or_weak_absolute_movement_denies_actual_n1_without_partial_hold(
    tmp_path, monkeypatch, magnitude
):
    captures, _ = setup(monkeypatch, magnitude=magnitude)
    cover.native._run_layered_entry_supervisor_v1(tmp_path, short=False)
    _kwargs, admitted, snapshot = captures[0]
    assert admitted.status != "PASS"
    assert "MOVEMENT_OBSERVED_AMPLITUDE_DOES_NOT_EXCEED_ROUNDTRIP_COSTS" in admitted.reason_codes
    assert snapshot["state"]["reservations"] == []


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "wrong-instrument",
        "wrong-native",
        "gap",
        "unfinished",
        "future-capture",
        "before-finality",
        "stale-window",
        "future-window",
        "last-as-mark",
        "nonfinite",
        "tampered-input",
        "wrong-cost-parent",
    ],
)
def test_unbound_or_invalid_market_source_rejects_real_financial_consumer(
    tmp_path, monkeypatch, fault
):
    captures, _ = setup(monkeypatch, fault=fault)
    cover.native._run_layered_entry_supervisor_v1(tmp_path, short=False)
    _kwargs, admitted, snapshot = captures[0]
    assert admitted.status != "PASS", fault
    assert any("MOVEMENT" in code for code in admitted.reason_codes), admitted.reason_codes
    assert snapshot["state"]["reservations"] == []


def test_retained_receipt_is_rebuilt_and_old_observation_cannot_authorize_late_entry(
    tmp_path, monkeypatch
):
    captures, clock = setup(monkeypatch)
    cover.native._run_layered_entry_supervisor_v1(tmp_path, short=False)
    kwargs, result, _ = captures[0]
    assert result.status == "PASS", result.reason_codes
    owner = kwargs["portfolio_budget_owner"]
    (binding,) = owner._sizing_bindings.values()
    retained = binding.absolute_movement_cost_binding
    receipt = json.loads(retained.receipt_json)
    receipt["original_relative_amplitude"] = "999"
    with pytest.raises(ValueError, match="MOVEMENT_RETAINED_RECEIPT_MISMATCH"):
        replace(retained, receipt_json=cost.canonical(receipt)).validate_v1(sizing=binding)
    later = datetime.fromisoformat(clock[0].replace("Z", "+00:00")).timestamp() + 6
    with pytest.raises(ValueError):
        retained.validate_v1(
            sizing=binding, evaluated_at_utc=datetime.fromtimestamp(later, timezone.utc).isoformat()
        )
    assert all(row.counts_against_budget for row in owner._by_key.values())


def test_new_policy_requires_this_admission_and_preserves_prior_schema():
    raw = policy().to_dict_v1()
    for value in (False, None, "true"):
        with pytest.raises(ValueError):
            parse_slot_entry_budget_v1({**raw, "require_absolute_movement_cost_cover": value})
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V10.json"
    )
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v11"
    assert "require_absolute_movement_cost_cover" not in old.to_dict_v1()
