#!/usr/bin/env python3
"""Read-only AWS export smoke: verify PT_EXPORT_REMOTE is reachable via rclone."""

import base64
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class SmokeResult:
    ok: bool
    reason: str
    export_remote: str
    export_prefix: str
    rclone_present: bool
    listed_ok: bool
    sample_listing: list[str]
    timestamp_utc: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def main() -> int:
    ts = _utc_now()

    export_remote = os.getenv("PT_EXPORT_REMOTE", "").strip()
    export_prefix = os.getenv("PT_EXPORT_PREFIX", "").strip()
    rclone_conf_b64 = os.getenv("PT_RCLONE_CONF_B64", "").strip()

    rclone_present = subprocess.call(["bash", "-lc", "command -v rclone >/dev/null 2>&1"]) == 0

    if not export_remote:
        res = SmokeResult(
            ok=False,
            reason="MISSING_PT_EXPORT_REMOTE",
            export_remote=export_remote,
            export_prefix=export_prefix,
            rclone_present=rclone_present,
            listed_ok=False,
            sample_listing=[],
            timestamp_utc=ts,
        )
        _write_reports(res)
        return 2

    if not rclone_present:
        res = SmokeResult(
            ok=False,
            reason="MISSING_RCLONE",
            export_remote=export_remote,
            export_prefix=export_prefix,
            rclone_present=False,
            listed_ok=False,
            sample_listing=[],
            timestamp_utc=ts,
        )
        _write_reports(res)
        return 2

    if not rclone_conf_b64:
        res = SmokeResult(
            ok=False,
            reason="MISSING_PT_RCLONE_CONF_B64",
            export_remote=export_remote,
            export_prefix=export_prefix,
            rclone_present=True,
            listed_ok=False,
            sample_listing=[],
            timestamp_utc=ts,
        )
        _write_reports(res)
        return 2

    # Write rclone.conf from base64
    conf_dir = Path(".cache/rclone")
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_path = conf_dir / "rclone.conf"
    conf_path.write_bytes(base64.b64decode(rclone_conf_b64))

    env = os.environ.copy()
    env["RCLONE_CONFIG"] = str(conf_path)

    # Build target
    target = export_remote.rstrip("/")
    if export_prefix:
        target = f"{target}/{export_prefix.lstrip('/')}"

    # List (read-only)
    listed_ok = False
    sample_listing: list[str] = []
    cp = _run(["rclone", "lsf", target, "--max-depth", "1"], env=env)
    if cp.returncode == 0:
        listed_ok = True
        sample_listing = [line for line in cp.stdout.splitlines() if line.strip()][:25]
        reason = "OK"
        ok = True
        rc = 0
    else:
        reason = "RCLONE_LIST_FAILED"
        ok = False
        rc = 2
        sample_listing = (cp.stderr.splitlines() + cp.stdout.splitlines())[:25]

    res = SmokeResult(
        ok=ok,
        reason=reason,
        export_remote=export_remote,
        export_prefix=export_prefix,
        rclone_present=True,
        listed_ok=listed_ok,
        sample_listing=sample_listing,
        timestamp_utc=ts,
    )
    _write_reports(res)
    return rc


def _write_reports(res: SmokeResult) -> None:
    outdir = Path("reports/status")
    outdir.mkdir(parents=True, exist_ok=True)

    jpath = outdir / "aws_export_smoke.json"
    mpath = outdir / "aws_export_smoke.md"

    jpath.write_text(json.dumps(asdict(res), indent=2) + "\n", encoding="utf-8")

    lines = []
    lines.append("# AWS Export Smoke")
    lines.append(f"- timestamp_utc: {res.timestamp_utc}")
    lines.append(f"- ok: **{res.ok}**")
    lines.append(f"- reason: `{res.reason}`")
    lines.append(f"- export_remote: `{res.export_remote}`")
    lines.append(f"- export_prefix: `{res.export_prefix}`")
    lines.append(f"- rclone_present: `{res.rclone_present}`")
    lines.append(f"- listed_ok: `{res.listed_ok}`")
    lines.append("")
    lines.append("## Sample listing (max 25)")
    if res.sample_listing:
        for x in res.sample_listing:
            lines.append(f"- {x}")
    else:
        lines.append("- (none)")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
