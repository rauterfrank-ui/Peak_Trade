from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "governance" / "verify_transitive_evidence_manifests_v0.py"


def _sha256(path: Path) -> str:
    proc = subprocess.run(
        ["shasum", "-a", "256", str(path)],
        capture_output=True,
        text=True,
        shell=False,
        check=True,
    )
    # format: "<hex>  <path>"
    return proc.stdout.strip().split()[0]


def _write_manifest(root: Path) -> None:
    lines: list[str] = []
    for p in sorted([p for p in root.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"]):
        rel = p.relative_to(root).as_posix()
        lines.append(f"{_sha256(p)}  {rel}")
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _bundle(archive_root: Path, name: str) -> Path:
    d = archive_root / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _snapshot_bytes(root: Path) -> dict[str, bytes]:
    snap: dict[str, bytes] = {}
    for p in sorted([p for p in root.rglob("*") if p.is_file()]):
        snap[str(p)] = p.read_bytes()
    return snap


def _assert_snapshot_unchanged(before: dict[str, bytes], after_root: Path) -> None:
    after = _snapshot_bytes(after_root)
    assert set(before.keys()) == set(after.keys())
    for k in before:
        assert before[k] == after[k]


def test_import_side_effect_free() -> None:
    # Import must not execute subprocesses or write files.
    proc = subprocess.run(
        [sys.executable, "-c", "import scripts.governance.verify_transitive_evidence_manifests_v0 as m; print('OK')"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        shell=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_canonicalize_bundle_reference_normalizations(tmp_path: Path) -> None:
    from scripts.governance.verify_transitive_evidence_manifests_v0 import canonicalize_bundle_reference

    archive = tmp_path / "archive"
    archive.mkdir()
    a = _bundle(archive, "A")

    # trailing slash
    d = canonicalize_bundle_reference(str(a) + "/", archive_root=archive)
    assert d.canonical_dir == str(a.absolute())

    # backticks
    d = canonicalize_bundle_reference(f"`{a}`", archive_root=archive)
    assert d.canonical_dir == str(a.absolute())

    # quotes + whitespace
    d = canonicalize_bundle_reference(f"  \"{a}\"  ", archive_root=archive)
    assert d.canonical_dir == str(a.absolute())

    # trailing punctuation (non-existing with punctuation, existing without)
    d = canonicalize_bundle_reference(str(a) + ").", archive_root=archive)
    assert d.canonical_dir == str(a.absolute())

    # MANIFEST file ref
    (a / "MANIFEST.sha256").write_text("", encoding="utf-8")
    d = canonicalize_bundle_reference(str(a / "MANIFEST.sha256"), archive_root=archive)
    assert d.canonical_dir == str(a.absolute())

    # normal file ignored
    (a / "x.txt").write_text("x", encoding="utf-8")
    d = canonicalize_bundle_reference(str(a / "x.txt"), archive_root=archive)
    assert d.canonical_dir is None

    # relative blocked
    d = canonicalize_bundle_reference("relative/path", archive_root=archive)
    assert d.canonical_dir is None

    # outside-root blocked
    outside = tmp_path / "outside"
    outside.mkdir()
    d = canonicalize_bundle_reference(str(outside), archive_root=archive)
    assert d.canonical_dir is None

    # url ignored
    d = canonicalize_bundle_reference("https://example.com/foo", archive_root=archive)
    assert d.canonical_dir is None


def test_cli_fixture_smoke_bfs_checkpoint_resume_and_append_only_log(tmp_path: Path) -> None:
    # Arrange synthetic archive
    archive = tmp_path / "archive"
    archive.mkdir()
    out = tmp_path / "out"
    out.mkdir()

    a = _bundle(archive, "A")
    b = _bundle(archive, "B")
    c = _bundle(archive, "C")
    d = _bundle(archive, "D")
    e = _bundle(archive, "E")

    # Minimal content files
    (a / "final_report.txt").write_text("", encoding="utf-8")
    (b / "final_report.txt").write_text("", encoding="utf-8")
    (c / "final_report.txt").write_text("", encoding="utf-8")
    (d / "final_report.txt").write_text("", encoding="utf-8")
    (e / "final_report.txt").write_text("", encoding="utf-8")

    # References:
    # A -> B, D, E (plus duplicate forms)
    (a / "references.txt").write_text(
        "\n".join(
            [
                str(b) + "/",
                f"`{b}`",
                f"\"{d}\"",
                str(e) + ").",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    # B -> C
    (b / "references.txt").write_text(str(c) + "\n", encoding="utf-8")
    # C -> A (cycle)
    (c / "references.txt").write_text(str(a) + "\n", encoding="utf-8")
    # D -> D (self)
    (d / "references.txt").write_text(str(d) + "\n", encoding="utf-8")
    # E no references
    (e / "references.txt").write_text("", encoding="utf-8")

    # Manifests: A/B/C/D valid, E invalid (missing)
    for root in (a, b, c, d):
        (root / "payload.txt").write_text(root.name, encoding="utf-8")
        _write_manifest(root)

    # Snapshot source bundles (must remain byte-identical)
    before = _snapshot_bytes(archive)

    # Run 1
    progress = out / "progress.jsonl"
    proc1 = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root-bundle",
            str(a),
            "--archive-root",
            str(archive),
            "--output-dir",
            str(out),
            "--max-unique-bundles",
            "10",
            "--max-queue-size",
            "10",
            "--max-references-per-bundle",
            "50",
            "--progress-log",
            str(progress),
        ],
        capture_output=True,
        text=True,
        shell=False,
    )
    assert proc1.returncode == 1  # E missing manifest -> failure visible

    # Ensure output artifacts exist
    assert (out / "run_contract.json").is_file()
    assert (out / "bundle_results.jsonl").is_file()
    assert (out / "graph_summary.json").is_file()
    assert (out / "checkpoint.json").is_file()
    assert progress.is_file()
    assert (out / "final_report.txt").is_file()

    # BFS determinism: A then B then D then E then C (A references sorted: B, D, E; then B enqueues C)
    keys = [json.loads(line)["canonical_key"] for line in (out / "bundle_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert keys[0].endswith("/A")
    assert keys[1].endswith("/B")
    assert keys[2].endswith("/D")
    assert keys[3].endswith("/E")
    assert keys[4].endswith("/C")

    # Self-reference does not requeue and cycle terminates (no duplicate keys)
    assert len(keys) == len(set(keys))

    # Append-only progress has RUN_BEGIN and RUN_FAILED
    prog_lines = progress.read_text(encoding="utf-8").splitlines()
    assert any('"event_type": "RUN_BEGIN"' in l for l in prog_lines)
    assert any('"event_type": "RUN_FAILED"' in l or '"event_type": "RUN_COMPLETE"' in l for l in prog_lines)

    # Source unchanged
    _assert_snapshot_unchanged(before, archive)

    # Run 2 (resume)
    before2 = _snapshot_bytes(archive)
    proc2 = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root-bundle",
            str(a),
            "--archive-root",
            str(archive),
            "--output-dir",
            str(out),
            "--resume-checkpoint",
            str(out / "checkpoint.json"),
            "--max-unique-bundles",
            "10",
            "--max-queue-size",
            "10",
            "--max-references-per-bundle",
            "50",
            "--progress-log",
            str(progress),
        ],
        capture_output=True,
        text=True,
        shell=False,
    )
    assert proc2.returncode in (0, 1)  # resume may find nothing new; still must not crash
    _assert_snapshot_unchanged(before2, archive)

    # Append-only: second run adds another RUN_BEGIN block (no truncation)
    prog_lines2 = progress.read_text(encoding="utf-8").splitlines()
    assert sum(1 for l in prog_lines2 if '"event_type": "RUN_BEGIN"' in l) >= 2


def test_guard_file_size_limit_fail_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    a = _bundle(archive, "A")
    (a / "final_report.txt").write_text("", encoding="utf-8")
    big = a / "references.md"
    big.write_bytes(b"x" * (600 * 1024))
    (a / "payload.txt").write_text("A", encoding="utf-8")
    _write_manifest(a)

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root-bundle",
            str(a),
            "--archive-root",
            str(archive),
            "--output-dir",
            str(out),
            "--max-unique-bundles",
            "10",
            "--max-queue-size",
            "10",
            "--max-references-per-bundle",
            "50",
        ],
        capture_output=True,
        text=True,
        shell=False,
    )
    assert proc.returncode == 3
    assert (out / "bundle_results.jsonl").is_file()
    last = json.loads((out / "bundle_results.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert last["status"] == "BLOCKED_LIMIT_EXCEEDED"


def test_no_shell_true_in_script_source() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "shell=True" not in text

