"""Bounded productive Treasury read-only venue observation capture."""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import (
    observation_without_secrets_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    open_pl_tf_002_productive_read_only_get_session_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.chain_v1 import (
    execute_treasury_productive_reconciliation_chain_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    ALLOWED_WP_OWNER_GOS,
    MAX_NETWORK_REQUEST_COUNT,
    SESSION_OWNER_GO,
    TREASURY_OBSERVATION_INSTRUMENT_ID,
    WP_ID,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.funding_get_v1 import (
    observe_funding_balance_via_productive_transport_v1,
    resolve_account_identity_uid_from_config_get_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.pre_network_gate_v1 import (
    build_treasury_productive_pre_network_gate_proof_v1,
    merge_session_gate_facts_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.runtime_integrity_v1 import (
    TreasuryProductiveBranchTipIntegrityBackendV1,
    assert_treasury_productive_branch_tip_integrity_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.separation_matrix_v1 import (
    build_treasury_separation_matrix_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _observation_identity_v1(*, origin_main_sha: str, funding_body_sha256: str) -> str:
    material = f"{WP_ID}:{origin_main_sha[:12]}:{funding_body_sha256}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def execute_treasury_productive_read_only_venue_observation_v1(
    *,
    wp_owner_go: str,
    session_owner_go: str,
    origin_main_sha: str,
    execute_network: bool,
    integrity_backend: object | None = None,
    os_native_backend: object | None = None,
) -> dict[str, Any]:
    if str(wp_owner_go or "").strip() not in ALLOWED_WP_OWNER_GOS:
        raise TreasuryProductiveReadOnlyVenueObservationError("WP_OWNER_GO_NOT_AUTHORIZED")
    effective_integrity = integrity_backend
    bound_sha = str(origin_main_sha or "").strip().lower()
    if execute_network is True and effective_integrity is None:
        bound_sha = assert_treasury_productive_branch_tip_integrity_v1(
            declared_origin_main_sha=bound_sha,
            repo_root=_REPO_ROOT,
        )
        effective_integrity = TreasuryProductiveBranchTipIntegrityBackendV1(
            repo_root=_REPO_ROOT,
            declared_sha=bound_sha,
        )
    gate = build_treasury_productive_pre_network_gate_proof_v1(
        wp_owner_go=wp_owner_go,
        session_owner_go=session_owner_go,
        origin_main_sha=bound_sha if execute_network is True else origin_main_sha,
        integrity_backend=effective_integrity,
    )
    if execute_network is not True:
        sep = build_treasury_separation_matrix_v1(
            network_read_only_used=False,
            secret_material_persisted=False,
            secret_material_logged=False,
        )
        return {
            "disposition": "PRE_NETWORK_GATE_ONLY",
            "WP_ID": WP_ID,
            "pre_network_gate": gate,
            "NETWORK_READ_ONLY_USED": False,
            "NETWORK_REQUESTS_PERFORMED": 0,
            **sep,
        }

    decision_id = f"treasury-ro-obs-{str(origin_main_sha or '')[:12]}"
    with open_pl_tf_002_productive_read_only_get_session_v1(
        owner_go=session_owner_go,
        origin_main_sha=bound_sha,
        acquire_credential=True,
        backend=os_native_backend,
        integrity_backend=effective_integrity,  # type: ignore[arg-type]
    ) as session:
        gate = merge_session_gate_facts_v1(
            gate,
            credential_acquired=session.credential_acquired is True,
            k1_handle_bound=bool(session.k1_handle_id),
        )
        if gate.get("K1_ACQUISITION") != "PASS":
            raise TreasuryProductiveReadOnlyVenueObservationError("K1_ACQUISITION_FAIL_CLOSED")

        transport = session.transport
        if not isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1):
            raise TreasuryProductiveReadOnlyVenueObservationError("TRANSPORT_TYPE_MISMATCH")
        if transport.max_request_count < MAX_NETWORK_REQUEST_COUNT:
            raise TreasuryProductiveReadOnlyVenueObservationError(
                "TRANSPORT_MAX_REQUEST_BUDGET_TOO_LOW"
            )

        account_uid = resolve_account_identity_uid_from_config_get_v1(
            transport=transport,
            pretrade_decision_id=decision_id,
        )
        funding_obs, funding_get = observe_funding_balance_via_productive_transport_v1(
            transport=transport,
            pretrade_decision_id=decision_id,
        )
        network_count = int(transport.request_count)
        if network_count < 1:
            raise TreasuryProductiveReadOnlyVenueObservationError("NETWORK_REQUEST_COUNT_ZERO")
        if network_count > MAX_NETWORK_REQUEST_COUNT:
            raise TreasuryProductiveReadOnlyVenueObservationError("NETWORK_REQUEST_COUNT_EXCEEDED")
        if "POST" in {m.upper() for m in transport.methods_used}:
            raise TreasuryProductiveReadOnlyVenueObservationError("POST_METHOD_DETECTED")

        evidence_id = _observation_identity_v1(
            origin_main_sha=origin_main_sha,
            funding_body_sha256=str(funding_obs.body_sha256),
        )
        context = TreasuryCapitalDepositObservationContextV1(
            evidence_id=evidence_id,
            account_identity=f"okx-eea-uid:{account_uid}",
            instrument_id=TREASURY_OBSERVATION_INSTRUMENT_ID,
            deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
            deposit_history_confirms_increase=False,
            internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
            external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
            prior_reconciled_capital_raw="",
            cached_trading_capital_raw="",
            balance_freshness_override="",
        )
        treasury_observation = build_treasury_venue_observation_from_funding_balance_v1(
            funding_obs,
            context,
        )
        chain = execute_treasury_productive_reconciliation_chain_v1(treasury_observation)
        funding_public = observation_without_secrets_v1(funding_obs)
        observed_ms = int(time.time() * 1000)

        sep = build_treasury_separation_matrix_v1(
            network_read_only_used=True,
            secret_material_persisted=False,
            secret_material_logged=False,
        )
        return {
            "disposition": "PRODUCTIVE_OBSERVATION_COMPLETE",
            "WP_ID": WP_ID,
            "pre_network_gate": gate,
            "NETWORK_READ_ONLY_USED": True,
            "NETWORK_REQUESTS_PERFORMED": network_count,
            "NETWORK_METHODS_USED": sorted({m.upper() for m in transport.methods_used}),
            "OBSERVATION_IDENTITY": evidence_id,
            "OBSERVATION_PROVENANCE": {
                "transport_class": funding_get.transport_class,
                "venue_live_contact": funding_get.venue_live_contact,
                "data_safety_source_kind": funding_get.data_safety_source_kind,
                "endpoint": funding_get.endpoint,
                "body_sha256": funding_obs.body_sha256,
                "account_identity_scope": "okx-eea-uid",
            },
            "OBSERVATION_FRESHNESS": {
                "balance_freshness": treasury_observation.balance_freshness,
                "observed_at_utc": treasury_observation.observed_at_utc,
                "local_observed_unix_ms": observed_ms,
            },
            "OBSERVATION_AMBIGUITY": {
                "deposit_history_freshness": treasury_observation.deposit_history_freshness,
                "reconciliation_class": chain.get("RECONCILIATION_STATUS"),
            },
            "funding_observation_public": funding_public,
            "treasury_venue_observation": asdict(treasury_observation),
            "reconciliation_chain": chain,
            **sep,
        }
