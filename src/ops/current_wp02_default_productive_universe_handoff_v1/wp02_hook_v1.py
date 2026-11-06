"""Standing supervisor WP-02 hook — productive default chain composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp02_default_productive_universe_handoff_v1.composition_v1 import (
    Wp02ProductiveDefaultChainRequestV1,
    Wp02ProductiveDefaultChainResultV1,
    run_wp02_productive_default_chain_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.errors_v1 import (
    Wp02ProductiveDefaultChainError,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.time_alignment_v1 import (
    producer_observed_at_unix_from_source_event_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.wp02_insertion_v1 import (
    Wp02HookV1,
    Wp02InsertionContextV1,
)


@dataclass(frozen=True)
class Wp02HookBindingV1:
    wp02_state_root: Path
    topology_state_root_base: Path
    repository_sha: str
    universe_source_payload: Mapping[str, Any]
    universe_mark_price_payload: Mapping[str, Any]
    source_event_time: str
    lane_assignment_writer: Any = None
    producer_observed_at_unix: float | None = None


def build_default_wp02_hook_v1(binding: Wp02HookBindingV1) -> Wp02HookV1:
    def _hook(ctx: Wp02InsertionContextV1) -> None:
        if ctx.economic_md_mark_count < 1:
            raise Wp02ProductiveDefaultChainError(
                "ECONOMIC_MD_MARKS_INSUFFICIENT",
                str(ctx.economic_md_mark_count),
            )
        result = run_wp02_productive_default_chain_v1(
            Wp02ProductiveDefaultChainRequestV1(
                wp02_state_root=binding.wp02_state_root,
                public_store_root=ctx.public_store_root,
                venue_native_id=ctx.venue_native_id,
                repository_sha=binding.repository_sha,
                universe_source_payload=binding.universe_source_payload,
                universe_mark_price_payload=binding.universe_mark_price_payload,
                source_event_time=binding.source_event_time,
                topology_state_root_base=binding.topology_state_root_base,
                producer_observed_at_unix=(
                    binding.producer_observed_at_unix
                    if binding.producer_observed_at_unix is not None
                    else producer_observed_at_unix_from_source_event_v1(binding.source_event_time)
                ),
                session_id_prefix=f"supervisor-tick-{ctx.tick_index}",
                lane_assignment_writer=binding.lane_assignment_writer,
            )
        )
        ctx.wp02_result_sink["chain_result"] = result
        if not result.ok:
            raise Wp02ProductiveDefaultChainError(result.failure_code or "WP02_CHAIN_FAIL_CLOSED")

    return _hook
