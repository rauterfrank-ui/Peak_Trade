"""Build sanitized child-process environments without mutating os.environ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    ALLOWLIST_KEYS,
    CLASSIFICATION_ALLOWED,
    ENVIRONMENT_POLICY_ID,
)
from src.ops.canonical_runtime_environment_contract_v1.digest_v1 import (
    effective_environment_digest_v1,
    parent_environment_digest_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.policy_v1 import (
    classify_parent_environment_v1,
)


class CanonicalEnvironmentContractError(ValueError):
    """Fail-closed O1 environment contract violation."""

    def __init__(self, blockers: list[str]) -> None:
        self.blockers = list(blockers)
        super().__init__(",".join(self.blockers))


@dataclass(frozen=True)
class EffectiveEnvironmentBuildResultV1:
    ok: bool
    environment_policy_id: str
    effective_environ: dict[str, str]
    parent_environment_digest: str
    effective_environment_digest: str
    allowed_keys: tuple[str, ...]
    stripped_keys: tuple[str, ...]
    rejected_keys: tuple[str, ...]
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "environment_policy_id": self.environment_policy_id,
            "parent_environment_digest": self.parent_environment_digest,
            "effective_environment_digest": self.effective_environment_digest,
            "allowed_keys": list(self.allowed_keys),
            "stripped_keys": list(self.stripped_keys),
            "rejected_keys": list(self.rejected_keys),
            "reason_codes": list(self.reason_codes),
            "blockers": list(self.blockers),
            "effective_env_keys": sorted(self.effective_environ.keys()),
            # Never embed effective values here — digests only.
        }


def build_effective_runtime_environment_v1(
    parent_environ: Mapping[str, str],
    *,
    require_policy_id: bool = False,
) -> EffectiveEnvironmentBuildResultV1:
    """Construct allowlist-only child env. Does not mutate ``os.environ``."""
    classification = classify_parent_environment_v1(parent_environ)
    parent_digest = parent_environment_digest_v1(parent_environ)
    blockers: list[str] = []
    for key in classification.rejected_keys:
        decision = next(d for d in classification.decisions if d.key == key)
        blockers.append(f"{decision.reason_code}:{key}")

    effective: dict[str, str] = {}
    for decision in classification.decisions:
        if decision.classification != CLASSIFICATION_ALLOWED:
            continue
        raw = parent_environ.get(decision.key)
        if raw is None:
            continue
        effective[decision.key] = str(raw)

    if (
        require_policy_id
        and effective.get("PEAK_TRADE_ENVIRONMENT_POLICY_ID") != ENVIRONMENT_POLICY_ID
    ):
        blockers.append("ENVIRONMENT_POLICY_ID_MISSING_OR_MISMATCH")

    # Always stamp policy id into effective env when build succeeds.
    if not blockers:
        effective["PEAK_TRADE_ENVIRONMENT_POLICY_ID"] = ENVIRONMENT_POLICY_ID
        # Drop keys that somehow left allowlist (defense).
        effective = {k: v for k, v in effective.items() if k in ALLOWLIST_KEYS}

    effective_digest = effective_environment_digest_v1(effective) if not blockers else ""
    ok = not blockers
    return EffectiveEnvironmentBuildResultV1(
        ok=ok,
        environment_policy_id=ENVIRONMENT_POLICY_ID,
        effective_environ=effective if ok else {},
        parent_environment_digest=parent_digest,
        effective_environment_digest=effective_digest,
        allowed_keys=classification.allowed_keys,
        stripped_keys=classification.stripped_keys,
        rejected_keys=classification.rejected_keys,
        reason_codes=classification.reason_codes,
        blockers=tuple(sorted(set(blockers))),
    )


def build_or_raise_effective_runtime_environment_v1(
    parent_environ: Mapping[str, str],
    *,
    require_policy_id: bool = False,
) -> dict[str, str]:
    result = build_effective_runtime_environment_v1(
        parent_environ, require_policy_id=require_policy_id
    )
    if not result.ok:
        raise CanonicalEnvironmentContractError(list(result.blockers))
    return dict(result.effective_environ)
