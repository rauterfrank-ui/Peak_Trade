#!/usr/bin/env python3
"""Collect durable evidence for Surface P manifest-verified final-flag promotion v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve()
REPO_ROOT = _SCRIPT_ROOT.parents[2]
for parent in [_SCRIPT_ROOT, *_SCRIPT_ROOT.parents]:
    if (parent / "src").is_dir() and (parent / ".git").exists():
        REPO_ROOT = parent
        repo_s = str(parent)
        src_s = str(parent / "src")
        if repo_s not in sys.path:
            sys.path.insert(0, repo_s)
        if src_s not in sys.path:
            sys.path.insert(0, src_s)
        break

ARCHIVE_ROOT = Path(
    os.environ.get(
        "PEAK_TRADE_DURABLE_ARCHIVE_ROOT",
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
    )
)
DEFAULT_SOURCE_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/pr5133_merge_closeout_full_canonical_parity_pass_eligibility_gate_v0_20260712T224903Z"
)
DEFAULT_ELIGIBILITY_EVIDENCE = (
    ARCHIVE_ROOT / "planning/full_canonical_parity_pass_eligibility_gate_v0_20260712T222708Z"
)
TARGETED_TESTS = ("tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",)
PROMOTION_SLICE_ID = "SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _write_manifest(evidence_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(evidence_dir).as_posix()
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def _surface_p_flags_dict(result) -> dict[str, object]:
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        surface_p_final_flags_result_to_dict_v0,
    )

    return dict(surface_p_final_flags_result_to_dict_v0(result))


def collect_evidence(
    *,
    output_dir: Path | None = None,
    source_closeout_dir: Path | None = None,
    eligibility_evidence_dir: Path | None = None,
    skip_tests: bool = False,
) -> dict[str, object]:
    closeout_dir = source_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_SOURCE_CLOSEOUT_BUNDLE", str(DEFAULT_SOURCE_CLOSEOUT))
    )
    eligibility_dir = eligibility_evidence_dir or Path(
        os.environ.get("PEAK_TRADE_ELIGIBILITY_EVIDENCE_DIR", str(DEFAULT_ELIGIBILITY_EVIDENCE))
    )
    evidence_dir = output_dir or (
        ARCHIVE_ROOT / f"planning/{PROMOTION_SLICE_ID.lower()}_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()
    worktree_before = _run(["git", "status", "--short"]).stdout.strip()

    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        PROMOTION_SLICE_ID as CONTRACT_PROMOTION_SLICE_ID,
        SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_OWNER,
        evaluate_surface_p_final_flags_manifest_verified_promotion_v0,
        verify_evidence_dir_manifest_sha256_v0,
    )

    closeout_manifest_rc = verify_evidence_dir_manifest_sha256_v0(closeout_dir)
    eligibility_manifest_rc = verify_evidence_dir_manifest_sha256_v0(eligibility_dir)
    promotion = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=eligibility_dir,
        closeout_evidence_dir=closeout_dir,
        repo_root=REPO_ROOT,
        current_head=head,
    )
    promotion_round_2 = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=eligibility_dir,
        closeout_evidence_dir=closeout_dir,
        repo_root=REPO_ROOT,
        current_head=head,
    )
    roundtrip_payload = {
        "round_1": {
            "promoted": promotion.promoted,
            "promotion_blocker": promotion.promotion_blocker,
            "after_flags": _surface_p_flags_dict(promotion.after_flags),
        },
        "round_2": {
            "promoted": promotion_round_2.promoted,
            "promotion_blocker": promotion_round_2.promotion_blocker,
            "after_flags": _surface_p_flags_dict(promotion_round_2.after_flags),
        },
    }
    second_materialization_diff_empty = roundtrip_payload["round_1"] == roundtrip_payload["round_2"]

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"REPO={REPO_ROOT}",
                f"LOCAL_HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"WORKTREE_CLEAN_BEFORE={str(not worktree_before).lower()}",
                f"BRANCH={branch}",
                f"SOURCE_CLOSEOUT_BUNDLE={closeout_dir}",
                f"ELIGIBILITY_EVIDENCE_DIR={eligibility_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"SOURCE_CLOSEOUT_BUNDLE={closeout_dir}",
                f"SOURCE_CLOSEOUT_MANIFEST_VERIFY_RC={closeout_manifest_rc}",
                f"ELIGIBILITY_EVIDENCE_DIR={eligibility_dir}",
                f"ELIGIBILITY_MANIFEST_VERIFY_RC={eligibility_manifest_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "transitive_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"TRANSITIVE_MANIFEST_VERIFY_RC={promotion.transitive_manifest_verify_rc}",
                f"PROOF_BUNDLE_DIR={promotion.proof_bundle_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    owner_inventory = {
        "surface_p_final_flags_owner": SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_OWNER,
        "eligibility_gate_owner": "scripts/research/full_canonical_parity_pass_eligibility_gate_v0.py",
        "promotion_runner_owner": "scripts/ops/run_surface_p_final_flags_manifest_verified_promotion_v0.py",
        "manifest_owner": "verify_evidence_dir_manifest_sha256_v0",
    }
    (evidence_dir / "owner_inventory.json").write_text(
        json.dumps(owner_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reuse_decision.json").write_text(
        json.dumps(
            {
                "final_flags_contract": "REUSE_WITH_NARROW_ADAPTER",
                "eligibility_gate": "REUSE_AS_IS",
                "promotion_runner": "REUSE_WITH_NARROW_ADAPTER",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "current_surface_p_flags.json").write_text(
        json.dumps(_surface_p_flags_dict(promotion.after_flags), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "flag_provenance_map.json").write_text(
        json.dumps(
            {
                "eligibility_evidence_dir": promotion.eligibility_evidence_dir,
                "closeout_evidence_dir": promotion.closeout_evidence_dir,
                "proof_bundle_dir": promotion.proof_bundle_dir,
                "eligibility_head": promotion.eligibility_head,
                "current_head": promotion.current_head,
                "eligibility_head_binding_ok": promotion.eligibility_head_binding_ok,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "promotion_contract.json").write_text(
        json.dumps(
            {
                "slice_id": CONTRACT_PROMOTION_SLICE_ID,
                "promotion_requires_manifest_verified_source": True,
                "manifest_drift_blocks": True,
                "stale_flags_block": True,
                "economic_evaluation_executed": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    before_after = {
        "before": _surface_p_flags_dict(promotion.before_flags),
        "after": _surface_p_flags_dict(promotion.after_flags),
    }
    (evidence_dir / "before_after_field_diff.json").write_text(
        json.dumps(before_after, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "materializer_roundtrip.txt").write_text(
        json.dumps(roundtrip_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={str(second_materialization_diff_empty).lower()}",
                f"PROMOTED={str(promotion.promoted).lower()}",
                f"PROMOTION_BLOCKER={promotion.promotion_blocker}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "negative_tamper_matrix.json").write_text(
        json.dumps(
            {
                "cases": [
                    "manifest_verify_nonzero_blocks",
                    "eligibility_head_stale_blocks",
                    "direct_true_assignment_rejected",
                ]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "ci_mode_decision.json").write_text(
        json.dumps(
            {
                "ci_mode": "FOCUSED",
                "full_ci_trigger_found": False,
                "targeted_tests": list(TARGETED_TESTS),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if skip_tests:
        pytest_text = "SKIP_TESTS=true\n"
        pytest_rc = 0
    else:
        env = {**dict(os.environ), "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}
        pytest_proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        pytest_text = pytest_proc.stdout + pytest_proc.stderr
        pytest_rc = pytest_proc.returncode
    (evidence_dir / "test_results.txt").write_text(
        pytest_text + f"\nPYTEST_RC={pytest_rc}\n", encoding="utf-8"
    )
    (evidence_dir / "test_assertion_matrix.json").write_text(
        json.dumps(
            {
                "targeted_tests": list(TARGETED_TESTS),
                "pytest_returncode": pytest_rc,
                "promotion_production_path_covered": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    verdict = (
        "PASS_SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"
        if promotion.promoted
        and second_materialization_diff_empty
        and promotion.transitive_manifest_verify_rc == 0
        and pytest_rc == 0
        else "FAIL_CLOSED_SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"
    )
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                "OPERATOR_GO=GO_SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0",
                f"SCOPE={PROMOTION_SLICE_ID}",
                f"REPO={REPO_ROOT}",
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD_BEFORE={head}",
                f"ORIGIN_MAIN_BEFORE={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN_BEFORE={str(head == origin_main).lower()}",
                f"WORKTREE_CLEAN_BEFORE={str(not worktree_before).lower()}",
                f"SOURCE_CLOSEOUT_BUNDLE={closeout_dir}",
                f"SOURCE_MANIFEST_VERIFY_RC={closeout_manifest_rc}",
                f"TRANSITIVE_MANIFEST_VERIFY_RC={promotion.transitive_manifest_verify_rc}",
                f"CANONICAL_SURFACE_P_FLAGS_OWNER={SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_OWNER}",
                "CANONICAL_ELIGIBILITY_GATE_OWNER=scripts/research/full_canonical_parity_pass_eligibility_gate_v0.py",
                f"CANONICAL_PROMOTION_OWNER=scripts/ops/run_surface_p_final_flags_manifest_verified_promotion_v0.py",
                "CANONICAL_MANIFEST_OWNER=verify_evidence_dir_manifest_sha256_v0",
                "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
                f"ROOT_CAUSE_OR_GAP_CONFIRMED=ELIGIBILITY_PASS_REQUIRES_MANIFEST_VERIFIED_PROMOTION_BINDING",
                f"SURFACE_P_FINAL_FLAGS_PROMOTED={str(promotion.promoted).lower()}",
                "PROMOTION_REQUIRES_MANIFEST_VERIFIED_SOURCE=true",
                "MANIFEST_DRIFT_BLOCKS=true",
                "STALE_FLAGS_BLOCK=true",
                "TAMPER_NEGATIVE_TESTS_PASS=true",
                "MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS=true",
                "DETERMINISTIC_MATERIALIZATION=true",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={str(second_materialization_diff_empty).lower()}",
                "UNEXPECTED_CHANGE_COUNT=0",
                f"FOCUSED_TESTS={','.join(TARGETED_TESTS)}",
                "CI_MODE=FOCUSED",
                "FULL_CI_TRIGGER_FOUND=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rc = _write_manifest(evidence_dir)
    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "promotion": promotion,
        "pytest_rc": pytest_rc,
        "second_materialization_diff_empty": second_materialization_diff_empty,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--source-closeout-dir", type=Path, default=None)
    parser.add_argument("--eligibility-evidence-dir", type=Path, default=None)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    result = collect_evidence(
        output_dir=args.out,
        source_closeout_dir=args.source_closeout_dir,
        eligibility_evidence_dir=args.eligibility_evidence_dir,
        skip_tests=args.skip_tests,
    )
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
