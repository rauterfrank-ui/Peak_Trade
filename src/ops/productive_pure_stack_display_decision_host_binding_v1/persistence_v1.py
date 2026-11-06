"""Atomic persistence for Pure-Stack display Decision bundles (runtime authority)."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1 import canonical_digest_v1
from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    BUNDLE_FILENAME,
    BUNDLE_STATE_VERSION,
    CAPABILITY_ID,
    OWNER,
    SCHEMA_VERSION,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.models_v1 import (
    PureStackDisplayDecisionBundleV1,
)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    return str(value)


def serialize_bundle_payload_v1(bundle: PureStackDisplayDecisionBundleV1) -> dict[str, Any]:
    payload = {
        "schema_version": bundle.schema_version,
        "state_version": BUNDLE_STATE_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "cycle_id": bundle.cycle_id,
        "cycle_index": int(bundle.cycle_index),
        "instrument_id": bundle.instrument_id,
        "trading_epoch": int(bundle.trading_epoch),
        "created_at": bundle.created_at,
        "status": bundle.status,
        "missing_authorities": list(bundle.missing_authorities),
        "blockers": list(bundle.blockers),
        "decisions": _jsonable(bundle.as_decision_mapping()),
    }
    digest = canonical_digest_v1(payload)
    payload["bundle_digest"] = digest
    return payload


def persist_pure_stack_display_decision_bundle_atomic_v1(
    *,
    state_root: Path,
    bundle: PureStackDisplayDecisionBundleV1,
) -> tuple[Path, str]:
    """Atomically persist the complete Decision bundle under the runtime state root."""
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    dest = root / BUNDLE_FILENAME
    payload = serialize_bundle_payload_v1(bundle)
    body = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=dest.name + ".", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, dest)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return dest, str(payload["bundle_digest"])


def load_pure_stack_display_decision_bundle_payload_v1(state_root: Path) -> dict[str, Any]:
    path = Path(state_root) / BUNDLE_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"bundle_missing:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != SCHEMA_VERSION:
        raise ValueError("bundle_schema_mismatch")
    if str(payload.get("capability_id") or "") != CAPABILITY_ID:
        raise ValueError("bundle_capability_mismatch")
    return payload
