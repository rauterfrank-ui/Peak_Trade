"""Terminal authorized campaign run orchestration owner for F1/M9 prospective selection.

Execution modes (explicit, non-conflated):
- BUILD_BIND_ONLY: verify/bind only — no REAL public-MD read, no durable repo writes.
- HERMETIC_TERMINAL_TEST: isolated tmp_path terminal path via hermetic evidence builder.
- REAL_AUTHORIZED_CAMPAIGN_EXECUTION: issued authorization + canonical supplier adapter path
  (process-gated; enablement slice proves wiring via fake adapter in tests only).
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
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_mode_v1 import (
    F1M9OrchestrationExecutionModeV1,
    STATUS_REAL_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    AUTHORIZATION_REF_FILENAME,
    EXECUTION_STATE_FILENAME,
    ORCHESTRATION_OWNER_ID,
    ORCHESTRATION_SCHEMA_VERSION,
    REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS,
    STATUS_ALREADY_COMPLETE_REPLAY,
    STATUS_BUILD_SLICE_BOUND_ONLY,
    STATUS_ORCHESTRATION_DENIED,
    STATUS_REAL_TERMINAL_VERDICT_PASS,
    STATUS_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_campaign_evidence_pipeline_v1 import (
    RealCampaignEvidencePipelineError,
    build_real_campaign_sealed_evidence_bundle_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    RealPublicMdSessionAdapterV1,
    resolve_canonical_real_md_supplier_runtime_binding_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_issuance_v1 import (
    verify_issued_runtime_authorization_bindings_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.work_unit_exactly_once_v1 import (
    WorkUnitExactlyOnceError,
    record_work_unit_execution_v1,
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
    execution_mode: F1M9OrchestrationExecutionModeV1 = (
        F1M9OrchestrationExecutionModeV1.BUILD_BIND_ONLY
    )
    hermetic_isolated_campaign_root: Path | None = None
    real_campaign_root: Path | None = None
    allow_hermetic_terminal_effects: bool = False
    hermetic_evidence_class: HermeticEvidenceClass = HermeticEvidenceClass.REAL_CLASS
    hermetic_force_incomplete: bool = False
    public_md_session_fn: PublicMdSessionFn | None = None
    real_public_md_adapter: RealPublicMdSessionAdapterV1 | None = None
    allow_real_execution_effects_for_test: bool = False
    real_force_incomplete: bool = False
    expected_bound_origin_main_sha: str | None = None


@dataclass(frozen=True, slots=True)
class F1M9AuthorizedCampaignRunOrchestrationResultV1:
    orchestration_status: str
    orchestration_owner_id: str
    reason_codes: tuple[str, ...]
    execution_mode: str
    authorized_campaign_execution_terminal_path_proven: bool
    real_authorized_campaign_execution_path_proven: bool
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
            "execution_mode": self.execution_mode,
            "authorized_campaign_execution_terminal_path_proven": (
                self.authorized_campaign_execution_terminal_path_proven
            ),
            "real_authorized_campaign_execution_path_proven": (
                self.real_authorized_campaign_execution_path_proven
            ),
            "campaign_executed": self.campaign_executed,
            "public_market_data_external_read_occurred": (
                self.public_market_data_external_read_occurred
            ),
            "real_evidence_written": self.real_evidence_written,
            "productive_apply_occurred": self.productive_apply_occurred,
            "terminal_selection": self.terminal_selection,
            "replay": self.replay,
        }


def _resolve_execution_mode_v1(
    request: F1M9AuthorizedCampaignRunOrchestrationRequestV1,
) -> F1M9OrchestrationExecutionModeV1:
    if request.execution_mode != F1M9OrchestrationExecutionModeV1.BUILD_BIND_ONLY:
        return request.execution_mode
    if request.allow_hermetic_terminal_effects:
        return F1M9OrchestrationExecutionModeV1.HERMETIC_TERMINAL_TEST
    return F1M9OrchestrationExecutionModeV1.BUILD_BIND_ONLY


def _denied(
    *reasons: str,
    execution_mode: str = F1M9OrchestrationExecutionModeV1.BUILD_BIND_ONLY.value,
    real_evidence_written: bool = False,
) -> F1M9AuthorizedCampaignRunOrchestrationResultV1:
    return F1M9AuthorizedCampaignRunOrchestrationResultV1(
        orchestration_status=STATUS_ORCHESTRATION_DENIED,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=reasons,
        execution_mode=execution_mode,
        authorized_campaign_execution_terminal_path_proven=False,
        real_authorized_campaign_execution_path_proven=False,
        campaign_executed=False,
        public_market_data_external_read_occurred=False,
        real_evidence_written=real_evidence_written,
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
            execution_mode=F1M9OrchestrationExecutionModeV1.HERMETIC_TERMINAL_TEST.value,
            authorized_campaign_execution_terminal_path_proven=False,
            real_authorized_campaign_execution_path_proven=False,
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
            execution_mode=F1M9OrchestrationExecutionModeV1.HERMETIC_TERMINAL_TEST.value,
            authorized_campaign_execution_terminal_path_proven=False,
            real_authorized_campaign_execution_path_proven=False,
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
        execution_mode=F1M9OrchestrationExecutionModeV1.HERMETIC_TERMINAL_TEST.value,
        authorized_campaign_execution_terminal_path_proven=True,
        real_authorized_campaign_execution_path_proven=False,
        campaign_executed=False,
        public_market_data_external_read_occurred=False,
        real_evidence_written=True,
        productive_apply_occurred=productive_apply,
        terminal_selection=selection,
        replay=replay,
    )


def _run_real_authorized_path_v1(
    *,
    repo_root: Path,
    campaign_root: Path,
    auth: F1M9ProspectiveCampaignRuntimeAuthorizationV1,
    auth_payload: Mapping[str, Any],
    evaluation_time_utc: datetime,
    request: F1M9AuthorizedCampaignRunOrchestrationRequestV1,
) -> F1M9AuthorizedCampaignRunOrchestrationResultV1:
    mode = F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION.value
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
        return _denied(
            *tuple(resume.get("reason_codes") or ("RESUME_FAIL_CLOSED",)), execution_mode=mode
        )

    if resume["resume_state"] == RESUME_STATE_ALREADY_COMPLETE:
        replay_reasons = verify_authorization_not_replay_source_v1(
            campaign_root=campaign_root,
            sealed_manifest=sealed_existing,
        )
        if replay_reasons:
            return _denied(*replay_reasons, execution_mode=mode)
        if sealed_existing is None:
            return _denied("SEALED_BUNDLE_MISSING", execution_mode=mode)
        try:
            replay = replay_sealed_campaign_evidence_v1(sealed_existing, repo_root=repo_root)
        except CampaignReplayError as exc:
            return _denied(str(exc), execution_mode=mode)
        return F1M9AuthorizedCampaignRunOrchestrationResultV1(
            orchestration_status=STATUS_ALREADY_COMPLETE_REPLAY,
            orchestration_owner_id=ORCHESTRATION_OWNER_ID,
            reason_codes=("REPLAY_ONLY_NO_NEW_REAL_EVIDENCE",),
            execution_mode=mode,
            authorized_campaign_execution_terminal_path_proven=False,
            real_authorized_campaign_execution_path_proven=False,
            campaign_executed=False,
            public_market_data_external_read_occurred=False,
            real_evidence_written=False,
            productive_apply_occurred=False,
            terminal_selection=replay.get("selection"),
            replay=replay,
        )

    if resume["resume_state"] != RESUME_STATE_RESUME_AUTHORIZED:
        return _denied("RESUME_STATE_UNKNOWN", execution_mode=mode)

    if not auth.public_market_data_read_authorized or not auth.durable_evidence_write_authorized:
        return _denied(
            "REAL_PUBLIC_MD_READ_NOT_AUTHORIZED",
            "DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED",
            execution_mode=mode,
        )

    adapter = request.real_public_md_adapter
    if adapter is None:
        return _denied("REAL_PUBLIC_MD_ADAPTER_REQUIRED", execution_mode=mode)

    consumed_at = evaluation_time_utc.isoformat().replace("+00:00", "Z")
    allow_effects = (
        REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS or request.allow_real_execution_effects_for_test
    )
    try:
        atomic_consume_runtime_authorization_v1(
            campaign_root=campaign_root,
            authorization_id=auth.authorization_id,
            authorization_digest=auth.authorization_digest,
            execution_identity=execution_identity,
            consumed_at_utc=consumed_at,
            allow_consume=allow_effects,
        )
    except AuthorizationConsumeError as exc:
        return _denied(str(exc), execution_mode=mode)

    state_path = campaign_root / EXECUTION_STATE_FILENAME
    _write_execution_state(
        state_path,
        execution_identity=execution_identity,
        partial=True,
        complete=False,
    )

    work_units = resolve_preregistered_session_work_units_v1(repo_root=repo_root)
    authorized_unit_ids = tuple(
        str(x) for x in (auth_payload.get("authorized_work_unit_ids") or [])
    )
    expected_ids = tuple(str(u["session_id"]) for u in work_units)
    if authorized_unit_ids != expected_ids:
        return _denied("PREREGISTERED_WORK_UNIT_BINDING_MISMATCH", execution_mode=mode)

    session_results = []
    for unit in work_units:
        session_id = str(unit["session_id"])
        try:
            record_work_unit_execution_v1(
                campaign_root=campaign_root,
                session_id=session_id,
                execution_identity=execution_identity,
                allow_record=allow_effects,
            )
        except WorkUnitExactlyOnceError as exc:
            return _denied(str(exc), execution_mode=mode)
        row = adapter.execute_work_unit_v1(work_unit=unit, authorization=auth_payload)
        if row.private_api_effect or row.credential_access or row.order_effect:
            return _denied("FORBIDDEN_SIDE_EFFECT_IN_REAL_ADAPTER", execution_mode=mode)
        session_results.append(row)

    try:
        sealed_bundle = build_real_campaign_sealed_evidence_bundle_v1(
            session_results=session_results,
            decision_making_evidence_timestamp_utc=consumed_at,
            execution_identity=execution_identity,
            force_incomplete=request.real_force_incomplete,
        )
    except RealCampaignEvidencePipelineError as exc:
        return _denied(str(exc), execution_mode=mode)

    leakage = assert_decision_evidence_downstream_of_new_preregistration_v1(
        sealed_bundle, repo_root=repo_root
    )
    if leakage.get("historical_evidence_decision_leakage"):
        return _denied("CONTAMINATION_LEAKAGE", execution_mode=mode)

    completeness = adjudicate_campaign_completeness_v1(sealed_bundle, repo_root=repo_root)
    if not completeness.campaign_selection_eligible:
        return F1M9AuthorizedCampaignRunOrchestrationResultV1(
            orchestration_status=STATUS_ORCHESTRATION_DENIED,
            orchestration_owner_id=ORCHESTRATION_OWNER_ID,
            reason_codes=tuple(completeness.reason_codes or ("CAMPAIGN_INCOMPLETE",)),
            execution_mode=mode,
            authorized_campaign_execution_terminal_path_proven=False,
            real_authorized_campaign_execution_path_proven=False,
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
            "issuance_owner_id": auth_payload.get("issuance_owner_id"),
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
            "real_authorized_campaign_execution_path": True,
            "simulated_public_md_in_hermetic": False,
            "private_api_effect": False,
            "order_effect": False,
            "credential_access": False,
        },
    )
    _persist(
        "session_evidence.json",
        {
            "campaign_id": CAMPAIGN_ID,
            "preregistration_digest": PREREGISTRATION_DIGEST,
            "work_units": sealed_bundle.get("work_units"),
            "session_results": sealed_bundle.get("session_results"),
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
            "execution_mode": mode,
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
        orchestration_status=STATUS_REAL_TERMINAL_VERDICT_PASS,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=(),
        execution_mode=mode,
        authorized_campaign_execution_terminal_path_proven=False,
        real_authorized_campaign_execution_path_proven=True,
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

    mode = _resolve_execution_mode_v1(request)
    eval_time = request.evaluation_time_utc or datetime.now(timezone.utc)

    if mode == F1M9OrchestrationExecutionModeV1.HERMETIC_TERMINAL_TEST:
        isolated = request.hermetic_isolated_campaign_root or request.real_campaign_root
        if isolated is None:
            return _denied(
                "HERMETIC_ROOT_REQUIRED",
                execution_mode=mode.value,
            )
        return _run_hermetic_terminal_path_v1(
            repo_root=root,
            campaign_root=isolated,
            auth=auth,
            evaluation_time_utc=eval_time,
            request=request,
        )

    if mode == F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION:
        if request.runtime_authorization is None:
            return _denied(
                "RUNTIME_AUTHORIZATION_ABSENT",
                execution_mode=mode.value,
            )
        issuance_reasons = verify_issued_runtime_authorization_bindings_v1(
            request.runtime_authorization,
            repo_root=root,
            expected_bound_origin_main_sha=request.expected_bound_origin_main_sha,
        )
        if issuance_reasons:
            return _denied(*issuance_reasons, execution_mode=mode.value)
        supplier_binding = resolve_canonical_real_md_supplier_runtime_binding_v1(repo_root=root)
        if not supplier_binding.get("real_md_supplier_runtime_bound"):
            return _denied("REAL_MD_SUPPLIER_NOT_RUNTIME_BOUND", execution_mode=mode.value)
        if not REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS and not (
            request.allow_real_execution_effects_for_test
        ):
            return F1M9AuthorizedCampaignRunOrchestrationResultV1(
                orchestration_status=STATUS_REAL_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE,
                orchestration_owner_id=ORCHESTRATION_OWNER_ID,
                reason_codes=("REAL_CAMPAIGN_EXECUTION_REQUIRES_PROCESS_ENABLEMENT",),
                execution_mode=mode.value,
                authorized_campaign_execution_terminal_path_proven=False,
                real_authorized_campaign_execution_path_proven=False,
                campaign_executed=CAMPAIGN_EXECUTED,
                public_market_data_external_read_occurred=PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED,
                real_evidence_written=NEW_DECISION_MAKING_EVIDENCE_GENERATED,
                productive_apply_occurred=False,
                terminal_selection=None,
                replay=None,
            )
        campaign_root = request.real_campaign_root or request.hermetic_isolated_campaign_root
        if campaign_root is None:
            durable = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
            campaign_root = durable.campaign_root
        return _run_real_authorized_path_v1(
            repo_root=root,
            campaign_root=campaign_root,
            auth=auth,
            auth_payload=dict(request.runtime_authorization),
            evaluation_time_utc=eval_time,
            request=request,
        )

    _ = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
    return F1M9AuthorizedCampaignRunOrchestrationResultV1(
        orchestration_status=STATUS_BUILD_SLICE_BOUND_ONLY,
        orchestration_owner_id=ORCHESTRATION_OWNER_ID,
        reason_codes=("REAL_EFFECTS_DISABLED_IN_BUILD_SLICE",),
        execution_mode=F1M9OrchestrationExecutionModeV1.BUILD_BIND_ONLY.value,
        authorized_campaign_execution_terminal_path_proven=False,
        real_authorized_campaign_execution_path_proven=False,
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
    "F1M9OrchestrationExecutionModeV1",
    "HermeticEvidenceClass",
    "orchestration_boundary_invariants_v1",
    "run_f1_m9_prospective_authorized_campaign_run_orchestration_v1",
]
