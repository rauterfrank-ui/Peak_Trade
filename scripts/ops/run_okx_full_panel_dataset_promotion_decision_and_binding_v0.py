#!/usr/bin/env python3
"""Run bounded OKX full-panel dataset promotion decision and immutable binding v0.

Offline-only promotion evaluation for manifest-verified fetch completeness candidates.
No economic evaluation, no runtime or authority effect.
Operator GO: GO_BOUNDED_DATASET_PROMOTION_DECISION_AND_BINDING_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_full_panel_dataset_promotion_decision_and_binding_v0 import (  # noqa: E402
    GO_TOKEN,
    PromotionDecisionStatus,
    run_okx_full_panel_dataset_promotion_decision_and_binding_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True, help=f"Required GO token: {GO_TOKEN}")
    parser.add_argument(
        "--candidate-root",
        type=Path,
        required=True,
        help="Immutable staged dataset candidate root",
    )
    parser.add_argument(
        "--durable-archive-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    parser.add_argument("--implementation-evidence-ref", default="")
    parser.add_argument("--closeout-evidence-ref", default="")
    parser.add_argument("--closeout-manifest-digest", default="")
    parser.add_argument(
        "--no-registry-write",
        action="store_true",
        help="Evaluate only; do not write promoted dataset registry",
    )
    args = parser.parse_args()

    if args.confirm != GO_TOKEN:
        _die(f"ERR: confirm_go_token_required:{GO_TOKEN}")

    result = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=args.confirm,
        candidate_root=args.candidate_root,
        durable_archive_root=args.durable_archive_root,
        repo_root=_REPO_ROOT,
        implementation_evidence_ref=args.implementation_evidence_ref,
        closeout_evidence_ref=args.closeout_evidence_ref,
        closeout_manifest_digest=args.closeout_manifest_digest or None,
        write_registry=not args.no_registry_write,
    )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        args.durable_archive_root
        / "implementation"
        / f"bounded_dataset_promotion_decision_and_binding_v0_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=True)

    summary = {
        "go_token": GO_TOKEN,
        "decision": result.decision.value,
        "reason_codes": list(result.reason_codes),
        "dataset_promoted": result.dataset_promoted,
        "dataset_binding_active": result.dataset_binding_active,
        "registry_mutation": result.registry_mutation,
        "idempotent_status": result.idempotent_status.value,
        "promoted_dataset_root": result.promoted_dataset_root,
        "candidate_integrity_status": result.candidate_integrity.status,
        "dataset_content_digest": result.candidate_integrity.dataset_content_digest,
        "economic_evaluation_authorized": result.economic_evaluation_authorized,
        "promotion_effect": result.promotion_effect,
        "runtime_effect": result.runtime_effect,
        "authority_effect": result.authority_effect,
    }
    (evidence_root / "EXECUTION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "VERDICT.md").write_text(
        "\n".join(
            [
                "# VERDICT",
                "",
                f"DATASET_PROMOTION_DECISION={result.decision.value}",
                f"DATASET_PROMOTED={str(result.dataset_promoted).lower()}",
                f"DATASET_BINDING_ACTIVE={str(result.dataset_binding_active).lower()}",
                f"ECONOMIC_EVALUATION_AUTHORIZED={str(result.economic_evaluation_authorized).lower()}",
                f"PROMOTION_EFFECT={result.promotion_effect}",
                f"RUNTIME_EFFECT={result.runtime_effect}",
                f"AUTHORITY_EFFECT={result.authority_effect}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if result.promotion_binding is not None:
        (evidence_root / "promotion_binding.json").write_text(
            json.dumps(result.promotion_binding.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    from scripts.ops.primary_evidence_retention_v0 import finalize_durable_bundle_manifest

    rc, _ = finalize_durable_bundle_manifest(evidence_root)
    print(json.dumps({**summary, "evidence_root": str(evidence_root), "manifest_verify_rc": rc}))

    if result.decision not in {
        PromotionDecisionStatus.PROMOTED,
        PromotionDecisionStatus.REJECTED,
        PromotionDecisionStatus.BLOCKED,
        PromotionDecisionStatus.INCONCLUSIVE,
    }:
        _die(f"ERR: unexpected_decision:{result.decision.value}")


if __name__ == "__main__":
    main()
