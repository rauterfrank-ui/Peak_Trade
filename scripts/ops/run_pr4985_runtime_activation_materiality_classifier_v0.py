#!/usr/bin/env python3
"""Collect durable evidence for PR4985 runtime activation materiality classifier v0."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve()
REPO_ROOT = _SCRIPT_ROOT.parents[2]
for parent in [_SCRIPT_ROOT, *_SCRIPT_ROOT.parents]:
    if (parent / "src").is_dir() and (parent / ".git").exists():
        REPO_ROOT = parent
        repo_s = str(parent)
        src_s = str(parent / "src")
        if repo_s not in sys.path:
            sys.path.insert(0, repo_s)
        if src_s not in sys.path:
            sys.path.insert(0, src_s)
        break

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SOURCE_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research/post_pr4985_false_positive_corrected_runtime_activation_reassessment_v0_20260708T001554Z"
)
VERDICT = "POST_PR4985_RUNTIME_ACTIVATION_MATERIALITY_CLASSIFIER_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_pr4985_runtime_activation_materiality_classifier_v0.py",
    "tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/test_full_canonical_system_backtest_parity_gap_assessment_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/pr4985_runtime_activation_materiality_classifier_v0.py",
    "scripts/ops/run_pr4985_runtime_activation_materiality_classifier_v0.py",
    "tests/trading/master_v2/test_pr4985_runtime_activation_materiality_classifier_v0.py",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _write_manifest(evidence_dir: Path) -> int:
    entries: list[str] = []
    for path in sorted(evidence_dir.iterdir()):
        if path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.name}\n")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("".join(entries), encoding="utf-8")
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def _discover_pr4985_reassessment_test_files(repo_root: Path) -> list[str]:
    patterns = (
        "SurfacePFinalFlagsFailClosedContractV0",
        "FINAL_FLAGS_FAIL_CLOSED",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE",
        "FULL_CANONICAL_CHAIN_WIRED",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
    )
    hits: set[str] = set()
    for root_name in ("tests", "src"):
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md"}:
                continue
            rel = path.relative_to(repo_root).as_posix()
            if root_name == "tests" or "test_" in rel or rel.endswith("_test.py"):
                text = path.read_text(encoding="utf-8", errors="replace")
                if any(token in text for token in patterns):
                    hits.add(rel)
    return sorted(hits)


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    from trading.master_v2.pr4985_runtime_activation_materiality_classifier_v0 import (
        classify_runtime_activation_materiality_v0,
        write_classifier_evidence_files_v0,
    )

    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/pr4985_runtime_activation_materiality_classifier_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--porcelain=v1"]).stdout.strip()
    changed = _run(["git", "diff", "--name-only", "origin/main...HEAD"]).stdout.strip()

    source_manifest_rc = 999
    if (SOURCE_EVIDENCE_DIR / "MANIFEST.sha256").is_file():
        proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE_DIR)
        (evidence_dir / "source_manifest_verify.log").write_text(
            proc.stdout + proc.stderr + f"\nSOURCE_MANIFEST_VERIFY_RC={proc.returncode}\n",
            encoding="utf-8",
        )
        source_manifest_rc = proc.returncode
    else:
        (evidence_dir / "source_manifest_verify.log").write_text(
            f"SOURCE_MANIFEST_MISSING={SOURCE_EVIDENCE_DIR / 'MANIFEST.sha256'}\n",
            encoding="utf-8",
        )

    materiality = classify_runtime_activation_materiality_v0(REPO_ROOT)
    write_classifier_evidence_files_v0(evidence_dir, materiality)

    reassessment_tests = _discover_pr4985_reassessment_test_files(REPO_ROOT)
    (evidence_dir / "reassessment_test_files.txt").write_text(
        ("\n".join(reassessment_tests) + "\n") if reassessment_tests else "NO_FILES\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}
    pytest_targets = sorted(set(TARGETED_TESTS) | set(reassessment_tests))
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *pytest_targets],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "targeted_pytest.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr + f"\nTARGETED_TEST_RC={pytest_proc.returncode}\n",
        encoding="utf-8",
    )

    ruff_targets = [str(REPO_ROOT / p) for p in SLICE_CHANGED_FILES if p.endswith(".py")]
    ruff_proc = _run([sys.executable, "-m", "ruff", "check", *ruff_targets])
    (evidence_dir / "ruff_targeted.log").write_text(
        ruff_proc.stdout + ruff_proc.stderr + f"\nRUFF_RC={ruff_proc.returncode}\n",
        encoding="utf-8",
    )

    blocked = (
        head != origin_main
        or source_manifest_rc != 0
        or materiality.direct_true_flag_assignment
        or materiality.runtime_activation
        or pytest_proc.returncode != 0
        or ruff_proc.returncode != 0
    )
    verdict = (
        VERDICT
        if not blocked
        else "POST_PR4985_RUNTIME_ACTIVATION_MATERIALITY_CLASSIFIER_V0_BLOCKED"
    )

    (evidence_dir / "final_operator_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"BRANCH={branch}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                (
                    "DIRECT_TRUE_FLAG_ASSIGNMENT="
                    f"{str(materiality.direct_true_flag_assignment).lower()}"
                ),
                (
                    "RUNTIME_AUTHORITY_TRUE_MATERIAL="
                    f"{str(materiality.runtime_authority_true_material).lower()}"
                ),
                (
                    "EXECUTION_ACTION_CALL_MATERIAL="
                    f"{str(materiality.execution_action_call_material).lower()}"
                ),
                f"RUNTIME_ACTIVATION={str(materiality.runtime_activation).lower()}",
                (
                    "AUTHORITY_TRUE_NEGATIVE_FIXTURE_HITS_COUNT="
                    f"{len(materiality.authority_true_negative_fixture_hits)}"
                ),
                (
                    "AUTHORITY_TRUE_MATERIAL_HITS_COUNT="
                    f"{len(materiality.authority_true_material_hits)}"
                ),
                (
                    "EXECUTION_DOCSTRING_EXAMPLE_HITS_COUNT="
                    f"{len(materiality.execution_docstring_example_hits)}"
                ),
                (
                    "EXECUTION_GUARDED_INFRASTRUCTURE_HITS_COUNT="
                    f"{len(materiality.execution_guarded_infrastructure_hits)}"
                ),
                (
                    "EXECUTION_MATERIAL_ACTIVATION_HITS_COUNT="
                    f"{len(materiality.execution_material_activation_hits)}"
                ),
                f"TARGETED_TEST_RC={pytest_proc.returncode}",
                f"RUFF_RC={ruff_proc.returncode}",
                f"WORKTREE_STATUS<<WORKTREE",
                worktree or "(clean)",
                "WORKTREE",
                f"CHANGED_FILES<<CHANGED",
                changed or "(no committed diff vs origin/main yet)",
                "CHANGED",
                f"SELECTED_NEXT_STEP=FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE_READ_ONLY_REASSESSMENT_AFTER_PR4985",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    (evidence_dir / "final_operator_report.txt").write_text(
        (evidence_dir / "final_operator_report.txt")
        .read_text(encoding="utf-8")
        .replace(
            "NEW_MANIFEST_VERIFY_RC=pending",
            f"NEW_MANIFEST_VERIFY_RC={manifest_rc}",
        ),
        encoding="utf-8",
    )
    report_lines = (evidence_dir / "final_operator_report.txt").read_text(encoding="utf-8")
    if "NEW_MANIFEST_VERIFY_RC=" not in report_lines:
        (evidence_dir / "final_operator_report.txt").write_text(
            report_lines + f"NEW_MANIFEST_VERIFY_RC={manifest_rc}\n",
            encoding="utf-8",
        )
        manifest_rc = _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "pytest_rc": pytest_proc.returncode,
        "ruff_rc": ruff_proc.returncode,
        "source_manifest_verify_rc": source_manifest_rc,
        "runtime_activation": materiality.runtime_activation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out)
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
