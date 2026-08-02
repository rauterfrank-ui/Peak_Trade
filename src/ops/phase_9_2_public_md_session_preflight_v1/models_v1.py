"""Typed models for Phase 9.2 public-MD smoke preflight."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class SmokeSessionContractV1:
    schema_version: str
    capability_id: str
    session_id: str
    session_ladder_step: str
    purpose: str
    repository_sha: str
    activation_config_version: str
    activation_config_digest: str
    smoke_contract_digest: str
    canonical_instrument_id: str
    eea_public_md_host: str
    runtime_session_id: str
    confirmation_session_id: str
    persistence_root: str
    evidence_root: str
    verifier: str
    duration_seconds: int
    poll_interval_seconds: float
    heartbeat_seconds: float
    heartbeat_loss_seconds: float
    staleness_budget_seconds: float
    max_gap_seconds: float
    consecutive_stale_budget: int
    reconnect_attempt_limit: int
    reconnect_time_limit_seconds: int
    per_request_max_retries: int
    session_http_429_budget: int
    backoff_initial_seconds: float
    backoff_multiplier: float
    backoff_max_seconds: float
    retry_after_max_seconds: float
    minimum_interval_seconds: float
    max_requests_per_session: int
    abort_conditions: tuple[str, ...]
    restart_recovery_behavior: tuple[str, ...]
    allowed_side_effects: tuple[str, ...]
    forbidden_side_effects: tuple[str, ...]
    required_metrics: tuple[str, ...]
    network_session_authorized: bool
    authorization_issuance_authorized: bool
    authorization_consumption_authorized: bool
    runtime_start_authorized: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreflightClaimsV1:
    PHASE_9_1_CLOSED: bool = False
    STRATEGY_REGISTRY_CLOSED: bool = False
    PHASE_9_2_PREREQUISITES_PROVEN: bool = False
    FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE: bool = False
    SIMULATED_EXECUTION_ACTIVE: bool = False
    RECONCILIATION_BEFORE_ALPHA: bool = False
    PUBLIC_MD_ONLY_BOUNDARY_PROVEN: bool = False
    GET_ONLY_PROVEN: bool = False
    PRIVATE_ENDPOINT_REACHABLE: bool = True
    AUTH_HEADER_PRESENT: bool = True
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = True
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = True
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = True
    PAPER_EXCHANGE_EXECUTION_REACHABLE: bool = True
    LIVE_PATH_REACHABLE: bool = True
    TESTNET_PATH_REACHABLE: bool = True
    NO_ZERO_INTERVAL_REQUEST_BURST: bool = False
    EXPLICIT_PACING_BUDGET: bool = False
    BOUNDED_RETRY: bool = False
    BOUNDED_BACKOFF: bool = False
    HTTP_429_CLASSIFIED: bool = False
    STALENESS_GATE_PROVEN: bool = False
    CONFIRMATION_SESSION_ID_STABLE: bool = False
    RUNTIME_SESSION_ID_STABLE: bool = False
    DECISION_STATE_PERSISTENCE_PROVEN: bool = False
    RESTART_SEMANTICS_PROVEN: bool = False
    NO_DUPLICATE_CONFIRMATION_ADVANCE: bool = False
    NO_DUPLICATE_FILL: bool = False
    EVIDENCE_RECOVERY_IDEMPOTENT: bool = False
    SESSION_LADDER_DEFINED: bool = False
    SMOKE_SESSION_CONTRACT_CREATED: bool = False
    SESSION_PREREGISTRATION_READY: bool = False
    AUTHORIZATION_PATH_IDENTIFIED: bool = False
    CONFIRM_TOKEN_CANONICAL_PATH_IDENTIFIED: bool = False
    CONFIRM_TOKEN_PLAINTEXT_EXPOSED: bool = True
    CORE_LOGIC_CHANGED: bool = True
    GOLDEN_VECTOR_PARITY_PASS: bool = False
    CALL_ORDER_PARITY_PROVEN: bool = False
    INPUT_OUTPUT_PARITY_PROVEN: bool = False
    STATE_TRANSITION_PARITY_PROVEN: bool = False
    DECISION_REASON_PARITY_PROVEN: bool = False
    RISK_PARITY_PROVEN: bool = False
    SAFETY_PARITY_PROVEN: bool = False
    EXIT_PRECEDENCE_PARITY_PROVEN: bool = False
    PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreflightEvidenceV1:
    ok: bool
    capability_id: str
    task_id: str
    repository_sha: str
    smoke_contract_digest: str
    activation_config_digest: str
    claims: Mapping[str, Any]
    gaps: list[str] = field(default_factory=list)
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "task_id": self.task_id,
            "repository_sha": self.repository_sha,
            "smoke_contract_digest": self.smoke_contract_digest,
            "activation_config_digest": self.activation_config_digest,
            "claims": dict(self.claims),
            "gaps": list(self.gaps),
            "evidence_digest": self.evidence_digest,
        }
