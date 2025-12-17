"""
Core engine functions for the Promotion Loop v0.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import toml

from src.meta.learning_loop.models import ConfigPatch, PatchStatus

from .models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from .policy import AutoApplyBounds, AutoApplyPolicy
from .safety import (
    SafetyConfig,
    apply_safety_filters,
    has_p0_violations,
    write_audit_log_entry,
)


def build_promotion_candidates_from_patches(
    patches: Iterable[ConfigPatch],
) -> list[PromotionCandidate]:
    """
    Build PromotionCandidate objects from ConfigPatch instances.

    v0 heuristic:
    - Only consider patches with status APPLIED_OFFLINE or PROMOTED.
    - Tag candidates based on target heuristics (very simple).
    - eligible_for_live bleibt False (muss explizit gesetzt werden).
    """
    candidates: list[PromotionCandidate] = []

    for patch in patches:
        if patch.status not in (PatchStatus.APPLIED_OFFLINE, PatchStatus.PROMOTED):
            continue

        tags: list[str] = []
        target_lower = patch.target.lower()
        if "leverage" in target_lower:
            tags.append("leverage")
        if "risk" in target_lower:
            tags.append("risk")
        if "macro" in target_lower:
            tags.append("macro")
        if "trigger" in target_lower:
            tags.append("trigger")

        candidate = PromotionCandidate(
            patch=patch,
            tags=tags,
            eligible_for_live=False,
            notes="Initial candidate built from ConfigPatch; eligibility must be set by policy or operator.",
        )
        candidates.append(candidate)

    return candidates


def filter_candidates_for_live(
    candidates: Iterable[PromotionCandidate],
    safety_config: SafetyConfig | None = None,
    mode: str = "manual_only",
) -> list[PromotionDecision]:
    """
    Apply conservative governance filters to candidates.

    v1 implementation:
    - Apply P0 safety filters (blacklist, bounds, guardrails)
    - Reject candidates with P0 violations for bounded_auto
    - Reject candidates not marked as eligible_for_live
    - Extra sanity checks (Leverage-Hardlimit)

    Args:
        candidates: Promotion candidates to filter
        safety_config: Safety configuration (P0/P1 settings)
        mode: Promotion mode (manual_only, bounded_auto, disabled)

    Returns:
        List of promotion decisions
    """
    decisions: list[PromotionDecision] = []

    MAX_LEVERAGE_HARD_LIMIT = 3.0

    for candidate in candidates:
        reasons: list[str] = []

        # Apply P0 safety filters
        if safety_config:
            apply_safety_filters(candidate, safety_config, mode)

        # Check eligibility
        if not candidate.eligible_for_live:
            reasons.append("candidate not marked as eligible_for_live")
            decision = PromotionDecision(
                candidate=candidate,
                status=DecisionStatus.REJECTED_BY_POLICY,
                reasons=reasons,
            )
            decisions.append(decision)

            # P1: Write audit log
            if safety_config:
                write_audit_log_entry(candidate, decision, mode, safety_config)

            continue

        # Check for P0 violations
        if has_p0_violations(candidate):
            reasons.append("candidate has P0 safety violations")
            reasons.extend(candidate.safety_flags)
            decision = PromotionDecision(
                candidate=candidate,
                status=DecisionStatus.REJECTED_BY_POLICY,
                reasons=reasons,
            )
            decisions.append(decision)

            # P1: Write audit log
            if safety_config:
                write_audit_log_entry(candidate, decision, mode, safety_config)

            continue

        # Legacy sanity check: Leverage hard limit
        target = candidate.patch.target.lower()
        if "leverage" in target:
            new_value = candidate.patch.new_value
            if isinstance(new_value, (int, float)) and new_value > MAX_LEVERAGE_HARD_LIMIT:
                reasons.append(
                    f"new leverage value {new_value} exceeds hard limit {MAX_LEVERAGE_HARD_LIMIT}"
                )
                decision = PromotionDecision(
                    candidate=candidate,
                    status=DecisionStatus.REJECTED_BY_SANITY_CHECK,
                    reasons=reasons,
                )
                decisions.append(decision)

                # P1: Write audit log
                if safety_config:
                    write_audit_log_entry(candidate, decision, mode, safety_config)

                continue

        # Accepted
        decision = PromotionDecision(
            candidate=candidate,
            status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
            reasons=reasons,
        )
        decisions.append(decision)

        # P1: Write audit log
        if safety_config:
            write_audit_log_entry(candidate, decision, mode, safety_config)

    return decisions


def build_promotion_proposals(
    decisions: Iterable[PromotionDecision],
    *,
    proposal_id_prefix: str = "live_promotion",
) -> list[PromotionProposal]:
    """
    Group accepted decisions into a single PromotionProposal (v0: genau eines).
    """
    accepted = [d for d in decisions if d.status is DecisionStatus.ACCEPTED_FOR_PROPOSAL]

    if not accepted:
        return []

    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    proposal_id = f"{proposal_id_prefix}_{now}"

    proposal = PromotionProposal(
        proposal_id=proposal_id,
        title=f"Live Promotion Proposal ({now})",
        description="Auto-generated proposal from accepted promotion candidates.",
        decisions=accepted,
        meta={
            "generated_at": now,
            "num_candidates": len(accepted),
        },
    )
    return [proposal]


def materialize_promotion_proposals(
    proposals: Iterable[PromotionProposal],
    base_dir: Path,
) -> list[Path]:
    """
    Write proposal artifacts to disk under reports/live_promotion/<proposal_id>/.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for proposal in proposals:
        proposal_dir = base_dir / proposal.proposal_id
        proposal_dir.mkdir(parents=True, exist_ok=True)
        proposal.output_dir = proposal_dir

        # proposal_meta.json
        meta_path = proposal_dir / "proposal_meta.json"
        meta_payload = {
            "proposal_id": proposal.proposal_id,
            "title": proposal.title,
            "description": proposal.description,
            "meta": proposal.meta,
            "num_decisions": len(proposal.decisions),
        }
        meta_path.write_text(_to_json(meta_payload), encoding="utf-8")
        written_paths.append(meta_path)

        # config_patches.json
        patches_path = proposal_dir / "config_patches.json"
        patches_payload = []
        for decision in proposal.decisions:
            patch_dict = asdict(decision.candidate.patch)
            patches_payload.append(
                {
                    "decision_status": decision.status.value,
                    "decision_reasons": decision.reasons,
                    "candidate_tags": decision.candidate.tags,
                    "patch": patch_dict,
                }
            )
        patches_path.write_text(_to_json(patches_payload), encoding="utf-8")
        written_paths.append(patches_path)

        # OPERATOR_CHECKLIST.md
        checklist_path = proposal_dir / "OPERATOR_CHECKLIST.md"
        checklist_path.write_text(_build_operator_checklist_md(proposal), encoding="utf-8")
        written_paths.append(checklist_path)

    return written_paths


def apply_proposals_to_live_overrides(
    proposals: Iterable[PromotionProposal],
    *,
    policy: AutoApplyPolicy,
    live_override_path: Path,
) -> Path | None:
    """
    Optional step: apply accepted promotion proposals to a live override TOML file,
    respecting the given AutoApplyPolicy.

    - Wenn policy.mode != "bounded_auto": macht nichts, return None.
    - Nur numerische Patches.
    - Nur Patches mit passenden Bounds (leverage/trigger/macro).
    """
    if not policy.is_bounded_auto():
        return None

    updates = {}

    for proposal in proposals:
        for decision in proposal.decisions:
            if decision.status is not DecisionStatus.ACCEPTED_FOR_PROPOSAL:
                continue

            patch = decision.candidate.patch
            if not isinstance(patch.new_value, (int, float)):
                continue

            bounds: AutoApplyBounds | None = None
            for tag in decision.candidate.tags:
                if tag == "leverage":
                    bounds = policy.leverage_bounds
                    break
                if tag == "macro":
                    bounds = policy.macro_weight_bounds
                    break
                if tag == "trigger":
                    bounds = policy.trigger_delay_bounds
                    break

            if bounds is None:
                continue

            old_val = patch.old_value
            new_val = float(patch.new_value)

            if new_val < bounds.min_value or new_val > bounds.max_value:
                continue

            if isinstance(old_val, (int, float)):
                delta = abs(new_val - float(old_val))
                if delta > bounds.max_step:
                    continue

            updates[patch.target] = new_val

    if not updates:
        return None

    live_override_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if live_override_path.exists():
        try:
            data = toml.loads(live_override_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    auto_table = data.get("auto_applied", {})
    for target, new_value in updates.items():
        auto_table[target] = new_value
    data["auto_applied"] = auto_table

    live_override_path.write_text(toml.dumps(data), encoding="utf-8")
    return live_override_path


def _to_json(obj: object) -> str:
    """Helper to convert object to JSON string."""
    import json
    from datetime import datetime

    def json_serial(o):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    return json.dumps(obj, indent=2, sort_keys=True, default=json_serial)


def _build_operator_checklist_md(proposal: PromotionProposal) -> str:
    """Build operator checklist markdown for a proposal."""
    lines = []
    lines.append(f"# Live Promotion Proposal: {proposal.proposal_id}")
    lines.append("")
    lines.append(f"**Title:** {proposal.title}")
    lines.append("")
    lines.append(f"**Description:** {proposal.description}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Generated at: {proposal.meta.get('generated_at', 'n/a')}")
    lines.append(f"- Number of accepted candidates: {len(proposal.decisions)}")
    lines.append("")

    # Check for P0 violations
    has_p0 = any(
        any(f.startswith("P0_") for f in d.candidate.safety_flags)
        for d in proposal.decisions
    )
    if has_p0:
        lines.append("## ⚠️ Safety Warnings")
        lines.append("")
        lines.append("**WARNING:** Some candidates have P0 safety violations.")
        lines.append("These candidates CANNOT be auto-promoted in bounded_auto mode.")
        lines.append("Manual review and approval is required.")
        lines.append("")

    lines.append("## Checklist")
    lines.append("- [ ] Review each patch and confirm it is safe for live.")
    lines.append("- [ ] Verify that no R&D strategies are being promoted.")
    lines.append("- [ ] Verify risk limits and leverage bounds.")
    lines.append("- [ ] Check that no P0 safety violations are present.")
    lines.append("- [ ] Run additional TestHealth / backtests if needed.")
    lines.append("- [ ] Perform Go/No-Go decision according to the governance runbook.")
    lines.append("")
    lines.append("## Patches")
    for idx, decision in enumerate(proposal.decisions, start=1):
        patch = decision.candidate.patch
        candidate = decision.candidate

        lines.append(f"### Patch {idx}: {patch.id}")
        lines.append(f"- Target: `{patch.target}`")
        lines.append(f"- Old value: `{patch.old_value}`")
        lines.append(f"- New value: `{patch.new_value}`")
        lines.append(f"- Confidence: `{patch.confidence_score:.3f}`" if patch.confidence_score else "- Confidence: N/A")
        lines.append(f"- Tags: {', '.join(candidate.tags) or '(none)'}")

        # Show safety flags if present
        if candidate.safety_flags:
            lines.append(f"- **Safety Flags:** {', '.join(candidate.safety_flags)}")

        if decision.reasons:
            lines.append(f"- Decision notes: {', '.join(decision.reasons)}")
        lines.append("")

    return "\n".join(lines)
