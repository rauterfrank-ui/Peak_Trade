"""Branch-tip runtime integrity for Treasury productive capture on feature branches.

PL_TF_002 protected wire surfaces must match origin/main; HEAD may be ahead for
this Owner-GO WP only. Does not relax POST/mutation gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ops.pl_tf_002_productive_read_only_session_executor_v1.runtime_integrity_v1 import (
    GitPlTf002RuntimeIntegrityBackendV1,
    PROTECTED_WIRE_SURFACE_PATHS,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)


@dataclass(frozen=True)
class TreasuryProductiveBranchTipIntegrityBackendV1:
    """Declared SHA must equal HEAD; protected PL_TF_002 surfaces must match origin/main."""

    repo_root: Path
    declared_sha: str

    def resolve_origin_main_sha_v1(self) -> str:
        return str(self.declared_sha or "").strip().lower()

    def resolve_head_sha_v1(self) -> str:
        return GitPlTf002RuntimeIntegrityBackendV1(repo_root=self.repo_root).resolve_head_sha_v1()

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str:
        return GitPlTf002RuntimeIntegrityBackendV1(repo_root=self.repo_root).diff_origin_main_for_paths_v1(
            paths
        )


def assert_treasury_productive_branch_tip_integrity_v1(
    *,
    declared_origin_main_sha: str,
    repo_root: Path | str,
) -> str:
    backend = TreasuryProductiveBranchTipIntegrityBackendV1(
        repo_root=Path(repo_root),
        declared_sha=str(declared_origin_main_sha or "").strip().lower(),
    )
    head = backend.resolve_head_sha_v1()
    declared = backend.resolve_origin_main_sha_v1()
    if len(declared) != 40 or declared != head:
        raise TreasuryProductiveReadOnlyVenueObservationError(
            "TREASURY_PRODUCTIVE_BRANCH_TIP_SHA_MISMATCH"
        )
    drift = backend.diff_origin_main_for_paths_v1(PROTECTED_WIRE_SURFACE_PATHS)
    if drift.strip():
        raise TreasuryProductiveReadOnlyVenueObservationError("PL_TF_002_PROTECTED_SURFACE_DRIFT")
    return head
