"""Read-only Class-A Spot/Paper scheduled workflow snapshot report (v0).

Summarizes `gh run list` JSON for the Class-A shadow/paper scheduled probe workflow.
No network I/O unless ``--gh`` is used. No mutations, no artifact downloads.

This report is infrastructure-smoke evidence only: it is not Futures/Perp readiness,
not Testnet/Live approval, and does not authorize execution wiring or gate bypass.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

CONTRACT = "class_a_spot_paper_snapshot_report_v0"
DEFAULT_WORKFLOW = "class-a-shadow-paper-scheduled-probe-v1.yml"
GH_JSON_FIELDS = "databaseId,status,conclusion,event,createdAt,updatedAt,headBranch,headSha,url"


def normalize_run_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal dict with string values for known keys (best-effort)."""
    out: dict[str, Any] = {}
    for key in (
        "databaseId",
        "status",
        "conclusion",
        "event",
        "createdAt",
        "updatedAt",
        "headBranch",
        "headSha",
        "url",
    ):
        val = raw.get(key)
        if val is None:
            out[key] = None
        elif isinstance(val, (str, int, bool)):
            out[key] = val
        else:
            out[key] = str(val)
    return out


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure summary counters and caveats from normalized or raw gh run records."""
    total = len(runs)
    completed = 0
    completed_success = 0
    completed_skipped = 0
    completed_failure = 0
    completed_cancelled = 0
    completed_other = 0
    not_completed = 0
    schedule_rows = 0

    for raw in runs:
        r = raw if "databaseId" in raw else normalize_run_record(raw)
        status = (r.get("status") or "").strip().lower()
        conclusion = r.get("conclusion")
        conclusion_l = conclusion.strip().lower() if isinstance(conclusion, str) else None
        event = (r.get("event") or "").strip().lower()
        if event == "schedule":
            schedule_rows += 1

        if status != "completed":
            not_completed += 1
            continue

        completed += 1
        if conclusion_l == "success":
            completed_success += 1
        elif conclusion_l == "skipped":
            completed_skipped += 1
        elif conclusion_l == "failure":
            completed_failure += 1
        elif conclusion_l == "cancelled":
            completed_cancelled += 1
        else:
            completed_other += 1

    caveats: list[str] = [
        "Class-A Spot/Paper scheduled workflow visibility is infrastructure-smoke only.",
        "This is not Futures/Perp readiness and not Testnet/Live approval.",
        "Schedule success does not imply PaperExecutionEngine or Futures wiring.",
        "Do not treat 'skipped' conclusions as successful probes without reading that run's logs.",
    ]
    if completed_skipped:
        caveats.append(
            "At least one completed run has conclusion 'skipped'; review URLs before inferring health."
        )
    if completed_failure or completed_cancelled:
        caveats.append(
            "Non-success conclusions appear in the sample; treat the window as not uniformly green."
        )
    if not_completed:
        caveats.append(
            "Some runs are not completed in this sample; conclusions apply only to listed rows."
        )

    return {
        "run_count": total,
        "schedule_event_rows": schedule_rows,
        "completed_total": completed,
        "completed_success": completed_success,
        "completed_skipped": completed_skipped,
        "completed_failure": completed_failure,
        "completed_cancelled": completed_cancelled,
        "completed_other_conclusion": completed_other,
        "not_completed": not_completed,
        "caveats": caveats,
    }


def build_json_payload(
    *,
    workflow: str,
    runs: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    normalized = [normalize_run_record(r) if isinstance(r, dict) else {} for r in runs]
    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "read_only": True,
        "workflow_file": workflow,
        "summary": summary,
        "runs": normalized,
    }


def render_markdown(
    *,
    workflow: str,
    runs: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines: list[str] = [
        "# Class-A Spot/Paper workflow snapshot (read-only)",
        "",
        f"- **Contract:** `{CONTRACT}`",
        f"- **Workflow file:** `{workflow}`",
        f"- **Runs in sample:** {summary['run_count']}",
        "",
        "## Interpretation boundaries",
        "",
        "- Infrastructure-smoke / scheduled probe visibility only.",
        "- **Not** Futures or perpetual readiness.",
        "- **Not** Testnet or Live approval.",
        "- **Not** evidence of PaperExecutionEngine ↔ Futures accounting wiring.",
        "- Does **not** bypass Master V2 / Double Play, Scope/Capital, Risk/KillSwitch, or execution gates.",
        "",
        "## Summary counts",
        "",
        f"- Schedule-tagged rows (event=`schedule`): **{summary['schedule_event_rows']}**",
        f"- Completed + conclusion **success**: **{summary['completed_success']}**",
        f"- Completed + conclusion **skipped**: **{summary['completed_skipped']}**",
        f"- Completed + **failure** / **cancelled**: **{summary['completed_failure']}** / "
        f"**{summary['completed_cancelled']}**",
        f"- Completed + other/unknown conclusion: **{summary['completed_other_conclusion']}**",
        f"- Not **completed** in this sample: **{summary['not_completed']}**",
        "",
        "## Caveats",
        "",
    ]
    for c in summary["caveats"]:
        lines.append(f"- {c}")
    lines.extend(
        [
            "",
            "## Recent runs (newest first as provided)",
            "",
            "| databaseId | status | conclusion | event | createdAt |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for raw in runs:
        r = normalize_run_record(raw) if isinstance(raw, dict) else {}
        lines.append(
            "| {id} | {st} | {co} | {ev} | {cr} |".format(
                id=r.get("databaseId", ""),
                st=r.get("status", ""),
                co=r.get("conclusion", ""),
                ev=r.get("event", ""),
                cr=r.get("createdAt", ""),
            )
        )
    lines.append("")
    return "\n".join(lines)


def coerce_run_list(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of run objects")
    out: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Run at index {i} is not a JSON object")
        out.append(item)
    return out


def load_runs_from_json_stream(stream: TextIO) -> list[dict[str, Any]]:
    return coerce_run_list(json.load(stream))


def fetch_runs_via_gh(*, workflow: str, limit: int) -> list[dict[str, Any]]:
    proc = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            workflow,
            "--limit",
            str(limit),
            "--json",
            GH_JSON_FIELDS,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"gh run list failed (exit {proc.returncode}): {err}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gh output was not valid JSON: {e}") from e
    return coerce_run_list(data)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Summarize Class-A Spot/Paper scheduled workflow runs from gh JSON "
            "(stdin, file, or optional gh subprocess)."
        ),
        epilog=(
            "Example (stdin): "
            "gh run list --workflow class-a-shadow-paper-scheduled-probe-v1.yml "
            f"--limit 12 --json {GH_JSON_FIELDS} | "
            "uv run python scripts/ops/report_class_a_spot_paper_snapshot_v0.py "
            "--stdin-json"
        ),
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--stdin-json",
        action="store_true",
        help="Read gh run list JSON array from stdin",
    )
    src.add_argument(
        "--input-file",
        type=Path,
        metavar="PATH",
        help="Read gh run list JSON array from a file",
    )
    src.add_argument(
        "--gh",
        action="store_true",
        help=f"Run gh run list locally (workflow default: {DEFAULT_WORKFLOW})",
    )
    p.add_argument(
        "--workflow",
        default=DEFAULT_WORKFLOW,
        help=f"Workflow YAML name for --gh (default: {DEFAULT_WORKFLOW})",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Limit for --gh (default: 12)",
    )
    p.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Emit JSON instead of Markdown (default is Markdown)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.gh:
            runs = fetch_runs_via_gh(workflow=args.workflow, limit=args.limit)
        elif args.stdin_json:
            runs = load_runs_from_json_stream(sys.stdin)
        elif args.input_file is not None:
            with args.input_file.open(encoding="utf-8") as f:
                runs = load_runs_from_json_stream(f)
        else:  # pragma: no cover — argparse requires one source
            raise ValueError("No input source (internal error)")
    except (ValueError, OSError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    summary = summarize_runs(runs)
    if args.emit_json:
        payload = build_json_payload(workflow=args.workflow, runs=runs, summary=summary)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            render_markdown(workflow=args.workflow, runs=runs, summary=summary),
            end="",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
