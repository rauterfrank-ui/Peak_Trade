"""Read-only handoff check for an original, bound ENTER plan.

The caller owns the handoff before POST Owner-GO consumption and permit
issuance. This module reads original state and public market data and returns
a liquidity assessment for the exact envelope.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from time import time
from typing import TypeVar

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperLiquidityPolicyV1,
    collect_bound_paper_liquidity_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    inspect_original_portfolio_execution_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.plan_origin_v1 import (
    PortfolioExecutionPlanContextV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parents[2] / "docs/ops/specs/LIVE_ENTRY_LIQUIDITY_PROFILES_V1.toml"
)
_DECIMAL_FIELDS = ("spread_limit_bps", "slippage_limit_bps", "adv_participation_limit")
_T = TypeVar("_T")


@dataclass(frozen=True)
class LiveEntryLiquidityPrecheckV1:
    status: str
    reason_codes: tuple[str, ...]
    evidence: dict = field(default_factory=dict)
    authority_effect: str = "NONE"


class LiveEntryLiquidityBlockedV1(ValueError):
    def __init__(self, assessment: LiveEntryLiquidityPrecheckV1):
        super().__init__(", ".join(assessment.reason_codes))
        self.assessment = assessment


def _load_profile(path: Path, lane_id: str) -> tuple[str, PaperLiquidityPolicyV1]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    assignments = document["slot_profiles"]
    if document["schema"] != "live_entry_liquidity_profiles.v1" or set(assignments) != set(
        LANE_IDS
    ):
        raise ValueError("LIVE_ENTRY_LIQUIDITY_SLOT_PROFILE_MAP_INVALID")
    name = assignments[lane_id]
    if not isinstance(name, str) or not name or name.strip() != name:
        raise ValueError(f"LIVE_ENTRY_LIQUIDITY_PROFILE_UNASSIGNED:{lane_id}")
    profile = document["profiles"].get(name)
    if not isinstance(profile, dict) or profile.keys() != {*_DECIMAL_FIELDS, "adv_days"}:
        raise ValueError(f"LIVE_ENTRY_LIQUIDITY_PROFILE_INVALID:{lane_id}:{name}")
    spread, slip, participation = (Decimal(str(profile[key])) for key in _DECIMAL_FIELDS)
    days = profile["adv_days"]
    if (
        any(not value.is_finite() or value <= 0 for value in (spread, slip, participation))
        or participation > 1
        or type(days) is not int
        or not 1 <= days < 300
    ):
        raise ValueError(f"LIVE_ENTRY_LIQUIDITY_PROFILE_LIMITS_INVALID:{lane_id}:{name}")
    return name, PaperLiquidityPolicyV1(spread, slip, participation, days)


def _read_original_entry(owner, reservation_id, envelope, plan_context, futures_financial_custody):
    proof = inspect_original_portfolio_execution_context_v1(
        envelope=envelope,
        portfolio_budget_owner=owner,
        portfolio_reservation_id=reservation_id,
        execution_plan_context=plan_context,
        required_execution_environment="LIVE",
        futures_financial_custody=futures_financial_custody,
    )
    state = owner.risk_snapshot_v1()["state"]
    (reservation,) = (
        row for row in state["reservations"] if row["reservation_id"] == reservation_id
    )
    lane = reservation["slot_id"]
    link = state["execution_links"][reservation_id]
    origin = link["plan_origin"]
    intent = origin["canonical_order_intent"]
    raw_bound = reservation["binding"]["bound"]
    if (
        lane not in LANE_IDS
        or state["lane_bindings"][lane]["bound"] != raw_bound
        or reservation["state"] != "COMMITTED"
        or link["phase"] != "PLAN_BOUND"
        or origin["digest"] != proof["plan_origin_digest"]
        or link["envelope"] != envelope.to_runtime_json_v1()
        or "double_play" in link
        or envelope.instrument_id != raw_bound["venue_native_id"]
        or intent["instrument_id"] != raw_bound["instrument_id"]
        or intent["decision_id"] != reservation["decision_id"]
        or intent["intent_action"] != {"buy": "ENTER_LONG", "sell": "ENTER_SHORT"}[envelope.side]
    ):
        raise ValueError("LIVE_ENTRY_LIQUIDITY_ORIGINAL_ENTRY_BINDING_MISMATCH")
    return {
        "lane_id": lane,
        "reservation_id": reservation_id,
        "decision_id": reservation["decision_id"],
        "cycle_id": reservation["cycle_id"],
        "envelope_digest": envelope.envelope_digest,
        "plan_origin_digest": origin["digest"],
        "order_environment": proof["order_environment"],
        "bound": raw_bound,
        "contract": state["sizing_bindings"][reservation_id]["applied_input"]["instrument"],
    }


def precheck_live_entry_liquidity_v1(
    *,
    owner,
    reservation_id: str,
    envelope: FinalOrderEnvelopeV1,
    execution_plan_context,
    transport_factory: Callable[[], FullCoreFreshPretradeGetTransportV1],
    profile_path: Path = DEFAULT_PROFILE_PATH,
    futures_financial_custody=None,
    clock: Callable[[], float] = time,
) -> LiveEntryLiquidityPrecheckV1:
    """Evaluate fresh book/ADV data once for the existing committed order plan."""
    evidence = {}
    try:
        if (
            type(envelope) is not FinalOrderEnvelopeV1
            or envelope.reduce_only
            or envelope.order_type != "market"
            or envelope.quantity_unit != "CONTRACTS"
            or envelope.side not in {"buy", "sell"}
        ):
            raise ValueError("LIVE_ENTRY_LIQUIDITY_MARKET_ENTER_REQUIRED")
        args = (
            owner,
            reservation_id,
            envelope,
            execution_plan_context,
            futures_financial_custody,
        )
        original = _read_original_entry(*args)
        evidence = {key: value for key, value in original.items() if key != "contract"}
        lane = original["lane_id"]
        profile_id, policy = _load_profile(profile_path, lane)
        profile = {key: str(value) for key, value in asdict(policy).items()}
        evidence.update(profile_id=profile_id, profile=profile)
        capture = canonical_digest_v1(
            {
                "lane_id": lane,
                "envelope_digest": envelope.envelope_digest,
                "profile_id": profile_id,
                "profile": profile,
                "selection": original["bound"]["selection_integrity_digest"],
            }
        )
        liquidity = collect_bound_paper_liquidity_v1(
            transport_factory(),
            bound=BoundInstrumentV1(**original["bound"]),
            policy=policy,
            capture_id=capture,
            clock=clock,
        )
        created_at = datetime.fromisoformat(envelope.creation_epoch.replace("Z", "+00:00"))
        if created_at.utcoffset() is None or liquidity.observed_unix < created_at.timestamp():
            raise ValueError("LIVE_ENTRY_LIQUIDITY_CAPTURE_PRECEDES_PLAN")
        snapshot = liquidity.snapshot
        planned = original["contract"]
        if (
            snapshot.contract_size,
            snapshot.lot_size,
            snapshot.minimum_contracts,
            snapshot.tick_size,
        ) != tuple(
            Decimal(planned[key])
            for key in ("contract_multiplier", "lot_size", "minimum_quantity", "tick_size")
        ):
            raise ValueError("LIVE_ENTRY_LIQUIDITY_CONTRACT_METADATA_CHANGED")
        check = snapshot.assess_quantity_v1(
            side=envelope.side.upper(), quantity=Decimal(envelope.quantity)
        )
        reasons = tuple(
            reason.replace("ZKP_PAPER_", "LIVE_ENTRY_LIQUIDITY_", 1)
            for reason in check["reason_codes"]
        )
        evidence.update(
            liquidity={**check, "reason_codes": list(reasons)},
            mark_event_unix=liquidity.mark_event_unix,
            observed_unix=liquidity.observed_unix,
            quote_asset=liquidity.quote_asset,
            source_hashes=snapshot.source_hashes,
        )
        if _read_original_entry(*args) != original or _load_profile(profile_path, lane) != (
            profile_id,
            policy,
        ):
            raise ValueError("LIVE_ENTRY_LIQUIDITY_BINDING_CHANGED_DURING_CAPTURE")
        if not liquidity.is_fresh_v1(clock()):
            raise ValueError("LIVE_ENTRY_LIQUIDITY_MARKET_EXPIRED")
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, ArithmeticError) as exc:
        return LiveEntryLiquidityPrecheckV1("BLOCKED", (str(exc),), evidence)
    return LiveEntryLiquidityPrecheckV1("BLOCKED" if reasons else "PASS", reasons, evidence)


def forward_live_entry_after_liquidity_check_v1(
    *,
    owner,
    reservation_id: str,
    envelope: FinalOrderEnvelopeV1,
    execution_plan_context: PortfolioExecutionPlanContextV1,
    transport_factory: Callable[[], FullCoreFreshPretradeGetTransportV1],
    prepermit_handoff: Callable[..., _T],
    profile_path: Path = DEFAULT_PROFILE_PATH,
    futures_financial_custody=None,
    clock: Callable[[], float] = time,
) -> _T:
    """Hand the unchanged plan to the existing owner at its pre-permit boundary.

    The intended invocation is immediately before POST Owner-GO consumption.
    Each invocation evaluates current public data and the current slot profile.
    """
    assessment = precheck_live_entry_liquidity_v1(
        owner=owner,
        reservation_id=reservation_id,
        envelope=envelope,
        execution_plan_context=execution_plan_context,
        transport_factory=transport_factory,
        profile_path=profile_path,
        futures_financial_custody=futures_financial_custody,
        clock=clock,
    )
    if assessment.status != "PASS":
        raise LiveEntryLiquidityBlockedV1(assessment)
    return prepermit_handoff(
        envelope=envelope,
        portfolio_budget_owner=owner,
        portfolio_reservation_id=reservation_id,
        execution_plan_context=execution_plan_context,
    )
