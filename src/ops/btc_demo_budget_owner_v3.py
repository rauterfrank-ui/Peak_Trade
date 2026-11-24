"""Slot 3 TESTNET specialization over the original SQLite writer and recovery.

The shared store keeps its storage format. The owner envelope carries the
TESTNET contract and environment. A generic owner rejects that envelope.
"""

from copy import deepcopy
import json
from pathlib import Path
from threading import RLock

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    observation_identity_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    ADMISSION_CONTEXT_TESTNET,
    EVIDENCE_CLASS_TESTNET_TYPED,
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_SOURCE_OBSERVED_VENUE,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    PRODUCER_IDENTITY,
    bind_step_29p_typed_equity_from_risk_capital_v1,
)

CONTRACT = "btc_demo_budget_owner.v3"


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


class BtcDemoBudgetOwnerV3(PortfolioCapitalReservationBudgetOwnerV1):
    def __init__(
        self,
        *,
        durable_root,
        durable_account_identity,
        durable_mode,
        durable_lane_bindings,
        entry_budget_policy=None,
        slot_capital_allocation=None,
    ):
        root = Path(durable_root)
        _need(root.is_absolute() and len(root.parents) >= 3, "BTC_DEMO_V3_OWNER_SCOPE_REQUIRED")
        lane = demo._demo_lane_root(root.parents[2])
        _need(
            root.resolve() == root
            and root == lane.parent / "budget-owner" / "owner"
            and set(durable_lane_bindings) == {demo._LANE}
            and durable_lane_bindings[demo._LANE].venue_native_id == demo._NATIVE,
            "BTC_DEMO_V3_OWNER_SCOPE_REQUIRED",
        )
        self._bounded_demo_session_control = None
        super().__init__(
            durable_root=root,
            durable_account_identity=durable_account_identity,
            durable_mode=durable_mode,
            durable_lane_bindings=durable_lane_bindings,
            entry_budget_policy=entry_budget_policy,
            slot_capital_allocation=slot_capital_allocation,
            execution_environment="TESTNET",
        )
        self._lock = RLock()

    def execution_environment_v1(self):
        return "TESTNET"

    def _durable_payload_locked(self):
        body = {
            **super()._durable_payload_locked(),
            "testnet_owner_contract": CONTRACT,
            "execution_environment": "TESTNET",
        }
        if self._bounded_demo_session_control is not None:
            body["bounded_demo_session_control"] = deepcopy(self._bounded_demo_session_control)
        return body

    def _restore_locked(self, payload):
        _need(
            payload.get("testnet_owner_contract") == CONTRACT
            and payload.get("execution_environment") == "TESTNET",
            "BTC_DEMO_V3_JOURNAL_ENVIRONMENT_REQUIRED",
        )
        body = deepcopy(payload)
        del body["testnet_owner_contract"]
        session = body.pop("bounded_demo_session_control", None)
        super()._restore_locked(body)
        from src.ops.btc_demo_session_control_v1 import validate_session_control_v1

        validate_session_control_v1(self, session)
        self._bounded_demo_session_control = deepcopy(session)

    def register_bounded_demo_session_v1(self, registration, *, expected_head, now_utc):
        from src.ops.btc_demo_session_control_v1 import register_session_locked_v1

        with self._lock:
            return register_session_locked_v1(
                self, registration, expected_head=expected_head, now_utc=now_utc
            )

    def require_bounded_demo_risk_window_v1(self):
        from src.ops.btc_demo_session_control_v1 import require_risk_window_v1
        from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
            utc_now_iso_v1,
        )

        with self._lock:
            return require_risk_window_v1(self, now_utc=utc_now_iso_v1())

    def bounded_demo_session_result_v1(self):
        """Read the original once-funded session's confirmed settlement only."""
        from decimal import Decimal, localcontext
        from src.ops.btc_demo_session_control_v1 import validate_session_control_v1

        with self._lock:
            if self._store is None or self._closed_owner or self._storage_failed:
                raise ValueError("BTC_DEMO_SESSION_RESULT_WRITER_UNAVAILABLE")
            registration = validate_session_control_v1(self, self._bounded_demo_session_control)
            if registration is None or self._bounded_demo_session_control["phase"] != "CLOSED":
                raise ValueError("BTC_DEMO_CONFIRMED_SESSION_CLOSE_REQUIRED")
            receipt = self._bounded_demo_session_control["close_receipt"]
            reversals = self._live_net_reversal_bookings.get(receipt["reservation_id"], ())
            allocation = self._slot_capital_allocation
            if (
                allocation is None
                or allocation["schema"] != "slot_capital_allocation.v1"
                or allocation["funding"] is None
            ):
                raise ValueError("BTC_DEMO_ORIGINAL_TESTNET_FUNDING_REQUIRED")
            initial = Decimal(allocation["declaration"]["initial_usdc_by_slot"]["LANE_3"])
            with localcontext() as ctx:
                ctx.prec = 96
                net = sum(
                    (Decimal(row["net_result_usdc"]) for row in reversals),
                    Decimal(receipt["net_result_usdc"]),
                )
                return dict(
                    session_id=registration.session_id,
                    registration_digest=registration.digest_v1(),
                    settlement_currency="USDC",
                    initial_usdc=str(initial),
                    booked_net_usdc=str(net),
                    final_session_basis_usdc=str(initial + net),
                    reversal_count=len(reversals),
                    close_receipt_digest=digest(receipt),
                    hold_released=True,
                    account_balance_or_return_claim=False,
                )

    def inspect_current_entry_budget_policy_v1(self, *args, **kwargs):
        self.require_bounded_demo_risk_window_v1()
        return super().inspect_current_entry_budget_policy_v1(*args, **kwargs)

    def try_reserve_v1(self, **kwargs):
        return self._closed(("BTC_DEMO_V3_ORIGINAL_ENTRY_SOURCES_REQUIRED",))

    def reserve_demo_entry_v3(
        self,
        *,
        output,
        observation,
        slot_id,
        decision_id,
        cycle_id,
        account_identity,
        sizing_input,
        monetary_source,
        opening_cost_observation,
        funding_cost_observation,
        native_initial_margin_observation,
        absolute_movement_cost_observation,
        expected_durable_head,
        local_generation,
        source_checksum,
        evaluated_at_utc,
    ):
        from src.ops.btc_demo_testnet_entry_reservation_v1 import (
            reserve_btc_demo_costed_hold_locked_v1,
        )

        with self._lock:
            self.require_bounded_demo_risk_window_v1()
            _need(self._store.head == expected_durable_head, "RESERVATION_DURABLE_HEAD_CHANGED")
            _need(
                self._admitted
                and not self._by_key
                and not self._recovery_required
                and not self._storage_failed
                and not self._closed_owner,
                "BTC_DEMO_V3_FRESH_FIRST_ENTRY_REQUIRED",
            )
            _need(
                account_identity == self._account_identity
                and slot_id == demo._LANE
                and observation_identity_v1(output) == self._observation_id,
                "BTC_DEMO_V3_OBSERVATION_SCOPE_MISMATCH",
            )
            lane = demo._demo_lane_root(self._store.root.parents[2])
            _need(
                isinstance(source_checksum, str)
                and len(source_checksum) == 64
                and all(c in "0123456789abcdef" for c in source_checksum),
                "BTC_DEMO_V3_SOURCE_DIGEST_REQUIRED",
            )
            packet_path = lane / "entry-reservation-sources" / (source_checksum + ".json")
            _need(packet_path.resolve() == packet_path, "BTC_DEMO_V3_SOURCE_PATH_INVALID")
            packet = json.loads(packet_path.read_bytes())
            _need(
                digest(packet) == source_checksum
                and packet["schema"] == "btc_demo_entry_sources.v1"
                and packet["execution_environment"] == "TESTNET"
                and packet["account_identity"] == account_identity
                and packet["decision_id"] == decision_id == sizing_input.decision_id
                and packet["cycle_id"] == cycle_id
                and packet["bound"] == self._lane_bindings[slot_id]["bound"]
                and packet["policy_digest"] == self._entry_budget_policy.digest_v1()
                and sizing_input.config_digest == source_checksum
                and packet["sources"]["funding"] == json.loads(funding_cost_observation.source_json)
                and {key: packet["sources"][key] for key in ("balance", "leverage")}
                == json.loads(native_initial_margin_observation.sources_json)
                and {
                    key: packet["sources"][key]
                    for key in ("account", "instruments", "fees", "book")
                }
                == json.loads(opening_cost_observation.sources_json),
                "BTC_DEMO_V3_JOURNAL_SOURCE_MISMATCH",
            )
            parent_sequence, parent_head = packet["budget_parent_revision"]
            _need(
                self._store.sequence == parent_sequence + 1
                and self._store.read_revision_v1(self._store.sequence)["previous"] == parent_head
                and packet["decision_epoch"] == output.decision_epoch
                and packet["native_price_currency"] == "USD"
                and packet["capital_risk_mode"] == "TESTNET_ACCOUNT_BOUND",
                "BTC_DEMO_V3_SOURCE_RECOVERY_LINEAGE_MISMATCH",
            )
            claim = CapitalAdmissionClaimV1(
                source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
                account_identity=account_identity,
                instrument_id=sizing_input.instrument_id,
                observed_capital_raw=output.value,
                observed_field_name=PRODUCER_IDENTITY,
                evidence_class=EVIDENCE_CLASS_TESTNET_TYPED,
                execution_environment="TESTNET",
                evidence_id=source_checksum,
            )
            capital = evaluate_capital_admission_v1(
                claim=claim,
                expected_account_identity=account_identity,
                expected_instrument_id=sizing_input.instrument_id,
                admission_context=ADMISSION_CONTEXT_TESTNET,
            )
            risk_claim = bind_step_29p_typed_equity_from_risk_capital_v1(
                output=output,
                fresh_pretrade_get_status="TRUSTED_PRESENT",
                live_account_bound_status="TRUSTED_PRESENT",
                expected_instrument_id=sizing_input.instrument_id,
                observed_instrument_id=sizing_input.instrument_id,
                fresh_evidence_fetched=True,
                fresh_evidence_validated=True,
            )
            admissibility = evaluate_step_29p_capital_risk_admissibility_v1(
                capital=capital,
                claim=risk_claim,
            )
            _need(admissibility.risk_admissible is True, "BTC_DEMO_V3_CAPITAL_NOT_ADMITTED")
            return reserve_btc_demo_costed_hold_locked_v1(
                self,
                output=output,
                observation=observation,
                slot_id=slot_id,
                decision_id=decision_id,
                cycle_id=cycle_id,
                account_identity=account_identity,
                sizing_input=sizing_input,
                local_generation=local_generation,
                monetary_source=monetary_source,
                opening_cost_observation=opening_cost_observation,
                funding_cost_observation=funding_cost_observation,
                native_initial_margin_observation=native_initial_margin_observation,
                absolute_movement_cost_observation=absolute_movement_cost_observation,
                evaluated_at_utc=evaluated_at_utc,
                reason_code="BTC_DEMO_TESTNET_RESERVED",
            )
