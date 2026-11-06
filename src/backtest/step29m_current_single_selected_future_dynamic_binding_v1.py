"""STEP29M post-selection instrument binding v1 (non-authorizing consumer).

Consumes persisted Cap 2.3 single selected future output only. Does not rank,
reselect, or reconstruct selection. Does not read ranking/universe snapshots.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID as SELECTION_CAPABILITY_ID,
    SELECTION_FILENAME,
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)

CONTRACT_VERSION = "step29m_current_single_selected_future_dynamic_binding_v1"
CONTRACT_OWNER = "backtest.step29m_current_single_selected_future_dynamic_binding_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/step29m_current_single_selected_future_dynamic_binding_v1.json"
)

DEFAULT_EVALUATION_CONFIG_TEMPLATE_REL = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_economic_evaluation_v1.json"
)

STEP29M_SELECTION_AUTHORITY = False
STEP29M_CONSUMES_POST_SELECTION_OUTPUT_ONLY = True

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_NATIVE_SUFFIX_RE = re.compile(r"^[A-Z0-9]+-[A-Z0-9]+-SWAP$")


class Step29mDynamicBindingError(ValueError):
    """Fail-closed STEP29M dynamic binding error."""


class Step29mDynamicBindingFailureCode(str, Enum):
    SELECTION_STATE_ROOT_MISSING = "SELECTION_STATE_ROOT_MISSING"
    SELECTION_LOAD_FAILED = "SELECTION_LOAD_FAILED"
    SELECTION_NOT_ACTIVE = "SELECTION_NOT_ACTIVE"
    SELECTION_INSTRUMENT_ID_MISSING = "SELECTION_INSTRUMENT_ID_MISSING"
    SELECTION_VENUE_NATIVE_ID_MISSING = "SELECTION_VENUE_NATIVE_ID_MISSING"
    SELECTION_IDENTITY_MISMATCH = "SELECTION_IDENTITY_MISMATCH"
    SELECTION_STALE = "SELECTION_STALE"
    SELECTION_FORBIDDEN_INSTRUMENT = "SELECTION_FORBIDDEN_INSTRUMENT"
    EVALUATION_CONFIG_TEMPLATE_MISSING = "EVALUATION_CONFIG_TEMPLATE_MISSING"


@dataclass(frozen=True)
class Step29mInstrumentBindingV1:
    """Instrument identity bound from post-selection output only."""

    canonical_instrument_id: str
    native_instrument_id: str
    selection_id: str
    selection_integrity_digest: str
    selection_state: str
    source_artifact: str
    consumption_class: str = "POST_SELECTION_OUTPUT_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "native_instrument_id": self.native_instrument_id,
            "selection_id": self.selection_id,
            "selection_integrity_digest": self.selection_integrity_digest,
            "selection_state": self.selection_state,
            "source_artifact": self.source_artifact,
            "consumption_class": self.consumption_class,
        }


@dataclass(frozen=True)
class Step29mPublicMarketDataIngestInstrumentBindingV1:
    """Explicit ingest binding derived from post-selection instrument binding."""

    native_instrument_id: str
    canonical_instrument_id: str
    selection_id: str
    selection_integrity_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "native_instrument_id": self.native_instrument_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "selection_id": self.selection_id,
            "selection_integrity_digest": self.selection_integrity_digest,
        }


def default_contract_config_path(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / CONTRACT_CONFIG_REL_PATH


def load_contract_config_v1(
    path: Optional[Path] = None,
    *,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    config_path = path or default_contract_config_path(repo_root)
    if not config_path.is_file():
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.EVALUATION_CONFIG_TEMPLATE_MISSING.value}:"
            f"{config_path}"
        )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Step29mDynamicBindingError("contract_config_not_object")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise Step29mDynamicBindingError("contract_version_mismatch")
    return payload


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _parse_rfc3339_to_unix(value: str) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc).timestamp()
    except ValueError:
        return None


def validate_post_selection_identity_fields_v1(
    *,
    instrument_id: str,
    venue_native_id: str,
) -> tuple[str, ...]:
    """Cross-field checks using fields already present on selection output."""
    reasons: list[str] = []
    canon = instrument_id.strip()
    native = venue_native_id.strip()
    if not canon:
        reasons.append(Step29mDynamicBindingFailureCode.SELECTION_INSTRUMENT_ID_MISSING.value)
    if not native:
        reasons.append(Step29mDynamicBindingFailureCode.SELECTION_VENUE_NATIVE_ID_MISSING.value)
    if canon and _contains_forbidden_token(canon):
        reasons.append(Step29mDynamicBindingFailureCode.SELECTION_FORBIDDEN_INSTRUMENT.value)
    if native and _contains_forbidden_token(native):
        reasons.append(Step29mDynamicBindingFailureCode.SELECTION_FORBIDDEN_INSTRUMENT.value)
    if native and not _NATIVE_SUFFIX_RE.fullmatch(native):
        reasons.append(Step29mDynamicBindingFailureCode.SELECTION_IDENTITY_MISMATCH.value)
    if canon and native:
        expected_suffix = native.lower()
        if not canon.endswith(f":{expected_suffix}"):
            reasons.append(Step29mDynamicBindingFailureCode.SELECTION_IDENTITY_MISMATCH.value)
    return tuple(reasons)


def resolve_step29m_instrument_binding_from_selection_state_root_v1(
    selection_state_root: Path,
    *,
    observed_at_unix: Optional[float] = None,
    require_manifest: bool = True,
) -> Step29mInstrumentBindingV1:
    """Load Cap 2.3 persisted selection and bind instrument identity fail-closed."""
    root = Path(selection_state_root).expanduser().resolve()
    if not root.is_dir():
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_STATE_ROOT_MISSING.value}:{root}"
        )

    loaded = load_and_validate_selection_v1(
        root,
        require_manifest=require_manifest,
    )
    if not loaded.ok or loaded.selection is None:
        codes = loaded.failure_codes or ("SELECTION_LOAD_FAILED",)
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_LOAD_FAILED.value}:"
            f"{','.join(codes)}:{loaded.detail}"
        )

    selection = loaded.selection
    if selection.capability_id != SELECTION_CAPABILITY_ID:
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_LOAD_FAILED.value}:capability_mismatch"
        )
    if selection.state == STATE_NO_SELECTION:
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_NOT_ACTIVE.value}:{selection.state}"
        )
    if selection.state != STATE_SELECTED_ACTIVE:
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_NOT_ACTIVE.value}:{selection.state}"
        )

    identity_reasons = validate_post_selection_identity_fields_v1(
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
    )
    if identity_reasons:
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_IDENTITY_MISMATCH.value}:"
            f"{','.join(identity_reasons)}"
        )

    now_unix = (
        float(observed_at_unix)
        if observed_at_unix is not None
        else datetime.now(timezone.utc).timestamp()
    )
    valid_until_unix = _parse_rfc3339_to_unix(selection.valid_until)
    if valid_until_unix is not None and now_unix > valid_until_unix:
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.SELECTION_STALE.value}:{selection.valid_until}"
        )

    artifact = str(root / SELECTION_FILENAME)
    return Step29mInstrumentBindingV1(
        canonical_instrument_id=selection.instrument_id.strip(),
        native_instrument_id=selection.venue_native_id.strip(),
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        selection_state=selection.state,
        source_artifact=artifact,
    )


def to_public_market_data_ingest_instrument_binding_v1(
    binding: Step29mInstrumentBindingV1,
) -> Step29mPublicMarketDataIngestInstrumentBindingV1:
    return Step29mPublicMarketDataIngestInstrumentBindingV1(
        native_instrument_id=binding.native_instrument_id,
        canonical_instrument_id=binding.canonical_instrument_id,
        selection_id=binding.selection_id,
        selection_integrity_digest=binding.selection_integrity_digest,
    )


def materialize_step29m_evaluation_config_for_instrument_binding_v1(
    instrument_binding: Step29mInstrumentBindingV1,
    *,
    template_config_path: Path,
    dataset_path: str,
    dataset_manifest_path: str,
) -> dict[str, Any]:
    """Overlay instrument/dataset identity onto the ratified evaluation template.

    Strategy and evaluation semantics remain on the template. Frozen historical
    dataset digests and period bindings are removed so CURRENT datasets bind
    explicitly without reusing archived identity.
    """
    if not template_config_path.is_file():
        raise Step29mDynamicBindingError(
            f"{Step29mDynamicBindingFailureCode.EVALUATION_CONFIG_TEMPLATE_MISSING.value}:"
            f"{template_config_path}"
        )
    cfg = json.loads(template_config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise Step29mDynamicBindingError("evaluation_template_not_object")

    cfg = copy.deepcopy(cfg)
    binding_section = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding_section, dict):
        raise Step29mDynamicBindingError("evaluation_template_binding_missing")

    binding_section = dict(binding_section)
    binding_section["canonical_instrument_id"] = instrument_binding.canonical_instrument_id
    binding_section["native_instrument_id"] = instrument_binding.native_instrument_id
    binding_section["dataset_path"] = dataset_path
    binding_section["dataset_manifest_path"] = dataset_manifest_path
    for frozen_key in (
        "expected_dataset_digest",
        "expected_manifest_digest",
        "development_partition_digest",
        "frozen_holdout_digest",
        "training_period",
        "validation_period",
        "out_of_sample_period",
    ):
        binding_section.pop(frozen_key, None)
    binding_section["current_selection_binding"] = {
        "consumption_class": instrument_binding.consumption_class,
        "selection_id": instrument_binding.selection_id,
        "selection_integrity_digest": instrument_binding.selection_integrity_digest,
        "source_artifact": instrument_binding.source_artifact,
    }
    cfg["real_admissible_futures_evaluation_binding_v1"] = binding_section
    return cfg


def resolve_evaluation_config_template_path_v1(
    repo_root: Path,
    contract: Optional[Mapping[str, Any]] = None,
) -> Path:
    payload = dict(contract or load_contract_config_v1(repo_root=repo_root))
    rel = str(
        payload.get("evaluation_config_template_path") or DEFAULT_EVALUATION_CONFIG_TEMPLATE_REL
    )
    return (repo_root / rel).resolve()
