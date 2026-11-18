"""Continue the occupied ZKP Paper slot on its original Master V2 state."""

from dataclasses import replace
from decimal import Decimal
import json
from math import isfinite
from pathlib import Path
from time import time

from src.execution.position_delta import signed_position_delta
from src.governance.capital_risk_sizing_v1 import evaluate_capital_risk_sizing_v1
from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import repository_source_digest_v1
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import (
    _BUDGET_POLICY,
    _MODE,
    _ZERO,
    paper_constraints_v1,
    paper_fill_fresh_v1,
    paper_sizing_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    PAPER_ALLOCATION_USDC,
    PAPER_FEE_RATE,
    ZKP_PAPER_SLOT,
    load_paper_liquidity_policy_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import OCCUPANCY_OCCUPIED
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    recover_current_cursor_publication_v1,
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    IDENTITY_FILENAME,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
    canonical_digest_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import _source
from src.ops.first_entry_mark_clock_v2 import ENTRY_MARK_STATE_DIRECTORY
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import _fill
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import SimulatedFillInputV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)


def _read(path):
    return json.loads(path.read_bytes())


def _is_l10_exit(frame, seal_id):
    entry = frame["entry"]
    return (
        frame["parent"]["decision_outcome"] == entry["decision_outcome"] == "exit"
        and entry["exit_class"] == "strategy_invalidation_exit"
        and "l10_scope_switch_exit:" + seal_id in entry["reason_codes"]
    )


def _scope_frame(cursor, mark):
    frame = read_current_core_entry_assessment_frame_v1(cursor)
    price_source = cursor.entry_assessment_frame["scope_price_source"]
    if json.loads(price_source["mark_clock_json"])["payload_sha256"] != mark["mark_payload_sha256"]:
        raise ValueError("ZKP_PAPER_ORIGINAL_SCOPE_CURSOR_MISMATCH")
    return frame


def apply_paper_funding_v1(terms, accounting, *, identity, binding_digest, settlement_time):
    """Validate and apply the original Paper Funding booking to the supplied owner."""
    position = accounting.position
    event = terms["event_time_unix"]
    following = terms["next_funding_unix"]
    observed = terms["observed_unix"]
    if (
        terms["episode_id"] != identity.episode_id
        or terms["binding_digest"] != binding_digest
        or terms["instrument_id"] != identity.venue_native_id
        or terms["currency"] != accounting.contract.quote_currency
        or event != settlement_time
        or not all(isfinite(value) for value in (event, following, observed))
        or not accounting.last_fill_time < event <= observed
        or following <= event
        or position is None
        or terms["position_side"] != position.side.value
        or Decimal(terms["position_contracts"]) != position.qty
        or Decimal(terms["contract_size"]) != accounting.contract.contract_size
    ):
        raise ValueError("ZKP_PAPER_FUNDING_BOOKING_BINDING_MISMATCH")
    mark = Decimal(terms["preceding_mark_close_usd"])
    rate = Decimal(terms["realized_rate"])
    if not mark.is_finite() or mark <= 0 or not rate.is_finite():
        raise ValueError("ZKP_PAPER_FUNDING_BOOKING_TERMS_INVALID")
    direction = 1 if identity.position_side == "long" else -1
    amount = -direction * position.qty * accounting.contract.contract_size * mark * rate
    event_id = f"paper-funding:{identity.venue_native_id}:{int(event * 1000)}"
    applied = accounting.apply_funding_observation_v1(
        event_id=event_id,
        amount=str(amount),
        currency=terms["currency"],
        instrument_id=identity.venue_native_id,
        event_time_unix=event,
    )
    if applied["idempotent_replay"]:
        raise ValueError("ZKP_PAPER_FUNDING_DUPLICATE_IN_JOURNAL")
    return {
        "terms": terms,
        "event_id": event_id,
        "amount_usd": str(amount),
        "accounting_digest": canonical_digest_v1(applied["portfolio"]),
    }


class ZkpPaperContinuationV1:
    """One writer for the original Paper cursor and its confirmed net fills."""

    def __init__(self, *, root: Path, repo: Path, revision: str, slot=ZKP_PAPER_SLOT):
        if (
            not root.is_absolute()
            or root != root.resolve()
            or root.is_relative_to(repo)
            or root.is_relative_to(Path.home() / ".local/state/peak_trade/deployments")
            or not root.is_dir()
        ):
            raise ValueError("ZKP_PAPER_ISOLATED_ROOT_REQUIRED")
        self.slot = slot
        self.root = root
        self.revision = revision
        self.profile = _read(root / "paper-profile.json")
        self.bound = BoundInstrumentV1(**self.profile["instrument_binding"])
        self.budget = load_slot_entry_budget_v1(repo / _BUDGET_POLICY)
        self.policy = load_paper_liquidity_policy_v1(repo)
        binding = self.profile["binding"]
        if (
            self.profile["schema"] != "bounded_single_instrument_paper_profile.v1"
            or self.profile["repository_sha"] != revision
            or self.profile["source_tree_sha256"] != repository_source_digest_v1()
            or self.profile["execution_environment"] != _MODE
            or self.profile["venue_order_transport"] is not False
            or self.profile["authority"] != "NONE"
            or self.profile["entry_budget"] != self.budget.to_dict_v1()
            or self.profile["fee_rate"] != str(PAPER_FEE_RATE)
            or self.bound.instrument_id != self.slot.instrument_id
            or self.bound.venue_native_id != self.slot.native_id
            or self.bound.selection_state != "EXPLICIT_SINGLE_INSTRUMENT_PAPER"
            or self.bound.selection_id != f"paper-fixed:{self.slot.native_id}"
            or self.bound.selection_integrity_digest != canonical_digest_v1(binding)
            or (binding["session_id"], binding["lane_id"]) != (root.name, self.slot.lane_id)
            or (binding["instrument_id"], binding["venue_native_id"])
            != (slot.instrument_id, slot.native_id)
            or binding["budget_digest"] != self.budget.digest_v1()
            or (
                binding["spread_limit_bps"],
                binding["slippage_limit_bps"],
                binding["adv_limit_fraction"],
                binding["adv_days"],
            )
            != (
                str(self.policy.spread_limit_bps),
                str(self.policy.slippage_limit_bps),
                str(self.policy.adv_participation_limit),
                self.policy.adv_days,
            )
        ):
            raise ValueError("ZKP_PAPER_ORIGINAL_PROFILE_REQUIRED")
        self.scope = PositionEpisodeScopeV1(root.name, _MODE)
        self.cursor_root = root / ENTRY_MARK_STATE_DIRECTORY / self.slot.lane_id
        occupied_slot = IsolatedLaneSlotV1(
            lane_id=slot.lane_id,
            occupancy=OCCUPANCY_OCCUPIED,
            canonical_instrument_id=self.bound.instrument_id,
            lane_state_root=str(self.cursor_root),
            universe_snapshot_id=self.bound.universe_snapshot_id,
            ranking_snapshot_id=self.bound.ranking_snapshot_id,
            ranking_integrity_digest=self.bound.ranking_integrity_digest,
        )
        self.pairs = {slot.lane_id: (occupied_slot, self.bound)}
        self.reconciliation = (
            build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
                bound_instrument_id=self.slot.instrument_id,
                session_id=root.name,
                repository_sha=revision,
            )
        )
        self.config_digest = layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        )
        self._g17_window = None
        self._g17_producer = None
        self._recover_required = False
        with exclusive_v1(self.root / ".paper-opening.lock"):
            self._restore()

    def _episode(self, fill, *, create=False):
        side = "long" if fill.side == "BUY" else "short"
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=PositionEpisodeIdentityV1(
                self.slot.lane_id,
                self.slot.instrument_id,
                self.slot.native_id,
                "pending",
                side,
                self.scope,
            ),
            opening_fill=fill,
        )
        args = dict(
            identity=identity,
            state_root=self.root / "episodes" / identity.episode_id,
            repository_sha=self.revision,
            config_digest=self.config_digest,
            writer_session_id=self.root.name,
        )
        if create and not args["state_root"].exists():
            return create_position_episode_from_simulated_accounting_v1(
                **args,
                session=self.accounting,
                fills=(*self.fills, fill),
                source_archive_root=self.root / "episode-sources",
            )
        reference = _read(args["state_root"] / IDENTITY_FILENAME)["entry_source_ref"]
        source_path = Path(reference.split(":", 2)[2])
        if (
            source_path.parent != self.root / "episode-sources"
            or source_path.resolve() != source_path
        ):
            raise ValueError("ZKP_PAPER_ORIGINAL_EPISODE_SOURCE_REQUIRED")
        return recover_position_episode_from_simulated_accounting_v1(
            **args, source_path=source_path
        )

    @property
    def _booking_path(self):
        return self.root / "reversals" / (self.episode.identity.episode_id + ".json")

    @property
    def _funding_path(self):
        return self.root / "funding" / f"{int(self.funding_time * 1000)}.json"

    def _restore(self):
        opening = _read(self.root / "opening-fill.json")
        plan = _read(self.root / "opening-plan.json")
        fill = _fill(opening["fill"])
        self.episode = self._episode(fill)
        source, _ = _source(self.episode.entry_source_ref, self.episode.identity)
        self.accounting = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            source["accounting_checkpoint"]
        )
        if (
            opening["status"] != "FIRST_FILL_BOOKED"
            or opening["episode_id"] != self.episode.identity.episode_id
            or opening["opening_plan_digest"] != canonical_digest_v1(plan)
            or source["fills"] != [opening["fill"]]
            or plan["fill"] != opening["fill"]
            or self.accounting.contract.to_dict() != self.profile["contract"]
            or self.accounting.initial_equity != Decimal(self.profile["initial_equity_usd"])
            or self.accounting.portfolio_state().to_dict() != opening["accounting"]
            or self.accounting.applied_fill_results[fill.fill_id].accounting_output_digest
            != opening["accounting_output_digest"]
        ):
            raise ValueError("ZKP_PAPER_ORIGINAL_OPENING_REQUIRED")
        self.fills = (fill,)
        self.funding_time = plan["costs"]["next_funding_unix"]
        self.last_receipt = opening
        self.last_funding = None
        while True:
            reversal = _read(self._booking_path) if self._booking_path.is_file() else None
            while self._funding_path.is_file() and (
                reversal is None or self.funding_time <= reversal["fill"]["event_time_unix"]
            ):
                self._publish_funding(_read(self._funding_path))
            if reversal is None:
                break
            self._publish_booking(reversal)
        raw = load_current_productive_sidestate_confirmation_cursor_v1(self.cursor_root)
        if raw is None:
            raise ValueError("ZKP_PAPER_ORIGINAL_CURSOR_REQUIRED")
        if self.episode.binding.current_cursor_publication is not None:
            recover_current_cursor_publication_v1(
                episode=self.episode,
                store_root=self.cursor_root,
                expected_scope=self.scope,
                writer_session_id=self.root.name,
            )
        elif current_productive_cursor_digest_v1(raw) != self.last_receipt["cursor_digest"]:
            raise ValueError("ZKP_PAPER_SUCCESSOR_CURSOR_MISMATCH")

    def _apply(self, plan, fill, accounting):
        before = Decimal(plan["current_contracts"])
        target = Decimal(plan["target_contracts"])
        if (
            plan["episode_id"] != self.episode.identity.episode_id
            or plan["binding_digest"] != self.bound.selection_integrity_digest
            or fill.fill_id != "direct-reversal:" + canonical_digest_v1(plan)
            or fill.instrument_id != self.slot.native_id
            or fill.mark_price != Decimal(plan["reference_mark"])
            or fill.fee != fill.notional * PAPER_FEE_RATE
            or fill.event_time_unix >= self.funding_time
        ):
            raise ValueError("ZKP_PAPER_REVERSAL_BOOKING_BINDING_MISMATCH")
        return accounting.apply_simulated_net_reversal_v1(
            fill, current_contracts=before, target_contracts=target
        )

    def _publish_booking(self, record):
        plan, fill = record["plan"], _fill(record["fill"])
        publication = self.episode.binding.current_cursor_publication
        if publication is None or publication["outgoing_digest"] != plan["cursor_digest"]:
            raise ValueError("ZKP_PAPER_REVERSAL_ORIGINAL_CURSOR_MISMATCH")
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(
            publication["outgoing_payload"]
        )
        frame = read_current_core_entry_assessment_frame_v1(cursor)
        if (
            not _is_l10_exit(frame, plan["scope_seal_id"])
            or frame["parent"]["decision_id"] != plan["decision_id"]
            or cursor.trading_epoch != plan["trading_epoch"]
        ):
            raise ValueError("ZKP_PAPER_REVERSAL_ORIGINAL_DECISION_MISMATCH")
        candidate = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            self.accounting.to_durable_dict()
        )
        applied = self._apply(plan, fill, candidate)
        if applied.accounting_output_digest != record["accounting_output_digest"]:
            raise ValueError("ZKP_PAPER_REVERSAL_BOOKING_READBACK_MISMATCH")
        self.accounting = candidate
        successor = self._episode(fill, create=True)
        source, _ = _source(successor.entry_source_ref, successor.identity)
        self.fills = (*self.fills, fill)
        if source["accounting_checkpoint"] != self.accounting.to_durable_dict() or source[
            "fills"
        ] != [row.to_dict() for row in self.fills]:
            raise ValueError("ZKP_PAPER_SUCCESSOR_ACCOUNTING_MISMATCH")
        self.episode = successor
        self.funding_time = plan["costs"]["next_funding_unix"]
        self.last_receipt = {
            "status": "NET_REVERSAL_BOOKED",
            "lane_id": self.slot.lane_id,
            "native_instrument_id": self.slot.native_id,
            "episode_id": successor.identity.episode_id,
            "previous_episode_id": plan["episode_id"],
            "cursor_digest": plan["cursor_digest"],
            "trading_epoch": plan["trading_epoch"],
            "decision_id": plan["decision_id"],
            "current_contracts": plan["current_contracts"],
            "target_contracts": plan["target_contracts"],
            "accounting_output_digest": applied.accounting_output_digest,
            "accounting": self.accounting.portfolio_state().to_dict(),
            "fill": fill.to_dict(),
            "authority": "NONE",
            "orders_sent": 0,
            "permits_created": 0,
        }
        return self.last_receipt

    def _publish_funding(self, record):
        candidate = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            self.accounting.to_durable_dict()
        )
        applied = apply_paper_funding_v1(
            record["terms"],
            candidate,
            identity=self.episode.identity,
            binding_digest=self.bound.selection_integrity_digest,
            settlement_time=self.funding_time,
        )
        if applied != record:
            raise ValueError("ZKP_PAPER_FUNDING_BOOKING_READBACK_MISMATCH")
        self.accounting = candidate
        self.funding_time = record["terms"]["next_funding_unix"]
        self.last_funding = {
            "status": "FUNDING_BOOKED",
            "lane_id": self.slot.lane_id,
            **record,
            "accounting": candidate.portfolio_state().to_dict(),
        }

    def _settle_due_funding(self, market, raw, clock):
        # A rolled schedule must connect the first unbooked cut to the venue's
        # latest previous settlement. Missing rates or marks block execution.
        events = tuple(
            event
            for event in market.funding_history_times
            if self.funding_time <= event <= market.previous_funding_unix
        )
        evidence = {row.event_unix: row for row in market.funding_settlements}
        if (
            not events
            or events[0] != self.funding_time
            or events[-1] != market.previous_funding_unix
            or any(event not in evidence for event in events)
        ):
            return {"status": "FUNDING_WAIT", "reason": "ZKP_PAPER_SETTLEMENT_EVIDENCE_PENDING"}
        if clock() < market.observed_unix:
            raise ValueError("ZKP_PAPER_FUNDING_CLOCK_REVERSED")
        for event, following in zip(events, (*events[1:], market.funding_time_unix)):
            position = self.accounting.position
            row = evidence[event]
            terms = {
                "episode_id": self.episode.identity.episode_id,
                "binding_digest": self.bound.selection_integrity_digest,
                "cursor_digest": current_productive_cursor_digest_v1(raw),
                "instrument_id": self.slot.native_id,
                "currency": self.accounting.contract.quote_currency,
                "event_time_unix": event,
                "observed_unix": market.observed_unix,
                "next_funding_unix": following,
                "realized_rate": str(row.realized_rate),
                "preceding_mark_close_usd": str(row.preceding_mark_close_usd),
                "position_side": position.side.value,
                "position_contracts": str(position.qty),
                "contract_size": str(self.accounting.contract.contract_size),
                "source_hashes": {
                    name: market.source_hashes[name]
                    for name in ("funding", "funding-history", "mark-candles")
                },
            }
            candidate = ProductiveFuturesAccountingSessionV1.from_durable_dict(
                self.accounting.to_durable_dict()
            )
            record = apply_paper_funding_v1(
                terms,
                candidate,
                identity=self.episode.identity,
                binding_digest=self.bound.selection_integrity_digest,
                settlement_time=self.funding_time,
            )
            path = self._funding_path
            immutable_json_v1(path, record)
            self._publish_funding(_read(path))
        return self.last_funding

    def step_v1(self, market, *, clock=time):
        with exclusive_v1(self.root / ".paper-opening.lock"):
            # A failed write or a second process may have advanced the original owners.
            # Reopen explicitly after any interrupted step.
            if self._recover_required or self._booking_path.exists() or self._funding_path.exists():
                raise ValueError("ZKP_PAPER_REOPEN_REQUIRED")
            self._recover_required = True
            result = self._step(market, clock)
            self._recover_required = False
            return result

    def _step(self, market, clock):
        if (
            market.slot != self.slot
            or market.native_contract != self.accounting.contract
            or market.policy != self.policy
        ):
            raise ValueError("ZKP_PAPER_CONTRACT_OR_POLICY_DRIFT")
        raw = load_current_productive_sidestate_confirmation_cursor_v1(self.cursor_root)
        if raw is None:
            raise ValueError("ZKP_PAPER_ORIGINAL_CURSOR_REQUIRED")
        require_current_cursor_continuity_v1(
            episode=self.episode, incoming=raw, store_root=self.cursor_root
        )
        scope = read_occupied_scope_mark_snapshot_v1(self.cursor_root)
        mark = scope["mark"] if scope is not None else None
        prior = self.episode.binding.current_cursor_publication
        if (
            prior is None
            and current_productive_cursor_digest_v1(raw) != self.last_receipt["cursor_digest"]
        ):
            raise ValueError("ZKP_PAPER_SUCCESSOR_CURSOR_MISMATCH")
        if market.previous_funding_unix >= self.funding_time:
            return self._settle_due_funding(market, raw, clock)
        if (
            market.observed_unix >= self.funding_time
            or market.funding_time_unix != self.funding_time
        ):
            return {"status": "FUNDING_WAIT", "reason": "ZKP_PAPER_FUNDING_SCHEDULE_UNCONFIRMED"}
        if mark and mark["position_episode_id"] == self.episode.identity.episode_id:
            frame = _scope_frame(
                parse_current_productive_sidestate_confirmation_cursor_v1(raw), mark
            )
            if frame["entry"]["decision_outcome"] in {"exit", "reduce"} and not _is_l10_exit(
                frame, mark["seal_id"]
            ):
                return {"status": "BLOCKED", "reason": "ZKP_PAPER_NON_REVERSAL_EXIT_REQUIRED"}
        mark_floor = max(
            self.fills[-1].event_time_unix,
            mark["event_unix"] if mark else 0,
            self.last_funding["terms"]["event_time_unix"] if self.last_funding else 0,
        )
        if market.market_event_unix <= mark_floor:
            return {"status": "WAITING_FOR_NEW_MARK"}
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=market.mark_payload,
            venue_native_id=self.slot.native_id,
            index_from_index_tickers=market.index_payload,
            mark_acquired_at_utc=market.mark_acquired_at,
        )
        if (
            float(market.mark) != provenance.mark_px
            or market.market_event_unix
            != provenance.require_current_mark_clock_v1(observed_unix=market.observed_unix)
        ):
            raise ValueError("ZKP_PAPER_OCCUPIED_MARK_BINDING_MISMATCH")
        if mark and mark.get("pending_reversal_episode_id") == self.episode.identity.episode_id:
            return self._reverse(scope, raw, market, clock)

        producer = self._producer(market)
        if producer is None:
            return {"status": "BLOCKED", "reason": "ZKP_PAPER_G17_ABSENT"}
        cycle = self._cycle(market, producer, raw, provenance)
        if cycle.replay_pass != "true" or cycle.decision_outcome.startswith("enter_"):
            raise ValueError("ZKP_PAPER_OCCUPIED_CORE_DECISION_UNPROVEN")
        raw = load_current_productive_sidestate_confirmation_cursor_v1(self.cursor_root)
        scope = read_occupied_scope_mark_snapshot_v1(self.cursor_root)
        if scope["mark"].get(
            "pending_reversal_episode_id"
        ) == self.episode.identity.episode_id and _is_l10_exit(
            _scope_frame(cycle.outgoing_cursor, scope["mark"]), scope["mark"]["seal_id"]
        ):
            return self._reverse(scope, raw, market, clock)
        if cycle.decision_outcome in {"exit", "reduce"} or scope["mark"].get(
            "pending_reversal_episode_id"
        ):
            return {"status": "BLOCKED", "reason": "ZKP_PAPER_NON_REVERSAL_EXIT_REQUIRED"}
        return {
            "status": "WAIT",
            "decision_outcome": cycle.decision_outcome,
            "decision_id": cycle.replay.evidence.decision_id,
            "episode_id": self.episode.identity.episode_id,
            "trading_epoch": raw["trading_epoch"],
            "cursor_digest": current_productive_cursor_digest_v1(raw),
        }

    def _producer(self, market):
        window = (market.g17_c1_open_unix, market.g17_window_digest)
        if window == self._g17_window:
            return self._g17_producer
        if self._g17_window is not None and window[0] <= self._g17_window[0]:
            return None
        g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
            evidence_store_root=self.root,
            bound_instrument=self.bound,
            mark_candles_payload=market.g17_payload,
            receive_or_capture_timestamp=market.g17_acquired_at,
        )
        if g17.fail_closed or g17.producer is None:
            return None
        producer = g17.producer
        records = producer.history.trailing_window_records_v1()
        if (
            not records
            or records[-1].event_time.unix_seconds != window[0]
            or canonical_digest_v1(
                [(record.event_time.unix_seconds, record.mark_price) for record in records]
            )
            != window[1]
        ):
            return None
        if not g17.estimate_present:
            # Cold restore leaves the estimate empty for duplicate candles.
            # Replay the verified original window through the same G17 producer.
            producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
                venue=producer.history.venue,
                canonical_instrument_id=self.slot.instrument_id,
                venue_instrument_id=self.slot.native_id,
            )
            for record in records:
                producer.ingest_finalized_pt1m_mark_sample_v1(sample=record.market_sample_identity)
            if producer.output_port_v1().estimate is None:
                return None
        self._g17_window, self._g17_producer = window, producer
        return self._g17_producer

    def _cycle(self, market, producer, raw, provenance):
        closes, c1 = extract_finalized_candle_closes_v1(market.candles_payload)
        if c1 != market.g17_c1_open_unix:
            raise ValueError("ZKP_PAPER_OCCUPIED_MARK_BINDING_MISMATCH")
        return compose_occupied_lane_mv2_dp_durable_cycle_v1(
            self.pairs,
            cycle_id_prefix=f"{self.root.name}:occupied:{int(market.market_event_unix * 1000)}",
            observed_unix=market.observed_unix,
            mark_px=provenance.mark_px,
            index_px=provenance.index_px,
            bid_px=float(market.book.bids[0][0]),
            ask_px=float(market.book.asks[0][0]),
            volume=float(market.volume_contracts),
            open_interest=float(market.oi_contracts),
            funding_rate=float(market.funding_rate),
            finalized_closes=closes,
            last_finalized_event_ts_unix=c1,
            venue_flat=False,
            existing_position_side=ExistingPositionSide(self.episode.identity.position_side),
            g17_typed_vol_producers={self.slot.lane_id: producer},
            canonical_price_provenance=provenance,
            master_v2_reconciliation_admission=self.reconciliation,
            position_episode_bindings={self.slot.lane_id: self.episode},
            position_episode_scope=self.scope,
            occupied_scope_mark=True,
            incoming_cursor_override=raw,
        )[self.slot.lane_id].cycle_result

    def _reverse(self, scope, raw, market, clock):
        require_current_cursor_continuity_v1(
            episode=self.episode, incoming=raw, store_root=self.cursor_root
        )
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        mark = scope["mark"]
        frame = _scope_frame(cursor, mark)
        parent = frame["parent"]
        snapshot = scope["snapshot"]
        old_side = self.episode.identity.position_side
        regime_pair = ("bull", "bear") if old_side == "long" else ("bear", "bull")
        if (
            not _is_l10_exit(frame, mark["seal_id"])
            or mark["switch_condition_met"] is not True
            or mark["pending_reversal_episode_id"] != self.episode.identity.episode_id
            or mark["pending_close_episode_id"] is not None
            or snapshot["instrument_id"] != self.slot.instrument_id
            or (mark["regime_pre"], snapshot["regime"]) != regime_pair
            or snapshot["scope"]["valid"] is not True
            or mark["counter_move"] < snapshot["scope"]["d_t"]
        ):
            raise ValueError("ZKP_PAPER_ORIGINAL_L10_SWITCH_REQUIRED")
        prepared = self._prepare_fill(
            market,
            clock,
            old_side,
            Decimal(str(snapshot["scope"]["d_t"])),
            decision_id=parent["decision_id"],
            assessment_digest=cursor.entry_assessment_frame["digest"],
        )
        if "fill_terms" not in prepared:
            return {"status": "REVERSAL_BLOCKED", **prepared}
        terms = prepared.pop("fill_terms")
        plan = {
            **prepared,
            "episode_id": self.episode.identity.episode_id,
            "binding_digest": self.bound.selection_integrity_digest,
            "scope_digest": scope["digest"],
            "scope_seal_id": mark["seal_id"],
            "cycle_id": mark["cycle_id"],
            "decision_id": parent["decision_id"],
            "cursor_digest": current_productive_cursor_digest_v1(raw),
            "trading_epoch": raw["trading_epoch"],
            "source_hashes": market.source_hashes,
        }
        fill = SimulatedFillInputV1(fill_id="direct-reversal:" + canonical_digest_v1(plan), **terms)
        candidate = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            self.accounting.to_durable_dict()
        )
        applied = self._apply(plan, fill, candidate)
        record = {
            "plan": plan,
            "fill": fill.to_dict(),
            "accounting_output_digest": applied.accounting_output_digest,
        }
        # The immutable booking is the commit point. Cold recovery replays the
        # confirmed fill and completes the successor using the same cursor.
        immutable_json_v1(self._booking_path, record)
        return self._publish_booking(_read(self._booking_path))

    def _prepare_fill(self, market, clock, old_side, distance, *, decision_id, assessment_digest):
        position = self.accounting.position
        current = position.qty if old_side == "long" else -position.qty
        side = "short" if current > 0 else "long"
        fill_side = "BUY" if side == "long" else "SELL"
        stop = derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=side, reference_price=market.mark, adverse_exit_distance=distance
        )
        maximum = market.maximum_contracts - abs(current)
        if stop is None or maximum < self.accounting.contract.min_qty:
            return {"reason_codes": ["ZKP_PAPER_REVERSAL_STOP_OR_NET_LIMIT"]}
        from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import (
            current_paper_slot_capital_v1,
        )

        capital, portfolio, cap = current_paper_slot_capital_v1(
            self.accounting, self.budget, market
        )
        equity = portfolio.equity
        marked_net = equity - capital.initial_equity
        loss_limit = min(
            self.budget.per_slot_test_loss_limit * market.usd_per_usdc + min(_ZERO, marked_net),
            equity,
        )
        # Reserve closing costs for the old leg before sizing the new exposure.
        impact = market.policy.slippage_limit_bps / 10000
        old_base = abs(current) * market.native_contract.contract_size
        ceiling = market.mark * (1 + impact)
        old_cost = old_base * (market.mark * impact + ceiling * PAPER_FEE_RATE)
        reserve_rate = market.funding_cap if side == "long" else -market.funding_floor
        new_cost_per_base = (
            2 * market.mark * impact
            + (ceiling + max(ceiling, stop)) * PAPER_FEE_RATE
            + max(ceiling, stop) * reserve_rate
        )
        risk = loss_limit - old_cost
        usable = min(cap, equity) - old_cost
        if risk <= 0 or usable <= 0:
            return {"reason_codes": ["ZKP_PAPER_REVERSAL_BUDGET_EXHAUSTED"]}
        size = evaluate_capital_risk_sizing_v1(
            paper_sizing_v1(
                decision_id=decision_id,
                input_digest=canonical_digest_v1(
                    {
                        "assessment_digest": assessment_digest,
                        "market_sources": market.source_hashes,
                        "position": portfolio.digest(),
                    }
                ),
                side=side,
                market=market,
                stop=stop,
                distance=distance,
                equity=equity,
                cap=usable * market.mark / (ceiling + new_cost_per_base),
                loss_limit=risk * distance / (distance + new_cost_per_base),
                budget=self.budget,
                config_digest=self.bound.selection_integrity_digest,
                instrument=replace(paper_constraints_v1(market), maximum_quantity=maximum),
            )
        )
        if size.canonical_position_sizing is None or size.final_quantity <= 0:
            return {"reason_codes": list(size.reason_codes)}
        target = size.final_quantity if side == "long" else -size.final_quantity
        net = abs(signed_position_delta(current, target))
        liquidity = market.assess_quantity_v1(side=fill_side, quantity=net)
        result = {"liquidity": liquidity, "reason_codes": liquidity["reason_codes"]}
        if not liquidity["risk_admitted"]:
            return result
        qty = abs(target)
        price = Decimal(liquidity["open_price_usd"])
        close_price = market.book.executable_price_v1(
            "SELL" if side == "long" else "BUY", qty, market.native_contract.tick_size
        )
        direction = 1 if side == "long" else -1
        base = qty * market.native_contract.contract_size
        net_base = net * market.native_contract.contract_size
        notional = net_base * price
        fee = notional * PAPER_FEE_RATE
        slippage = net_base * max(_ZERO, direction * (price - market.mark))
        worst_price = max(market.mark, stop, price, close_price)
        exit_fee = base * worst_price * PAPER_FEE_RATE
        exit_slippage = base * max(_ZERO, direction * (market.mark - close_price))
        funding = base * worst_price * reserve_rate
        costs = fee + slippage + exit_fee + exit_slippage + funding
        result["costs"] = {
            "currency": "USD",
            "net_fee": str(fee),
            "net_slippage": str(slippage),
            "exit_fee_allowance": str(exit_fee),
            "exit_slippage_allowance": str(exit_slippage),
            "funding_allowance": str(funding),
            "next_funding_unix": market.funding_time_unix,
            "target_notional_limit": str(cap),
            "loss_limit": str(loss_limit),
        }
        if max(base * market.mark, base * price) + costs > min(cap, equity) or (
            base * distance + costs > loss_limit
        ):
            return {**result, "reason_codes": ["ZKP_PAPER_REVERSAL_NOTIONAL_OR_COST_LIMIT"]}
        now = clock()
        if now >= self.funding_time or not paper_fill_fresh_v1(market, now):
            return {**result, "reason_codes": ["ZKP_PAPER_MARKET_EXPIRED_AT_FILL"]}
        return {
            **result,
            "current_contracts": str(current),
            "target_contracts": str(target),
            "reference_mark": str(market.mark),
            "protective_stop": str(stop),
            "scope_distance": str(distance),
            "fill_terms": dict(
                instrument_id=self.slot.native_id,
                side=fill_side,
                quantity=net,
                mark_price=market.mark,
                fill_price=price,
                fee=fee,
                slippage_cost=slippage,
                notional=notional,
                event_time_unix=now,
            ),
        }
