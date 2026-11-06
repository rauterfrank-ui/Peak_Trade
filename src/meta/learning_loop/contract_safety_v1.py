"""Shared offline safety validators for Self-Learning contract manifests v1."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

SCHEMA_VERSION_V1 = "1.0"

VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION = (
    "FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION"
)
VERDICT_TARGET_NOT_ALLOWED = "TARGET_NOT_ALLOWED"
VERDICT_FUTURES_SCOPE_VIOLATION = "FUTURES_SCOPE_VIOLATION"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_FORBIDDEN_TARGET_SEGMENTS = frozenset(
    {
        "master_v2",
        "double_play",
        "bull",
        "bear",
        "strategy",
        "signal",
        "entry",
        "exit",
        "sizing",
        "leverage",
        "stop",
        "stop_loss",
        "take_profit",
        "execution",
        "routing",
        "order",
        "risk_limit",
        "killswitch",
        "kill_switch",
        "capital_slot",
        "dynamic_scope",
        "state_switch",
        "runtime",
        "live",
        "arming",
    }
)

_FORBIDDEN_TARGET_EXACT = frozenset(
    {
        "portfolio.leverage",
        "macro.regime_weight",
        "risk.stop_loss",
    }
)

_FORBIDDEN_SCOPE_TOKENS = frozenset(
    {
        "btc",
        "xbt",
        "bitcoin",
        "spot",
        "synthetic_spot",
        "synthetic spot",
        "synthetic-spot",
    }
)

_CANONICAL_FORBIDDEN_SURFACES = (
    "master_v2",
    "double_play",
    "bull_bear_logic",
    "strategy_selection",
    "signal_generation",
    "entry_exit_logic",
    "position_sizing",
    "leverage",
    "stop_loss",
    "take_profit",
    "execution_semantics",
    "order_routing",
    "risk_limits",
    "killswitch",
    "capital_slot",
    "dynamic_scope",
    "state_switch",
)


class ValidationPhase(str, Enum):
    SCHEMA = "schema"
    SCHEMA_VERSION = "schema_version"
    FUTURES_SCOPE = "futures_scope"
    TARGET_POLICY = "target_policy"
    TRADING_LOGIC_IMMUTABILITY = "trading_logic_immutability"
    LINEAGE_REFERENCES = "lineage_references"
    CARDINALITY = "cardinality"
    INTEGRITY = "integrity"
    RESULT = "result"


@dataclass(frozen=True)
class ContractValidationResult:
    valid: bool
    phase: ValidationPhase
    errors: tuple[str, ...] = ()
    verdict: str | None = None


@dataclass(frozen=True)
class ContractSafetyError(ValueError):
    phase: ValidationPhase
    message: str
    verdict: str | None = None

    def __str__(self) -> str:
        if self.verdict:
            return f"{self.verdict}: {self.message}"
        return self.message


def canonical_futures_scope_ref() -> dict[str, Any]:
    return {
        "scope": "FUTURES_ONLY",
        "bitcoin_direction_allowed": False,
        "autonomous_live_promotion": False,
        "autonomous_order_authority": False,
    }


def canonical_trading_logic_immutability_ref() -> dict[str, Any]:
    return {
        "trading_logic_immutability": True,
        "forbidden_surfaces": list(_CANONICAL_FORBIDDEN_SURFACES),
        "reference_only": True,
        "mutable_trading_payloads_forbidden": True,
    }


def normalize_path_token(value: str) -> str:
    lowered = value.strip().lower()
    normalized = lowered.replace("/", ".").replace("\\", ".").replace("-", "_")
    while ".." in normalized:
        normalized = normalized.replace("..", ".")
    return normalized.strip(".")


def normalize_target_path(target: str) -> str:
    return normalize_path_token(target)


def is_valid_sha256_hex(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def is_valid_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(value))


def deterministic_json_dumps(payload: Mapping[str, Any] | Sequence[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_content_sha256(payload: Mapping[str, Any]) -> str:
    body = deterministic_json_dumps(payload)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _scope_value_contains_forbidden_token(value: str) -> str | None:
    normalized = normalize_path_token(value)
    for token in _FORBIDDEN_SCOPE_TOKENS:
        token_norm = normalize_path_token(token)
        if token_norm in normalized.split(".") or token_norm in normalized:
            return token
    if re.search(r"\bbtc\b", normalized):
        return "btc"
    if re.search(r"\bxbt\b", normalized):
        return "xbt"
    if "bitcoin" in normalized:
        return "bitcoin"
    if "spot" in normalized.split(".") or normalized.endswith(".spot") or normalized == "spot":
        return "spot"
    if "synthetic" in normalized and "spot" in normalized:
        return "synthetic_spot"
    return None


def _collect_scope_strings(ref: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("scope", "market", "symbol", "instrument", "venue", "product_class"):
        raw = ref.get(key)
        if isinstance(raw, str) and raw.strip():
            values.append(raw)
    metadata = ref.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("scope", "market", "symbol", "instrument", "venue", "product_class"):
            raw = metadata.get(key)
            if isinstance(raw, str) and raw.strip():
                values.append(raw)
    return values


def validate_futures_scope_ref(ref: Any) -> ContractValidationResult:
    if not isinstance(ref, dict):
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.FUTURES_SCOPE,
            errors=("futures_scope_ref must be an object",),
            verdict=VERDICT_FUTURES_SCOPE_VIOLATION,
        )

    expected = canonical_futures_scope_ref()
    for key, expected_value in expected.items():
        if ref.get(key) != expected_value:
            return ContractValidationResult(
                valid=False,
                phase=ValidationPhase.FUTURES_SCOPE,
                errors=(f"futures_scope_ref.{key} must equal canonical futures-only value",),
                verdict=VERDICT_FUTURES_SCOPE_VIOLATION,
            )

    for scope_value in _collect_scope_strings(ref):
        forbidden = _scope_value_contains_forbidden_token(scope_value)
        if forbidden is not None:
            return ContractValidationResult(
                valid=False,
                phase=ValidationPhase.FUTURES_SCOPE,
                errors=(f"futures_scope_ref contains forbidden scope token: {forbidden}",),
                verdict=VERDICT_FUTURES_SCOPE_VIOLATION,
            )

    return ContractValidationResult(valid=True, phase=ValidationPhase.FUTURES_SCOPE)


def validate_trading_logic_immutability_ref(ref: Any) -> ContractValidationResult:
    if not isinstance(ref, dict):
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.TRADING_LOGIC_IMMUTABILITY,
            errors=("trading_logic_immutability_ref must be an object",),
            verdict=VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
        )

    expected = canonical_trading_logic_immutability_ref()
    for key in (
        "trading_logic_immutability",
        "reference_only",
        "mutable_trading_payloads_forbidden",
    ):
        if ref.get(key) is not True:
            return ContractValidationResult(
                valid=False,
                phase=ValidationPhase.TRADING_LOGIC_IMMUTABILITY,
                errors=(f"trading_logic_immutability_ref.{key} must be true",),
                verdict=VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
            )

    forbidden_surfaces = ref.get("forbidden_surfaces")
    if forbidden_surfaces != expected["forbidden_surfaces"]:
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.TRADING_LOGIC_IMMUTABILITY,
            errors=("trading_logic_immutability_ref.forbidden_surfaces must match canonical list",),
            verdict=VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
        )

    return ContractValidationResult(
        valid=True,
        phase=ValidationPhase.TRADING_LOGIC_IMMUTABILITY,
    )


def classify_patch_target(target: str) -> tuple[bool, str | None]:
    if not isinstance(target, str) or not target.strip():
        return False, "patch target must be a non-empty string"

    normalized = normalize_target_path(target)
    if normalized in _FORBIDDEN_TARGET_EXACT:
        return False, normalized

    segments = [segment for segment in normalized.split(".") if segment]
    if not segments:
        return False, "patch target must contain at least one segment"

    for index, segment in enumerate(segments):
        if segment in _FORBIDDEN_TARGET_SEGMENTS:
            return False, segment
        if segment == "risk" and index + 1 < len(segments):
            return False, f"risk.{segments[index + 1]}"
        if (
            segment == "portfolio"
            and index + 1 < len(segments)
            and segments[index + 1] == "leverage"
        ):
            return False, "portfolio.leverage"

    if normalized.startswith("master_v2") or normalized.startswith("double_play"):
        return False, normalized.split(".")[0]

    return True, None


def validate_patch_target(target: str) -> ContractValidationResult:
    allowed, reason = classify_patch_target(target)
    if allowed:
        return ContractValidationResult(valid=True, phase=ValidationPhase.TARGET_POLICY)

    if reason in _FORBIDDEN_TARGET_SEGMENTS or reason in _FORBIDDEN_TARGET_EXACT:
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.TRADING_LOGIC_IMMUTABILITY,
            errors=(f"forbidden trading-logic patch target: {target}",),
            verdict=VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
        )

    return ContractValidationResult(
        valid=False,
        phase=ValidationPhase.TARGET_POLICY,
        errors=(f"target not allowed: {target}",),
        verdict=VERDICT_TARGET_NOT_ALLOWED,
    )


def validate_schema_version(value: Any) -> ContractValidationResult:
    if value != SCHEMA_VERSION_V1:
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.SCHEMA_VERSION,
            errors=(f"unsupported schema_version: {value!r}",),
        )
    return ContractValidationResult(valid=True, phase=ValidationPhase.SCHEMA_VERSION)


def validate_integrity_block(integrity: Any, *, expected_digest: str) -> ContractValidationResult:
    if not isinstance(integrity, dict):
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.INTEGRITY,
            errors=("integrity must be an object",),
        )
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.INTEGRITY,
            errors=("integrity.content_sha256 must be 64-char lowercase sha256 hex",),
        )
    if digest != expected_digest:
        return ContractValidationResult(
            valid=False,
            phase=ValidationPhase.INTEGRITY,
            errors=("integrity.content_sha256 mismatch",),
        )
    return ContractValidationResult(valid=True, phase=ValidationPhase.INTEGRITY)
