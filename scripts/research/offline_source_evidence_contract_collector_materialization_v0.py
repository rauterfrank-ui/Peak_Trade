#!/usr/bin/env python3
"""Execute offline source evidence contract collector/materialization v0.

Read-only collector/materializer for PR4911-defined source-evidence contracts.
No economic evaluation, no runtime authority, no performance claims.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.offline_source_evidence_contract_collector_materialization_v0 import (  # noqa: E402
    CONTRACT_IDS,
    EXECUTION_ID,
    EXECUTION_STATUS,
    OPERATOR_GO,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    collect_all_contracts,
    deterministic_collection_digest,
    parent_manifest_ref,
    sha256_path,
    write_jsonl,
)

DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/offline_source_evidence_contract_collector_materialization_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "offline_source_evidence_contract_collector_materialization_v0"
PARENT_PR4911_CLOSEOUT_SUFFIX = (
    "offline_source_evidence_instrumentation_admissibility_gap_merge_closeout_20260706T053813Z"
)
PARENT_PR4909_MATERIALIZATION_SUFFIX = (
    "post_pr4908_offline_terminal_failure_artifact_materialization_v0_20260706T051227Z"
)
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
NEXT_STEP = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_VALIDATION_OR_"
    "ADMISSIBILITY_GATE_EXECUTION_SCOPE_V0"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _require_config_gates(config: dict[str, Any]) -> None:
    if config.get("scope_id") != SCOPE_ID:
        _die("ERR:config scope_id mismatch")
    if config.get("execution_id") != EXECUTION_ID:
        _die("ERR:config execution_id mismatch")
    if config.get("non_authorizing") is not True:
        _die("ERR:config non_authorizing must be true")
    if config.get("source_evidence_only") is not True:
        _die("ERR:config source_evidence_only must be true")
    if config.get("no_economic_claim") is not True:
        _die("ERR:config no_economic_claim must be true")
    for flag in (
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "runtime_authority",
        "orders_allowed",
        "scheduler_runtime_allowed",
        "live_authorized",
        "failed_evidence_is_terminal",
    ):
        expected = flag == "failed_evidence_is_terminal"
        if config.get(flag) is not expected:
            _die(f"ERR:config {flag} must be {expected}")


def _verify_source_manifest(source_ref: Path, log_path: Path) -> int:
    ok, msg = verify_manifest_sha256(source_ref)
    rc = 0 if ok else 1
    log_path.write_text(
        "\n".join(
            [
                f"SOURCE_EVIDENCE_REF={source_ref}",
                f"MANIFEST_VERIFY_RC={rc}",
                f"MANIFEST_VERIFY_MSG={msg or 'ok'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rc


def run_offline_source_evidence_contract_collector_materialization_v0(
    *,
    go_token: str,
    parent_pr4911_closeout_dir: Path,
    parent_pr4909_materialization_bundle: Path,
    parent_evaluation_bundle: Path,
    durable_archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if go_token != OPERATOR_GO:
        _die("ERR:invalid go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    _require_config_gates(config)

    for label, ref in (
        ("parent_pr4911_closeout_dir", parent_pr4911_closeout_dir),
        ("parent_pr4909_materialization_bundle", parent_pr4909_materialization_bundle),
        ("parent_evaluation_bundle", parent_evaluation_bundle),
    ):
        if not ref.is_dir():
            _die(f"ERR:missing {label}: {ref}")

    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    manifest_status: dict[str, int] = {}
    for key, ref in (
        ("parent_pr4911_closeout_dir", parent_pr4911_closeout_dir),
        ("parent_pr4909_materialization_bundle", parent_pr4909_materialization_bundle),
        ("parent_evaluation_bundle", parent_evaluation_bundle),
    ):
        rc = _verify_source_manifest(ref, output_dir / f"{key}_manifest_verify.log")
        manifest_status[key] = rc
        if rc != 0:
            _die(f"ERR:manifest invalid for {key}: {ref}")

    parent_manifest_digest = parent_manifest_ref(parent_evaluation_bundle)
    collection = collect_all_contracts(
        parent_evaluation_ref=parent_evaluation_bundle,
        parent_manifest_digest=parent_manifest_digest,
    )
    if collection["validation_errors"]:
        _die(f"ERR:contract validation failed: {collection['validation_errors']}")

    git_snapshot = _git_snapshot()
    config_digest = sha256_path(config_path)
    implementation_digest = sha256_path(
        _REPO_ROOT / "src/research/offline_source_evidence_contract_collector_materialization_v0.py"
    )
    data_digest = deterministic_collection_digest(collection["contracts"])

    for contract_id in CONTRACT_IDS:
        contract_payload = collection["contracts"][contract_id]
        (output_dir / f"{contract_id}.json").write_text(
            json.dumps(contract_payload["envelope"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_jsonl(output_dir / f"{contract_id}.jsonl", contract_payload["records"])

    report = {
        "verdict": EXECUTION_STATUS,
        "execution_status": EXECUTION_STATUS,
        "execution_id": EXECUTION_ID,
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "source_evidence_only": True,
        "no_economic_claim": True,
        "no_runtime_authority": True,
        "contracts_materialized": list(CONTRACT_IDS),
        "contract_record_counts": {
            contract_id: len(collection["contracts"][contract_id]["records"])
            for contract_id in CONTRACT_IDS
        },
        "parent_bindings": {
            "parent_pr4911_closeout_dir": str(parent_pr4911_closeout_dir),
            "parent_pr4909_materialization_bundle": str(parent_pr4909_materialization_bundle),
            "parent_evaluation_bundle": str(parent_evaluation_bundle),
        },
        "parent_manifest_status": manifest_status,
        "git_snapshot": git_snapshot,
        "go_token_consumed": OPERATOR_GO,
        "config_digest": config_digest,
        "implementation_digest": implementation_digest,
        "data_digest": data_digest,
        "authority_boundary": {
            "economic_evaluation_executed": False,
            "runtime_authority_granted": False,
            "orders_allowed": False,
            "scheduler_runtime_allowed": False,
            "live_authorized": False,
            "failed_evidence_is_terminal": True,
        },
        "next_step": NEXT_STEP,
        "durable_evidence_path": str(output_dir),
    }
    (output_dir / "SOURCE_EVIDENCE_COLLECTION_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_manifest_verification.json").write_text(
        json.dumps(
            {
                "manifest_verify_results": manifest_status,
                "all_parent_manifests_verified": all(rc == 0 for rc in manifest_status.values()),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "execution_summary.json").write_text(
        json.dumps(
            {
                "verdict": EXECUTION_STATUS,
                "contracts_materialized": list(CONTRACT_IDS),
                "source_evidence_only": True,
                "no_economic_claim": True,
                "runtime_authority_granted": False,
                "next_step": NEXT_STEP,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir.joinpath("AUTHORITY_BOUNDARY.txt").write_text(
        "\n".join(
            [
                "SOURCE_EVIDENCE_ONLY=true",
                "NO_ECONOMIC_CLAIM=true",
                "NO_RUNTIME_AUTHORITY=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "RUNTIME_AUTHORITY_GRANTED=false",
                "ORDERS_ALLOWED=false",
                "SCHEDULER_RUNTIME_ALLOWED=false",
                "LIVE_AUTHORIZED=false",
                "FAILED_EVIDENCE_IS_TERMINAL=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_rc = 0 if verify_manifest_sha256(output_dir)[0] else 1
    if manifest_rc != 0:
        _die(f"ERR:output manifest verify failed: {output_dir}")

    return {
        "verdict": EXECUTION_STATUS,
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "contracts_materialized": list(CONTRACT_IDS),
        "data_digest": data_digest,
        "next_step": NEXT_STEP,
        "parent_manifest_verify_results": manifest_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute offline source evidence contract collector/materialization v0"
    )
    parser.add_argument("--go-token", required=True, choices=[OPERATOR_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    archive = args.durable_evidence_root
    result = run_offline_source_evidence_contract_collector_materialization_v0(
        go_token=args.go_token,
        parent_pr4911_closeout_dir=archive / "implementation" / PARENT_PR4911_CLOSEOUT_SUFFIX,
        parent_pr4909_materialization_bundle=archive
        / "implementation"
        / PARENT_PR4909_MATERIALIZATION_SUFFIX,
        parent_evaluation_bundle=archive / "implementation" / PARENT_EVALUATION_SUFFIX,
        durable_archive_root=archive,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    for key, value in result.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
