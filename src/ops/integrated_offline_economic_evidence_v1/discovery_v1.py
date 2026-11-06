"""Discovery for verified integrated offline economic evidence v1."""

from __future__ import annotations

from pathlib import Path

from src.ops.integrated_offline_economic_evidence_v1.binding_v1 import (
    resolve_configured_integrated_offline_economic_evidence_relpath_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    SYNTHETIC_FIXTURE_RELPATH_PREFIX,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)


def discover_verified_integrated_offline_economic_evidence_v1(
    *,
    repo_root: Path,
) -> tuple[bool, str]:
    """Return (verified, evidence_note). Fail-closed when config unset or verify fails."""
    root = repo_root.resolve()
    rel = resolve_configured_integrated_offline_economic_evidence_relpath_v1(repo_root=root)
    if not rel:
        return False, "canonical_evidence_relpath_unset_fail_closed"
    if not rel.startswith(SYNTHETIC_FIXTURE_RELPATH_PREFIX):
        return False, "productive_discovery_disabled_until_increment_b"
    evidence_root = root / rel
    result = verify_integrated_offline_economic_evidence_v1(
        repo_root=root,
        evidence_root=evidence_root,
    )
    if not result.verified:
        blockers = ",".join(result.blockers[:5]) or "verify_fail_closed"
        return False, f"integrated_offline_economic_verify_blocked:{blockers}"
    return True, f"verified:{rel}"
