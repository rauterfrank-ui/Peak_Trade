#!/usr/bin/env python3
"""CLI: Stage-2 Shadow Campaign Input Authority Surface-B export v1.

No-order / offline / non-authorizing. Builds immutable observation packs,
structural COMPLETE manifests, and a ShadowCampaignRequestV1 binder payload.
Does not set productive numbers, flip INPUT_AUTHORITY_*, mutate O4/dashboards,
or touch order/testnet/live paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    STAGE1_MANIFEST_REL,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    sha256_file,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.export_api_v1 import (
    export_surface_b_shadow_campaign_input_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    InstrumentBindingV1,
    MarkPriceInputV1,
    VenueNativeCandleInputV1,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export Stage-2 Surface-B PT1M finalized-OHLCV observation pack and "
            "structural manifests bound to ShadowCampaignRequestV1 "
            "(no productive numbers; no authority flips)."
        )
    )
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--event-time-epoch-s", type=int, required=True)
    parser.add_argument("--binding-json", type=Path, required=True)
    parser.add_argument("--candles-json", type=Path, required=True)
    parser.add_argument("--marks-json", type=Path, required=True)
    parser.add_argument("--partition-boundaries-json", type=Path, required=True)
    parser.add_argument("--fold-ids-json", type=Path, required=True)
    parser.add_argument("--bootstrap-seeds-json", type=Path, required=True)
    parser.add_argument("--regime-coverage-json", type=Path, required=True)
    parser.add_argument("--export-json-out", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or _repo_root()).resolve()
    try:
        binding_raw = _load_json(args.binding_json)
        binding = InstrumentBindingV1(**binding_raw)
        candles = tuple(
            VenueNativeCandleInputV1(**row) for row in _load_json(args.candles_json)["candles"]
        )
        marks = tuple(MarkPriceInputV1(**row) for row in _load_json(args.marks_json)["marks"])
        boundaries = _load_json(args.partition_boundaries_json)
        fold_ids = list(_load_json(args.fold_ids_json)["fold_ids"])
        bootstrap_seeds = list(_load_json(args.bootstrap_seeds_json)["seeds"])
        regime_coverage = dict(_load_json(args.regime_coverage_json))
        stage1 = sha256_file(repo_root / STAGE1_MANIFEST_REL)
        protocol = sha256_file(repo_root / CALIBRATION_PROTOCOL_REL)
        result = export_surface_b_shadow_campaign_input_v1(
            repo_root=repo_root,
            campaign_id=args.campaign_id,
            origin_main_sha=args.origin_main_sha,
            output_root=args.output_root,
            dataset_id=args.dataset_id,
            scenario_id=args.scenario_id,
            seed=int(args.seed),
            event_time_epoch_s=int(args.event_time_epoch_s),
            binding=binding,
            candles=candles,
            marks=marks,
            segment_boundaries_event_time_epoch_s=boundaries,
            fold_ids=fold_ids,
            bootstrap_seeds=bootstrap_seeds,
            regime_coverage=regime_coverage,
            stage1_manifest_digest=stage1,
            calibration_protocol_digest=protocol,
        )
    except (InputAuthorityErrorV1, TypeError, KeyError, ValueError, OSError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "non_authorizing": True,
                    "productive_activation": False,
                    "input_authority": False,
                    "o4_unchanged": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    request = result.shadow_campaign_request
    payload = {
        "ok": True,
        "campaign_id": request.campaign_id,
        "authority_surface": "B",
        "repository_sha": result.repository_sha,
        "observation_pack_digest": result.observation_pack.observation_pack_digest,
        "reproducibility_observation_pack_digest": (
            request.reproducibility.observation_pack_digest
        ),
        "bar_count": len(request.observation_bars),
        "dataset_manifest_status": request.dataset_manifest.status,
        "partition_manifest_status": (
            request.train_calibration_validation_partition_manifest.status
        ),
        "walk_forward_manifest_status": request.walk_forward_manifest.status,
        "bootstrap_manifest_status": request.bootstrap_monte_carlo_manifest.status,
        "stress_manifest_status": request.stress_pack_manifest.status,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "productive_activation": False,
        "o4_unchanged": True,
        "dashboard_authority_effect": "NONE",
        "boundary_guard": dict(result.boundary_guard),
        "non_authorizing": True,
        "observation_pack": result.observation_pack.to_dict(),
    }
    args.export_json_out.parent.mkdir(parents=True, exist_ok=True)
    args.export_json_out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: payload[k] for k in payload if k != "observation_pack"}, indent=2, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
