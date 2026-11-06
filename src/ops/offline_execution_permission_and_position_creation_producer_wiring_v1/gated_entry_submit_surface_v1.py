"""Type-surface bind to the existing gated authenticated entry-submit client.

Imports the existing permit/client types only to prove the surface exists.
Never instantiates a live client, never calls post_entry_order, never
materializes secrets, and never sends HTTP.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    CURRENT_PRODUCTIVE_WIRE_REACHABLE,
    GATED_ENTRY_SUBMIT_CLIENT_TYPE_NAME,
    GATED_ENTRY_SUBMIT_METHOD_NAME,
    GATED_ENTRY_SUBMIT_PERMIT_KIND,
    GATED_ENTRY_SUBMIT_PERMIT_TYPE_NAME,
    GATED_ENTRY_SUBMIT_SURFACE_MODULE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
)


class GatedEntrySubmitSurfaceError(RuntimeError):
    """Fail-closed gated entry-submit surface bind violation."""


@dataclass(frozen=True)
class GatedEntrySubmitSurfaceBindingV1:
    module: str
    client_type_name: str
    permit_type_name: str
    method_name: str
    permit_kind: str
    client_type_qualname: str
    permit_type_qualname: str
    method_bound: bool
    http_invoked: bool
    secret_materialized: bool
    productive_wire_reachable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "client_type_name": self.client_type_name,
            "permit_type_name": self.permit_type_name,
            "method_name": self.method_name,
            "permit_kind": self.permit_kind,
            "client_type_qualname": self.client_type_qualname,
            "permit_type_qualname": self.permit_type_qualname,
            "method_bound": self.method_bound,
            "http_invoked": self.http_invoked,
            "secret_materialized": self.secret_materialized,
            "productive_wire_reachable": self.productive_wire_reachable,
        }


def bind_gated_entry_submit_surface_v1() -> GatedEntrySubmitSurfaceBindingV1:
    """Bind the existing gated POST type surface without invoking it."""
    if LiveCanaryHttpClientV1.__name__ != GATED_ENTRY_SUBMIT_CLIENT_TYPE_NAME:
        raise GatedEntrySubmitSurfaceError("GATED_ENTRY_CLIENT_TYPE_MISMATCH")
    if CanaryEntrySubmitPermitV1.__name__ != GATED_ENTRY_SUBMIT_PERMIT_TYPE_NAME:
        raise GatedEntrySubmitSurfaceError("GATED_ENTRY_PERMIT_TYPE_MISMATCH")
    method = getattr(LiveCanaryHttpClientV1, GATED_ENTRY_SUBMIT_METHOD_NAME, None)
    if method is None or not callable(method):
        raise GatedEntrySubmitSurfaceError("GATED_ENTRY_SUBMIT_METHOD_MISSING")
    if inspect.isclass(method):
        raise GatedEntrySubmitSurfaceError("GATED_ENTRY_SUBMIT_METHOD_NOT_CALLABLE")
    default_kind = CanaryEntrySubmitPermitV1.__dataclass_fields__["kind"].default
    if str(default_kind) != GATED_ENTRY_SUBMIT_PERMIT_KIND:
        raise GatedEntrySubmitSurfaceError("GATED_ENTRY_PERMIT_KIND_MISMATCH")
    if CURRENT_PRODUCTIVE_WIRE_REACHABLE is not False:
        raise GatedEntrySubmitSurfaceError("PRODUCTIVE_WIRE_REACHABLE_STRUCTURALLY_FORBIDDEN")
    return GatedEntrySubmitSurfaceBindingV1(
        module=GATED_ENTRY_SUBMIT_SURFACE_MODULE,
        client_type_name=GATED_ENTRY_SUBMIT_CLIENT_TYPE_NAME,
        permit_type_name=GATED_ENTRY_SUBMIT_PERMIT_TYPE_NAME,
        method_name=GATED_ENTRY_SUBMIT_METHOD_NAME,
        permit_kind=GATED_ENTRY_SUBMIT_PERMIT_KIND,
        client_type_qualname=f"{LiveCanaryHttpClientV1.__module__}.{LiveCanaryHttpClientV1.__name__}",
        permit_type_qualname=(
            f"{CanaryEntrySubmitPermitV1.__module__}.{CanaryEntrySubmitPermitV1.__name__}"
        ),
        method_bound=True,
        http_invoked=False,
        secret_materialized=False,
        productive_wire_reachable=False,
    )
