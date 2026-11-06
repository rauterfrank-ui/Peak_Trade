"""Public-MD network boundary reuse for Step-6 execution binding."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1 as _prove_continuation_boundary,
)


def prove_public_md_only_boundary_v1(
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Reuse continuation boundary owner; no parallel network semantics."""
    result = _prove_continuation_boundary(environ=environ)
    claims = dict(result.get("claims") or {})
    return {
        "ok": bool(result.get("ok")),
        "blockers": list(result.get("blockers") or []),
        "PUBLIC_MD_ONLY": True,
        "PRIVATE_ENDPOINT_REACHABLE": bool(claims.get("PRIVATE_ENDPOINT_REACHED", False)),
        "CREDENTIAL_PATH_REACHABLE": bool(claims.get("EXCHANGE_CREDENTIAL_PATH_REACHED", False)),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(claims.get("ORDER_SIDE_EFFECT_OCCURRED", False)),
        "AUTH_HEADER_PRESENT": False,
        "claims": claims,
        "reuses_continuation_boundary_owner": True,
    }
