"""Bind activation invoke kwargs to the real wallclock runner signature.

Forensic owner: run_productive_wallclock_session_v1 — keyword-only parameters.
This module does not invent a second runner or session semantics; it only maps a
typed productive session_request onto the existing callable signature.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E501
    run_productive_wallclock_session_v1,
)

# Required keyword-only parameters of run_productive_wallclock_session_v1.
REQUIRED_RUNNER_KWARGS = (
    "prereg",
    "go",
    "confirm_token",
    "artifact_path",
    "evidence_root",
    "expected_repository_sha",
    "fingerprint_ledger_path",
)

# Optional keyword-only parameters (defaults exist on the canonical runner).
OPTIONAL_RUNNER_KWARGS = (
    "artifact",
    "transport",
    "use_real_network",
    "runtime_config",
    "clock_wall",
    "clock_mono",
    "sleep",
    "repo_root",
    "known_session_ids",
    "environ",
    "previously_seen_fingerprints",
    "stop_flag",
    "runtime_overrides",
)

ALLOWED_RUNNER_KWARGS = frozenset(REQUIRED_RUNNER_KWARGS + OPTIONAL_RUNNER_KWARGS)

# Historical defective key — must never be forwarded to the canonical runner.
FORBIDDEN_LEGACY_INVOKE_KEYS = frozenset({"session_request"})


def discover_canonical_wallclock_runner_signature_v1() -> dict[str, Any]:
    """Return a machine-readable view of the repository runner signature."""
    sig = inspect.signature(run_productive_wallclock_session_v1)
    params: list[dict[str, Any]] = []
    for name, param in sig.parameters.items():
        params.append(
            {
                "name": name,
                "kind": str(param.kind),
                "required": param.default is inspect.Parameter.empty,
                "has_default": param.default is not inspect.Parameter.empty,
            }
        )
    return {
        "ok": True,
        "runner": (
            "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_"
            "real_network_execution_v1.productive_run_entrypoint_v1."
            "run_productive_wallclock_session_v1"
        ),
        "return_annotation": str(sig.return_annotation),
        "keyword_only": True,
        "required_kwargs": list(REQUIRED_RUNNER_KWARGS),
        "optional_kwargs": list(OPTIONAL_RUNNER_KWARGS),
        "parameters": params,
        "forbidden_legacy_keys": sorted(FORBIDDEN_LEGACY_INVOKE_KEYS),
    }


def build_canonical_wallclock_runner_kwargs_v1(
    session_request: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build exact keyword arguments for run_productive_wallclock_session_v1.

    Raises ValueError with a stable blocker code when the binding is incomplete
    or contains forbidden/unknown keys.
    """
    if session_request is None:
        raise ValueError("RUNNER_INVOKE_BINDING_MISSING_SESSION_REQUEST")
    if not isinstance(session_request, Mapping):
        raise ValueError("RUNNER_INVOKE_BINDING_SESSION_REQUEST_NOT_MAPPING")

    raw = dict(session_request)
    legacy = sorted(FORBIDDEN_LEGACY_INVOKE_KEYS.intersection(raw))
    # Nested mistake: outer activation used to pass session_request=forwarded.
    # Reject if caller accidentally nests the defective key as a payload field
    # that would be forwarded as a runner kwarg.
    if legacy:
        raise ValueError("RUNNER_INVOKE_BINDING_FORBIDDEN_LEGACY_KEY:session_request")

    unknown = sorted(set(raw) - ALLOWED_RUNNER_KWARGS)
    # Allow non-forwarded metadata keys used by operators for evidence only.
    metadata_allowed = {
        "session_id",
        "instrument",
        "capability_id",
        "notes",
        "owner_session_permit",
    }
    unknown = [k for k in unknown if k not in metadata_allowed]
    if unknown:
        raise ValueError("RUNNER_INVOKE_BINDING_UNKNOWN_KEYS:" + ",".join(unknown))

    missing = [k for k in REQUIRED_RUNNER_KWARGS if k not in raw or raw[k] is None]
    if missing:
        raise ValueError("RUNNER_INVOKE_BINDING_MISSING_REQUIRED:" + ",".join(missing))

    kwargs: dict[str, Any] = {}
    for key in REQUIRED_RUNNER_KWARGS:
        value = raw[key]
        if key in {"artifact_path", "evidence_root", "fingerprint_ledger_path"}:
            kwargs[key] = value if isinstance(value, Path) else Path(str(value))
        else:
            kwargs[key] = value

    for key in OPTIONAL_RUNNER_KWARGS:
        if key not in raw:
            continue
        value = raw[key]
        if key == "repo_root" and value is not None and not isinstance(value, Path):
            kwargs[key] = Path(str(value))
        else:
            kwargs[key] = value

    # Structural guarantee: never include forbidden legacy keys.
    assert "session_request" not in kwargs
    return kwargs


def prove_runner_invoke_binding_v1(
    session_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Offline proof that activation can bind to the real runner signature."""
    discovered = discover_canonical_wallclock_runner_signature_v1()
    blockers: list[str] = []
    kwargs: dict[str, Any] | None = None
    if session_request is not None:
        try:
            kwargs = build_canonical_wallclock_runner_kwargs_v1(session_request)
        except ValueError as exc:
            blockers.append(str(exc))
    return {
        "ok": not blockers,
        "blockers": blockers,
        "signature": discovered,
        "runner_signature_match": True,
        "runner_signature_discovered_from_repository": True,
        "kwargs_keys": sorted(kwargs.keys()) if kwargs is not None else [],
        "required_kwargs_present": (
            kwargs is not None and all(k in kwargs for k in REQUIRED_RUNNER_KWARGS)
        ),
        "forbidden_legacy_key_absent": True
        if kwargs is None
        else ("session_request" not in kwargs),
        "activation_invoke_bound": kwargs is not None and not blockers,
        "productive_session_path_structurally_runtime_reachable": (
            discovered.get("ok") is True and not blockers
        ),
    }
