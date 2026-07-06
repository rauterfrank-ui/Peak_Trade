#!/usr/bin/env python3
"""Materialize post-PR4895 versioned fleet binding ratification v0.

Offline-first: validates versioned v4 fleet bindings and emits durable evidence bundle.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0
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

CONFIRM_GO = "GO_POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PARENT_SCOPE_BUNDLE_SUFFIX = "post_pr4894_next_scope_definition_v0_20260706T020323Z"
DECOMPOSITION_BUNDLE_SUFFIX = (
    "post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0_20260706T015337Z"
)

from src.research.post_pr4895_versioned_fleet_binding_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    NEXT_CANONICAL_STEP,
    NEXT_EXECUTION_GO,
    PROCESS_CLASSIFICATION,
    REQUIRED_BINDING_FIELDS,
    SCOPE_CLASSIFICATION,
    ValidationVerdict,
    materialize_post_pr4895_versioned_fleet_binding_ratification_v0,
    serialize_completion_canonical_v0,
    validate_post_pr4895_versioned_fleet_binding_ratification_v0,
)
from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH as V3_CONFIG_REL,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _verify_source_manifest(source_dir: Path, log_path: Path) -> int:
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, msg = verify_manifest_sha256(source_dir)
    rc = 0 if ok else 1
    log_path.write_text(
        f"SOURCE={source_dir}\nMANIFEST_VERIFY_RC={rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\n",
        encoding="utf-8",
    )
    return rc


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _write_binding_gap_matrix(output_dir: Path, completion: dict[str, Any]) -> None:
    lines = [
        "# Binding Gap Matrix",
        "",
        f"- all_required_bindings_complete: `{completion.get('all_required_bindings_complete')}`",
        f"- blocked_missing_bindings: `{completion.get('blocked_missing_bindings')}`",
        "",
        "| strategy_id | strategy_version | binding_status | all_14_bindings | evaluation_ready |",
        "|---|---|---|---|---|",
    ]
    for item in completion["candidates"]:
        missing = [f for f in REQUIRED_BINDING_FIELDS if f not in item or item[f] in (None, "", {})]
        all_complete = len(missing) == 0
        eval_ready = all_complete and item.get("binding_status") == (
            "READY_FOR_SEPARATE_OFFLINE_EVALUATION_RATIFICATION"
        )
        lines.append(
            f"| `{item['strategy_id']}` | `{item['strategy_version']}` | "
            f"`{item['binding_status']}` | `{all_complete}` | `{eval_ready}` |"
        )
    if completion.get("blocked_missing_bindings"):
        lines.extend(
            [
                "",
                "## BLOCKED_MISSING_BINDING entries",
                "",
                *[f"- `{entry}`" for entry in completion["blocked_missing_bindings"]],
            ]
        )
    else:
        lines.extend(["", "All three fleet candidates have complete v4 bindings. No gaps."])
    (output_dir / "BINDING_GAP_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_authority_boundary(output_dir: Path) -> None:
    (output_dir / "AUTHORITY_BOUNDARY.md").write_text(
        "\n".join(
            [
                "# Authority Boundary",
                "",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "BACKTEST_EXECUTED=false",
                "RUNTIME_AUTHORITY=NONE",
                "FAILED_BINDINGS_RETRY_ALLOWED=false",
                "NEW_CANDIDATE_RATIFIED=false",
                "PROMOTION_AUTHORITY=false",
                "SHADOW_AUTHORIZED=false",
                "PAPER_AUTHORIZED=false",
                "TESTNET_AUTHORIZED=false",
                "LIVE_AUTHORIZED=false",
                "BOUNDARIES=NO_RUNTIME_NO_BACKTEST_NO_EVALUATION_NO_SHADOW_NO_PAPER_NO_TESTNET_NO_ORDERS_NO_LIVE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    v3_path = _REPO_ROOT / V3_CONFIG_REL
    v3_completion = json.loads(v3_path.read_text(encoding="utf-8"))

    completion = materialize_post_pr4895_versioned_fleet_binding_ratification_v0(
        repo_root=_REPO_ROOT,
        v3_completion=v3_completion,
    )
    validation = validate_post_pr4895_versioned_fleet_binding_ratification_v0(
        completion,
        v3_completion=v3_completion,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_completion_canonical_v0(completion), encoding="utf-8")

    scope_ref = durable_evidence_root / "implementation" / PARENT_SCOPE_BUNDLE_SUFFIX
    decomp_ref = durable_evidence_root / "implementation" / DECOMPOSITION_BUNDLE_SUFFIX
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"post_pr4895_versioned_fleet_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)

    scope_manifest_rc = _verify_source_manifest(
        scope_ref, evidence_dir / "parent_scope_definition_manifest_verify.log"
    )
    decomp_manifest_rc = _verify_source_manifest(
        decomp_ref, evidence_dir / "parent_decomposition_manifest_verify.log"
    )
    if scope_manifest_rc != 0:
        _die("ERR:parent scope definition manifest verify failed")
    if decomp_manifest_rc != 0:
        _die("ERR:parent decomposition manifest verify failed")

    (evidence_dir / "CANDIDATE_BINDINGS.json").write_text(
        json.dumps(completion["candidates"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "binding_ratification_v0.json").write_text(
        serialize_completion_canonical_v0(completion), encoding="utf-8"
    )
    (evidence_dir / "git_snapshot.json").write_text(
        json.dumps(_git_snapshot(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    (evidence_dir / "FLEET_BINDING_RATIFICATION_REPORT.md").write_text(
        "\n".join(
            [
                "# Fleet Binding Ratification Report",
                "",
                f"- evidence_class_id: `POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
                f"- status: `{completion['status']}`",
                f"- strategy_version: `{completion['strategy_version']}`",
                f"- all_required_bindings_complete: `{completion['all_required_bindings_complete']}`",
                f"- fleet_bindings_ratified: `{completion['fleet_bindings_ratified']}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- completion_digest: `{completion['completion_digest']}`",
                "",
                "## Next canonical step",
                "",
                f"- `{NEXT_CANONICAL_STEP}`",
                f"- execution_go (later, separate): `{NEXT_EXECUTION_GO}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_binding_gap_matrix(evidence_dir, completion)
    _write_authority_boundary(evidence_dir)

    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    write_manifest_sha256(evidence_dir)
    manifest_rc = 0 if verify_manifest_sha256(evidence_dir)[0] else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {evidence_dir}")

    return {
        "verdict": "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED",
        "all_required_bindings_complete": completion["all_required_bindings_complete"],
        "blocked_missing_bindings": completion["blocked_missing_bindings"],
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "completion_digest": completion["completion_digest"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize post-PR4895 versioned fleet binding ratification v0"
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ARCHIVE_ROOT)
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()

    result = run_materialization(
        confirm=args.confirm_go_token,
        durable_evidence_root=args.durable_evidence_root,
        write_repo_config=args.write_repo_config,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    for key, value in result.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
