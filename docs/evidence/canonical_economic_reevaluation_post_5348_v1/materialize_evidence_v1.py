#!/usr/bin/env python3
"""Materialize durable evidence wrappers for post-#5348 economic reevaluation."""

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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=_REPO, text=True, capture_output=True, check=False)


def main() -> int:
    py = str(_REPO / ".venv/bin/python")
    ruff = str(_REPO / ".venv/bin/ruff")
    summary = json.loads((_EVIDENCE / "probe_summary.json").read_text(encoding="utf-8"))
    baseline = summary["baseline"]

    base_sha = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    head_sha = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()

    pytest_cmd = [
        py,
        "-m",
        "pytest",
        "tests/governance/test_canonical_economic_reevaluation_post_5348_v1.py",
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
                "ECONOMIC_GATE_OPENED=false",
                "PROMOTION_ELIGIBLE=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    commands = [
        "# Canonical economic reevaluation post-#5348 commands",
        f"{py} docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
        "economic_reevaluation_probe_v1.py",
        f"{py} docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
        "materialize_evidence_v1.py",
        " ".join(pytest_cmd),
        f"{ruff} format --check "
        "docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
        "economic_reevaluation_probe_v1.py "
        "tests/governance/test_canonical_economic_reevaluation_post_5348_v1.py",
        f"{ruff} check "
        "docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
        "economic_reevaluation_probe_v1.py "
        "tests/governance/test_canonical_economic_reevaluation_post_5348_v1.py",
        "git diff --check",
        "",
    ]
    (_EVIDENCE / "commands.log").write_text("\n".join(commands), encoding="utf-8")

    readme = f"""# Canonical Economic Reevaluation post-#5348 v1

```text
SLICE=CANONICAL_ECONOMIC_REEVALUATION_POST_5348_V1
BASE_SHA={base_sha}
BRANCH={branch}
PRODUCTIVE_FILES_CHANGED=false
STATUS={summary["status"]}
ECONOMIC_CLASS={summary["economic_class"]}
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
ENTRY_SIDE=NONE
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

{summary["rationale"]}

Full 118-member PIT OKX linear USDT non-BTC futures panel (same durable calendar
coverage as the prior 4-instrument sample). No longer chronological local dataset
exists; period extension is a documented PARTIAL blocker. Cross-sectional
expansion and walk-forward / stress / LOO robustness were executed on the
existing canonical chain without parameter optimization.

## Bindings (unchanged)

| Field | Value |
|---|---|
| CONFIG_ID | `{summary["config_id"]}` |
| DATASET_ID | `{summary["dataset_id"]}` |
| PERIOD | `{summary["period"]}` |
| SEED | `{summary["seed"]}` |
| Instruments | {baseline.get("instruments")} |
| Total trades | {baseline.get("total_trades")} |
| LONG / SHORT | {baseline.get("long_trades")} / {baseline.get("short_trades")} |
| Net return | {baseline.get("net_return")} |
| Walk-forward | {summary.get("walk_forward_verdict")} |
| Stress | {summary.get("stress_verdict")} |

## Safety

`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`, no productive mutation,
no live/orders/shadow/capital, Bollinger `entry_side=NONE` unchanged, Master V2
Double-Play remains sole direction authority.
"""
    (_EVIDENCE / "README.md").write_text(readme, encoding="utf-8")

    # Run focused tests + ruff; capture logs.
    test_proc = _run(pytest_cmd)
    (_EVIDENCE / "tests.log").write_text(
        test_proc.stdout + "\n" + test_proc.stderr + f"\nRC={test_proc.returncode}\n",
        encoding="utf-8",
    )

    ruff_fmt = _run(
        [
            ruff,
            "format",
            "--check",
            "docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
            "economic_reevaluation_probe_v1.py",
            "tests/governance/test_canonical_economic_reevaluation_post_5348_v1.py",
        ]
    )
    ruff_chk = _run(
        [
            ruff,
            "check",
            "docs/evidence/canonical_economic_reevaluation_post_5348_v1/"
            "economic_reevaluation_probe_v1.py",
            "tests/governance/test_canonical_economic_reevaluation_post_5348_v1.py",
        ]
    )
    (_EVIDENCE / "ruff.txt").write_text(
        "FORMAT:\n"
        + ruff_fmt.stdout
        + ruff_fmt.stderr
        + f"RC={ruff_fmt.returncode}\nCHECK:\n"
        + ruff_chk.stdout
        + ruff_chk.stderr
        + f"RC={ruff_chk.returncode}\n",
        encoding="utf-8",
    )

    changed = _run(["git", "diff", "--name-only", "origin/main...HEAD"]).stdout.strip().splitlines()
    untracked = (
        _run(["git", "ls-files", "--others", "--exclude-standard"]).stdout.strip().splitlines()
    )
    all_files = sorted({*changed, *untracked})
    # Prefer evidence-dir relative listing of tracked+present files
    present = sorted(
        str(p.relative_to(_REPO))
        for p in _EVIDENCE.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )
    (_EVIDENCE / "changed_files.txt").write_text(
        "\n".join(present) + "\n",
        encoding="utf-8",
    )

    files_meta = []
    for rel in present:
        path = _REPO / rel
        files_meta.append(
            {
                "path": rel,
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )

    run_manifest = {
        "evidence_id": "canonical_economic_reevaluation_post_5348_v1",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "branch": branch,
        "status": summary["status"],
        "economic_class": summary["economic_class"],
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "pytest_rc": test_proc.returncode,
        "ruff_format_rc": ruff_fmt.returncode,
        "ruff_check_rc": ruff_chk.returncode,
        "reproducibility_ok": summary.get("reproducibility_ok"),
        "wall_seconds": summary.get("wall_seconds"),
        "file_count": len(files_meta),
        "files": files_meta,
        "git_changed_vs_origin_main": all_files,
    }
    (_EVIDENCE / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": test_proc.returncode == 0
                and ruff_fmt.returncode == 0
                and ruff_chk.returncode == 0,
                "pytest_rc": test_proc.returncode,
                "ruff_format_rc": ruff_fmt.returncode,
                "ruff_check_rc": ruff_chk.returncode,
                "files": len(files_meta),
            }
        )
    )
    return 0 if run_manifest["pytest_rc"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
