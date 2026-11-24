"""Acquire exact decision-bound Demo originals after the original L10 seal.

No sizing, reservation, permit or order. Existing cost and quantity owners
consume these sources. Actual receipt clocks and original bodies are retained.
"""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.native_initial_margin_v1 import (
    NativeInitialMarginObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    AbsoluteMovementCostObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
    capture_n1_venue_quantity_limits_v1,
)


@dataclass(frozen=True)
class BtcDemoNetReversalPretradeV1:
    reads: object
    bound: object
    account: str
    clock: object
    movement_input: object

    def acquire_for_reversal_v1(self, *, decision_epoch, cycle_id, account, bound):
        if account != self.account or bound != self.bound or bound.venue_native_id != demo._NATIVE:
            raise ValueError("TESTNET_REVERSAL_PRETRADE_SCOPE_MISMATCH")
        originals = {}
        rows = demo.read_btc_demo_pretrade_sources_v1(
            reads=self.reads,
            expected_uid=account,
            decision_epoch=decision_epoch,
            cycle_id=cycle_id,
            clock=self.clock,
            original_response_sink=lambda k, b: originals.__setitem__(k, b.hex()),
        )
        context = cost.canonical(dict(decision_epoch=decision_epoch, cycle_id=cycle_id))
        for key, path, query, private in (
            (
                "quantity_public",
                "/api/v5/public/instruments",
                dict(instType="FUTURES", instId=demo._NATIVE),
                False,
            ),
            (
                "quantity_private",
                "/api/v5/account/max-size",
                dict(instId=demo._NATIVE, tdMode="cross"),
                True,
            ),
        ):
            payload, acquired, body = self.reads.read_original_v1(path, **query)
            originals[key] = body.hex()
            rows[key] = cost.FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=path + "?" + demo.urlencode(query),
                http_status=200,
                payload=payload,
                auth_header_sent=private,
                transport_class="OKX_EEA_DEMO_READ_ONLY_GET",
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                body_sha256=sha256(body).hexdigest(),
                pretrade_decision_id=context,
                acquired_at_utc=acquired.isoformat(),
            )
        now = datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()
        for source in rows.values():
            cost.acquisition_age_seconds_v1(
                acquired_at_utc=decision_epoch, now_utc=source.acquired_at_utc
            )
            cost.acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now)
        base = dict(
            bound_instrument=bound,
            decision_epoch=decision_epoch,
            cycle_id=cycle_id,
            evaluated_at_utc=now,
        )
        opening = cost.EntryExecutionCostObservationV1.capture_v1(
            **base,
            account_identity=account,
            sources={k: rows[k] for k in ("account", "instruments", "fees", "book")},
        )
        native = NativeInitialMarginObservationV1.capture_v1(
            sources={k: rows[k] for k in ("balance", "leverage")},
            opening_observation=opening,
            evaluated_at_utc=now,
        )
        funding = cost.FundingCostObservationV1.capture_v1(**base, source=rows["funding"])
        movement = AbsoluteMovementCostObservationV1.capture_v1(
            instrument_raw_input=self.movement_input,
            opening_observation=opening,
            evaluated_at_utc=now,
        )
        limits = capture_n1_venue_quantity_limits_v1(
            results=dict(instruments=rows["quantity_public"], max_size=rows["quantity_private"]),
            acquisition_decision_id=context,
            account_identity=account,
            bound_instrument=bound,
            decision_epoch=decision_epoch,
            cycle_id=cycle_id,
            execution_environment="TESTNET",
        )
        return CurrentProductiveEnterLive29PInjectedGetV1(
            payload=rows["balance"].payload,
            get_performed=True,
            http_status=200,
            body_sha256=rows["balance"].body_sha256,
            observed_at=now,
            raw_acct_lv=demo._only(rows["account"].payload)["acctLv"],
            expected_account_identity=account,
            fresh_pretrade_get_status="TRUSTED_PRESENT",
            instruments_payload=rows["instruments"].payload,
            acquisition_decision_id=context,
            acquisition_cycle_id=cycle_id,
            opening_cost_observation=opening,
            funding_cost_observation=funding,
            native_initial_margin_observation=native,
            absolute_movement_cost_observation=movement,
            venue_quantity_limits=limits,
            testnet_original_sources_json=cost.canonical({k: asdict(v) for k, v in rows.items()}),
            testnet_original_bodies_json=cost.canonical(originals),
        )
