"""Apply PR #6922 fixpoint extension: delete 234 adjudicated legacy nodes. ATLAS_AUTHORITY=NONE."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.ops.system_atlas_v1.generate_v1 import _HUB_ENTITY_IDS
from scripts.ops.system_atlas_v1.load_v1 import (
    ATLAS_ENTITY_RECORD_FILES,
    atlas_root,
    iter_closures,
    iter_entities,
    iter_relations,
    load_atlas_v1,
)

ATLAS = atlas_root(REPO)
BASELINE_WT = Path("/tmp/pt_baseline_atlas")
MANIFEST_PATH = ATLAS / "provenance" / "atlas_legacy_fixpoint_extension_v1_manifest.json"

RETAIN_IDS = frozenset(
    {
        "ACRONYM:SSOT",
        "ACRONYM:XPERP",
        "ADAPTER:okx_public_md_client",
        "FORENSIC_REFERENCE:information_corpus_persistence_base",
        "OKX_FEATURE:quote_identity_from_quoteCcy_or_instId",
        "SCHEMA:ranking_snapshot_v1",
        "VENUE:okx",
        "VENUE:okx_eea",
        "VENUE_ENDPOINT:okx_public_instruments",
        "VENUE_ENDPOINT:okx_trade_order",
        "VENUE_ENDPOINT:okx_account_positions",
        "VENUE_FIELD:instId",
        "VENUE_FIELD:quoteCcy",
        "VENUE_FIELD:uly",
    }
)

P = (
    "src/ops/full_core_live_path_composition_root_v1/",
    "src/ops/governed_futures_universe_producer_v1/",
    "src/ops/productive_futures_ranking_producer_v1/",
    "src/ops/single_selected_future",
    "src/ops/governed_productive_",
    "src/ops/current_productive_",
    "src/ops/b05_full_core",
    "src/governance/capital_risk_sizing_v1.py",
    "src/trading/master_v2/",
    "scripts/ops/system_atlas_v1/",
    "scripts/ops/current_system_interaction_authority_map_v1.py",
    "config/governance/current_system_interaction_authority_map_v1/",
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
)


def eid(row: dict) -> str | None:
    for key in (
        "id",
        "term_id",
        "schema_id",
        "feature_id",
        "endpoint_id",
        "field_id",
        "host_id",
        "shape_id",
        "acronym_id",
        "dod_id",
    ):
        val = row.get(key)
        if val:
            return str(val).strip()
    if row.get("acronym"):
        return f"ACRONYM:{row['acronym']}"
    if row.get("term"):
        return f"TERM:{row['term']}"
    return None


def classify_forensic(atlas: dict) -> set[str]:
    emap = {eid(e): e for e in iter_entities(atlas) if eid(e)}
    relations = iter_relations(atlas)
    root_ids: set[str] = set()
    for i, e in emap.items():
        st = str(e.get("current_status") or "")
        if e.get("current_canonical") or st in (
            "CURRENT_CANONICAL",
            "STILL_CURRENT_AND_CANONICALLY_SUPPORTED",
        ):
            root_ids.add(i)
        for p in e.get("source_paths") or []:
            if any(str(p).startswith(x) for x in P):
                root_ids.add(i)
                break
    adj: dict[str, set[str]] = defaultdict(set)
    for rel in relations:
        s, t = str(rel.get("source") or ""), str(rel.get("target") or "")
        if s and t:
            adj[s].add(t)
            adj[t].add(s)
    reach = set(root_ids)
    q: deque[str] = deque(root_ids)
    while q:
        n = q.popleft()
        for d in adj.get(n, ()):
            if d in emap and d not in reach:
                reach.add(d)
                q.append(d)
    label: dict[str, str] = {}
    for i, e in emap.items():
        st = str(e.get("current_status") or "")
        epi = str(e.get("epistemic_class") or "")
        if i in root_ids and (
            e.get("current_canonical")
            or st in ("CURRENT_CANONICAL", "STILL_CURRENT_AND_CANONICALLY_SUPPORTED")
        ):
            label[i] = "PROVEN_CURRENT"
        elif i in reach:
            label[i] = "CURRENT_SUPPORT_DEPENDENCY"
        elif (
            st in ("REMOVED", "SUPERSEDED", "HISTORICAL_ONLY")
            or st == "FORENSIC_REFERENCE_ONLY"
            or epi == "HISTORICAL"
        ):
            label[i] = "REMOVE_LEGACY"
        elif st in (
            "CURRENT_NONCANONICAL",
            "CURRENT_IMPLEMENTATION_WITHOUT_PROVEN_CANONICAL_SUPPORT",
        ):
            label[i] = "REMOVE_LEGACY"
        else:
            label[i] = "UNRESOLVED"
    for i in emap:
        if label[i] == "UNRESOLVED" and i not in reach:
            label[i] = "REMOVE_LEGACY"
    forensic = {i for i, c in label.items() if c == "REMOVE_LEGACY"}
    forensic.update(
        {
            "FORENSIC_REFERENCE:information_corpus_persistence_base",
            "CHILD:nested_structural_child",
        }
    )
    return forensic


def partition_residual(*, head_atlas: dict) -> tuple[set[str], set[str]]:
    if not BASELINE_WT.is_dir():
        raise SystemExit(f"BASELINE_WORKTREE_MISSING:{BASELINE_WT}")
    base_atlas = load_atlas_v1(repo_root=BASELINE_WT)
    forensic = classify_forensic(base_atlas)
    hids = {eid(e) for e in iter_entities(head_atlas) if eid(e)}
    residual = forensic & hids
    hlabel, hem = _head_labels(head_atlas, residual)
    delete, retain = _adjudicate_partition(head_atlas, residual, hlabel, hem)
    return delete, retain


def _head_labels(head_atlas: dict, residual: set[str]) -> tuple[dict, dict[str, dict]]:
    emap = {eid(e): e for e in iter_entities(head_atlas) if eid(e)}
    relations = iter_relations(head_atlas)
    root_ids: set[str] = set()
    for i, e in emap.items():
        st = str(e.get("current_status") or "")
        if e.get("current_canonical") or st in (
            "CURRENT_CANONICAL",
            "STILL_CURRENT_AND_CANONICALLY_SUPPORTED",
        ):
            root_ids.add(i)
        for p in e.get("source_paths") or []:
            if any(str(p).startswith(x) for x in P):
                root_ids.add(i)
                break
    adj: dict[str, set[str]] = defaultdict(set)
    for rel in relations:
        s, t = str(rel.get("source") or ""), str(rel.get("target") or "")
        if s and t:
            adj[s].add(t)
            adj[t].add(s)
    reach = set(root_ids)
    q: deque[str] = deque(root_ids)
    while q:
        n = q.popleft()
        for d in adj.get(n, ()):
            if d in emap and d not in reach:
                reach.add(d)
                q.append(d)
    label: dict[str, str] = {}
    for i, e in emap.items():
        st = str(e.get("current_status") or "")
        epi = str(e.get("epistemic_class") or "")
        if i in root_ids and (
            e.get("current_canonical")
            or st in ("CURRENT_CANONICAL", "STILL_CURRENT_AND_CANONICALLY_SUPPORTED")
        ):
            label[i] = "PROVEN_CURRENT"
        elif i in reach:
            label[i] = "CURRENT_SUPPORT_DEPENDENCY"
        else:
            label[i] = "LEGACY"
    return label, emap


def _adjudicate_partition(
    head_atlas: dict,
    residual: set[str],
    hlabel: dict[str, str],
    hem: dict[str, dict],
) -> tuple[set[str], set[str]]:
    relations = iter_relations(head_atlas)
    adj: dict[str, set[str]] = defaultdict(set)
    for rel in relations:
        s, t = str(rel.get("source") or ""), str(rel.get("target") or "")
        if s and t:
            adj[s].add(t)
            adj[t].add(s)
    proven = {i for i, c in hlabel.items() if c == "PROVEN_CURRENT" and i not in residual}
    shell = set(proven)
    q: deque[str] = deque(proven)
    while q:
        n = q.popleft()
        for d in adj.get(n, ()):
            if d in hem and d not in residual and d not in shell:
                shell.add(d)
                q.append(d)

    closure_ref: set[str] = set()
    for row in iter_closures(head_atlas):
        for key in ("inspect", "upstream", "downstream", "depends_on"):
            for dep in row.get(key) or []:
                dep = str(dep)
                if dep in residual:
                    closure_ref.add(dep)

    field_required: set[str] = set()
    for rel in relations:
        src = str(rel.get("source") or "")
        if src not in shell and src not in proven:
            continue
        for f in rel.get("requires_okx_fields") or []:
            field_required.add(f"VENUE_FIELD:{f}")

    surfaces = {
        "validator": (REPO / "scripts/ops/system_atlas_v1/validate_v1.py").read_text(
            encoding="utf-8"
        ),
        "generator": (REPO / "scripts/ops/system_atlas_v1/generate_v1.py").read_text(
            encoding="utf-8"
        ),
        "tests_atlas": (REPO / "tests/ops/test_system_atlas_v1.py").read_text(encoding="utf-8"),
    }

    retain: set[str] = set()
    for nid in residual:
        if nid in RETAIN_IDS:
            retain.add(nid)
            continue
        reasons: list[str] = []
        if nid in closure_ref:
            reasons.append("CLOSURE_GRAPH")
        if nid in field_required:
            reasons.append("OKX_FIELD")
        for text in surfaces.values():
            if nid in text:
                reasons.append("REF")
        e = hem.get(nid)
        for p in (e.get("source_paths") or []) if e else []:
            if any(str(p).startswith(x) for x in P):
                reasons.append("PROD")
        if nid in _HUB_ENTITY_IDS:
            reasons.append("HUB")
        if reasons:
            retain.add(nid)

    delete = residual - retain
    if retain != set(RETAIN_IDS):
        raise SystemExit(f"RETAIN_MISMATCH:expected={sorted(RETAIN_IDS)}:got={sorted(retain)}")
    return delete, retain


def filter_catalog_text(text: str, delete_ids: set[str]) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    pending: list[str] = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^  - id:\s*(\S+)\s*$", line)
        if m:
            ent_id = m.group(1)
            block = [line]
            i += 1
            while i < len(lines) and not re.match(r"^  - id:\s*\S", lines[i]):
                block.append(lines[i])
                i += 1
            if ent_id in delete_ids:
                removed += 1
                pending = []
                continue
            out.extend(pending)
            pending = []
            out.extend(block)
            continue
        if line.startswith("#") or line.strip() == "":
            pending.append(line)
        else:
            out.extend(pending)
            pending = []
            out.append(line)
        i += 1
    out.extend(pending)
    return "".join(out), removed


LIST_KEYS = frozenset(
    {
        "entities",
        "terms",
        "kinds",
        "acronyms",
        "dods",
        "schemas",
        "features",
        "endpoints",
        "fields",
        "hosts",
        "shapes",
        "lineage",
        "entrypoints",
        "configs",
        "chains",
        "gaps",
        "collisions",
        "contradictions",
        "closures",
        "changes",
        "events",
        "relations",
    }
)


def filter_relation_rows(rows: list, delete_ids: set[str]) -> tuple[list, int]:
    kept: list = []
    removed = 0
    for row in rows:
        if not isinstance(row, dict):
            kept.append(row)
            continue
        src = str(row.get("source") or "")
        dst = str(row.get("target") or "")
        if src in delete_ids or dst in delete_ids:
            removed += 1
            continue
        kept.append(row)
    return kept, removed


def filter_entity_rows(rows: list, delete_ids: set[str]) -> tuple[list, int]:
    kept: list = []
    removed = 0
    for row in rows:
        if not isinstance(row, dict):
            kept.append(row)
            continue
        rid = eid(row) or str(row.get("id") or "")
        if rid in delete_ids:
            removed += 1
            continue
        kept.append(row)
    return kept, removed


def filter_yaml_obj(obj, delete_ids: set[str]) -> tuple[any, int]:
    removed = 0
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in LIST_KEYS and isinstance(v, list):
                if k == "relations":
                    filtered, n = filter_relation_rows(v, delete_ids)
                else:
                    filtered, n = filter_entity_rows(v, delete_ids)
                out[k] = filtered
                removed += n
            elif isinstance(v, dict):
                out[k], n = filter_yaml_obj(v, delete_ids)
                removed += n
            elif isinstance(v, list):
                out[k] = v
            else:
                out[k] = v
        return out, removed
    return obj, 0


def apply_delete(delete_ids: set[str]) -> tuple[int, int]:
    entity_removed = 0
    rel_removed = 0
    for rel in ATLAS_ENTITY_RECORD_FILES:
        path = ATLAS / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if rel == "entities/catalog.yaml":
            new_text, n = filter_catalog_text(text, delete_ids)
            entity_removed += n
            path.write_text(new_text, encoding="utf-8")
            continue
        if rel.startswith("relations/") or rel == "wiring/family_child_mmr.yaml":
            data = yaml.safe_load(text) or {}
            new_data, n = filter_yaml_obj(data, delete_ids)
            rel_removed += n
            path.write_text(
                text
                if n == 0
                else yaml.dump(new_data, sort_keys=False, allow_unicode=True, width=120),
                encoding="utf-8",
            )
            continue
        data = yaml.safe_load(text) or {}
        new_data, n = filter_yaml_obj(data, delete_ids)
        entity_removed += n
        if n:
            path.write_text(
                yaml.dump(new_data, sort_keys=False, allow_unicode=True, width=120),
                encoding="utf-8",
            )
    return entity_removed, rel_removed


def main() -> None:
    head = load_atlas_v1(repo_root=REPO)
    delete_ids, retain_ids = partition_residual(head_atlas=head)
    if delete_ids & retain_ids:
        raise SystemExit("DELETE_RETAIN_INTERSECT")
    if len(delete_ids) != 234 or len(retain_ids) != 14:
        raise SystemExit(f"PARTITION_COUNT_FAIL:delete={len(delete_ids)}:retain={len(retain_ids)}")
    if delete_ids & RETAIN_IDS:
        raise SystemExit("RETAIN_SET_WOULD_MUTATE")

    manifest = {
        "schema_version": "atlas_legacy_fixpoint_extension_v1",
        "delete_ids": sorted(delete_ids),
        "retain_ids": sorted(retain_ids),
        "delete_count": len(delete_ids),
        "retain_count": len(retain_ids),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    ent, rel = apply_delete(delete_ids)
    print(f"DELETE_MANIFEST_COUNT={len(delete_ids)}")
    print(f"RETAIN_MANIFEST_COUNT={len(retain_ids)}")
    print(f"ENTITY_BLOCKS_REMOVED={ent}")
    print(f"RELATIONS_REMOVED={rel}")
    print(f"MANIFEST_PATH={MANIFEST_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
