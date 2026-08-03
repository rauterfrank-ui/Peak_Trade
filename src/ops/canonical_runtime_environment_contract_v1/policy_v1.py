"""Classify parent environment keys for O1 allowlist-first policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    ALLOWLIST_KEYS,
    CLASSIFICATION_ALLOWED,
    CLASSIFICATION_REJECTED,
    CLASSIFICATION_STRIPPED,
    CREDENTIAL_MARKER_EXACT,
    CREDENTIAL_UPPER_FRAGMENTS,
    ENVIRONMENT_POLICY_ID,
    REASON_ALLOWED,
    REASON_REJECTED_CREDENTIAL,
    REASON_REJECTED_POLICY_ID_MISMATCH,
    REASON_REJECTED_PROXY,
    REASON_REJECTED_UNEXPECTED,
    REASON_STRIPPED_SAFE_OS,
    REASON_STRIPPED_TOOLING,
    REJECTED_PROXY_KEYS,
    SAFE_TO_STRIP_EXACT,
    SAFE_TO_STRIP_PREFIXES,
    STRIP_EXACT_KEYS,
    STRIP_PREFIXES,
)


@dataclass(frozen=True)
class EnvKeyDecisionV1:
    key: str
    classification: str
    reason_code: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class EnvClassificationResultV1:
    decisions: tuple[EnvKeyDecisionV1, ...]
    allowed_keys: tuple[str, ...]
    stripped_keys: tuple[str, ...]
    rejected_keys: tuple[str, ...]
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.rejected_keys

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "allowed_keys": list(self.allowed_keys),
            "stripped_keys": list(self.stripped_keys),
            "rejected_keys": list(self.rejected_keys),
            "reason_codes": list(self.reason_codes),
            "decisions": [d.to_dict() for d in self.decisions],
        }


def _is_credential_marker(key: str) -> bool:
    upper = key.upper()
    if upper in CREDENTIAL_MARKER_EXACT or key in CREDENTIAL_MARKER_EXACT:
        return True
    if upper.startswith("OKX_") and any(frag in upper for frag in CREDENTIAL_UPPER_FRAGMENTS):
        return True
    if upper.startswith("EXCHANGE_") and any(frag in upper for frag in CREDENTIAL_UPPER_FRAGMENTS):
        return True
    return False


def _is_strip_tooling(key: str) -> bool:
    if key in STRIP_EXACT_KEYS:
        return True
    return any(key.startswith(prefix) for prefix in STRIP_PREFIXES)


def _is_safe_to_strip(key: str) -> bool:
    if key in SAFE_TO_STRIP_EXACT:
        return True
    if key.startswith("LC_") and key != "LC_ALL":
        return True
    return any(key.startswith(prefix) for prefix in SAFE_TO_STRIP_PREFIXES)


def classify_env_key_v1(key: str, *, value: str | None = None) -> EnvKeyDecisionV1:
    _ = value  # values never influence classification reason text (except policy-id handled by caller)
    if key in REJECTED_PROXY_KEYS:
        return EnvKeyDecisionV1(
            key=key,
            classification=CLASSIFICATION_REJECTED,
            reason_code=REASON_REJECTED_PROXY,
        )
    if _is_credential_marker(key):
        return EnvKeyDecisionV1(
            key=key,
            classification=CLASSIFICATION_REJECTED,
            reason_code=REASON_REJECTED_CREDENTIAL,
        )
    if key in ALLOWLIST_KEYS:
        return EnvKeyDecisionV1(
            key=key,
            classification=CLASSIFICATION_ALLOWED,
            reason_code=REASON_ALLOWED,
        )
    if _is_strip_tooling(key):
        return EnvKeyDecisionV1(
            key=key,
            classification=CLASSIFICATION_STRIPPED,
            reason_code=REASON_STRIPPED_TOOLING,
        )
    if _is_safe_to_strip(key):
        return EnvKeyDecisionV1(
            key=key,
            classification=CLASSIFICATION_STRIPPED,
            reason_code=REASON_STRIPPED_SAFE_OS,
        )
    return EnvKeyDecisionV1(
        key=key,
        classification=CLASSIFICATION_REJECTED,
        reason_code=REASON_REJECTED_UNEXPECTED,
    )


def classify_parent_environment_v1(
    parent_environ: Mapping[str, str],
) -> EnvClassificationResultV1:
    decisions: list[EnvKeyDecisionV1] = []
    allowed: list[str] = []
    stripped: list[str] = []
    rejected: list[str] = []
    reasons: list[str] = []

    for key in sorted(parent_environ.keys()):
        value = parent_environ.get(key)
        decision = classify_env_key_v1(key, value=value)
        if (
            key == "PEAK_TRADE_ENVIRONMENT_POLICY_ID"
            and decision.classification == CLASSIFICATION_ALLOWED
            and str(value or "").strip()
            and str(value).strip() != ENVIRONMENT_POLICY_ID
        ):
            decision = EnvKeyDecisionV1(
                key=key,
                classification=CLASSIFICATION_REJECTED,
                reason_code=REASON_REJECTED_POLICY_ID_MISMATCH,
            )
        # Reject non-empty proxy values only — empty string still rejects per MUST_BE_ABSENT
        # (key presence is enough for proxy/NO_PROXY keys).
        decisions.append(decision)
        reasons.append(f"{decision.reason_code}:{key}")
        if decision.classification == CLASSIFICATION_ALLOWED:
            allowed.append(key)
        elif decision.classification == CLASSIFICATION_STRIPPED:
            stripped.append(key)
        else:
            rejected.append(key)

    return EnvClassificationResultV1(
        decisions=tuple(decisions),
        allowed_keys=tuple(allowed),
        stripped_keys=tuple(stripped),
        rejected_keys=tuple(rejected),
        reason_codes=tuple(reasons),
    )
