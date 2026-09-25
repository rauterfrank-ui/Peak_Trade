#!/usr/bin/env python3
"""
Generate demo ConfigPatch objects for the Promotion Loop.

Writes:
  reports/learning_snippets/demo_patches_for_promotion.json

This is a lightweight stand-in for the (future) Learning Loop bridge/emitter.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from src.meta.learning_loop.models import ConfigPatch, PatchStatus


def _serialize_patch(patch: ConfigPatch) -> Dict[str, Any]:
    d = asdict(patch)
    # datetimes -> ISO
    for k in ("generated_at", "applied_at", "promoted_at"):
        if d.get(k) is not None:
            d[k] = d[k].isoformat()
    # enum -> value
    if isinstance(d.get("status"), PatchStatus):
        d["status"] = d["status"].value
    return d


def build_demo_patches(*, variant: str, base_confidence: float) -> List[ConfigPatch]:
    now = datetime.utcnow()

    # "Good" candidates (should be accepted in manual_only and bounded_auto if eligible)
    patches: List[ConfigPatch] = [
        ConfigPatch(
            id="demo_patch_leverage_175",
            target="portfolio.leverage",
            old_value=1.0,
            new_value=1.75,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=now - timedelta(hours=2),
            applied_at=now - timedelta(hours=1, minutes=50),
            reason="Demo: improved stability in offline runs",
            confidence_score=min(0.99, base_confidence + 0.10),
            meta={"is_live_ready": True},
        ),
        ConfigPatch(
            id="demo_patch_trigger_delay_8",
            target="strategy.trigger_delay",
            old_value=10.0,
            new_value=8.0,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=now - timedelta(hours=2),
            applied_at=now - timedelta(hours=1, minutes=45),
            reason="Demo: reduced latency after trigger-training drill",
            confidence_score=min(0.99, base_confidence + 0.05),
            meta={"is_live_ready": True},
        ),
        ConfigPatch(
            id="demo_patch_macro_weight_035",
            target="macro.regime_weight",
            old_value=0.25,
            new_value=0.35,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=now - timedelta(hours=2),
            applied_at=now - timedelta(hours=1, minutes=40),
            reason="Demo: better drawdown profile in macro stress",
            confidence_score=min(0.99, base_confidence + 0.08),
            meta={"is_live_ready": True},
        ),
    ]

    if variant == "simple":
        return patches

    # "Diverse" adds some intentionally problematic candidates to exercise safety logic
    patches.extend(
        [
            ConfigPatch(
                id="demo_patch_blacklisted_stop_loss",
                target="risk.stop_loss",
                old_value=0.02,
                new_value=0.015,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now - timedelta(hours=2),
                applied_at=now - timedelta(hours=1, minutes=30),
                reason="Demo: should be blocked by blacklist",
                confidence_score=min(0.99, base_confidence + 0.12),
                meta={"is_live_ready": True},
            ),
            ConfigPatch(
                id="demo_patch_excessive_leverage",
                target="portfolio.leverage",
                old_value=2.0,
                new_value=3.5,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now - timedelta(hours=2),
                applied_at=now - timedelta(hours=1, minutes=20),
                reason="Demo: should be rejected by bounds/hard-limits",
                confidence_score=min(0.99, base_confidence + 0.12),
                meta={"is_live_ready": True},
            ),
            ConfigPatch(
                id="demo_patch_low_confidence",
                target="macro.regime_weight",
                old_value=0.35,
                new_value=0.45,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now - timedelta(hours=2),
                applied_at=now - timedelta(hours=1, minutes=10),
                reason="Demo: should be rejected by confidence heuristic in script",
                confidence_score=max(0.10, base_confidence - 0.20),
                meta={"is_live_ready": True},
            ),
        ]
    )

    return patches


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate demo patches for Promotion Loop.")
    p.add_argument(
        "--output",
        type=Path,
        default=Path("reports/learning_snippets/demo_patches_for_promotion.json"),
        help="Output JSON path.",
    )
    p.add_argument(
        "--variant",
        type=str,
        default="diverse",
        choices=["simple", "diverse"],
        help="Patch set variant.",
    )
    p.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        help="Base confidence score for the demo patches.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    patches = build_demo_patches(variant=args.variant, base_confidence=args.confidence)

    payload = [_serialize_patch(p) for p in patches]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[demo_patches] Wrote {len(patches)} patch(es) to {args.output}")


if __name__ == "__main__":
    main()
