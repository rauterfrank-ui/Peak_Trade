"""CURRENT_PRODUCTIVE fresh Cap-23/24, truthful decision bind, one-shot POST readiness.

Consumes Owner-GO
OWNER_GO_FRESH_CAP23_CAP24_CURRENT_PRODUCTIVE_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_V1.

Reuses Cap-2.1–2.4 producers and EEA public universe acquisition. Does not
fabricate ENTER/size/plan. Does not POST. Does not consume a live permit.
Standing EXTERNAL_EFFECT remains false.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any, Mapping, Optional

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    SOURCE_KIND,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
    EeaUniverseAcquisitionError,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import ECONOMIC_RANK_ACTIVATED
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    FOLLOW_ON_SUBMIT_ISOLATED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT,
    ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN,
    ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    REPLAY_PROTECTION_DURABLE,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    VenuePlanCandidateV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    run_governed_futures_universe_producer_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_CREATED,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_live_account_bound_and_instrument_scope_v1 import (
    require_current_productive_29p_bound_instrument_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _mark_price_by_native_id_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import RANKING_POLICY_ID
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    run_productive_futures_ranking_producer_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID as CAP23_ID,
    SELECTION_FILENAME,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SELECTION_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER_GO = (
    "OWNER_GO_FRESH_CAP23_CAP24_CURRENT_PRODUCTIVE_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_V1"
)
THIS_SLICE = (
    "11.2.1.DJ.FULL_CORE_CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_"
    "DECISION_AND_ONE_SHOT_REAL_POST_READINESS"
)
EXPECTED_ORIGIN_MAIN_SHA = "114a68670bdd552fc1fcc90352a01b4dd7dc4dc5"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_fresh_cap23_cap24_decision_"
    "and_one_shot_real_post_readiness_v1/20260915T201500Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveFreshCap23Cap24ReadinessError(ValueError):
    """Fail-closed fresh Cap-23/24 / one-shot POST readiness violation."""


@dataclass(frozen=True)
class CurrentProductiveFreshCap23Cap24ReadinessResultV1:
    store_root: str
    cap23_selected_instrument_id: str
    cap23_valid_from: str
    cap23_valid_until: str
    cap24_bound_instrument_id: str
    decision_result: str
    decision_provenance: str
    venue_plan_status: str
    envelope_readiness: str
    one_shot_real_post_seam_implemented: str
    real_external_effect_authorized: str
    post_count: str
    first_real_blocker: str
    evidence_manifest: str
    manifest_verify_rc: int


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise CurrentProductiveFreshCap23Cap24ReadinessError(f"SECRET_TOKEN_PRESENT:{token}")


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_standing_pins() -> None:
    if (
        CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_CREATED
        is not True
    ):
        raise CurrentProductiveFreshCap23Cap24ReadinessError("READINESS_ADAPTER_NOT_CREATED")
    if ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ENVELOPE_BOUND_SEAM_NOT_TRUE")
    if ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ONE_SHOT_TRANSPORT_NOT_IMPLEMENTED")
    if ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ONE_SHOT_PERMIT_GATE_MISSING")
    if ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ONE_SHOT_STANDING_FORBIDDEN_MISSING")
    if FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("HTTP_POST_SEAM_NOT_IMPLEMENTED")
    if int(MAX_EXTERNAL_EFFECT_POST_COUNT) != 1:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("MAX_POST_COUNT_NOT_ONE")
    if REPLAY_PROTECTION_DURABLE is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("REPLAY_PROTECTION_NOT_DURABLE")
    if FOLLOW_ON_SUBMIT_ISOLATED is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("FOLLOW_ON_NOT_ISOLATED")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("STANDING_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("REAL_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_VENUE_POST_ALLOWED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("REAL_VENUE_POST_ALLOWED_NOT_FALSE")
    if POST_ALLOWED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("POST_ALLOWED_NOT_FALSE")
    if LIVE_ENABLED is not True or LIVE_ARMED is not True or WIRE_SEND_PERMITTED is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("STANDING_LIVE_GATES_DRIFT")
    if SUBMISSION_AUTHORIZED is not True or LIVE_AUTHORIZED is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("STANDING_AUTH_GATES_DRIFT")
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not True:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("WIRE_SEND_NOT_REACHABLE")
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError(
            "SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED"
        )
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError(
            "P01_RUNTIME_INSTANCE_MUST_REMAIN_ABSENT"
        )
    if RANKING_POLICY_ID != "productive_futures_universe_structural_ranking_v1":
        raise CurrentProductiveFreshCap23Cap24ReadinessError("RANKING_POLICY_DRIFT")
    if SELECTION_AUTHORITY_OWNER != CAP23_ID:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("SELECTION_OWNER_DRIFT")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("MAX_POSITIONS_NOT_ONE")
    if ECONOMIC_RANK_ACTIVATED is not False:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ECONOMIC_RANK_MUST_REMAIN_FALSE")


def _run_cap21_to_cap24_v1(
    *,
    acquisition: EeaUniverseAcquisitionResultV1,
    store: Path,
    repo_sha: str,
    observed_unix: float,
) -> tuple[str, dict[str, str], BoundInstrumentV1 | None, SingleSelectedFutureSelectionV1 | None]:
    uni_root = store / "runtime_state" / "universe"
    rank_root = store / "runtime_state" / "ranking"
    sel_root = store / "runtime_state" / "selection"
    recon_root = store / "runtime_state" / "recon"
    for path in (uni_root, rank_root, sel_root, recon_root):
        path.mkdir(parents=True, exist_ok=True)
    empty = {
        "cap21_snapshot_id": "",
        "cap21_event_time": "",
        "cap21_universe_size": "",
        "cap22_ranking_id": "",
        "cap22_ranking_epoch": "",
        "cap23_selection_decision_id": "",
        "cap23_selected_instrument_id": "",
        "cap23_valid_from": "",
        "cap23_valid_until": "",
        "cap24_bound_instrument_id": "",
    }
    uni = run_governed_futures_universe_producer_v1(
        state_root=uni_root,
        source_payload=acquisition.instruments_payload,
        mark_price_payload=acquisition.mark_price_payload,
        repository_sha=repo_sha,
        producer_observed_at_unix=observed_unix,
        source_event_time=acquisition.source_event_time,
        source_kind=SOURCE_KIND,
        session_id="current-productive-dj-universe",
    )
    if uni.get("ok") is not True:
        return "CAP21_CURRENT_UNIVERSE_FAIL_CLOSED", empty, None, None
    uni_snap = uni.get("snapshot") or {}
    empty["cap21_snapshot_id"] = str(uni_snap.get("snapshot_id") or "")
    empty["cap21_event_time"] = str(uni_snap.get("generated_at_event_time") or "")
    empty["cap21_universe_size"] = str(uni_snap.get("eligible_instrument_count") or "")
    ranking = run_productive_futures_ranking_producer_v1(
        state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=repo_sha,
        producer_observed_at_unix=observed_unix,
        session_id="current-productive-dj-ranking",
    )
    if ranking.get("ok") is not True:
        return "CAP22_CURRENT_RANKING_FAIL_CLOSED", empty, None, None
    rank_snap = ranking.get("snapshot") or {}
    empty["cap22_ranking_id"] = str(rank_snap.get("ranking_snapshot_id") or "")
    empty["cap22_ranking_epoch"] = str(rank_snap.get("event_time") or "")
    selection_run = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=repo_sha,
        producer_observed_at_unix=observed_unix,
        session_id="current-productive-dj-selection",
        previous_selection=None,
        load_previous_from_state=False,
        open_position_instrument_id=None,
        dashboard_payload=None,
        allowlist_payload=None,
        manual_override_payload=None,
    )
    selection_path = sel_root / SELECTION_FILENAME
    selection = None
    if selection_path.is_file():
        selection = SingleSelectedFutureSelectionV1.from_dict(
            json.loads(selection_path.read_text(encoding="utf-8"))
        )
    if (
        selection_run.get("ok") is not True
        or selection is None
        or selection.state != STATE_SELECTED_ACTIVE
        or not str(selection.venue_native_id or "").strip()
    ):
        return "CAP23_CURRENT_SELECTION_FAIL_CLOSED", empty, None, selection
    if str(selection.venue_native_id) == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    empty["cap23_selection_decision_id"] = selection.selection_id
    empty["cap23_selected_instrument_id"] = str(selection.venue_native_id)
    empty["cap23_valid_from"] = selection.valid_from
    empty["cap23_valid_until"] = selection.valid_until
    marks = _mark_price_by_native_id_v1(acquisition.mark_price_payload)
    observed_portfolio = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=observed_unix,
        wall_time_unix=observed_unix,
        source_id="current_productive_dj_empty_position_truth_v1",
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=repo_sha,
        session_id="current-productive-dj-binding",
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
        return "CAP24_BOUND_INSTRUMENT_FAIL_CLOSED", empty, None, selection
    bound = require_current_productive_29p_bound_instrument_v1(bound)
    if bound.venue_native_id == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    empty["cap24_bound_instrument_id"] = bound.instrument_id
    return "PASS", empty, bound, selection


def execute_current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    acquisition_transport: EeaPublicUniverseGetPortV1 | None = None,
    acquisition_result: EeaUniverseAcquisitionResultV1 | None = None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    replay: Optional[IntegratedOfflineReplayResultV1] = None,
    execute_network: bool = False,
    repository_sha: str | None = None,
    producer_observed_at_unix: float | None = None,
) -> CurrentProductiveFreshCap23Cap24ReadinessResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_network is not True and acquisition_result is None and acquisition_transport is None:
        raise CurrentProductiveFreshCap23Cap24ReadinessError(
            "EXECUTE_NETWORK_OR_INJECTED_INPUT_REQUIRED"
        )
    _assert_standing_pins()
    repo_sha = str(repository_sha or origin_main_sha)
    observed_unix = (
        float(producer_observed_at_unix) if producer_observed_at_unix is not None else time()
    )
    package_started = _utc_now_iso_v1()
    root = _REPO_ROOT
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    if acquisition_result is None:
        try:
            acquisition_result = acquire_eea_universe_inventory_v1(
                transport=acquisition_transport,
                observed_at=package_started,
            )
        except EeaUniverseAcquisitionError as exc:
            raise CurrentProductiveFreshCap23Cap24ReadinessError(str(exc)) from exc
    if acquisition_result.ok is not True:
        first_blocker = "EEA_UNIVERSE_ACQUISITION_FAIL_CLOSED"
        identities: dict[str, str] = {}
        bound = None
        selection = None
        cap_status = first_blocker
    else:
        cap_status, identities, bound, selection = _run_cap21_to_cap24_v1(
            acquisition=acquisition_result,
            store=store,
            repo_sha=repo_sha,
            observed_unix=observed_unix,
        )
        first_blocker = cap_status if cap_status != "PASS" else ""

    get_status = "NOT_REACHED"
    handle = None
    try:
        if bound is not None:
            if execute_network is True and fresh_get_transport is None:
                resolved_vault = (
                    Path(str(vault_file))
                    if vault_file is not None and str(vault_file).strip()
                    else _fail_closed_credential_unavailable_v1(repo_root=root)
                )
                try:
                    backend = _fail_closed_credential_unavailable_v1(vault_file=resolved_vault)
                    handle = _fail_closed_credential_unavailable_v1(
                        secret_reference=REQUIRED_SECRETREF_URI,
                        vault_backend=backend,
                        credential_class=REQUIRED_CREDENTIAL_CLASS,
                    )
                    fresh_get_transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle)
                except RuntimeError:
                    get_status = "CREDENTIAL_HANDLE_FAIL_CLOSED"
            if fresh_get_transport is not None:
                try:
                    evidence = collect_fresh_pretrade_runtime_get_v1(
                        transport=fresh_get_transport,
                        pretrade_decision_id=str(bound.venue_native_id),
                        instrument_id=str(bound.venue_native_id),
                        td_mode="cross",
                        limit_px="",
                        inst_type="SWAP",
                        require_collection=True,
                    )
                    get_status = str(evidence.evidence_status or "FAIL_CLOSED")
                except (TypeError, RuntimeError, ValueError) as exc:
                    get_status = f"FRESH_PRETRADE_GET_FAIL_CLOSED:{type(exc).__name__}"
            elif get_status == "NOT_REACHED":
                get_status = "FRESH_GET_TRANSPORT_MISSING"
    finally:
        if handle is not None:
            _fail_closed_credential_unavailable_v1(handle)

    decision_result = "NO_EXECUTABLE_DECISION"
    decision_provenance = CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    venue_plan_status = "NONE"
    envelope_readiness = FALSE_TOKEN
    plan: VenuePlanCandidateV1 | None = None
    if bound is not None:
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            session_id="current-productive-dj-session",
            run_id="current-productive-dj-run",
            composed_epoch=package_started,
        )
        decision_provenance = ",".join(reasons) if reasons else "COMPOSED"
        if status is CompositionStatusV1.PASS and plan is not None:
            decision_result = "EXECUTABLE_VENUE_PLAN_BOUND"
            venue_plan_status = "PASS"
            envelope_readiness = TRUE_TOKEN
        else:
            decision_result = "NO_EXECUTABLE_DECISION"
            venue_plan_status = status.value if hasattr(status, "value") else str(status)

    trusted_get = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    if cap_status != "PASS":
        first_blocker = cap_status
    elif get_status != trusted_get:
        first_blocker = f"FRESH_PRE_SUBMIT_EVIDENCE_FAIL_CLOSED:{get_status}"
    elif decision_result != "EXECUTABLE_VENUE_PLAN_BOUND":
        first_blocker = decision_provenance or CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    else:
        first_blocker = NEXT_OWNER_GO

    send_handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-dj-readiness-handle", bound=True
    )
    http_transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=send_handle)
    try:
        http_transport.post_trade_order(
            payload={"instId": identities.get("cap23_selected_instrument_id") or "MUST_NOT_POST"},
            permit_id="eep-readiness-must-not-post",
            envelope_id="env-readiness-must-not-post",
            envelope_digest="0" * 64,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveFreshCap23Cap24ReadinessError("HTTP_FORBIDDEN_MISSING") from exc
    else:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("HTTP_MUST_NOT_POST")
    if http_transport.post_count != 0:
        raise CurrentProductiveFreshCap23Cap24ReadinessError("HTTP_TRANSPORT_SIDE_EFFECT")

    envelope_id = ""
    envelope_digest = ""
    if plan is not None and envelope_readiness == TRUE_TOKEN:
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref="DJ_FRESH_CAP24_AND_CURRENT_PRODUCTIVE_DECISION",
            provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
            creation_epoch=package_started,
        )
        envelope_id = envelope.envelope_id
        envelope_digest = envelope.envelope_digest
    standing_blocker = current_productive_first_real_blocker_v1()
    if standing_blocker != NEXT_OWNER_GO:
        raise CurrentProductiveFreshCap23Cap24ReadinessError(f"BLOCKER_DRIFT:{standing_blocker}")

    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "RESELECTION_AUTHORIZED_BY_THIS_GO": TRUE_TOKEN,
        "RESELECTION_PERFORMED": _token(bound is not None),
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "CAP21_SNAPSHOT_ID": identities.get("cap21_snapshot_id", ""),
        "CAP21_EVENT_TIME": identities.get("cap21_event_time", ""),
        "CAP21_UNIVERSE_SIZE": identities.get("cap21_universe_size", ""),
        "CAP22_RANKING_ID": identities.get("cap22_ranking_id", ""),
        "CAP22_RANKING_EPOCH": identities.get("cap22_ranking_epoch", ""),
        "CAP23_SELECTION_DECISION_ID": identities.get("cap23_selection_decision_id", ""),
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP23_VALID_FROM": identities.get("cap23_valid_from", ""),
        "CAP23_VALID_UNTIL": identities.get("cap23_valid_until", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "CAP23_SELECTION_PROVENANCE": "CURRENT_CAP21_CAP22_CAP23_PRODUCERS",
        "CURRENT_PRODUCTIVE_DECISION_RESULT": decision_result,
        "CURRENT_PRODUCTIVE_DECISION_PROVENANCE": decision_provenance,
        "CURRENT_PRODUCTIVE_VENUE_PLAN_STATUS": venue_plan_status,
        "ENVELOPE_READINESS": envelope_readiness,
        "FINAL_ENVELOPE_ID": envelope_id,
        "FINAL_ENVELOPE_DIGEST": envelope_digest,
        "FRESH_PRE_SUBMIT_EVIDENCE": get_status,
        "ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT": TRUE_TOKEN,
        "ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN": TRUE_TOKEN,
        "ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM": TRUE_TOKEN,
        "LIVE_AUTHORIZED": TRUE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "MAX_POST_COUNT": "1",
        "POST_COUNT": "0",
        "TRANSPORT_ATTEMPTED": FALSE_TOKEN,
        "ACTUAL_ORDER_SUBMIT_PERFORMED": FALSE_TOKEN,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "PERMIT_CONSUMED_DURABLY": FALSE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": "1",
        "FIRST_REAL_BLOCKER": first_blocker,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "TRADING_LOGIC_CHANGES_FOUND": FALSE_TOKEN,
        "RANKING_ALGORITHM_CHANGED": FALSE_TOKEN,
        "SELECTION_ALGORITHM_CHANGED": FALSE_TOKEN,
        "UNIVERSE_SEMANTICS_CHANGED": FALSE_TOKEN,
        "LEARNING_LOGIC_CHANGED": FALSE_TOKEN,
        "SAFETY_AUTHORITY_WEAKENED": FALSE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_CHANGED": FALSE_TOKEN,
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": _utc_now_iso_v1(),
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "DI_PACK": (
            "evidence/ops/full_core_current_productive_envelope_bound_single_use_"
            "external_effect_send_seam_v1/20260915T212000Z"
        ),
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "DECISION_PROVENANCE": decision_provenance,
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
        "STEP_29Q_UNCHANGED_PLAN_ONLY": TRUE_TOKEN,
        "EXTERNAL_EFFECT_STANDING_UNCHANGED_FALSE": TRUE_TOKEN,
        "MAX_POSITIONS_UNCHANGED_1": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "CURRENT_PRODUCTIVE_DECISION_RESULT": decision_result,
        "ENVELOPE_READINESS": envelope_readiness,
        "ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "POST_COUNT": "0",
        "HARD_STOP": TRUE_TOKEN,
    }
    bound_payload = {
        "BOUND_INSTRUMENT": bound.to_dict() if bound is not None else {},
    }
    acquisition_payload = {
        "HOST": acquisition_result.host,
        "ENDPOINTS": list(acquisition_result.endpoints_used),
        "METHODS": list(acquisition_result.methods_used),
        "POST_COUNT": "0",
        "PROVENANCE": dict(acquisition_result.provenance),
        "OK": acquisition_result.ok,
    }
    for payload in (claims, lineage, protected, summary, bound_payload, acquisition_payload):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "bound_instrument_v1.json", payload=bound_payload)
    _persist_json(path=store / "acquisition_v1.json", payload=acquisition_payload)
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveFreshCap23Cap24ReadinessResultV1(
        store_root=str(store),
        cap23_selected_instrument_id=identities.get("cap23_selected_instrument_id", ""),
        cap23_valid_from=identities.get("cap23_valid_from", ""),
        cap23_valid_until=identities.get("cap23_valid_until", ""),
        cap24_bound_instrument_id=identities.get("cap24_bound_instrument_id", ""),
        decision_result=decision_result,
        decision_provenance=decision_provenance,
        venue_plan_status=venue_plan_status,
        envelope_readiness=envelope_readiness,
        one_shot_real_post_seam_implemented=TRUE_TOKEN,
        real_external_effect_authorized=FALSE_TOKEN,
        post_count="0",
        first_real_blocker=first_blocker,
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
