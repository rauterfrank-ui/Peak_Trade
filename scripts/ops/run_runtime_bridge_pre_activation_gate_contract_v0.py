#!/usr/bin/env python3
"""Collect durable evidence for RuntimeBridgePreActivationGateContractV0."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
BASE_HEAD = "8ab416a3c46f38b798853c306acaa21372c788b6"
OPERATOR_GO_TOKEN = (
    "GO_IMPLEMENT_RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_CONTRACT_V0_NO_ACTIVATION_NO_RUNTIME_AUTHORITY"
)
REVIEW_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/operator_review_runtime_bridge_pre_activation_gate_contract_v0_20260707T204930Z"
)
PROPOSAL_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/runtime_bridge_pre_activation_gate_contract_proposal_v0_20260707T204830Z"
)
VERDICT = "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_CONTRACT_IMPLEMENTATION_V0_PASS"
TARGETED_TESTS = ("tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/runtime_bridge_pre_activation_gate_v0.py",
    "scripts/ops/run_runtime_bridge_pre_activation_gate_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",
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


def _verify_manifest(path: Path, label: str) -> tuple[int, str]:
    if not path.is_dir():
        return 1, f"{label}_ABSENT=true\n{label}_MANIFEST_VERIFY_RC=1\n"
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=path)
    return proc.returncode, (
        proc.stdout
        + proc.stderr
        + f"\n{label}_PATH={path}\n{label}_MANIFEST_VERIFY_RC={proc.returncode}\n"
    )


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/runtime_bridge_pre_activation_gate_contract_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()

    review_rc, review_log = _verify_manifest(REVIEW_EVIDENCE, "REVIEW")
    proposal_rc, proposal_log = _verify_manifest(PROPOSAL_EVIDENCE, "PROPOSAL")
    (evidence_dir / "review_manifest_reverify.log").write_text(review_log, encoding="utf-8")
    (evidence_dir / "proposal_manifest_reverify.log").write_text(proposal_log, encoding="utf-8")

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
        CONTRACT_NAME,
        current_head_default_gate_input_v0,
        evaluate_runtime_bridge_pre_activation_gate_v0,
    )

    gate_input = current_head_default_gate_input_v0()
    gate_result = evaluate_runtime_bridge_pre_activation_gate_v0(gate_input)
    (evidence_dir / "gate_evaluation.log").write_text(
        "\n".join(
            [
                f"CONTRACT_NAME={CONTRACT_NAME}",
                f"runtime_bridge_pre_activation_gate_status={gate_result.runtime_bridge_pre_activation_gate_status}",
                f"runtime_bridge_activation_admissible={str(gate_result.runtime_bridge_activation_admissible).lower()}",
                f"blocking_reasons={','.join(gate_result.blocking_reasons)}",
                f"required_next_gates={','.join(gate_result.required_next_gates)}",
                f"authority_effect={gate_result.authority_effect}",
                f"runtime_effect={gate_result.runtime_effect}",
                f"order_effect={gate_result.order_effect}",
                f"execution_eligible={str(gate_result.execution_eligible).lower()}",
                f"adapter_compatible={str(gate_result.adapter_compatible).lower()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_proc = _run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=REPO_ROOT,
    )
    (evidence_dir / "targeted_pytest.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )
    pytest_summary = ""
    for line in pytest_proc.stdout.splitlines():
        if "passed" in line or "failed" in line or "error" in line:
            pytest_summary = line.strip()
            break

    ruff_targets = list(SLICE_CHANGED_FILES)
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
        gate_result.runtime_bridge_pre_activation_gate_status != "FAIL"
        or gate_result.authority_effect != "NONE"
        or gate_result.runtime_effect != "NONE"
        or gate_result.order_effect != "NONE"
        or gate_result.execution_eligible
        or gate_result.adapter_compatible
        or pytest_proc.returncode != 0
        or ruff_format.returncode != 0
        or ruff_check.returncode != 0
    )
    verdict = (
        VERDICT
        if not blocked
        else "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_CONTRACT_IMPLEMENTATION_V0_BLOCKED"
    )

    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BASE_HEAD={BASE_HEAD}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"WORKTREE_STATUS={worktree or 'clean'}",
                f"OPERATOR_GO_TOKEN={OPERATOR_GO_TOKEN}",
                f"REVIEW_MANIFEST_VERIFY_RC={review_rc}",
                f"PROPOSAL_MANIFEST_VERIFY_RC={proposal_rc}",
                f"CONTRACT_NAME={CONTRACT_NAME}",
                f"runtime_bridge_pre_activation_gate_status={gate_result.runtime_bridge_pre_activation_gate_status}",
                "RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE=false",
                "RUNTIME_AUTHORITY_ACTIVATED=false",
                "ORDERS_ALLOWED=false",
                "SCHEDULER_RUNTIME_ALLOWED=false",
                "SHADOW_AUTHORIZED=false",
                "PAPER_AUTHORIZED=false",
                "TESTNET_AUTHORIZED=false",
                "LIVE_AUTHORIZED=false",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"TARGETED_PYTEST_SUMMARY={pytest_summary}",
                f"RUFF_FORMAT_RC={ruff_format.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"CHANGED_FILES={','.join(SLICE_CHANGED_FILES)}",
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
        "gate_status": gate_result.runtime_bridge_pre_activation_gate_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out)
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"GATE_STATUS={result['gate_status']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
