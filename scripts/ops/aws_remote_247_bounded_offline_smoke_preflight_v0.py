#!/usr/bin/env python3
"""Bounded offline AWS Remote 247 smoke preflight (fixture + durable evidence only).

Non-network, non-executing: validates G1-G6 using local fixture input and writes
durable evidence under --durable-output-dir. Does not call AWS, SSH, S3 upload,
or start any runtime lane.

Machine marker: ``AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_PREFLIGHT_V0=true``
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.preflight_remote_runtime_runner_v0 import run_preflight as run_remote_preflight
from scripts.ops.preflight_s3_finalized_evidence_export_v0 import run_preflight as run_s3_preflight
from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)

SCHEMA_VERSION = "peak_trade.aws_remote_247_bounded_offline_smoke_preflight.v0"
PREFLIGHT_NAME = "aws_remote_247_bounded_offline_smoke_preflight_v0"
REQUIRED_APPROVED_SCOPE = "aws_remote_247_bounded_offline_smoke_implementation_v0"
MANIFEST_FILENAME = "MANIFEST.sha256"
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)secret[_-]?key\s*[:=]"),
    re.compile(r"(?i)aws_secret_access_key"),
)

REMOTE_BOUNDARY_BOOLS_FALSE = (
    "runner_implemented",
    "aws_cli_called",
    "network_called",
    "s3_upload_called",
    "live_authority",
)

S3_BOUNDARY_BOOLS_FALSE = (
    "aws_cli_called",
    "upload_called",
    "network_actions_called",
    "live_authority",
)

SAFETY_MACHINE_LINES: dict[str, str] = {
    "START_RUNTIME_NOW": "false",
    "START_SCHEDULER_NOW": "false",
    "START_SUPERVISOR_NOW": "false",
    "START_DAEMON_NOW": "false",
    "START_PAPER_NOW": "false",
    "START_SHADOW_NOW": "false",
    "START_TESTNET_NOW": "false",
    "START_LIVE_NOW": "false",
    "AWS_REMOTE_TOUCHED": "false",
    "S3_UPLOAD_REQUIRED": "false",
    "SSH_REQUIRED": "false",
    "NETWORK_REQUIRED": "false",
    "LIVE_AUTHORITY_CHANGED": "false",
}


@dataclass(frozen=True)
class GateResults:
    g1: bool
    g2: bool
    g3: bool
    g4: bool
    g5: bool
    g6: bool
    reasons: tuple[str, ...]

    @property
    def all_pass(self) -> bool:
        return self.g1 and self.g2 and self.g3 and self.g4 and self.g5 and self.g6


def _fail_reasons(*parts: str) -> tuple[str, ...]:
    return tuple(p for p in parts if p)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_has_no_secret_literals(
    fixture_path: Path, payload: dict[str, Any]
) -> tuple[bool, str]:
    text = fixture_path.read_text(encoding="utf-8") + json.dumps(payload, sort_keys=True)
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if pattern.search(text):
            return False, f"forbidden_secret_pattern:{pattern.pattern}"
    return True, ""


def _write_registry(
    path: Path,
    *,
    archive_root: Path,
    run_id: str,
    lane_id: str,
    archive_path: str,
    evidence_transport: str,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "peak_trade.generic_evidence_run_registry.v1",
                "archive_root": str(archive_root.resolve()),
                "runs": [
                    {
                        "run_id": run_id,
                        "lane_id": lane_id,
                        "archive_path": archive_path,
                        "evidence_transport": evidence_transport,
                        "manifest_verified": True,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_synthetic_evidence_root(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    (root / "evidence.txt").write_text("aws_remote_247_offline_smoke_fixture", encoding="utf-8")
    write_manifest_sha256(root)


def _verify_gate_g1(*, approved_scope_name: str, fixture: dict[str, Any]) -> tuple[bool, str]:
    if approved_scope_name != REQUIRED_APPROVED_SCOPE:
        return False, "approved_scope_name_mismatch"
    if fixture.get("approved_scope_name") != REQUIRED_APPROVED_SCOPE:
        return False, "fixture_approved_scope_mismatch"
    return True, ""


def _verify_gate_g2(fixture: dict[str, Any]) -> tuple[bool, str]:
    if (
        fixture.get("schema_version")
        != "peak_trade.aws_remote_247_bounded_offline_smoke_fixture.v0"
    ):
        return False, "invalid_fixture_schema_version"
    inv = fixture.get("offline_inventory")
    if not isinstance(inv, dict):
        return False, "offline_inventory_missing"
    required = (
        "remote_run_id",
        "lane_id",
        "host_inventory_relpath",
        "evidence_transport",
    )
    for key in required:
        if key not in inv:
            return False, f"offline_inventory_missing:{key}"
    return True, ""


def _verify_gate_g3(fixture_path: Path, fixture: dict[str, Any]) -> tuple[bool, str]:
    cred = fixture.get("credential_boundary")
    if not isinstance(cred, dict):
        return False, "credential_boundary_missing"
    for key in (
        "secrets_present",
        "broker_credentials_present",
        "exchange_credentials_present",
        "aws_profile_required",
    ):
        if cred.get(key) is not False:
            return False, f"credential_boundary_must_be_false:{key}"
    ok, msg = _fixture_has_no_secret_literals(fixture_path, fixture)
    if not ok:
        return False, msg
    inv_path = fixture_path.parent / fixture["offline_inventory"]["host_inventory_relpath"]
    if not inv_path.is_file():
        return False, "host_inventory_missing"
    inv = _load_json(inv_path)
    if inv.get("secrets_present") is not False:
        return False, "host_inventory_secrets_present"
    if inv.get("aws_cli_called") is not False:
        return False, "host_inventory_aws_cli_called"
    if inv.get("ssh_called") is not False:
        return False, "host_inventory_ssh_called"
    return True, ""


def _verify_gate_g4(
    *,
    fixture: dict[str, Any],
    work_dir: Path,
) -> tuple[bool, str]:
    inv = fixture["offline_inventory"]
    run_id = str(inv["remote_run_id"])
    lane_id = str(inv["lane_id"])
    archive_path = str(inv.get("archive_path", "synthetic_evidence"))
    evidence_root = work_dir / archive_path
    _write_synthetic_evidence_root(evidence_root)
    registry_path = work_dir / "registry_v1.json"
    _write_registry(
        registry_path,
        archive_root=work_dir,
        run_id=run_id,
        lane_id=lane_id,
        archive_path=archive_path,
        evidence_transport=str(inv.get("registry_evidence_transport", "local_only")),
    )
    remote = run_remote_preflight(
        dry_run=True,
        no_network=True,
        runtime_host=str(inv.get("runtime_host", "remote")),
        runtime_backend=str(inv.get("runtime_backend", "ec2")),
        runtime_mode=str(inv.get("runtime_mode", "paper_only")),
        lane_id=lane_id,
        remote_run_id=run_id,
        max_runtime_seconds=int(inv.get("max_runtime_seconds", 3600)),
        evidence_root_type=str(inv.get("evidence_root_type", "remote_durable")),
        evidence_transport=str(inv.get("evidence_transport", "local_only")),
        registry_json=registry_path,
        s3_prefix_plan_json=None,
        approval_record=None,
        scheduler_guard_json=None,
    )
    if remote.get("status") not in {"eligible", "blocked"}:
        return False, f"remote_preflight_status:{remote.get('status')}"
    if remote.get("dry_run") is not True or remote.get("no_network") is not True:
        return False, "remote_preflight_missing_dry_run_or_no_network"
    for field in REMOTE_BOUNDARY_BOOLS_FALSE:
        if remote.get(field) is not False:
            return False, f"remote_preflight_boundary:{field}"
    s3 = run_s3_preflight(
        evidence_root,
        dry_run=True,
        no_network=True,
        run_id=run_id,
        lane_id=lane_id,
        export_prefix_plan=True,
    )
    if s3.get("status") != "eligible":
        return False, f"s3_preflight_status:{s3.get('status')}"
    for field in S3_BOUNDARY_BOOLS_FALSE:
        if s3.get(field) is not False:
            return False, f"s3_preflight_boundary:{field}"
    return True, ""


def _verify_gate_g5(output_dir: Path) -> tuple[bool, str]:
    if is_under_tmp(output_dir):
        return False, "durable_output_dir_under_tmp"
    return True, ""


def _verify_gate_g6(
    *,
    g1: bool,
    g2: bool,
    g3: bool,
    g4: bool,
    g5: bool,
    fail_closed: bool,
) -> tuple[bool, str]:
    prior_pass = g1 and g2 and g3 and g4 and g5
    if fail_closed and not prior_pass:
        return False, "fail_closed_closeout:any_gate_false"
    if prior_pass:
        return True, ""
    return False, "gates_incomplete"


def run_bounded_offline_smoke_preflight(
    *,
    fixture_path: Path,
    durable_output_dir: Path,
    approved_scope_name: str,
    offline: bool,
    no_network: bool,
) -> tuple[GateResults, dict[str, Any]]:
    reasons: list[str] = []
    if not offline:
        reasons.append("offline_flag_required")
    if not no_network:
        reasons.append("no_network_flag_required")
    if not fixture_path.is_file():
        reasons.append("fixture_missing")
    if reasons:
        gates = GateResults(False, False, False, False, False, False, tuple(reasons))
        return gates, _build_report(
            gates, reasons, durable_output_dir, fixture_path, approved_scope_name
        )

    fixture = _load_json(fixture_path)
    g1, r1 = _verify_gate_g1(approved_scope_name=approved_scope_name, fixture=fixture)
    if r1:
        reasons.append(r1)
    g2, r2 = _verify_gate_g2(fixture)
    if r2:
        reasons.append(r2)
    g3, r3 = _verify_gate_g3(fixture_path, fixture)
    if r3:
        reasons.append(r3)

    g4 = False
    if g1 and g2 and g3:
        work = durable_output_dir / "work"
        work.mkdir(parents=True, exist_ok=True)
        g4, r4 = _verify_gate_g4(fixture=fixture, work_dir=work)
        if r4:
            reasons.append(r4)
    else:
        reasons.append("g4_skipped_prior_gates_failed")

    g5, r5 = _verify_gate_g5(durable_output_dir)
    if r5:
        reasons.append(r5)
    if g5:
        durable_output_dir.mkdir(parents=True, exist_ok=True)

    fail_closed = bool(fixture.get("closeout_plan", {}).get("fail_closed_on_any_gate_false", True))
    g6, r6 = _verify_gate_g6(g1=g1, g2=g2, g3=g3, g4=g4, g5=g5, fail_closed=fail_closed)
    if r6:
        reasons.append(r6)
    gates = GateResults(g1, g2, g3, g4, g5, g6, tuple(reasons))
    report = _build_report(
        gates, list(gates.reasons), durable_output_dir, fixture_path, approved_scope_name
    )
    return gates, report


def _build_report(
    gates: GateResults,
    reasons: list[str],
    output_dir: Path,
    fixture_path: Path,
    approved_scope_name: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_name": PREFLIGHT_NAME,
        "status": "pass" if gates.all_pass else "blocked",
        "fixture": str(fixture_path.resolve()),
        "durable_output_dir": str(output_dir.resolve()),
        "approved_scope_name": approved_scope_name,
        "gates": {
            "G1_OPERATOR_SCOPE_VERIFIED": gates.g1,
            "G2_OFFLINE_INVENTORY_VERIFIED": gates.g2,
            "G3_CREDENTIAL_BOUNDARY_VERIFIED": gates.g3,
            "G4_REMOTE_S3_DRY_RUN_CONTRACT_VERIFIED": gates.g4,
            "G5_DURABLE_EVIDENCE_DESTINATION_VERIFIED": gates.g5,
            "G6_FAIL_CLOSED_CLOSEOUT_VERIFIED": gates.g6,
        },
        "reasons": reasons,
    }


def _write_machine_lines(path: Path, gates: GateResults, report: dict[str, Any]) -> None:
    lines = [
        "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_PREFLIGHT_V0=true",
        f"G1_OPERATOR_SCOPE_VERIFIED={'true' if gates.g1 else 'false'}",
        f"G2_OFFLINE_INVENTORY_VERIFIED={'true' if gates.g2 else 'false'}",
        f"G3_CREDENTIAL_BOUNDARY_VERIFIED={'true' if gates.g3 else 'false'}",
        f"G4_REMOTE_S3_DRY_RUN_CONTRACT_VERIFIED={'true' if gates.g4 else 'false'}",
        f"G5_DURABLE_EVIDENCE_DESTINATION_VERIFIED={'true' if gates.g5 else 'false'}",
        f"G6_FAIL_CLOSED_CLOSEOUT_VERIFIED={'true' if gates.g6 else 'false'}",
        f"BOUNDED_OFFLINE_SMOKE_STATUS={report['status']}",
    ]
    lines.extend(f"{k}={v}" for k, v in SAFETY_MACHINE_LINES.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_durable_evidence(
    output_dir: Path,
    gates: GateResults,
    report: dict[str, Any],
) -> tuple[bool, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_lines = [
        "# AWS Remote 247 Bounded Offline Smoke Preflight Report",
        "",
        f"- status: {report['status']}",
        f"- fixture: `{report['fixture']}`",
        "",
        "## Gates",
    ]
    for key, val in report["gates"].items():
        md_lines.append(f"- {key}: {str(val).lower()}")
    if report["reasons"]:
        md_lines.extend(["", "## Reasons", *[f"- {r}" for r in report["reasons"]]])
    (output_dir / "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_REPORT.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines(output_dir / "FINAL_MACHINE_LINES.txt", gates, report)
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    verify_log = output_dir / "MANIFEST_VERIFY.log"
    if ok:
        verify_log.write_text("MANIFEST_VERIFY_RC=0\n", encoding="utf-8")
    else:
        verify_log.write_text(f"MANIFEST_VERIFY_RC=1\n{msg}\n", encoding="utf-8")
    return ok, msg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded offline AWS Remote 247 smoke preflight (fixture only; no network)."
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--durable-output-dir", type=Path, required=True)
    parser.add_argument("--approved-scope-name", required=True)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--no-network", action="store_true", required=True)
    args = parser.parse_args(argv)

    if is_under_tmp(args.durable_output_dir):
        sys.stderr.write("durable-output-dir must be outside /tmp\n")
        return 2

    gates, report = run_bounded_offline_smoke_preflight(
        fixture_path=args.fixture.resolve(),
        durable_output_dir=args.durable_output_dir.resolve(),
        approved_scope_name=args.approved_scope_name,
        offline=args.offline,
        no_network=args.no_network,
    )
    manifest_ok, manifest_msg = _write_durable_evidence(
        args.durable_output_dir.resolve(),
        gates,
        report,
    )
    if not manifest_ok:
        report["reasons"] = list(report.get("reasons", [])) + [f"manifest_verify:{manifest_msg}"]
        gates = GateResults(
            gates.g1,
            gates.g2,
            gates.g3,
            gates.g4,
            False,
            gates.g6,
            gates.reasons + (f"manifest_verify:{manifest_msg}",),
        )

    for line in (
        (args.durable_output_dir / "FINAL_MACHINE_LINES.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        if line.strip():
            sys.stdout.write(line + "\n")

    if gates.all_pass and manifest_ok:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
