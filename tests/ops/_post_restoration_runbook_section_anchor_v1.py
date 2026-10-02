"""Post-restoration navigational anchors after Master Runbook restructure (AUTHORITY=NONE).

Historical tests extracted §5.3–§5.4 slices from the Master Runbook. CURRENT
runbook no longer carries those headings; bounded subordinate specs retain the
same token semantics. Tests reuse this helper instead of failing closed on
missing runbook substrings.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_HOST_GRAPH_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md"
)
_BASELINE_PRESERVATION_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)


def canonical_productive_no_order_call_graph_section_v1() -> str:
    parts: list[str] = []
    for path in (_HOST_GRAPH_SPEC, _BASELINE_PRESERVATION_SPEC):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)
