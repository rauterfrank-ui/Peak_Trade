#!/usr/bin/env python3
"""Dry-run entrypoint for cross-sectional relative-strength v0 offline economic evaluation.

Validates bindings, manifests, dataset materialization, and stage wiring.
Stops before economic evaluation execution. No runtime or order effect.
Operator GO (infrastructure): GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_COMPLETION_V1
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

from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    materialize_panel_staging_source_manifests_v1,
    source_manifest_result_to_dict,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    materialization_result_to_dict,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    run_full_evaluation_entrypoint_dry_run_v1,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def run_dry_run(
    *,
    confirm: str,
    staging_root: Path,
    durable_evidence_root: Path | None = None,
    write_evidence: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    ratification = materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    manifest_result = materialize_panel_staging_source_manifests_v1(staging_root)
    panel_series, _ = load_panel_series_from_staging(staging_root)
    entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        go_token=confirm,
    )
    materialization = materialize_bound_panel_dataset_v0(
        staging_root,
        period_binding=ratification["period_binding"],
    )

    payload: dict[str, Any] = {
        "verdict": entrypoint.status.value,
        "confirm_go_token": confirm,
        "origin_main_sha": _resolve_origin_main(_REPO_ROOT),
        "staging_root": str(staging_root),
        "source_manifests": source_manifest_result_to_dict(manifest_result),
        "dataset_materialization": materialization_result_to_dict(materialization),
        "entrypoint": entrypoint_result_to_dict(entrypoint),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }

    if write_evidence and durable_evidence_root is not None:
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bundle_dir = (
            durable_evidence_root
            / f"bounded_cross_sectional_relative_strength_v0_offline_economic_evaluation_infrastructure_completion_v1_{ts_slug}"
        )
        bundle_dir.mkdir(parents=True, exist_ok=False)
        (bundle_dir / "DRY_RUN_RESULT.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["durable_evidence_path"] = str(bundle_dir)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=None)
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    result = run_dry_run(
        confirm=args.confirm,
        staging_root=args.staging_root,
        durable_evidence_root=args.durable_evidence_root,
        write_evidence=args.write_evidence,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
