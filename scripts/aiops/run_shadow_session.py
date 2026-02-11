#!/usr/bin/env python3
"""P6 — Shadow Session Runner (dry-run, deterministic).

Orchestrates P4C + P5A + P7 (optional paper trading) as a shadow session (no live trading).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p4c.evidence import build_manifest, write_json
from src.aiops.p6.session_schema import ShadowSessionSummary


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_outdir(base: Path, run_id: str = "") -> Path:
    rid = run_id.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = base / "out" / "ops" / "p6" / f"shadow_{rid}"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise TypeError(f"expected dict JSON: {path}")
    return obj


def _run(cmd: List[str], cwd: Path) -> List[str]:
    p = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", type=str, required=True, help="Shadow session spec JSON")
    ap.add_argument("--outdir", type=str, default="", help="Override output directory (optional)")
    ap.add_argument(
        "--run-id",
        type=str,
        default="",
        help="Deterministic run id (optional; used when outdir not provided)",
    )
    ap.add_argument(
        "--evidence", type=int, default=1, help="Write evidence manifest (1 default, 0 disable)"
    )
    ap.add_argument(
        "--dry-run", action="store_true", default=True, help="Dry-run only (default true)"
    )
    ap.add_argument(
        "--p7-spec",
        type=str,
        default="",
        help="P7 paper run spec JSON (optional; overrides spec p7_spec_path)",
    )
    ap.add_argument(
        "--p7-enable",
        type=int,
        default=1,
        help="Enable P7 paper trading step (1 default, 0 disable)",
    )
    ap.add_argument(
        "--p7-evidence",
        type=int,
        default=1,
        help="Write P7 evidence manifest (1 default, 0 disable)",
    )
    args = ap.parse_args()

    repo = _repo_root
    spec_path = (
        Path(args.spec).expanduser().resolve()
        if Path(args.spec).is_absolute()
        else (repo / args.spec).resolve()
    )
    spec = load_json(spec_path)

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else ensure_outdir(repo, args.run_id)
    )

    capsule = (repo / spec["capsule_path"]).resolve()
    p5a_input = (repo / spec["p5a_input_path"]).resolve()
    if not capsule.is_file():
        raise FileNotFoundError(capsule)
    if not p5a_input.is_file():
        raise FileNotFoundError(p5a_input)

    p4c_runner = repo / "scripts" / "aiops" / "run_l2_market_outlook_capsule.py"
    p5a_runner = repo / "scripts" / "aiops" / "run_l3_trade_plan_advisory_p5a.py"
    if not p4c_runner.is_file():
        raise FileNotFoundError(p4c_runner)
    if not p5a_runner.is_file():
        raise FileNotFoundError(p5a_runner)

    # Step 1: P4C (no evidence here; session handles evidence)
    p4c_out_lines = _run(
        [
            sys.executable,
            str(p4c_runner),
            "--capsule",
            str(capsule),
            "--outdir",
            str(outdir / "p4c"),
            "--evidence",
            "0",
            "--dry-run",
        ],
        cwd=repo,
    )
    p4c_out = Path(p4c_out_lines[0]).resolve()

    # Step 2: P5A (inject from P4C)
    p5a_out_lines = _run(
        [
            sys.executable,
            str(p5a_runner),
            "--input",
            str(p5a_input),
            "--from-p4c",
            str(p4c_out),
            "--outdir",
            str(outdir / "p5a"),
            "--evidence",
            "0",
            "--dry-run",
        ],
        cwd=repo,
    )
    p5a_out = Path(p5a_out_lines[0]).resolve()

    p4c_obj = load_json(p4c_out)
    outlook = (p4c_obj.get("outlook") or {}) if isinstance(p4c_obj, dict) else {}
    no_trade = bool(outlook.get("no_trade", False))

    p7_outputs: Dict[str, Any] = {}
    p7_account_summary: Dict[str, Any] = {}
    p7_printed: List[Path] = []

    if int(args.p7_enable) == 1:
        p7_spec_path = (
            Path(args.p7_spec).expanduser().resolve()
            if args.p7_spec
            else (
                repo / (spec.get("p7_spec_path") or "tests/fixtures/p7/paper_run_min_v0.json")
            ).resolve()
        )
        if not p7_spec_path.is_file():
            raise FileNotFoundError(p7_spec_path)
        p7_runner = repo / "scripts" / "aiops" / "run_paper_trading_session.py"
        if not p7_runner.is_file():
            raise FileNotFoundError(p7_runner)

        p7_subdir = outdir / "p7"
        p7_subdir.mkdir(parents=True, exist_ok=True)
        p7_out_lines = _run(
            [
                sys.executable,
                str(p7_runner),
                "--spec",
                str(p7_spec_path),
                "--run-id",
                args.run_id.strip() or outdir.name,
                "--outdir",
                str(p7_subdir),
                "--evidence",
                str(args.p7_evidence),
            ],
            cwd=repo,
        )
        p7_fills = p7_subdir / "fills.json"
        p7_acct = p7_subdir / "account.json"
        p7_manifest = p7_subdir / "evidence_manifest.json"

        out_p7_fills = outdir / "p7_fills.json"
        out_p7_acct = outdir / "p7_account.json"
        out_p7_manifest = outdir / "p7_evidence_manifest.json"
        write_json(out_p7_fills, load_json(p7_fills))
        write_json(out_p7_acct, load_json(p7_acct))
        p7_outputs = {"p7_fills": str(out_p7_fills), "p7_account": str(out_p7_acct)}
        p7_account_summary = load_json(p7_acct)
        p7_printed = [out_p7_fills, out_p7_acct]
        if p7_manifest.is_file() and int(args.p7_evidence) == 1:
            write_json(out_p7_manifest, load_json(p7_manifest))
            p7_outputs["p7_evidence_manifest"] = str(out_p7_manifest)
            p7_printed.append(out_p7_manifest)

    summary = ShadowSessionSummary(
        run_id=(args.run_id.strip() or outdir.name),
        asof_utc=str(spec.get("asof_utc", "")),
        steps=[
            {"name": "p4c", "out": str(p4c_out)},
            {"name": "p5a", "out": str(p5a_out)},
        ]
        + ([{"name": "p7", "out": str(outdir / "p7_fills.json")}] if p7_outputs else []),
        outputs={"p4c_out": str(p4c_out), "p5a_out": str(p5a_out), **p7_outputs},
        no_trade=no_trade,
        notes=["dry_run_only", "no_execution"],
        p7_outputs=p7_outputs,
        p7_account_summary=p7_account_summary,
    )

    out_summary = outdir / "shadow_session_summary.json"
    write_json(out_summary, summary.to_dict())

    printed: List[Path] = [out_summary, p4c_out, p5a_out] + p7_printed

    if int(args.evidence) == 1:
        meta = {
            "kind": "p6_shadow_session_manifest",
            "schema_version": summary.schema_version,
            "created_at_utc": utc_now_iso(),
        }
        manifest = build_manifest(printed, meta, base_dir=outdir)
        out_manifest = outdir / "evidence_manifest.json"
        write_json(out_manifest, manifest)
        printed.append(out_manifest)

    for fp in printed:
        print(str(fp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
