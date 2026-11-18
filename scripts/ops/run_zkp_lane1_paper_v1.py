#!/usr/bin/env python3
"""Probe or explicitly run one configured, isolated XPERP Paper slot."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal, DecimalException
from functools import partial
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep, time
from uuid import uuid4

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (  # noqa: E402
    collect_bound_paper_liquidity_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.xperp_paper_episode_outcome_v1 import (  # noqa: E402
    seal_xperp_paper_archive_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_continuation_v1 import (  # noqa: E402
    ZkpPaperContinuationV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import ZkpPaperEntryV1  # noqa: E402
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (  # noqa: E402
    IRYS_PAPER_SLOT,
    PAPER_ALLOCATION_USDC,
    PAPER_FEE_RATE,
    UP_PAPER_SLOT,
    ZKP_PAPER_SLOT,
    collect_zkp_paper_market_v1,
    load_paper_liquidity_policy_v1,
    zkp_public_queries_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (  # noqa: E402
    durable_bytes_v1,
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (  # noqa: E402
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1  # noqa: E402
from src.ops.instrument_card_stream_v1 import InstrumentCardStreamV1, paper_budget_source_v1  # noqa: E402

_POLL_SECONDS = 5


def _isolated_root(path):
    if (
        not path.is_absolute()
        or path != path.resolve()
        or not path.parent.is_dir()
        or path.is_relative_to(REPO)
        or path.is_relative_to(Path.home() / ".local/state/peak_trade/deployments")
    ):
        raise ValueError("ZKP_PAPER_ISOLATED_PATH_REQUIRED")
    return path


def _new_root(path):
    if _isolated_root(path).exists():
        raise ValueError("ZKP_PAPER_NEW_ISOLATED_PATH_REQUIRED")
    return path


def _read_paper_slot(path):
    config = json.loads(path.read_bytes())
    # Historical local preparations used environment=PAPER. Preserve their
    # original files; accept only this explicit equivalent declaration.
    surface = config.get("surface")
    if surface is None and config.get("environment") == "PAPER":
        surface = "PAPER_EXCHANGE"
    if "environment" in config and config["environment"] != "PAPER":
        raise ValueError("PAPER_SLOT_ENVIRONMENT_MISMATCH")
    slot = IRYS_PAPER_SLOT if config["lane"] == IRYS_PAPER_SLOT.lane_id else UP_PAPER_SLOT
    if (
        config["lane"],
        config["canonical_instrument_id"],
        config["native_instrument_id"],
        surface,
        config["authority"],
    ) != (slot.lane_id, slot.instrument_id, slot.native_id, "PAPER_EXCHANGE", "NONE"):
        raise ValueError(f"{slot.base_currency}_PAPER_SLOT_CONFIG_MISMATCH")
    return slot


def _capture(policy, *, label, output=None, bound=None, slot=ZKP_PAPER_SLOT):
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        timeout_seconds=6,
        max_request_count=(
            4 if bound is not None else len(zkp_public_queries_v1(policy.adv_days, slot=slot))
        ),
    )
    records = {}

    def retain(name, result, body):
        if output is None:
            return
        path = output / f"{name}.json"
        durable_bytes_v1(path, body)
        record = asdict(result)
        del record["payload"]
        records[name] = {"file": str(path), **record}

    if bound is None:
        market = collect_zkp_paper_market_v1(
            transport, policy=policy, capture_id=label, retain=retain, slot=slot
        )
    else:
        market = collect_bound_paper_liquidity_v1(
            transport, bound=bound, policy=policy, capture_id=label, retain=retain
        ).to_preflight_v1()
    if output is not None:
        immutable_json_v1(output / "receipts.json", records)
    return market


def _read_cap24_binding(root: Path) -> BoundInstrumentV1:
    manifest = (root / MANIFEST_FILENAME).read_text()
    raw = (root / EVIDENCE_FILENAME).read_bytes()
    if (
        f"{sha256(raw).hexdigest()}  {EVIDENCE_FILENAME}" not in manifest.splitlines()
        or (root / MANIFEST_FILENAME).read_text() != manifest
    ):
        raise ValueError("PAPER_LIQUIDITY_CAP24_EVIDENCE_DIGEST_MISMATCH")
    record = json.loads(raw)
    if (
        record["capability_id"] != CAPABILITY_ID
        or record["schema_version"] != SCHEMA_VERSION
        or record["ok"] is not True
        or record["hard_stop"] is not False
    ):
        raise ValueError("PAPER_LIQUIDITY_CAP24_BOUND_EVIDENCE_REQUIRED")
    bound = BoundInstrumentV1(**record["bound"])
    for field in ("instrument_id", "venue_native_id", "selection_id", "selection_integrity_digest"):
        if not getattr(bound, field) or getattr(bound, field) != record[field]:
            raise ValueError("PAPER_LIQUIDITY_CAP24_IDENTITY_MISMATCH")
    return bound


def _preflight_cap24(policy, *, cap24_root, output):
    bound = _read_cap24_binding(cap24_root)
    market = _capture(
        policy, label=f"lane-1-paper-liquidity:{uuid4().hex}", output=output, bound=bound
    )
    if _read_cap24_binding(cap24_root) != bound:
        raise ValueError("PAPER_LIQUIDITY_CAP24_SELECTION_CHANGED")
    return {
        "status": "PREPARED",
        "session_started": False,
        "authority": "NONE",
        "lane_id": "LANE_1",
        **market,
        "current_book_admitted_on_both_sides": all(
            check["risk_admitted"] for check in market["liquidity_at_minimum_quantity"].values()
        ),
        "pending": "FRESH_MASTER_V2_DECISION_AND_EXACT_QUANTITY_CHECK",
    }


def preflight_zkp_paper_v1(*, market):
    checks = {side: market.assess_opening_liquidity_v1(side=side) for side in ("BUY", "SELL")}
    return {
        "status": "PREPARED",
        "session_started": False,
        "authority": "NONE",
        "lane_id": market.slot.lane_id,
        "native_instrument_id": market.slot.native_id,
        "instrument_id": market.slot.instrument_id,
        "observed_unix": market.observed_unix,
        "source_hashes": market.source_hashes,
        "allocation_usdc": str(PAPER_ALLOCATION_USDC),
        "valuation_usd": str(PAPER_ALLOCATION_USDC * market.usd_per_usdc),
        "fee_rate": str(PAPER_FEE_RATE),
        "liquidity_at_minimum_quantity": checks,
        "current_book_admitted_on_both_sides": all(row["risk_admitted"] for row in checks.values()),
        "pending": "FRESH_MASTER_V2_DECISION_AND_EXACT_QUANTITY_CHECK",
    }


def _run(
    root, market, *, policy, duration, started_at, deadline, revision, capture, card_assignment=None
):
    session = ZkpPaperEntryV1(
        root=root,
        repo=REPO,
        revision=revision,
        initial_market=market,
        duration=duration,
        slot=market.slot,
    )
    with exclusive_v1(root / ".paper-driver.lock"):
        if card_assignment is not None:
            immutable_json_v1(root / "card-assignment.json", card_assignment.to_dict())
        immutable_json_v1(
            root / "window.json", {"started_at": started_at, "duration_seconds": duration}
        )
        return _drive(
            root, market, session, None, policy, deadline, revision, capture, card_assignment
        )


class _WindowEnded(ValueError):
    pass


def _drive(
    root, market, opening, occupied, policy, deadline, revision, capture, card_assignment=None
):
    folder = None
    session = occupied or opening
    cards = InstrumentCardStreamV1(
        root=root,
        bound=session.bound,
        lane_id=session.slot.lane_id,
        source_mode="PAPER",
        session_id=root.name,
        budget_source=paper_budget_source_v1(lambda: occupied or opening),
        ranking_bound=card_assignment,
    )

    def active():
        return monotonic() < deadline and not (root / "STOP").exists()

    def fill_clock():
        if not active():
            raise _WindowEnded
        return time()

    while active():
        if market is not None:
            try:
                cards.update_v1(market, now=fill_clock())
                with cards.observe_v1():
                    result = (occupied or opening).step_v1(market, clock=fill_clock)
                cards.complete_v1(result)
            except _WindowEnded:
                break
            except (ValueError, TypeError, KeyError, DecimalException) as exc:
                cards.unavailable_v1(exc, now=time())
                result = {"status": "BLOCKED", "reason": str(exc)}
            result_path = root / "initial-result.json" if folder is None else folder / "result.json"
            immutable_json_v1(result_path, result)
            if result["status"] == "FIRST_FILL_BOOKED":
                occupied = ZkpPaperContinuationV1(
                    root=root, repo=REPO, revision=revision, slot=opening.slot
                )
            elif result.get("reason") == "ZKP_PAPER_NON_REVERSAL_EXIT_REQUIRED":
                result = {
                    **result,
                    "last_booking": occupied.last_receipt,
                    "last_funding": occupied.last_funding,
                    "orders_sent": 0,
                    "permits_created": 0,
                    "authority": "NONE",
                }
                immutable_json_v1(root / "closeout.json", result)
                seal_xperp_paper_archive_v1(root, result)
                return result
        sleep(min(_POLL_SECONDS, max(0, deadline - monotonic())))
        if not active():
            break
        poll = uuid4().hex
        folder = root / "public" / poll
        try:
            market = capture(policy, label=f"{root.name}:{poll}", output=folder)
        except (OSError, ValueError, TypeError, KeyError, DecimalException) as exc:
            cards.unavailable_v1(exc, now=time())
            immutable_json_v1(
                folder / "blocked.json", {"reason": str(exc), "observed_unix": time()}
            )
            market = None
    result = {
        "status": "WINDOW_ENDED_OCCUPIED" if occupied else "WINDOW_ENDED_BEFORE_FIRST_FILL",
        "last_booking": occupied.last_receipt if occupied else None,
        "last_funding": occupied.last_funding if occupied else None,
        "orders_sent": 0,
        "permits_created": 0,
        "authority": "NONE",
    }
    cards.unavailable_v1("ORIGINAL_PAPER_WINDOW_ENDED", now=time())
    immutable_json_v1(root / "closeout.json", result)
    seal_xperp_paper_archive_v1(root, result)
    return result


def _resume(root, *, policy, revision, capture, slot=ZKP_PAPER_SLOT, card_assignment=None):
    if not _isolated_root(root).is_dir():
        raise ValueError("ZKP_PAPER_ORIGINAL_RUN_ROOT_REQUIRED")
    with exclusive_v1(root / ".paper-driver.lock"):
        assignment_path = root / "card-assignment.json"
        original_assignment = (
            BoundInstrumentV1(**json.loads(assignment_path.read_bytes()))
            if assignment_path.exists()
            else None
        )
        if card_assignment is not None and card_assignment != original_assignment:
            raise ValueError("PAPER_ORIGINAL_CARD_ASSIGNMENT_CHANGED")
        window = json.loads((root / "window.json").read_bytes())
        duration, started = window["duration_seconds"], window["started_at"]
        now = time()
        if (
            type(duration) is not int
            or not 1 <= duration <= 7200
            or not isinstance(started, (int, float))
            or not isfinite(started)
            or not 0 < started <= now
        ):
            raise ValueError("ZKP_PAPER_ORIGINAL_WINDOW_INVALID")
        closeout = root / "closeout.json"
        if closeout.is_file():
            profile = json.loads((root / "paper-profile.json").read_bytes())
            binding = profile["binding"]
            if (binding["lane_id"], binding["venue_native_id"], binding["instrument_id"]) != (
                slot.lane_id,
                slot.native_id,
                slot.instrument_id,
            ):
                raise ValueError("PAPER_CLOSEOUT_SLOT_MISMATCH")
            result = json.loads(closeout.read_bytes())
            seal_xperp_paper_archive_v1(root, result)
            return result
        occupied = ZkpPaperContinuationV1(root=root, repo=REPO, revision=revision, slot=slot)
        if duration != occupied.profile["duration_seconds"]:
            raise ValueError("ZKP_PAPER_ORIGINAL_WINDOW_INVALID")
        deadline = monotonic() + max(0, started + duration - now)
        return _drive(
            root, None, None, occupied, policy, deadline, revision, capture, original_assignment
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    preflight = modes.add_parser(
        "preflight", help="Read public inputs and check executable liquidity"
    )
    preflight.add_argument("--evidence-root", type=Path)
    preflight.add_argument(
        "--cap24-evidence-root",
        type=Path,
        help="Measure the instrument from the selected future's Cap24 evidence",
    )
    run = modes.add_parser("run", help="Explicitly start the bounded Paper slot")
    run.add_argument("--run-root", required=True, type=Path)
    run.add_argument("--duration-seconds", type=int, default=7200)
    resume = modes.add_parser("resume", help="Resume the original occupied Paper slot")
    resume.add_argument("--run-root", required=True, type=Path)
    for mode in (run, resume):
        mode.add_argument(
            "--card-cap24-evidence-root",
            type=Path,
            help="Carry an existing verified Cap24 selection into the card; no new selection",
        )
    for mode in (preflight, run, resume):
        mode.add_argument(
            "--slot-config", type=Path, help="Use the prepared UP (LANE_2) or IRYS (LANE_4) binding"
        )
    args = parser.parse_args(argv)
    try:
        policy = load_paper_liquidity_policy_v1(REPO)
        slot = ZKP_PAPER_SLOT if args.slot_config is None else _read_paper_slot(args.slot_config)
        capture = _capture if args.slot_config is None else partial(_capture, slot=slot)
        if args.mode == "preflight":
            if args.cap24_evidence_root is not None and args.slot_config is not None:
                raise ValueError("PAPER_PREFLIGHT_REQUIRES_ONE_BINDING_SOURCE")
            output = None if args.evidence_root is None else _new_root(args.evidence_root)
            if output is not None:
                output.mkdir(mode=0o700)
            if args.cap24_evidence_root is None:
                market = capture(
                    policy, label=f"{slot.lane_id}-paper-input-preflight", output=output
                )
                result = preflight_zkp_paper_v1(market=market)
            else:
                result = _preflight_cap24(
                    policy, cap24_root=args.cap24_evidence_root, output=output
                )
            if output is not None:
                immutable_json_v1(output / "preflight.json", result)
        else:
            card_assignment = (
                None
                if args.card_cap24_evidence_root is None
                else _read_cap24_binding(args.card_cap24_evidence_root)
            )
            if card_assignment is not None and (
                card_assignment.instrument_id,
                card_assignment.venue_native_id,
            ) != (slot.instrument_id, slot.native_id):
                raise ValueError("PAPER_CARD_CAP24_SLOT_MISMATCH")
            revision = subprocess.check_output(
                ["git", f"--work-tree={REPO}", "rev-parse", "HEAD"],
                cwd=REPO,
                text=True,
            ).strip()
            if args.mode == "resume":
                result = _resume(
                    args.run_root,
                    policy=policy,
                    revision=revision,
                    capture=capture,
                    slot=slot,
                    card_assignment=card_assignment,
                )
            else:
                root = _new_root(args.run_root)
                if not 1 <= args.duration_seconds <= 7200:
                    raise ValueError("ZKP_PAPER_WINDOW_INVALID")
                started_at = time()
                deadline = monotonic() + args.duration_seconds
                # Retain the original public FX and market data before creating the slot.
                initial_root = root.with_name(root.name + "-inputs")
                _new_root(initial_root).mkdir(mode=0o700)
                market = capture(policy, label=f"{root.name}:0", output=initial_root)
                if monotonic() >= deadline:
                    raise ValueError("ZKP_PAPER_WINDOW_ENDED_DURING_PREFLIGHT")
                result = _run(
                    root,
                    market,
                    policy=policy,
                    duration=args.duration_seconds,
                    started_at=started_at,
                    deadline=deadline,
                    revision=revision,
                    capture=capture,
                    card_assignment=card_assignment,
                )
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, DecimalException) as exc:
        parser.exit(2, f"Paper stopped: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
