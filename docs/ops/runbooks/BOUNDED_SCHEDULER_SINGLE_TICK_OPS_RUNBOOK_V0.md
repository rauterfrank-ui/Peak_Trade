---
title: Bounded Scheduler Single-Tick Ops Runbook (NO-LIVE)
status: ACTIVE
last_updated: 2026-05-15
scope: docs-only bounded operator procedure
repo_ref: scheduler contract chain on main
---

# Bounded Scheduler Single-Tick Ops Runbook (v0)

## 1. Purpose

This runbook documents how an operator can reproduce **exactly one** bounded scheduler tick against a **temporary copy** of the repository’s real scheduler jobs TOML—**offline**, **dry-run**, **without** `run_scheduler_loop`, **without** a daemon, **without** sleeps, and **without** subprocess execution of job commands.

It preserves the same safety posture as the merged contract tests:

- Canonical procedure reference: [tests/test_scheduler_real_config_single_tick_dry_run_contract_v0.py](../../../tests/test_scheduler_real_config_single_tick_dry_run_contract_v0.py)
- Scheduler overview (CLI, daemon, dry-run flags): [docs/SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md)

This document does **not** replace product code or tests; it mirrors their intent for **manual /tmp evidence**.

## 2. Non-authority statement

Reading or following this runbook **does not** authorize:

- Testnet, Paper, Shadow, or Live trading
- Broker, exchange, or order lifecycle actions
- Scheduler daemon or long-running loops (`run_scheduler_loop`, cron-style operation)
- Network access or credential use for execution
- Changing repository configuration files in place
- Bypassing safety gates, governance, or written operator approval

**Dashboards, signals, AI output, and docs are not approvals.** A single dry-run tick is not daemon readiness.

## 3. Preconditions

- Repository checkout is **`main`**.
- Working tree is **clean** (`git status --short` empty) before you start.
- You use **Python 3** (`python3` on PATH; adjust if your environment uses another entrypoint).
- You accept that **artifacts are written under `/tmp`** only (no repo writes from the harness beyond normal git read).

## 4. Operator GO phrase

Speak or log an explicit GO before running the harness (example):

> **GO BOUNDED SCHEDULER REAL CONFIG SINGLE TICK EXECUTION DRY RUN — tmp artifacts only, dry_run, no daemon, no network, no orders.**

If you cannot say that truthfully, **stop**.

## 5. Safety boundaries

| Rule | This runbook |
|------|----------------|
| `run_scheduler_tick_once` only | Yes (one invocation per harness run) |
| `dry_run=True` | Required |
| `subprocess_run` / real job commands | Must not execute (guarded inject raises if called) |
| `run_scheduler_loop` | Must not be used |
| Sleep / polling loop | Must not be part of this procedure |
| Mutate repo `config/scheduler/jobs.toml` (or other repo paths) | Forbidden |
| Testnet/Paper/Shadow/Live | Not authorized |

Mandatory vocabulary (boundary, not slogan):

- **Single bounded tick ≠** scheduler daemon readiness.
- **Dry-run dispatch ≠** order lifecycle.
- **Real-config candidate ≠** parameter tuning approval.

## 6. Command shape

High level:

1. `cd` to the Peak_Trade repository root (replace `~/Peak_Trade` in the appendix if yours differs).
2. Verify **§3** Preconditions.
3. Copy the **Appendix A — Repro harness (bash)** block into a local file **outside the repo** (e.g. under `/tmp`) or paste into your shell editor, save, `chmod +x`, and run once in the foreground.
4. Collect the printed `BASE=...` path and confirm `git status --short` is still empty.

The harness:

- Copies the top-scoring scheduler candidate (today: `config/scheduler/jobs.toml`) to **`config.copy.toml` under `/tmp`**.
- Applies **in-memory** schedule forcing for one due job only (matches contract-test intent); the on-disk `/tmp` copy stays byte-identical to the repo file.
- Writes `SINGLE_TICK_SUMMARY.json`, log captures, and a short markdown report under the same `/tmp` base.

**Do not** check the generated harness script into the repo unless a separate approved slice promotes it under `scripts/ops/` (this v0 runbook intentionally keeps the script operator-local in `/tmp`).

## 7. Expected artifacts

Under `BASE="&#47;tmp&#47;peak_trade_bounded_scheduler_real_config_single_tick_execution_dry_run_<TS>&#47;"` you should see:

| File | Meaning |
|------|---------|
| `SELECTED_CONFIG.txt` | Top candidate scoreboard |
| `config.copy.toml` | Byte copy of selected repo config at start |
| `config.copy.diff` | Unified diff vs repo (typically “identical after copy”) |
| `single_tick_stdout.txt` / `single_tick_stderr.txt` | Captured tick logs |
| `SINGLE_TICK_SUMMARY.json` | Machine-readable summary (`verdict`, counts) |
| `BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN.md` | Human report |

## 8. Pass criteria

- **PASS_1:** `main` + clean worktree **before** run.
- **PASS_2:** `SELECTED_CONFIG` recorded (or explicit refusal JSON if no candidate).
- **PASS_3:** `/tmp` config copy exists.
- **PASS_4:** Repo config file **byte-unchanged** after the tick.
- **PASS_5:** Exactly one `run_scheduler_tick_once` completed in the harness.
- **PASS_6:** `SINGLE_TICK_SUMMARY.json` written and parseable.
- **PASS_7–9:** `loaded`, `due`, `dispatched` (and related) counts present.
- **PASS_10:** No network/exchange/broker/order path in this procedure (dry-run + subprocess guard).
- **PASS_11:** No daemon / `run_scheduler_loop` started.
- **PASS_12:** `git status --short` empty **after** run.

## 9. Hold / stop criteria

**Stop and treat as HOLD** if any of these occur:

- **HOLD_1:** No scheduler config candidate found (`verdict` ends with `_REFUSED_NO_SAFE_CONFIG`).
- **HOLD_2:** Harness raises (`subprocess_run` invoked, git dirty, repo bytes changed).
- **HOLD_3:** Repo config file size or bytes differ after the run.
- **HOLD_4:** Working tree dirty after the run.
- **HOLD_5:** Any long-running scheduler or sleep loop was started (procedure violation).
- **HOLD_6–HOLD_7:** Any attempt to use live/testnet/paper/shadow execution in the same session as “proof” for this slice.
- **HOLD_8:** Paid AI eval or external execution flags enabled for this proof (not in scope).

## 10. Interpretation of counts

Typical successful shape (example from an observed dry-run; your job definitions may change counts):

- `loaded`: jobs parsed from the temp config path.
- `eligible_after_tags`: jobs considered after tag filter (this harness does not pass include/exclude tags; values match loaded when unset).
- `skipped_not_due`: eligible jobs not due at the synthetic `now`.
- `due` / `dispatched`: should match for a single pass; each due job is dispatched once per tick.
- `succeeded` / `failed`: dry-run successes are normal when `dry_run=True` and validation passes.

The harness uses a **fixed synthetic clock** (`2026-05-15T19:30:00`) aligned with contract tests for reproducibility.

## 11. What this does not prove

- Continuous scheduler operation, crash recovery, or poll-interval behavior.
- Real subprocess execution of scheduled commands.
- Shadow, Paper, or Testnet scheduled runs over time.
- Live readiness, profitability, or risk suitability.
- That production parameters are correct—only that **one offline dry-run tick** can load real config shape safely when copied to `/tmp`.

## 12. Closeout template

After a successful run, you may record a closeout (example fields):

```text
VERDICT=BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN_OK
SOURCE_BASE=/tmp/peak_trade_bounded_scheduler_real_config_single_tick_execution_dry_run_<TS>
SELECTED_CONFIG=config/scheduler/jobs.toml
NO_REPO_CHANGE=true
DRY_RUN=true
NOTES=Operator GO logged; no daemon; no network; subprocess guard active.
```

## 13. Machine lines (header)

```text
RUNBOOK_ID=BOUNDED_SCHEDULER_SINGLE_TICK_OPS_RUNBOOK_V0
MODE=bounded_single_tick_dry_run
DAEMON_AUTHORIZED=false
RUNTIME_LOOP_AUTHORIZED=false
TESTNET_RUN_AUTHORIZED=false
PAPER_RUN_AUTHORIZED=false
SHADOW_RUN_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDER_LIFECYCLE_AUTHORIZED=false
```

## 14. Docs validation (for changes to this file)

From the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

## Appendix A — Repro harness (bash)

**Operator-owned.** Save as e.g. `/tmp/run_peak_trade_bounded_scheduler_real_config_single_tick_execution_dry_run.sh`, review, then execute.  
Replace `~/Peak_Trade` if your checkout path differs.

````bash
#!/usr/bin/env bash
set -euo pipefail

cd ~/Peak_Trade

test "$(git rev-parse --abbrev-ref HEAD)" = "main"
test -z "$(git status --porcelain)"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BASE="/tmp/peak_trade_bounded_scheduler_real_config_single_tick_execution_dry_run_${TS}"
mkdir -p "$BASE"

RESULT="$BASE/BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN.md"
RUNNER="$BASE/run_bounded_scheduler_real_config_single_tick_execution_dry_run.py"
SUMMARY_JSON="$BASE/SINGLE_TICK_SUMMARY.json"
SELECTED_CONFIG_TXT="$BASE/SELECTED_CONFIG.txt"
TMP_CONFIG="$BASE/config.copy.toml"
CONFIG_DIFF="$BASE/config.copy.diff"
STDOUT_FILE="$BASE/single_tick_stdout.txt"
STDERR_FILE="$BASE/single_tick_stderr.txt"

cat > "$RUNNER" <<'PY'
from __future__ import annotations

import contextlib
import difflib
import io
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

base = Path(sys.argv[1])
result = Path(sys.argv[2])
summary_json = Path(sys.argv[3])
selected_config_txt = Path(sys.argv[4])
tmp_config = Path(sys.argv[5])
config_diff = Path(sys.argv[6])
stdout_file = Path(sys.argv[7])
stderr_file = Path(sys.argv[8])

repo = Path.cwd()

# Deterministic bucket (aligned with scheduler contract tests).
NOW = datetime(2026, 5, 15, 19, 30, 0)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_git(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=False,
        cwd=repo,
    ).stdout.strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
head = run_git(["rev-parse", "HEAD"])
short_head = run_git(["rev-parse", "--short", "HEAD"])
status_before = run_git(["status", "--short"])

if branch != "main":
    raise SystemExit(f"REFUSE_NOT_MAIN branch={branch!r}")
if status_before:
    raise SystemExit("REFUSE_DIRTY_WORKTREE_BEFORE_RUN")

import re

candidate_files: list[tuple[int, str]] = []
for root_name in ("config", "configs"):
    root = repo / root_name
    if not root.exists():
        continue
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() in {".toml", ".yaml", ".yml"}:
            text = read_text(path)
            score = 0
            if "[[job]]" in text:
                score += 100
            if "[jobs]" in text or "jobs." in text or "job_" in text:
                score += 30
            if re.search(r"\benabled\s*=", text):
                score += 10
            if re.search(r"\binterval\b|\bcron\b|\bschedule\b|\bnext_run\b", text, re.I):
                score += 10
            if re.search(r"\bcommand\b|\bhandler\b", text, re.I):
                score += 10
            candidate_files.append((score, str(path.relative_to(repo))))

candidate_files.sort(key=lambda item: (-item[0], item[1]))
safe_candidates = [(score, rel) for score, rel in candidate_files if score > 0]
selected_rel = safe_candidates[0][1] if safe_candidates else ""
selected_path = repo / selected_rel if selected_rel else None

selected_config_txt.write_text(
    "\n".join(f"{score}\t{rel}" for score, rel in safe_candidates[:50]) + ("\n" if safe_candidates else ""),
    encoding="utf-8",
)

if not selected_path or not selected_path.exists():
    summary: dict[str, Any] = {
        "verdict": "BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN_REFUSED_NO_SAFE_CONFIG",
        "selected_config": None,
        "candidate_count": len(safe_candidates),
        "loaded": 0,
        "due": 0,
        "dispatched": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped_not_due": 0,
        "eligible_after_tags": 0,
        "no_repo_change": run_git(["status", "--short"]) == "",
    }
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.write_text(
        f"""# Bounded Scheduler Real-Config Single-Tick Execution Dry-Run

Generated UTC: {utc_now_iso()}

## Git Context

- Branch: `{branch}`
- HEAD: `{head}`
- Short HEAD: `{short_head}`
- Working tree clean before: `true`

## Refusal

```text
No safe existing scheduler config candidate was found.
```

## Summary (machine)

```text
VERDICT={summary["verdict"]}
CANDIDATE_COUNT={summary["candidate_count"]}
NO_REPO_CHANGE={str(summary["no_repo_change"]).lower()}
```
""",
        encoding="utf-8",
    )
    raise SystemExit(0)

# --- Single-tick dry run on /tmp copy (repo file bytes unchanged) ---
import shutil

before_repo_bytes = selected_path.read_bytes()
shutil.copyfile(selected_path, tmp_config)
after_copy_repo_bytes = selected_path.read_bytes()
if after_copy_repo_bytes != before_repo_bytes:
    raise SystemExit("REFUSE_REPO_CONFIG_MUTATED_DURING_COPY")

orig_lines = before_repo_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
tmp_lines = tmp_config.read_bytes().decode("utf-8", errors="replace").splitlines(keepends=True)
diff_text = "".join(
    difflib.unified_diff(
        orig_lines,
        tmp_lines,
        fromfile=f"repo/{selected_rel}",
        tofile="tmp/config.copy.toml",
    )
)
config_diff.write_text(diff_text if diff_text.strip() else "(identical_bytes_after_copy)\n", encoding="utf-8")


def _utc():
    return NOW


def boom_sub(*_a: Any, **_k: Any):
    raise AssertionError("subprocess_run invoked during dry_run tick")


sys.path.insert(0, str(repo))
import scripts.run_scheduler as rs  # noqa: E402

real_load = rs.load_jobs_from_toml
tmp_resolved = tmp_config.resolve()


def wrap_load(path: Path | str):
    jobs = real_load(path)
    p = Path(path).resolve()
    if p != tmp_resolved:
        return jobs
    anchor_name = "daily_forward_signals_btc"
    try:
        anchor = next(j for j in jobs if j.name == anchor_name)
    except StopIteration:
        enabled = [j for j in jobs if j.enabled]
        anchor = enabled[0] if enabled else None
    if anchor is None:
        return jobs
    for j in jobs:
        j.schedule.next_run_at = NOW + timedelta(days=30)
    anchor.schedule.next_run_at = NOW - timedelta(seconds=5)
    return jobs


buf_out = io.StringIO()
buf_err = io.StringIO()
rs.load_jobs_from_toml = wrap_load
try:
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        summary_obj = rs.run_scheduler_tick_once(
            tmp_config,
            now=NOW,
            dry_run=True,
            verbose=True,
            subprocess_run=boom_sub,
            utcnow=_utc,
        )
finally:
    rs.load_jobs_from_toml = real_load

write_text(stdout_file, buf_out.getvalue())
write_text(stderr_file, buf_err.getvalue())

if selected_path.read_bytes() != before_repo_bytes:
    raise SystemExit("REFUSE_REPO_CONFIG_BYTES_CHANGED_AFTER_TICK")

git_after = run_git(["status", "--short"])
summary_out: dict[str, Any] = {
    "verdict": "BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN_OK",
    "selected_config": selected_rel,
    "candidate_count": len(safe_candidates),
    **asdict(summary_obj),
    "dry_run": True,
    "no_repo_change": git_after == "",
    "tick_now_iso": NOW.isoformat() + "Z",
}
summary_json.write_text(json.dumps(summary_out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

result.write_text(
    f"""# Bounded Scheduler Real-Config Single-Tick Execution Dry-Run

Generated UTC: {utc_now_iso()}

## Git Context

- Branch: `{branch}`
- HEAD: `{head}`
- Short HEAD: `{short_head}`
- Working tree clean before: `true`

## Selected config

- Repo path (relative): `{selected_rel}`
- Temp copy: `{tmp_config}`

## Boundary

```text
Single tick via run_scheduler_tick_once only.
dry_run=True, fake/subprocess guarded (boom if subprocess_run called).
No run_scheduler_loop, no daemon, no sleep in this harness.
/tmp config is a byte-copy; due-job forcing is in-memory loader wrap only (on-disk jobs.toml unchanged).
```

## Outputs

- `SELECTED_CONFIG.txt`: candidate scoreboard (top 50)
- `config.copy.toml`: byte-identical copy at run start
- `config.copy.diff`: unified diff repo vs tmp (expect empty except header when identical)
- `single_tick_stdout.txt` / `single_tick_stderr.txt`: captured CLI-style logs
- `SINGLE_TICK_SUMMARY.json`: machine summary incl. SchedulerTickSummary fields

## SchedulerTickSummary

```json
{json.dumps(asdict(summary_obj), indent=2, sort_keys=True)}
```

## Final machine lines

```text
VERDICT=BOUNDED_SCHEDULER_REAL_CONFIG_SINGLE_TICK_EXECUTION_DRY_RUN_OK
SELECTED_CONFIG={selected_rel}
LOADED={summary_obj.loaded}
ELIGIBLE_AFTER_TAGS={summary_obj.eligible_after_tags}
SKIPPED_NOT_DUE={summary_obj.skipped_not_due}
DUE={summary_obj.due}
DISPATCHED={summary_obj.dispatched}
SUCCEEDED={summary_obj.succeeded}
FAILED={summary_obj.failed}
GIT_STATUS_AFTER(empty=true)={(git_after == "")!s}
NO_REPO_BYTES_CHANGE=true
```
""",
    encoding="utf-8",
)
PY

python3 "$RUNNER" \
  "$BASE" \
  "$RESULT" \
  "$SUMMARY_JSON" \
  "$SELECTED_CONFIG_TXT" \
  "$TMP_CONFIG" \
  "$CONFIG_DIFF" \
  "$STDOUT_FILE" \
  "$STDERR_FILE"

printf '\nBASE=%s\n' "$BASE"
printf '\n--- GIT STATUS (after) ---\n'
git status --short
````

## Related references

- [OPERATOR_C1_EXECUTION_BOUNDARY_NO_LIVE.md](OPERATOR_C1_EXECUTION_BOUNDARY_NO_LIVE.md)
- [ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md](ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md)
- [docs/SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md)
