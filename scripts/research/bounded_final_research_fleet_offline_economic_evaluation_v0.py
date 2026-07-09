from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


FINAL_FLEET = ("trend_following", "bollinger_bands", "momentum_1h")


def _run_materializer(
    repo_root: Path, output_dir: Path, operator: str, go_token: str
) -> dict[str, Any]:
    materializer = (
        repo_root
        / "scripts"
        / "ops"
        / "materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
    )
    if not materializer.exists():
        return {
            "status": "FAIL_CLOSED",
            "reason_codes": ["MATERIALIZER_SCRIPT_MISSING"],
            "materializer_path": str(materializer),
            "rc": 2,
        }

    cmd = [
        sys.executable,
        str(materializer),
        "--repo-root",
        str(repo_root),
        "--output-dir",
        str(output_dir),
        "--operator",
        operator,
        "--go-token",
        go_token,
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    (output_dir / "materializer_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output_dir / "materializer_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (output_dir / "materializer.rc").write_text(f"{completed.returncode}\n", encoding="utf-8")

    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL_CLOSED",
        "reason_codes": [] if completed.returncode == 0 else ["MATERIALIZER_RC_NONZERO"],
        "materializer_path": str(materializer),
        "rc": completed.returncode,
    }


def _write_manifest(output_dir: Path) -> int:
    manifest = output_dir / "MANIFEST.sha256"
    files = sorted(
        p
        for p in output_dir.rglob("*")
        if p.is_file()
        and p.name not in {"MANIFEST.sha256", "MANIFEST.verify.txt", "MANIFEST.verify.rc"}
    )

    lines: list[str] = []
    for file_path in files:
        rel = file_path.relative_to(output_dir)
        digest = subprocess.check_output(
            ["shasum", "-a", "256", str(file_path)], text=True
        ).split()[0]
        lines.append(f"{digest}  {rel}\n")

    manifest.write_text("".join(lines), encoding="utf-8")
    verify = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(output_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    (output_dir / "MANIFEST.verify.txt").write_text(verify.stdout, encoding="utf-8")
    (output_dir / "MANIFEST.verify.rc").write_text(f"{verify.returncode}\n", encoding="utf-8")
    return verify.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--go-token", required=True)
    parser.add_argument("--fleet", required=True)
    parser.add_argument("--futures-only", action="store_true")
    parser.add_argument("--offline-only", action="store_true")
    parser.add_argument("--no-runtime", action="store_true")
    parser.add_argument("--no-orders", action="store_true")
    parser.add_argument("--require-full-canonical-chain-wired", action="store_true")
    parser.add_argument("--require-backtest-runtime-decision-parity-pass", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    requested_fleet = tuple(x.strip() for x in args.fleet.split(",") if x.strip())
    reason_codes: list[str] = []

    if requested_fleet != FINAL_FLEET:
        reason_codes.append("FINAL_RESEARCH_FLEET_MISMATCH")
    if not args.futures_only:
        reason_codes.append("FUTURES_ONLY_NOT_ASSERTED")
    if not args.offline_only:
        reason_codes.append("OFFLINE_ONLY_NOT_ASSERTED")
    if not args.no_runtime:
        reason_codes.append("NO_RUNTIME_NOT_ASSERTED")
    if not args.no_orders:
        reason_codes.append("NO_ORDERS_NOT_ASSERTED")
    if not args.require_full_canonical_chain_wired:
        reason_codes.append("FULL_CANONICAL_CHAIN_WIRED_REQUIREMENT_MISSING")
    if not args.require_backtest_runtime_decision_parity_pass:
        reason_codes.append("BACKTEST_RUNTIME_DECISION_PARITY_REQUIREMENT_MISSING")

    materializer_result = _run_materializer(repo_root, output_dir, args.operator, args.go_token)
    reason_codes.extend(materializer_result["reason_codes"])

    status = "PASS" if not reason_codes else "FAIL_CLOSED"

    report = {
        "verdict": (
            "PASS_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
            if status == "PASS"
            else "BLOCKED_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
        ),
        "status": status,
        "repo_root": str(repo_root),
        "operator": args.operator,
        "go_token": args.go_token,
        "final_research_fleet": list(FINAL_FLEET),
        "requested_fleet": list(requested_fleet),
        "futures_only": args.futures_only,
        "bitcoin_direction_allowed": False,
        "offline_only": args.offline_only,
        "no_runtime": args.no_runtime,
        "no_orders": args.no_orders,
        "no_credentials": True,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "economic_validity_offline_gate_pass": False,
        "materializer_result": materializer_result,
        "reason_codes": reason_codes,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
    }

    (output_dir / "bounded_final_research_fleet_offline_economic_evaluation_v0.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    final_report_lines = [
        f"VERDICT={report['verdict']}",
        f"STATUS={status}",
        f"REPO_ROOT={repo_root}",
        f"OPERATOR={args.operator}",
        f"GO_TOKEN={args.go_token}",
        "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
        f"REQUESTED_FLEET={','.join(requested_fleet)}",
        f"FUTURES_ONLY={str(args.futures_only).lower()}",
        "BITCOIN_DIRECTION_ALLOWED=false",
        f"OFFLINE_ONLY={str(args.offline_only).lower()}",
        f"NO_RUNTIME={str(args.no_runtime).lower()}",
        f"NO_ORDERS={str(args.no_orders).lower()}",
        "NO_CREDENTIALS=true",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        f"MATERIALIZER_RC={materializer_result['rc']}",
        f"REASON_CODES={','.join(reason_codes) if reason_codes else 'NONE'}",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_EFFECT=NONE",
    ]
    (output_dir / "final_report.txt").write_text(
        "\n".join(final_report_lines) + "\n", encoding="utf-8"
    )

    manifest_rc = _write_manifest(output_dir)
    return 0 if status == "PASS" and manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
