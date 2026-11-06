"""OKX Futures Shadow offline end-to-end projection binding v0.

Composition-only boundary:
  readiness gate → durable readiness projection write → reader/verifier →
  (if offline preparation path permitted) canonical no-order cycle.

Activation readiness may remain BLOCKED for non-29U gates; when verified
Step 29U evidence is bound, CANONICAL_STEP_29U_ABSENT is not emitted.
Activation gaps do not veto the offline no-order preparation cycle when
the offline path remains permitted. Reuses existing canonical owners only. No
second decision/risk/safety/execution/reconciliation/readiness/writer/reader/
projection truth. Offline, non-activating.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Optional

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    PRODUCTION_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_TYPE,
    VENUE_OKX_EUROPE,
)
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    OkxFuturesShadowNoOrderCycleResultV0,
    run_okx_futures_shadow_no_order_cycle_v0,
    serialize_okx_futures_shadow_no_order_cycle_result_v0,
)
from src.ops.shadow_preparation_readiness_gate_v0 import (
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    PROJECTION_OUTPUT_PATH_CONFIG_KEY,
    PROJECTION_OVERALL_STATUS_VERIFIED,
    PROJECTION_SCHEMA_ID,
    PROJECTION_SCHEMA_VERSION,
    ShadowPreparationReadinessGateError,
    ShadowPreparationReadinessGateResultV0,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
    verify_shadow_preparation_readiness_projection_v0,
    write_shadow_preparation_readiness_projection_v0,
)

PACKAGE_MARKER = "OKX_FUTURES_SHADOW_OFFLINE_E2E_PROJECTION_BINDING_V0=true"
PRODUCER_FAMILY = "ops.okx_futures_shadow_offline_e2e_projection_binding_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CLI_RELPATH = "scripts/ops/run_okx_futures_shadow_offline_e2e_projection_binding_v0.py"
ENTRYPOINT_OWNER = PRODUCER_FAMILY

BINDING_STATUS_PASS: Literal["BINDING_PASS"] = "BINDING_PASS"
BINDING_STATUS_BLOCKED: Literal["BINDING_BLOCKED"] = "BINDING_BLOCKED"
BINDING_STATUS_ERROR: Literal["BINDING_ERROR"] = "BINDING_ERROR"

READINESS_STATUS_READY: Literal["READY"] = "READY"
READINESS_STATUS_BLOCKED: Literal["BLOCKED"] = "BLOCKED"

OFFLINE_PATH_TOKEN = "CONTINUE_OFFLINE_SHADOW_PREPARATION"

EXPECTED_DECISION = "hold"
EXPECTED_RISK_SIZING = "NONE"
EXPECTED_SAFETY = "PASS"
EXPECTED_EXECUTION_PROJECTION = "NOT_APPLICABLE:NONE"
EXPECTED_RECONCILIATION = "BOUND_OFFLINE"

BindingStatusV0 = Literal["BINDING_PASS", "BINDING_BLOCKED", "BINDING_ERROR"]
ReadinessStatusV0 = Literal["READY", "BLOCKED"]

CycleRunnerV0 = Callable[..., OkxFuturesShadowNoOrderCycleResultV0]


@dataclass(frozen=True)
class OkxFuturesShadowOfflineE2EProjectionBindingResultV0:
    """Structured fail-closed outcome for one offline e2e binding invocation."""

    binding_status: BindingStatusV0
    schema_id: str
    schema_version: str
    generated_at: str | None
    readiness_result: ReadinessStatusV0 | None
    final_decision: str | None
    risk_sizing_result: str | None
    safety_result: str | None
    execution_projection_result: str | None
    reconciliation_result: str | None
    venue: str | None
    instrument_class: str | None
    btc_excluded: bool | None
    spot_excluded: bool | None
    futures_only: bool | None
    order_submission_count: int
    order_capable_client_instantiated: bool
    cycle_invoked: bool
    projection_path: str | None
    projection_schema_id: str | None
    projection_schema_version: str | None
    projection_sha256: str | None
    verification_status: Literal["VERIFIED", "BLOCKED"] | None
    verification_verified: bool | None
    verification_result: str | None
    reason_codes: tuple[str, ...]
    cycle_projection: Mapping[str, Any] | None
    network_access: bool = False
    background_process_left_running: bool = False
    package_marker: str = PACKAGE_MARKER
    entrypoint_owner: str = ENTRYPOINT_OWNER
    cli_relpath: str = CLI_RELPATH

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "binding_status": self.binding_status,
            "generated_at": self.generated_at,
            "readiness_result": self.readiness_result,
            "final_decision": self.final_decision,
            "risk_sizing_result": self.risk_sizing_result,
            "safety_result": self.safety_result,
            "execution_projection_result": self.execution_projection_result,
            "reconciliation_result": self.reconciliation_result,
            "venue": self.venue,
            "instrument_class": self.instrument_class,
            "btc_excluded": self.btc_excluded,
            "spot_excluded": self.spot_excluded,
            "futures_only": self.futures_only,
            "order_submission_count": self.order_submission_count,
            "order_capable_client_instantiated": self.order_capable_client_instantiated,
            "cycle_invoked": self.cycle_invoked,
            "projection_path": self.projection_path,
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "projection_sha256": self.projection_sha256,
            "verification_status": self.verification_status,
            "verification_verified": self.verification_verified,
            "verification_result": self.verification_result,
            "reason_codes": list(self.reason_codes),
            "cycle_projection": (
                dict(self.cycle_projection) if self.cycle_projection is not None else None
            ),
            "network_access": False,
            "background_process_left_running": False,
            "authority_effect": "NONE",
            "activation_authority": False,
            "projection_only": True,
            "package_marker": self.package_marker,
            "entrypoint_owner": self.entrypoint_owner,
            "cli_relpath": self.cli_relpath,
        }


def _error_result(
    *,
    reason_codes: tuple[str, ...],
    generated_at: str | None = None,
    readiness_result: ReadinessStatusV0 | None = None,
    cycle_invoked: bool = False,
    cycle: OkxFuturesShadowNoOrderCycleResultV0 | None = None,
    projection_path: str | None = None,
    projection_schema_id: str | None = None,
    projection_schema_version: str | None = None,
    projection_sha256: str | None = None,
    verification_status: Literal["VERIFIED", "BLOCKED"] | None = None,
    verification_verified: bool | None = None,
) -> OkxFuturesShadowOfflineE2EProjectionBindingResultV0:
    return OkxFuturesShadowOfflineE2EProjectionBindingResultV0(
        binding_status=BINDING_STATUS_ERROR,
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        readiness_result=readiness_result,
        final_decision=cycle.decision_result if cycle is not None else None,
        risk_sizing_result=cycle.risk_sizing_result if cycle is not None else None,
        safety_result=cycle.safety_result if cycle is not None else None,
        execution_projection_result=(cycle.execution_intent_result if cycle is not None else None),
        reconciliation_result=(cycle.reconciliation_audit_result if cycle is not None else None),
        venue=cycle.venue if cycle is not None else None,
        instrument_class=cycle.market_classification if cycle is not None else None,
        btc_excluded=cycle.btc_excluded if cycle is not None else None,
        spot_excluded=cycle.spot_excluded if cycle is not None else None,
        futures_only=cycle.futures_only if cycle is not None else None,
        order_submission_count=_order_submission_count(cycle) if cycle is not None else 0,
        order_capable_client_instantiated=(
            bool(cycle.order_capable_client_instantiated) if cycle is not None else False
        ),
        cycle_invoked=cycle_invoked,
        projection_path=projection_path,
        projection_schema_id=projection_schema_id,
        projection_schema_version=projection_schema_version,
        projection_sha256=projection_sha256,
        verification_status=verification_status,
        verification_verified=verification_verified,
        verification_result=(
            None if verification_status is None else ("PASS" if verification_verified else "FAIL")
        ),
        reason_codes=reason_codes,
        cycle_projection=(
            serialize_okx_futures_shadow_no_order_cycle_result_v0(cycle)
            if cycle is not None
            else None
        ),
    )


def _classify_readiness_status(
    evaluation: ShadowPreparationReadinessGateResultV0,
) -> ReadinessStatusV0:
    if (
        evaluation.shadow_preparation_complete
        and not evaluation.blockers
        and not evaluation.unmet_gates
    ):
        return READINESS_STATUS_READY
    return READINESS_STATUS_BLOCKED


def _offline_shadow_preparation_path_permitted(
    evaluation: ShadowPreparationReadinessGateResultV0,
) -> bool:
    """Existing contract: offline classification only; never activation."""
    if evaluation.authority_effect != "NONE":
        return False
    if evaluation.shadow_activation_authorized:
        return False
    if evaluation.paper_activation_authorized:
        return False
    if evaluation.testnet_activation_authorized:
        return False
    if evaluation.scheduler_activation_authorized:
        return False
    if evaluation.runtime_activation_authorized:
        return False
    if evaluation.live_authorized or evaluation.orders_authorized:
        return False
    if OFFLINE_PATH_TOKEN not in evaluation.next_permitted_action:
        return False
    return True


def _resolve_output_path(
    *,
    repo_root: Path,
    output_path: str | None,
    config: Mapping[str, Any] | None,
    config_path: Path | None,
) -> str:
    if output_path is not None:
        if not isinstance(output_path, str) or not output_path.strip():
            raise ShadowPreparationReadinessGateError("BINDING_OUTPUT_PATH_EMPTY")
        return output_path.strip()
    cfg = (
        dict(config)
        if config is not None
        else load_shadow_preparation_readiness_gate_config_v0(config_path, repo_root=repo_root)
    )
    raw = cfg.get(PROJECTION_OUTPUT_PATH_CONFIG_KEY)
    if not isinstance(raw, str) or not raw.strip():
        raise ShadowPreparationReadinessGateError("BINDING_OUTPUT_PATH_UNCONFIGURED")
    return raw.strip()


def _order_submission_count(cycle: OkxFuturesShadowNoOrderCycleResultV0) -> int:
    flags = (
        bool(cycle.real_order_submission),
        bool(cycle.exchange_order_submission),
        bool(cycle.testnet_order_submission),
    )
    return sum(1 for flag in flags if flag)


def validate_cycle_projection_for_binding_v0(
    cycle: OkxFuturesShadowNoOrderCycleResultV0 | None,
) -> tuple[str, ...]:
    """Fail-closed validation of the exact returned cycle (no recomputation)."""
    if cycle is None:
        return ("CYCLE_RESULT_MISSING",)
    reasons: list[str] = []
    if cycle.terminal_status != "PASS":
        reasons.append("CYCLE_TERMINAL_STATUS_NOT_PASS")
    if not isinstance(cycle.decision_result, str) or not cycle.decision_result.strip():
        reasons.append("CYCLE_RESULT_INVALID:decision_result")
    elif cycle.decision_result != EXPECTED_DECISION:
        reasons.append("CYCLE_DECISION_NOT_HOLD")
    if cycle.risk_sizing_result != EXPECTED_RISK_SIZING:
        reasons.append("CYCLE_RISK_SIZING_NOT_NONE")
    if cycle.safety_result != EXPECTED_SAFETY:
        reasons.append("CYCLE_SAFETY_NOT_PASS")
    if cycle.execution_intent_result != EXPECTED_EXECUTION_PROJECTION:
        reasons.append("CYCLE_EXECUTION_PROJECTION_NOT_APPLICABLE_NONE")
    if cycle.reconciliation_audit_result != EXPECTED_RECONCILIATION:
        reasons.append("CYCLE_RECONCILIATION_NOT_BOUND_OFFLINE")
    if cycle.venue != VENUE_OKX_EUROPE:
        reasons.append("CYCLE_VENUE_NOT_OKX")
    if cycle.market_classification != PRODUCTION_INSTRUMENT_TYPE:
        reasons.append("CYCLE_INSTRUMENT_CLASS_NOT_FUTURES")
    if not cycle.futures_only:
        reasons.append("CYCLE_FUTURES_ONLY_REQUIRED")
    if not cycle.btc_excluded:
        reasons.append("CYCLE_BTC_NOT_EXCLUDED")
    if not cycle.spot_excluded:
        reasons.append("CYCLE_SPOT_NOT_EXCLUDED")
    if _order_submission_count(cycle) != 0:
        reasons.append("CYCLE_ORDER_SUBMISSION_COUNT_NONZERO")
    if cycle.order_capable_client_instantiated:
        reasons.append("CYCLE_ORDER_CAPABLE_CLIENT_INSTANTIATED")
    if cycle.background_process_left_running:
        reasons.append("CYCLE_BACKGROUND_PROCESS_LEFT_RUNNING")
    if cycle.live_activation or cycle.scheduler:
        reasons.append("CYCLE_ACTIVATION_SURFACE_FORBIDDEN")
    # Preserve order, drop duplicates.
    deduped: list[str] = []
    for code in reasons:
        if code not in deduped:
            deduped.append(code)
    return tuple(deduped)


def run_okx_futures_shadow_offline_e2e_projection_binding_v0(
    *,
    repo_root: Path,
    output_path: str | None = None,
    config: Mapping[str, Any] | None = None,
    config_path: Path | None = None,
    evaluated_at: str | None = None,
    as_of: str | None = None,
    mode: str = "shadow",
    instrument_id: Optional[str] = None,
    cycle_runner: CycleRunnerV0 | None = None,
) -> OkxFuturesShadowOfflineE2EProjectionBindingResultV0:
    """Bind readiness → canonical no-order cycle → durable projection → verify."""
    root = repo_root.resolve()
    runner = cycle_runner or run_okx_futures_shadow_no_order_cycle_v0

    try:
        resolved_output = _resolve_output_path(
            repo_root=root,
            output_path=output_path,
            config=config,
            config_path=config_path,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(reason_codes=(f"BINDING_INPUT_INVALID:{exc}",))

    try:
        evaluation = evaluate_shadow_preparation_readiness_gate_v0(
            config=config,
            config_path=config_path,
            repo_root=root,
            evaluated_at=evaluated_at,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(reason_codes=(f"GATE_EVALUATION_FAILED:{exc}",))
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(reason_codes=(f"GATE_EVALUATION_FAILED:{type(exc).__name__}:{exc}",))

    generated_at = evaluation.evaluated_at
    readiness_status = _classify_readiness_status(evaluation)

    if not _offline_shadow_preparation_path_permitted(evaluation):
        return _error_result(
            reason_codes=("OFFLINE_SHADOW_PREPARATION_PATH_NOT_PERMITTED",),
            generated_at=generated_at,
            readiness_result=readiness_status,
        )

    try:
        write_meta = write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=root,
            output_path=resolved_output,
            evaluated_at=generated_at,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(
            reason_codes=(f"PROJECTION_WRITE_FAILED:{exc}",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=resolved_output,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(
            reason_codes=(f"PROJECTION_WRITE_FAILED:{type(exc).__name__}:{exc}",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=resolved_output,
        )

    verify_as_of = as_of if as_of is not None else generated_at
    try:
        verification = verify_shadow_preparation_readiness_projection_v0(
            repo_root=root,
            projection_path=write_meta.output_path,
            config=config,
            config_path=config_path,
            as_of=verify_as_of,
            expected_sha256=write_meta.sha256,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(
            reason_codes=(f"PROJECTION_VERIFY_FAILED:{type(exc).__name__}:{exc}",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
        )

    if (
        not verification.verified
        or verification.overall_status != PROJECTION_OVERALL_STATUS_VERIFIED
    ):
        codes = tuple(verification.reason_codes) or ("PROJECTION_VERIFICATION_BLOCKED",)
        # Schema/digest mismatches surface through verifier reason codes.
        return _error_result(
            reason_codes=codes,
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )

    if write_meta.schema_id != PROJECTION_SCHEMA_ID:
        return _error_result(
            reason_codes=("SCHEMA_MISMATCH",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )
    if write_meta.schema_version != PROJECTION_SCHEMA_VERSION:
        return _error_result(
            reason_codes=("SCHEMA_MISMATCH",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )

    # Activation readiness READY is not required for the offline no-order cycle.
    # Remaining activation blockers must not invent a second readiness truth or
    # authorize Shadow activation. Step 29U presence comes from the bound cycle.
    selected = (
        PRODUCTION_INSTRUMENT_ID
        if instrument_id is None or str(instrument_id).strip() == ""
        else str(instrument_id).strip()
    )
    try:
        cycle = runner(mode=mode, instrument_id=selected)
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(
            reason_codes=(f"CYCLE_INVOCATION_FAILED:{type(exc).__name__}:{exc}",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            cycle_invoked=True,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )

    if cycle is None:
        return _error_result(
            reason_codes=("CYCLE_RESULT_MISSING",),
            generated_at=generated_at,
            readiness_result=readiness_status,
            cycle_invoked=True,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )

    cycle_codes = validate_cycle_projection_for_binding_v0(cycle)
    if cycle_codes:
        return _error_result(
            reason_codes=cycle_codes,
            generated_at=generated_at,
            readiness_result=readiness_status,
            cycle_invoked=True,
            cycle=cycle,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
        )

    cycle_payload = serialize_okx_futures_shadow_no_order_cycle_result_v0(cycle)
    return OkxFuturesShadowOfflineE2EProjectionBindingResultV0(
        binding_status=BINDING_STATUS_PASS,
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        readiness_result=readiness_status,
        final_decision=cycle.decision_result,
        risk_sizing_result=cycle.risk_sizing_result,
        safety_result=cycle.safety_result,
        execution_projection_result=cycle.execution_intent_result,
        reconciliation_result=cycle.reconciliation_audit_result,
        venue=cycle.venue,
        instrument_class=cycle.market_classification,
        btc_excluded=cycle.btc_excluded,
        spot_excluded=cycle.spot_excluded,
        futures_only=cycle.futures_only,
        order_submission_count=0,
        order_capable_client_instantiated=False,
        cycle_invoked=True,
        projection_path=write_meta.output_path,
        projection_schema_id=write_meta.schema_id,
        projection_schema_version=write_meta.schema_version,
        projection_sha256=write_meta.sha256,
        verification_status=verification.overall_status,
        verification_verified=verification.verified,
        verification_result="PASS",
        reason_codes=(),
        cycle_projection=cycle_payload,
    )


def result_to_machine_lines(
    result: OkxFuturesShadowOfflineE2EProjectionBindingResultV0,
) -> list[str]:
    data = result.to_dict()
    lines: list[str] = []
    for key, value in data.items():
        if key == "cycle_projection":
            rendered = "present" if value is not None else "none"
        elif isinstance(value, list):
            rendered = "[" + ",".join(str(v) for v in value) + "]"
        elif isinstance(value, bool):
            rendered = str(value).lower()
        elif value is None:
            rendered = "none"
        else:
            rendered = str(value)
        lines.append(f"{key.upper()}={rendered}")
    return lines


__all__ = [
    "BINDING_STATUS_BLOCKED",
    "BINDING_STATUS_ERROR",
    "BINDING_STATUS_PASS",
    "CLI_RELPATH",
    "DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH",
    "ENTRYPOINT_OWNER",
    "EXPECTED_DECISION",
    "EXPECTED_EXECUTION_PROJECTION",
    "EXPECTED_RECONCILIATION",
    "EXPECTED_RISK_SIZING",
    "EXPECTED_SAFETY",
    "OkxFuturesShadowOfflineE2EProjectionBindingResultV0",
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "READINESS_STATUS_BLOCKED",
    "READINESS_STATUS_READY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "result_to_machine_lines",
    "run_okx_futures_shadow_offline_e2e_projection_binding_v0",
    "validate_cycle_projection_for_binding_v0",
]
