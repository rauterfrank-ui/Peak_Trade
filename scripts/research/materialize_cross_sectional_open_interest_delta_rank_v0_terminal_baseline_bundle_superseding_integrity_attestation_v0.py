#!/usr/bin/env python3
"""Materialize cross_sectional_open_interest_delta_rank v0 terminal baseline superseding integrity attestation."""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_superseding_integrity_attestation_v0 import (  # noqa: E402
    ATTESTATION_ID,
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    CONFIRM_GO,
    build_final_report,
    materialize_attestation_config,
    validate_attestation_bundle,
    validate_attestation_preconditions,
    validate_target_bundle_unchanged,
    write_attestation_bundle,
)

OUTPUT_PREFIX = (
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _worktree_clean(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == ""


def _collect_changed_files(repo_root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    names = sorted(
        {
            line.strip()
            for line in (result.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    return tuple(names)


def _materialize_payload(*, evidence_dir: Path | None = None):
    preconditions = validate_attestation_preconditions()
    payload = materialize_attestation_config(
        preconditions,
        attestation_evidence_dir=evidence_dir,
    )
    return preconditions, payload


def _write_config(repo_root: Path, payload) -> Path:
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_body = {
        "artifact_kind": ATTESTATION_ID,
        "artifact_version": "v0",
        "go_token": CONFIRM_GO,
        "governance_ref": GOVERNANCE_REL_PATH,
        **payload["attestation"],
        "external_superseding_integrity_attestation_contract": payload[
            "external_superseding_integrity_attestation_contract"
        ],
        "downstream_admissibility_assessment": payload["downstream_assessment"],
    }
    config_path.write_text(
        json.dumps(config_body, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return config_path


def _deterministic_materialization_check(repo_root: Path) -> tuple[bool, bool]:
    with (
        tempfile.TemporaryDirectory(prefix="attestation_mat_a_") as tmp_a,
        tempfile.TemporaryDirectory(prefix="attestation_mat_b_") as tmp_b,
    ):
        dir_a = Path(tmp_a)
        dir_b = Path(tmp_b)
        pre_a, payload_a = _materialize_payload()
        pre_b, payload_b = _materialize_payload()
        deterministic = payload_a["attestation"] == payload_b["attestation"]
        write_attestation_bundle(
            dir_a,
            repo_root=repo_root,
            payload=payload_a,
            preconditions=pre_a,
            changed_files=(),
            repo_mutation=False,
            pr_number="NONE",
            worktree_clean_before=True,
            worktree_clean_after=True,
            deterministic_materialization=deterministic,
            second_materialization_diff_empty=False,
        )
        write_attestation_bundle(
            dir_b,
            repo_root=repo_root,
            payload=payload_b,
            preconditions=pre_b,
            changed_files=(),
            repo_mutation=False,
            pr_number="NONE",
            worktree_clean_before=True,
            worktree_clean_after=True,
            deterministic_materialization=deterministic,
            second_materialization_diff_empty=False,
        )
        compare_names = [
            "integrity_attestation.json",
            "target_integrity_defect.json",
            "semantic_provenance_matrix.json",
            "supersession_contract.json",
            "downstream_admissibility_assessment.json",
            "historical_preservation_assertions.json",
            "test_assertion_matrix.json",
        ]
        diff_empty = all(
            (dir_a / name).read_bytes() == (dir_b / name).read_bytes() for name in compare_names
        )
        return deterministic, diff_empty


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--go-token", default=CONFIRM_GO)
    parser.add_argument("--archive-root", type=Path, default=DURABLE_ARCHIVE_ROOT)
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--skip-determinism-check", action="store_true")
    args = parser.parse_args()
    if args.go_token != CONFIRM_GO:
        _die(f"unexpected_go_token:{args.go_token}")

    subprocess.run(["git", "fetch", "origin", "--prune"], cwd=_REPO_ROOT, check=True)
    worktree_clean_before = _worktree_clean(_REPO_ROOT)

    preconditions = validate_attestation_preconditions()
    deterministic = True
    second_diff_empty = True
    if not args.skip_determinism_check:
        deterministic, second_diff_empty = _deterministic_materialization_check(_REPO_ROOT)
        if not deterministic or not second_diff_empty:
            _die("deterministic_materialization_failed")

    if args.write_config:
        _, payload = _materialize_payload()
        config_path = _write_config(_REPO_ROOT, payload)
        print(f"CONFIG_WRITTEN={config_path}")

    evidence_dir: Path | None = None
    manifest_rc = -1
    if args.write_evidence:
        evidence_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
        if evidence_dir.exists():
            _die(f"evidence_dir_exists:{evidence_dir}")
        _, payload = _materialize_payload(evidence_dir=evidence_dir)
        changed_files = _collect_changed_files(_REPO_ROOT)
        repo_mutation = bool(changed_files)
        manifest_rc = write_attestation_bundle(
            evidence_dir,
            repo_root=_REPO_ROOT,
            payload=payload,
            preconditions=preconditions,
            changed_files=changed_files,
            repo_mutation=repo_mutation,
            pr_number="PENDING",
            worktree_clean_before=worktree_clean_before,
            worktree_clean_after=_worktree_clean(_REPO_ROOT),
            deterministic_materialization=deterministic,
            second_materialization_diff_empty=second_diff_empty,
        )
        validate_target_bundle_unchanged(preconditions.target_snapshot)
        print(f"EVIDENCE_DIR={evidence_dir}")
        print(f"MANIFEST_VERIFY_RC={manifest_rc}")
        print(
            build_final_report(
                repo_root=_REPO_ROOT,
                attestation_evidence_dir=evidence_dir,
                payload=payload,
                manifest_verify_rc=manifest_rc,
                deterministic_materialization=deterministic,
                second_materialization_diff_empty=second_diff_empty,
                repo_mutation=repo_mutation,
                pr_number="PENDING",
                worktree_clean_before=worktree_clean_before,
                worktree_clean_after=_worktree_clean(_REPO_ROOT),
            ).strip()
        )

    if not args.write_config and not args.write_evidence:
        validate_attestation_preconditions()
        print("PRECONDITIONS_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
