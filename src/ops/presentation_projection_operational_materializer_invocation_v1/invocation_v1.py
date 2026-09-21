"""Governed operational invocation for presentation materializers (sibling-only).

CAPABILITY_ID=CAPABILITY_PRESENTATION_PROJECTION_OPERATIONAL_MATERIALIZER_INVOCATION_V1

Delegates to CAPABILITY_PRESENTATION_PROJECTION_OCTET_ORCHESTRATOR_V1 with caller
objects unset so each materializer loads its ratified durable sibling path only.
Does not run archive sibling exporters or touch trading / execution state.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.presentation_projection_octet_orchestrator_v1.orchestrator_v1 import (
    OctetOrchestratorResultV1,
    run_presentation_projection_octet_orchestrator_v1,
)
from src.ops.presentation_projection_operational_materializer_invocation_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DASHBOARD_ROLE,
    ERROR_ARCHIVE_ROOT_NOT_DIRECTORY,
    ERROR_ARCHIVE_ROOT_REQUIRED,
    ERROR_GENERATED_AT_REQUIRED,
    ERROR_OWNER_GO_REQUIRED,
    OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES,
    OWNER,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
    require_owner_go_v1,
)


@dataclass(frozen=True)
class OperationalMaterializerInvocationResultV1:
    """Bounded result for governed sibling-only materializer invocation."""

    ok: bool
    archive_root: str
    generated_at: str | None
    families: tuple[str, ...]
    orchestrator: OctetOrchestratorResultV1 | None
    errors: tuple[str, ...]
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    dashboard_role: str = DASHBOARD_ROLE
    owner: str = OWNER

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_root": self.archive_root,
            "authority_effect": self.authority_effect,
            "capability_id": self.capability_id,
            "dashboard_role": self.dashboard_role,
            "errors": list(self.errors),
            "families": list(self.families),
            "generated_at": self.generated_at,
            "ok": self.ok,
            "orchestrator": None if self.orchestrator is None else self.orchestrator.to_dict(),
            "owner": self.owner,
        }


def _require_nonempty_str(value: object | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def run_operational_presentation_materializer_invocation_v1(
    *,
    archive_root: str | Path,
    generated_at: str | None,
    owner_go: bool,
    families: Sequence[str] | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> OperationalMaterializerInvocationResultV1:
    """Invoke read-only presentation materializers against durable archive siblings.

    Requires explicit Owner-GO. ``generated_at`` must be caller-supplied (never
    invented). Missing or invalid siblings fail closed per family via the octet
    orchestrator; partial success is allowed when ``contract_ok`` holds.
    """
    archive_str = _require_nonempty_str(str(archive_root) if archive_root is not None else None)
    if archive_str is None:
        return OperationalMaterializerInvocationResultV1(
            ok=False,
            archive_root="",
            generated_at=_require_nonempty_str(generated_at),
            families=(),
            orchestrator=None,
            errors=(ERROR_ARCHIVE_ROOT_REQUIRED,),
        )

    try:
        require_owner_go_v1(owner_go=bool(owner_go))
    except ProductiveHostAuthorizationError:
        return OperationalMaterializerInvocationResultV1(
            ok=False,
            archive_root=archive_str,
            generated_at=_require_nonempty_str(generated_at),
            families=(),
            orchestrator=None,
            errors=(ERROR_OWNER_GO_REQUIRED,),
        )

    root = Path(archive_str).expanduser().resolve()
    if not root.is_dir():
        return OperationalMaterializerInvocationResultV1(
            ok=False,
            archive_root=str(root),
            generated_at=_require_nonempty_str(generated_at),
            families=(),
            orchestrator=None,
            errors=(ERROR_ARCHIVE_ROOT_NOT_DIRECTORY,),
        )

    generated = _require_nonempty_str(generated_at)
    if generated is None:
        return OperationalMaterializerInvocationResultV1(
            ok=False,
            archive_root=str(root),
            generated_at=None,
            families=(),
            orchestrator=None,
            errors=(ERROR_GENERATED_AT_REQUIRED,),
        )

    selected = (
        tuple(families) if families is not None else OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES
    )

    orchestrator = run_presentation_projection_octet_orchestrator_v1(
        archive_root=root,
        generated_at=generated,
        families=selected,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    ok = bool(orchestrator.contract_ok)
    return OperationalMaterializerInvocationResultV1(
        ok=ok,
        archive_root=str(root),
        generated_at=generated,
        families=selected,
        orchestrator=orchestrator,
        errors=(),
    )
