"""Prepare one bounded UP Paper run and evaluate its independent public recording offline.

plan writes JSON to stdout and starts no process. The commands in a bound plan
are for a later authorized run on one host. report operates on finished files.
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.run_zkp_lane1_paper_v1 import _new_root
from scripts.ops.up_paper_ws_depth_v1 import preparation, subscription_plan
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_case_v1 import (
    archive_identity,
    load_reversal_window,
    read_confirmed_reversal,
)
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_replay_v1 import (
    Pair,
    _read_recording,
    compare_recording,
)
from src.ops.bounded_peaktrade_system_composition_v1.xperp_paper_episode_outcome_v1 import _Archive
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import UP_PAPER_SLOT
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.ranked_slot_run_source_v1 import read_ranked_paper_slot_v1

CONFIRMATION_DIR = "PEAK_TRADE_UP_PAPER_CONFIRMATION_DIR"
MS = 1_000_000


def prepare(args, *, now):
    session, seconds = args.session, args.seconds
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", session) or not 1 <= seconds <= 7140:
        raise ValueError("new session id and a bounded Paper window of 1..7140 seconds required")
    parent = args.parent.resolve(strict=True)
    root = _new_root(parent / session)
    _new_root(parent / (session + "-inputs"))
    evidence = _new_root(parent / (session + "-measurement"))
    capture = evidence / "public.jsonl"
    result = dict(
        schema="up_paper_measurement_plan.v1",
        authority="NONE",
        session_started=False,
        session=session,
        instrument=UP_PAPER_SLOT.native_id,
        paper_seconds=seconds,
        recorder_seconds=seconds + 60,
        paper_root=str(root),
        evidence_root=str(evidence),
        target_ms=300,
        slot_config=str(args.slot_config) if args.slot_config else None,
        status="AWAITING_SESSION_BOUND_PAPER_SLOT_AND_CAP24",
        parallel_commands=None,
    )
    if not args.slot_config or not args.slot_config.is_file():
        return result
    config = json.loads(args.slot_config.read_bytes())
    if config["session_id"] != session:
        raise ValueError("historical or foreign session cannot supply the next run")
    if not config.get("paper_cap24"):
        return result
    bound = preparation(args, current_at=now)
    launcher = str(REPO / "scripts/pt")
    tools_dir = REPO / "scripts/ops"
    result.update(
        status="OFFLINE_INPUTS_BOUND",
        identity=bound["identity"],
        parallel_commands=dict(
            recorder=[
                launcher,
                str(tools_dir / "up_paper_ws_depth_v1.py"),
                "record",
                "--slot-config",
                str(args.slot_config.resolve()),
                "--seconds",
                str(seconds + 60),
                "--output",
                str(capture),
            ],
            paper=[
                launcher,
                str(tools_dir / "run_zkp_lane1_paper_v1.py"),
                "run",
                "--run-root",
                str(root),
                "--slot-config",
                str(args.slot_config.resolve()),
                "--card-cap24-evidence-root",
                config["paper_cap24"]["root"],
                "--duration-seconds",
                str(seconds),
            ],
            paper_environment={
                CONFIRMATION_DIR: str(evidence / "confirmations"),
                "PEAK_TRADE_NONLIVE_TIMING_STAGES": "0",
            },
        ),
    )
    return result


def await_public_pair(process, path, plan, tick, lot, deadline):
    pair = Pair(plan, tick, lot)
    header = False
    with path.open("rb") as stream:
        while time.monotonic() < deadline and process.poll() is None:
            offset = stream.tell()
            line = stream.readline()
            if not line.endswith(b"\n"):
                stream.seek(offset)
                time.sleep(0.05)
                continue
            row = json.loads(line)
            if not header:
                if (
                    row.get("kind") != "start"
                    or row.get("source") != "public_websocket"
                    or any(row.get(k) != v for k, v in plan.items())
                ):
                    raise ValueError("wrong public recording")
                header = True
                continue
            if row["kind"] != "frame":
                break
            pair.accept(row["raw"], row["received_ns"], row["frame"])
            if pair.terminal:
                raise ValueError(pair.terminal)
            if pair.unavailable(0) is None and all(
                time.time_ns() < obs.until(ch) for ch, obs in pair.data.items()
            ):
                return
    raise ValueError("no fresh jointly observed UP mark and book within recorder lead time")


def start_prepared(args):
    # This entry point is deliberately separate from plan. No process exists until
    # current entry originals have passed the same Paper binding used by the driver.
    packet = prepare(args, now=time.time())
    commands = packet["parallel_commands"]
    if commands is None:
        raise ValueError(packet["status"])
    config = json.loads(args.slot_config.read_bytes())
    assignment, _ = read_ranked_paper_slot_v1(config)
    evidence = Path(packet["evidence_root"])
    evidence.mkdir(mode=0o700)
    (evidence / "bound-plan.json").write_text(json.dumps(packet, indent=2) + "\n")
    path = evidence / "public.jsonl"
    env = dict(os.environ, GIT_WORK_TREE=str(REPO))
    env.pop("PEAK_TRADE_NONLIVE_TIMING_DIR", None)
    with (
        (evidence / "recorder.log").open("xb") as wslog,
        (evidence / "paper.log").open("xb") as paperlog,
    ):
        started = time.monotonic()
        recorder = subprocess.Popen(
            commands["recorder"], cwd=REPO, env=env, stdout=wslog, stderr=subprocess.STDOUT
        )
        try:
            deadline = time.monotonic() + 30
            while not path.is_file() and recorder.poll() is None and time.monotonic() < deadline:
                time.sleep(0.05)
            await_public_pair(
                recorder,
                path,
                subscription_plan(packet["identity"]),
                Decimal(assignment.instrument.tick_size),
                Decimal(assignment.instrument.lot_size),
                deadline,
            )
            subprocess.run(
                commands["paper"],
                cwd=REPO,
                check=True,
                stdout=paperlog,
                stderr=subprocess.STDOUT,
                env=dict(env, **commands["paper_environment"]),
            )
            rc = recorder.wait(
                timeout=max(0, started + packet["recorder_seconds"] + 45 - time.monotonic())
            )
            if rc:
                raise RuntimeError(f"public recorder exited with status {rc}; retained evidence")
        finally:
            if recorder.poll() is None:
                recorder.send_signal(signal.SIGINT)
                try:
                    recorder.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    recorder.kill()
                    recorder.wait()
    return dict(
        session=packet["session"],
        session_started=True,
        status="PROCESSES_EXITED",
        paper_root=packet["paper_root"],
        evidence_root=packet["evidence_root"],
    )


def confirmed_timing(receipt, *, result, plan, identity, signal_ms, execution_ms):
    expected = dict(
        schema="up_paper_confirmed.v1",
        session=identity["session"],
        lane=identity["lane"],
        native_id=identity["native_id"],
        binding_digest=identity["binding_digest"],
        cycle_id=plan["cycle_id"],
        decision_id=result["decision_id"],
        fill_id=result["fill"]["fill_id"],
        result_digest=canonical_digest_v1(result),
        execution_mark_sha256=plan["source_hashes"]["mark"],
    )
    if any(receipt.get(k) != v for k, v in expected.items()):
        raise ValueError("confirmation and original booking differ")
    end, mono = receipt["confirmed_ns"], receipt["confirmed_mono_ns"]
    if (
        type(end) is not int
        or type(mono) is not int
        or mono <= 0
        or not receipt["clock_host"]
        or not 0 < signal_ms <= execution_ms
        or execution_ms * MS > end
        or Decimal(str(result["fill"]["event_time_unix"])) * 10**9 > end
    ):
        raise ValueError("booking confirmation clocks inconsistent")
    return dict(
        signal_mark_to_confirmation_ms=(end - signal_ms * MS) / MS,
        within_300ms_from_signal=end - signal_ms * MS <= 300 * MS,
        execution_mark_to_confirmation_ms=(end - execution_ms * MS) / MS,
        within_300ms_from_execution=end - execution_ms * MS <= 300 * MS,
        confirmed_ns=end,
        confirmed_mono_ns=mono,
        clock_host=receipt["clock_host"],
    )


def matched_ws_ms(candidates, header, timing, expected_px):
    if (
        header["clock_host"] != timing["clock_host"]
        or not header["from_ns"] <= timing["confirmed_ns"] <= header["until_ns"]
    ):
        return None
    seen = [
        (px, mono)
        for px, wall, mono in candidates
        if wall <= timing["confirmed_ns"] and mono <= timing["confirmed_mono_ns"]
    ]
    if not seen or {px for px, _ in seen} != {Decimal(expected_px)}:
        return None
    return (timing["confirmed_mono_ns"] - seen[0][1]) / MS


def report(root, evidence):
    root = root.resolve(strict=True)
    closeout = json.loads((root / "closeout.json").read_bytes())
    if not (root / "MANIFEST.sha256").is_file():
        return dict(
            session=root.name,
            status="NO_SEALED_REVERSAL_ARCHIVE",
            closeout=closeout.get("status"),
            confirmed_booking_count=None,
            within_300ms=None,
        )
    archive = _Archive(root)
    identity = archive_identity(archive)
    subscriptions = subscription_plan(identity)
    # Enumerate the original owner's manifest, so a missing observation stays in the denominator.
    rows = {
        rel: dict(booking_sha256=digest, timing=None, earlier_liquidity=None)
        for rel, digest in archive.pins.items()
        if rel.startswith("reversals/")
    }
    by_parent = defaultdict(list)
    for path in (root / "public").glob("*/result.json"):
        result = json.loads(path.read_bytes())
        if result.get("status") == "NET_REVERSAL_BOOKED":
            by_parent[f"reversals/{result['previous_episode_id']}.json"].append(path)
    requested = set()
    for rel, row in rows.items():
        if len(by_parent[rel]) != 1:
            row["missing"] = "unique original booked poll"
            continue
        path = by_parent[rel][0]
        result, plan, mark, signal, booking_hash = read_confirmed_reversal(archive, path, identity)
        execution = int(mark["ts"])
        row.update(
            decision_id=result["decision_id"],
            signal_ms=signal,
            execution_ms=execution,
            execution_px=mark["markPx"],
            signal_px=mark["markPx"] if signal == execution else None,
        )
        requested.update((signal, execution))
        confirmation = (
            evidence
            / "confirmations"
            / (canonical_digest_v1({"fill_id": result["fill"]["fill_id"]}) + ".json")
        )
        if confirmation.is_file():
            row["timing"] = confirmed_timing(
                json.loads(confirmation.read_bytes()),
                result=result,
                plan=plan,
                identity=identity,
                signal_ms=signal,
                execution_ms=execution,
            )
        else:
            row["missing"] = "original confirmation timestamp"
        if signal < execution:
            try:
                _, window = load_reversal_window(path, REPO)
                row["signal_px"] = str(window.liquidity.mark)
                if (evidence / "public.jsonl").is_file():
                    row["earlier_liquidity"] = compare_recording(
                        evidence / "public.jsonl", subscriptions, window
                    )
            except (OSError, ValueError, KeyError) as exc:
                row["earlier_evidence_error"] = str(exc)
    marks = defaultdict(list)
    header = None
    ws_error = None
    try:
        contract = archive.profile["contract"]
        pair = Pair(subscriptions, Decimal(contract["tick_size"]), Decimal(contract["min_qty"]))

        def observe(previous, now, mono, index, raw):
            pair.accept(raw, now, index)
            mark = pair.data.get("mark-price")
            if mark and mark.frame == index and mark.event_ms in requested:
                marks[mark.event_ms].append((mark.value, now, mono))

        header = _read_recording(
            evidence / "public.jsonl",
            subscriptions,
            on_start=lambda _: None,
            on_frame=observe,
            on_end=lambda *_: None,
        )
        header["protocol_error"] = pair.terminal
        header["acknowledged"] = sorted(pair.acked)
    except (OSError, ValueError, KeyError) as exc:
        ws_error = str(exc)
    timings = []
    for row in rows.values():
        timing = row["timing"]
        if timing is None:
            continue
        timings.append(timing)
        for label in ("signal", "execution"):
            px = row[label + "_px"]
            timing["ws_" + label + "_receipt_to_confirmation_ms"] = (
                matched_ws_ms(marks[row[label + "_ms"]], header, timing, px)
                if header and header["source"] == "public_websocket" and px is not None
                else None
            )
    return dict(
        session=root.name,
        identity=identity,
        closed_status=closeout["status"],
        target_ms=300,
        clock_basis="exchange event to host UTC confirmation (offset unmeasured); WS receipt intervals use the same host monotonic clock",
        confirmed_booking_count=len(rows),
        measurable=len(timings),
        within_300ms_from_signal=sum(t["within_300ms_from_signal"] for t in timings),
        within_300ms_from_execution=sum(t["within_300ms_from_execution"] for t in timings),
        recording=header,
        recording_error=ws_error,
        bookings=list(rows.values()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    for name in ("plan", "start"):
        plan = subs.add_parser(name)
        plan.add_argument("--session", required=True)
        plan.add_argument("--parent", type=Path, required=True)
        plan.add_argument("--slot-config", type=Path, required=name == "start")
        plan.add_argument("--seconds", type=int, default=3600)
    analyze = subs.add_parser("report")
    analyze.add_argument("--run-root", type=Path, required=True)
    analyze.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "plan":
        result = prepare(args, now=time.time())
    elif args.action == "start":
        result = start_prepared(args)
    else:
        result = report(args.run_root, args.evidence)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
