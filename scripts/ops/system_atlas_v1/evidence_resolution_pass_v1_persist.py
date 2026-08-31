"""Persist OPEN_EVIDENCE_RESOLUTION_PASS_V1. Evidence resolution only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not change disposition, fuse identities, reintegrate, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION snapshots remain frozen.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    ADJUDICATE_FROZEN_SHA,
    ALLOWED_RESOLUTION_STATUSES,
    CENSUS_BOUND_SHA,
    CONTRADICTION,
    EVIDENCE_RESOLUTION_BOUND_REF,
    EVIDENCE_RESOLUTION_BOUND_SHA,
    EVIDENCE_RESOLUTION_PASS_ID,
    LANDSCAPE_V1_IDS,
    PARTIAL,
    RESOLVED,
    SELECTOR_ADD_SHA,
    SELECTOR_REVERT_SHA,
    STACK_DELETE_SHA,
    STACK_PARENT_SHA,
    UNRESOLVED,
    evidence_resolution_records,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _dump

FROZEN_SNAPSHOT_DIRS = ("understand", "evaluate", "adjudicate")


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": EVIDENCE_RESOLUTION_BOUND_REF,
        "bound_against_sha": EVIDENCE_RESOLUTION_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "evidence_resolution_pass_id": EVIDENCE_RESOLUTION_PASS_ID,
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
        "final_disposition_change_performed": False,
        "adjudication_snapshot_frozen": True,
        "evaluate_snapshot_frozen": True,
        "understand_snapshot_frozen": True,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "identity_merges_performed": 0,
    }


def _git(*args: str, repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")


def _write_command_artifacts(*, repo_root: Path, recon: Path) -> None:
    commands = recon / "evidence" / "evidence_resolution_v1" / "commands"
    ledger = yaml.safe_load((recon / "ledger.yaml").read_text(encoding="utf-8"))
    lines = [
        f"COMMAND=git ls-tree -r --name-only <sha> -- <historical_path[0]>",
        f"CENSUS_SHA={CENSUS_BOUND_SHA}",
        f"ORIGIN_MAIN_SHA={EVIDENCE_RESOLUTION_BOUND_SHA}",
        "EPISTEMIC_CLASS=FORENSIC_RAW",
        "",
        f"{'RID':<12} {'presence':<22} {'census_n':>8} {'main_n':>8} path",
    ]
    for rec in ledger["records"]:
        adj = rec.get("adjudication") or {}
        if not (
            adj.get("disposition") == "INSUFFICIENT_EVIDENCE"
            and adj.get("lifecycle_state") == "OPEN"
        ):
            continue
        rid = rec["identity"]["reconciliation_id"]
        presence = rec["discovery"].get("current_presence") or ""
        paths = rec["discovery"].get("historical_paths") or []
        path0 = str(paths[0]) if paths else ""
        census_n = 0
        main_n = 0
        if path0:
            census_n = len(
                [
                    ln
                    for ln in _git(
                        "ls-tree",
                        "-r",
                        "--name-only",
                        CENSUS_BOUND_SHA,
                        "--",
                        path0,
                        repo_root=repo_root,
                    ).splitlines()
                    if ln
                ]
            )
            main_n = len(
                [
                    ln
                    for ln in _git(
                        "ls-tree",
                        "-r",
                        "--name-only",
                        EVIDENCE_RESOLUTION_BOUND_SHA,
                        "--",
                        path0,
                        repo_root=repo_root,
                    ).splitlines()
                    if ln
                ]
            )
        lines.append(f"{rid:<12} {presence:<22} {census_n:8d} {main_n:8d} {path0}")
    _write_text(commands / "presence_matrix.txt", "\n".join(lines))

    imports = _git(
        "grep",
        "-n",
        "-E",
        r"^from src\.webui\.|^import src\.webui\.",
        STACK_PARENT_SHA,
        "--",
        "src/webui/market_dashboard_product_surface_v1",
        "src/webui/market_dashboard_readmodels_v1",
        "src/webui/market_surface.py",
        "src/webui/futures_read_only_market_dashboard_runtime_v0.py",
        repo_root=repo_root,
    )
    _write_text(
        commands / "landscape_v1_import_edges.txt",
        "COMMAND=git grep -n -E '^from src.webui.|^import src.webui.' "
        f"{STACK_PARENT_SHA} -- <v1 dashboard paths>\n"
        "EPISTEMIC_CLASS=FORENSIC_RAW\n"
        f"SOURCE_SHA={STACK_PARENT_SHA}\n\n" + imports,
    )
    hub_census = _git(
        "ls-tree",
        "-r",
        "--name-only",
        CENSUS_BOUND_SHA,
        "--",
        "docs/webui/observability",
        repo_root=repo_root,
    )
    _write_text(
        commands / "rcn_000052_census_tree.txt",
        "COMMAND=git ls-tree -r --name-only "
        f"{CENSUS_BOUND_SHA} -- docs/webui/observability\n"
        "EPISTEMIC_CLASS=FORENSIC_RAW\n"
        f"SOURCE_SHA={CENSUS_BOUND_SHA}\n\n" + hub_census,
    )
    delete_msg = _git(
        "show",
        "--format=%H%n%ad%n%s%n%b",
        "--date=iso",
        "--no-patch",
        STACK_DELETE_SHA,
        repo_root=repo_root,
    )
    _write_text(
        commands / "b5b81728_delete_message.txt",
        "COMMAND=git show --no-patch --format='%H%n%ad%n%s%n%b' "
        f"{STACK_DELETE_SHA}\n"
        "EPISTEMIC_CLASS=FORENSIC_RAW\n\n" + delete_msg,
    )
    revert_msg = _git(
        "show",
        "--format=%H%n%ad%n%s%n%b",
        "--date=iso",
        "--no-patch",
        SELECTOR_REVERT_SHA,
        repo_root=repo_root,
    )
    add_msg = _git(
        "show",
        "--format=%H%n%ad%n%s%n%b",
        "--date=iso",
        "--no-patch",
        SELECTOR_ADD_SHA,
        repo_root=repo_root,
    )
    _write_text(
        commands / "rcn_000015_add_revert_messages.txt",
        "COMMAND=git show --no-patch "
        f"{SELECTOR_ADD_SHA} {SELECTOR_REVERT_SHA}\n"
        "EPISTEMIC_CLASS=FORENSIC_RAW\n\n"
        f"===== ADD =====\n{add_msg}\n===== REVERT =====\n{revert_msg}",
    )


def _quotes() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "RCN-000015",
            "source": f"{SELECTOR_ADD_SHA}:src/ops/master_v2_minimal_selector_v1/constants_v1.py",
            "source_sha": SELECTOR_ADD_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": (
                "This package is a new Owner policy surface. It does not rewrite Cap 2.1 GFU "
                "eligibility, Cap 2.2 ranking authority, Cap 2.3 stickiness/ranking selection, "
                "or Cap 2.4 ranking-gated binding."
            ),
        },
        {
            "record_id": "RCN-000015",
            "source": f"{SELECTOR_ADD_SHA}:src/ops/master_v2_minimal_selector_v1/selection_v1.py",
            "source_sha": SELECTOR_ADD_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": (
                "eligible_count == 0 → NO_SELECTION\neligible_count == 1 → SELECT that candidate\n"
                "eligible_count > 1 → NO_SELECTION\nNo ranking, score, sort-to-select, fallback, "
                "cadence, or hot-path rescan."
            ),
        },
        {
            "record_id": "RCN-000015",
            "source": f"{SELECTOR_REVERT_SHA}",
            "source_sha": SELECTOR_REVERT_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": "This reverts commit 75eee7bdc501ab4b0ec93812675cd074acb9e2ee.",
        },
        {
            "record_id": "RCN-000019",
            "source": "14d58ec3b9d7acac26720d1aa4cf5ce46acfb725:src/risk_layer/kill_switch/adapter.py",
            "source_sha": "14d58ec3b9d7acac26720d1aa4cf5ce46acfb725",
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": (
                "Legacy Adapter for KillSwitchLayer API Compatibility.\n"
                "TEMPORARY / DEPRECATED\n"
                "This adapter bridges the gap between the new Kill Switch (State Machine API) "
                "and the old KillSwitchLayer (Evaluator API) used by risk_gate."
            ),
        },
        {
            "record_id": "RCN-000019",
            "source": "6e1ce02727f1719f8a9a5d1f001bb3e0c59411c7:src/risk_layer/kill_switch.py",
            "source_sha": "6e1ce02727f1719f8a9a5d1f001bb3e0c59411c7",
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": "class KillSwitchLayer:",
        },
        {
            "record_id": "RCN-000009",
            "source": f"{STACK_DELETE_SHA}",
            "source_sha": STACK_DELETE_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": (
                "delete(webui): remove market dashboard product stack\n"
                "kein Rebuild autorisiert oder begonnen"
            ),
        },
        {
            "record_id": "RCN-000023",
            "source": f"{STACK_PARENT_SHA}:src/webui/market_surface.py",
            "source_sha": STACK_PARENT_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": 'CANONICAL_MARKET_ROUTE = "/market"',
        },
        {
            "record_id": "RCN-000052",
            "source": f"{CENSUS_BOUND_SHA}:docs/webui/observability",
            "source_sha": CENSUS_BOUND_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": "git ls-tree census SHA lists 11 files under docs/webui/observability",
        },
        {
            "record_id": "RCN-000001",
            "source": "src/webui/market_dashboard_landscape_v2/owner_registry.py",
            "source_sha": EVIDENCE_RESOLUTION_BOUND_SHA,
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": "This package is a consumer boundary only — it does not own trading truth.",
        },
        {
            "record_id": "RCN-000048",
            "source": "42c3f443d84c4f27110083c86d0c99db61a022ed",
            "source_sha": "42c3f443d84c4f27110083c86d0c99db61a022ed",
            "epistemic_class": "FORENSIC_RAW",
            "used_as_fact": True,
            "quote": (
                "R100 docs/PHASE_16A_EXECUTION_PIPELINE.md -> "
                "docs/20_phases/PHASE_16A_EXECUTION_PIPELINE.md"
            ),
        },
    ]


def persist_evidence_resolution_pass_v1(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    for frozen in FROZEN_SNAPSHOT_DIRS:
        if not (recon / frozen / "records").is_dir():
            raise ValueError(f"frozen_snapshot_missing:{frozen}")
    _write_command_artifacts(repo_root=repo_root, recon=recon)

    pass_root = recon / "evidence_resolution"
    records_dir = pass_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = recon / "evidence" / "evidence_resolution_v1"

    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])
    generated = {row["record_id"]: row for row in evidence_resolution_records()}
    if len(generated) != 35:
        raise ValueError(f"resolution_record_count_mismatch:{len(generated)}")

    status_counts = {RESOLVED: 0, PARTIAL: 0, UNRESOLVED: 0, CONTRADICTION: 0}
    attempted = 0
    index_rows: list[dict[str, Any]] = []
    marker = (
        f"{EVIDENCE_RESOLUTION_PASS_ID} bound against {EVIDENCE_RESOLUTION_BOUND_SHA}. "
        "Disposition unchanged."
    )

    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        adj = rec["adjudication"]
        presence = rec["discovery"].get("current_presence") or ""
        if rid == "RCN-000052" and presence != "CURRENTLY_ABSENT":
            raise ValueError("census_presence_rewrite_forbidden:RCN-000052")
        if rid not in generated:
            if rec.get("evidence_resolution") is not None:
                raise ValueError(f"evidence_resolution_on_non_open_record:{rid}")
            continue
        if str(adj.get("disposition") or "") != "INSUFFICIENT_EVIDENCE":
            raise ValueError(f"open_record_disposition_drift:{rid}:{adj.get('disposition')}")
        if str(adj.get("lifecycle_state") or "") != "OPEN":
            raise ValueError(f"open_record_lifecycle_drift:{rid}:{adj.get('lifecycle_state')}")
        payload = generated[rid]
        if payload["evidence_resolution_status"] not in ALLOWED_RESOLUTION_STATUSES:
            raise ValueError(f"resolution_status_invalid:{rid}")
        rec["evidence_resolution"] = {
            "pass_id": EVIDENCE_RESOLUTION_PASS_ID,
            "evidence_resolution_status": payload["evidence_resolution_status"],
            "final_disposition_change_performed": False,
            "identity_merge_performed": False,
            "reintegration_performed": False,
            "runtime_mutation_performed": False,
            "missing_proof_question": payload["missing_proof_question"],
            "identity_gap": payload["identity_gap"],
            "function_gap": payload["function_gap"],
            "relation_gap": payload["relation_gap"],
            "successor_or_replacement_gap": payload["successor_or_replacement_gap"],
            "current_system_fit_gap": payload["current_system_fit_gap"],
            "claims": list(payload["claims"]),
            "evidence_refs": list(payload["evidence_refs"]),
            "remaining_open_questions": list(payload["remaining_open_questions"]),
            "relations_proven": list(payload.get("relations_proven") or []),
            "contradictions": list(payload.get("contradictions") or []),
            "bound_against_sha": EVIDENCE_RESOLUTION_BOUND_SHA,
        }
        audit = rec["audit"]
        note = str(audit.get("notes") or "")
        if marker not in note:
            audit["notes"] = (note + " " + marker).strip()
        file_payload = {**_header(), **payload}
        _dump(records_dir / f"{rid}.yaml", file_payload)
        status_counts[payload["evidence_resolution_status"]] += 1
        attempted += 1
        index_rows.append(
            {
                "record_id": rid,
                "evidence_resolution_status": payload["evidence_resolution_status"],
                "census_current_presence": presence,
                "evaluate_capability_overlap": rec["current_comparison"].get("capability_overlap")
                or "",
                "identity_status": adj.get("identity_status") or "",
                "disposition_unchanged": True,
                "final_disposition": adj.get("disposition"),
                "lifecycle_state": adj.get("lifecycle_state"),
                "reintegration_performed": False,
            }
        )

    if attempted != 35:
        raise ValueError(f"attempted_count_mismatch:{attempted}")

    ledger["evidence_resolution_pass_id"] = EVIDENCE_RESOLUTION_PASS_ID
    ledger["evidence_resolution_bound_against_sha"] = EVIDENCE_RESOLUTION_BOUND_SHA
    _dump(ledger_path, ledger)

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "adjudicate_pass_id_frozen": "INTEGRATE_OR_DISPOSITION_PASS_V1",
        "adjudicate_bound_against_sha_frozen": ADJUDICATE_FROZEN_SHA,
        "ledger_record_count": len(ledger_records),
        "input_open_record_count": 35,
        "evidence_resolution_attempted_count": attempted,
        "evidence_gap_resolved_count": status_counts[RESOLVED],
        "evidence_gap_partially_resolved_count": status_counts[PARTIAL],
        "evidence_gap_unresolved_count": status_counts[UNRESOLVED],
        "contradiction_discovered_count": status_counts[CONTRADICTION],
        "final_disposition_changes_performed": 0,
        "identity_merges_performed": 0,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "landscape_v1_ids": list(LANDSCAPE_V1_IDS),
        "status_counts": status_counts,
    }
    _dump(pass_root / "pass_v1_status.yaml", status)
    _dump(
        pass_root / "index.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )
    _dump(
        evidence_dir / "raw_quotes.yaml",
        {
            **_header(),
            "kind": "FORENSIC_RAW_QUOTES",
            "interpretation_forbidden_in_this_file": True,
            "items": _quotes(),
        },
    )

    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("evidence_resolution_artifact_files") or [])
    for rel in (
        "evidence_resolution/pass_v1_status.yaml",
        "evidence_resolution/index.yaml",
        "evidence/evidence_resolution_v1/raw_quotes.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["evidence_resolution_artifact_files"] = extra
    if "evidence_resolution" not in schema:
        schema["evidence_resolution"] = []
    for field in (
        "pass_id",
        "evidence_resolution_status",
        "missing_proof_question",
        "identity_gap",
        "function_gap",
        "relation_gap",
        "successor_or_replacement_gap",
        "current_system_fit_gap",
        "claims",
        "evidence_refs",
        "remaining_open_questions",
        "relations_proven",
        "contradictions",
    ):
        if field not in schema["evidence_resolution"]:
            schema["evidence_resolution"].append(field)
    schema["allowed_evidence_resolution_statuses"] = sorted(ALLOWED_RESOLUTION_STATUSES)
    schema["evidence_resolution_is_not_disposition"] = True
    schema["current_presence_is_not_disposition"] = True
    _dump(schema_path, schema)
    return {
        "attempted": attempted,
        "partial": status_counts[PARTIAL],
        "contradiction": status_counts[CONTRADICTION],
        "resolved": status_counts[RESOLVED],
        "unresolved": status_counts[UNRESOLVED],
    }


def main() -> int:
    stats = persist_evidence_resolution_pass_v1(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
