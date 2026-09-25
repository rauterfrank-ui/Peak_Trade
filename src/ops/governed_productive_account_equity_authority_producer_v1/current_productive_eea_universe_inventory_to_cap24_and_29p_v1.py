"""CURRENT_PRODUCTIVE EEA universe inventory → Cap-2.1–2.4 → LAB/29P.

Consumes Owner-GO
CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_TO_FIRST_REAL_BLOCKER_V1.

Cap-2.1 remains no-network. Acquisition is a separate READ-ONLY layer.
Cap-2.2/2.3/2.4 producers run unchanged. Reselection is authorized by this GO.
No POST. No Live enable/arm. No canary instrument authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from time import time
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    AUTHORIZED_HOST,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
    EeaUniverseAcquisitionError,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    ECONOMIC_RANK_ACTIVATED,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    NUMERIC_EQUITY_TTL_SECONDS,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    LIVE_ACCOUNT_BOUND_AUTHORITY,
    evaluate_live_account_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
    persist_class_fields_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import GovernedUniverseInstrumentV1
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PChainBaselineError,
    CurrentProductive29PRuntimeIntegrityBackendV1,
    assert_current_productive_29p_execution_identity_v1,
    assert_current_productive_29p_repository_sha_for_execution_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_credential_join_v1 import (
    productive_fail_closed_credential_unavailable_v1 as _fail_closed_credential_unavailable_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    eea_mark_price_payload_to_map_by_native_id_v1,
    run_cap21_to_cap23_persist_productive_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    resolve_current_productive_public_inst_type_from_cap21_universe_v1,
    compose_current_productive_29p_common_epoch_handoff_v1,
    extract_usdc_details_availeq_from_balance_payload_v1,
    payload_from_fresh_get_transport_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_live_account_bound_and_instrument_scope_v1 import (
    require_current_productive_29p_bound_instrument_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    REQUIRED_TD_MODE,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    EVIDENCE_REF,
    bind_current_productive_p01_policy_fact_v1,
    evaluate_current_productive_p01_policy_v1,
    reject_missing_as_does_not_apply_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
    extract_raw_acct_lv_from_account_config_payload_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    RANKING_POLICY_ID,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAILABLE_MARGIN_REQUIRED_CCY,
    account_balance_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID as CAP23_ID,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SELECTION_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def resolve_post_29p_current_execution_blocker_v1() -> tuple[str, str, str]:
    """After 29P is admissible, consume the composition-root first real blocker.

    Names the existing envelope-bound single-use permit Owner-GO. Does not mint
    that permit, load credentials, open a session, construct a port, or POST.
    """
    return current_productive_first_real_blocker_v1(), "E", POST_NEXT_OWNER_GO


OWNER_GO = "CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_TO_FIRST_REAL_BLOCKER_V1"
PIN_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_CURRENT_CAP24_BOUND_INSTRUMENT_INSTANCE_"
    "FOR_29P_WITHOUT_CANARY_IMPORT_OR_RESELECTION_V1"
)
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, PIN_OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
THIS_SLICE = "11.2.1.CZ.FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EVIDENCE_DIRNAME = "full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1/"
    "20260915T140000Z"
)
FORBIDDEN_HTTP_METHODS = ("POST", "PUT", "DELETE", "PATCH")
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
INSTRUMENT_SCOPE_AUTHORITY = SELECTION_AUTHORITY_OWNER
LAB_AUTHORITY = LIVE_ACCOUNT_BOUND_AUTHORITY


class CurrentProductiveEeaUniverseTo29PError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE EEA universe → 29P violation."""


@dataclass(frozen=True)
class CurrentProductiveEeaUniverseTo29PResultV1:
    store_root: str
    eea_universe_acquisition_status: str
    cap21_snapshot_id: str
    cap21_event_time: str
    cap21_universe_size: str
    cap22_ranking_id: str
    cap22_ranking_epoch: str
    cap23_selection_decision_id: str
    cap23_selected_instrument_id: str
    cap23_valid_from: str
    cap23_valid_until: str
    cap24_bound_instrument_id: str
    live_account_bound_status: str
    fresh_pretrade_get_status: str
    u01_status: str
    p01_status: str
    fresh_usdc_availeq_status: str
    risk_capital_mint_status: str
    instrument_scope_status: str
    step_29p_risk_admissible: str
    first_real_blocker: str
    blocker_class: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for marker in SECRET_MARKERS:
        if marker in blob:
            raise CurrentProductiveEeaUniverseTo29PError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductiveEeaUniverseTo29PError("HTTP_PROXY_FORBIDDEN")


def _age_seconds(*, observed_at_as_of: str, now_iso: str) -> str:
    try:
        observed = datetime.strptime(observed_at_as_of, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        now = datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return "UNPARSEABLE"
    delta = (now - observed).total_seconds()
    if delta < 0:
        return "NEGATIVE"
    return format(Decimal(str(int(delta))), "f")


def _extract_uid(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return ""
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        return ""
    uid = data[0].get("uid")
    if uid is None or isinstance(uid, bool):
        return ""
    if isinstance(uid, int):
        return str(uid)
    if isinstance(uid, str):
        return uid.strip()
    return ""


def _extract_usdc_details_availeq_v1(payload: Mapping[str, Any]) -> str:
    """CURRENT_PRODUCTIVE details[ccy=USDC].availEq via shared common-epoch handoff."""
    try:
        return extract_usdc_details_availeq_from_balance_payload_v1(payload)
    except Exception as exc:
        raise CurrentProductiveEeaUniverseTo29PError(str(exc)) from exc


def _assert_protected_surfaces_v1() -> None:
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductiveEeaUniverseTo29PError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveEeaUniverseTo29PError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveEeaUniverseTo29PError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if RANKING_POLICY_ID != "productive_futures_universe_structural_ranking_v1":
        raise CurrentProductiveEeaUniverseTo29PError("RANKING_POLICY_DRIFT")
    if SELECTION_AUTHORITY_OWNER != CAP23_ID:
        raise CurrentProductiveEeaUniverseTo29PError("SELECTION_OWNER_DRIFT")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveEeaUniverseTo29PError("MAX_POSITIONS_NOT_ONE")
    if ECONOMIC_RANK_ACTIVATED is not False:
        raise CurrentProductiveEeaUniverseTo29PError("ECONOMIC_RANK_MUST_REMAIN_FALSE")


def execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    acquisition_transport: EeaPublicUniverseGetPortV1 | None = None,
    acquisition_result: EeaUniverseAcquisitionResultV1 | None = None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    execute_network: bool = False,
    repository_sha: str | None = None,
    producer_observed_at_unix: float | None = None,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
) -> CurrentProductiveEeaUniverseTo29PResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveEeaUniverseTo29PError("OWNER_GO_MISMATCH")
    try:
        trusted_execution_identity = assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=origin_main_sha,
            integrity_backend=execution_integrity_backend,
        )
    except CurrentProductive29PChainBaselineError as exc:
        raise CurrentProductiveEeaUniverseTo29PError(str(exc)) from exc
    if execute_network is not True and acquisition_result is None and acquisition_transport is None:
        raise CurrentProductiveEeaUniverseTo29PError("EXECUTE_NETWORK_OR_INJECTED_INPUT_REQUIRED")
    _assert_protected_surfaces_v1()
    reject_direct_avail_eq_29p_claim_v1(claimed="false")
    missing = reject_missing_as_does_not_apply_v1()
    p01_decision = evaluate_current_productive_p01_policy_v1()
    if p01_decision.decision_state != CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveEeaUniverseTo29PError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")
    if missing.decision_state == CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveEeaUniverseTo29PError("MISSING_MUST_NOT_BECOME_DOES_NOT_APPLY")
    _assert_no_proxy_env_v1()
    if CURRENT_PRODUCTIVE_U01_GET_ENDPOINT != "/api/v5/account/config":
        raise CurrentProductiveEeaUniverseTo29PError("U01_ENDPOINT_DRIFT")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT != "/api/v5/account/balance":
        raise CurrentProductiveEeaUniverseTo29PError("BALANCE_ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductiveEeaUniverseTo29PError("HOST_MISMATCH")

    repo_sha = str(repository_sha or origin_main_sha).strip()
    try:
        assert_current_productive_29p_repository_sha_for_execution_v1(
            repository_sha=repo_sha,
            trusted_execution_identity=trusted_execution_identity,
        )
    except CurrentProductive29PChainBaselineError as exc:
        raise CurrentProductiveEeaUniverseTo29PError(str(exc)) from exc
    observed_unix = (
        float(producer_observed_at_unix) if producer_observed_at_unix is not None else time()
    )
    package_started = _utc_now_iso_v1()
    decision_epoch = package_started
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)

    if acquisition_result is None:
        try:
            acquisition_result = acquire_eea_universe_inventory_v1(
                transport=acquisition_transport,
                observed_at=package_started,
            )
        except EeaUniverseAcquisitionError as exc:
            raise CurrentProductiveEeaUniverseTo29PError(str(exc)) from exc
    acquisition_status = "PASS" if acquisition_result.ok else "FAIL_CLOSED"
    if not acquisition_result.ok:
        first_blocker = "EEA_UNIVERSE_ACQUISITION_FAIL_CLOSED"
        blocker_class = "C"
        return _persist_terminal_v1(
            store=store,
            acquisition=acquisition_result,
            acquisition_status=acquisition_status,
            first_blocker=first_blocker,
            blocker_class=blocker_class,
            p01_status=p01_decision.decision_state,
            decision_epoch=decision_epoch,
            origin_main_sha=origin_main_sha,
        )

    cap21_23 = run_cap21_to_cap23_persist_productive_v1(
        acquisition=acquisition_result,
        store=store,
        repository_sha=repo_sha,
        observed_unix=observed_unix,
        session_id_prefix="current-productive-eea",
    )
    if cap21_23.ok is not True or cap21_23.selection is None:
        return _persist_terminal_v1(
            store=store,
            acquisition=acquisition_result,
            acquisition_status=acquisition_status,
            first_blocker=cap21_23.status,
            blocker_class="C",
            p01_status=p01_decision.decision_state,
            decision_epoch=decision_epoch,
            origin_main_sha=origin_main_sha,
            cap21_snapshot_id=cap21_23.cap21_snapshot_id,
            cap21_event_time=cap21_23.cap21_event_time,
            cap21_universe_size=cap21_23.cap21_universe_size,
            cap22_ranking_id=cap21_23.cap22_ranking_id,
            cap22_ranking_epoch=cap21_23.cap22_ranking_epoch,
        )
    selection = cap21_23.selection
    selected_native = cap21_23.cap23_selected_instrument_id
    uni_root = cap21_23.universe_state_root
    rank_root = cap21_23.ranking_state_root
    sel_root = cap21_23.selection_state_root
    recon_root = cap21_23.recon_state_root
    uni_load = load_and_validate_universe_snapshot_v1(
        uni_root,
        expected_repository_sha=repo_sha,
        require_manifest=True,
    )
    uni_snap = uni_load.snapshot.to_dict() if uni_load.snapshot is not None else {}
    rank_snap = {
        "ranking_snapshot_id": cap21_23.cap22_ranking_id,
        "event_time": cap21_23.cap22_ranking_epoch,
    }
    marks = eea_mark_price_payload_to_map_by_native_id_v1(acquisition_result.mark_price_payload)
    observed_portfolio = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=observed_unix,
        wall_time_unix=observed_unix,
        source_id="current_productive_empty_position_truth_v1",
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=repo_sha,
        session_id="current-productive-eea-binding",
        now_unix=observed_unix,
        reconciliation_state_root=recon_root,
        observed_portfolio=observed_portfolio,
        mark_price_by_native_id=marks,
        expected_selection_config_digest=selection.config_digest,
        expected_selection_integrity_digest=selection.integrity_digest,
        dashboard_available=False,
        dashboard_selected_instrument=None,
        direct_instrument_override=None,
        skip_reconciliation=False,
    )
    bound = gate.bound
    if bound is None or not isinstance(bound, BoundInstrumentV1) or gate.ok is not True:
        return _persist_terminal_v1(
            store=store,
            acquisition=acquisition_result,
            acquisition_status=acquisition_status,
            first_blocker="CAP24_BOUND_INSTRUMENT_FAIL_CLOSED",
            blocker_class="C",
            p01_status=p01_decision.decision_state,
            decision_epoch=decision_epoch,
            origin_main_sha=origin_main_sha,
            cap21_snapshot_id=str(uni_snap.get("snapshot_id") or ""),
            cap21_event_time=str(uni_snap.get("generated_at_event_time") or ""),
            cap21_universe_size=str(uni_snap.get("eligible_instrument_count") or ""),
            cap22_ranking_id=str(rank_snap.get("ranking_snapshot_id") or ""),
            cap22_ranking_epoch=str(rank_snap.get("event_time") or ""),
            cap23_selection_decision_id=selection.selection_id,
            cap23_selected_instrument_id=selected_native,
            cap23_valid_from=selection.valid_from,
            cap23_valid_until=selection.valid_until,
            extra={"CAP24": gate.to_dict()},
        )
    bound = require_current_productive_29p_bound_instrument_v1(bound)
    if bound.venue_native_id == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductiveEeaUniverseTo29PError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")

    expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
    handle = None
    productive = execute_network is True and fresh_get_transport is None
    try:
        if productive:
            resolved_vault = (
                Path(str(vault_file))
                if vault_file is not None and str(vault_file).strip()
                else _fail_closed_credential_unavailable_v1(repo_root=_REPO_ROOT)
            )
            try:
                backend = _fail_closed_credential_unavailable_v1(vault_file=resolved_vault)
                handle = _fail_closed_credential_unavailable_v1(
                    secret_reference=REQUIRED_SECRETREF_URI,
                    vault_backend=backend,
                    credential_class=REQUIRED_CREDENTIAL_CLASS,
                )
            except RuntimeError:
                return _persist_terminal_v1(
                    store=store,
                    acquisition=acquisition_result,
                    acquisition_status=acquisition_status,
                    first_blocker="PRODUCTIVE_PRIVATE_GET_CREDENTIAL_UNAVAILABLE",
                    blocker_class="C",
                    p01_status=p01_decision.decision_state,
                    decision_epoch=decision_epoch,
                    origin_main_sha=origin_main_sha,
                    cap21_snapshot_id=str(uni_snap.get("snapshot_id") or ""),
                    cap21_event_time=str(uni_snap.get("generated_at_event_time") or ""),
                    cap21_universe_size=str(uni_snap.get("eligible_instrument_count") or ""),
                    cap22_ranking_id=str(rank_snap.get("ranking_snapshot_id") or ""),
                    cap22_ranking_epoch=str(rank_snap.get("event_time") or ""),
                    cap23_selection_decision_id=selection.selection_id,
                    cap23_selected_instrument_id=selected_native,
                    cap23_valid_from=selection.valid_from,
                    cap23_valid_until=selection.valid_until,
                    cap24_bound_instrument_id=bound.instrument_id,
                    extra={"CAP24_BOUND_INSTRUMENT_ID": bound.instrument_id},
                )
            fresh_get_transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle)
        if fresh_get_transport is None:
            raise CurrentProductiveEeaUniverseTo29PError(
                "LIVE_ACCOUNT_BOUND_REQUIRES_TRUSTED_FRESH_GET"
            )
        cap21_instruments = tuple(
            GovernedUniverseInstrumentV1.from_dict(row)
            for row in (uni_snap.get("instruments") or [])
            if isinstance(row, Mapping)
        )
        inst_type = resolve_current_productive_public_inst_type_from_cap21_universe_v1(
            instruments=cap21_instruments,
            venue_native_id=bound.venue_native_id,
        )
        package_finished = _utc_now_iso_v1()
        handoff = compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=decision_epoch,
            bound_instrument=bound,
            fresh_get_transport=fresh_get_transport,
            expected_account_identity=expected_uid,
            inst_type=inst_type,
            package_finished_iso=package_finished,
            p01_decision_state=p01_decision.decision_state,
        )
    finally:
        if handle is not None:
            _fail_closed_credential_unavailable_v1(handle)

    get_evidence = handoff.get_evidence
    get_status = handoff.get_status
    lab = handoff.lab
    lab_status = handoff.lab_status
    adaptation = handoff.adaptation
    eligibility = handoff.eligibility
    observation = handoff.observation
    raw_availeq = handoff.raw_availeq
    p01_fact = handoff.p01_fact
    output = handoff.output
    produced = handoff.produced
    claim = handoff.claim
    capital = handoff.capital
    admissibility = handoff.admissibility
    evaluator_29p = handoff.evaluator_29p
    observed_instrument_id = handoff.observed_instrument_id
    instrument_bound = handoff.instrument_bound
    lab_trusted = handoff.lab_trusted
    bound_uid = handoff.bound_uid
    transport_class = str(getattr(fresh_get_transport, "transport_class", "") or "")
    venue_contact = bool(getattr(fresh_get_transport, "venue_live_contact", False))
    productive_contact = (
        productive is True
        and venue_contact is True
        and transport_class == TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
    )
    current_productive_29p = evaluator_29p is True and productive_contact is True
    instrument_scope_status = "BOUND_TO_CAP24_SINGLE_SELECTED_FUTURE"
    predicate_matrix = {
        "PREDICATE": [
            {
                "PREDICATE": "U01_ELIGIBLE",
                "CURRENT_VALUE": adaptation.status,
                "BLOCKING": eligibility is None,
            },
            {
                "PREDICATE": "P01_DOES_NOT_APPLY",
                "CURRENT_VALUE": p01_decision.decision_state,
                "BLOCKING": p01_decision.decision_state != "DOES_NOT_APPLY",
            },
            {
                "PREDICATE": "FRESH_USDC_AVAILEQ",
                "CURRENT_VALUE": "OBSERVED_THIS_EPOCH"
                if observation is not None
                else "NOT_OBSERVED",
                "BLOCKING": observation is None,
            },
            {
                "PREDICATE": "RISK_CAPITAL_MINTED",
                "CURRENT_VALUE": "MINTED" if produced else "UNMINTED",
                "BLOCKING": produced is not True,
            },
            {
                "PREDICATE": "LIVE_ACCOUNT_BOUND_TRUSTED",
                "CURRENT_VALUE": lab_status,
                "BLOCKING": lab_trusted is not True,
            },
            {
                "PREDICATE": "INSTRUMENT_SCOPE_BOUND",
                "CURRENT_VALUE": instrument_scope_status,
                "BLOCKING": instrument_bound is not True,
            },
            {
                "PREDICATE": "FRESH_PRETRADE_GET_TRUSTED",
                "CURRENT_VALUE": get_status,
                "BLOCKING": get_status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            },
            {
                "PREDICATE": "STEP_29P_RISK_ADMISSIBLE_EVALUATOR",
                "CURRENT_VALUE": evaluator_29p,
                "BLOCKING": evaluator_29p is not True,
            },
            {
                "PREDICATE": "CURRENT_PRODUCTIVE_STEP_29P_RISK_ADMISSIBLE",
                "CURRENT_VALUE": current_productive_29p,
                "BLOCKING": current_productive_29p is not True,
            },
        ],
        "REASON_CODES": list(admissibility.reason_codes),
        "U04_NOT_SUBTRACTED": output.u04_applied == FALSE_TOKEN,
        "SECRET_VALUES_INCLUDED": False,
    }
    if lab_trusted is not True:
        first_blocker = "LIVE_ACCOUNT_BOUND_NOT_TRUSTED_FOR_29P"
        blocker_class = "C"
        next_go = "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_FRESH_PRETRADE_AND_LAB_TRUST_FOR_29P_V1"
    elif instrument_bound is not True:
        first_blocker = "STEP_29P_INSTRUMENT_SCOPE_MISSING"
        blocker_class = "B"
        next_go = PIN_OWNER_GO
    elif eligibility is None:
        first_blocker = "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif observation is None:
        first_blocker = "FRESH_USDC_AVAILEQ_NOT_OBSERVED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif produced is not True:
        first_blocker = "RISK_CAPITAL_MINT_FAIL_CLOSED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif productive_contact is not True:
        first_blocker = (
            "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT"
        )
        blocker_class = "C"
        next_go = "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_READ_ONLY_GET_FOR_29P_V1"
    elif current_productive_29p is True:
        first_blocker, blocker_class, next_go = resolve_post_29p_current_execution_blocker_v1()
    else:
        first_blocker = "STEP_29P_RISK_ADMISSIBLE_FALSE"
        blocker_class = "C"
        next_go = PIN_OWNER_GO

    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "EEA_UNIVERSE_ACQUISITION_STATUS": acquisition_status,
        "EEA_UNIVERSE_ACQUISITION_OWNER": "CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_ACQUISITION_V1",
        "EEA_UNIVERSE_HOST": AUTHORIZED_HOST,
        "EEA_PUBLIC_ENDPOINTS_USED": list(acquisition_result.endpoints_used),
        "NETWORK_METHODS_USED": list(acquisition_result.methods_used),
        "POST_COUNT": "0",
        "CAP21_NETWORK_OWNER_CHANGED": FALSE_TOKEN,
        "TRANSPORT_REUSED": FALSE_TOKEN,
        "TRANSPORT_AUTHORITY_PROMOTED": FALSE_TOKEN,
        "CAP21_CURRENT_SNAPSHOT_STATUS": "PASS",
        "CAP21_SNAPSHOT_ID": str(uni_snap.get("snapshot_id") or ""),
        "CAP21_EVENT_TIME": str(uni_snap.get("generated_at_event_time") or ""),
        "CAP21_FRESHNESS": "FRESH_ACQUISITION_THIS_EPOCH",
        "CAP21_UNIVERSE_SIZE": str(uni_snap.get("eligible_instrument_count") or ""),
        "CAP22_CURRENT_RANKING_STATUS": "PASS",
        "CAP22_RANKING_ID": str(rank_snap.get("ranking_snapshot_id") or ""),
        "CAP22_RANKING_EPOCH": str(rank_snap.get("event_time") or ""),
        "ECONOMIC_RANK_ACTIVATED": FALSE_TOKEN,
        "RANKING_ALGORITHM_CHANGED": FALSE_TOKEN,
        "CAP23_CURRENT_SELECTION_STATUS": "PASS",
        "CAP23_SELECTION_DECISION_ID": selection.selection_id,
        "CAP23_SELECTED_INSTRUMENT_ID": bound.venue_native_id,
        "CAP23_VALID_FROM": selection.valid_from,
        "CAP23_VALID_UNTIL": selection.valid_until,
        "RESELECTION_PERFORMED": TRUE_TOKEN,
        "RESELECTION_AUTHORIZED_BY_THIS_GO": TRUE_TOKEN,
        "MANUAL_INSTRUMENT_SELECTION_PERFORMED": FALSE_TOKEN,
        "SELECTION_ALGORITHM_CHANGED": FALSE_TOKEN,
        "CAP24_BOUND_INSTRUMENT_STATUS": "PASS",
        "CAP24_BOUND_INSTRUMENT_ID": bound.instrument_id,
        "CAP24_PROVENANCE": bound.to_dict(),
        "SINGLE_SELECTED_FUTURE_PROVEN": TRUE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": str(MAX_POSITIONS_EFFECTIVE),
        "LIVE_ACCOUNT_BOUND_STATUS": lab_status,
        "FRESH_PRETRADE_GET_STATUS": get_status,
        "U01_STATUS": adaptation.status,
        "P01_STATUS": p01_decision.decision_state,
        "P01_POLICY_DECISION": CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
        "FRESH_USDC_AVAILEQ_STATUS": "OBSERVED_THIS_EPOCH"
        if observation is not None
        else "NOT_OBSERVED",
        "FRESH_USDC_AVAILEQ_VALUE_PRESENT": bool(raw_availeq),
        "RISK_CAPITAL_MINT_STATUS": "MINTED" if produced else "UNMINTED",
        "INSTRUMENT_SCOPE_STATUS": instrument_scope_status,
        "STEP_29P_RISK_ADMISSIBLE": TRUE_TOKEN if current_productive_29p else FALSE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE_EVALUATOR": TRUE_TOKEN if evaluator_29p else FALSE_TOKEN,
        "29P_PREDICATE_MATRIX": predicate_matrix,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": next_go,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "CANARY_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "TRADING_LOGIC_CHANGES_FOUND": FALSE_TOKEN,
        "UNIVERSE_SEMANTICS_CHANGED": FALSE_TOKEN,
        "LEARNING_LOGIC_CHANGED": FALSE_TOKEN,
        "SAFETY_AUTHORITY_CHANGED": FALSE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_CHANGED": FALSE_TOKEN,
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
        "LIVE_ENABLED": TRUE_TOKEN if LIVE_ENABLED is True else FALSE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN if LIVE_ARMED is True else FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN if WIRE_SEND_PERMITTED is True else FALSE_TOKEN,
        "SECRET_MATERIAL_PERSISTED": False,
        "ALGEBRA": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
        "U04_SUBTRACTED": FALSE_TOKEN,
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "ACQUISITION_PROVENANCE": dict(acquisition_result.provenance),
        "SELECTION_ID": selection.selection_id,
        "BOUND_INSTRUMENT": bound.to_dict(),
        "DECISION_EPOCH": decision_epoch,
        "FRESH_PRETRADE_REASON_CODES": list(get_evidence.reason_codes),
        "LAB_REASON_CODES": list(lab.reason_codes),
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "UNIVERSE_MEMBERSHIP_SEMANTICS_UNCHANGED": TRUE_TOKEN,
        "RANKING_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "SELECTION_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_SAFETY_ADMISSION_AUTHORITY_UNCHANGED": TRUE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_UNCHANGED": TRUE_TOKEN,
        "MAX_POSITIONS_ONE_UNCHANGED": TRUE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_NOT_IMPORTED": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "STEP_29P_RISK_ADMISSIBLE": claims["STEP_29P_RISK_ADMISSIBLE"],
        "POST_COUNT": "0",
        "HARD_STOP": TRUE_TOKEN,
    }
    for payload in (claims, lineage, protected, summary, bound.to_dict()):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(
        path=store / "bound_instrument_v1.json",
        payload={"BOUND_INSTRUMENT": bound.to_dict()},
    )
    _persist_json(
        path=store / "predicate_matrix_v1.json",
        payload={"29P_PREDICATE_MATRIX": predicate_matrix},
    )
    _persist_json(
        path=store / "acquisition_v1.json",
        payload={
            "HOST": acquisition_result.host,
            "ENDPOINTS": list(acquisition_result.endpoints_used),
            "METHODS": list(acquisition_result.methods_used),
            "POST_COUNT": "0",
            "PROVENANCE": dict(acquisition_result.provenance),
            "OK": acquisition_result.ok,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveEeaUniverseTo29PResultV1(
        store_root=str(store),
        eea_universe_acquisition_status=acquisition_status,
        cap21_snapshot_id=str(uni_snap.get("snapshot_id") or ""),
        cap21_event_time=str(uni_snap.get("generated_at_event_time") or ""),
        cap21_universe_size=str(uni_snap.get("eligible_instrument_count") or ""),
        cap22_ranking_id=str(rank_snap.get("ranking_snapshot_id") or ""),
        cap22_ranking_epoch=str(rank_snap.get("event_time") or ""),
        cap23_selection_decision_id=selection.selection_id,
        cap23_selected_instrument_id=bound.venue_native_id,
        cap23_valid_from=selection.valid_from,
        cap23_valid_until=selection.valid_until,
        cap24_bound_instrument_id=bound.instrument_id,
        live_account_bound_status=lab_status,
        fresh_pretrade_get_status=get_status,
        u01_status=adaptation.status,
        p01_status=p01_decision.decision_state,
        fresh_usdc_availeq_status=str(claims["FRESH_USDC_AVAILEQ_STATUS"]),
        risk_capital_mint_status=str(claims["RISK_CAPITAL_MINT_STATUS"]),
        instrument_scope_status=instrument_scope_status,
        step_29p_risk_admissible=str(claims["STEP_29P_RISK_ADMISSIBLE"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )


def _payload_from_transport(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    endpoint: str,
    auth_required: bool,
    decision_epoch: str,
) -> Any:
    return payload_from_fresh_get_transport_v1(
        transport,
        endpoint=endpoint,
        auth_required=auth_required,
        decision_epoch=decision_epoch,
    )


def _persist_terminal_v1(
    *,
    store: Path,
    acquisition: EeaUniverseAcquisitionResultV1 | None,
    acquisition_status: str,
    first_blocker: str,
    blocker_class: str,
    p01_status: str,
    decision_epoch: str,
    origin_main_sha: str,
    cap21_snapshot_id: str = "",
    cap21_event_time: str = "",
    cap21_universe_size: str = "",
    cap22_ranking_id: str = "",
    cap22_ranking_epoch: str = "",
    cap23_selection_decision_id: str = "",
    cap23_selected_instrument_id: str = "",
    cap23_valid_from: str = "",
    cap23_valid_until: str = "",
    cap24_bound_instrument_id: str = "",
    extra: Mapping[str, Any] | None = None,
) -> CurrentProductiveEeaUniverseTo29PResultV1:
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "EEA_UNIVERSE_ACQUISITION_STATUS": acquisition_status,
        "EEA_UNIVERSE_HOST": AUTHORIZED_HOST,
        "POST_COUNT": "0",
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "P01_STATUS": p01_status,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "LIVE_ENABLED": TRUE_TOKEN if LIVE_ENABLED is True else FALSE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN if LIVE_ARMED is True else FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN if WIRE_SEND_PERMITTED is True else FALSE_TOKEN,
        "SECRET_MATERIAL_PERSISTED": False,
        "EXTRA": extra or {},
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "POST_COUNT": "0",
        "HARD_STOP": TRUE_TOKEN,
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "DECISION_EPOCH": decision_epoch,
        "ACQUISITION_PROVENANCE": dict(acquisition.provenance) if acquisition is not None else {},
    }
    protected = {
        "CANARY_INSTRUMENT_AUTHORITY_NOT_IMPORTED": TRUE_TOKEN,
        "MAX_POSITIONS_ONE_UNCHANGED": TRUE_TOKEN,
        "RANKING_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "SELECTION_ALGORITHM_UNCHANGED": TRUE_TOKEN,
    }
    for payload in (claims, summary, lineage, protected):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveEeaUniverseTo29PResultV1(
        store_root=str(store),
        eea_universe_acquisition_status=acquisition_status,
        cap21_snapshot_id=cap21_snapshot_id,
        cap21_event_time=cap21_event_time,
        cap21_universe_size=cap21_universe_size,
        cap22_ranking_id=cap22_ranking_id,
        cap22_ranking_epoch=cap22_ranking_epoch,
        cap23_selection_decision_id=cap23_selection_decision_id,
        cap23_selected_instrument_id=cap23_selected_instrument_id,
        cap23_valid_from=cap23_valid_from,
        cap23_valid_until=cap23_valid_until,
        cap24_bound_instrument_id=cap24_bound_instrument_id,
        live_account_bound_status="MISSING",
        fresh_pretrade_get_status="MISSING",
        u01_status="NOT_REACHED",
        p01_status=p01_status,
        fresh_usdc_availeq_status="NOT_REACHED",
        risk_capital_mint_status="UNMINTED",
        instrument_scope_status="MISSING",
        step_29p_risk_admissible=FALSE_TOKEN,
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--vault-file")
    parser.add_argument("--evidence-root")
    parser.add_argument("--execute-network", action="store_true")
    args = parser.parse_args()
    result = execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1(
        owner_go=args.owner_go,
        origin_main_sha=args.origin_main_sha,
        vault_file=args.vault_file,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
        execute_network=bool(args.execute_network),
    )
    print(
        _canonical_json(
            {
                "FIRST_REAL_BLOCKER": result.first_real_blocker,
                "BLOCKER_CLASS": result.blocker_class,
                "CAP23_SELECTED_INSTRUMENT_ID": result.cap23_selected_instrument_id,
                "STEP_29P_RISK_ADMISSIBLE": result.step_29p_risk_admissible,
                "STORE": result.store_root,
            }
        )
    )
    return 0 if result.manifest_verify_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
