"""Step-7 Campaign→Wallclock packaging adapter (signature-compatible).

Reuses the Step-4 canonical runner-invoke binder. Session identity for the
productive wallclock runner lives in ``prereg`` / ``go`` contracts (and
``evidence_root`` packaging paths). Campaign bookkeeping keys such as
``session_id`` / ``campaign_session_index`` are metadata only and must never
be forwarded as unexpected kwargs to ``run_productive_wallclock_session_v1``.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    ALLOWED_RUNNER_KWARGS,
    REQUIRED_RUNNER_KWARGS,
    build_canonical_wallclock_runner_kwargs_v1,
    discover_canonical_wallclock_runner_signature_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    CANONICAL_WALLCLOCK_RUNNER,
    OWNER,
)

# Campaign-local metadata — never part of the wallclock runner API contract.
CAMPAIGN_METADATA_KEYS = frozenset(
    {
        "session_id",
        "campaign_session_index",
        "campaign_planned_session_count",
        "instrument",
        "capability_id",
        "notes",
        "owner_session_permit",
        "per_session_packages",
    }
)

STEP7_WALLCLOCK_PACKAGING_OWNER = f"{OWNER}.wallclock_packaging_v1"
SESSION_IDENTITY_PACKAGING_PATH = (
    "prereg.session_id + go.session_id + evidence_root "
    "(via Step-4 build_canonical_wallclock_runner_kwargs_v1; "
    "campaign session_id is metadata-only)"
)


def strip_campaign_metadata_keys_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a shallow copy without campaign/bookkeeping metadata keys."""
    return {k: v for k, v in dict(payload).items() if k not in CAMPAIGN_METADATA_KEYS}


def filter_allowed_runner_kwargs_present_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only keys that exist on the canonical wallclock runner signature."""
    return {k: v for k, v in dict(payload).items() if k in ALLOWED_RUNNER_KWARGS}


def package_step7_wallclock_runner_kwargs_v1(
    session_package: Mapping[str, Any] | None,
    *,
    require_complete: bool,
) -> dict[str, Any]:
    """Package one session request into exact wallclock runner kwargs.

    When ``require_complete`` is True (productive callsite), reuse the Step-4
    binder which fail-closes on missing required keys / unknown keys.
    When False (injected test doubles), only filter to allowed signature keys.
    """
    raw = dict(session_package or {})
    # Ensure binder sees session_id as metadata (stripped), never as runner kwarg.
    filtered_meta = strip_campaign_metadata_keys_v1(raw)
    # Re-attach session_id only as binder metadata (allowed non-forwarded).
    if "session_id" in raw:
        binder_input = dict(filtered_meta)
        binder_input["session_id"] = raw["session_id"]
    else:
        binder_input = filtered_meta

    if require_complete:
        return build_canonical_wallclock_runner_kwargs_v1(binder_input)
    return filter_allowed_runner_kwargs_present_v1(binder_input)


def resolve_step7_session_package_v1(
    *,
    shared_wallclock_kwargs: Mapping[str, Any] | None,
    per_session_wallclock_packages: list[Mapping[str, Any]] | None,
    session_index: int,
    planned_session_count: int,
    campaign_session_id: str,
) -> dict[str, Any]:
    """Merge shared + per-session packaging; attach campaign metadata (non-forwarded)."""
    package: dict[str, Any] = dict(shared_wallclock_kwargs or {})
    packages = list(per_session_wallclock_packages or [])
    if packages:
        if len(packages) != int(planned_session_count):
            raise ValueError(
                "STEP7_PER_SESSION_PACKAGES_COUNT_MISMATCH:"
                f"expected={int(planned_session_count)}:got={len(packages)}"
            )
        idx = int(session_index) - 1
        package.update(dict(packages[idx]))
    package.setdefault("session_id", campaign_session_id)
    package["campaign_session_index"] = int(session_index)
    package["campaign_planned_session_count"] = int(planned_session_count)
    return package


def prove_step7_wallclock_packaging_bound_v1() -> dict[str, Any]:
    """Offline proof that Step-7 packaging reuses the canonical runner signature."""
    discovered = discover_canonical_wallclock_runner_signature_v1()
    blockers: list[str] = []
    if not discovered.get("ok"):
        blockers.append("CANONICAL_WALLCLOCK_SIGNATURE_DISCOVERY_FAILED")
    if "session_id" in list(REQUIRED_RUNNER_KWARGS):
        blockers.append("SESSION_ID_MUST_NOT_BE_REQUIRED_RUNNER_KWARG")
    if "session_id" in ALLOWED_RUNNER_KWARGS:
        blockers.append("SESSION_ID_MUST_NOT_BE_ALLOWED_RUNNER_KWARG")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "owner": STEP7_WALLCLOCK_PACKAGING_OWNER,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "session_identity_packaging_path": SESSION_IDENTITY_PACKAGING_PATH,
        "reuses_step4_runner_invoke_binding": True,
        "campaign_metadata_keys": sorted(CAMPAIGN_METADATA_KEYS),
        "required_runner_kwargs": list(REQUIRED_RUNNER_KWARGS),
        "allowed_runner_kwargs": sorted(ALLOWED_RUNNER_KWARGS),
        "signature": discovered,
        "NETWORK_SESSION_STARTED": False,
        "CONFIRM_TOKEN_MINTED": False,
    }
