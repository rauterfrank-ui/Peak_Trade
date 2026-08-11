"""Fail-closed LIVE venue binding for §11.13.4 (strictly separated from Demo/Testnet)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    FORBIDDEN_ENVIRONMENTS,
    FORBIDDEN_HOST_MARKERS,
    HARDCODED_PRODUCTION_HOST,
    OWNER_SUPPLIED_LIVE_HOST_REQUIRED,
    REQUIRED_ENVIRONMENT,
)


class LiveDryRunOrderPlanBindingError(RuntimeError):
    """Fail-closed Live dry-run order plan binding violation."""


@dataclass(frozen=True)
class LiveDryRunOrderPlanVenueBindingV1:
    environment: str
    venue: str
    entity: str
    region: str
    rest_host: str
    rest_base: str
    account_scope: str
    instrument_scope: str | None
    order_capability: bool = False
    demo_simulation_header_forbidden: bool = True
    cross_binding_demo_testnet_forbidden: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "venue": self.venue,
            "entity": self.entity,
            "region": self.region,
            "rest_host": self.rest_host,
            "rest_base": self.rest_base,
            "account_scope": self.account_scope,
            "instrument_scope": self.instrument_scope,
            "order_capability": self.order_capability,
            "demo_simulation_header_forbidden": self.demo_simulation_header_forbidden,
            "cross_binding_demo_testnet_forbidden": (self.cross_binding_demo_testnet_forbidden),
        }


def normalize_rest_host(rest_base_or_host: str) -> str:
    raw = str(rest_base_or_host or "").strip().lower()
    if not raw:
        raise LiveDryRunOrderPlanBindingError("REST_HOST_REQUIRED")
    if "://" in raw:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
    else:
        host = raw.split("/")[0].split(":")[0]
    if not host:
        raise LiveDryRunOrderPlanBindingError("REST_HOST_UNPARSEABLE")
    return host


def _assert_not_forbidden_host(host: str) -> None:
    for marker in FORBIDDEN_HOST_MARKERS:
        if marker in host:
            raise LiveDryRunOrderPlanBindingError(f"FORBIDDEN_NON_LIVE_HOST:{host}")


def _assert_environment(environment: str) -> None:
    env = str(environment or "").strip().upper()
    if env != REQUIRED_ENVIRONMENT:
        raise LiveDryRunOrderPlanBindingError(f"ENVIRONMENT_MUST_BE_LIVE:{env or '<empty>'}")
    if env in FORBIDDEN_ENVIRONMENTS:
        raise LiveDryRunOrderPlanBindingError(f"FORBIDDEN_ENVIRONMENT:{env}")


def reject_cross_binding_v1(
    *,
    live_environment: str,
    peer_environment: str,
    live_credential_class: str,
    peer_credential_class: str,
) -> None:
    """Fail-closed Live↔Demo/Testnet cross-binding reject."""
    live_env = str(live_environment or "").strip().upper()
    peer_env = str(peer_environment or "").strip().upper()
    if live_env != REQUIRED_ENVIRONMENT:
        raise LiveDryRunOrderPlanBindingError("CROSS_BINDING_LIVE_SIDE_INVALID")
    if peer_env in FORBIDDEN_ENVIRONMENTS or peer_env in {"DEMO", "TESTNET"}:
        raise LiveDryRunOrderPlanBindingError(f"CROSS_BINDING_LIVE_DEMO_TESTNET_REJECT:{peer_env}")
    live_klass = str(live_credential_class or "").strip().upper()
    peer_klass = str(peer_credential_class or "").strip().upper()
    if any(m in peer_klass for m in ("DEMO", "TESTNET", "SIMULATED", "PAPER")):
        raise LiveDryRunOrderPlanBindingError(
            f"CROSS_BINDING_PEER_CREDENTIAL_CLASS_REJECT:{peer_klass}"
        )
    if any(m in live_klass for m in ("DEMO", "TESTNET", "SIMULATED", "PAPER")):
        raise LiveDryRunOrderPlanBindingError(
            f"CROSS_BINDING_LIVE_CREDENTIAL_CLASS_CONTAMINATED:{live_klass}"
        )


def build_live_dry_run_order_plan_venue_binding_v1(
    *,
    environment: str,
    venue: str,
    entity: str,
    region: str,
    rest_host: str,
    rest_base: str | None = None,
    account_scope: str,
    instrument_scope: str | None = None,
    owner_declared_host_allowlist: tuple[str, ...] | list[str] | None = None,
) -> LiveDryRunOrderPlanVenueBindingV1:
    """Build LIVE binding. Missing owner host/venue fields fail closed."""
    _assert_environment(environment)
    venue_s = str(venue or "").strip()
    entity_s = str(entity or "").strip()
    region_s = str(region or "").strip()
    account_s = str(account_scope or "").strip()
    if not venue_s:
        raise LiveDryRunOrderPlanBindingError("VENUE_REQUIRED")
    if not entity_s:
        raise LiveDryRunOrderPlanBindingError("ENTITY_REQUIRED")
    if not region_s:
        raise LiveDryRunOrderPlanBindingError("REGION_REQUIRED")
    if not account_s:
        raise LiveDryRunOrderPlanBindingError("ACCOUNT_SCOPE_REQUIRED")
    if OWNER_SUPPLIED_LIVE_HOST_REQUIRED and not str(rest_host or "").strip():
        raise LiveDryRunOrderPlanBindingError("OWNER_SUPPLIED_LIVE_HOST_REQUIRED")
    if HARDCODED_PRODUCTION_HOST:
        # Preparation package intentionally leaves this empty.
        raise LiveDryRunOrderPlanBindingError("HARDCODED_PRODUCTION_HOST_MUST_REMAIN_EMPTY")

    host = normalize_rest_host(rest_host)
    _assert_not_forbidden_host(host)
    base = str(rest_base or "").strip() or f"https://{host}"
    base_host = normalize_rest_host(base)
    if base_host != host:
        raise LiveDryRunOrderPlanBindingError("REST_BASE_HOST_MISMATCH")

    allowlist = tuple(normalize_rest_host(h) for h in (owner_declared_host_allowlist or (host,)))
    if not allowlist:
        raise LiveDryRunOrderPlanBindingError("LIVE_HOST_ALLOWLIST_EMPTY")
    if host not in allowlist:
        raise LiveDryRunOrderPlanBindingError(f"LIVE_HOST_NOT_IN_ALLOWLIST:{host}")
    for allowed in allowlist:
        _assert_not_forbidden_host(allowed)

    return LiveDryRunOrderPlanVenueBindingV1(
        environment=REQUIRED_ENVIRONMENT,
        venue=venue_s,
        entity=entity_s,
        region=region_s,
        rest_host=host,
        rest_base=base.rstrip("/"),
        account_scope=account_s,
        instrument_scope=(str(instrument_scope).strip() or None)
        if instrument_scope is not None
        else None,
        order_capability=False,
    )


def validate_binding_against_payload_v1(
    binding: LiveDryRunOrderPlanVenueBindingV1,
    payload: Mapping[str, Any],
) -> None:
    """Reject Demo/Testnet payload markers against a LIVE binding."""
    env = str(payload.get("environment", "")).strip().upper()
    if env and env != REQUIRED_ENVIRONMENT:
        raise LiveDryRunOrderPlanBindingError(f"PAYLOAD_ENVIRONMENT_REJECT:{env}")
    host = str(payload.get("rest_host", "")).strip().lower()
    if host and normalize_rest_host(host) != binding.rest_host:
        raise LiveDryRunOrderPlanBindingError("PAYLOAD_HOST_MISMATCH")
    if bool(payload.get("order_capability")):
        raise LiveDryRunOrderPlanBindingError(
            "ORDER_CAPABILITY_FORBIDDEN_IN_LIVE_DRY_RUN_ORDER_PLAN_BINDING"
        )
