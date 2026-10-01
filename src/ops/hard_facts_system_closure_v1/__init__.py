"""Hard-facts deterministic system closure (Peak_Trade)."""

from __future__ import annotations

from typing import Any

from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    HardFactsAuthorityProofResultV1,
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.hard_facts_system_closure_v1.constants_v1 import PACKAGE_MARKER
from src.ops.hard_facts_system_closure_v1.durable_kill_switch_mv2_binding_v1 import (
    DurableKillSwitchMv2BindingV1,
    resolve_durable_kill_switch_for_mv2_host_v1,
)

# productive_mf_n5_handoff_join_v1 imports recovered_topology consumer; loading it at
# package init creates a cycle when N5 lifecycle imports position_aware_rotation_v1.
_HANDOFF_LAZY_NAMES = frozenset(
    {
        "HardFactsCap22MembershipHandoffRequestV1",
        "HardFactsMfN5HandoffResultV1",
        "execute_hard_facts_cap22_to_mf_n5_handoff_v1",
        "resolve_membership_via_hard_facts_handoff_v1",
    }
)


def __getattr__(name: str) -> Any:
    if name in _HANDOFF_LAZY_NAMES:
        from src.ops.hard_facts_system_closure_v1 import productive_mf_n5_handoff_join_v1 as handoff

        return getattr(handoff, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DurableKillSwitchMv2BindingV1",
    "HardFactsAuthorityProofResultV1",
    "HardFactsCap22MembershipHandoffRequestV1",
    "HardFactsMfN5HandoffResultV1",
    "PACKAGE_MARKER",
    "execute_hard_facts_cap22_to_mf_n5_handoff_v1",
    "prove_hard_facts_authority_invariants_v1",
    "resolve_durable_kill_switch_for_mv2_host_v1",
    "resolve_membership_via_hard_facts_handoff_v1",
]
