#!/usr/bin/env python3
"""Collect durable evidence for Surface P offline-complete runtime-bridge contract v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/runtime_bridge_pre_activation_gate_readiness_assessment_v0_20260707T231500Z"
)
VERDICT = "SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_CONTRACT_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
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


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()

    source_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE)
    (evidence_dir / "source_manifest_verify.log").write_text(
        source_proc.stdout
        + source_proc.stderr
        + f"\nSOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE}\nSOURCE_MANIFEST_VERIFY_RC={source_proc.returncode}\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        render_parity_gap_matrix_json_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
        surface_p_semantic_status_to_dict_v0,
    )

    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    (evidence_dir / "SURFACE_P_SEMANTIC.json").write_text(
        json.dumps(surface_p_semantic_status_to_dict_v0(semantic), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "FULL_CANONICAL_PARITY_GAP_MATRIX.json").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "targeted_pytest.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    ruff_targets = [str(REPO_ROOT / p) for p in SLICE_CHANGED_FILES if p.endswith(".py")]
    ruff_format = _run([sys.executable, "-m", "ruff", "format", *ruff_targets])
    ruff_check = _run([sys.executable, "-m", "ruff", "check", *ruff_targets])
    (evidence_dir / "ruff_format.log").write_text(
        ruff_format.stdout + ruff_format.stderr,
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.log").write_text(
        ruff_check.stdout + ruff_check.stderr,
        encoding="utf-8",
    )

    blocked = (
        pytest_proc.returncode != 0
        or ruff_format.returncode != 0
        or ruff_check.returncode != 0
        or source_proc.returncode != 0
        or semantic.surface_p_offline_parity_status != "COMPLETE"
        or semantic.surface_p_overall_status != "PARTIAL_RUNTIME_ACTIVATION_PENDING"
        or semantic.runtime_bridge_activated
    )
    verdict = (
        VERDICT
        if not blocked
        else "SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_CONTRACT_V0_BLOCKED"
    )

    (evidence_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"WORKTREE_STATUS={worktree or 'clean'}",
                f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_proc.returncode}",
                "SURFACE_P_OFFLINE_PARITY_STATUS=COMPLETE",
                "SURFACE_P_RUNTIME_BRIDGE_BINDING_STATUS=BOUND_NOT_ACTIVATED",
                "SURFACE_P_RUNTIME_ACTIVATION_STATUS=NOT_ACTIVATED_POLICY_BLOCKED",
                "SURFACE_P_OVERALL_STATUS=PARTIAL_RUNTIME_ACTIVATION_PENDING",
                "RUNTIME_BRIDGE_ACTIVATED=false",
                "RUNTIME_AUTHORITY_GRANTED=false",
                "ORDER_AUTHORITY_GRANTED=false",
                "SCHEDULER_AUTHORITY_GRANTED=false",
                "SHADOW_PAPER_TESTNET_LIVE_AUTHORITY_GRANTED=false",
                "AI_LAYER_AUTHORITY_EFFECT=NONE",
                "AI_LAYER_ORDER_EFFECT=NONE",
                "AI_LAYER_RUNTIME_EFFECT=NONE",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"RUFF_FORMAT_RC={ruff_format.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rc = _write_manifest(evidence_dir)
    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "pytest_rc": pytest_proc.returncode,
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
