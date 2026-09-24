"""Terminal authorized campaign run orchestration owner for F1/M9 prospective selection.

Build-slice default: bind and verify only — no REAL public-MD read, no durable repo writes.
Hermetic isolated execution (tests): full terminal path through selection verdict in tmp_path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_PUBLIC_MD_HOST_V1,
    BOUND_VENUE_INSTRUMENT_ID,
)

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorization_consume_v1 import (
    AuthorizationConsumeError,
    atomic_consume_runtime_authorization_v1,
    verify_authorization_not_replay_source_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    EVIDENCE_SOURCE_FIXTURE,
    EVIDENCE_SOURCE_REAL,
    PREREGISTRATION_DIGEST,
    RESUME_STATE_ALREADY_COMPLETE,
    RESUME_STATE_FAIL_CLOSED,
    RESUME_STATE_RESUME_AUTHORIZED,
    SELECTION_POLICY_DIGEST,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.durable_paths_v1 import (
    resolve_f1_m9_prospective_campaign_durable_paths_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.evidence_sealing_v1 import (
    build_hermetic_real_class_evidence_bundle_v1,
    seal_manifest_sha256_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.evidence_writer_v1 import (
    write_campaign_artifact_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.exactly_once_v1 import (
    adjudicate_execution_resume_state_v1,
    derive_campaign_execution_identity_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_boundary_v1 import (
    CAMPAIGN_EXECUTED,
    EXCHANGE_PRIVATE_TRADING_EFFECT_OCCURRED,
    NEW_DECISION_MAKING_EVIDENCE_GENERATED,
    ORDER_EFFECT_OCCURRED,
    PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED,
    evaluate_f1_m9_prospective_campaign_execution_v1,
    F1M9ProspectiveCampaignExecutionPhaseV1,
    F1M9ProspectiveCampaignExecutionRequestV1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    AUTHORIZATION_REF_FILENAME,
    EXECUTION_STATE_FILENAME,
    ORCHESTRATION_OWNER_ID,
    ORCHESTRATION_SCHEMA_VERSION,
    STATUS_ALREADY_COMPLETE_REPLAY,
    STATUS_BUILD_SLICE_BOUND_ONLY,
    STATUS_ORCHESTRATION_DENIED,
    STATUS_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_md_supplier_v1 import (
    resolve_real_md_supplier_binding_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.replay_v1 import (
    CampaignReplayError,
    replay_sealed_campaign_evidence_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    F1M9ProspectiveCampaignRuntimeAuthorizationV1,
    resolve_runtime_authorization_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.session_work_units_v1 import (
    resolve_preregistered_session_work_units_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.completeness_v1 import (
    adjudicate_campaign_completeness_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    assert_decision_evidence_downstream_of_new_preregistration_v1,
)

PublicMdSessionFn = Callable[..., dict[str, Any]]


class HermeticEvidenceClass(str, Enum):
    REAL_CLASS = "REAL_CLASS"
    FIXTURE_CLASS = "FIXTURE_CLASS"


@dataclass(frozen=True, slots=True)
class F1M9AuthorizedCampaignRunOrchestrationRequestV1:
    runtime_authorization: Mapping[str, Any] | None
    evaluation_time_utc: datetime | None = None
    repo_root: Path | None = None
    hermetic_isolated_campaign_root: Path | None = None
    allow_hermetic_terminal_effects: bool = False
    hermetic_evidence_class: HermeticEvidenceClass = HermeticEvidenceClass.REAL_CLASS
    hermetic_force_incomplete: bool = False
    public_md_session_fn: PublicMdSessionFn | None = None


@dataclass(frozen=True, slots=True)
class F1M9AuthorizedCampaignRunOrchestrationResultV1:
    orchestration_status: str
    orchestration_owner_id: str
    reason_codes: tuple[str, ...]
    campaign_executed: bool
    public_market_data_external_read_occurred: bool
    real_evidence_written: bool
    productive_apply_occurred: bool
    terminal_selection: dict[str, Any] | None
    replay: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "orchestration_status": self.orchestration_status,
            "orchestration_owner_id": self.orchestration_owner_id,
            "reason_codes": list(self.reason_codes),
            "campaign_executed": self.campaign_executed,
            "public_market_data_external_read_occurred": (
                self.public_market_data_external_read_occurred
            ),
            "real_evidence_written": self.real_evidence_written,
            "productive_apply_occurred": self.productive_apply_occurred,
            "terminal_selection": self.terminal_selection,
            "replay": self.replay,
        }


def _denied(*reasons: str) -> F1M9AuthorizedCampaignRunOrchestrationResultV1:
    return F1M9AuthorizedCampaignRunOrchestrationResultV1(
        orchestration_status=STATUS_ORCHESTRATION_DENIED,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=reasons,
        campaign_executed=False,
        public_market_data_external_read_occurred=False,
        real_evidence_written=False,
        productive_apply_occurred=False,
        terminal_selection=None,
        replay=None,
    )


def _verify_supplier_binding_against_authorization_v1(
    auth: F1M9ProspectiveCampaignRuntimeAuthorizationV1,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    reasons: list[str] = []
    binding = resolve_real_md_supplier_binding_v1(repo_root=repo_root)
    if binding.get("missing_real_md_execution_dependency"):
        reasons.append("REAL_MD_SUPPLIER_UNRESOLVED")
    expected_host = str(BOUND_PUBLIC_MD_HOST_V1)
    authorized_host = str(auth.authorized_public_md_host or "")
    if authorized_host and authorized_host.rstrip("/") != expected_host.rstrip("/"):
        reasons.append("PUBLIC_MD_HOST_BINDING_MISMATCH")
    if auth.authorized_data_source != "REAL_PUBLIC_MARKET_DATA":
        reasons.append("AUTHORIZED_DATA_SOURCE_MISMATCH")
    if binding.get("order_endpoint_allowed") or binding.get("account_endpoint_allowed"):
        reasons.append("SUPPLIER_FORBIDS_PRIVATE_ENDPOINTS_VIOLATED")
    return tuple(reasons)


def _write_execution_state(
    path: Path,
    *,
    execution_identity: str,
    partial: bool,
    complete: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "execution_identity": execution_identity,
                "partial": partial,
                "complete": complete,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _load_sealed_bundle_from_root(campaign_root: Path) -> dict[str, Any] | None:
    completeness_path = campaign_root / "campaign_completeness.json"
    if not completeness_path.is_file():
        return None
    payload = json.loads(completeness_path.read_text(encoding="utf-8"))
    sealed = payload.get("sealed_evidence_bundle")
    if isinstance(sealed, dict):
        return sealed
    return None


def _run_hermetic_terminal_path_v1(
    *,
    repo_root: Path,
    campaign_root: Path,
    auth: F1M9ProspectiveCampaignRuntimeAuthorizationV1,
    evaluation_time_utc: datetime,
    request: F1M9AuthorizedCampaignRunOrchestrationRequestV1,
) -> F1M9AuthorizedCampaignRunOrchestrationResultV1:
    execution_identity = derive_campaign_execution_identity_v1(
        campaign_id=CAMPAIGN_ID,
        preregistration_digest=PREREGISTRATION_DIGEST,
        execution_idempotency_key=auth.execution_idempotency_key,
    )
    sealed_existing = _load_sealed_bundle_from_root(campaign_root)
    resume = adjudicate_execution_resume_state_v1(
        campaign_root=campaign_root,
        execution_identity=execution_identity,
        sealed_manifest=sealed_existing,
    )
    if resume["resume_state"] == RESUME_STATE_FAIL_CLOSED:
        return _denied(*tuple(resume.get("reason_codes") or ("RESUME_FAIL_CLOSED",)))

    if resume["resume_state"] == RESUME_STATE_ALREADY_COMPLETE:
        replay_reasons = verify_authorization_not_replay_source_v1(
            campaign_root=campaign_root,
            sealed_manifest=sealed_existing,
        )
        if replay_reasons:
            return _denied(*replay_reasons)
        if sealed_existing is None:
            return _denied("SEALED_BUNDLE_MISSING")
        try:
            replay = replay_sealed_campaign_evidence_v1(sealed_existing, repo_root=repo_root)
        except CampaignReplayError as exc:
            return _denied(str(exc))
        return F1M9AuthorizedCampaignRunOrchestrationResultV1(
            orchestration_status=STATUS_ALREADY_COMPLETE_REPLAY,
            orchestration_owner_id=ORCHESTRATION_OWNER_ID,
            reason_codes=("REPLAY_ONLY_NO_NEW_REAL_EVIDENCE",),
            campaign_executed=False,
            public_market_data_external_read_occurred=False,
            real_evidence_written=False,
            productive_apply_occurred=False,
            terminal_selection=replay.get("selection"),
            replay=replay,
        )

    if resume["resume_state"] != RESUME_STATE_RESUME_AUTHORIZED:
        return _denied("RESUME_STATE_UNKNOWN")

    if not auth.public_market_data_read_authorized or not auth.durable_evidence_write_authorized:
        return _denied(
            "REAL_PUBLIC_MD_READ_NOT_AUTHORIZED",
            "DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED",
        )

    consumed_at = evaluation_time_utc.isoformat().replace("+00:00", "Z")
    try:
        atomic_consume_runtime_authorization_v1(
            campaign_root=campaign_root,
            authorization_id=auth.authorization_id,
            authorization_digest=auth.authorization_digest,
            execution_identity=execution_identity,
            consumed_at_utc=consumed_at,
            allow_consume=True,
        )
    except AuthorizationConsumeError as exc:
        return _denied(str(exc))

    state_path = campaign_root / EXECUTION_STATE_FILENAME
    _write_execution_state(
        state_path,
        execution_identity=execution_identity,
        partial=True,
        complete=False,
    )

    work_units = resolve_preregistered_session_work_units_v1(repo_root=repo_root)
    evidence_class = (
        EVIDENCE_SOURCE_REAL
        if request.hermetic_evidence_class == HermeticEvidenceClass.REAL_CLASS
        else EVIDENCE_SOURCE_FIXTURE
    )
    md_read_simulated = False
    if request.public_md_session_fn is not None:
        for unit in work_units:
            request.public_md_session_fn(work_unit=unit, authorization=auth.to_dict())
        md_read_simulated = True

    timestamp = consumed_at
    sealed_bundle = build_hermetic_real_class_evidence_bundle_v1(
        work_units=work_units,
        decision_making_evidence_timestamp_utc=timestamp,
        execution_identity=execution_identity,
        evidence_source_class=evidence_class,
        force_incomplete=request.hermetic_force_incomplete,
    )
    leakage = assert_decision_evidence_downstream_of_new_preregistration_v1(
        sealed_bundle, repo_root=repo_root
    )
    if leakage.get("historical_evidence_decision_leakage"):
        return _denied("CONTAMINATION_LEAKAGE")

    completeness = adjudicate_campaign_completeness_v1(sealed_bundle, repo_root=repo_root)
    if not completeness.campaign_selection_eligible:
        return F1M9AuthorizedCampaignRunOrchestrationResultV1(
            orchestration_status=STATUS_ORCHESTRATION_DENIED,
            orchestration_owner_id=ORCHESTRATION_OWNER_ID,
            reason_codes=tuple(completeness.reason_codes or ("CAMPAIGN_INCOMPLETE",)),
            campaign_executed=False,
            public_market_data_external_read_occurred=False,
            real_evidence_written=True,
            productive_apply_occurred=False,
            terminal_selection=None,
            replay=None,
        )

    artifact_digests: dict[str, str] = {}
    durable_write = auth.durable_evidence_write_authorized

    def _persist(name: str, payload: Mapping[str, Any]) -> None:
        path = campaign_root / name
        meta = write_campaign_artifact_v1(
            artifact_path=path,
            payload=payload,
            durable_evidence_write_authorized=durable_write,
        )
        artifact_digests[name] = str(meta["artifact_digest"])

    _persist(
        AUTHORIZATION_REF_FILENAME,
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "authorization_id": auth.authorization_id,
            "authorization_digest": auth.authorization_digest,
            "execution_identity": execution_identity,
        },
    )
    _persist(
        "source_provenance.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "real_md_supplier_id": "CANONICAL_VOLATILITY_PREREGISTERED_PUBLIC_MD_SOURCE_V1",
            "venue_instrument": BOUND_VENUE_INSTRUMENT_ID,
            "public_md_host": BOUND_PUBLIC_MD_HOST_V1,
            "simulated_public_md_in_hermetic": md_read_simulated,
            "private_api_effect": False,
            "order_effect": False,
        },
    )
    _persist(
        "session_evidence.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "work_units": sealed_bundle.get("work_units"),
        },
    )
    _persist(
        "oos_evidence.json",
        {"campaign_id": CAMPAIGN_ID, **dict(sealed_bundle.get("oos_evidence") or {})},
    )
    _persist(
        "robustness_evidence.json",
        {"campaign_id": CAMPAIGN_ID, **dict(sealed_bundle.get("robustness_evidence") or {})},
    )
    _persist(
        "economic_evidence.json",
        {"campaign_id": CAMPAIGN_ID, **dict(sealed_bundle.get("economic_evidence") or {})},
    )
    _persist(
        "failure_evidence.json",
        {"campaign_id": CAMPAIGN_ID, **dict(sealed_bundle.get("failure_evidence") or {})},
    )
    _persist(
        "contamination_adjudication.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            **leakage,
        },
    )
    _persist(
        "campaign_completeness.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "completeness": completeness.to_dict(),
            "sealed_evidence_bundle": sealed_bundle,
        },
    )

    replay = replay_sealed_campaign_evidence_v1(sealed_bundle, repo_root=repo_root)
    selection = replay.get("selection") or {}
    _persist(
        "selection_result.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "selection_policy_digest": SELECTION_POLICY_DIGEST,
            "selection": selection,
            "proposal_only": True,
            "productive_apply": False,
        },
    )
    _persist(
        "campaign_manifest.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "campaign_sealed": True,
            "execution_identity": execution_identity,
            "schema_version": ORCHESTRATION_SCHEMA_VERSION,
        },
    )
    seal_manifest_sha256_v1(campaign_root=campaign_root, artifact_digests=artifact_digests)

    _write_execution_state(
        state_path,
        execution_identity=execution_identity,
        partial=False,
        complete=True,
    )

    productive_apply = bool(selection.get("productive_apply"))
    return F1M9AuthorizedCampaignRunOrchestrationResultV1(
        orchestration_status=STATUS_TERMINAL_VERDICT_PASS,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=(),
        campaign_executed=False,
        public_market_data_external_read_occurred=False,
        real_evidence_written=True,
        productive_apply_occurred=productive_apply,
        terminal_selection=selection,
        replay=replay,
    )


def run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
    request: F1M9AuthorizedCampaignRunOrchestrationRequestV1,
) -> F1M9AuthorizedCampaignRunOrchestrationResultV1:
    root = request.repo_root or Path(__file__).resolve().parents[3]
    path_ready = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=request.runtime_authorization,
            evaluation_time_utc=request.evaluation_time_utc,
            repo_root=root,
        )
    )
    if path_ready.execution_status != "F1_M9_AUTHORIZED_CAMPAIGN_EXECUTION_PATH_READY":
        return _denied(*path_ready.reason_codes)

    auth, auth_reasons = resolve_runtime_authorization_v1(
        request.runtime_authorization,
        evaluation_time_utc=request.evaluation_time_utc,
    )
    if auth is None or auth_reasons:
        return _denied(*(auth_reasons or ("RUNTIME_AUTHORIZATION_INVALID",)))

    supplier_reasons = _verify_supplier_binding_against_authorization_v1(auth, repo_root=root)
    if supplier_reasons:
        return _denied(*supplier_reasons)

    if request.allow_hermetic_terminal_effects:
        if request.hermetic_isolated_campaign_root is None:
            return _denied("HERMETIC_ROOT_REQUIRED")
        return _run_hermetic_terminal_path_v1(
            repo_root=root,
            campaign_root=request.hermetic_isolated_campaign_root,
            auth=auth,
            evaluation_time_utc=request.evaluation_time_utc or datetime.now(timezone.utc),
            request=request,
        )

    _ = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
    return F1M9AuthorizedCampaignRunOrchestrationResultV1(
        orchestration_status=STATUS_BUILD_SLICE_BOUND_ONLY,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=("REAL_EFFECTS_DISABLED_IN_BUILD_SLICE",),
        campaign_executed=CAMPAIGN_EXECUTED,
        public_market_data_external_read_occurred=PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED,
        real_evidence_written=NEW_DECISION_MAKING_EVIDENCE_GENERATED,
        productive_apply_occurred=False,
        terminal_selection=None,
        replay=None,
    )


def orchestration_boundary_invariants_v1() -> dict[str, bool]:
    return {
        "campaign_executed": CAMPAIGN_EXECUTED is False,
        "public_market_data_external_read_occurred": (
            PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED is False
        ),
        "new_decision_making_evidence_generated": NEW_DECISION_MAKING_EVIDENCE_GENERATED is False,
        "exchange_private_trading_effect_occurred": EXCHANGE_PRIVATE_TRADING_EFFECT_OCCURRED
        is False,
        "order_effect_occurred": ORDER_EFFECT_OCCURRED is False,
    }


__all__ = [
    "F1M9AuthorizedCampaignRunOrchestrationRequestV1",
    "F1M9AuthorizedCampaignRunOrchestrationResultV1",
    "HermeticEvidenceClass",
    "orchestration_boundary_invariants_v1",
    "run_f1_m9_prospective_authorized_campaign_run_orchestration_v1",
]
