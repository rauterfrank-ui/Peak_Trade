"""Canonical typed config loader — no silent fallback for required keys."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CONFIG_TOML_SECTION,
    CONFIG_VERSION,
    EXPECTED_ADVERSE_EXIT_DISTANCE,
    EXPECTED_CONFIRMATION_EPOCHS,
    EXPECTED_REVERSAL_DISTANCE,
    EXPECTED_UP_DISTANCE,
    REQUIRED_CONFIG_KEYS,
    canonical_config_path_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    CanonicalDecisionRuntimeConfigV1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.reason_codes_v1 import (
    DecisionConfigFailureCodeV1,
)


class DecisionConfigError(RuntimeError):
    def __init__(self, code: DecisionConfigFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


def _require_key(section: Mapping[str, Any], key: str) -> Any:
    if key not in section:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_KEY_MISSING,
            key,
        )
    return section[key]


def _require_int(section: Mapping[str, Any], key: str) -> int:
    raw = _require_key(section, key)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_TYPE_INVALID,
            f"{key}:expected_int:got={type(raw).__name__}",
        )
    if raw <= 0:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_VALUE_INVALID,
            f"{key}:must_be_positive",
        )
    return int(raw)


def _require_float(section: Mapping[str, Any], key: str) -> float:
    raw = _require_key(section, key)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_TYPE_INVALID,
            f"{key}:expected_float:got={type(raw).__name__}",
        )
    value = float(raw)
    if value <= 0.0 or value != value:  # NaN check
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_VALUE_INVALID,
            f"{key}:must_be_positive_finite",
        )
    return value


def _require_str(section: Mapping[str, Any], key: str) -> str:
    raw = _require_key(section, key)
    if not isinstance(raw, str) or not raw.strip():
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_TYPE_INVALID,
            f"{key}:expected_nonempty_str",
        )
    return str(raw)


def validate_effective_parity_v1(cfg: CanonicalDecisionRuntimeConfigV1) -> None:
    """Fail-closed if ownership migration would alter productive numerics."""
    checks = (
        ("confirmation_epochs", int(cfg.confirmation_epochs), EXPECTED_CONFIRMATION_EPOCHS),
        ("up_distance", float(cfg.up_distance), EXPECTED_UP_DISTANCE),
        (
            "adverse_exit_distance",
            float(cfg.adverse_exit_distance),
            EXPECTED_ADVERSE_EXIT_DISTANCE,
        ),
        ("reversal_distance", float(cfg.reversal_distance), EXPECTED_REVERSAL_DISTANCE),
    )
    for name, actual, expected in checks:
        if actual != expected:
            raise DecisionConfigError(
                DecisionConfigFailureCodeV1.CONFIG_EFFECTIVE_VALUE_DRIFT,
                f"{name}:actual={actual}:expected={expected}",
            )


def load_canonical_decision_runtime_config_v1(
    path: Path | None = None,
    *,
    enforce_frozen_effective_values: bool = True,
) -> CanonicalDecisionRuntimeConfigV1:
    """Load typed config from the canonical TOML owner. No silent defaults."""
    config_path = Path(path) if path is not None else canonical_config_path_v1()
    if not config_path.is_file():
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_PATH_MISSING,
            str(config_path),
        )
    try:
        with config_path.open("rb") as fh:
            doc = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.STATE_CORRUPT,
            f"toml_decode:{exc}",
        ) from exc

    if CONFIG_TOML_SECTION not in doc or not isinstance(doc[CONFIG_TOML_SECTION], dict):
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_SECTION_MISSING,
            CONFIG_TOML_SECTION,
        )
    section = doc[CONFIG_TOML_SECTION]
    for key in REQUIRED_CONFIG_KEYS:
        _require_key(section, key)

    config_version = _require_str(section, "config_version")
    schema_version = _require_str(section, "schema_version")
    if config_version != CONFIG_VERSION:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.CONFIG_VERSION_INCOMPATIBLE,
            f"actual={config_version}:expected={CONFIG_VERSION}",
        )

    cfg = CanonicalDecisionRuntimeConfigV1(
        config_version=config_version,
        schema_version=schema_version,
        confirmation_epochs=_require_int(section, "confirmation_epochs"),
        up_distance=_require_float(section, "up_distance"),
        adverse_exit_distance=_require_float(section, "adverse_exit_distance"),
        reversal_distance=_require_float(section, "reversal_distance"),
        owner=AUTHORITY_OWNER,
        source_path=str(config_path),
    )
    if enforce_frozen_effective_values:
        validate_effective_parity_v1(cfg)
    return cfg


def reject_legacy_bridge_fallback_v1(*, attempted: bool, detail: str = "") -> None:
    if attempted:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.LEGACY_BRIDGE_FALLBACK_ATTEMPT,
            detail or "local_bridge_fallback_forbidden",
        )


def reject_parallel_owner_conflict_v1(
    *,
    owner_a_value: float | int,
    owner_b_value: float | int,
    key: str,
) -> None:
    if owner_a_value != owner_b_value:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.PARALLEL_CONFIG_OWNER_CONFLICT,
            f"{key}:a={owner_a_value}:b={owner_b_value}",
        )
