"""Read a sealed original simulated episode for a slot's test loss budget.

Accounting is replayed by its original owner. This adapter attributes and values
the result; it neither applies fills nor creates venue/capital authority.
"""

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

from .durable_store_v1 import digest
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
    inspect_sealed_simulated_episode_v1,
    _read_reference,
    SCHEMA as CLOSE_SCHEMA,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    economic_journal_events_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import SimulatedFillInputV1
from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
    conversion_pair_monetary_identity_from_okx_payload_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
    build_usdt_usdc_conversion_edge_from_index_tickers_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    USDT_USDC_PAIR_NATIVE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
)


@dataclass(frozen=True)
class SlotCloseAccountingSourceV1:
    identity_json: str
    state_root: str
    repository_sha: str
    config_digest: str
    initial_source_ref: str
    valuation_epoch: str
    index_tickers_json: str = "null"
    pair_instruments_json: str = "null"
    fx_acquired_at_utc: str = ""

    @classmethod
    def from_episode_v1(
        cls,
        episode,
        *,
        valuation_epoch,
        index_tickers_payload=None,
        pair_instruments_payload=None,
        fx_acquired_at_utc="",
    ):
        return cls(
            json.dumps(asdict(episode.identity), sort_keys=True, allow_nan=False),
            episode.binding.state_root,
            episode.binding.repository_sha,
            episode.binding.config_digest,
            episode.entry_source_ref,
            valuation_epoch,
            json.dumps(index_tickers_payload, sort_keys=True, allow_nan=False),
            json.dumps(pair_instruments_payload, sort_keys=True, allow_nan=False),
            fx_acquired_at_utc,
        )

    def identity_v1(self):
        if any(type(getattr(self, f.name)) is not str for f in fields(self)):
            raise ValueError("SLOT_ECONOMIC_SOURCE_STRING_FIELDS_REQUIRED")
        if not Path(self.state_root).is_absolute():
            raise ValueError("SLOT_ECONOMIC_SOURCE_ABSOLUTE_ROOT_REQUIRED")
        data = json.loads(self.identity_json)
        scope = PositionEpisodeScopeV1(**data.pop("account_scope"))
        identity = PositionEpisodeIdentityV1(**data, account_scope=scope)
        identity.validate_v1()
        return identity

    def to_dict_v1(self):
        return {"schema": "slot_close_accounting_source.v1", **asdict(self)}

    @classmethod
    def from_dict_v1(cls, value):
        if (
            not isinstance(value, dict)
            or value.get("schema") != "slot_close_accounting_source.v1"
            or set(value) != {"schema", *(f.name for f in fields(cls))}
        ):
            raise ValueError("SLOT_ECONOMIC_SOURCE_SCHEMA_INVALID")
        return cls(**{k: v for k, v in value.items() if k != "schema"})


def _fill(row):
    money = {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
    return SimulatedFillInputV1(**{k: Decimal(v) if k in money else v for k, v in row.items()})


def read_closed_slot_economics_v1(
    source,
    *,
    monetary_source,
    entry_envelope,
    close_envelope,
    slot_id,
    account_identity,
    canonical_id,
    native_id,
):
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        FinalOrderEnvelopeV1,
        assert_envelope_unmodified_v1,
    )

    for envelope in (entry_envelope, close_envelope):
        assert_envelope_unmodified_v1(FinalOrderEnvelopeV1(**envelope))
    if type(source) is not SlotCloseAccountingSourceV1:
        raise ValueError("SLOT_ECONOMIC_TYPED_SEALED_SOURCE_REQUIRED")
    identity = source.identity_v1()
    if (
        identity.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
        or (
            identity.lane_id,
            identity.account_scope.account_identity,
            identity.instrument_id,
            identity.venue_native_id,
        )
        != (slot_id, account_identity, canonical_id, native_id)
        or monetary_source.canonical_instrument_id != canonical_id
        or monetary_source.venue_native_id != native_id
    ):
        raise ValueError("SLOT_ECONOMIC_SOURCE_SCOPE_MISMATCH")
    sealed = inspect_sealed_simulated_episode_v1(
        identity=identity,
        state_root=source.state_root,
        repository_sha=source.repository_sha,
        config_digest=source.config_digest,
        expected_initial_source_ref=source.initial_source_ref,
    )
    valuation = datetime.fromisoformat(source.valuation_epoch.replace("Z", "+00:00"))
    closure_path, _ = _read_reference(sealed["closure_ref"], CLOSE_SCHEMA)
    known_at = json.loads(closure_path.read_text())["payload"]["observed_unix"]
    if (
        valuation.utcoffset() is None
        or valuation.timestamp() < sealed["close_event_time"]
        or valuation.timestamp() < known_at
    ):
        raise ValueError("SLOT_ECONOMIC_VALUATION_BEFORE_CLOSE")
    payload = sealed["source_payload"]
    frozen = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        payload["accounting_checkpoint"]
    )
    _ctx, money_identity, constraints = monetary_source.rebuild_v1()
    if (
        frozen.contract.quote_currency != money_identity.settle_currency
        or money_identity.quote_currency != money_identity.settle_currency
        or frozen.contract.contract_size != constraints.contract_multiplier
        or frozen.contract.tick_size != constraints.tick_size
        or frozen.contract.min_qty != constraints.minimum_quantity
    ):
        raise ValueError("SLOT_ECONOMIC_CONTRACT_MISMATCH")
    last = payload["fills"][-1]
    if (
        close_envelope["instrument_id"] != native_id
        or last["fill_id"] != "original-close:" + close_envelope["envelope_digest"]
        or last["side"].lower() != close_envelope["side"]
        or Decimal(last["quantity"]) != Decimal(close_envelope["quantity"])
        or last["reduce_only"] is not True
    ):
        raise ValueError("SLOT_ECONOMIC_ORIGINAL_CLOSE_FILL_REQUIRED")
    replay = ProductiveFuturesAccountingSessionV1(
        contract=frozen.contract,
        initial_equity=frozen.initial_equity,
        writer_identity=frozen.writer_identity,
    )
    opening = None
    initial = final = None
    maximum_open = Decimal(0)
    for event in economic_journal_events_v1(payload):
        if final is not None:
            raise ValueError("SLOT_ECONOMIC_EVENTS_AFTER_TARGET_CLOSE")
        if event["kind"] == "FUNDING":
            row = event["value"]
            replay.apply_funding_observation_v1(
                event_id=event["event_id"],
                amount=row["amount"],
                currency=row["currency"],
                instrument_id=row["instrument_id"],
                event_time_unix=row["event_time_unix"],
            )
            continue
        fill = _fill(event["value"])
        before = replay.portfolio_state().equity
        result = replay.apply_fill(fill)
        if result.action_code in {"LONG_OPEN", "SHORT_OPEN"}:
            if (
                bind_simulated_accounting_episode_identity_v1(identity=identity, opening_fill=fill)
                == identity
            ):
                opening, initial = fill, before
                allowed_ids = {
                    prefix + entry_envelope["envelope_digest"]
                    for prefix in ("original-plan:", "next-original-plan:", "offline-envelope:")
                }
                if fill.fill_id not in allowed_ids or fill.side.lower() != entry_envelope["side"]:
                    raise ValueError("SLOT_ECONOMIC_ORIGINAL_ENTRY_FILL_REQUIRED")
        if opening is not None:
            maximum_open = max(
                maximum_open, replay.position.qty if replay.position is not None else Decimal(0)
            )
            if result.action_code in {"LONG_CLOSE", "SHORT_CLOSE"}:
                final = replay.portfolio_state().equity
    if initial is None or final is None or maximum_open > Decimal(entry_envelope["quantity"]):
        raise ValueError("SLOT_ECONOMIC_EPISODE_OR_ENTRY_QUANTITY_MISMATCH")
    native_result = final - initial
    rate = Decimal(1)
    fx_digest = None
    if frozen.contract.quote_currency == "USDT":
        acquisition_age_seconds_v1(
            acquired_at_utc=source.fx_acquired_at_utc, now_utc=source.valuation_epoch
        )
        pair_base, pair_quote = conversion_pair_monetary_identity_from_okx_payload_v1(
            json.loads(source.pair_instruments_json),
            pair_native_id=USDT_USDC_PAIR_NATIVE_ID,
        )
        edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=json.loads(source.index_tickers_json),
            decision_epoch=source.valuation_epoch,
            observed_at=source.fx_acquired_at_utc,
            fresh_pretrade_get_status="TRUSTED_PRESENT",
            pair_base_currency=pair_base,
            pair_quote_currency=pair_quote,
        )
        event = datetime.fromtimestamp(int(edge.source_timestamp) / 1000, timezone.utc).isoformat()
        acquisition_age_seconds_v1(acquired_at_utc=event, now_utc=source.fx_acquired_at_utc)
        acquisition_age_seconds_v1(acquired_at_utc=event, now_utc=source.valuation_epoch)
        rate, fx_digest = edge.normalized_rate, edge.payload_digest
    elif frozen.contract.quote_currency != "USDC":
        raise ValueError("SLOT_ECONOMIC_CURRENCY_NOT_SUPPORTED")
    receipt = dict(
        schema="slot_closed_net_result_valuation.v1",
        episode_id=identity.episode_id,
        slot_id=slot_id,
        account_identity=account_identity,
        currency="USDC",
        native_currency=frozen.contract.quote_currency,
        native_net_result=str(native_result),
        net_result_usdc=str(native_result * rate),
        valuation_epoch=source.valuation_epoch,
        valuation_basis="NET_SETTLED_EPISODE_VALUED_AT_CLOSE_REVIEW_NOT_CASH_CONVERSION",
        fx_payload_digest=fx_digest,
        closure_ref=sealed["closure_ref"],
        source=source.to_dict_v1(),
        entry_envelope_digest=entry_envelope["envelope_digest"],
        close_envelope=close_envelope,
    )
    return {**receipt, "digest": digest(receipt)}
