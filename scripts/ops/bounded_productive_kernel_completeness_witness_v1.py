#!/usr/bin/env python3
"""Independent bounded productive-kernel completeness witness for CSIA.

AUTHORITY_EFFECT=NONE. Navigation/proof only; does not trade or authorize execution.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WITNESS_PATH = (
    REPO_ROOT
    / "config/governance/current_system_interaction_authority_map_v1"
    / "bounded_productive_kernel_completeness_witness_v1.json"
)
CSIA_SOURCE_PATH = (
    REPO_ROOT / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)


def load_witness_v1(path: Path | None = None) -> dict:
    return json.loads((path or WITNESS_PATH).read_text(encoding="utf-8"))


def load_csia_source_v1(path: Path | None = None) -> dict:
    return json.loads((path or CSIA_SOURCE_PATH).read_text(encoding="utf-8"))


def verify_bounded_kernel_completeness_v1(
    *,
    witness: dict | None = None,
    csia: dict | None = None,
) -> list[str]:
    witness = witness if witness is not None else load_witness_v1()
    csia = csia if csia is not None else load_csia_source_v1()
    errors: list[str] = []
    domain_ids = {str(d["id"]) for d in csia.get("domains", [])}
    edges = list(csia.get("edges", []))
    edge_by_id = {str(e["id"]): e for e in edges}
    edge_pairs = {(str(e["from_domain"]), str(e["to_domain"])) for e in edges}

    for obj_id in witness.get("bounded_kernel_object_ids", []):
        if str(obj_id) not in domain_ids:
            errors.append(f"missing_domain:{obj_id}")

    for edge_id in witness.get("bounded_kernel_required_edge_ids", []):
        if str(edge_id) not in edge_by_id:
            errors.append(f"missing_edge_id:{edge_id}")
    for spec in witness.get("bounded_kernel_required_edges", []):
        from_d = str(spec["from_domain"])
        to_d = str(spec["to_domain"])
        spec_edge_id = spec.get("edge_id")
        if spec_edge_id is not None:
            edge = edge_by_id.get(str(spec_edge_id))
            if edge is None:
                errors.append(f"missing_edge_id:{spec_edge_id}")
            elif edge["from_domain"] != from_d or edge["to_domain"] != to_d:
                errors.append(f"edge_id_endpoint_mismatch:{spec_edge_id}")
        elif (from_d, to_d) not in edge_pairs:
            errors.append(f"missing_edge_pair:{from_d}->{to_d}")

    for edge in edges:
        if edge["from_domain"] not in domain_ids or edge["to_domain"] not in domain_ids:
            errors.append(f"dangling_edge:{edge.get('id')}")

    return errors


def main() -> int:
    errors = verify_bounded_kernel_completeness_v1()
    if errors:
        print("\n".join(errors))
        return 1
    print("BOUNDED_KERNEL_COMPLETENESS_WITNESS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
