import subprocess
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts/ops/sha256sums_style_guard_v1.sh"

def run(cmd, **kw):
    return subprocess.run(cmd, text=True, capture_output=True, **kw)

def test_guard_ok_on_repo_root_relative_format(tmp_path):
    sha = tmp_path / "SHA256SUMS.txt"
    sha.write_text("0"*64 + "  out/ops/x.txt\n", encoding="utf-8")
    r = run(["bash", str(GUARD), str(sha)])
    assert r.returncode == 0, r.stdout + r.stderr

def test_guard_rejects_absolute_path(tmp_path):
    sha = tmp_path / "SHA256SUMS.txt"
    sha.write_text("0"*64 + "  /abs/x.txt\n", encoding="utf-8")
    r = run(["bash", str(GUARD), str(sha)])
    assert r.returncode == 3, r.stdout + r.stderr

def test_guard_rejects_parent_path(tmp_path):
    sha = tmp_path / "SHA256SUMS.txt"
    sha.write_text("0"*64 + "  ../x.txt\n", encoding="utf-8")
    r = run(["bash", str(GUARD), str(sha)])
    assert r.returncode == 3, r.stdout + r.stderr
