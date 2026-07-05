#!/usr/bin/env python3
"""Materialize post-no-pass metric materialization path activation binding ratification v0.

Offline-first: validates versioned path-activation bindings and emits durable evidence bundle.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0
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

CONFIRM_GO = "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
NEXT_EXECUTION_GO = (
    "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SCOPE_DEFINITION_BUNDLE_SUFFIX = "post_no_pass_metric_materialization_diagnostics_derived_next_research_scope_definition_v0_20260705T232358Z"

from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    NEXT_CANONICAL_STEP,
    PRIMARY_CAUSE,
    PROCESS_CLASSIFICATION,
    REQUIRED_BINDING_FIELDS,
    SCOPE_CLASSIFICATION,
    ValidationVerdict,
    materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0,
    serialize_completion_canonical_v0,
    validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (  # noqa: E402
    CONFIG_REL_PATH as SPARSE_V2_CONFIG_REL,
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


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    sparse_v2_path = _REPO_ROOT / SPARSE_V2_CONFIG_REL
    sparse_v2_completion = json.loads(sparse_v2_path.read_text(encoding="utf-8"))

    completion = (
        materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
            repo_root=_REPO_ROOT,
            sparse_v2_completion=sparse_v2_completion,
        )
    )
    validation = (
        validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
            completion,
            sparse_v2_completion=sparse_v2_completion,
        )
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_completion_canonical_v0(completion), encoding="utf-8")

    scope_definition_ref = durable_evidence_root / "implementation" / SCOPE_DEFINITION_BUNDLE_SUFFIX
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"post_no_pass_metric_materialization_path_activation_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)

    if scope_definition_ref.is_dir():
        source_manifest_rc = _verify_source_manifest(
            scope_definition_ref,
            evidence_dir / "source_scope_definition_manifest_verify.log",
        )
        if source_manifest_rc != 0:
            _die("ERR:source scope definition manifest verify failed")
    else:
        source_manifest_rc = -1

    completion_path = evidence_dir / "BINDING_COMPLETION.json"
    completion_path.write_text(serialize_completion_canonical_v0(completion), encoding="utf-8")

    (evidence_dir / "PATH_ACTIVATION_BINDING_RATIFICATION_REPORT.md").write_text(
        "\n".join(
            [
                "# Path Activation Binding Ratification Report",
                "",
                f"- evidence_class_id: `{SCOPE_CLASSIFICATION}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- status: `{completion['status']}`",
                f"- primary_cause: `{PRIMARY_CAUSE}`",
                f"- binding_class: `{completion['binding_class']}`",
                f"- strategy_version: `{completion['strategy_version']}`",
                f"- path_activation_binding_ratified: `{completion['path_activation_binding_ratified']}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- completion_digest: `{completion['completion_digest']}`",
                "",
                "## Activation semantics",
                "",
                "- PATH_PRESENT_BUT_NOT_EXECUTED remains the diagnosed primary cause.",
                "- This ratification binds the existing metric materialization path for later evaluation only.",
                "- No evaluation executed in this scope.",
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

    matrix_lines = [
        "# Required Bindings Matrix",
        "",
        "| strategy_id | strategy_version | path_activation_status | metric_materialization_path_ref |",
        "|---|---|---|---|",
    ]
    for item in completion["candidates"]:
        matrix_lines.append(
            f"| `{item['strategy_id']}` | `{item['strategy_version']}` | "
            f"`{item['path_activation_status']}` | `{item['metric_materialization_path_ref']}` |"
        )
    matrix_lines.extend(
        [
            "",
            "## Required binding fields (all candidates)",
            "",
            *[f"- `{field}`" for field in REQUIRED_BINDING_FIELDS],
        ]
    )
    (evidence_dir / "REQUIRED_BINDINGS_MATRIX.md").write_text(
        "\n".join(matrix_lines) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "REGISTRY_UPDATE.md").write_text(
        "\n".join(
            [
                "# Registry Update",
                "",
                "- CURRENT_STATE: `POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_V0`",
                f"- NEXT_CANONICAL_STEP: `{NEXT_CANONICAL_STEP}`",
                "- CURRENT_ADMISSIBLE_NEXT_SCOPE: `POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN: `{NEXT_EXECUTION_GO}`",
                f"- PATH_ACTIVATION_BINDING_RATIFIED: `{completion['path_activation_binding_ratified']}`",
                f"- GO_TOKEN_CONSUMED: `{CONFIRM_GO}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "RESOLVER_UPDATE.md").write_text(
        "\n".join(
            [
                "# Resolver Update",
                "",
                f"- CURRENT_STATE: `POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_V0`",
                f"- NEXT_CANONICAL_STEP: `{NEXT_CANONICAL_STEP}`",
                "- CURRENT_ADMISSIBLE_NEXT_SCOPE: `POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN: `{NEXT_EXECUTION_GO}`",
                "- PATH_ACTIVATION_BINDING_RATIFIED=true",
                f"- GO_TOKEN_CONSUMED={CONFIRM_GO}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "SAFETY_BOUNDARY_CONFIRMATION.md").write_text(
        "\n".join(
            [
                "# Safety Boundary Confirmation",
                "",
                "- ECONOMIC_EVALUATION_AUTHORIZED=false",
                "- EVALUATION_EXECUTED=false",
                "- BACKTEST_EXECUTED=false",
                "- WALK_FORWARD_EXECUTED=false",
                "- MONTE_CARLO_EXECUTED=false",
                "- STRESS_EXECUTED=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- LIVE_AUTHORIZED=false",
                "- CORE_SYSTEM_MUTATION_ALLOWED=false",
                "- NO_PARAMETER_RESCUE=true",
                "- NO_THRESHOLD_LOWERING=true",
                "- NO_SAME_BINDING_RETRY=true",
                "- NO_RESULT_RESCUE=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "go_token_consumption.json").write_text(
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
        "source_scope_definition_manifest_verify_rc": source_manifest_rc,
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
