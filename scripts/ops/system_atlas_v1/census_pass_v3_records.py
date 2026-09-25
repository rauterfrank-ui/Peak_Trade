"""FIND_COMPLETELY pass v3 ledger records. No disposition. No identity fusion."""

from __future__ import annotations

from typing import Any

from scripts.ops.system_atlas_v1.census_pass_v2_records import _psa, _record


def pass_v3_records() -> list[dict[str, Any]]:
    records = [
        _record(
            rid="RCN-000053",
            name="src/docs misplaced documentation tree",
            historical_names=["src/docs"],
            aliases=[],
            presence="CURRENTLY_PRESENT",
            discovered_from=["SURF:git_history_all_reachable", "SURF:current_tree"],
            evidence=[
                "docs/system_atlas/reconciliation/inventories/blob_scope_v3.yaml",
                "origin/main:src/docs",
            ],
            paths=["src/docs"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": (
                        "origin/main contains 13 markdown files under src/docs/. Unique historical "
                        "blobs for those paths were content-scanned in pass v3."
                    ),
                    "evidence": ["origin/main:src/docs"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": (
                        "Whether src/docs is a documentation component versus a misplaced dump "
                        "of files that also exist under docs/ remains uninvestigated."
                    ),
                    "evidence": [],
                },
            ],
            questions=["Distinct documentation set versus copies of docs/ files?"],
            notes=(
                "Path-family census from unique blob inventory. Not purpose-understood. "
                "Not fused with CAND:src_docs_workflow_notes or RCN-000049."
            ),
            relations=[
                _psa("RCN-000049", "overview/workflow notes also appear under docs/00_overview")
            ],
        ),
    ]
    records[0]["discovery"]["discovery_evidence"].extend(
        [
            "blob:3dd607a3b721b5d82174abc291628fba5947ee56",
            "origin/main:src/docs/CONTRIBUTING.md",
        ]
    )
    return records
