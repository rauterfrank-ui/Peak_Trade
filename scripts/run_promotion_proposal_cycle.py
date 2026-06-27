#!/usr/bin/env python3
"""
Run the Promotion Loop v0: build promotion candidates from config patches,
apply governance filters, and materialize live promotion proposals.

Usage:
    # Manual-only mode (only generate proposals, no auto-apply)
    python scripts/run_promotion_proposal_cycle.py \
        --promotion-input-manifest reports/learning_snippets/promotion_input_manifest.json \
        --auto-apply-mode manual_only

    # Bounded auto-apply mode (proposals + live overrides within bounds)
    python scripts/run_promotion_proposal_cycle.py \
        --promotion-input-manifest reports/learning_snippets/promotion_input_manifest.json \
        --auto-apply-mode bounded_auto

    # Disabled mode (no proposals, no auto-apply)
    python scripts/run_promotion_proposal_cycle.py \
        --promotion-input-manifest reports/learning_snippets/promotion_input_manifest.json \
        --auto-apply-mode disabled
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List

from src.governance.promotion_loop import (
    build_promotion_candidates_from_patches,
    build_promotion_proposals,
    check_global_promotion_lock,
    filter_candidates_for_live,
    load_safety_config_from_toml,
    materialize_promotion_proposals,
)
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.promotion_loop.models import DecisionStatus
from src.governance.promotion_loop.policy import AutoApplyBounds, AutoApplyPolicy
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestError,
    ConfigPatchManifestValidationError,
    load_config_patches_for_promotion_from_manifest_path,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the Promotion Loop v0: build promotion candidates from config patches, "
            "apply governance filters, and materialize live promotion proposals."
        )
    )
    parser.add_argument(
        "--promotion-input-manifest",
        type=Path,
        default=None,
        help=("Path to ConfigPatch-Manifest v1 JSON (canonical offline promotion input; AD-01)."),
    )
    parser.add_argument(
        "--non-canonical-demo-legacy-patches",
        action="store_true",
        help=(
            "NON_CANONICAL test-only: load legacy raw demo patch list JSON. "
            "Not a valid ConfigPatch-Manifest v1 input and must never be used as default."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/live_promotion"),
        help="Directory where promotion proposals will be written.",
    )
    parser.add_argument(
        "--live-overrides-path",
        type=Path,
        default=Path("config/live_overrides/auto.toml"),
        help="Path to the live overrides TOML file for bounded auto-apply.",
    )
    parser.add_argument(
        "--auto-apply-mode",
        type=str,
        default="manual_only",
        choices=["disabled", "manual_only", "bounded_auto"],
        help="Auto-apply mode for live promotion.",
    )
    return parser.parse_args()


def _load_non_canonical_demo_legacy_patches() -> List[ConfigPatch]:
    """
    NON_CANONICAL test-only loader for legacy raw demo patch JSON.

    This path exists solely for explicit regression coverage. It is not a valid
    ConfigPatch-Manifest v1 promotion input and must never be used as default SSOT.
    """
    demo_path = Path("reports/learning_snippets/demo_patches_for_promotion.json")

    if not demo_path.is_file():
        print(f"[promotion_loop] NON_CANONICAL demo legacy path: no patches found at {demo_path}")
        return []

    with demo_path.open("r", encoding="utf-8") as handle:
        patches_data = json.load(handle)

    if not isinstance(patches_data, list):
        print("[promotion_loop] NON_CANONICAL demo legacy path: expected JSON array of patches")
        return []

    patches: List[ConfigPatch] = []
    for patch_dict in patches_data:
        if not isinstance(patch_dict, dict):
            continue
        patch_payload = dict(patch_dict)
        if patch_payload.get("generated_at"):
            patch_payload["generated_at"] = datetime.fromisoformat(patch_payload["generated_at"])
        if patch_payload.get("applied_at"):
            patch_payload["applied_at"] = (
                datetime.fromisoformat(patch_payload["applied_at"])
                if patch_payload["applied_at"]
                else None
            )
        if patch_payload.get("promoted_at"):
            patch_payload["promoted_at"] = (
                datetime.fromisoformat(patch_payload["promoted_at"])
                if patch_payload["promoted_at"]
                else None
            )
        if isinstance(patch_payload.get("status"), str):
            patch_payload["status"] = PatchStatus(patch_payload["status"])
        patch_payload.setdefault("old_value", None)
        patches.append(ConfigPatch(**patch_payload))

    print(
        "[promotion_loop] NON_CANONICAL demo legacy path loaded "
        f"{len(patches)} patch(es) from {demo_path}"
    )
    return patches


def _load_patches_for_promotion(
    *,
    promotion_input_manifest: Path | None,
    non_canonical_demo_legacy_patches: bool = False,
) -> List[ConfigPatch]:
    """
    Load ConfigPatch objects that are candidates for live promotion.

    Canonical path (AD-01): ConfigPatch-Manifest v1 JSON via Package-A validation.
    """
    if non_canonical_demo_legacy_patches:
        return _load_non_canonical_demo_legacy_patches()

    if promotion_input_manifest is None:
        print(
            "[promotion_loop] Error: --promotion-input-manifest is required for the "
            "canonical ConfigPatch-Manifest v1 promotion input."
        )
        print(
            "[promotion_loop] demo_patches_for_promotion.json is a NON-SSOT test fixture "
            "only; use --non-canonical-demo-legacy-patches explicitly for legacy tests."
        )
        return []

    try:
        patches = load_config_patches_for_promotion_from_manifest_path(promotion_input_manifest)
    except ConfigPatchManifestValidationError as exc:
        print(
            f"[promotion_loop] ConfigPatch-Manifest v1 validation failed ({exc.phase.value}): {exc}"
        )
        for error in exc.errors:
            print(f"[promotion_loop]   - {error}")
        if exc.verdict:
            print(f"[promotion_loop] Verdict: {exc.verdict}")
        return []
    except ConfigPatchManifestError as exc:
        print(f"[promotion_loop] Failed to load promotion input manifest: {exc}")
        return []

    print(
        "[promotion_loop] Loaded "
        f"{len(patches)} patch(es) from ConfigPatch-Manifest v1 {promotion_input_manifest}"
    )
    return patches


def main() -> None:
    """Main entry point for the promotion proposal cycle."""
    args = parse_args()

    # Load safety config (P0/P1 features)
    config_path = Path("config/promotion_loop_config.toml")
    safety_config = load_safety_config_from_toml(config_path)
    print(f"[promotion_loop] Loaded safety config from {config_path}")

    # Check global promotion lock (P1)
    lock_warning = check_global_promotion_lock(safety_config)
    if lock_warning:
        print(f"[promotion_loop] {lock_warning}")
        if args.auto_apply_mode == "bounded_auto":
            print("[promotion_loop] Forcing mode to manual_only due to global lock.")
            args.auto_apply_mode = "manual_only"

    print("[promotion_loop] Loading patches for promotion...")
    patches = _load_patches_for_promotion(
        promotion_input_manifest=args.promotion_input_manifest,
        non_canonical_demo_legacy_patches=args.non_canonical_demo_legacy_patches,
    )
    print(f"[promotion_loop] Loaded {len(patches)} patch(es).")

    candidates = build_promotion_candidates_from_patches(patches)
    print(f"[promotion_loop] Built {len(candidates)} promotion candidate(s).")

    # Demo mode: Mark candidates with high confidence as eligible for live
    # In production, this would be done by policy or operator review
    for candidate in candidates:
        confidence = candidate.patch.confidence_score
        if confidence and confidence >= 0.75:
            candidate.eligible_for_live = True
            print(
                f"[promotion_loop] Marked {candidate.patch.id} as eligible_for_live (confidence: {confidence:.2f})"
            )
        else:
            conf_str = f"{confidence:.2f}" if confidence else "N/A"
            print(
                f"[promotion_loop] Rejected {candidate.patch.id} due to low confidence ({conf_str})"
            )

    # Apply P0/P1 safety filters
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode=args.auto_apply_mode,
    )
    accepted = [d for d in decisions if d.status is DecisionStatus.ACCEPTED_FOR_PROPOSAL]

    print(f"[promotion_loop] Accepted candidates: {len(accepted)}")
    print(f"[promotion_loop] Rejected candidates: {len(decisions) - len(accepted)}")

    # Show P0 violations if any
    p0_violations = [
        d for d in decisions if any(f.startswith("P0_") for f in d.candidate.safety_flags)
    ]
    if p0_violations:
        print(
            f"[promotion_loop] WARNING: {len(p0_violations)} candidates have P0 safety violations"
        )

    proposals = build_promotion_proposals(decisions)
    if not proposals:
        print("[promotion_loop] No proposals generated.")
        return

    written = materialize_promotion_proposals(proposals, args.output_dir)
    print(
        f"[promotion_loop] Written {len(written)} proposal artifact file(s) to {args.output_dir}."
    )

    # Auto-Apply
    policy = AutoApplyPolicy(
        mode=args.auto_apply_mode,
        leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=0.25),
        trigger_delay_bounds=AutoApplyBounds(min_value=3.0, max_value=15.0, max_step=2.0),
        macro_weight_bounds=AutoApplyBounds(min_value=0.0, max_value=0.8, max_step=0.1),
    )

    live_path = apply_proposals_to_live_overrides(
        proposals,
        policy=policy,
        live_override_path=args.live_overrides_path,
    )
    if live_path is None:
        print(f"[promotion_loop] Auto-apply: no changes applied (mode={args.auto_apply_mode!r}).")
    else:
        print(f"[promotion_loop] Auto-apply: written live overrides to {live_path}")


if __name__ == "__main__":
    main()
