#!/usr/bin/env python3
"""Materialize momentum_1h v2 offline economic evaluation authorization ratification v0."""

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
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (  # noqa: E402
    CONFIRM_GO,
    CONFIG_REL_PATH,
    DISCOVERY_EVIDENCE_DIR,
    GO_TOKEN,
    GOVERNANCE_REL_PATH,
    materialize_and_validate_authorization_ratification_v0,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    serialize_authorization_ratification_json_v0,
)
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    DECISION_PACKET_DIR,
    POST_PR4921_CLOSEOUT_DIR,
    TREND_FOLLOWING_V2_CLOSEOUT_DIR,
    materialize_versioned_research_binding_v0,
    serialize_versioned_binding_json_v0,
)

DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0"
FOCUSED_TEST = (
    "tests/research/"
    "test_momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0_contract.py"
)
PROGRESS_REGISTRY_TEST = (
    "tests/ops/"
    "test_momentum_1h_v2_offline_economic_evaluation_authorization_ratification_progress_registry_contract_v0.py"
)
BOUNDARY_TEST = "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py"
EXPECTED_ORIGIN_MAIN = "da34ecaf36d2d22c6e1638936c1172e9e98999d2"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "branch": _run(["branch", "--show-current"]),
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _verify_source_manifests() -> tuple[int, list[dict[str, object]]]:
    results: list[dict[str, object]] = []
    overall_rc = 0
    for label, bundle in (
        ("DISCOVERY_EVIDENCE", Path(DISCOVERY_EVIDENCE_DIR)),
        ("DECISION_PACKET", Path(DECISION_PACKET_DIR)),
        ("TREND_FOLLOWING_V2_CLOSEOUT", Path(TREND_FOLLOWING_V2_CLOSEOUT_DIR)),
        ("POST_PR4921_CLOSEOUT", Path(POST_PR4921_CLOSEOUT_DIR)),
    ):
        ok, msg = verify_manifest_sha256(bundle)
        rc = 0 if ok else 1
        results.append(
            {
                "label": label,
                "bundle": str(bundle),
                "manifest_verify_rc": rc,
                "message": msg,
            }
        )
        if rc != 0:
            overall_rc = rc
    return overall_rc, results


def _write_repo_configs(
    *,
    versioned_binding: dict[str, Any],
    authorization_ratification: dict[str, Any],
) -> None:
    binding_path = _REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(
        serialize_versioned_binding_json_v0(versioned_binding), encoding="utf-8"
    )

    auth_path = _REPO_ROOT / CONFIG_REL_PATH
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(
        serialize_authorization_ratification_json_v0(authorization_ratification),
        encoding="utf-8",
    )


def _run_focused_tests() -> int:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            FOCUSED_TEST,
            PROGRESS_REGISTRY_TEST,
            BOUNDARY_TEST,
            "-q",
            "--tb=short",
        ],
        cwd=_REPO_ROOT,
        check=False,
    )
    return proc.returncode


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool = True,
    run_tests: bool = True,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    git = _git_snapshot()
    if git["origin_main"] != EXPECTED_ORIGIN_MAIN:
        _die(f"ERR: preflight_origin_main_mismatch:origin_main={git['origin_main']}")
    if git["status_short"] != "(clean)":
        _die(f"ERR: worktree_not_clean:{git['status_short']}")

    source_manifest_rc, source_inventory = _verify_source_manifests()
    if source_manifest_rc != 0:
        _die(f"ERR: source_manifest_verify_failed:{source_manifest_rc}")

    result = materialize_and_validate_authorization_ratification_v0(
        go_token=CONFIRM_GO,
        repo_root=_REPO_ROOT,
    )
    if result.verdict.value != "COMPLETE":
        _die(f"ERR: authorization_ratification_invalid:{result.fail_reasons}")

    versioned_binding = materialize_versioned_research_binding_v0(repo_root=_REPO_ROOT)
    authorization_ratification = result.ratification

    if write_repo_config:
        _write_repo_configs(
            versioned_binding=versioned_binding,
            authorization_ratification=authorization_ratification,
        )

    test_rc = 0
    if run_tests:
        test_rc = _run_focused_tests()
        if test_rc != 0:
            _die(f"ERR: focused_tests_failed:{test_rc}")

    bundle_dir = durable_evidence_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    bundle_dir.mkdir(parents=True, exist_ok=False)

    (bundle_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"SCOPE={OUTPUT_PREFIX}",
                f"OPERATOR_GO={GO_TOKEN}",
                f"HEAD={git['head']}",
                f"ORIGIN_MAIN={git['origin_main']}",
                "HEAD_EQUALS_ORIGIN_MAIN=true",
                "WORKTREE_CLEAN=true",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                "RESEARCH_SCOPE=momentum_1h/v2",
                "OFFLINE_ONLY=true",
                "NO_ECONOMIC_EVALUATION=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "source_manifest_verification.txt").write_text(
        json.dumps(source_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "versioned_binding.json").write_text(
        serialize_versioned_binding_json_v0(versioned_binding), encoding="utf-8"
    )
    (bundle_dir / "authorization_ratification.json").write_text(
        serialize_authorization_ratification_json_v0(authorization_ratification),
        encoding="utf-8",
    )
    (bundle_dir / "authorization_contract.json").write_text(
        json.dumps(
            authorization_ratification["authorization_contract"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "digest_dependency_graph.json").write_text(
        json.dumps(
            authorization_ratification["digest_dependency_graph"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(bundle_dir)

    final_report = (
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=MOMENTUM_1H_V2_AUTHORIZATION_RATIFICATION_COMPLETE",
                f"SCOPE={OUTPUT_PREFIX}",
                f"OPERATOR_GO={GO_TOKEN}",
                f"BINDING_DIGEST={versioned_binding['binding_digest']}",
                f"DATASET_DIGEST={versioned_binding['dataset_digest']}",
                f"RATIFICATION_DIGEST={authorization_ratification['ratification_digest']}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                f"FOCUSED_TEST_RC={test_rc}",
                f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle_dir}",
                "NEXT_ADMISSIBLE_SCOPE=MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0",
                "NEXT_OPERATOR_GO=GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0",
            ]
        )
        + "\n"
    )
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    print(final_report)
    return {
        "bundle_dir": str(bundle_dir),
        "binding_digest": versioned_binding["binding_digest"],
        "dataset_digest": versioned_binding["dataset_digest"],
        "manifest_verify_rc": manifest_verify_rc,
        "source_manifest_verify_rc": source_manifest_rc,
        "test_rc": test_rc,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
    )
    parser.add_argument("--no-write-repo-config", action="store_true")
    parser.add_argument("--no-tests", action="store_true")
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        write_repo_config=not args.no_write_repo_config,
        run_tests=not args.no_tests,
    )


if __name__ == "__main__":
    main()
