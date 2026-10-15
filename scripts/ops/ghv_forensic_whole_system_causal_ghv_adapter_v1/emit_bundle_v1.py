"""Emit deterministic inspection bundle artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.contracts_v1 import (
    ADAPTER_AUTHORITY,
    ADAPTER_OWNER,
    INSPECTION_BUNDLE_SCHEMA,
    INSPECTION_MANIFEST_SCHEMA,
    OUTPUT_WRITE_FAILURE,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.types_v1 import (
    InspectionResultV1,
)


def _fail(result: InspectionResultV1, semantic: str, msg: str) -> InspectionResultV1:
    result.ok = False
    result.failure_semantic = semantic
    result.errors.append(msg)
    return result


def _canonical_json_bytes(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def emit_inspection_bundle_v1(
    *,
    inspection: InspectionResultV1,
    wp2a_output_dir: Path,
    output_dir: Path,
) -> InspectionResultV1:
    out = inspection
    bundle_doc = dict(out.bundle_doc)
    bundle_doc["schema_version"] = INSPECTION_BUNDLE_SCHEMA
    bundle_bytes = _canonical_json_bytes(bundle_doc)
    bundle_hash = hashlib.sha256(bundle_bytes).hexdigest()

    manifest_doc: dict[str, Any] = {
        "schema_version": INSPECTION_MANIFEST_SCHEMA,
        "authority": ADAPTER_AUTHORITY,
        "owner": ADAPTER_OWNER,
        "wp2a_output_dir": str(wp2a_output_dir.resolve()),
        "input_artifact_sha256": bundle_doc.get("input_artifact_sha256") or {},
        "inspection_bundle_sha256": bundle_hash,
        "output_artifacts": {
            "inspection_bundle.v1.json": bundle_hash,
        },
        "CURRENT_CAUSAL_GRAPH_VERIFIED": (bundle_doc.get("authority_assessment") or {}).get(
            "CURRENT_CAUSAL_GRAPH_VERIFIED"
        ),
        "PRODUCTIVE_TRADING_AUTHORITY": False,
    }

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "inspection_bundle.v1.json").write_bytes(bundle_bytes)
        (output_dir / "inspection_manifest.v1.json").write_bytes(
            _canonical_json_bytes(manifest_doc)
        )
    except OSError as exc:
        return _fail(out, OUTPUT_WRITE_FAILURE, f"output_write_failed:{exc}")

    out.ok = True
    out.output_dir = output_dir
    out.bundle_doc = bundle_doc
    out.manifest_doc = manifest_doc
    return out
