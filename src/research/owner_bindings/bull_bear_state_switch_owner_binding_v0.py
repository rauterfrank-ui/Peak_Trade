from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Tuple


AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "NONE"

SURFACE_ID: Final[str] = "bull_bear_state_switch_owner"
SURFACE_NAME: Final[str] = "Bull/Bear State Switch Owner Surface"
BINDING_VERSION: Final[str] = "v0"

CANONICAL_OWNER: Final[str] = "src/trading/master_v2"
REUSE_DECISION: Final[str] = "REUSE_WITH_NARROW_ADAPTER"
IMPLEMENTATION_MODE: Final[str] = "OWNER_BINDING_ONLY_NO_RUNTIME_REWIRE"

NO_RUNTIME_REWIRE: Final[bool] = True
NO_RUNTIME_EVIDENCE: Final[bool] = True
NO_ORDER_AUTHORITY: Final[bool] = True
NO_CREDENTIAL_AUTHORITY: Final[bool] = True
NO_SCHEDULER_AUTHORITY: Final[bool] = True
NO_PROMOTION_AUTHORITY: Final[bool] = True
NO_ECONOMIC_PASS_AUTHORITY: Final[bool] = True

REQUIRED_REUSE_PATHS: Final[Tuple[str, ...]] = ("src/trading/master_v2",)

BLOCKED_EFFECTS: Final[Tuple[str, ...]] = (
    "runtime_rewire",
    "runtime_evidence",
    "shadow_evidence",
    "paper_evidence",
    "testnet_evidence",
    "canary_evidence",
    "live_evidence",
    "order_submission",
    "credential_use",
    "arming",
    "scheduler_start",
    "promotion_pass",
    "economic_pass_claim",
)

REQUIRED_PARITY_ASSERTIONS: Final[Tuple[str, ...]] = (
    "BULL_BEAR_STATE_SWITCH_OWNER_BOUND",
    "NO_PARALLEL_STATE_SWITCH_OWNER",
    "NO_RUNTIME_AUTHORITY_FROM_OWNER_BINDING",
    "NO_ORDER_AUTHORITY_FROM_OWNER_BINDING",
    "BACKTEST_PARITY_NOT_CLAIMED_BY_THIS_SLICE",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE_FALSE",
)


@dataclass(frozen=True)
class BullBearStateSwitchOwnerBindingV0:
    surface_id: str
    surface_name: str
    binding_version: str
    canonical_owner: str
    reuse_decision: str
    implementation_mode: str
    required_reuse_paths: Tuple[str, ...]
    blocked_effects: Tuple[str, ...]
    required_parity_assertions: Tuple[str, ...]
    authority_effect: str
    runtime_effect: str

    def as_contract(self) -> Mapping[str, object]:
        return {
            "surface_id": self.surface_id,
            "surface_name": self.surface_name,
            "binding_version": self.binding_version,
            "canonical_owner": self.canonical_owner,
            "reuse_decision": self.reuse_decision,
            "implementation_mode": self.implementation_mode,
            "required_reuse_paths": list(self.required_reuse_paths),
            "blocked_effects": list(self.blocked_effects),
            "required_parity_assertions": list(self.required_parity_assertions),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "no_runtime_rewire": NO_RUNTIME_REWIRE,
            "no_runtime_evidence": NO_RUNTIME_EVIDENCE,
            "no_order_authority": NO_ORDER_AUTHORITY,
            "no_credential_authority": NO_CREDENTIAL_AUTHORITY,
            "no_scheduler_authority": NO_SCHEDULER_AUTHORITY,
            "no_promotion_authority": NO_PROMOTION_AUTHORITY,
            "no_economic_pass_authority": NO_ECONOMIC_PASS_AUTHORITY,
        }


def build_bull_bear_state_switch_owner_binding_v0() -> BullBearStateSwitchOwnerBindingV0:
    return BullBearStateSwitchOwnerBindingV0(
        surface_id=SURFACE_ID,
        surface_name=SURFACE_NAME,
        binding_version=BINDING_VERSION,
        canonical_owner=CANONICAL_OWNER,
        reuse_decision=REUSE_DECISION,
        implementation_mode=IMPLEMENTATION_MODE,
        required_reuse_paths=REQUIRED_REUSE_PATHS,
        blocked_effects=BLOCKED_EFFECTS,
        required_parity_assertions=REQUIRED_PARITY_ASSERTIONS,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )
