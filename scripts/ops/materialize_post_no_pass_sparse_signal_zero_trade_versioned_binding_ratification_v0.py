#!/usr/bin/env python3
"""Materialize post-no-pass sparse-signal / zero-trade versioned binding ratification v0.

Offline-first: validates versioned research bindings and emits durable evidence bundle.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    CONFIRM_GO,
    NEXT_EXECUTION_GO,
    ValidationVerdict,
    materialize_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
    serialize_completion_canonical_v0,
    validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    class_d_path = _REPO_ROOT / (
        "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
    )
    class_d_completion = json.loads(class_d_path.read_text(encoding="utf-8"))

    completion = materialize_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
        repo_root=_REPO_ROOT,
        class_d_completion=class_d_completion,
    )
    validation = validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
        completion,
        class_d_completion=class_d_completion,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_completion_canonical_v0(completion), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"post_no_pass_sparse_signal_zero_trade_versioned_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    completion_path = evidence_dir / "BINDING_COMPLETION.json"
    completion_path.write_text(serialize_completion_canonical_v0(completion), encoding="utf-8")

    matrix_path = evidence_dir / "CANDIDATE_BINDING_MATRIX.json"
    matrix_payload = {
        "binding_class": completion["binding_class"],
        "candidates": [
            {
                "strategy_id": item["strategy_id"],
                "strategy_version": item["strategy_version"],
                "binding_semantic_digest": item["binding_semantic_digest"],
                "terminal_class_d_v1_verdict": item["terminal_class_d_v1_verdict"],
                "substantially_differs_from_class_d_v1": item[
                    "substantially_differs_from_class_d_v1"
                ],
            }
            for item in completion["candidates"]
        ],
        "completion_digest": completion["completion_digest"],
        "failed_class_d_strategy_version": "v1",
        "go_token_consumed": CONFIRM_GO,
    }
    matrix_path.write_text(
        json.dumps(matrix_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary_md = evidence_dir / "binding_ratification_summary.md"
    summary_md.write_text(
        "\n".join(
            [
                "# Post No-Pass Sparse Signal Zero Trade Versioned Binding Ratification v0",
                "",
                f"- evidence_class_id: `{completion['evidence_class_id']}`",
                f"- status: `{completion['status']}`",
                f"- binding_class: `{completion['binding_class']}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- next_execution_go: `{NEXT_EXECUTION_GO}`",
                f"- completion_digest: `{completion['completion_digest']}`",
                "",
                "## Candidate matrix",
                "",
                "| strategy_id | strategy_version | terminal_class_d_v1_verdict |",
                "|---|---|---|",
                "| trend_following | v2 | ROBUSTNESS_FAILED |",
                "| bollinger_bands | v2 | ROBUSTNESS_FAILED |",
                "| momentum_1h | v2 | ROBUSTNESS_FAILED |",
                "",
                "## Authority boundary",
                "",
                "- economic_evaluation_authorized=false",
                "- backtest_run_executed=false",
                "- walk_forward_run_executed=false",
                "- monte_carlo_run_executed=false",
                "- stress_run_executed=false",
                "- runtime_effect=NONE",
                "- trading_effect=NONE",
                "- authority_effect=NONE",
                "",
            ]
        ),
        encoding="utf-8",
    )

    go_token_path = evidence_dir / "go_token_consumption.json"
    go_token_path.write_text(
        json.dumps(
            {
                "consumed_at_utc": _utc_now_z(),
                "go_token": CONFIRM_GO,
                "next_required_go": NEXT_EXECUTION_GO,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    if rc != 0:
        _die(f"ERR: manifest_verify_failed:{verify_msg}")

    return {
        "completion": completion,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": rc,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=DEFAULT_DURABLE_ARCHIVE_ROOT,
    )
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()

    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        write_repo_config=args.write_repo_config,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
