#!/usr/bin/env python3
"""Hard-gated write+delete smoke for AWS export target."""

import base64
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class WriteSmokeResult:
    ok: bool
    reason: str
    export_remote: str
    export_prefix: str
    target_path: str
    wrote: bool
    deleted: bool
    timestamp_utc: str
    notes: list[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def main() -> int:
    ts = _utc_now()

    export_remote = os.getenv("PT_EXPORT_REMOTE", "").strip()
    export_prefix = os.getenv("PT_EXPORT_PREFIX", "").strip()
    rclone_conf_b64 = os.getenv("PT_RCLONE_CONF_B64", "").strip()
    enabled = os.getenv("PT_EXPORT_SMOKE_WRITE_ENABLED", "").strip().lower() == "true"
    confirm = os.getenv("PT_EXPORT_SMOKE_CONFIRM_TOKEN", "").strip()

    notes: list[str] = []
    if not enabled:
        res = WriteSmokeResult(
            ok=False,
            reason="WRITE_SMOKE_DISABLED",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path="",
            wrote=False,
            deleted=False,
            timestamp_utc=ts,
            notes=["Set repo variable PT_EXPORT_SMOKE_WRITE_ENABLED=true to allow writes."],
        )
        _write_reports(res)
        return 2

    if confirm != "YES_WRITE_SMOKE":
        res = WriteSmokeResult(
            ok=False,
            reason="CONFIRM_TOKEN_MISSING",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path="",
            wrote=False,
            deleted=False,
            timestamp_utc=ts,
            notes=["Provide workflow_dispatch input confirm_token=YES_WRITE_SMOKE."],
        )
        _write_reports(res)
        return 2

    if not export_remote or not rclone_conf_b64:
        res = WriteSmokeResult(
            ok=False,
            reason="MISSING_EXPORT_CONFIG",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path="",
            wrote=False,
            deleted=False,
            timestamp_utc=ts,
            notes=["Missing PT_EXPORT_REMOTE or PT_RCLONE_CONF_B64."],
        )
        _write_reports(res)
        return 2

    if subprocess.call(["bash", "-lc", "command -v rclone >/dev/null 2>&1"]) != 0:
        res = WriteSmokeResult(
            ok=False,
            reason="MISSING_RCLONE",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path="",
            wrote=False,
            deleted=False,
            timestamp_utc=ts,
            notes=["rclone not installed on runner."],
        )
        _write_reports(res)
        return 2

    conf_dir = Path(".cache/rclone")
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_path = conf_dir / "rclone.conf"
    conf_path.write_bytes(base64.b64decode(rclone_conf_b64))

    env = os.environ.copy()
    env["RCLONE_CONFIG"] = str(conf_path)
    # Skip bucket existence check/creation (pt-gh-export-consumer has no s3:CreateBucket)
    env["RCLONE_S3_NO_CHECK_BUCKET"] = "true"

    base = export_remote.rstrip("/")
    prefix = export_prefix.strip().strip("/")
    smoke_prefix = "_smoke/aws_export_write_smoke"
    fname = f"{ts.replace(':', '').replace('.', '')}.txt"

    target = base
    if prefix:
        target = f"{base}/{prefix}"
    target = f"{target}/{smoke_prefix}/{fname}"

    tmp = Path(".cache/aws_export_write_smoke.txt")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(f"aws_export_write_smoke {ts}\n", encoding="utf-8")

    wrote = False
    deleted = False

    cp = _run(["rclone", "copyto", str(tmp), target], env=env)
    if cp.returncode != 0:
        res = WriteSmokeResult(
            ok=False,
            reason="RCLONE_WRITE_FAILED",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path=target,
            wrote=False,
            deleted=False,
            timestamp_utc=ts,
            notes=(cp.stderr.splitlines() + cp.stdout.splitlines())[:25],
        )
        _write_reports(res)
        return 2
    wrote = True

    cp2 = _run(["rclone", "deletefile", target], env=env)
    if cp2.returncode != 0:
        stderr = cp2.stderr or ""
        # If IAM forbids DeleteObject, treat as warning (write-path verified; cleanup via lifecycle)
        if "AccessDenied" in stderr or "access denied" in stderr.lower():
            res = WriteSmokeResult(
                ok=True,
                reason="DELETE_DENIED_WARNING",
                export_remote=export_remote,
                export_prefix=export_prefix,
                target_path=target,
                wrote=True,
                deleted=False,
                timestamp_utc=ts,
                notes=[
                    "Delete denied (likely missing s3:DeleteObject). Write-path verified.",
                    "Recommended: configure S3 lifecycle to expire _smoke/aws_export_write_smoke/* quickly (e.g. 1 day).",
                ]
                + (cp2.stderr.splitlines() + cp2.stdout.splitlines())[:10],
            )
            _write_reports(res)
            return 0
        res = WriteSmokeResult(
            ok=False,
            reason="RCLONE_DELETE_FAILED",
            export_remote=export_remote,
            export_prefix=export_prefix,
            target_path=target,
            wrote=True,
            deleted=False,
            timestamp_utc=ts,
            notes=(cp2.stderr.splitlines() + cp2.stdout.splitlines())[:25],
        )
        _write_reports(res)
        return 2
    deleted = True

    res = WriteSmokeResult(
        ok=True,
        reason="OK",
        export_remote=export_remote,
        export_prefix=export_prefix,
        target_path=target,
        wrote=wrote,
        deleted=deleted,
        timestamp_utc=ts,
        notes=notes,
    )
    _write_reports(res)
    return 0


def _write_reports(res: WriteSmokeResult) -> None:
    outdir = Path("reports/status")
    outdir.mkdir(parents=True, exist_ok=True)
    jpath = outdir / "aws_export_write_smoke.json"
    mpath = outdir / "aws_export_write_smoke.md"

    jpath.write_text(json.dumps(asdict(res), indent=2) + "\n", encoding="utf-8")

    lines = []
    lines.append("# AWS Export Write Smoke")
    lines.append(f"- timestamp_utc: {res.timestamp_utc}")
    lines.append(f"- ok: **{res.ok}**")
    lines.append(f"- reason: `{res.reason}`")
    lines.append(f"- export_remote: `{res.export_remote}`")
    lines.append(f"- export_prefix: `{res.export_prefix}`")
    lines.append(f"- target_path: `{res.target_path}`")
    lines.append(f"- wrote: `{res.wrote}`")
    lines.append(f"- deleted: `{res.deleted}`")
    lines.append("")
    lines.append("## Notes (max 25)")
    if res.notes:
        for x in res.notes[:25]:
            lines.append(f"- {x}")
    else:
        lines.append("- (none)")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
