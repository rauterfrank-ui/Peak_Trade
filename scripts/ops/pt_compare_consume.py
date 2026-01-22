#!/usr/bin/env python3
"""
Consume a deterministic replay compare report and emit:
1) Compact human-readable summary to stdout (CI/ops friendly)
2) Minified JSON summary file for dashboards

Offline-only, deterministic output (no wall clock).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

# Add repo root to path for imports (scripts/ops -> repo root)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.execution.replay_pack.canonical import (
    CanonicalJsonError,
    dumps_canonical,
    validate_no_floats,
)


EXIT_OK = 0
EXIT_CONTRACT = 2


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _as_str(x: Any) -> str:
    return str(x) if x is not None else ""


def _read_report(path: Path) -> Dict[str, Any]:
    try:
        txt = path.read_text(encoding="utf-8")
        obj = json.loads(txt)
    except FileNotFoundError:
        raise ValueError(f"report not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid json: {type(e).__name__}: {e}")
    if not isinstance(obj, dict):
        raise ValueError("report root must be a JSON object")
    return obj


def _get_nested(obj: Mapping[str, Any], *keys: str) -> Any:
    cur: Any = obj
    for k in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(k)
    return cur


def _parse_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _report_fields(
    report: Mapping[str, Any], *, max_reasons: int
) -> Tuple[Dict[str, Any], List[str]]:
    schema_version = _as_str(report.get("schema_version"))
    if not schema_version:
        raise ValueError("missing schema_version")

    meta = report.get("meta")
    summary = report.get("summary")
    replay = report.get("replay")
    if not isinstance(meta, Mapping):
        raise ValueError("missing meta object")
    if not isinstance(summary, Mapping):
        raise ValueError("missing summary object")
    if not isinstance(replay, Mapping):
        raise ValueError("missing replay object")

    status = _as_str(summary.get("status")) or "FAIL"
    exit_code = _parse_int(summary.get("exit_code"), default=1)
    reasons_raw = summary.get("reasons")
    if reasons_raw is None:
        reasons: List[str] = []
    elif isinstance(reasons_raw, list):
        reasons = sorted([_as_str(r) for r in reasons_raw if _as_str(r)])
    else:
        raise ValueError("summary.reasons must be a list")
    reasons = reasons[: max(0, int(max_reasons))]

    # Datarefs block is optional
    datarefs = report.get("datarefs")
    datarefs_out: Dict[str, Any] = {
        "hash_mismatch": 0,
        "missing": 0,
        "mode": "none",
        "resolved": 0,
        "source_status": "ABSENT",
        "total": 0,
    }
    if isinstance(datarefs, Mapping):
        datarefs_out["mode"] = _as_str(datarefs.get("mode")) or "none"
        src = datarefs.get("source")
        if isinstance(src, Mapping):
            datarefs_out["source_status"] = _as_str(src.get("status")) or "ABSENT"
        summ = datarefs.get("summary")
        if isinstance(summ, Mapping):
            datarefs_out["total"] = _parse_int(summ.get("total"), 0)
            datarefs_out["resolved"] = _parse_int(summ.get("resolved"), 0)
            datarefs_out["missing"] = _parse_int(summ.get("missing"), 0)
            datarefs_out["hash_mismatch"] = _parse_int(summ.get("hash_mismatch"), 0)

    # invariants
    inv = _get_nested(report, "replay", "invariants")
    inv_fills = _as_str(_get_nested(inv, "fills")) if isinstance(inv, Mapping) else ""
    inv_positions = _as_str(_get_nested(inv, "positions")) if isinstance(inv, Mapping) else ""
    check_outputs = _as_str(_get_nested(report, "replay", "check_outputs")) or "disabled"

    # diffs counts
    fills_diff = _get_nested(report, "replay", "diffs", "fills_diff")
    pos_diff = _get_nested(report, "replay", "diffs", "positions_diff")
    diffs_counts = {
        "fills_added": _parse_int(_get_nested(fills_diff, "added"), 0)
        if isinstance(fills_diff, Mapping)
        else 0,
        "fills_removed": _parse_int(_get_nested(fills_diff, "removed"), 0)
        if isinstance(fills_diff, Mapping)
        else 0,
        "fills_changed": _parse_int(_get_nested(fills_diff, "changed"), 0)
        if isinstance(fills_diff, Mapping)
        else 0,
        "positions_added": _parse_int(_get_nested(pos_diff, "added"), 0)
        if isinstance(pos_diff, Mapping)
        else 0,
        "positions_removed": _parse_int(_get_nested(pos_diff, "removed"), 0)
        if isinstance(pos_diff, Mapping)
        else 0,
        "positions_changed": _parse_int(_get_nested(pos_diff, "changed"), 0)
        if isinstance(pos_diff, Mapping)
        else 0,
    }

    tool = {
        "compare_version": _as_str(meta.get("compare_version")),
        "name": _as_str(meta.get("tool")),
        "version": _as_str(meta.get("tool_version")),
    }

    out: Dict[str, Any] = {
        "bundle_id": _as_str(meta.get("bundle_id")),
        "datarefs": datarefs_out,
        "diffs_counts": diffs_counts,
        "exit_code": int(exit_code),
        "generated_at_utc": _as_str(meta.get("generated_at_utc")),
        "invariants": {
            "check_outputs": check_outputs,
            "fills": inv_fills,
            "positions": inv_positions,
        },
        "reasons": reasons,
        "run_id": _as_str(meta.get("run_id")),
        "schema_version": "REPLAY_COMPARE_SUMMARY_V1",
        "status": status,
        "tool": tool,
    }

    # Basic minimal validation: require generated_at_utc to exist for dashboards.
    if not out["generated_at_utc"]:
        raise ValueError("missing meta.generated_at_utc")

    # Determinism: no floats
    validate_no_floats(out)
    return out, reasons


def _fmt_reasons(reasons: List[str]) -> str:
    return ",".join(reasons) if reasons else "NONE"


def _fmt_datarefs(dr: Mapping[str, Any]) -> str:
    return (
        f"{_as_str(dr.get('resolved'))}/"
        f"{_as_str(dr.get('missing'))}/"
        f"{_as_str(dr.get('hash_mismatch'))}"
    )


def _write_minified_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Use the existing canonical rules (sorted keys, no whitespace, LF, no floats).
    try:
        s = dumps_canonical(obj)
    except CanonicalJsonError as e:
        raise ValueError(str(e))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
        f.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="pt_compare_consume", add_help=True)
    ap.add_argument("--report", required=True, help="path to compare_report.json")
    ap.add_argument(
        "--out",
        default=None,
        help="path to write minified JSON summary (default: sibling compare_summary.min.json)",
    )
    ap.add_argument(
        "--mode",
        default="ci",
        choices=["ci", "ops"],
        help="output mode (ci=single line, ops=two lines)",
    )
    ap.add_argument("--max-reasons", type=int, default=5, help="max reasons to include")
    ap.add_argument(
        "--max-samples", type=int, default=3, help="max sample-derived items to print (reserved)"
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when report status is FAIL (default: informational exit 0)",
    )
    args = ap.parse_args(argv)

    report_path = Path(args.report)
    out_path = (
        Path(args.out)
        if args.out is not None
        else (report_path.parent / "compare_summary.min.json")
    )

    try:
        rep = _read_report(report_path)
        summary_obj, reasons = _report_fields(rep, max_reasons=int(args.max_reasons))
        _write_minified_json(out_path, summary_obj)
    except Exception as e:
        _eprint(f"ContractViolationError: {type(e).__name__}: {e}")
        return EXIT_CONTRACT

    status = _as_str(summary_obj.get("status")) or "FAIL"
    exit_val = summary_obj.get("exit_code")
    exit_code = int(exit_val) if exit_val is not None else 1
    dr = summary_obj.get("datarefs") if isinstance(summary_obj.get("datarefs"), Mapping) else {}
    one_line = (
        f"STATUS={status} "
        f"EXIT={exit_code} "
        f"REASONS={_fmt_reasons(reasons)} "
        f"DATAREFS={_fmt_datarefs(dr)}"
    )
    print(one_line)

    if args.mode == "ops":
        diffs = (
            summary_obj.get("diffs_counts")
            if isinstance(summary_obj.get("diffs_counts"), Mapping)
            else {}
        )
        inv = (
            summary_obj.get("invariants")
            if isinstance(summary_obj.get("invariants"), Mapping)
            else {}
        )
        second = (
            f"OUT={out_path} "
            f"BUNDLE={_as_str(summary_obj.get('bundle_id'))} "
            f"RUN={_as_str(summary_obj.get('run_id'))} "
            f"CHECK_OUTPUTS={_as_str(inv.get('check_outputs'))} "
            f"INV_FILLS={_as_str(inv.get('fills'))} "
            f"INV_POSITIONS={_as_str(inv.get('positions'))} "
            f"F_DIFF={_as_str(diffs.get('fills_added'))}/"
            f"{_as_str(diffs.get('fills_removed'))}/"
            f"{_as_str(diffs.get('fills_changed'))} "
            f"P_DIFF={_as_str(diffs.get('positions_added'))}/"
            f"{_as_str(diffs.get('positions_removed'))}/"
            f"{_as_str(diffs.get('positions_changed'))}"
        )
        print(second)

    if args.strict and status != "PASS":
        return int(exit_code) if exit_code else 1
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
