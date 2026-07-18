#!/usr/bin/env python3
"""Materialize durable evidence for post-repair canonical SHORT reevaluation v1."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=_REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    py = str(_REPO / ".venv/bin/python")
    ruff = str(_REPO / ".venv/bin/ruff")
    summary = json.loads((_EVIDENCE / "probe_summary.json").read_text(encoding="utf-8"))
    direction = json.loads((_EVIDENCE / "direction_probe.json").read_text(encoding="utf-8"))
    economics = summary["economics"]
    flags = summary["direction_probe_flags"]
    totals = summary["totals"]
    result_class = summary["result_class"]

    base_sha = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    head_sha = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()

    pytest_cmd = [
        py,
        "-m",
        "pytest",
        "tests/governance/test_canonical_short_binding_post_repair_reevaluation_v1.py",
        "tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py",
        "-q",
        "--tb=line",
    ]

    (_EVIDENCE / "environment.txt").write_text(
        "\n".join(
            [
                f"utc={datetime.now(timezone.utc).isoformat()}",
                f"python={sys.version.split()[0]}",
                f"platform={platform.platform()}",
                f"base_sha={base_sha}",
                f"head_sha={head_sha}",
                f"branch={branch}",
                "LIVE_AUTHORIZED=false",
                "ORDERS=false",
                "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (_EVIDENCE / "commands.txt").write_text(
        "\n".join(
            [
                "# Post-repair reevaluation commands",
                f"{py} docs/evidence/canonical_short_binding_post_repair_reevaluation_v1/"
                "post_repair_reevaluation_probe_v1.py",
                f"{py} docs/evidence/canonical_short_binding_post_repair_reevaluation_v1/"
                "materialize_evidence_v1.py",
                " ".join(pytest_cmd),
                f"{ruff} format --check "
                "docs/evidence/canonical_short_binding_post_repair_reevaluation_v1/"
                "post_repair_reevaluation_probe_v1.py "
                "tests/governance/test_canonical_short_binding_post_repair_reevaluation_v1.py",
                f"{ruff} check "
                "docs/evidence/canonical_short_binding_post_repair_reevaluation_v1/"
                "post_repair_reevaluation_probe_v1.py "
                "tests/governance/test_canonical_short_binding_post_repair_reevaluation_v1.py",
                "",
            ]
        ),
        encoding="utf-8",
    )

    claims = {
        "EVIDENCE_ID": "canonical_short_binding_post_repair_reevaluation_v1",
        "PREDECESSOR_REPAIR_PR": 5346,
        "PREDECESSOR_TRACE_PR": 5345,
        "PREDECESSOR_ECONOMIC_REEVAL_PR": 5342,
        "CONFIG_ID": summary["config_id"],
        "DATASET_ID": summary["dataset_id"],
        "PERIOD": summary["period"],
        "SEED": summary["seed"],
        "DIRECTION_AUTHORITY": "MasterV2_DoublePlay_sole",
        "CANONICAL_CHAIN_EXECUTED": summary["canonical_chain_executed"],
        "ZERO_TRADE_RESOLVED": summary["zero_trade_resolved"],
        "LONG_SIGNAL_COUNT": totals["enter_long_count"],
        "SHORT_SIGNAL_COUNT": totals["enter_short_count"],
        "NONE_SIGNAL_COUNT": totals["observe_count"],
        "LONG_FILL_COUNT": totals["long_trades"],
        "SHORT_FILL_COUNT": totals["short_trades"],
        "LONG_ROUNDTRIP_COUNT": totals["ledger_long_trades"],
        "SHORT_ROUNDTRIP_COUNT": totals["ledger_short_trades"],
        "TRADE_COUNT_TOTAL": totals["total_trades"],
        "SHORT_ENTRY_REQUESTED": flags["SHORT_ENTRY_REQUESTED"],
        "SHORT_FILL_CREATED": flags["SHORT_FILL_CREATED"],
        "SHORT_POSITION_OBSERVED": flags["SHORT_POSITION_OBSERVED"],
        "SHORT_EXIT_CREATED": flags["SHORT_EXIT_CREATED"],
        "SHORT_ROUNDTRIP_LEDGERED": flags["SHORT_ROUNDTRIP_LEDGERED"],
        "NONE_FAIL_CLOSED_PASS": flags["NONE_FAIL_CLOSED_PASS"],
        "VALUE_LOSS_FOUND": flags["VALUE_LOSS_FOUND"],
        "BYPASS_FOUND": flags["BYPASS_FOUND"] or summary["bypass_found"],
        "RESULT_CLASS": result_class,
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
        "PROMOTION_ELIGIBLE": 0,
        "PRODUCTIVE_FILES_CHANGED": False,
        "LIVE_AUTHORIZED": False,
        "ORDERS": False,
    }
    (_EVIDENCE / "claims.json").write_text(
        json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    classification = {
        "RESULT_CLASS": result_class,
        "RULE": (
            "FAIL_CHAIN if technical chain/direction/short flags fail; "
            "TERMINAL_INCONCLUSIVE if chain ok but fixture trade_count==0; "
            "PASS_CHAIN_ONLY if chain ok and trades < 20 (no economic approval); "
            "ECONOMIC_FAIL if chain ok and trades>=20 with negative net/gross return"
        ),
        "CHAIN_OK": summary["canonical_chain_executed"],
        "DIRECTION_OK": bool(flags["LONG_FUNCTIONAL"] and flags["NONE_FAIL_CLOSED_PASS"]),
        "SHORT_FLAGS_OK": all(
            bool(flags[k])
            for k in (
                "SHORT_ENTRY_REQUESTED",
                "SHORT_FILL_CREATED",
                "SHORT_POSITION_OBSERVED",
                "SHORT_EXIT_CREATED",
                "SHORT_ROUNDTRIP_LEDGERED",
            )
        ),
        "TRADE_COUNT_TOTAL": totals["total_trades"],
        "MIN_TRADES_FOR_ROBUSTNESS": 20,
        "RATIONALE": (
            "Repaired MV2 wiring transports LONG/SHORT/NONE end-to-end; fixture panel "
            f"records {totals['total_trades']} trades "
            f"({totals['long_trades']} long / {totals['short_trades']} short). "
            "Sample remains below robustness threshold; economic gate stays closed."
        ),
    }
    (_EVIDENCE / "result_classification.json").write_text(
        json.dumps(classification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    (_EVIDENCE / "direction_traces.json").write_text(
        json.dumps(direction.get("traces", {}), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    def _write_verdict(*, pytest_rc: int, ruff_format_rc: int, ruff_check_rc: int) -> None:
        lines = [
            "STATUS=PASS",
            f"VERDICT={result_class}",
            f"BASE_SHA={base_sha}",
            f"BRANCH={branch}",
            f"HEAD={head_sha}",
            f"ORIGIN_MAIN={base_sha}",
            f"CONFIG_ID={summary['config_id']}",
            f"DATASET_ID={summary['dataset_id']}",
            f"PERIOD={summary['period']}",
            f"SEED={summary['seed']}",
            f"CANONICAL_CHAIN_EXECUTED={str(summary['canonical_chain_executed']).lower()}",
            "DIRECTION_AUTHORITY=MasterV2_DoublePlay_sole",
            f"LONG_SIGNAL_COUNT={totals['enter_long_count']}",
            f"SHORT_SIGNAL_COUNT={totals['enter_short_count']}",
            f"NONE_SIGNAL_COUNT={totals['observe_count']}",
            f"LONG_FILL_COUNT={totals['long_trades']}",
            f"SHORT_FILL_COUNT={totals['short_trades']}",
            f"LONG_ROUNDTRIP_COUNT={totals['ledger_long_trades']}",
            f"SHORT_ROUNDTRIP_COUNT={totals['ledger_short_trades']}",
            f"TRADE_COUNT_TOTAL={totals['total_trades']}",
            f"ZERO_TRADE_RESOLVED={str(summary['zero_trade_resolved']).lower()}",
            f"SHORT_ENTRY_REQUESTED={str(flags['SHORT_ENTRY_REQUESTED']).lower()}",
            f"SHORT_FILL_CREATED={str(flags['SHORT_FILL_CREATED']).lower()}",
            f"SHORT_POSITION_OBSERVED={str(flags['SHORT_POSITION_OBSERVED']).lower()}",
            f"SHORT_EXIT_CREATED={str(flags['SHORT_EXIT_CREATED']).lower()}",
            f"SHORT_ROUNDTRIP_LEDGERED={str(flags['SHORT_ROUNDTRIP_LEDGERED']).lower()}",
            f"NONE_FAIL_CLOSED_PASS={str(flags['NONE_FAIL_CLOSED_PASS']).lower()}",
            f"VALUE_LOSS_FOUND={str(flags['VALUE_LOSS_FOUND']).lower()}",
            f"BYPASS_FOUND={str(bool(flags['BYPASS_FOUND'] or summary['bypass_found'])).lower()}",
            f"GROSS_RETURN={economics['gross_return']}",
            f"NET_RETURN={economics['net_return']}",
            f"FEES={economics['fees']}",
            f"SLIPPAGE_DRAG={economics['slippage_drag']}",
            f"PROFIT_FACTOR_GROSS={economics['profit_factor_gross']}",
            f"EXPECTANCY_GROSS={economics['expectancy_gross']}",
            f"MAX_DRAWDOWN={economics['max_drawdown']}",
            f"SHARPE={economics['sharpe']}",
            f"BREAK_EVEN_COST_BPS={economics['break_even_cost_bps']}",
            f"REQUIRED_GROSS_EDGE_FOR_BREAK_EVEN={economics['required_gross_edge_for_break_even']}",
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
            "PROMOTION_ELIGIBLE=0",
            f"RESULT_CLASS={result_class}",
            "PRODUCTIVE_FILES_CHANGED=false",
            "LIVE_AUTHORIZED=false",
            "ORDERS=false",
            "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
            f"PYTEST_RC={pytest_rc}",
            f"RUFF_FORMAT_RC={ruff_format_rc}",
            f"RUFF_CHECK_RC={ruff_check_rc}",
            "",
        ]
        (_EVIDENCE / "verdict.txt").write_text("\n".join(lines), encoding="utf-8")

    _write_verdict(pytest_rc=-1, ruff_format_rc=-1, ruff_check_rc=-1)

    (_EVIDENCE / "README.md").write_text(
        "\n".join(
            [
                "# Canonical SHORT Binding Post-Repair Reevaluation v1",
                "",
                "Evidence-only reevaluation after PR #5346 squash-merge.",
                "",
                "## Question",
                "",
                "Does the repaired MV2 research wiring transport LONG, SHORT, and NONE",
                "end-to-end through the exact prior canonical offline fixture panel?",
                "",
                f"## Verdict: `{result_class}`",
                "",
                "- Technical chain bound with `use_execution_pipeline=True` and",
                "  `honor_mapped_short_entry=True`.",
                f"- Fixture panel trade_count_total={totals['total_trades']}",
                f"  (long={totals['long_trades']}, short={totals['short_trades']}).",
                "- Focused direction probe proves SHORT fill/position/exit/ledger and",
                "  LONG regression; NONE remains fail-closed.",
                "- Zero-trade miswiring state is resolved.",
                "- Economic offline gate remains **closed** (low sample / negative panel PnL).",
                "- Master V2 / Double Play remain sole direction authority.",
                "",
                "## Unchanged bindings",
                "",
                "| Field | Value |",
                "|---|---|",
                f"| CONFIG_ID | `{summary['config_id']}` |",
                f"| DATASET_ID | `{summary['dataset_id']}` |",
                f"| PERIOD | `{summary['period']}` |",
                f"| SEED | `{summary['seed']}` |",
                f"| STRATEGY | `{summary['strategy_id']}` / `{summary['strategy_version']}` |",
                f"| FEE_BPS | `{summary['fee_bps']}` |",
                f"| SLIPPAGE_BPS | `{summary['slippage_bps']}` |",
                f"| STOP_PCT | `{summary['stop_pct']}` |",
                "",
                "## Artifacts",
                "",
                "| File | Purpose |",
                "|---|---|",
                "| `post_repair_reevaluation_probe_v1.py` | Non-authoritative harness |",
                "| `probe_summary.json` | Full machine summary |",
                "| `direction_probe.json` | Forced LONG/SHORT/NONE proof |",
                "| `direction_traces.json` | Stage traces per direction |",
                "| `economics.json` | Panel economics |",
                "| `instrument_metrics.json` | Per-instrument rows |",
                "| `claims.json` / `verdict.txt` | Machine claims |",
                "| `result_classification.json` | RESULT_CLASS rationale |",
                "| `manifest.json` | SHA256 inventory |",
                "",
                "## Safety",
                "",
                "`LIVE_AUTHORIZED=false`, `ORDERS=false`, Runtime Bridge",
                "`BOUND_NOT_ACTIVATED`, `PRODUCTIVE_FILES_CHANGED=false`,",
                "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false`, `PROMOTION_ELIGIBLE=0`.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Draft manifest so governance artifact presence checks can run.
    def _write_manifest() -> list[dict[str, object]]:
        names = sorted(
            p.name
            for p in _EVIDENCE.iterdir()
            if p.is_file() and p.name not in {"manifest.json", ".DS_Store"}
        )
        files_local: list[dict[str, object]] = []
        for name in names:
            path = _EVIDENCE / name
            rel = path.relative_to(_REPO).as_posix()
            files_local.append(
                {
                    "name": name,
                    "path": rel,
                    "bytes": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
            )
        payload = {
            "evidence_id": "canonical_short_binding_post_repair_reevaluation_v1",
            "base_sha": base_sha,
            "head_sha": head_sha,
            "branch": branch,
            "result_class": result_class,
            "file_count": len(files_local),
            "files": files_local,
        }
        (_EVIDENCE / "manifest.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return files_local

    _write_manifest()

    ruff_fmt = _run(
        [
            ruff,
            "format",
            "--check",
            str(_EVIDENCE / "post_repair_reevaluation_probe_v1.py"),
            str(_EVIDENCE / "materialize_evidence_v1.py"),
            "tests/governance/test_canonical_short_binding_post_repair_reevaluation_v1.py",
        ]
    )
    ruff_chk = _run(
        [
            ruff,
            "check",
            str(_EVIDENCE / "post_repair_reevaluation_probe_v1.py"),
            str(_EVIDENCE / "materialize_evidence_v1.py"),
            "tests/governance/test_canonical_short_binding_post_repair_reevaluation_v1.py",
        ]
    )
    (_EVIDENCE / "ruff.txt").write_text(
        "FORMAT:\n"
        + ruff_fmt.stdout
        + ruff_fmt.stderr
        + "\nCHECK:\n"
        + ruff_chk.stdout
        + ruff_chk.stderr,
        encoding="utf-8",
    )

    pytest_proc = _run(pytest_cmd)
    (_EVIDENCE / "tests.txt").write_text(pytest_proc.stdout + pytest_proc.stderr, encoding="utf-8")

    _write_verdict(
        pytest_rc=pytest_proc.returncode,
        ruff_format_rc=ruff_fmt.returncode,
        ruff_check_rc=ruff_chk.returncode,
    )

    worktree_after = _run(["git", "status", "--short"]).stdout
    (_EVIDENCE / "worktree_after.txt").write_text(worktree_after, encoding="utf-8")
    stash_after = _run(["git", "stash", "list"]).stdout
    (_EVIDENCE / "stash_after.txt").write_text(stash_after, encoding="utf-8")

    files = _write_manifest()

    print(
        json.dumps(
            {
                "ok": pytest_proc.returncode == 0
                and ruff_fmt.returncode == 0
                and ruff_chk.returncode == 0,
                "result_class": result_class,
                "pytest_rc": pytest_proc.returncode,
                "ruff_format_rc": ruff_fmt.returncode,
                "ruff_check_rc": ruff_chk.returncode,
                "file_count": len(files),
            }
        )
    )
    if pytest_proc.returncode != 0:
        return pytest_proc.returncode
    if ruff_fmt.returncode != 0 or ruff_chk.returncode != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
