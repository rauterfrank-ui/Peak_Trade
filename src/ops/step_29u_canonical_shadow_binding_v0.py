"""Canonical Step 29U → OKX Futures Shadow no-order binding v0.

Binds the verified offline Step 29U composition into the sole canonical OKX
Futures Shadow no-order execution path. Observability-only for presence;
does not authorize activation, orders, network Runtime, or Scheduler.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    OkxFuturesShadowNoOrderCycleResultV0,
    _fail_result,
    run_okx_futures_shadow_no_order_cycle_core_v0,
    validate_shadow_no_order_request_v0,
)
from src.ops.step_29u_offline_capability_v0 import (
    RESULT_PASS,
    SCHEMA_ID as STEP29U_SCHEMA_ID,
    run_step_29u_offline_capability_v0,
    verify_capability_evidence_v0,
)

PACKAGE_MARKER = "STEP_29U_CANONICAL_SHADOW_BINDING_V0=true"
PRODUCER_FAMILY = "ops.step_29u_canonical_shadow_binding_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
BINDING_OWNER = PRODUCER_FAMILY

CANONICAL_STEP_29U_EVIDENCE_RELPATH = (
    "evidence/ops/step_29u_offline_capability/2026-07-25_capability_hold_cycle"
)
STEP_29U_LIFECYCLE_OWNER = "ops.step_29u_offline_capability_v0"

CycleCoreRunner = Callable[..., OkxFuturesShadowNoOrderCycleResultV0]


class Step29UCanonicalShadowBindingError(ValueError):
    """Fail-closed binding error."""


def default_repo_root_v0() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_step_29u_evidence_dir_v0(repo_root: Path) -> Path:
    return (repo_root.resolve() / CANONICAL_STEP_29U_EVIDENCE_RELPATH).resolve()


def verify_canonical_step_29u_binding_evidence_v0(
    *,
    repo_root: Path,
    evidence_dir: Path | None = None,
) -> tuple[bool, tuple[str, ...], dict[str, Any] | None]:
    """Verify tracked Step 29U offline evidence for canonical shadow binding.

    Returns (ok, reason_codes, payload_or_none). Fail-closed on missing,
    malformed, digest/provenance contradiction, or activation claims.
    """
    root = repo_root.resolve()
    ev_dir = evidence_dir if evidence_dir is not None else canonical_step_29u_evidence_dir_v0(root)
    try:
        ev_dir.relative_to(root)
    except ValueError:
        return False, ("STEP_29U_EVIDENCE_OUTSIDE_REPO",), None

    if not ev_dir.is_dir():
        return False, ("STEP_29U_EVIDENCE_MISSING",), None

    result_path = ev_dir / "capability_result.json"
    manifest_path = ev_dir / "evidence_manifest.sha256"
    if not result_path.is_file():
        return False, ("STEP_29U_EVIDENCE_MISSING", "RESULT_MISSING"), None
    if not manifest_path.is_file():
        return False, ("STEP_29U_EVIDENCE_MISSING", "MANIFEST_MISSING"), None

    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, ("STEP_29U_EVIDENCE_INVALID", "RESULT_MALFORMED"), None
    if not isinstance(payload, dict):
        return False, ("STEP_29U_EVIDENCE_INVALID", "RESULT_NOT_OBJECT"), None

    reasons: list[str] = []
    if payload.get("schema_id") != STEP29U_SCHEMA_ID:
        reasons.append("STEP_29U_SCHEMA_ID_MISMATCH")
    if payload.get("capability_result") != RESULT_PASS:
        reasons.append("STEP_29U_CAPABILITY_NOT_PASS")
    if payload.get("step_29u_implemented") is not True:
        reasons.append("STEP_29U_NOT_IMPLEMENTED_IN_EVIDENCE")
    if payload.get("step_29u_bound_offline") is not True:
        reasons.append("STEP_29U_NOT_BOUND_OFFLINE_IN_EVIDENCE")
    if payload.get("step_29u_verified_offline") is not True:
        reasons.append("STEP_29U_NOT_VERIFIED_OFFLINE_IN_EVIDENCE")
    if payload.get("step_29u_activated") is True:
        reasons.append("STEP_29U_ACTIVATION_CLAIMED_IN_EVIDENCE")
    if payload.get("orders_created") is True or payload.get("orders_submitted") is True:
        reasons.append("STEP_29U_ORDERS_CLAIMED_IN_EVIDENCE")
    if payload.get("runtime_activated") is True or payload.get("scheduler_activated") is True:
        reasons.append("STEP_29U_RUNTIME_OR_SCHEDULER_CLAIMED")
    if payload.get("network_runtime_used") is True:
        reasons.append("STEP_29U_NETWORK_CLAIMED_IN_EVIDENCE")
    if payload.get("lifecycle_owner") != STEP_29U_LIFECYCLE_OWNER:
        reasons.append("STEP_29U_LIFECYCLE_OWNER_MISMATCH")

    identity = payload.get("identity")
    if not isinstance(identity, dict):
        reasons.append("STEP_29U_IDENTITY_MISSING")
    else:
        sha = str(identity.get("source_git_sha") or "").strip()
        if not sha or sha.upper() == "UNKNOWN":
            reasons.append("STEP_29U_PROVENANCE_GIT_SHA_MISSING")
        if str(identity.get("mode") or "") != "SHADOW_OFFLINE":
            reasons.append("STEP_29U_IDENTITY_MODE_INVALID")
        if identity.get("orders_allowed") is True:
            reasons.append("STEP_29U_IDENTITY_ORDERS_ALLOWED")
        if identity.get("runtime_activation_allowed") is True:
            reasons.append("STEP_29U_IDENTITY_RUNTIME_ALLOWED")

    ok_manifest, manifest_reasons = verify_capability_evidence_v0(evidence_dir=ev_dir)
    if not ok_manifest:
        reasons.extend(f"STEP_29U_MANIFEST:{r}" for r in manifest_reasons)

    if reasons:
        return False, tuple(reasons), payload
    return True, (), payload


def observe_canonical_step_29u_bound_v0(
    *,
    repo_root: Path,
    evidence_dir: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Read-only observation helper for readiness/projection surfaces."""
    ok, reasons, _payload = verify_canonical_step_29u_binding_evidence_v0(
        repo_root=repo_root,
        evidence_dir=evidence_dir,
    )
    return ok, reasons


def _enrich_cycle_result(
    cycle: OkxFuturesShadowNoOrderCycleResultV0,
    *,
    bound: bool,
    present: bool,
    evidence_verified: bool,
    capability_result: str,
    extra_blockers: tuple[str, ...] = (),
    force_fail: bool = False,
) -> OkxFuturesShadowNoOrderCycleResultV0:
    terminal = "FAIL_CLOSED" if force_fail else cycle.terminal_status
    blockers = tuple(cycle.blockers) + extra_blockers
    return replace(
        cycle,
        terminal_status=terminal,
        blockers=blockers,
        step_29u_bound=bound,
        step_29u_present=present,
        step_29u_evidence_verified=evidence_verified,
        step_29u_capability_result=capability_result,
        canonical_step_29u_absent=not bound,
        step_29u_binding_owner=BINDING_OWNER if bound else "NONE",
    )


def _cycle_result_from_payload_v0(
    payload: Mapping[str, Any],
) -> OkxFuturesShadowNoOrderCycleResultV0:
    blockers = payload.get("blockers") or ()
    reason_codes = payload.get("reason_codes") or ()
    return OkxFuturesShadowNoOrderCycleResultV0(
        terminal_status=str(payload.get("terminal_status") or "FAIL_CLOSED"),
        venue=str(payload.get("venue") or "NONE"),
        instrument=str(payload.get("instrument") or "NONE"),
        market_classification=str(payload.get("market_classification") or "UNKNOWN"),
        futures_only=bool(payload.get("futures_only", False)),
        btc_excluded=bool(payload.get("btc_excluded", True)),
        spot_excluded=bool(payload.get("spot_excluded", True)),
        input_provenance=str(payload.get("input_provenance") or "none"),
        decision_result=str(payload.get("decision_result") or "NOT_EVALUATED"),
        direction=str(payload.get("direction") or "NONE"),
        reason_codes=tuple(reason_codes),
        blockers=tuple(blockers),
        risk_sizing_result=str(payload.get("risk_sizing_result") or "NOT_EVALUATED"),
        safety_result=str(payload.get("safety_result") or "NOT_EVALUATED"),
        execution_intent_result=str(payload.get("execution_intent_result") or "NOT_EVALUATED"),
        reconciliation_audit_result=str(
            payload.get("reconciliation_audit_result") or "NOT_EVALUATED"
        ),
        real_order_submission=False,
        order_capable_client_instantiated=False,
        exchange_order_submission=False,
        testnet_order_submission=False,
        live_activation=False,
        scheduler=False,
        background_process_left_running=False,
    )


def run_step_29u_bound_okx_futures_shadow_no_order_cycle_v0(
    *,
    mode: str,
    instrument_id: Optional[str] = None,
    repo_root: Path | None = None,
    evidence_dir: Path | None = None,
    source_git_sha: str | None = None,
    live_enabled: bool = False,
    order_submission_enabled: bool = False,
    testnet_order_submission_enabled: bool = False,
    capital_change_enabled: bool = False,
    scheduler_enabled: bool = False,
    daemon_enabled: bool = False,
    reference_price: Decimal | None = None,
    cycle_core: CycleCoreRunner | None = None,
) -> OkxFuturesShadowNoOrderCycleResultV0:
    """Sole Step-29U-bound path for the canonical Shadow no-order entrypoint."""
    root = (repo_root or default_repo_root_v0()).resolve()
    selected = (
        PRODUCTION_INSTRUMENT_ID
        if instrument_id is None or str(instrument_id).strip() == ""
        else str(instrument_id).strip()
    )
    blockers = validate_shadow_no_order_request_v0(
        mode=mode,
        instrument_id=selected,
        live_enabled=live_enabled,
        order_submission_enabled=order_submission_enabled,
        testnet_order_submission_enabled=testnet_order_submission_enabled,
        capital_change_enabled=capital_change_enabled,
        scheduler_enabled=scheduler_enabled,
        daemon_enabled=daemon_enabled,
    )
    if blockers:
        return _enrich_cycle_result(
            _fail_result(blockers=blockers, instrument=selected),
            bound=False,
            present=False,
            evidence_verified=False,
            capability_result="NOT_EVALUATED",
            force_fail=True,
        )

    ok, reasons, _payload = verify_canonical_step_29u_binding_evidence_v0(
        repo_root=root,
        evidence_dir=evidence_dir,
    )
    if not ok:
        return _enrich_cycle_result(
            _fail_result(
                blockers=("STEP_29U_BINDING_FAIL_CLOSED", *reasons),
                instrument=selected,
            ),
            bound=False,
            present=False,
            evidence_verified=False,
            capability_result="STEP_29U_BINDING_BLOCKED",
            force_fail=True,
        )

    core = cycle_core or run_okx_futures_shadow_no_order_cycle_core_v0
    sha = (source_git_sha or "canonical-step-29u-shadow-binding-v0").strip()

    def _runner(**kwargs: Any) -> OkxFuturesShadowNoOrderCycleResultV0:
        return core(reference_price=reference_price, **kwargs)

    capability = run_step_29u_offline_capability_v0(
        repo_root=root,
        source_git_sha=sha,
        cycle_count=1,
        instrument_id=selected,
        cycle_runner=_runner,
        live_enabled=False,
        order_submission_enabled=False,
        testnet_order_submission_enabled=False,
        capital_change_enabled=False,
        scheduler_enabled=False,
        daemon_enabled=False,
        network_runtime_enabled=False,
        runtime_activation_enabled=False,
        ephemeral_pass_when_preverified=True,
    )

    if capability.orders_created or capability.orders_submitted:
        return _enrich_cycle_result(
            _fail_result(
                blockers=("STEP_29U_ORDER_PATH_FORBIDDEN",),
                instrument=selected,
            ),
            bound=False,
            present=True,
            evidence_verified=True,
            capability_result=str(capability.capability_result),
            force_fail=True,
        )

    if capability.capability_result != RESULT_PASS or not capability.cycles:
        fail_reasons = tuple(capability.reason_codes) or (
            f"STEP_29U_CAPABILITY_{capability.capability_result}",
        )
        return _enrich_cycle_result(
            _fail_result(
                blockers=("STEP_29U_COMPOSITION_FAIL_CLOSED", *fail_reasons),
                instrument=selected,
            ),
            bound=False,
            present=True,
            evidence_verified=True,
            capability_result=str(capability.capability_result),
            force_fail=True,
        )

    cycle_payload = capability.cycles[0].cycle_payload
    if not isinstance(cycle_payload, Mapping):
        return _enrich_cycle_result(
            _fail_result(
                blockers=("STEP_29U_CYCLE_PAYLOAD_INVALID",),
                instrument=selected,
            ),
            bound=False,
            present=True,
            evidence_verified=True,
            capability_result=str(capability.capability_result),
            force_fail=True,
        )

    core_cycle = _cycle_result_from_payload_v0(cycle_payload)
    if core_cycle.terminal_status != "PASS" or core_cycle.direction.upper() != "HOLD":
        return _enrich_cycle_result(
            core_cycle,
            bound=False,
            present=True,
            evidence_verified=True,
            capability_result=str(capability.capability_result),
            extra_blockers=("STEP_29U_BOUND_CYCLE_NOT_HOLD_PASS",),
            force_fail=True,
        )
    if (
        core_cycle.real_order_submission
        or core_cycle.order_capable_client_instantiated
        or core_cycle.exchange_order_submission
    ):
        return _enrich_cycle_result(
            core_cycle,
            bound=False,
            present=True,
            evidence_verified=True,
            capability_result=str(capability.capability_result),
            extra_blockers=("STEP_29U_ORDER_PATH_FORBIDDEN",),
            force_fail=True,
        )

    return _enrich_cycle_result(
        core_cycle,
        bound=True,
        present=True,
        evidence_verified=True,
        capability_result=str(capability.capability_result),
    )


__all__ = [
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "BINDING_OWNER",
    "CANONICAL_STEP_29U_EVIDENCE_RELPATH",
    "Step29UCanonicalShadowBindingError",
    "default_repo_root_v0",
    "canonical_step_29u_evidence_dir_v0",
    "verify_canonical_step_29u_binding_evidence_v0",
    "observe_canonical_step_29u_bound_v0",
    "run_step_29u_bound_okx_futures_shadow_no_order_cycle_v0",
]
