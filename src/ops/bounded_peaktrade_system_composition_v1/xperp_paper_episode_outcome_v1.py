"""Archive and read XPERP Paper episodes completed by an original net reversal."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1
from src.governance.canonical_order_intent_v1 import canonical_order_intent_from_dict
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_continuation_v1 import (
    apply_paper_funding_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    IRYS_PAPER_SLOT,
    UP_PAPER_SLOT,
    ZKP_PAPER_SLOT,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    EXIT_STATE_FILENAME,
    MANIFEST_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import ExitPolicyPersistenceError
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    IDENTITY_FILENAME,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    recover_position_episode_from_simulated_accounting_v1,
    require_economic_history_extension_v1,
)
from src.ops.first_entry_mark_clock_v2 import ENTRY_MARK_STATE_DIRECTORY
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    durable_bytes_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import _fill
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    AccountingEngineError,
    ProductiveFuturesAccountingSessionV1,
)

CLOSEOUT = "closeout.json"
_BOUNDARY = "XPERP_PAPER_NET_REVERSAL"
_MODE = "INTERNAL_SIMULATED_EXECUTION"
_STATE_FILES = (IDENTITY_FILENAME, EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME)
_ROOT_FILES = (
    "paper-profile.json",
    "window.json",
    CLOSEOUT,
    "opening-plan.json",
    "opening-fill.json",
)
_SLOTS = {slot.lane_id: slot for slot in (ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT)}


def _utc(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat().replace("+00:00", "Z")


def seal_xperp_paper_archive_v1(root: Path, closeout: dict) -> None:
    """Publish the finalized inventory under the Paper driver's existing lock."""
    last = closeout.get("last_booking")
    if last is None or last["status"] != "NET_REVERSAL_BOOKED":
        return
    # Older XPERP journals can lack the original opening decision. They cannot
    # be promoted to learning evidence by reconstructing a replacement.
    if "decision_cursor" not in json.loads((root / "opening-plan.json").read_bytes()):
        return
    paths = [root / name for name in _ROOT_FILES]
    for pattern in ("reversals/*.json", "funding/*.json", "episode-sources/*.json"):
        paths.extend(root.glob(pattern))
    for episode in (root / "episodes").iterdir():
        paths.extend(episode / name for name in _STATE_FILES)
    lines = []
    for path in sorted(paths):
        if path.resolve() != path:
            raise ValueError("XPERP_PAPER_ARCHIVE_SYMLINK")
        lines.append(
            f"{sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}\n"
        )
    manifest = root / MANIFEST_FILENAME
    raw = "".join(lines).encode()
    if manifest.is_symlink() or (manifest.exists() and manifest.read_bytes() != raw):
        raise ValueError("XPERP_PAPER_ARCHIVE_CONFLICT")
    if not manifest.exists():
        durable_bytes_v1(manifest, raw)


class _Archive:
    def __init__(self, root, expected_lane_id=None, *, include_decision_evidence=False):
        if root.resolve() != root:
            raise ValueError("XPERP_PAPER_ARCHIVE_PATH_INVALID")
        self.root = root
        self.include_decision_evidence = include_decision_evidence
        self.manifest = root / MANIFEST_FILENAME
        self.manifest_raw = self.manifest.read_bytes()
        ok, reason = verify_manifest_sha256(root, required_rel_paths=_ROOT_FILES)
        if not ok or self.manifest.read_bytes() != self.manifest_raw:
            raise ValueError(f"XPERP_PAPER_MANIFEST_INVALID:{reason}")
        self.pins = {}
        for line in self.manifest_raw.decode().splitlines():
            if line.strip():
                digest, rel = line.split(None, 1)
                self.pins[rel] = digest
        profile = self.profile = self.read("paper-profile.json")
        try:
            self.fee_rate = Decimal(profile["fee_rate"])
            self.contract_size = Decimal(profile["contract"]["contract_size"])
        except ArithmeticError as exc:
            raise ValueError("XPERP_PAPER_MONETARY_PROFILE_INVALID") from exc
        if any(
            not value.is_finite() or value <= 0 for value in (self.fee_rate, self.contract_size)
        ):
            raise ValueError("XPERP_PAPER_MONETARY_PROFILE_INVALID")
        binding = profile["binding"]
        self.slot = _SLOTS.get(binding["lane_id"])
        instrument = profile["instrument_binding"]
        closeout = self.read(CLOSEOUT)
        if (
            self.slot is None
            or (expected_lane_id is not None and binding["lane_id"] != expected_lane_id)
            or binding["session_id"] != root.name
            or (binding["instrument_id"], binding["venue_native_id"])
            != (self.slot.instrument_id, self.slot.native_id)
            or (instrument["instrument_id"], instrument["venue_native_id"])
            != (self.slot.instrument_id, self.slot.native_id)
            or instrument["selection_state"] != "EXPLICIT_SINGLE_INSTRUMENT_PAPER"
            or instrument["selection_integrity_digest"] != canonical_digest_v1(binding)
            or profile["schema"] != "bounded_single_instrument_paper_profile.v1"
            or profile["execution_environment"] != _MODE
            or profile["authority"] != "NONE"
            or profile["venue_order_transport"] is not False
            or binding["environment"] != _MODE
            or binding["fee_rate"] != profile["fee_rate"]
            or not re.fullmatch(r"[0-9a-f]{40}", profile["repository_sha"])
            or not re.fullmatch(r"[0-9a-f]{64}", profile["source_tree_sha256"])
            or closeout["authority"] != "NONE"
            or closeout["orders_sent"] != 0
            or closeout["permits_created"] != 0
            or (closeout["status"], closeout.get("reason"))
            not in {
                ("WINDOW_ENDED_OCCUPIED", None),
                ("BLOCKED", "ZKP_PAPER_NON_REVERSAL_EXIT_REQUIRED"),
            }
            or closeout["last_booking"]["status"] != "NET_REVERSAL_BOOKED"
        ):
            raise ValueError("XPERP_PAPER_EPISODE_SCOPE_MISMATCH")
        self.last = closeout["last_booking"]
        self.opening = self.read("opening-fill.json")
        self.window = self.read("window.json")
        start, duration = self.window["started_at"], self.window["duration_seconds"]
        if (
            type(start) not in (int, float)
            or not isfinite(start)
            or start <= 0
            or type(duration) is not int
            or not 1 <= duration <= 7200
            or duration != profile["duration_seconds"]
        ):
            raise ValueError("XPERP_PAPER_WINDOW_MISMATCH")

    def read(self, path):
        file = self.root / path
        if file.resolve() != file or path not in self.pins:
            raise ValueError(f"XPERP_PAPER_ARTIFACT_NOT_PINNED:{path}")
        raw = file.read_bytes()
        if sha256(raw).hexdigest() != self.pins[path]:
            raise ValueError(f"XPERP_PAPER_ARTIFACT_CHANGED:{path}")
        return json.loads(raw)

    def identity(self, fill):
        return bind_simulated_accounting_episode_identity_v1(
            identity=PositionEpisodeIdentityV1(
                self.slot.lane_id,
                self.slot.instrument_id,
                self.slot.native_id,
                "pending",
                "long" if fill.side == "BUY" else "short",
                PositionEpisodeScopeV1(self.root.name, _MODE),
            ),
            opening_fill=fill,
        )

    def episode(self, identity):
        prefix = Path("episodes") / identity.episode_id
        entry = self.read((prefix / IDENTITY_FILENAME).as_posix())
        state = self.read((prefix / EXIT_STATE_FILENAME).as_posix())
        for filename in (COMMIT_MARKER_FILENAME, MANIFEST_FILENAME):
            path = (prefix / filename).as_posix()
            if path not in self.pins:
                raise ValueError("XPERP_PAPER_EPISODE_OWNER_STATE_NOT_PINNED")
        ref = entry["entry_source_ref"]
        source_path = Path(ref.split(":", 2)[2])
        if source_path.parent != self.root / "episode-sources":
            raise ValueError("XPERP_PAPER_EPISODE_SOURCE_OUTSIDE_ARCHIVE")
        source = self.read(source_path.relative_to(self.root).as_posix())
        try:
            episode = recover_position_episode_from_simulated_accounting_v1(
                identity=identity,
                source_path=source_path,
                state_root=self.root / prefix,
                repository_sha=self.profile["repository_sha"],
                config_digest=state["config_digest"],
                writer_session_id=self.root.name,
            )
        except (ExitPolicyPersistenceError, AccountingEngineError, ArithmeticError) as exc:
            raise ValueError("XPERP_PAPER_EPISODE_OWNER_READBACK_FAILED") from exc
        payload = source["payload"]
        if (
            episode.entry_source_ref != ref
            or source["content_digest"] != ref.split(":", 2)[1]
            or payload["accounting_checkpoint"]["contract"] != self.profile["contract"]
            or Decimal(payload["accounting_checkpoint"]["initial_equity"])
            != Decimal(self.profile["initial_equity_usd"])
        ):
            raise ValueError("XPERP_PAPER_ACCOUNTING_DOMAIN_MISMATCH")
        return episode, payload

    def closed(self):
        """Follow the committed chain from the opening to the retained position."""
        remaining = {path for path in self.pins if path.startswith("reversals/")}
        identity = self.identity(_fill(self.opening["fill"]))
        if self.opening["episode_id"] != identity.episode_id:
            raise ValueError("XPERP_PAPER_OPENING_EPISODE_MISMATCH")
        closed = {}
        while remaining:
            key = f"reversals/{identity.episode_id}.json"
            if key not in remaining:
                raise ValueError("XPERP_PAPER_REVERSAL_CHAIN_BROKEN")
            remaining.remove(key)
            booking = self.read(key)
            fill = _fill(booking["fill"])
            successor = self.identity(fill)
            closed[identity.episode_id] = (identity, successor, booking)
            identity = successor
        if (
            not closed
            or self.last["episode_id"] != identity.episode_id
            or (self.last["lane_id"], self.last["native_instrument_id"])
            != (identity.lane_id, identity.venue_native_id)
            or self.last["previous_episode_id"] != next(reversed(closed))
            or self.last["fill"] != booking["fill"]
            or self.last["accounting_output_digest"] != booking["accounting_output_digest"]
        ):
            raise ValueError("XPERP_PAPER_CLOSEOUT_CHAIN_MISMATCH")
        return closed

    def decision(self, raw, fill, *, decision_id, cycle_id, expected_outcome):
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        frame = read_current_core_entry_assessment_frame_v1(cursor)
        parent = frame["parent"]
        context = json.loads(cursor.entry_assessment_frame["market_context"]["canonical"])
        stamp = datetime.fromisoformat(context["decision_time"].replace("Z", "+00:00"))
        if (
            (cursor.instrument_id, cursor.venue_native_id)
            != (self.slot.instrument_id, self.slot.native_id)
            or (parent["decision_id"], parent["decision_outcome"])
            != (decision_id, expected_outcome)
            or frame["entry"]["decision_outcome"] != expected_outcome
            or fill.instrument_id != self.slot.native_id
            or fill.reduce_only is not False
            or fill.notional != fill.quantity * self.contract_size * fill.fill_price
            or fill.fee != fill.notional * self.fee_rate
            or stamp.utcoffset() is None
            or not self.window["started_at"] <= stamp.timestamp() <= fill.event_time_unix
            or not fill.event_time_unix
            < self.window["started_at"] + self.window["duration_seconds"]
            or not cycle_id.startswith(self.root.name + ":")
            or not cycle_id.endswith(":" + self.slot.lane_id)
        ):
            raise ValueError("XPERP_PAPER_ORIGINAL_DECISION_MISMATCH")
        result = {
            "decision_id": decision_id,
            "decision_sha256": cursor.entry_assessment_frame["components"]["parent"][
                "semantic_digest"
            ],
            "cycle_id": cycle_id,
            "decision_observed_at_utc": _utc(stamp.timestamp()),
            "decision_outcome": expected_outcome,
            "decision_config_sha256": parent["config_digest"],
            "trading_epoch": str(parent["trading_epoch"]),
            "fill_id": fill.fill_id,
            "fill_event_at_utc": _utc(fill.event_time_unix),
        }
        if self.include_decision_evidence:
            # Copy the archived cursor, not a replay or today's state. This is
            # the original assessment output and post-decision cursor, not a
            # complete pre-decision DDO information set or a quality verdict.
            result["decision_evidence"] = {
                "schema": "paper_original_decision_cursor.v1",
                "scope": "ORIGINAL_ASSESSMENT_AND_POST_DECISION_CURSOR",
                "cursor": raw,
            }
        return result

    def reversal(self, episode, booking, fill):
        plan = booking["plan"]
        pub = episode.binding.current_cursor_publication
        if pub is None:
            raise ValueError("XPERP_PAPER_REVERSAL_CURSOR_MISSING")
        raw = pub["outgoing_payload"]
        require_current_cursor_continuity_v1(
            episode=episode,
            incoming=raw,
            store_root=self.root / ENTRY_MARK_STATE_DIRECTORY / self.slot.lane_id,
        )
        evidence = self.decision(
            raw,
            fill,
            decision_id=plan["decision_id"],
            cycle_id=plan["cycle_id"],
            expected_outcome="exit",
        )
        entry = json.loads(raw["entry_assessment_frame"]["components"]["entry"]["canonical"])
        if (
            plan["episode_id"] != episode.identity.episode_id
            or plan["binding_digest"]
            != self.profile["instrument_binding"]["selection_integrity_digest"]
            or plan["cursor_digest"] != current_productive_cursor_digest_v1(raw)
            or plan["trading_epoch"] != raw["trading_epoch"]
            or plan["reference_mark"] != str(fill.mark_price)
            or entry["exit_class"] != "strategy_invalidation_exit"
            or f"l10_scope_switch_exit:{plan['scope_seal_id']}" not in entry["reason_codes"]
            or fill.fill_id != "direct-reversal:" + canonical_digest_v1(plan)
        ):
            raise ValueError("XPERP_PAPER_REVERSAL_LINEAGE_MISMATCH")
        return evidence

    def verify_booking(self, identity, before, after, funding, funding_time, booking):
        replay = ProductiveFuturesAccountingSessionV1.from_durable_dict(before)
        plan, close = booking["plan"], _fill(booking["fill"])
        try:
            for event in funding:
                stamp = event["value"]["event_time_unix"]
                record = self.read(f"funding/{int(stamp * 1000)}.json")
                terms = record["terms"]
                if (
                    terms["event_time_unix"] != stamp
                    or not stamp <= terms["observed_unix"] <= close.event_time_unix
                ):
                    raise ValueError("XPERP_PAPER_FUNDING_CLOCK_MISMATCH")
                applied = apply_paper_funding_v1(
                    terms,
                    replay,
                    identity=identity,
                    settlement_time=funding_time,
                    binding_digest=plan["binding_digest"],
                )
                if applied != record or replay.funding_events[event["event_id"]] != event["value"]:
                    raise ValueError("XPERP_PAPER_FUNDING_BOOKING_MISMATCH")
                funding_time = terms["next_funding_unix"]
                # The writer restores its candidate from the durable owner at
                # every booking boundary, including after Funding.
                replay = ProductiveFuturesAccountingSessionV1.from_durable_dict(
                    replay.to_durable_dict()
                )
            if close.event_time_unix >= funding_time:
                raise ValueError("XPERP_PAPER_REVERSAL_UNSETTLED_FUNDING")
            applied = replay.apply_simulated_net_reversal_v1(
                close,
                current_contracts=Decimal(plan["current_contracts"]),
                target_contracts=Decimal(plan["target_contracts"]),
            )
        except (AccountingEngineError, ArithmeticError) as exc:
            raise ValueError("XPERP_PAPER_BOOKING_REPLAY_FAILED") from exc
        if (
            applied.accounting_output_digest != booking["accounting_output_digest"]
            or replay.to_durable_dict() != after
        ):
            raise ValueError("XPERP_PAPER_REVERSAL_ACCOUNTING_MISMATCH")


def closed_xperp_paper_episode_ids_v1(root: Path) -> tuple[str, ...]:
    return tuple(_Archive(root).closed())


def read_xperp_paper_episode_outcome_v1(
    root, episode_id, *, expected_lane_id=None, include_decision_evidence=False
):
    archive = _Archive(root, expected_lane_id, include_decision_evidence=include_decision_evidence)
    closed = archive.closed()
    if episode_id not in closed:
        raise ValueError("XPERP_PAPER_EPISODE_NOT_CLOSED")
    identity, successor, booking = closed[episode_id]
    episode, before = archive.episode(identity)
    following, after = archive.episode(successor)
    prior_events, events = require_economic_history_extension_v1(before, after)
    if not events[len(prior_events) :] or (
        any(event["kind"] != "FUNDING" for event in events[len(prior_events) : -1])
        or events[-1] != {"kind": "FILL", "value": booking["fill"]}
    ):
        raise ValueError("XPERP_PAPER_REVERSAL_ECONOMIC_HISTORY_MISMATCH")

    opening, close = _fill(before["fills"][-1]), _fill(booking["fill"])
    initial = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        before["accounting_checkpoint"]
    )
    final = ProductiveFuturesAccountingSessionV1.from_durable_dict(after["accounting_checkpoint"])
    initial_applied = initial.applied_fill_results[opening.fill_id]
    final_applied = final.applied_fill_results[close.fill_id]
    if len(before["fills"]) == 1:
        plan = archive.read("opening-plan.json")
        intent = canonical_order_intent_from_dict(plan["intent"])
        first = archive.opening
        opened = archive.decision(
            plan["decision_cursor"],
            opening,
            decision_id=plan["decision_id"],
            cycle_id=plan["cycle_id"],
            expected_outcome="enter_" + identity.position_side,
        )
        if (
            first["status"] != "FIRST_FILL_BOOKED"
            or first["opening_plan_digest"] != canonical_digest_v1(plan)
            or first["accounting_output_digest"] != initial_applied.accounting_output_digest
            or first["fill"] != plan["fill"]
            or first["fill"] != opening.to_dict()
            or first["decision_id"] != opened["decision_id"]
            or (intent.decision_id, intent.instrument_id, intent.quantity)
            != (opened["decision_id"], identity.instrument_id, opening.quantity)
            or intent.side != identity.position_side.upper()
            or intent.submission_authorized
            or intent.execution_eligible
            or intent.adapter_compatible
            or intent.reduce_only
            or opening.fill_id != f"paper:{intent.semantic_digest}"
        ):
            raise ValueError("XPERP_PAPER_OPENING_LINEAGE_MISMATCH")
        funding_time = plan["costs"]["next_funding_unix"]
    else:
        previous = archive.identity(_fill(before["fills"][-2]))
        prior_episode, _ = archive.episode(previous)
        _, original_successor, prior_booking = closed[previous.episode_id]
        if (
            original_successor != identity
            or prior_booking["fill"] != opening.to_dict()
            or prior_booking["accounting_output_digest"] != initial_applied.accounting_output_digest
        ):
            raise ValueError("XPERP_PAPER_PRIOR_REVERSAL_MISMATCH")
        opened = archive.reversal(prior_episode, prior_booking, opening)
        funding_time = prior_booking["plan"]["costs"]["next_funding_unix"]
    closed_by = archive.reversal(episode, booking, close)
    archive.verify_booking(
        identity,
        before["accounting_checkpoint"],
        after["accounting_checkpoint"],
        events[len(prior_events) : -1],
        funding_time,
        booking,
    )

    # The accounting owner already assigns the successor's share of the one
    # fee debit to its new position. Attribute the remainder to this close.
    entry_fee = initial.position.fees_paid
    closing_fee = close.fee - final.position.fees_paid
    fees = entry_fee + closing_fee
    entry_notional = initial.position.qty * initial.contract.contract_size * opening.fill_price
    close_notional = initial.position.qty * final.contract.contract_size * close.fill_price
    entry_slippage = opening.slippage_cost * initial.position.qty / opening.quantity
    close_slippage = close.slippage_cost - close.slippage_cost * final.position.qty / close.quantity
    slippage = entry_slippage + close_slippage
    realized = final.realized_pnl - initial.realized_pnl
    funding = final.funding_pnl - initial.funding_pnl
    if (
        min(entry_fee, closing_fee, entry_slippage, close_slippage) < 0
        or archive.manifest.read_bytes() != archive.manifest_raw
    ):
        raise ValueError("XPERP_PAPER_OUTCOME_INTEGRITY_MISMATCH")
    body = {
        "schema": "paper_episode_outcome.v1",
        "economic_boundary": _BOUNDARY,
        "authority": "NONE",
        "execution_environment": _MODE,
        "archive_manifest_sha256": sha256(archive.manifest_raw).hexdigest(),
        "repository_sha": archive.profile["repository_sha"],
        "source_tree_sha256": archive.profile["source_tree_sha256"],
        "episode_id": episode_id,
        "session_id": root.name,
        "lane_id": identity.lane_id,
        "instrument_id": identity.instrument_id,
        "venue_native_id": identity.venue_native_id,
        "currency": initial.contract.quote_currency,
        "observed_at_utc": closed_by["fill_event_at_utc"],
        "entry_source_ref": episode.entry_source_ref,
        "closure_ref": following.entry_source_ref,
        "fill_bindings": [
            {
                **opened,
                "episode_fill_role": "OPEN",
                "episode_contracts": str(initial.position.qty),
                "fee": str(entry_fee),
                "notional": str(entry_notional),
                "slippage": str(entry_slippage),
                "accounting_output_digest": initial_applied.accounting_output_digest,
            },
            {
                **closed_by,
                "episode_fill_role": "CLOSE",
                "episode_contracts": str(initial.position.qty),
                "fee": str(closing_fee),
                "notional": str(close_notional),
                "slippage": str(close_slippage),
                "accounting_output_digest": final_applied.accounting_output_digest,
            },
        ],
        "realized_pnl": str(realized),
        "fees": str(fees),
        "funding_pnl": str(funding),
        "slippage_already_reflected_in_fill_prices": str(slippage),
        "simulated_net_pnl": str(realized + funding - fees),
    }
    return {**body, "outcome_digest": digest_v1(body)}
