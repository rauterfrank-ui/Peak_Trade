#!/usr/bin/env python3
"""Materialize parent closeout manifest precondition gap fix v0.

Offline-only corrective provenance/materialization. No economic evaluation,
no runtime authority, no historical bundle mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
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

SCOPE_ID = "OFFLINE_SOURCE_EVIDENCE_PARENT_CLOSEOUT_MANIFEST_PRECONDITION_GAP_FIX_V0"
VERDICT_TARGET = "PRECONDITION_GAP_FIX_COMPLETE"
PROCESS_CLASSIFICATION = "OFFLINE_SOURCE_EVIDENCE_PARENT_CLOSEOUT_MANIFEST_PRECONDITION_GAP_FIX_V0"
SCOPE_CLASSIFICATION = (
    "PRECONDITION_PROVENANCE_MATERIALIZATION_ONLY_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0"
)
GO_TOKEN = (
    "GO_NARROW_PARENT_CLOSEOUT_MANIFEST_PRECONDITION_GAP_FIX_AFTER_ADMISSIBILITY_FAIL_PR4914_V0"
)
FAILURE_CLASS = "CLOSEOUT_MD_MODIFIED_AFTER_MANIFEST_WRITE"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0"
SUPERSEDING_SUBDIR = "superseding_parent_closeout"
MISSING_SOURCE_EVIDENCE = "MISSING_SOURCE_EVIDENCE"

FORBIDDEN_AUTHORITY_FLAGS = (
    "economic_evaluation_authorized",
    "economic_evaluation_executed",
    "economic_viability_evidence_emitted",
    "economic_viability_claimed",
    "runtime_authority_granted",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "adapter_submission_allowed",
    "credentials_required",
    "arming_allowed",
    "canary_authorized",
    "core_system_mutation_allowed",
    "canonical_trading_logic_mutation_allowed",
    "master_v2_mutation_allowed",
    "double_play_mutation_allowed",
    "risk_sizing_mutation_allowed",
    "safety_runtime_mutation_allowed",
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_rel_path(rel_path: str) -> str:
    return rel_path.removeprefix("./")


def _parse_manifest_entries(manifest_path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        entries.append((parts[0], parts[1]))
    return entries


def _parse_closeout_field(text: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}=(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("verdict_target") != VERDICT_TARGET:
        errors.append("unexpected verdict_target")
    if config.get("go_token") != GO_TOKEN:
        errors.append("unexpected go_token")
    if config.get("parent_pr") != 4913:
        errors.append("unexpected parent_pr")
    if config.get("admissibility_review_pr") != 4914:
        errors.append("unexpected admissibility_review_pr")
    if config.get("expected_failure_class") != FAILURE_CLASS:
        errors.append("unexpected expected_failure_class")
    if config.get("historical_bundle_mutation_allowed") is not False:
        errors.append("historical_bundle_mutation_allowed must be false")
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if config.get(flag) is not False:
            errors.append(f"forbidden authority flag must be false: {flag}")
    return errors


def _manifest_file_results(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return {}
    results: dict[str, dict[str, Any]] = {}
    for digest, rel_path in _parse_manifest_entries(manifest_path):
        file_path = bundle_dir / rel_path.removeprefix("./")
        actual_digest = _sha256_bytes(file_path.read_bytes()) if file_path.is_file() else None
        results[rel_path] = {
            "expected_digest": digest,
            "actual_digest": actual_digest,
            "match": actual_digest == digest,
        }
    return results


def _reconstruct_closeout_md(original_text: str, expected_digest: str) -> str | None:
    if _sha256_bytes(original_text.encode("utf-8")) == expected_digest:
        return original_text
    lines = original_text.splitlines()
    for end in range(len(lines), 0, -1):
        candidate = "\n".join(lines[:end]) + "\n"
        if _sha256_bytes(candidate.encode("utf-8")) == expected_digest:
            return candidate
    return None


def classify_invalid_parent_manifest(invalid_parent: Path) -> dict[str, Any]:
    manifest_rc = 1
    manifest_msg = "unknown"
    ok, msg = verify_manifest_sha256(invalid_parent)
    manifest_rc = 0 if ok else 1
    manifest_msg = msg or "ok"

    file_results = _manifest_file_results(invalid_parent)
    mismatched = [path for path, item in file_results.items() if not item["match"]]
    matched = [path for path, item in file_results.items() if item["match"]]
    mismatched_norm = {_normalize_rel_path(path) for path in mismatched}

    failure_class = "UNKNOWN_MANIFEST_FAILURE"
    closeout_keys = [path for path in file_results if _normalize_rel_path(path) == "CLOSEOUT.md"]
    if manifest_rc == 1 and mismatched_norm == {"CLOSEOUT.md"} and matched and closeout_keys:
        closeout_path = invalid_parent / "CLOSEOUT.md"
        closeout_text = closeout_path.read_text(encoding="utf-8")
        expected_digest = file_results[closeout_keys[0]]["expected_digest"]
        reconstructed = _reconstruct_closeout_md(closeout_text, expected_digest)
        if reconstructed is not None and reconstructed != closeout_text:
            failure_class = FAILURE_CLASS

    closeout_text = (invalid_parent / "CLOSEOUT.md").read_text(encoding="utf-8")
    return {
        "invalid_parent_closeout_dir": str(invalid_parent),
        "parent_closeout_manifest_verify_rc": manifest_rc,
        "parent_closeout_manifest_verify_msg": manifest_msg,
        "failure_class": failure_class,
        "manifest_file_results": file_results,
        "mismatched_files": mismatched,
        "matched_files": matched,
        "closeout_fields": {
            "PRE_MERGE_ORIGIN_MAIN": _parse_closeout_field(closeout_text, "PRE_MERGE_ORIGIN_MAIN"),
            "PR_HEAD": _parse_closeout_field(closeout_text, "PR_HEAD"),
            "POST_MERGE_HEAD": _parse_closeout_field(closeout_text, "POST_MERGE_HEAD"),
            "MERGE_COMMIT": _parse_closeout_field(closeout_text, "MERGE_COMMIT"),
        },
        "historical_bundle_preserved": True,
        "historical_bundle_mutated": False,
    }


def _count_missing_source_sentinels(bundle_dir: Path) -> tuple[int, int]:
    total = 0
    missing = 0
    if not bundle_dir.is_dir():
        return 0, 0
    for jsonl_path in bundle_dir.glob("*.jsonl"):
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            total += 1
            record = json.loads(line)
            if any(
                isinstance(value, dict) and value.get("status") == MISSING_SOURCE_EVIDENCE
                for value in record.values()
            ):
                missing += 1
    return missing, total


def materialize_superseding_parent_closeout(
    invalid_parent: Path,
    output_dir: Path,
    invalid_provenance: dict[str, Any],
) -> Path:
    superseding_dir = output_dir / SUPERSEDING_SUBDIR
    superseding_dir.mkdir(parents=True)

    file_results = invalid_provenance["manifest_file_results"]
    for rel_path, item in file_results.items():
        normalized = _normalize_rel_path(rel_path)
        src = invalid_parent / normalized
        dst = superseding_dir / normalized
        if normalized == "CLOSEOUT.md":
            original_text = src.read_text(encoding="utf-8")
            reconstructed = _reconstruct_closeout_md(original_text, item["expected_digest"])
            if reconstructed is None:
                _die(f"ERR:unable to reconstruct manifest-correct CLOSEOUT.md for {invalid_parent}")
            dst.write_text(reconstructed, encoding="utf-8")
        else:
            shutil.copy2(src, dst)

    write_manifest_sha256(superseding_dir)
    ok, msg = verify_manifest_sha256(superseding_dir)
    if not ok:
        _die(f"ERR:superseding parent closeout manifest verify failed: {msg}")
    return superseding_dir


def _write_findings_md(
    output_dir: Path,
    invalid_provenance: dict[str, Any],
    superseding_dir: Path,
    config: dict[str, Any],
) -> None:
    lines = [
        "# Precondition Fix Findings",
        "",
        f"- verdict_target: `{VERDICT_TARGET}`",
        f"- scope_id: `{SCOPE_ID}`",
        f"- failure_class: `{invalid_provenance['failure_class']}`",
        f"- parent_closeout_manifest_verify_rc: `{invalid_provenance['parent_closeout_manifest_verify_rc']}`",
        f"- admissibility_review_pr: `{config['admissibility_review_pr']}`",
        f"- admissibility_review_verdict: `{config['admissibility_review_verdict']}`",
        "",
        "## Root Cause",
        "",
        (
            "PR #4913 merge closeout wrote MANIFEST.sha256 before appending "
            "`MANIFEST_VERIFY_RC=0` to CLOSEOUT.md."
        ),
        "The historical parent bundle fails verification with checksum mismatch on `./CLOSEOUT.md`.",
        "PR #4914 admissibility review hard-blocked on `source_evidence_manifest_integrity`.",
        "",
        "## Corrective Action",
        "",
        f"- invalid parent bundle preserved unchanged: `{invalid_provenance['invalid_parent_closeout_dir']}`",
        f"- superseding manifest-correct snapshot: `{superseding_dir}`",
        "- no historical negative/inadmissible evidence mutated",
        "- no EconomicViabilityEvidenceV1 emitted",
        "- no economic evaluation executed",
        "- no runtime authority granted",
        "",
        "## Next Step",
        "",
        f"`{config['next_step']}`",
        "",
    ]
    output_dir.joinpath("PRECONDITION_FIX_FINDINGS.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
    *,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    invalid_parent = Path(config["invalid_parent_closeout_dir"])
    if not invalid_parent.is_dir():
        _die(f"ERR:missing invalid parent closeout dir: {invalid_parent}")

    admissibility_bundle = Path(config["admissibility_review_bundle"])
    if not admissibility_bundle.is_dir():
        _die(f"ERR:missing admissibility review bundle: {admissibility_bundle}")

    invalid_before_mtime = (invalid_parent / "CLOSEOUT.md").stat().st_mtime
    invalid_provenance = classify_invalid_parent_manifest(invalid_parent)
    if invalid_provenance["parent_closeout_manifest_verify_rc"] != int(
        config["expected_invalid_parent_manifest_rc"]
    ):
        _die(
            "ERR:invalid parent manifest RC mismatch: "
            f"expected {config['expected_invalid_parent_manifest_rc']} "
            f"got {invalid_provenance['parent_closeout_manifest_verify_rc']}"
        )
    if invalid_provenance["failure_class"] != config["expected_failure_class"]:
        _die(
            "ERR:unexpected failure class: "
            f"expected {config['expected_failure_class']} "
            f"got {invalid_provenance['failure_class']}"
        )

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    superseding_dir = materialize_superseding_parent_closeout(
        invalid_parent,
        output_dir,
        invalid_provenance,
    )
    superseding_manifest_rc = 0
    ok, superseding_msg = verify_manifest_sha256(superseding_dir)
    if not ok:
        _die(f"ERR:superseding parent closeout manifest verify failed: {superseding_msg}")

    shutil.copy2(
        superseding_dir / "MANIFEST.sha256",
        output_dir / "SUPERSEDING_PARENT_CLOSEOUT_MANIFEST.sha256",
    )

    if (invalid_parent / "CLOSEOUT.md").stat().st_mtime != invalid_before_mtime:
        _die("ERR:historical parent bundle was mutated")

    missing_sentinels, total_jsonl_rows = _count_missing_source_sentinels(output_dir)
    if missing_sentinels > 0:
        _die(
            "ERR:corrective bundle introduces MISSING_SOURCE_EVIDENCE sentinel ambiguity: "
            f"{missing_sentinels}/{total_jsonl_rows}"
        )

    git_snapshot = _git_snapshot()
    safety_boundaries = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    safety_boundaries.update(
        {
            "historical_bundle_mutation_allowed": False,
            "historical_bundle_mutated": False,
            "is_economic_viability_evidence_v1": False,
            "is_economic_evaluation": False,
            "grants_runtime_authority": False,
            "mutates_historical_negative_evidence": False,
            "missing_source_evidence_sentinel_rows": 0,
        }
    )

    fix_result = {
        "verdict": VERDICT_TARGET,
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": GO_TOKEN,
        "go_token_consumption": "CONSUMED",
        "parent_pr": config["parent_pr"],
        "parent_pre_merge_origin_main": config["parent_pre_merge_origin_main"],
        "parent_pr_head": config["parent_pr_head"],
        "parent_post_merge_head": config["parent_post_merge_head"],
        "invalid_parent_closeout_dir": str(invalid_parent),
        "invalid_parent_manifest_verify_rc": invalid_provenance[
            "parent_closeout_manifest_verify_rc"
        ],
        "failure_class": invalid_provenance["failure_class"],
        "admissibility_review_pr": config["admissibility_review_pr"],
        "admissibility_review_verdict": config["admissibility_review_verdict"],
        "admissibility_review_bundle": str(admissibility_bundle),
        "superseding_parent_closeout_dir": str(superseding_dir),
        "superseding_parent_manifest_verify_rc": superseding_manifest_rc,
        "historical_bundle_preserved": True,
        "historical_bundle_mutated": False,
        "is_economic_viability_evidence_v1": False,
        "is_economic_evaluation": False,
        "grants_runtime_authority": False,
        "economic_evaluation_executed": False,
        "economic_viability_evidence_emitted": False,
        "runtime_authority_granted": False,
        "next_step": config["next_step"],
        "durable_evidence_path": str(output_dir),
        "git_snapshot": git_snapshot,
    }

    (output_dir / "PRECONDITION_FIX_RESULT.json").write_text(
        json.dumps(fix_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "INVALID_PARENT_MANIFEST_PROVENANCE.json").write_text(
        json.dumps(invalid_provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SAFETY_BOUNDARIES.json").write_text(
        json.dumps(safety_boundaries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "execution_config_v0.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_findings_md(output_dir, invalid_provenance, superseding_dir, config)

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    verify_log_lines = [
        f"MANIFEST_VERIFY_RC={manifest_rc}",
        f"MANIFEST_VERIFY_MSG={manifest_msg or 'ok'}",
        f"SUPERSEDING_PARENT_MANIFEST_VERIFY_RC={superseding_manifest_rc}",
        f"SUPERSEDING_PARENT_MANIFEST_VERIFY_MSG={superseding_msg or 'ok'}",
        f"INVALID_PARENT_MANIFEST_VERIFY_RC={invalid_provenance['parent_closeout_manifest_verify_rc']}",
        f"FAILURE_CLASS={invalid_provenance['failure_class']}",
    ]
    (output_dir / "MANIFEST_VERIFY.log").write_text(
        "\n".join(verify_log_lines) + "\n", encoding="utf-8"
    )

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:corrective bundle manifest verify failed: {output_dir} ({manifest_msg})")

    fix_result["manifest_verify_rc"] = manifest_rc
    (output_dir / "PRECONDITION_FIX_RESULT.json").write_text(
        json.dumps(fix_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:corrective bundle manifest verify failed after result update: {manifest_msg}")

    fix_result["manifest_verify_rc"] = manifest_rc
    return fix_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize parent closeout manifest precondition gap fix v0"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=args.config,
        archive_root=args.durable_evidence_root,
    )
    print(f"VERDICT={result['verdict']}")
    print(f"PARENT_CLOSEOUT_MANIFEST_VERIFY_RC={result['invalid_parent_manifest_verify_rc']}")
    print(f"FAILURE_CLASS={result['failure_class']}")
    print(
        f"SUPERSEDING_PARENT_MANIFEST_VERIFY_RC={result['superseding_parent_manifest_verify_rc']}"
    )
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
