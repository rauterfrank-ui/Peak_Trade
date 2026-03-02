from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def _run(cmd: List[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RunRef:
    database_id: int
    created_at: str
    conclusion: str


def _gh_list_runs(workflow: str, branch: str, limit: int) -> List[RunRef]:
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow,
        "--branch",
        branch,
        "--limit",
        str(limit),
        "--json",
        "databaseId,createdAt,conclusion,status,event",
    ]
    cp = _run(cmd)
    data = json.loads(cp.stdout or "[]")
    out: List[RunRef] = []
    for r in data:
        if r.get("status") != "completed":
            continue
        if r.get("conclusion") != "success":
            continue
        out.append(
            RunRef(
                database_id=int(r["databaseId"]),
                created_at=str(r.get("createdAt", "")),
                conclusion=str(r.get("conclusion", "")),
            )
        )
    return out


def _download_run(run_id: int, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["gh", "run", "download", str(run_id), "--dir", str(outdir)]
    _run(cmd, check=False)


def _find_jsonl(base: Path) -> Optional[Path]:
    for p in base.rglob("execution_events.jsonl"):
        return p
    return None


def _iter_jsonl_lines(paths: Iterable[Path]) -> Iterable[str]:
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                yield s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", default="prbj-testnet-exec-events.yml")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--runs", type=int, default=10, help="how many recent runs to inspect")
    ap.add_argument("--take", type=int, default=5, help="how many successful runs to bundle (max)")
    ap.add_argument("--out-dir", default="out/ops/prbj_bundle_latest", help="untracked output dir")
    ap.add_argument(
        "--write-repo-latest",
        action="store_true",
        help="also write docs/ops/samples/execution_events_latest.jsonl (tracked) for PR-BG fallback chain",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = _gh_list_runs(args.workflow, args.branch, args.runs)[: args.take]
    meta = {
        "generated_at": _utc_now(),
        "workflow": args.workflow,
        "branch": args.branch,
        "requested_runs": args.runs,
        "bundled_take": args.take,
        "bundled_run_ids": [r.database_id for r in runs],
    }

    dl_root = out_dir / "downloads"
    if dl_root.exists():
        shutil.rmtree(dl_root)
    dl_root.mkdir(parents=True, exist_ok=True)

    jsonl_paths: List[Path] = []
    for r in runs:
        rdir = dl_root / str(r.database_id)
        _download_run(r.database_id, rdir)
        p = _find_jsonl(rdir)
        if p is not None:
            jsonl_paths.append(p)

    bundle_path = out_dir / "execution_events_bundled.jsonl"
    lines = list(_iter_jsonl_lines(jsonl_paths))
    bundle_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    meta_path = out_dir / "bundle_meta.json"
    meta_path.write_text(json.dumps({**meta, "line_count": len(lines)}, indent=2), encoding="utf-8")

    if args.write_repo_latest:
        repo_latest = Path("docs/ops/samples/execution_events_latest.jsonl")
        repo_latest.parent.mkdir(parents=True, exist_ok=True)
        repo_latest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    print(
        f"BUNDLE_OK out_dir={out_dir} line_count={len(lines)} run_ids={[r.database_id for r in runs]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
