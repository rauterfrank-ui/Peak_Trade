"""Inspect real process death without upgrading the known reservation gap."""

import json
from pathlib import Path
import signal
import subprocess
import time

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("quantity", ["1", "-2"])
def test_process_restart_restores_topology_but_not_capital_reservations(tmp_path, quantity):
    command = [
        str(REPO / "scripts/pt"),
        "-m",
        "tests.ops._reservation_custody_restart_probe_v1",
        str(tmp_path),
    ]
    marker = tmp_path / "probe_before.json"
    with (tmp_path / "stdout").open("w") as out, (tmp_path / "stderr").open("w") as err:
        process = subprocess.Popen([*command, "before", quantity], cwd=REPO, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 15
            while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.03)
            assert marker.exists(), (tmp_path / "stderr").read_text()
            process.send_signal(signal.SIGKILL)
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    before = json.loads(marker.read_text())
    assert before["active_sum"] == "60" and before["reservation_count"] == 1
    assert before["reservation_state"] == "COMMITTED"
    assert before["canonical_restart_reconstructable"] is False
    after = subprocess.run(
        [*command, "after", quantity], cwd=REPO, capture_output=True, text=True, timeout=15
    )
    assert after.returncode == 0, after.stderr
    result = json.loads(after.stdout.splitlines()[-1])
    assert result["mapping"] == before["mapping"]
    assert result["custody_retained_same_lane"] is True
    assert result["unadmitted_after_restart"] is True
    assert result["active_sum_after_independent_fact"] == "0"
    assert result["reservation_count_after_independent_fact"] == 0
    assert result["budget_after_independent_fact"] == "100.00"
    assert result["canonical_restart_reconstructable"] is False
    # The zero in a fresh in-memory owner is NOT evidence that old obligations
    # have been reconciled/released. The test deliberately preserves this gap.
