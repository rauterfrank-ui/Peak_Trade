"""Independent public observer for ranked UP Paper. prepare and compare are offline.

prepare --slot-config SLOT
record --slot-config SLOT --seconds N --output NEW.jsonl
compare --recording FILE.jsonl --booked-result PUBLIC_POLL/result.json

Invoke with scripts/pt scripts/ops/up_paper_ws_depth_v1.py. Only record opens a
socket. Record on the Paper host so both local receipt clocks have the same
origin. A disconnect ends the file. Each new file requires its own subscriptions
and initial book snapshot. Raw frames retain exchange time and both host clocks.

compare reads a closed Paper archive and a single matching recording. Its
window starts at the blocked signal's market observation and ends before the
original execution-input mark. It replays the full books stream, projects the
first 50 levels per side and applies the Paper liquidity owner to the original
native reversal quantity and same-day ADV. A pass describes observed liquidity.
Sizing, candle availability, fees, funding and confirmed booking have separate
inputs. Mark pushes have no contiguous sequence. Unobserved intrapush changes
and the offset between exchange and host clocks remain unknown.
"""

import argparse
import json
import platform
import sys
import time
from contextlib import ExitStack, closing
from hashlib import sha256
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ops.ranked_slot_run_source_v1 import (
    read_paper_entry_admission_v1,
    read_ranked_paper_slot_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_case_v1 import (
    load_reversal_window,
    paper_identity,
)
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_replay_v1 import (
    compare_recording,
    sealed_digest,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import UP_PAPER_SLOT
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    load_ratified_eea_public_ws_binding_v1,
)


def preparation(args):
    config = json.loads(args.slot_config.read_bytes())
    if (config["surface"], config["canonical_instrument_id"], config["native_instrument_id"]) != (
        "PAPER_EXCHANGE",
        UP_PAPER_SLOT.instrument_id,
        UP_PAPER_SLOT.native_id,
    ):
        raise ValueError("ranked UP dated future on PAPER required")
    assignment, slot = read_ranked_paper_slot_v1(config)
    admission = read_paper_entry_admission_v1(config, assignment)
    if "paper_cap24" in config:
        from scripts.ops.run_zkp_lane1_paper_v1 import (
            _read_cap24_binding,
            _verify_renewed_paper_cap24,
        )

        root = Path(config["paper_cap24"]["root"])
        bound = _read_cap24_binding(root, entry_repository_sha=assignment.selection.repository_sha)
        admission.require_binding_v1(bound)
        if "paper_entry_admission" in config:
            _verify_renewed_paper_cap24(config, root, assignment, admission, bound)
    identity = paper_identity(
        slot,
        config["session_id"],
        assignment.selection.integrity_digest,
        admission.selection.integrity_digest,
    )
    return subscription_plan(identity)


def subscription_plan(identity):
    binding = load_ratified_eea_public_ws_binding_v1()
    return dict(
        schema="up_paper_joint_depth.v1",
        identity=identity,
        endpoint=binding.ws_base_url,
        subscriptions=[
            dict(channel=channel, instId=identity["native_id"])
            for channel in (binding.public_channel_mark_price, "books")
        ],
    )


def record(plan, output, seconds, *, connect=None, timeout_error=TimeoutError):
    if not 1 <= seconds <= 7200:
        raise ValueError("observation duration must be between 1 and 7200 seconds")
    source = "offline_fixture"
    transport_version = None
    if connect is None:
        from websocket import WebSocketTimeoutException, __version__, create_connection
        from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
            assert_http_client_proxy_env_clean_v1,
        )

        assert_http_client_proxy_env_clean_v1()
        connect, timeout_error = create_connection, WebSocketTimeoutException
        source, transport_version = "public_websocket", __version__
    digest = sha256()
    with output.open("xb") as stream, ExitStack() as resources:

        def write(kind, **fields):
            line = (json.dumps(dict(kind=kind, **fields), allow_nan=False) + "\n").encode()
            stream.write(line)
            stream.flush()
            digest.update(line)

        def clocks():
            return dict(received_ns=time.time_ns(), received_mono_ns=time.monotonic_ns())

        write(
            "start",
            **plan,
            source=source,
            transport_version=transport_version,
            clock_host=platform.node(),
            **clocks(),
        )
        frames = 0
        status = "interrupted"
        try:
            ws = resources.enter_context(
                closing(
                    connect(plan["endpoint"], timeout=10, redirect_limit=0, suppress_origin=True)
                )
            )
            if ws.getstatus() != 101:
                raise ValueError("public WebSocket handshake rejected")
            ws.send(json.dumps(dict(op="subscribe", args=plan["subscriptions"])))
            deadline_ns = time.monotonic_ns() + seconds * 10**9
            while (remaining_ns := deadline_ns - time.monotonic_ns()) > 0:
                ws.settimeout(min(15, remaining_ns / 10**9))
                try:
                    raw = ws.recv()
                except timeout_error:
                    if time.monotonic_ns() >= deadline_ns:
                        break
                    if remaining_ns <= 15 * 10**9:
                        continue
                    raise ValueError("public WebSocket silent")
                stamp = clocks()
                if not isinstance(raw, str) or not raw:
                    raise ValueError("public WebSocket disconnected or non-text frame")
                frames += 1
                write("frame", frame=frames, raw=raw, **stamp)
                if raw != "pong" and json.loads(raw).get("event") == "error":
                    raise ValueError("public subscription rejected (see original frame)")
            status = "duration_elapsed"
        except Exception as exc:
            status = str(exc) or type(exc).__name__
            raise
        finally:
            footer = dict(frames=frames, status=status, **clocks())
            write("end", **footer, content_sha256=sealed_digest(digest, footer))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "record", "compare"):
        sub = commands.add_parser(name)
        if name != "compare":
            sub.add_argument("--slot-config", type=Path, required=True)
        if name == "record":
            sub.add_argument("--seconds", type=int, required=True)
            sub.add_argument("--output", type=Path, required=True)
        if name == "compare":
            sub.add_argument("--recording", type=Path, required=True)
            sub.add_argument("--booked-result", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "compare":
        identity, window = load_reversal_window(args.booked_result, REPO)
        print(
            json.dumps(
                compare_recording(args.recording, subscription_plan(identity), window), indent=2
            )
        )
        return
    plan = preparation(args)
    if args.command == "record":
        record(plan, args.output, args.seconds)
    else:
        print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
