import json
import subprocess
import sys

PY = sys.executable


def run_cli(args):
    p = subprocess.run(
        [PY, "-m", "src.execution.networked.onramp_cli_v1", *args],
        capture_output=True,
        text=True,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def parse_stdout(out):
    return json.loads(out) if out else {}


def test_transport_allow_yes_requires_allowlist_yes_and_match():
    # allowlist NO -> rc=2 (allowlist denied before transport)
    rc, out, _ = run_cli(
        [
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
            "--allowlist-allow",
            "NO",
            "--transport-allow",
            "YES",
        ]
    )
    assert rc == 2
    j = parse_stdout(out)
    assert j["allowlist"]["rc"] == 1

    # allowlist YES empty -> rc=2
    rc, out, _ = run_cli(
        [
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
            "--allowlist-allow",
            "YES",
            "--allowlist-adapters",
            "",
            "--allowlist-markets",
            "",
            "--transport-allow",
            "YES",
        ]
    )
    assert rc == 2
    j = parse_stdout(out)
    assert j["allowlist"]["rc"] == 1


def test_transport_allow_yes_after_allowlist_still_networkless_default_deny():
    # allowlist pass + transport_allow YES -> transport ok (gate), but adapter still denies (no real send)
    rc, out, _ = run_cli(
        [
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
            "--allowlist-allow",
            "YES",
            "--allowlist-adapters",
            "networked_stub",
            "--allowlist-markets",
            "BTC-USD",
            "--transport-allow",
            "YES",
        ]
    )
    # rc stays 0 by convention; adapter.rc=1 indicates send denied
    assert rc == 0
    j = parse_stdout(out)
    assert j["allowlist"]["rc"] == 0
    assert j["transport_gate"]["transport_allow"] == "YES"
    assert j["adapter"]["rc"] == 1


def test_cli_rejects_transport_allow_yes_in_live_mode():
    # CLI accepts --mode live so guards can reject deterministically
    rc, out, _ = run_cli(
        [
            "--mode",
            "live",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
            "--transport-allow",
            "YES",
        ]
    )
    assert rc != 0
    j = parse_stdout(out)
    # either entry_guard or gate guard rejects
    assert "guards" in j or "allowlist" in j or "transport" in j or "error" in j
