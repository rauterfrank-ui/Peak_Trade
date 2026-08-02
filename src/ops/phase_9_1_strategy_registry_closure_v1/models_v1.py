"""Models for Phase 9.1 strategy registry closure."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class StrategyAuthorityClassV1(str, Enum):
    CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
    AUTHORIZED_COMPOSITION_INPUT = "AUTHORIZED_COMPOSITION_INPUT"
    RESEARCH_INFORMATION = "RESEARCH_INFORMATION"
    EXPERIMENT_ONLY = "EXPERIMENT_ONLY"
    LEGACY_DEAUTHORIZED = "LEGACY_DEAUTHORIZED"


class EnabledStateV1(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    AUTHORITY_ONLY = "AUTHORITY_ONLY"


@dataclass(frozen=True)
class StrategyRegistryMatrixRowV1:
    STRATEGY_ID: str
    IMPLEMENTATION_SYMBOL: str
    SOURCE_PATH: str
    CURRENT_CLASSIFICATION: str
    TARGET_CLASSIFICATION: str
    PRODUCTIVE_CALLERS: Tuple[str, ...]
    RUNTIME_REACHABLE: bool
    CONFIG_OWNER: str
    CONFIG_VERSION: str
    CONFIG_DIGEST: str
    ENABLED_STATE: str
    FAIL_CLOSED_BEHAVIOR: str
    COMPOSITION_INPUT_CONTRACT: str
    DIRECT_INTENT_REACHABLE: bool
    DIRECT_FILL_REACHABLE: bool
    DIRECT_ORDER_REACHABLE: bool
    MASTER_V2_BYPASS_REACHABLE: bool
    DOUBLE_PLAY_BYPASS_REACHABLE: bool
    RISK_BYPASS_REACHABLE: bool
    SAFETY_BYPASS_REACHABLE: bool
    RESTART_SEMANTICS: str
    AUTHORITY_OWNER: str
    DEAUTHORIZATION_REASON: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["PRODUCTIVE_CALLERS"] = list(self.PRODUCTIVE_CALLERS)
        return d


@dataclass(frozen=True)
class ClosureClaimsV1:
    STRATEGY_REGISTRY_CLOSED: bool
    EVERY_STRATEGY_CLASSIFIED: bool
    PRODUCTIVE_CALLERS_ENUMERATED: bool
    DIRECT_ORDER_CAPABILITY_ABSENT: bool
    DIRECT_FILL_CAPABILITY_ABSENT: bool
    DIRECT_INTENT_BYPASS_ABSENT: bool
    MASTER_V2_BYPASS_ABSENT: bool
    DOUBLE_PLAY_BYPASS_ABSENT: bool
    RISK_BYPASS_ABSENT: bool
    SAFETY_BYPASS_ABSENT: bool
    COMPOSITION_CONTRACT_EXPLICIT: bool
    DISABLED_STRATEGIES_FAIL_CLOSED: bool
    UNKNOWN_STRATEGIES_FAIL_CLOSED: bool
    CONFIG_VERSION_MISMATCH_REJECTED: bool
    CONFIG_DIGEST_MISMATCH_REJECTED: bool
    RESTART_DETERMINISTIC: bool
    SILENT_AUTHORITY_PROMOTION: bool
    LEGACY_PARALLEL_AUTHORITY_ABSENT: bool
    DASHBOARD_AUTHORITY_EFFECT: str
    CORE_LOGIC_CHANGE: bool
    LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED: bool
    GOLDEN_VECTOR_PARITY_PASS: bool
    CALL_ORDER_PARITY_PROVEN: bool
    INPUT_OUTPUT_PARITY_PROVEN: bool
    STATE_TRANSITION_PARITY_PROVEN: bool
    DECISION_REASON_PARITY_PROVEN: bool
    RISK_PARITY_PROVEN: bool
    SAFETY_PARITY_PROVEN: bool
    EXIT_PRECEDENCE_PARITY_PROVEN: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def ok(self) -> bool:
        d = self.to_dict()
        bool_ok = all(
            bool(d[k]) is True
            for k in d
            if k
            not in {
                "SILENT_AUTHORITY_PROMOTION",
                "CORE_LOGIC_CHANGE",
                "DASHBOARD_AUTHORITY_EFFECT",
            }
        )
        return (
            bool_ok
            and d["SILENT_AUTHORITY_PROMOTION"] is False
            and d["CORE_LOGIC_CHANGE"] is False
            and d["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
        )


@dataclass(frozen=True)
class ClosureEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    strategy_count: int
    classification_counts: Dict[str, int]
    matrix_digest: str
    config_digest: str
    registry_snapshot_digest: str
    claims: ClosureClaimsV1
    failure_injections: Dict[str, Any]
    parity: Dict[str, Any]
    bypass_proof: Dict[str, Any]
    restart_proof: Dict[str, Any]
    call_graph: Tuple[str, ...]
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "strategy_count": self.strategy_count,
            "classification_counts": dict(self.classification_counts),
            "matrix_digest": self.matrix_digest,
            "config_digest": self.config_digest,
            "registry_snapshot_digest": self.registry_snapshot_digest,
            "claims": self.claims.to_dict(),
            "failure_injections": dict(self.failure_injections),
            "parity": dict(self.parity),
            "bypass_proof": dict(self.bypass_proof),
            "restart_proof": dict(self.restart_proof),
            "call_graph": list(self.call_graph),
            "notes": list(self.notes),
        }
