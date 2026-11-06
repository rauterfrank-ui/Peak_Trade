"""Preflight APIs for O1 — invoke before auth consumption / HTTP client construction."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.canonical_runtime_environment_contract_v1.builder_v1 import (
    CanonicalEnvironmentContractError,
    EffectiveEnvironmentBuildResultV1,
    build_effective_runtime_environment_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    ENVIRONMENT_POLICY_ID,
    NO_PROXY_POLICY,
    PROXY_POLICY,
    REJECTED_PROXY_KEYS,
)
from src.ops.canonical_runtime_environment_contract_v1.macos_portability_v1 import (
    MacOsPortabilityPreflightResultV1,
    run_macos_portability_preflight_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.policy_v1 import (
    classify_parent_environment_v1,
)


@dataclass(frozen=True)
class CanonicalEnvironmentPreflightResultV1:
    ok: bool
    environment_policy_id: str
    proxy_policy: str
    no_proxy_policy: str
    parent_environment_digest: str
    effective_environment_digest: str
    rejected_keys: tuple[str, ...]
    stripped_keys: tuple[str, ...]
    allowed_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    reason_codes: tuple[str, ...]
    macos_portability: dict[str, Any]
    stage: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "environment_policy_id": self.environment_policy_id,
            "proxy_policy": self.proxy_policy,
            "no_proxy_policy": self.no_proxy_policy,
            "parent_environment_digest": self.parent_environment_digest,
            "effective_environment_digest": self.effective_environment_digest,
            "rejected_keys": list(self.rejected_keys),
            "stripped_keys": list(self.stripped_keys),
            "allowed_keys": list(self.allowed_keys),
            "blockers": list(self.blockers),
            "reason_codes": list(self.reason_codes),
            "macos_portability": dict(self.macos_portability),
            "stage": self.stage,
        }


def collect_proxy_no_proxy_blockers_v1(
    environ: Optional[Mapping[str, str]] = None,
) -> list[str]:
    """Fail-closed when any proxy / NO_PROXY key is present (even empty after strip check).

    Presence of the key with any value (including whitespace) is forbidden.
    """
    env = environ if environ is not None else os.environ
    blockers: list[str] = []
    for key in sorted(REJECTED_PROXY_KEYS):
        if key in env and str(env.get(key) if env.get(key) is not None else "").strip() != "":
            blockers.append(f"PROXY_EGRESS_FORBIDDEN:{key}")
        elif key in env:
            # Key present but empty/whitespace — still unambiguous reject for NO_PROXY policy.
            blockers.append(f"PROXY_OR_NO_PROXY_KEY_PRESENT:{key}")
    return blockers


def assert_proxy_and_no_proxy_policy_fail_closed_v1(
    *,
    environ: Optional[Mapping[str, str]] = None,
) -> list[str]:
    return collect_proxy_no_proxy_blockers_v1(environ)


def run_canonical_environment_preflight_v1(
    parent_environ: Optional[Mapping[str, str]] = None,
    *,
    stage: str,
    include_macos_portability: bool = True,
    build_effective: bool = True,
) -> CanonicalEnvironmentPreflightResultV1:
    """Full O1 preflight. Does not mutate ``os.environ`` and starts no network session."""
    parent = dict(parent_environ) if parent_environ is not None else dict(os.environ)
    macos: MacOsPortabilityPreflightResultV1 | None = None
    blockers: list[str] = []
    if include_macos_portability:
        macos = run_macos_portability_preflight_v1()
        blockers.extend(macos.blockers)

    build: EffectiveEnvironmentBuildResultV1 | None = None
    if build_effective:
        build = build_effective_runtime_environment_v1(parent)
        blockers.extend(build.blockers)
        parent_digest = build.parent_environment_digest
        effective_digest = build.effective_environment_digest
        rejected = build.rejected_keys
        stripped = build.stripped_keys
        allowed = build.allowed_keys
        reasons = build.reason_codes
    else:
        classification = classify_parent_environment_v1(parent)
        proxy_blockers = collect_proxy_no_proxy_blockers_v1(parent)
        blockers.extend(proxy_blockers)
        from src.ops.canonical_runtime_environment_contract_v1.digest_v1 import (
            parent_environment_digest_v1,
        )

        parent_digest = parent_environment_digest_v1(parent)
        effective_digest = ""
        rejected = classification.rejected_keys
        stripped = classification.stripped_keys
        allowed = classification.allowed_keys
        reasons = classification.reason_codes

    ok = not blockers
    return CanonicalEnvironmentPreflightResultV1(
        ok=ok,
        environment_policy_id=ENVIRONMENT_POLICY_ID,
        proxy_policy=PROXY_POLICY,
        no_proxy_policy=NO_PROXY_POLICY,
        parent_environment_digest=parent_digest,
        effective_environment_digest=effective_digest,
        rejected_keys=tuple(rejected),
        stripped_keys=tuple(stripped),
        allowed_keys=tuple(allowed),
        blockers=tuple(sorted(set(blockers))),
        reason_codes=tuple(reasons),
        macos_portability=macos.to_dict() if macos is not None else {},
        stage=stage,
    )


def assert_preflight_before_authorization_consumption_v1(
    parent_environ: Optional[Mapping[str, str]] = None,
) -> CanonicalEnvironmentPreflightResultV1:
    result = run_canonical_environment_preflight_v1(
        parent_environ,
        stage="BEFORE_AUTHORIZATION_CONSUMPTION",
        build_effective=True,
    )
    if not result.ok:
        raise CanonicalEnvironmentContractError(list(result.blockers))
    return result


def assert_preflight_before_network_client_construction_v1(
    parent_environ: Optional[Mapping[str, str]] = None,
) -> CanonicalEnvironmentPreflightResultV1:
    result = run_canonical_environment_preflight_v1(
        parent_environ,
        stage="BEFORE_NETWORK_CLIENT_CONSTRUCTION",
        build_effective=True,
    )
    if not result.ok:
        raise CanonicalEnvironmentContractError(list(result.blockers))
    return result


def assert_preflight_before_ohlcv_http_client_construction_v1(
    parent_environ: Optional[Mapping[str, str]] = None,
) -> CanonicalEnvironmentPreflightResultV1:
    result = run_canonical_environment_preflight_v1(
        parent_environ,
        stage="BEFORE_OHLCV_HTTP_CLIENT_CONSTRUCTION",
        build_effective=True,
    )
    if not result.ok:
        raise CanonicalEnvironmentContractError(list(result.blockers))
    return result


def assert_http_client_proxy_env_clean_v1(
    *,
    environ: Optional[Mapping[str, str]] = None,
) -> None:
    """Lightweight gate for shared HTTP clients: reject proxy/NO_PROXY presence."""
    blockers = collect_proxy_no_proxy_blockers_v1(environ)
    if blockers:
        raise CanonicalEnvironmentContractError(blockers)
