#!/usr/bin/env python3
"""CLI: Stage-2 Pure-Stack numeric policy shadow campaign runner v1.

No-order / offline / non-authorizing. Emits schema-compatible Evidence packs only.
Does not set productive numbers, flip INPUT_AUTHORITY_*, mutate dashboards/archives,
or touch order/testnet/live paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.campaign_runner_v1 import (
    empty_scaffold_manifest,
    run_shadow_campaign_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    RELATIVE_OUTPUT_ROOT,
    SOLE_TRADING_AUTHORITY,
    STAGE1_MANIFEST_REL,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.evidence_emitter_v1 import (
    ShadowCampaignEmitError,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ReproducibilityRecordV1,
    ShadowCampaignRequestV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    compute_config_digest,
    sha256_file,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_sha(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    if not head.is_file():
        raise ShadowCampaignEmitError("git_head_missing")
    content = head.read_text(encoding="utf-8").strip()
    if content.startswith("ref:"):
        ref = content.split(" ", 1)[1].strip()
        ref_path = repo_root / ".git" / ref
        if not ref_path.is_file():
            raise ShadowCampaignEmitError("git_ref_missing")
        return ref_path.read_text(encoding="utf-8").strip()
    return content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run isolated Stage-2 Pure-Stack numeric policy shadow campaign "
            "(evidence only; no productive numbers; no authority flips)."
        )
    )
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help=f"Must resolve under repo/{RELATIVE_OUTPUT_ROOT}/",
    )
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--instrument-id", required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--event-time-epoch-s", type=int, required=True)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (defaults to checkout containing this script)",
    )
    parser.add_argument(
        "--force-reject",
        action="append",
        default=[],
        help="Optional explicit rejection reason (fail-closed campaign)",
    )
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or _repo_root()).resolve()
    try:
        stage1_digest = sha256_file(repo_root / STAGE1_MANIFEST_REL)
        protocol_digest = sha256_file(repo_root / CALIBRATION_PROTOCOL_REL)
        git_sha = _git_sha(repo_root)
        config_digest = compute_config_digest(
            seed=args.seed,
            scenario_id=args.scenario_id,
            campaign_id=args.campaign_id,
        )
        request = ShadowCampaignRequestV1(
            campaign_id=args.campaign_id,
            origin_main_sha=args.origin_main_sha,
            repo_root=str(repo_root),
            output_root=str(args.output_root),
            reproducibility=ReproducibilityRecordV1(
                git_sha=git_sha,
                config_digest=config_digest,
                stage1_manifest_digest=stage1_digest,
                calibration_protocol_digest=protocol_digest,
                dataset_id=args.dataset_id,
                instrument_id=args.instrument_id,
                scenario_id=args.scenario_id,
                seed=int(args.seed),
                event_time_epoch_s=int(args.event_time_epoch_s),
                wall_time_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                sole_trading_authority=SOLE_TRADING_AUTHORITY,
            ),
            observation_bars=(),
            dataset_manifest=empty_scaffold_manifest("CLI hermetic declare; dataset not populated"),
            train_calibration_validation_partition_manifest=empty_scaffold_manifest(
                "CLI hermetic declare; partitions not populated"
            ),
            walk_forward_manifest=empty_scaffold_manifest(
                "CLI hermetic declare; walk-forward not populated"
            ),
            bootstrap_monte_carlo_manifest=empty_scaffold_manifest(
                "CLI hermetic declare; bootstrap/MC not populated"
            ),
            stress_pack_manifest=empty_scaffold_manifest(
                "CLI hermetic declare; stress packs not populated"
            ),
            force_reject_reasons=tuple(args.force_reject),
            allow_overwrite=False,
        )
        result = run_shadow_campaign_v1(request)
    except ShadowCampaignEmitError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "non_authorizing": True,
                    "productive_activation": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "campaign_id": result.campaign_id,
                "campaign_state": result.campaign_state.value,
                "pack_campaign_status": result.pack_campaign_status,
                "token_count": result.token_count,
                "productive_numeric_values_set": result.productive_numeric_values_set,
                "input_authority": result.input_authority,
                "runtime_implemented": result.runtime_implemented,
                "owner_ratified": result.owner_ratified,
                "productive_activation": result.productive_activation,
                "evidence_complete": result.evidence_complete,
                "sole_trading_authority": result.sole_trading_authority,
                "output_dir": result.output_dir,
                "pack_digest": result.pack_digest,
                "rejection_reasons": list(result.rejection_reasons),
                "non_authorizing": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not result.rejection_reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
