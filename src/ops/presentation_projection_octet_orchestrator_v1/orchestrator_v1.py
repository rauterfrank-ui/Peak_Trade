"""Presentation-only manual one-shot octet orchestrator V1.

CAPABILITY_ID=CAPABILITY_PRESENTATION_PROJECTION_OCTET_ORCHESTRATOR_V1

Dispatches to the eight existing presentation projection materializers.
Never recomputes trading/regime/risk/safety/execution/economic truth.
Never autoloads live KillSwitch state. Never invents timestamps.
Never discovers latest artifacts. Never updates MANIFEST.sha256.

Invariants:
- AUTHORITY_EFFECT=NONE
- ORCHESTRATOR_AUTHORITY_EFFECT=NONE
- DASHBOARD_ROLE=PURE_CONSUMER
- EXPLICIT_INPUT_OR_WELLKNOWN_SIBLING_ONLY=true
- PER_FAMILY_FAIL_CLOSED=true
- PARTIAL_SUCCESS_ALLOWED=true
- NO_TRADING_STATE_WRITE=true
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    ALLOWED_PROJECTION_RELATIVE_PATHS,
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DASHBOARD_ROLE,
    ERROR_ARCHIVE_ROOT_REQUIRED,
    ERROR_GENERATED_AT_REQUIRED,
    ERROR_INVALID_OVERRIDE,
    ERROR_SAFETY_CALLER_OBJECT_REQUIRED,
    ERROR_UNKNOWN_FAMILY,
    FAMILY_CANONICAL_DECISION,
    FAMILY_DOUBLE_PLAY,
    FAMILY_DYNAMIC_SCOPE,
    FAMILY_ECONOMIC_SUMMARY,
    FAMILY_EXECUTION_RECONCILIATION,
    FAMILY_ORDER,
    FAMILY_REGIME_BULL_BEAR_SWITCH,
    FAMILY_RISK_SIZING_CAPITAL,
    FAMILY_SAFETY_AUTHORITY,
    ORCHESTRATOR_AUTHORITY_EFFECT,
    OWNER,
    PROJECTION_PATH_BY_FAMILY,
    SIBLING_PATH_BY_FAMILY,
    STATUS_BLOCKED,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_SKIPPED,
    STATUS_WRITTEN,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1 import (
    materialize_bull_bear_regime_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_materializer_v1 import (
    materialize_canonical_decision_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
    materialize_double_play_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1 import (
    materialize_dynamic_scope_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1 import (
    materialize_economic_summary_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_materializer_v1 import (
    materialize_execution_reconciliation_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_materializer_v1 import (
    materialize_risk_sizing_capital_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_materializer_v1 import (
    materialize_safety_authority_presentation_projection_v1,
)

_INPUT_KWARG_BY_FAMILY: dict[str, str] = {
    FAMILY_DYNAMIC_SCOPE: "dynamic_scope",
    FAMILY_REGIME_BULL_BEAR_SWITCH: "regime_bull_bear_switch",
    FAMILY_CANONICAL_DECISION: "evidence",
    FAMILY_DOUBLE_PLAY: "display",
    FAMILY_SAFETY_AUTHORITY: "safety_authority",
    FAMILY_RISK_SIZING_CAPITAL: "risk_sizing_capital",
    FAMILY_EXECUTION_RECONCILIATION: "execution_reconciliation",
    FAMILY_ECONOMIC_SUMMARY: "economic_summary",
}

_MATERIALIZER_BY_FAMILY: dict[str, Callable[..., Any]] = {
    FAMILY_DYNAMIC_SCOPE: materialize_dynamic_scope_presentation_projection_v1,
    FAMILY_REGIME_BULL_BEAR_SWITCH: materialize_bull_bear_regime_presentation_projection_v1,
    FAMILY_CANONICAL_DECISION: materialize_canonical_decision_presentation_projection_v1,
    FAMILY_DOUBLE_PLAY: materialize_double_play_presentation_projection_v1,
    FAMILY_SAFETY_AUTHORITY: materialize_safety_authority_presentation_projection_v1,
    FAMILY_RISK_SIZING_CAPITAL: materialize_risk_sizing_capital_presentation_projection_v1,
    FAMILY_EXECUTION_RECONCILIATION: (
        materialize_execution_reconciliation_presentation_projection_v1
    ),
    FAMILY_ECONOMIC_SUMMARY: materialize_economic_summary_presentation_projection_v1,
}


@dataclass(frozen=True)
class OctetFamilyResultV1:
    """Per-family orchestration outcome."""

    family_id: str
    status: str
    written: bool
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    payload_digest: str | None = None
    sibling_relative_path: str | None = None
    caller_object_provided: bool = False


@dataclass(frozen=True)
class OctetOrchestratorResultV1:
    """Bounded batch result for the presentation octet orchestrator."""

    archive_root: str
    generated_at: str | None
    family_results: tuple[OctetFamilyResultV1, ...]
    written_count: int
    skipped_count: int
    missing_source_count: int
    fail_closed_count: int
    blocked_count: int
    contract_ok: bool
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    orchestrator_authority_effect: str = ORCHESTRATOR_AUTHORITY_EFFECT
    dashboard_role: str = DASHBOARD_ROLE
    owner: str = OWNER

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable summary (deterministic key order via JSON dumps elsewhere)."""
        return {
            "archive_root": self.archive_root,
            "authority_effect": self.authority_effect,
            "blocked_count": self.blocked_count,
            "capability_id": self.capability_id,
            "contract_ok": self.contract_ok,
            "dashboard_role": self.dashboard_role,
            "fail_closed_count": self.fail_closed_count,
            "family_results": [asdict(item) for item in self.family_results],
            "generated_at": self.generated_at,
            "missing_source_count": self.missing_source_count,
            "orchestrator_authority_effect": self.orchestrator_authority_effect,
            "owner": self.owner,
            "skipped_count": self.skipped_count,
            "written_count": self.written_count,
        }


def _require_nonempty_str(value: object | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _empty_family(
    *,
    family_id: str,
    status: str,
    errors: tuple[str, ...],
    caller_object_provided: bool = False,
) -> OctetFamilyResultV1:
    return OctetFamilyResultV1(
        family_id=family_id,
        status=status,
        written=False,
        errors=errors,
        sibling_relative_path=SIBLING_PATH_BY_FAMILY.get(family_id),
        caller_object_provided=caller_object_provided,
    )


def _normalize_families(
    families: Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[OctetFamilyResultV1, ...]]:
    if families is None:
        return FAMILY_ORDER, ()

    selected: list[str] = []
    blocked: list[OctetFamilyResultV1] = []
    seen: set[str] = set()
    for raw in families:
        family_id = str(raw).strip()
        if not family_id:
            continue
        if family_id not in _MATERIALIZER_BY_FAMILY:
            blocked.append(
                _empty_family(
                    family_id=family_id,
                    status=STATUS_BLOCKED,
                    errors=(ERROR_UNKNOWN_FAMILY,),
                )
            )
            continue
        if family_id in seen:
            continue
        seen.add(family_id)
        selected.append(family_id)

    ordered = tuple(fid for fid in FAMILY_ORDER if fid in seen)
    return ordered, tuple(blocked)


def _override_map(
    per_family_overrides: Mapping[str, Mapping[str, Any]] | None,
    family_id: str,
) -> Mapping[str, Any]:
    if per_family_overrides is None:
        return {}
    raw = per_family_overrides.get(family_id)
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        return {"__invalid__": True}
    return raw


def _resolve_caller_object(
    *,
    family_id: str,
    top_level_inputs: Mapping[str, object | None],
    override: Mapping[str, Any],
) -> tuple[object | None, tuple[str, ...]]:
    if override.get("__invalid__") is True:
        return None, (ERROR_INVALID_OVERRIDE,)

    input_kwarg = _INPUT_KWARG_BY_FAMILY[family_id]
    if input_kwarg in override:
        return override[input_kwarg], ()
    if "input" in override:
        return override["input"], ()
    return top_level_inputs.get(input_kwarg), ()


def _resolve_timestamp_fields(
    *,
    override: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None,
    source_reference: str | None,
) -> tuple[str, str | None, str | None, str | None, tuple[str, ...]]:
    if override.get("__invalid__") is True:
        return generated_at, effective_at, source_reference, None, (ERROR_INVALID_OVERRIDE,)

    family_generated = override.get("generated_at", generated_at)
    resolved_generated = _require_nonempty_str(family_generated)
    if resolved_generated is None:
        return "", None, None, None, (ERROR_GENERATED_AT_REQUIRED,)

    family_effective = override.get("effective_at", effective_at)
    resolved_effective = (
        None if family_effective is None else _require_nonempty_str(family_effective)
    )
    if family_effective is not None and resolved_effective is None:
        return (
            resolved_generated,
            None,
            None,
            None,
            (ERROR_INVALID_OVERRIDE, "effective_at_must_be_nonempty_str_or_none"),
        )

    family_source_ref = override.get("source_reference", source_reference)
    resolved_source_ref = (
        None if family_source_ref is None else _require_nonempty_str(family_source_ref)
    )
    if family_source_ref is not None and resolved_source_ref is None:
        return (
            resolved_generated,
            resolved_effective,
            None,
            None,
            (ERROR_INVALID_OVERRIDE, "source_reference_must_be_nonempty_str_or_none"),
        )

    saved_at_raw = override.get("saved_at")
    resolved_saved_at = None if saved_at_raw is None else _require_nonempty_str(saved_at_raw)
    if saved_at_raw is not None and resolved_saved_at is None:
        return (
            resolved_generated,
            resolved_effective,
            resolved_source_ref,
            None,
            (ERROR_INVALID_OVERRIDE, "saved_at_must_be_nonempty_str_or_none"),
        )

    return (
        resolved_generated,
        resolved_effective,
        resolved_source_ref,
        resolved_saved_at,
        (),
    )


def _map_materializer_status(status: str) -> str:
    if status == STATUS_WRITTEN:
        return STATUS_WRITTEN
    if status == STATUS_MISSING_SOURCE:
        return STATUS_MISSING_SOURCE
    if status == STATUS_FAIL_CLOSED:
        return STATUS_FAIL_CLOSED
    # Preserve unknown materializer statuses as fail-closed for the batch report.
    return STATUS_FAIL_CLOSED


def _dispatch_family(
    *,
    archive_root: Path,
    family_id: str,
    caller_object: object | None,
    generated_at: str,
    effective_at: str | None,
    source_reference: str | None,
    saved_at: str | None,
) -> OctetFamilyResultV1:
    caller_provided = caller_object is not None
    sibling_relative = SIBLING_PATH_BY_FAMILY[family_id]

    if family_id == FAMILY_SAFETY_AUTHORITY and caller_object is None:
        return _empty_family(
            family_id=family_id,
            status=STATUS_SKIPPED,
            errors=(ERROR_SAFETY_CALLER_OBJECT_REQUIRED,),
            caller_object_provided=False,
        )

    materializer = _MATERIALIZER_BY_FAMILY[family_id]
    input_kwarg = _INPUT_KWARG_BY_FAMILY[family_id]
    kwargs: dict[str, Any] = {
        input_kwarg: caller_object,
        "generated_at": generated_at,
        "effective_at": effective_at,
        "source_reference": source_reference,
    }
    if family_id == FAMILY_SAFETY_AUTHORITY:
        kwargs["saved_at"] = saved_at

    result = materializer(archive_root, **kwargs)
    status = _map_materializer_status(str(getattr(result, "status", STATUS_FAIL_CLOSED)))
    errors = tuple(str(item) for item in getattr(result, "errors", ()) or ())
    projection_path = getattr(result, "projection_path", None)
    if projection_path is not None:
        projection_path = str(projection_path)
        try:
            relative = (
                Path(projection_path).resolve().relative_to(archive_root.resolve()).as_posix()
            )
        except ValueError:
            relative = None
        if relative not in ALLOWED_PROJECTION_RELATIVE_PATHS:
            return OctetFamilyResultV1(
                family_id=family_id,
                status=STATUS_FAIL_CLOSED,
                written=False,
                errors=errors + ("OCTET_ORCHESTRATOR_UNEXPECTED_PROJECTION_PATH",),
                projection_path=projection_path,
                source_path=(
                    None
                    if getattr(result, "source_path", None) is None
                    else str(result.source_path)
                ),
                payload_digest=getattr(result, "payload_digest", None),
                sibling_relative_path=sibling_relative,
                caller_object_provided=caller_provided,
            )

    return OctetFamilyResultV1(
        family_id=family_id,
        status=status,
        written=bool(getattr(result, "written", False)),
        errors=errors,
        projection_path=projection_path,
        source_path=(
            None if getattr(result, "source_path", None) is None else str(result.source_path)
        ),
        payload_digest=getattr(result, "payload_digest", None),
        sibling_relative_path=sibling_relative,
        caller_object_provided=caller_provided,
    )


def run_presentation_projection_octet_orchestrator_v1(
    *,
    archive_root: str | Path,
    generated_at: str | None,
    families: Sequence[str] | None = None,
    dynamic_scope: object | None = None,
    regime_bull_bear_switch: object | None = None,
    evidence: object | None = None,
    display: object | None = None,
    safety_authority: object | None = None,
    risk_sizing_capital: object | None = None,
    execution_reconciliation: object | None = None,
    economic_summary: object | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
    per_family_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> OctetOrchestratorResultV1:
    """Run the bounded presentation octet orchestrator against an explicit archive root.

    Caller must provide ``generated_at``. Materializers perform atomic writes only.
    Partial success is allowed: one family SKIPPED/MISSING_SOURCE/FAIL_CLOSED does
    not abort the remaining selected families.
    """
    if archive_root is None or (isinstance(archive_root, str) and not archive_root.strip()):
        return OctetOrchestratorResultV1(
            archive_root="",
            generated_at=_require_nonempty_str(generated_at),
            family_results=(
                _empty_family(
                    family_id="*",
                    status=STATUS_FAIL_CLOSED,
                    errors=(ERROR_ARCHIVE_ROOT_REQUIRED,),
                ),
            ),
            written_count=0,
            skipped_count=0,
            missing_source_count=0,
            fail_closed_count=1,
            blocked_count=0,
            contract_ok=False,
        )

    root = Path(archive_root).expanduser().resolve()
    selected, blocked_results = _normalize_families(families)
    top_level_inputs: dict[str, object | None] = {
        "dynamic_scope": dynamic_scope,
        "regime_bull_bear_switch": regime_bull_bear_switch,
        "evidence": evidence,
        "display": display,
        "safety_authority": safety_authority,
        "risk_sizing_capital": risk_sizing_capital,
        "execution_reconciliation": execution_reconciliation,
        "economic_summary": economic_summary,
    }

    batch_generated = _require_nonempty_str(generated_at)
    family_results: list[OctetFamilyResultV1] = list(blocked_results)

    if batch_generated is None:
        for family_id in selected:
            family_results.append(
                _empty_family(
                    family_id=family_id,
                    status=STATUS_FAIL_CLOSED,
                    errors=(ERROR_GENERATED_AT_REQUIRED,),
                    caller_object_provided=top_level_inputs.get(_INPUT_KWARG_BY_FAMILY[family_id])
                    is not None,
                )
            )
    else:
        for family_id in selected:
            override = _override_map(per_family_overrides, family_id)
            caller_object, input_errors = _resolve_caller_object(
                family_id=family_id,
                top_level_inputs=top_level_inputs,
                override=override,
            )
            if input_errors:
                family_results.append(
                    _empty_family(
                        family_id=family_id,
                        status=STATUS_FAIL_CLOSED,
                        errors=input_errors,
                        caller_object_provided=False,
                    )
                )
                continue

            (
                family_generated,
                family_effective,
                family_source_ref,
                family_saved_at,
                ts_errors,
            ) = _resolve_timestamp_fields(
                override=override,
                generated_at=batch_generated,
                effective_at=effective_at,
                source_reference=source_reference,
            )
            if ts_errors:
                family_results.append(
                    _empty_family(
                        family_id=family_id,
                        status=STATUS_FAIL_CLOSED,
                        errors=ts_errors,
                        caller_object_provided=caller_object is not None,
                    )
                )
                continue

            family_results.append(
                _dispatch_family(
                    archive_root=root,
                    family_id=family_id,
                    caller_object=caller_object,
                    generated_at=family_generated,
                    effective_at=family_effective,
                    source_reference=family_source_ref,
                    saved_at=family_saved_at,
                )
            )

    written_count = sum(1 for item in family_results if item.status == STATUS_WRITTEN)
    skipped_count = sum(1 for item in family_results if item.status == STATUS_SKIPPED)
    missing_source_count = sum(1 for item in family_results if item.status == STATUS_MISSING_SOURCE)
    fail_closed_count = sum(1 for item in family_results if item.status == STATUS_FAIL_CLOSED)
    blocked_count = sum(1 for item in family_results if item.status == STATUS_BLOCKED)
    # Contract-level failure only for missing archive root / unknown families /
    # batch generated_at absence. Per-family MISSING_SOURCE/SKIPPED remain success.
    contract_ok = blocked_count == 0 and not (batch_generated is None and bool(selected))

    return OctetOrchestratorResultV1(
        archive_root=str(root),
        generated_at=batch_generated,
        family_results=tuple(family_results),
        written_count=written_count,
        skipped_count=skipped_count,
        missing_source_count=missing_source_count,
        fail_closed_count=fail_closed_count,
        blocked_count=blocked_count,
        contract_ok=contract_ok,
    )


def allowed_projection_relative_paths_v1() -> frozenset[str]:
    """Expose the ratified projection write set for tests/gates."""
    return ALLOWED_PROJECTION_RELATIVE_PATHS


def projection_relative_path_for_family_v1(family_id: str) -> str | None:
    """Return the ratified projection relative path for a family id."""
    return PROJECTION_PATH_BY_FAMILY.get(family_id)
