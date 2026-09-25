"""Persist REEVALUATE_OPEN_RECORDS_PASS_V2. Additive. Does not rewrite V1 snapshots.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reintegrate, fuse identities, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION / OPEN_EVIDENCE_RESOLUTION
and REEVALUATE_OPEN_RECORDS_PASS_V1 files remain byte-stable.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    LANDSCAPE_V1_IDS,
    OPEN_IDS,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
    INSUFFICIENT,
    REEVALUATE_BOUND_SHA as REEVALUATE_V1_BOUND_SHA,
    REEVALUATE_PASS_ID as REEVALUATE_V1_PASS_ID,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v2_records import (
    BLOB_BACKUP_SIZER,
    BLOB_CURRENT_ENGINE,
    BLOB_CURRENT_MA,
    BLOB_CURRENT_SIZER,
    BLOB_ENGINE,
    BLOB_EXPORT_ENGINE,
    BLOB_EXPORT_MA,
    BLOB_EXPORT_SIZER,
    BLOB_MA,
    BLOB_README,
    BLOB_RESULTS,
    BLOB_SIZER,
    BLOB_STATS,
    CENSUS_BOUND_SHA,
    CONTRADICTION_ID_052,
    EXPLICIT_REMAIN_OPEN_IDS,
    INCOMPATIBLE,
    INPUT_PASS_ID,
    NOCH_PARENT,
    OUT_OF_SCOPE_OPEN_IDS,
    PREDECESSOR_BOUND_SHA,
    PREDECESSOR_PASS_ID,
    PTR_README_COMMIT,
    REJECT,
    REEVALUATE_V2_BOUND_REF,
    REEVALUATE_V2_BOUND_SHA,
    REEVALUATE_V2_PASS_ID,
    REMAINING_OPEN_IDS,
    RESULTING_DISPOSITIONS,
    SELECTOR_ADD_SHA,
    SELECTOR_REVERT_SHA,
    TARGET_FINAL_IDS,
    V2_WRITTEN_RECORD_IDS,
    reevaluate_open_records_pass_v2,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _dump

FROZEN_SNAPSHOT_DIRS = (
    "understand",
    "evaluate",
    "adjudicate",
    "evidence_resolution",
)
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})
PR_6166_BODY = """## Summary

- Reverts squash commit `75eee7bdc501ab4b0ec93812675cd074acb9e2ee` (PR #6165) only.
- Owner decision (A+1): Cap 2.3 remains exclusive selection authority. BTC remains excluded from the productive Master V2 / Double Play path.
- Existing productive chain is unchanged: Cap 2.1 → Cap 2.2 → Cap 2.3 → Cap 2.4 → Wallclock → Master V2 → Double Play.
- #6165 was isolated add-only (10 files), not runtime-consumed, and created no Cap-2.x / host importers.

## Scope (exact)

Deletes only the 10 files added by #6165. No Cap-2.x, Wallclock, Master V2, Double Play, BTC-policy, canonical-doc, config, or governance changes.
"""
SAME_BLOB_RELATION = {
    "relation_type": "SAME_BLOB_AS",
    "target_id": "RCN-000014",
    "unresolved_target": "",
    "evidence": [
        f"{NOCH_PARENT}:archive/noch_einordnen/README.md",
        f"{PTR_README_COMMIT}:archive/PeakTradeRepo/README.md",
        f"blob:{BLOB_README}",
    ],
    "epistemic_status": "FORENSIC_RAW_FACT",
}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": REEVALUATE_V2_BOUND_REF,
        "bound_against_sha": REEVALUATE_V2_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "reevaluate_pass_id": REEVALUATE_V2_PASS_ID,
        "input_pass_id": INPUT_PASS_ID,
        "predecessor_pass_id": PREDECESSOR_PASS_ID,
        "predecessor_bound_sha": PREDECESSOR_BOUND_SHA,
        "identity_fusion_forbidden": True,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "identity_merges_performed": 0,
        "understand_snapshot_frozen": True,
        "evaluate_snapshot_frozen": True,
        "adjudication_snapshot_frozen": True,
        "evidence_resolution_snapshot_frozen": True,
        "reevaluate_v1_snapshot_frozen": True,
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def _blob_text(repo_root: Path, blob: str) -> str:
    return _git(repo_root, "cat-file", "-p", blob)


def _write_command_artifacts(*, repo_root: Path, recon: Path) -> None:
    cmd = recon / "evidence" / "reevaluate_v2" / "commands"
    cmd.mkdir(parents=True, exist_ok=True)
    engine = _blob_text(repo_root, BLOB_ENGINE).rstrip("\n")
    results = _blob_text(repo_root, BLOB_RESULTS).rstrip("\n")
    stats = _blob_text(repo_root, BLOB_STATS).rstrip("\n")
    sizer = _blob_text(repo_root, BLOB_SIZER).rstrip("\n")
    ma = _blob_text(repo_root, BLOB_MA).rstrip("\n")
    readme = _blob_text(repo_root, BLOB_README).splitlines()[0]
    export_engine = _blob_text(repo_root, BLOB_EXPORT_ENGINE).splitlines()[1]
    export_sizer = _blob_text(repo_root, BLOB_EXPORT_SIZER).splitlines()[1]
    export_ma = _blob_text(repo_root, BLOB_EXPORT_MA).splitlines()[1]
    backup = _blob_text(repo_root, BLOB_BACKUP_SIZER).splitlines()[1]
    current_engine = _git(
        repo_root, "rev-parse", f"{REEVALUATE_V2_BOUND_SHA}:src/backtest/engine.py"
    ).strip()
    current_sizer = _git(
        repo_root, "rev-parse", f"{REEVALUATE_V2_BOUND_SHA}:src/risk/position_sizer.py"
    ).strip()
    current_ma = _git(
        repo_root, "rev-parse", f"{REEVALUATE_V2_BOUND_SHA}:src/strategies/ma_crossover.py"
    ).strip()
    if current_engine != BLOB_CURRENT_ENGINE:
        raise ValueError(f"current_engine_blob_mismatch:{current_engine}")
    if current_sizer != BLOB_CURRENT_SIZER:
        raise ValueError(f"current_sizer_blob_mismatch:{current_sizer}")
    if current_ma != BLOB_CURRENT_MA:
        raise ValueError(f"current_ma_blob_mismatch:{current_ma}")
    if engine != "# Engine placeholder":
        raise ValueError(f"engine_placeholder_mismatch:{engine!r}")
    if results != "# Results placeholder":
        raise ValueError(f"results_placeholder_mismatch:{results!r}")
    if stats != "# Stats placeholder":
        raise ValueError(f"stats_placeholder_mismatch:{stats!r}")
    if sizer != "# Position sizer placeholder":
        raise ValueError(f"sizer_placeholder_mismatch:{sizer!r}")
    if ma != "# MA Strategy placeholder":
        raise ValueError(f"ma_placeholder_mismatch:{ma!r}")
    noch_tree = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        NOCH_PARENT,
        "--",
        "archive/noch_einordnen",
    )
    if noch_tree.strip().splitlines() != ["archive/noch_einordnen/README.md"]:
        raise ValueError(f"noch_einordnen_tree_mismatch:{noch_tree!r}")
    noch_blob = _git(
        repo_root,
        "rev-parse",
        f"{NOCH_PARENT}:archive/noch_einordnen/README.md",
    ).strip()
    ptr_blob = _git(
        repo_root,
        "rev-parse",
        f"{PTR_README_COMMIT}:archive/PeakTradeRepo/README.md",
    ).strip()
    if noch_blob != BLOB_README or ptr_blob != BLOB_README:
        raise ValueError(f"readme_blob_mismatch:{noch_blob}:{ptr_blob}")
    (cmd / "placeholder_blobs.txt").write_text(
        "\n".join(
            [
                "EPISTEMIC_CLASS=FORENSIC_RAW",
                f"blob:{BLOB_ENGINE}={engine}",
                f"blob:{BLOB_RESULTS}={results}",
                f"blob:{BLOB_STATS}={stats}",
                f"blob:{BLOB_SIZER}={sizer}",
                f"blob:{BLOB_MA}={ma}",
                f"blob:{BLOB_README} first line={readme}",
                f"blob:{BLOB_EXPORT_ENGINE}={export_engine}",
                f"blob:{BLOB_EXPORT_SIZER}={export_sizer}",
                f"blob:{BLOB_EXPORT_MA}={export_ma}",
                f"blob:{BLOB_BACKUP_SIZER}={backup}",
                f"blob:{BLOB_CURRENT_ENGINE}=src/backtest/engine.py@{REEVALUATE_V2_BOUND_SHA}",
                f"blob:{BLOB_CURRENT_SIZER}=src/risk/position_sizer.py@{REEVALUATE_V2_BOUND_SHA}",
                f"blob:{BLOB_CURRENT_MA}=src/strategies/ma_crossover.py@{REEVALUATE_V2_BOUND_SHA}",
                f"SAME_BLOB_AS archive/noch_einordnen/README.md == archive/PeakTradeRepo/README.md == {BLOB_README}",
                "NOCH_TREE=",
                noch_tree.rstrip("\n"),
                "",
            ]
        ),
        encoding="utf-8",
    )
    constants = _git(
        repo_root,
        "show",
        f"{SELECTOR_ADD_SHA}:src/ops/master_v2_minimal_selector_v1/constants_v1.py",
    )
    add_stat = _git(repo_root, "show", "--stat", "--format=%H %s", SELECTOR_ADD_SHA)
    revert_stat = _git(repo_root, "show", "--stat", "--format=%H %s", SELECTOR_REVERT_SHA)
    (cmd / "selector_add_revert.txt").write_text(
        "\n".join(
            [
                "EPISTEMIC_CLASS=FORENSIC_RAW",
                f"SELECTOR_ADD_SHA={SELECTOR_ADD_SHA}",
                f"SELECTOR_REVERT_SHA={SELECTOR_REVERT_SHA}",
                add_stat.rstrip("\n"),
                revert_stat.rstrip("\n"),
                "CONSTANTS_HEAD=",
                "\n".join(constants.splitlines()[:12]),
                "",
            ]
        ),
        encoding="utf-8",
    )
    (cmd / "pr_6166_body.txt").write_text(
        "EPISTEMIC_CLASS=FORENSIC_RAW\nSOURCE=https://github.com/rauterfrank-ui/Peak_Trade/pull/6166\n\n"
        + PR_6166_BODY,
        encoding="utf-8",
    )
    census_tree = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        CENSUS_BOUND_SHA,
        "--",
        "docs/webui/observability",
    )
    auth_tree = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        REEVALUATE_V2_BOUND_SHA,
        "--",
        "docs/webui/observability",
    )
    census_count = len([ln for ln in census_tree.splitlines() if ln.strip()])
    auth_count = len([ln for ln in auth_tree.splitlines() if ln.strip()])
    if census_count != 11 or auth_count != 11:
        raise ValueError(f"hub_file_count_mismatch:{census_count}:{auth_count}")
    (cmd / "rcn_000052_presence_scope.txt").write_text(
        "\n".join(
            [
                "EPISTEMIC_CLASS=FORENSIC_RAW",
                f"CONTRADICTION_ID={CONTRADICTION_ID_052}",
                "C052_CONTRADICTION_RESOLVED=false",
                "SCOPE_RECONSTRUCTED_NOT_NORMALIZED=true",
                f"CENSUS_SHA={CENSUS_BOUND_SHA}",
                f"AUTH_SHA={REEVALUATE_V2_BOUND_SHA}",
                f"CENSUS_HUB_FILE_COUNT={census_count}",
                f"AUTH_HUB_FILE_COUNT={auth_count}",
                "CENSUS_TREE=",
                census_tree.rstrip("\n"),
                "AUTH_TREE=",
                auth_tree.rstrip("\n"),
                "FIND_V2_HARDCODED_PRESENCE=CURRENTLY_ABSENT",
                "FIND_V2_CLAIM=31 files in census",
                "INVENTORY_DELETED_FAMILY_METHOD=git log --diff-filter=D/R",
                "INVENTORY_DELETED_FAMILY_COUNT=31",
                "GET /observability currently wired in src/webui/app.py",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_raw_quotes(*, recon: Path) -> None:
    quotes = {
        **_header(),
        "kind": "FORENSIC_RAW_QUOTES",
        "interpretation_forbidden_in_this_file": True,
        "items": [
            {
                "id": "Q-PR6166-OWNER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/pr_6166_body.txt",
                "quote": "Owner decision (A+1): Cap 2.3 remains exclusive selection authority. BTC remains excluded from the productive Master V2 / Double Play path.",
            },
            {
                "id": "Q-PR6166-ADDONLY",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/pr_6166_body.txt",
                "quote": "#6165 was isolated add-only (10 files), not runtime-consumed, and created no Cap-2.x / host importers.",
            },
            {
                "id": "Q-SELECTOR-NOREWRITE",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/selector_add_revert.txt",
                "quote": "This package is a new Owner policy surface. It does not rewrite Cap 2.1 GFU",
            },
            {
                "id": "Q-ENGINE-PLACEHOLDER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"blob:{BLOB_ENGINE}=# Engine placeholder",
            },
            {
                "id": "Q-RESULTS-PLACEHOLDER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"blob:{BLOB_RESULTS}=# Results placeholder",
            },
            {
                "id": "Q-STATS-PLACEHOLDER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"blob:{BLOB_STATS}=# Stats placeholder",
            },
            {
                "id": "Q-SIZER-PLACEHOLDER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"blob:{BLOB_SIZER}=# Position sizer placeholder",
            },
            {
                "id": "Q-MA-PLACEHOLDER",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"blob:{BLOB_MA}=# MA Strategy placeholder",
            },
            {
                "id": "Q-README-SAME-BLOB",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/placeholder_blobs.txt",
                "quote": f"SAME_BLOB_AS archive/noch_einordnen/README.md == archive/PeakTradeRepo/README.md == {BLOB_README}",
            },
            {
                "id": "Q-C052-HUB-COUNT",
                "source": "docs/system_atlas/reconciliation/evidence/reevaluate_v2/commands/rcn_000052_presence_scope.txt",
                "quote": "CENSUS_HUB_FILE_COUNT=11",
            },
            {
                "id": "Q-CAP23-AUTHORITY",
                "source": "src/ops/single_selected_future_policy_v1/constants_v1.py",
                "quote": "SELECTION_AUTHORITY_ADDED = True",
            },
            {
                "id": "Q-GET-OBSERVABILITY",
                "source": "src/webui/app.py",
                "quote": '@app.get("/observability", response_class=HTMLResponse)',
            },
        ],
    }
    _dump(recon / "evidence" / "reevaluate_v2" / "raw_quotes.yaml", quotes)


def _v1_frozen_hashes(recon: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in (
        "reevaluate/pass_v1_status.yaml",
        "reevaluate/index.yaml",
    ):
        hashes[rel] = _sha256_path(recon / rel)
    records_dir = recon / "reevaluate" / "records"
    for path in sorted(records_dir.glob("RCN-*.yaml")):
        hashes[f"reevaluate/records/{path.name}"] = _sha256_path(path)
    if len(hashes) != 37:
        raise ValueError(f"v1_frozen_hash_count_mismatch:{len(hashes)}")
    return hashes


def _dump_record_item(record: dict[str, Any]) -> str:
    body = (
        yaml.dump(
            record,
            Dumper=NoAliasDumper,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        ).rstrip()
        + "\n"
    )
    lines = body.splitlines(keepends=True)
    out = ["- " + lines[0]]
    for line in lines[1:]:
        if line.strip() == "":
            out.append("\n" if line.endswith("\n") else line)
        else:
            out.append("  " + line)
    return "".join(out)


def _split_ledger(text: str) -> tuple[str, list[tuple[str, str]], str]:
    starts = [m.start() for m in re.finditer(r"^- identity:\n", text, re.M)]
    footer_match = re.search(r"^census_pass_id:", text, re.M)
    if not starts or footer_match is None:
        raise ValueError("ledger_split_failed")
    header = text[: starts[0]]
    ends = starts[1:] + [footer_match.start()]
    items: list[tuple[str, str]] = []
    for start, end in zip(starts, ends, strict=True):
        chunk = text[start:end]
        match = re.search(r"reconciliation_id: (RCN-\d{6})\n", chunk)
        if not match:
            raise ValueError("ledger_record_id_missing")
        items.append((match.group(1), chunk))
    footer = text[footer_match.start() :]
    if len(items) != 53:
        raise ValueError(f"ledger_split_count_mismatch:{len(items)}")
    return header, items, footer


def _reevaluate_v2_block(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "pass_id": REEVALUATE_V2_PASS_ID,
        "input_pass_id": INPUT_PASS_ID,
        "predecessor_pass_id": PREDECESSOR_PASS_ID,
        "predecessor_bound_sha": PREDECESSOR_BOUND_SHA,
        "disposition_burden_met": payload["disposition_burden_met"],
        "disposition_candidate": payload["disposition"],
        "disposition": payload["disposition"],
        "lifecycle_state": payload["lifecycle_state"],
        "final_disposition_change_performed": payload["final_disposition_change_performed"],
        "identity_merge_performed": False,
        "reintegration_performed": False,
        "reintegration_candidate": False,
        "runtime_mutation_performed": False,
        "further_evidence_required": payload["further_evidence_required"],
        "positive_reason": payload.get("positive_reason") or "",
        "contradiction_id": payload.get("contradiction_id") or "",
        "current_evidence_set": list(payload["current_evidence_set"]),
        "historical_function": payload["historical_function"],
        "historical_relations": payload["historical_relations"],
        "current_system_analogues": payload["current_system_analogues"],
        "identity_status": payload["identity_status"],
        "successor_status": payload["successor_status"],
        "replacement_status": payload["replacement_status"],
        "current_value_status": payload["current_value_status"],
        "current_compatibility_status": payload["current_compatibility_status"],
        "contradictions": list(payload["contradictions"]),
        "unresolved_gaps": list(payload["unresolved_gaps"]),
        "evaluation_result": payload["evaluation_result"],
        "alternatives_rejected": list(payload["alternatives_rejected"]),
        "claims": list(payload["claims"]),
        "evidence_refs": list(payload["evidence_refs"]),
        "previous_adjudication": dict(payload["previous_adjudication"]),
        "bound_against_sha": REEVALUATE_V2_BOUND_SHA,
        "v1_snapshot_frozen": True,
    }


def _apply_live_record(rec: dict[str, Any], payload: dict[str, Any]) -> None:
    rid = rec["identity"]["reconciliation_id"]
    presence = rec["discovery"].get("current_presence") or ""
    if rid == "RCN-000052" and presence != "CURRENTLY_ABSENT":
        raise ValueError("census_presence_rewrite_forbidden:RCN-000052")
    adj = rec["adjudication"]
    if str(adj.get("disposition") or "") != INSUFFICIENT:
        raise ValueError(f"open_record_disposition_drift:{rid}:{adj.get('disposition')}")
    if str(adj.get("lifecycle_state") or "") != "OPEN":
        raise ValueError(f"open_record_lifecycle_drift:{rid}:{adj.get('lifecycle_state')}")
    v1_block = rec.get("reevaluate") or {}
    if v1_block.get("pass_id") != REEVALUATE_V1_PASS_ID:
        raise ValueError(f"v1_reevaluate_missing:{rid}")
    if v1_block.get("disposition_burden_met") is not False:
        raise ValueError(f"v1_reevaluate_mutated:{rid}")
    rec["reevaluate_v2"] = _reevaluate_v2_block(payload)
    if rid in TARGET_FINAL_IDS:
        adj["lifecycle_state"] = payload["lifecycle_state"]
        adj["disposition"] = payload["disposition"]
        adj["positive_reason"] = payload["positive_reason"]
        adj["evidence_refs"] = list(payload["evidence_refs"])
        adj["contradictions"] = list(payload["contradictions"])
        adj["unresolved_questions"] = list(payload["unresolved_gaps"])
        adj["identity_status"] = payload["identity_status"]
        adj["alternatives_rejected"] = list(payload["alternatives_rejected"])
        adj["further_evidence_required"] = False
        adj["reintegration_candidate"] = False
        adj["adjudication_attempted"] = True
        adj["claims"] = list(payload["claims"])
        rec["audit"]["last_adjudicated_against_sha"] = REEVALUATE_V2_BOUND_SHA
        if rid == "RCN-000051":
            items = list((rec.get("relations") or {}).get("items") or [])
            if not any(item.get("relation_type") == "SAME_BLOB_AS" for item in items):
                items.append(dict(SAME_BLOB_RELATION))
            rec["relations"]["items"] = items
            for rel in items:
                if str(rel.get("relation_type") or "") in FUSION:
                    raise ValueError(f"identity_fusion_forbidden:{rid}")
    marker = f"{REEVALUATE_V2_PASS_ID} bound against {REEVALUATE_V2_BOUND_SHA}. " + (
        f"Final disposition {payload['disposition']}."
        if rid in TARGET_FINAL_IDS
        else f"{CONTRADICTION_ID_052} remains OPEN; INSUFFICIENT_EVIDENCE unchanged."
    )
    note = str(rec["audit"].get("notes") or "")
    if marker not in note:
        rec["audit"]["notes"] = (note + " " + marker).strip()
    rec["integration"]["reintegration_required"] = False


def _patch_relations_index(recon: Path) -> None:
    path = recon / "relations.yaml"
    text = path.read_text(encoding="utf-8")
    if "relation_type: SAME_BLOB_AS" in text and "from: RCN-000051" in text:
        return
    item = yaml.dump(
        {"from": "RCN-000051", **SAME_BLOB_RELATION},
        Dumper=NoAliasDumper,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    ).rstrip()
    item_lines = ["- " + item.splitlines()[0]] + ["  " + ln for ln in item.splitlines()[1:]]
    block = "\n".join(item_lines) + "\n"
    needle = "- from: RCN-000052\n"
    if needle not in text:
        raise ValueError("relations_insert_anchor_missing")
    text = text.replace(needle, block + needle, 1)
    text = text.replace("relation_count: 66\n", "relation_count: 67\n", 1)
    path.write_text(text, encoding="utf-8")


def _update_schema(recon: Path) -> None:
    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("reevaluate_artifact_files") or [])
    for rel in (
        "reevaluate/pass_v1_status.yaml",
        "reevaluate/index.yaml",
        "reevaluate/pass_v2_status.yaml",
        "reevaluate/index_v2.yaml",
        "evidence/reevaluate_v2/raw_quotes.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["reevaluate_artifact_files"] = extra
    if "reevaluate_v2" not in schema:
        schema["reevaluate_v2"] = list(schema.get("reevaluate") or [])
    for field in (
        "predecessor_pass_id",
        "predecessor_bound_sha",
        "contradiction_id",
        "positive_reason",
        "v1_snapshot_frozen",
    ):
        if field not in schema["reevaluate_v2"]:
            schema["reevaluate_v2"].append(field)
    schema["reevaluate_v1_snapshots_are_frozen"] = True
    schema["reevaluate_v2_is_not_reintegration"] = True
    schema["reevaluate_v2_input_open_count"] = 35
    schema["reevaluate_v2_finalized_count"] = 5
    schema["reevaluate_v2_remaining_open_count"] = 30
    schema["reevaluate_v2_rcn_000052_remains_open"] = True
    schema["reevaluate_v2_no_identity_merges"] = True
    schema["reevaluate_v2_no_runtime_mutation"] = True
    schema["reevaluate_v2_no_reintegration"] = True
    _dump(schema_path, schema)


def persist_reevaluate_open_records_pass_v2(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    for frozen in FROZEN_SNAPSHOT_DIRS:
        if not (recon / frozen / "records").is_dir():
            raise ValueError(f"frozen_snapshot_missing:{frozen}")
    v1_status = yaml.safe_load((recon / "reevaluate" / "pass_v1_status.yaml").read_text())
    if v1_status.get("reevaluate_pass_id") != REEVALUATE_V1_PASS_ID:
        raise ValueError("v1_pass_id_mismatch")
    if int(v1_status["remaining_insufficient_evidence_open_count"]) != 35:
        raise ValueError("v1_remaining_open_mismatch")
    if int(v1_status["new_final_disposition_count"]) != 0:
        raise ValueError("v1_new_final_mismatch")
    if v1_status.get("bound_against_sha") != REEVALUATE_V1_BOUND_SHA:
        raise ValueError("v1_bound_sha_mismatch")
    v1_hashes_before = _v1_frozen_hashes(recon)
    _write_command_artifacts(repo_root=repo_root, recon=recon)
    _write_raw_quotes(recon=recon)

    generated = {row["record_id"]: row for row in reevaluate_open_records_pass_v2()}
    records_v2 = recon / "reevaluate" / "records_v2"
    records_v2.mkdir(parents=True, exist_ok=True)
    for rid, payload in generated.items():
        _dump(records_v2 / f"{rid}.yaml", {**_header(), **payload})

    ledger_path = recon / "ledger.yaml"
    original = ledger_path.read_text(encoding="utf-8")
    header, items, footer = _split_ledger(original)
    loaded = yaml.safe_load(original)
    by_id = {rec["identity"]["reconciliation_id"]: rec for rec in loaded["records"]}
    if tuple(by_id) != tuple(rid for rid, _ in items):
        raise ValueError("ledger_id_order_mismatch")
    if len(by_id) != 53:
        raise ValueError("ledger_record_count_mismatch")

    retain = 0
    insufficient = 0
    incompatible = 0
    rejected = 0
    for rec in loaded["records"]:
        rid = rec["identity"]["reconciliation_id"]
        disp = str(rec["adjudication"].get("disposition") or "")
        if disp == "RETAIN_AS_IS":
            retain += 1
        elif disp == INSUFFICIENT:
            insufficient += 1
        if rec.get("reevaluate_v2") is not None:
            raise ValueError(f"unexpected_preexisting_v2:{rid}")
        if rid in generated:
            _apply_live_record(rec, generated[rid])
        elif rid in OPEN_IDS:
            if rec.get("reevaluate") is None:
                raise ValueError(f"missing_v1_reevaluate:{rid}")
        elif rec.get("reevaluate") is not None:
            raise ValueError(f"reevaluate_on_non_open_record:{rid}")

    retain_after = sum(
        1 for rec in loaded["records"] if rec["adjudication"]["disposition"] == "RETAIN_AS_IS"
    )
    insufficient_after = sum(
        1 for rec in loaded["records"] if rec["adjudication"]["disposition"] == INSUFFICIENT
    )
    incompatible_after = sum(
        1 for rec in loaded["records"] if rec["adjudication"]["disposition"] == INCOMPATIBLE
    )
    rejected_after = sum(
        1 for rec in loaded["records"] if rec["adjudication"]["disposition"] == REJECT
    )
    if retain_after != 18:
        raise ValueError(f"retain_count_mismatch:{retain_after}")
    if insufficient_after != 30:
        raise ValueError(f"insufficient_count_mismatch:{insufficient_after}")
    if incompatible_after != 1:
        raise ValueError(f"incompatible_count_mismatch:{incompatible_after}")
    if rejected_after != 4:
        raise ValueError(f"reject_count_mismatch:{rejected_after}")
    if retain != 18 or insufficient != 35:
        raise ValueError(f"input_count_mismatch:{retain}:{insufficient}")
    rec052 = by_id["RCN-000052"]
    if rec052["adjudication"]["disposition"] != INSUFFICIENT:
        raise ValueError("rcn_000052_finalized")
    if rec052["discovery"]["current_presence"] != "CURRENTLY_ABSENT":
        raise ValueError("rcn_000052_presence_rewrite")
    if rec052["reevaluate_v2"].get("contradiction_id") != CONTRADICTION_ID_052:
        raise ValueError("rcn_000052_contradiction_id_missing")

    rebuilt: list[str] = []
    for rid, original_chunk in items:
        if rid in generated:
            rebuilt.append(_dump_record_item(by_id[rid]))
        else:
            rebuilt.append(
                original_chunk if original_chunk.endswith("\n") else original_chunk + "\n"
            )
    new_footer = footer
    new_footer = new_footer.replace(
        "reevaluate_pass_id: REEVALUATE_OPEN_RECORDS_PASS_V1\n"
        "reevaluate_bound_against_sha: f9618c73f1834b68588ceab586da4d6408962a10\n"
        "reevaluate_input_pass_id: OPEN_EVIDENCE_RESOLUTION_PASS_V1\n",
        "reevaluate_pass_id: REEVALUATE_OPEN_RECORDS_PASS_V2\n"
        "reevaluate_bound_against_sha: 7426af2daa4019e7986584a4c53d40b5e182673d\n"
        "reevaluate_input_pass_id: REEVALUATE_OPEN_RECORDS_PASS_V1\n"
        "reevaluate_v1_pass_id_frozen: REEVALUATE_OPEN_RECORDS_PASS_V1\n"
        "reevaluate_v1_bound_against_sha_frozen: f9618c73f1834b68588ceab586da4d6408962a10\n"
        "reevaluate_v1_input_pass_id_frozen: OPEN_EVIDENCE_RESOLUTION_PASS_V1\n",
        1,
    )
    if "reevaluate_pass_id: REEVALUATE_OPEN_RECORDS_PASS_V2" not in new_footer:
        raise ValueError("ledger_footer_pass_id_not_updated")
    ledger_path.write_text(header + "".join(rebuilt) + new_footer, encoding="utf-8")
    _patch_relations_index(recon)

    index_rows: list[dict[str, Any]] = []
    for rid in OPEN_IDS:
        rec = by_id[rid]
        presence = rec["discovery"].get("current_presence") or ""
        if rid in generated:
            payload = generated[rid]
            index_rows.append(
                {
                    "record_id": rid,
                    "census_current_presence": presence,
                    "v2_record_written": True,
                    "predecessor_unchanged": False,
                    "disposition_burden_met": payload["disposition_burden_met"],
                    "disposition": payload["disposition"],
                    "lifecycle_state": payload["lifecycle_state"],
                    "final_disposition_change_performed": payload[
                        "final_disposition_change_performed"
                    ],
                    "identity_merge_performed": False,
                    "reintegration_performed": False,
                }
            )
        else:
            if rid not in OUT_OF_SCOPE_OPEN_IDS:
                raise ValueError(f"unexpected_index_id:{rid}")
            index_rows.append(
                {
                    "record_id": rid,
                    "census_current_presence": presence,
                    "v2_record_written": False,
                    "predecessor_unchanged": True,
                    "disposition_burden_met": False,
                    "disposition": INSUFFICIENT,
                    "lifecycle_state": "OPEN",
                    "final_disposition_change_performed": False,
                    "identity_merge_performed": False,
                    "reintegration_performed": False,
                }
            )
    if len(index_rows) != 35:
        raise ValueError(f"index_v2_row_count_mismatch:{len(index_rows)}")

    v1_hashes_after = _v1_frozen_hashes(recon)
    if v1_hashes_after != v1_hashes_before:
        raise ValueError("frozen_v1_snapshot_changed_during_persist")

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "adjudicate_pass_id_frozen": "INTEGRATE_OR_DISPOSITION_PASS_V1",
        "baseline_origin_main_sha": REEVALUATE_V2_BOUND_SHA,
        "ledger_record_count": 53,
        "ledger_input_insufficient_evidence_count": 35,
        "input_open_record_count": 35,
        "reevaluation_attempted_record_count": 35,
        "v2_written_record_count": 6,
        "target_final_record_ids": list(TARGET_FINAL_IDS),
        "explicit_remain_open_record_ids": list(EXPLICIT_REMAIN_OPEN_IDS),
        "out_of_scope_open_record_ids": list(OUT_OF_SCOPE_OPEN_IDS),
        "resulting_dispositions": dict(RESULTING_DISPOSITIONS),
        "new_retain_as_is_count": 0,
        "new_adapt_and_reintegrate_count": 0,
        "new_capability_already_covered_count": 0,
        "new_historically_valid_but_incompatible_count": 1,
        "new_reject_for_current_system_count": 4,
        "remaining_insufficient_evidence_open_count": 30,
        "new_final_disposition_count": 5,
        "final_disposition_changes_performed": 5,
        "rcn_000052_remains_open": True,
        "rcn_000052_contradiction_id": CONTRADICTION_ID_052,
        "c052_contradiction_resolved": False,
        "identity_merges_performed": 0,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "no_identity_merges": True,
        "no_reintegration": True,
        "no_runtime_mutation": True,
        "frozen_v1_snapshots_unchanged": True,
        "v1_frozen_file_sha256": v1_hashes_after,
        "landscape_v1_ids": list(LANDSCAPE_V1_IDS),
        "total_ledger_record_count": 53,
        "total_retain_as_is_count": 18,
        "total_adapt_and_reintegrate_count": 0,
        "total_capability_already_covered_count": 0,
        "total_historically_valid_but_incompatible_count": 1,
        "total_reject_for_current_system_count": 4,
        "total_insufficient_evidence_count": 30,
    }
    _dump(recon / "reevaluate" / "pass_v2_status.yaml", status)
    _dump(
        recon / "reevaluate" / "index_v2.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )
    _update_schema(recon)
    if _v1_frozen_hashes(recon) != v1_hashes_before:
        raise ValueError("frozen_v1_snapshot_changed_after_schema")
    return {
        "attempted": 35,
        "remaining_open": 30,
        "new_final": 5,
        "written_v2_records": 6,
    }


def main() -> int:
    stats = persist_reevaluate_open_records_pass_v2(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
