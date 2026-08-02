"""Smoke-session contract builder and digest for Phase 9.2 preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    CONFIG_SCHEMA_VERSION,
    EEA_PUBLIC_MD_HOST,
    EVIDENCE_DIRNAME,
    EVIDENCE_SUBDIR,
    REQUIRED_SESSION_METRICS,
    SMOKE_BACKOFF_INITIAL_SECONDS,
    SMOKE_BACKOFF_MAX_SECONDS,
    SMOKE_BACKOFF_MULTIPLIER,
    SMOKE_CONFIRMATION_SESSION_ID,
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_DURATION_SECONDS,
    SMOKE_HEARTBEAT_LOSS_SECONDS,
    SMOKE_HEARTBEAT_SECONDS,
    SMOKE_MAX_GAP_SECONDS,
    SMOKE_MAX_REQUESTS_PER_SESSION,
    SMOKE_MINIMUM_INTERVAL_SECONDS,
    SMOKE_PER_REQUEST_MAX_RETRIES,
    SMOKE_POLL_INTERVAL_SECONDS,
    SMOKE_RECONNECT_ATTEMPT_LIMIT,
    SMOKE_RECONNECT_TIME_LIMIT_SECONDS,
    SMOKE_RETRY_AFTER_MAX_SECONDS,
    SMOKE_RUNTIME_SESSION_ID,
    SMOKE_SESSION_HTTP_429_BUDGET,
    SMOKE_SESSION_ID,
    SMOKE_STALENESS_BUDGET_SECONDS,
    repo_root_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.models_v1 import SmokeSessionContractV1
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    compute_config_digest_v1,
    load_activation_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    SCHEMA_VERSION as ACTIVATION_SCHEMA_VERSION,
)


class SmokeContractError(RuntimeError):
    """Fail-closed smoke contract error."""


def _sha256_canonical(payload: Mapping[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_smoke_session_contract_v1(
    *,
    repository_sha: str,
    repo_root: Path | None = None,
) -> SmokeSessionContractV1:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    activation = load_activation_config_v1(
        config_path=root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    if not bool(activation.full_canonical_stateful_runtime_active):
        raise SmokeContractError("activation_not_active")
    if not bool(activation.simulated_execution_active):
        raise SmokeContractError("simulated_execution_not_active")

    persistence_root = f"var/runtime/phase_9_2/{SMOKE_SESSION_ID}/{repository_sha[:12]}"
    evidence_root = f"docs/evidence/{EVIDENCE_DIRNAME}/sessions/{SMOKE_SESSION_ID}"
    verifier = (
        "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1"
    )

    provisional: dict[str, Any] = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "session_id": SMOKE_SESSION_ID,
        "session_ladder_step": "SMOKE_SESSION",
        "purpose": (
            "Short public-MD no-order smoke proving EEA allowlist, pacing, "
            "staleness, stable session identity, restart-safe state and evidence "
            "binding under Cap 7.2 activated stateful simulated runtime."
        ),
        "repository_sha": repository_sha,
        "activation_config_version": ACTIVATION_SCHEMA_VERSION,
        "activation_config_digest": activation.config_digest,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "eea_public_md_host": EEA_PUBLIC_MD_HOST,
        "runtime_session_id": SMOKE_RUNTIME_SESSION_ID,
        "confirmation_session_id": SMOKE_CONFIRMATION_SESSION_ID,
        "persistence_root": persistence_root,
        "evidence_root": evidence_root,
        "verifier": verifier,
        "duration_seconds": SMOKE_DURATION_SECONDS,
        "poll_interval_seconds": SMOKE_POLL_INTERVAL_SECONDS,
        "heartbeat_seconds": SMOKE_HEARTBEAT_SECONDS,
        "heartbeat_loss_seconds": SMOKE_HEARTBEAT_LOSS_SECONDS,
        "staleness_budget_seconds": SMOKE_STALENESS_BUDGET_SECONDS,
        "max_gap_seconds": SMOKE_MAX_GAP_SECONDS,
        "consecutive_stale_budget": SMOKE_CONSECUTIVE_STALE_BUDGET,
        "reconnect_attempt_limit": SMOKE_RECONNECT_ATTEMPT_LIMIT,
        "reconnect_time_limit_seconds": SMOKE_RECONNECT_TIME_LIMIT_SECONDS,
        "per_request_max_retries": SMOKE_PER_REQUEST_MAX_RETRIES,
        "session_http_429_budget": SMOKE_SESSION_HTTP_429_BUDGET,
        "backoff_initial_seconds": SMOKE_BACKOFF_INITIAL_SECONDS,
        "backoff_multiplier": SMOKE_BACKOFF_MULTIPLIER,
        "backoff_max_seconds": SMOKE_BACKOFF_MAX_SECONDS,
        "retry_after_max_seconds": SMOKE_RETRY_AFTER_MAX_SECONDS,
        "minimum_interval_seconds": SMOKE_MINIMUM_INTERVAL_SECONDS,
        "max_requests_per_session": SMOKE_MAX_REQUESTS_PER_SESSION,
        "abort_conditions": [
            "RECONNECT_BUDGET_EXCEEDED",
            "HTTP_429_BUDGET_EXCEEDED",
            "STALE_DATA",
            "HEARTBEAT_LOSS",
            "PRIVATE_ENDPOINT_ATTEMPT",
            "AUTH_HEADER_DETECTED",
            "CREDENTIAL_ENV_PRESENT",
            "REPOSITORY_SHA_MISMATCH",
            "CONFIG_DIGEST_MISMATCH",
            "SESSION_IDENTITY_DRIFT",
            "DUPLICATE_CONFIRMATION_ADVANCE",
            "DUPLICATE_FILL",
            "RECONCILIATION_FAILURE",
            "NETWORK_BOUNDARY_VIOLATION",
            "ZERO_INTERVAL_BURST_FORBIDDEN",
        ],
        "restart_recovery_behavior": [
            "LOAD_PERSISTED_CONFIRMATION_AND_DYNAMIC_SCOPE",
            "RECONCILE_BEFORE_ALPHA",
            "REJECT_DUPLICATE_OBSERVATION_ADVANCE",
            "IDEMPOTENT_EVIDENCE_CURSOR_RECOVERY",
            "NO_DUPLICATE_SIMULATED_FILL",
        ],
        "allowed_side_effects": [
            "PUBLIC_MD_GET_EEA_ALLOWLISTED",
            "INTERNAL_SIMULATED_EXECUTION",
            "LOCAL_PERSISTENCE_UNDER_SESSION_ROOT",
            "LOCAL_EVIDENCE_UNDER_SESSION_ROOT",
        ],
        "forbidden_side_effects": [
            "LIVE_ORDERS",
            "TESTNET_ORDERS",
            "PAPER_EXCHANGE_ORDERS",
            "EXCHANGE_CREDENTIAL_USE",
            "REAL_CAPITAL_MOVEMENT",
            "PRIVATE_ENDPOINT_ACCESS",
            "AUTH_HEADER_TRANSMISSION",
            "CORE_LOGIC_MUTATION",
            "AUTHORIZATION_ISSUANCE",
            "AUTHORIZATION_CONSUMPTION",
        ],
        "required_metrics": list(REQUIRED_SESSION_METRICS),
        "network_session_authorized": False,
        "authorization_issuance_authorized": False,
        "authorization_consumption_authorized": False,
        "runtime_start_authorized": False,
    }
    digest = _sha256_canonical(
        {k: v for k, v in provisional.items() if k != "smoke_contract_digest"}
    )
    return SmokeSessionContractV1(
        schema_version=str(provisional["schema_version"]),
        capability_id=str(provisional["capability_id"]),
        session_id=str(provisional["session_id"]),
        session_ladder_step=str(provisional["session_ladder_step"]),
        purpose=str(provisional["purpose"]),
        repository_sha=str(provisional["repository_sha"]),
        activation_config_version=str(provisional["activation_config_version"]),
        activation_config_digest=str(provisional["activation_config_digest"]),
        smoke_contract_digest=digest,
        canonical_instrument_id=str(provisional["canonical_instrument_id"]),
        eea_public_md_host=str(provisional["eea_public_md_host"]),
        runtime_session_id=str(provisional["runtime_session_id"]),
        confirmation_session_id=str(provisional["confirmation_session_id"]),
        persistence_root=str(provisional["persistence_root"]),
        evidence_root=str(provisional["evidence_root"]),
        verifier=str(provisional["verifier"]),
        duration_seconds=int(provisional["duration_seconds"]),
        poll_interval_seconds=float(provisional["poll_interval_seconds"]),
        heartbeat_seconds=float(provisional["heartbeat_seconds"]),
        heartbeat_loss_seconds=float(provisional["heartbeat_loss_seconds"]),
        staleness_budget_seconds=float(provisional["staleness_budget_seconds"]),
        max_gap_seconds=float(provisional["max_gap_seconds"]),
        consecutive_stale_budget=int(provisional["consecutive_stale_budget"]),
        reconnect_attempt_limit=int(provisional["reconnect_attempt_limit"]),
        reconnect_time_limit_seconds=int(provisional["reconnect_time_limit_seconds"]),
        per_request_max_retries=int(provisional["per_request_max_retries"]),
        session_http_429_budget=int(provisional["session_http_429_budget"]),
        backoff_initial_seconds=float(provisional["backoff_initial_seconds"]),
        backoff_multiplier=float(provisional["backoff_multiplier"]),
        backoff_max_seconds=float(provisional["backoff_max_seconds"]),
        retry_after_max_seconds=float(provisional["retry_after_max_seconds"]),
        minimum_interval_seconds=float(provisional["minimum_interval_seconds"]),
        max_requests_per_session=int(provisional["max_requests_per_session"]),
        abort_conditions=tuple(provisional["abort_conditions"]),
        restart_recovery_behavior=tuple(provisional["restart_recovery_behavior"]),
        allowed_side_effects=tuple(provisional["allowed_side_effects"]),
        forbidden_side_effects=tuple(provisional["forbidden_side_effects"]),
        required_metrics=tuple(provisional["required_metrics"]),
        network_session_authorized=bool(provisional["network_session_authorized"]),
        authorization_issuance_authorized=bool(provisional["authorization_issuance_authorized"]),
        authorization_consumption_authorized=bool(
            provisional["authorization_consumption_authorized"]
        ),
        runtime_start_authorized=bool(provisional["runtime_start_authorized"]),
    )


def validate_smoke_session_contract_v1(contract: SmokeSessionContractV1) -> list[str]:
    gaps: list[str] = []
    if float(contract.poll_interval_seconds) <= 0:
        gaps.append("ZERO_INTERVAL_POLL")
    if float(contract.minimum_interval_seconds) <= 0:
        gaps.append("ZERO_INTERVAL_MINIMUM")
    if float(contract.minimum_interval_seconds) > float(contract.poll_interval_seconds):
        gaps.append("MINIMUM_INTERVAL_GT_POLL")
    if int(contract.duration_seconds) <= 0:
        gaps.append("NON_POSITIVE_DURATION")
    if int(contract.reconnect_attempt_limit) < 1:
        gaps.append("UNBOUNDED_OR_EMPTY_RECONNECT")
    if int(contract.per_request_max_retries) < 0:
        gaps.append("NEGATIVE_RETRY")
    if int(contract.session_http_429_budget) < 1:
        gaps.append("UNBOUNDED_OR_EMPTY_429_BUDGET")
    if float(contract.backoff_initial_seconds) <= 0:
        gaps.append("UNBOUNDED_BACKOFF_INITIAL")
    if float(contract.staleness_budget_seconds) <= 0:
        gaps.append("MISSING_STALENESS_BUDGET")
    if contract.eea_public_md_host != EEA_PUBLIC_MD_HOST:
        gaps.append("HOST_NOT_EEA")
    if contract.canonical_instrument_id != CANONICAL_INSTRUMENT_ID:
        gaps.append("INSTRUMENT_NOT_CANONICAL")
    if contract.network_session_authorized:
        gaps.append("NETWORK_SESSION_PREAUTHORIZED")
    if contract.authorization_issuance_authorized:
        gaps.append("AUTH_ISSUANCE_PREAUTHORIZED")
    if contract.authorization_consumption_authorized:
        gaps.append("AUTH_CONSUMPTION_PREAUTHORIZED")
    if contract.runtime_start_authorized:
        gaps.append("RUNTIME_START_PREAUTHORIZED")
    if set(REQUIRED_SESSION_METRICS) - set(contract.required_metrics):
        gaps.append("REQUIRED_METRICS_INCOMPLETE")
    material = contract.to_dict()
    declared = str(material.pop("smoke_contract_digest"))
    recomputed = _sha256_canonical(material)
    if declared != recomputed:
        gaps.append("SMOKE_CONTRACT_DIGEST_MISMATCH")
    return gaps


def load_smoke_session_contract_from_config_v1(
    *,
    repo_root: Path | None = None,
    expected_repository_sha: str | None = None,
) -> SmokeSessionContractV1:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    path = root / CONFIG_RELATIVE_PATH
    if not path.is_file():
        raise SmokeContractError(f"missing_smoke_contract_config:{path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if str(raw.get("schema_version")) != CONFIG_SCHEMA_VERSION:
        raise SmokeContractError(f"config_version_mismatch:{raw.get('schema_version')}")
    if (
        expected_repository_sha is not None
        and str(raw.get("repository_sha")) != expected_repository_sha
    ):
        raise SmokeContractError("repository_sha_mismatch")
    for key in (
        "abort_conditions",
        "restart_recovery_behavior",
        "allowed_side_effects",
        "forbidden_side_effects",
        "required_metrics",
    ):
        if key in raw and isinstance(raw[key], list):
            raw[key] = tuple(raw[key])
    contract = SmokeSessionContractV1(**raw)
    gaps = validate_smoke_session_contract_v1(contract)
    if gaps:
        raise SmokeContractError(",".join(gaps))
    # Bind activation digest truth.
    activation = load_activation_config_v1(
        config_path=root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    if contract.activation_config_digest != activation.config_digest:
        raise SmokeContractError("activation_config_digest_mismatch")
    _ = compute_config_digest_v1
    return contract
