"""Read the N5 assignment and Cap24 selection for an isolated Shadow entry."""

import json
from hashlib import sha256
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    require_i17_shadow_instrument_v1,
)
from src.ops.ranked_slot_run_source_v1 import (
    read_ranked_run_slot_v1,
    read_shadow_entry_admission_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    BINDING_RESULT_FILENAME,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    OWNER,
    SCHEMA_VERSION,
)
from src.ops.soph_slot_cap24_v1 import _active_binding


def inspect_ranked_shadow_entry_selection_v1(config_path, *, now, session_id=None, assignment=None):
    config = json.loads(Path(config_path).read_bytes())
    scope = require_i17_shadow_instrument_v1((config["native_instrument_id"],))
    if (
        scope.instrument_type != "SWAP"
        or (config["lane"], config["canonical_instrument_id"], config["surface"])
        != (scope.lane_id, scope.canonical_id, "SHADOW")
        or not config["session_id"]
        or (session_id is not None and config["session_id"] != session_id)
    ):
        raise ValueError("SHADOW_ENTRY_SESSION_SCOPE_MISMATCH")
    current = read_ranked_run_slot_v1(config)
    ref = current.reference()
    if assignment is not None and assignment.reference() != ref:
        raise ValueError("SHADOW_ENTRY_N5_ASSIGNMENT_CHANGED")
    admission = read_shadow_entry_admission_v1(config, current)
    blockers = []
    try:
        admission.require_current_v1(now)
    except ValueError as exc:
        blockers.append(str(exc))
    source = config.get("shadow_cap24")
    result = dict(
        session_id=config["session_id"],
        n5_assignment=ref,
        entry_admission=admission.reference(),
        cap24_evidence_sha256=None,
        blockers=blockers,
    )
    if source is None:
        blockers.append("SHADOW_ENTRY_CAP24_MISSING")
        return result
    try:
        root = Path(source["root"])
        if not root.is_absolute() or root != root.resolve():
            raise ValueError("SHADOW_ENTRY_CAP24_ROOT")
        manifest = (root / MANIFEST_FILENAME).read_bytes()
        files = {k: (root / k).read_bytes() for k in (EVIDENCE_FILENAME, BINDING_RESULT_FILENAME)}
        hashes = {k: sha256(v).hexdigest() for k, v in files.items()}
        if (
            set(manifest.decode().splitlines())
            != {f"{digest}  {name}" for name, digest in hashes.items()}
            or hashes[EVIDENCE_FILENAME] != source["evidence_sha256"]
            or manifest != (root / MANIFEST_FILENAME).read_bytes()
        ):
            raise ValueError("SHADOW_ENTRY_CAP24_MANIFEST_MISMATCH")
        evidence, receipt = (
            json.loads(files[k]) for k in (EVIDENCE_FILENAME, BINDING_RESULT_FILENAME)
        )
        gate = receipt["gate"]
        if (
            canonical_digest_v1(receipt) != source["result_digest"]
            or (receipt["session_id"], receipt["lane"], receipt["n5_assignment"])
            != (config["session_id"], scope.lane_id, ref)
            or receipt.get("entry_admission", ref) != admission.reference()
            or gate["evidence"] != evidence
            or (
                evidence["owner"],
                evidence["capability_id"],
                evidence["schema_version"],
                evidence["repository_sha"],
            )
            != (OWNER, CAPABILITY_ID, SCHEMA_VERSION, current.selection.repository_sha)
            or not all(gate[k] is True for k in ("ok", "alpha_enabled", "new_alpha_allowed"))
            or gate["hard_stop"] is not False
        ):
            raise ValueError("SHADOW_ENTRY_CAP24_SCOPE_MISMATCH")
        bound = _active_binding(gate, evidence)
        if (bound.selected_future_count, bound.max_positions_effective) != (1, 1):
            raise ValueError("SHADOW_ENTRY_SINGLE_POSITION_REQUIRED")
        admission.require_binding_v1(bound)
        result["cap24_evidence_sha256"] = hashes[EVIDENCE_FILENAME]
    except (OSError, KeyError, TypeError, ValueError) as exc:
        blockers.append(f"SHADOW_ENTRY_CAP24_INVALID:{exc}")
    return result
