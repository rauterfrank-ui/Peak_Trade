import re
import subprocess
from pathlib import Path


def test_run_end_to_end_verification_syntax():
    p = Path("scripts/ops/run_end_to_end_verification.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)


def test_run_end_to_end_verification_network_marker_contract_v0() -> None:
    """Static owner-review surface for E2E verification network/CLI markers.

    Reads the script as text only. It must not execute the script, run gh/aws,
    dispatch workflows, call network/API endpoints, or touch runtime paths.
    """
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "ops" / "run_end_to_end_verification.sh"
    source = script.read_text(encoding="utf-8")
    lowered = source.lower()

    assert script.exists()
    assert "run_end_to_end_verification.sh" in str(script)
    assert "gh " in source
    assert "aws" in lowered or "AWS" in source
    assert "workflow" in lowered or "verification" in lowered
    assert "runtime" in lowered or "testnet" in lowered or "live" in lowered
    assert "set -euo pipefail" in source
    assert "gh workflow view" in lowered
    assert "gh workflow run" in lowered

    forbidden_dispatch_or_network_mutation_patterns = [
        "gh run rerun",
        "gh api repos/",
        "curl" + " ",
        "wget" + " ",
    ]
    found = [
        pattern for pattern in forbidden_dispatch_or_network_mutation_patterns if pattern in lowered
    ]
    assert not found, (
        "run_end_to_end_verification network-marker contract should not gain "
        f"rerun/API-repo mutation or direct HTTP download surfaces: {found}"
    )

    test_source = Path(__file__).read_text(encoding="utf-8")
    marker = "def test_run_end_to_end_verification_network_marker_contract_v0"
    start = test_source.find(marker)
    assert start != -1
    tail = test_source[start:]
    after_sig = tail[len(marker) :]
    next_fn = re.search(r"\n^def test_", after_sig, re.MULTILINE)
    contract_src = tail[: len(marker) + next_fn.start()] if next_fn else tail

    forbidden_test_fragments = [
        "subprocess" + ".",
        "os" + ".system",
        "runpy" + ".",
        "importlib" + ".import_module",
        "requests" + ".",
        "httpx" + ".",
        "urllib" + ".",
        "socket" + ".",
        "aws " + " ",
    ]
    test_hits = [fragment for fragment in forbidden_test_fragments if fragment in contract_src]
    assert not test_hits, (
        "static run_end_to_end_verification network-marker contract must not use "
        f"execution/network hooks: {test_hits}"
    )
