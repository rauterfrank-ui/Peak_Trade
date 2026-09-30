"""Default Cap22→POLICY_A handoff resolution for productive control plane."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    Cap22ProductiveRealGateError,
    assert_cap22_productive_real_ranking_v1,
)
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    HardFactsCap22MembershipHandoffRequestV1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.constants_v1 import (
    DEFAULT_MEMBERSHIP_SUBDIR,
)


def default_membership_store_root_v1(*, topology_state_root_base: Path | str) -> Path:
    return Path(topology_state_root_base) / DEFAULT_MEMBERSHIP_SUBDIR


def resolve_default_hard_facts_cap22_handoff_v1(
    *,
    ranking_snapshot: Mapping[str, Any],
    explicit_handoff: HardFactsCap22MembershipHandoffRequestV1 | None,
    topology_state_root_base: Path | str,
    membership_store_root: Path | str | None = None,
) -> HardFactsCap22MembershipHandoffRequestV1 | None:
    """When explicit handoff is absent and ranking is productive-real, build default handoff."""

    if explicit_handoff is not None:
        return explicit_handoff
    try:
        assert_cap22_productive_real_ranking_v1(ranking_snapshot)
    except Cap22ProductiveRealGateError:
        return None
    store = (
        Path(membership_store_root)
        if membership_store_root is not None
        else default_membership_store_root_v1(topology_state_root_base=topology_state_root_base)
    )
    return HardFactsCap22MembershipHandoffRequestV1(
        ranking_snapshot=dict(ranking_snapshot),
        membership_store_root=store,
        topology_state_root_base=Path(topology_state_root_base),
    )
