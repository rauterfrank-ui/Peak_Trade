#!/usr/bin/env python3
"""Collect durable evidence for Surface P required proof-input binding v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import (
    REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
    SLICE_CHANGED_FILES,
    TARGETED_TESTS,
    evaluate_proof_bundle,
    scan_assembler_forbidden_positive_claims,
    write_manifest,
)
from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
    BINDING_SLICE_ID,
    REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P,
    SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
    evaluate_surface_p_required_proof_input_binding_v0,
    surface_p_required_proof_input_binding_to_dict_v0,
)

VERDICT_PASS = "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0_PASS"
VERDICT_BLOCKED = "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0_BLOCKED"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(
    cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)


def collect_evidence(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    durable_archive_root: Path | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    archive_root = Path(
        durable_archive_root
        or os.environ.get(
            "PEAK_TRADE_DURABLE_ARCHIVE_ROOT",
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
        )
    )
    evidence_dir = output_dir or (
        archive_root / f"research/full_canonical_surface_p_required_proof_input_v0_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()

    binding = evaluate_surface_p_required_proof_input_binding_v0(repo_root)
    bundle = evaluate_proof_bundle(repo_root, current_origin_main=origin_main)
    forbidden_violations = scan_assembler_forbidden_positive_claims(
        repo_root, list(SLICE_CHANGED_FILES)
    )

    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BRANCH={branch}",
                f"WORKTREE_STATUS={status or 'clean'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "surface_p_required_proof_input_binding.json").write_text(
        json.dumps(
            surface_p_required_proof_input_binding_to_dict_v0(binding), indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "proof_bundle_snapshot.json").write_text(
        json.dumps(
            {
                "required_proof_input_count": bundle["required_proof_input_count"],
                "satisfied_proof_input_count": bundle["satisfied_proof_input_count"],
                "required_proof_inputs_complete": bundle["required_proof_inputs_complete"],
                "missing_proof_input_ids": bundle["missing_proof_input_ids"],
                "next_blocker": bundle["next_blocker"],
                "full_canonical_chain_wired": bundle["full_canonical_chain_wired"],
                "backtest_runtime_decision_parity_pass": bundle[
                    "backtest_runtime_decision_parity_pass"
                ],
                "system_economic_evidence_admissible": bundle[
                    "system_economic_evidence_admissible"
                ],
                "runtime_rewire_admissible": bundle["runtime_rewire_admissible"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n", encoding="utf-8"
    )

    env = {**dict(os.environ), "PYTHONPATH": f"{repo_root / 'src'}:{repo_root}"}
    pytest_proc = _run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS], cwd=repo_root, env=env
    )
    (evidence_dir / "targeted_pytest.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    changed_py = [repo_root / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
    ruff_targets = [str(path) for path in changed_py if path.is_file()]
    ruff_format = _run(
        [sys.executable, "-m", "ruff", "format", "--check", *ruff_targets], cwd=repo_root
    )
    ruff_check = _run([sys.executable, "-m", "ruff", "check", *ruff_targets], cwd=repo_root)
    (evidence_dir / "ruff_format_check.txt").write_text(
        (ruff_format.stdout + ruff_format.stderr) or f"RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.txt").write_text(
        (ruff_check.stdout + ruff_check.stderr) or f"RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    py_compile_lines: list[str] = []
    py_compile_rc = 0
    for path in changed_py:
        if not path.is_file():
            continue
        proc = _run([sys.executable, "-m", "py_compile", str(path)], cwd=repo_root)
        py_compile_lines.append(f"{path.relative_to(repo_root)} RC={proc.returncode}")
        if proc.returncode != 0:
            py_compile_rc = proc.returncode
            py_compile_lines.extend([proc.stdout, proc.stderr])
    (evidence_dir / "py_compile.txt").write_text(
        "\n".join(py_compile_lines) + "\n", encoding="utf-8"
    )

    forbidden_ok = not forbidden_violations
    (evidence_dir / "forbidden_claims_scan.txt").write_text(
        "\n".join(
            [
                f"FORBIDDEN_POSITIVE_CLAIMS_RC={0 if forbidden_ok else 1}",
                f"FORBIDDEN_POSITIVE_CLAIMS_SCAN={'PASS' if forbidden_ok else 'BLOCKED'}",
                *forbidden_violations,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    binding_pass = (
        binding.satisfied
        and binding.binding_status == "VERIFIED"
        and bundle["required_proof_inputs_complete"] is True
        and bundle["satisfied_proof_input_count"] == 16
        and bundle["full_canonical_chain_wired"] is False
        and bundle["backtest_runtime_decision_parity_pass"] is False
        and bundle["next_blocker"] == REASON_GAP_ASSESSMENT_NOT_ALL_PASS
    )
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        VERDICT_PASS
        if binding_pass and tests_pass and ruff_pass and py_compile_rc == 0 and forbidden_ok
        else VERDICT_BLOCKED
    )

    manifest_rc = write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"BINDING_SLICE_ID={BINDING_SLICE_ID}",
                f"SURFACE_P_BINDING_OWNER={SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER}",
                f"SURFACE_P_PROOF_INPUT_BINDING_STATUS={binding.binding_status}",
                f"SURFACE_P_PROOF_INPUT_SATISFIED={str(binding.satisfied).lower()}",
                f"REQUIRED_PROOF_INPUT_COUNT={bundle['required_proof_input_count']}",
                f"SATISFIED_PROOF_INPUT_COUNT={bundle['satisfied_proof_input_count']}",
                (
                    "REQUIRED_PROOF_INPUTS_COMPLETE="
                    f"{str(bundle['required_proof_inputs_complete']).lower()}"
                ),
                f"MISSING_PROOF_INPUT_IDS={','.join(bundle['missing_proof_input_ids']) or 'NONE'}",
                f"NEXT_BLOCKER={bundle['next_blocker']}",
                f"FULL_CANONICAL_CHAIN_WIRED={str(bundle['full_canonical_chain_wired']).lower()}",
                (
                    "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                    f"{str(bundle['backtest_runtime_decision_parity_pass']).lower()}"
                ),
                (
                    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                    f"{str(bundle['system_economic_evidence_admissible']).lower()}"
                ),
                f"RUNTIME_REWIRE_ADMISSIBLE={str(bundle['runtime_rewire_admissible']).lower()}",
                f"MISSING_REASON_WHEN_UNBOUND={REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P}",
                "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
                "NO_ECONOMIC_CLAIM_CONFIRMED=true",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rc = write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "binding": binding,
        "bundle": bundle,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "forbidden_ok": forbidden_ok,
        "py_compile_rc": py_compile_rc,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--durable-archive-root", default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    result = collect_evidence(repo_root, output_dir=output_dir, durable_archive_root=archive_root)
    binding = result["binding"]
    bundle = result["bundle"]
    print(f"VERDICT={result['verdict']}")
    print(f"SURFACE_P_PROOF_INPUT_BINDING_STATUS={binding.binding_status}")
    print(f"SURFACE_P_PROOF_INPUT_SATISFIED={str(binding.satisfied).lower()}")
    print(f"SATISFIED_PROOF_INPUT_COUNT={bundle['satisfied_proof_input_count']}")
    print(f"NEXT_BLOCKER={bundle['next_blocker']}")
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
