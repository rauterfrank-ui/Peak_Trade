from pathlib import Path
import os
import stat
import subprocess


def test_stop_playbook_exists_and_is_executable():
    p = Path("scripts/ops/p101_stop_playbook_v1.sh")
    assert p.exists()
    st = p.stat()
    assert (st.st_mode & stat.S_IXUSR) != 0


def test_stop_playbook_bash_syntax_ok():
    p = Path("scripts/ops/p101_stop_playbook_v1.sh")
    subprocess.check_call(["bash", "-n", str(p)])


def test_stop_playbook_refuses_deny_vars(monkeypatch, tmp_path):
    # Fast path: set a deny var and expect exit 3 without doing real launchctl work.
    monkeypatch.setenv("LIVE", "1")
    monkeypatch.setenv("TS_OVERRIDE", "20990101T000000Z")
    monkeypatch.setenv("EVI_OVERRIDE", str(tmp_path / "evi"))
    r = subprocess.run(
        ["bash", "scripts/ops/p101_stop_playbook_v1.sh"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 3
