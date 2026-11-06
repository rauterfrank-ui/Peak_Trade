"""Verify preserved source bytes and revision-bound anchors, never causal closure.

Run with scripts/pt. No imports of product code, source acquisition or runtime calls.
Historical instructions in the archived texts are inert evidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


PACKAGE = "docs/ops/evidence/architecture_reconstruction_alignment_v1_2026_11_04"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(repo: Path) -> dict[str, object]:
    package = repo / PACKAGE
    manifest = json.loads((package / "source_manifest.json").read_text())
    alignment = json.loads((package / "alignment.json").read_text())
    for relative, expected in manifest["files"].items():
        path = (package / relative).resolve()
        if not path.is_relative_to(package.resolve()) or _sha(path) != expected:
            raise ValueError(f"ARCHIVED_SOURCE_MISMATCH:{relative}")
    reports = alignment["source_reports"]
    if len(reports) != 99 or len({r["id"] for r in reports}) != 99:
        raise ValueError("SOURCE_REPORT_INVENTORY_MISMATCH")
    for report in reports:
        if _sha(package / report["snapshot"]) != report["sha256"]:
            raise ValueError(f"REPORT_HASH_MISMATCH:{report['id']}")
    known_evidence = {r["id"] for r in reports}
    anchors = 0
    for role in alignment["transitions_and_roles"]:
        if not set(role["historical_evidence_ids"]).issubset(known_evidence):
            raise ValueError(f"UNKNOWN_EVIDENCE:{role['id']}")
        if role["runtime_chain_proven"] or role["final_design_ratified_by_this_review"]:
            raise ValueError(f"UNSUPPORTED_PROOF_UPGRADE:{role['id']}")
        for anchor in role["current_anchors"]:
            path = (repo / anchor["path"]).resolve()
            if not path.is_relative_to(repo.resolve()) or _sha(path) != anchor["sha256"]:
                raise ValueError(f"CURRENT_SOURCE_CHANGED_REVIEW_REQUIRED:{anchor['path']}")
            nodes = [
                n
                for n in ast.walk(ast.parse(path.read_text()))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and n.name == anchor["symbol"]
            ]
            if len(nodes) != 1 or (nodes[0].lineno, nodes[0].end_lineno) != (
                anchor["line"],
                anchor["end_line"],
            ):
                raise ValueError(f"CURRENT_ANCHOR_MISMATCH:{anchor['symbol']}")
            anchors += 1
    inventory = json.loads((package / alignment["historical_contract_inventory"]).read_text())
    register = (package / "vault_registers/REGISTERS__contracts_edges.md.txt").read_text()
    lines = register.splitlines()
    for item in inventory["items"]:
        line = lines[item["source_line"] - 1]
        if hashlib.sha256(line.encode()).hexdigest() != item["source_row_sha256"]:
            raise ValueError(f"HISTORICAL_REGISTER_ROW_MISMATCH:{item['historical_id']}")
    if len(inventory["items"]) != inventory["rows"]:
        raise ValueError("HISTORICAL_REGISTER_COUNT_MISMATCH")
    protected = alignment["protected_learning_ledger"]
    if _sha(repo / protected["path"]) != protected["sha256"]:
        raise ValueError("ORIGINAL_LEARNING_LEDGER_CHANGED_REVIEW_REQUIRED")
    if (
        alignment["complete_architecture_restored"]
        or alignment["all_historical_causal_chains_verified"]
    ):
        raise ValueError("UNSUPPORTED_ARCHITECTURE_COMPLETION")
    cases = [
        case
        for name in ("integration_tests.xml", "intermediate_tests.xml")
        for case in ET.parse(package / name).getroot().iter("testcase")
    ]
    failed = sum(case.find("failure") is not None for case in cases)
    errors = sum(case.find("error") is not None for case in cases)
    skipped = sum(case.find("skipped") is not None for case in cases)
    return {
        "archive_integrity": "PASS",
        "current_source_anchors": "PASS",
        "source_reports": len(reports),
        "current_anchors": anchors,
        "historical_register_rows_preserved": inventory["rows"],
        "stored_local_regressions": {
            "passed": len(cases) - failed - errors - skipped,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
        },
        "causal_reconstruction": "INCOMPLETE",
        "semantic_runtime_proof": "NOT_ESTABLISHED_BY_THIS_VERIFIER",
        "runtime_authorization_effect": "NONE",
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parents[2]), indent=2))
