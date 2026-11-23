"""Read original inputs for a retrospective, fixed-quantity UP Paper liquidity comparison."""

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from pathlib import Path

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperLiquiditySnapshotV1,
    load_paper_liquidity_policy_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.xperp_paper_episode_outcome_v1 import _Archive
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    UP_PAPER_SLOT,
    bind_zkp_paper_market_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)


@dataclass(frozen=True)
class ReversalWindow:
    decision_id: str
    quantity: Decimal
    side: str
    signal_ms: int
    start_ns: int  # Local market observation at the archived blocked decision.
    end_ns: int  # Exclusive exchange mark time of the actual execution input.
    liquidity: PaperLiquiditySnapshotV1
    evidence: dict


def _read(path):
    return json.loads(path.read_bytes())


def _trigger_market(public, archive, plan, signal_ms, policy):
    cards = archive.root / "instrument-cards" / archive.slot.lane_id / "versions"
    matches = []
    for path in cards.glob("*/decision.json"):
        envelope = _read(path)
        card = envelope["body"]
        if (
            card.get("mark_event_unix") is None
            or round(card["mark_event_unix"] * 1000) != signal_ms
        ):
            continue
        prepared = (card.get("master_v2") or {}).get("prepared_input") or {}
        seal = prepared.get("layered_core_authority_seal") or {}
        if seal.get("seal_id") == plan["scope_seal_id"]:
            if envelope["sha256"] != canonical_digest_v1(card):
                raise ValueError("UP Paper trigger card digest mismatch")
            matches.append(card)
    (card,) = matches
    if (
        card["session_id"] != archive.root.name
        or card["binding"] != archive.profile["instrument_binding"]
        or card["lane_id"] != archive.slot.lane_id
    ):
        raise ValueError("UP Paper trigger identity mismatch")
    mark_hash = card["sources"]["mark"]["body_sha256"]
    (trigger,) = [
        path.parent
        for path in public.glob("*/mark.json")
        if sha256(path.read_bytes()).hexdigest() == mark_hash
        and _read(path.parent / "receipts.json")["mark"]["acquired_at_utc"]
        == card["sources"]["mark"]["acquired_at_utc"]
    ]
    receipts = _read(trigger / "receipts.json")
    inputs, bodies = {}, {}
    for name, receipt in receipts.items():
        body = (trigger / (name + ".json")).read_bytes()
        digest = sha256(body).hexdigest()
        if (
            digest != receipt["body_sha256"]
            or digest != card["sources"][name]["body_sha256"]
            or receipt["pretrade_decision_id"] != f"{archive.root.name}:{trigger.name}:{name}"
            or receipt["acquired_at_utc"] != card["sources"][name]["acquired_at_utc"]
        ):
            raise ValueError("UP Paper trigger original receipt mismatch")
        bodies[name] = body
        inputs[name] = FreshPretradeGetTransportResultV1(
            **{k: v for k, v in receipt.items() if k != "file"}, payload=json.loads(body)
        )
    market = bind_zkp_paper_market_v1(
        inputs,
        policy=policy,
        observed_unix=card["observed_unix"],
        slot=archive.slot,
        original_bodies=bodies,
    )
    original = _read(trigger / "result.json")
    if original != card["master_v2"]["decision"] or original["status"] != "REVERSAL_BLOCKED":
        raise ValueError("original blocked UP reversal required")
    return market, original["liquidity"], trigger, canonical_digest_v1(card)


def paper_identity(slot, session, occupancy_digest, entry_digest):
    if (slot.native_id, slot.instrument_id) != (
        UP_PAPER_SLOT.native_id,
        UP_PAPER_SLOT.instrument_id,
    ):
        raise ValueError("UP dated future required")
    return dict(
        mode="PAPER",
        session=session,
        lane=slot.lane_id,
        native_id=slot.native_id,
        canonical_id=slot.instrument_id,
        occupancy_digest=occupancy_digest,
        binding_digest=entry_digest,
        instrument_type="FUTURES",
        settlement_asset="USD",
    )


def archive_identity(archive):
    return paper_identity(
        archive.slot,
        archive.root.name,
        archive.profile["n5_assignment"]["selection_digest"],
        archive.profile["instrument_binding"]["selection_integrity_digest"],
    )


def read_confirmed_reversal(archive, path, identity):
    if path.name != "result.json" or path.parents[1] != archive.root / "public":
        raise ValueError("original booked public poll result required")
    result = _read(path)
    if result["status"] != "NET_REVERSAL_BOOKED":
        raise ValueError("confirmed reversal required")
    relative = f"reversals/{result['previous_episode_id']}.json"
    booking = archive.read(relative)
    plan, fill = booking["plan"], booking["fill"]
    mark_body = (path.parent / "mark.json").read_bytes()
    if (
        plan["binding_digest"] != identity["binding_digest"]
        or result["decision_id"] != plan["decision_id"]
        or result["fill"] != fill
        or result["accounting_output_digest"] != booking["accounting_output_digest"]
        or fill["fill_id"] != "direct-reversal:" + canonical_digest_v1(plan)
        or fill["instrument_id"] != archive.slot.native_id
        or sha256(mark_body).hexdigest() != plan["source_hashes"]["mark"]
    ):
        raise ValueError("UP Paper original fill or execution mark mismatch")
    session, kind, signal, *_, lane = plan["cycle_id"].split(":")
    if (session, kind, lane) != (archive.root.name, "occupied", identity["lane"]):
        raise ValueError("UP Paper signal identity mismatch")
    (mark,) = json.loads(mark_body)["data"]
    if mark["instId"] != archive.slot.native_id or Decimal(mark["markPx"]) != Decimal(
        fill["mark_price"]
    ):
        raise ValueError("UP Paper execution mark mismatch")
    return result, plan, mark, int(signal), archive.pins[relative]


def load_reversal_window(booked_result, repo):
    path = Path(booked_result).resolve(strict=True)
    archive = _Archive(path.parents[2])
    identity = archive_identity(archive)
    result, plan, mark, signal, booking_hash = read_confirmed_reversal(archive, path, identity)
    fill = result["fill"]
    policy = load_paper_liquidity_policy_v1(repo)
    binding = archive.profile["binding"]
    if (
        policy.spread_limit_bps,
        policy.slippage_limit_bps,
        policy.adv_participation_limit,
        policy.adv_days,
    ) != (
        Decimal(binding["spread_limit_bps"]),
        Decimal(binding["slippage_limit_bps"]),
        Decimal(binding["adv_limit_fraction"]),
        binding["adv_days"],
    ):
        raise ValueError("archived UP Paper policy differs from current owner")
    market, blocked, trigger, card_hash = _trigger_market(
        path.parents[1], archive, plan, int(signal), policy
    )
    side, quantity = blocked["side"], Decimal(blocked["quantity_contracts"])
    if blocked != market.assess_quantity_v1(side=side, quantity=quantity) or (side, quantity) != (
        fill["side"],
        Decimal(fill["quantity"]),
    ):
        raise ValueError("original UP reversal quantity or assessment mismatch")
    start = int(
        (Decimal(str(market.observed_unix)) * 10**9).to_integral_value(rounding=ROUND_CEILING)
    )
    end = int(mark["ts"]) * 10**6
    if not start < end or start // (86400 * 10**9) != (end - 1) // (86400 * 10**9):
        raise ValueError("delayed reversal within one finalized ADV day required")
    return identity, ReversalWindow(
        plan["decision_id"],
        quantity,
        side,
        int(signal),
        start,
        end,
        market._liquidity_snapshot(),
        dict(
            booking_sha256=booking_hash,
            trigger_card_sha256=card_hash,
            trigger_poll=trigger.name,
            execution_mark_sha256=plan["source_hashes"]["mark"],
            trigger_source_hashes=market.source_hashes,
        ),
    )
