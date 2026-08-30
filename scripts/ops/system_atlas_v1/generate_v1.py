"""Deterministic System Atlas markdown generator. ATLAS_AUTHORITY=NONE."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from scripts.ops.system_atlas_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    ATLAS_ROLE,
    GENERATED_MARKER,
    GENERATED_VIEW_NAMES,
    GENERATOR_MODULE,
    SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.load_v1 import (
    atlas_root,
    iter_closures,
    iter_collisions,
    iter_configs,
    iter_contradictions,
    iter_entities,
    iter_entrypoints,
    iter_family_child_mmr,
    iter_gaps,
    iter_lineage,
    iter_relations,
    iter_safety_chains,
)

_HEADER = (
    f"<!-- {GENERATED_MARKER} -->\n"
    f"<!-- generator: {GENERATOR_MODULE} -->\n"
    f"<!-- atlas_authority: {ATLAS_AUTHORITY} -->\n"
    f"<!-- schema_version: {SCHEMA_VERSION} -->\n\n"
)

_BANNER = (
    f"`ATLAS_AUTHORITY={ATLAS_AUTHORITY}`  \n"
    f"`ATLAS_ROLE={ATLAS_ROLE}`  \n"
    "`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  \n"
    "`ATLAS_MUST_CITE_AUTHORITY=true`  \n"
    "`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`\n\n"
)

_DRILLDOWN_VIEW_NAMES = tuple(n for n in GENERATED_VIEW_NAMES if n != "SYSTEM_ATLAS.md")

MASTER_VIEW_SECTION_HEADINGS = (
    "1. Authority model",
    "2. Master V2 / Double Play relation",
    "3. System / subsystem hierarchy",
    "4. Family / Child / SSOT-CHILD / MMR model",
    "5. Capability map",
    "6. Productive selection / binding flow",
    "7. Runtime call / data flow",
    "8. Safety / governance model",
    "9. Configuration wiring",
    "10. Data contract / identity / unit model",
    "11. Complete OKX domain overview",
    "12. Current vs historical classification",
    "13. Provenance / timeline summary",
    "14. Contradictions",
    "15. Open gaps",
    "16. Orphan / missing-wiring findings",
    "17. Build guidance / dependency closures",
    "18. Terminology / acronym summary",
    "19. Schema / DoD / contract summary",
    "20. Coverage / completeness status",
)

_HUB_ENTITY_IDS = frozenset(
    {
        "SYSTEM:peak_trade",
        "SUBSYSTEM:master_v2",
        "FUNCTIONAL_CORE:double_play",
        "RUNBOOK:canonical_master_runbook",
        "RUNBOOK:vollautonomie_v4_4_12",
        "NAVIGATION_INDEX:map_of_truth",
        "CAPABILITY:cap_2_1_gfu",
        "CAPABILITY:cap_2_2_ranking",
        "CAPABILITY:cap_2_3_single_selected_future",
        "CAPABILITY:cap_2_4_runtime_binding",
        "CAPABILITY:cap_1_1_reconciliation",
        "CAPABILITY:cap_3_1_futures_accounting",
        "CAPABILITY:cap_4_1_pre_activation_closure",
        "CAPABILITY:cap_7_2_stateful_no_order",
        "CAPABILITY:cap_11_13_5_live_canary",
        "RUNTIME_COMPONENT:dp_core_wiring",
        "RUNTIME_COMPONENT:mv2_decision_packet",
        "RUNTIME_COMPONENT:mv2_integrated_replay",
        "UNIVERSE:governed_futures_universe",
        "SELECTOR:productive_futures_ranking",
        "SELECTOR:single_selected_future_policy",
        "BINDER:bound_instrument_v1",
        "HOST:cap72_stateful_host",
        "VENUE:okx",
        "VENUE:okx_eea",
        "GATE:live_authorized_false",
        "GATE:btc_exclusion",
        "GATE:flatten_execute_authority",
        "GATE:max_positions_1",
        "OBSERVER:post_action_canary",
        "TRANSPORT:bound_okx_testnet_http",
        "ADAPTER:okx_public_md_client",
        "AUTH_PRIMITIVE:okx_hmac_sign",
        "OWNER_DECISION:cap23_exclusive_selection",
        "OWNER_DECISION:btc_excluded",
        "INVARIANT:missing_metadata_never_defaulted",
        "RUNTIME_COMPONENT:gfu_eligibility",
        "RUNTIME_COMPONENT:dp_composition",
        "RUNTIME_COMPONENT:dp_survival",
        "RUNTIME_COMPONENT:dp_suitability",
        "RUNTIME_COMPONENT:dp_state",
        "SCRIPT:run_gfu_producer",
        "SCRIPT:run_cap23_policy",
        "VENUE_ENDPOINT:okx_public_instruments",
        "VENUE_ENDPOINT:okx_trade_order",
        "FORENSIC_REFERENCE:information_corpus_persistence_base",
    }
)

_OVERVIEW_KINDS = frozenset(
    {
        "SYSTEM",
        "SUBSYSTEM",
        "FUNCTIONAL_CORE",
        "CAPABILITY",
        "GATE",
        "HOST",
        "VENUE",
        "RUNBOOK",
        "FAMILY",
        "DOD",
        "SCHEMA",
        "DATA_CONTRACT",
        "OWNER_DECISION",
        "INVARIANT",
        "BINDER",
        "SELECTOR",
        "UNIVERSE",
        "OBSERVER",
        "TRANSPORT",
        "ADAPTER",
        "PHASE",
        "NAVIGATION_INDEX",
    }
)

_UPSTREAM_TYPES = frozenset(
    {
        "DEPENDS_ON",
        "REQUIRES",
        "CONSUMES",
        "CALLS",
        "READS",
        "LOADS",
        "GOVERNED_BY",
        "CONFIGURED_BY",
        "BINDS",
        "FETCHES",
    }
)
_DOWNSTREAM_TYPES = frozenset(
    {
        "PRODUCES",
        "HAS_CHILD",
        "HAS_FAMILY",
        "HAS_FUNCTIONAL_CORE",
        "HAS_CAPABILITY",
        "HAS_SSOT_CHILD",
        "HAS_MMR",
        "HAS_DOD",
        "CONTAINS",
        "EMITS",
        "WRITES",
        "PERSISTS",
        "AUTHORIZES",
    }
)


def _md_escape(text: str) -> str:
    return str(text).replace("|", "\\|")


def _collapse_ws(text: str) -> str:
    return " ".join(str(text or "").split())


def _incompleteness_record(atlas: dict[str, Any]) -> dict[str, Any]:
    return (atlas.get("records") or {}).get("census/incompleteness.yaml") or {}


def _flag_cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value or "")


def _incompleteness_table_rows(items: Iterable[dict[str, Any]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in items:
        extra = ",".join(str(x) for x in (row.get("additional_classes") or []))
        rows.append(
            [
                str(row.get("id") or ""),
                _flag_cell(row.get("flag")),
                str(row.get("primary_class") or ""),
                extra,
                _collapse_ws(str(row.get("remaining") or ""))[:220],
            ]
        )
    return rows


def _epi_label(status: str) -> str:
    if status == "OPEN":
        return "STATUS=OPEN (not proven)"
    if status == "CONTRADICTED":
        return "STATUS=CONTRADICTED (both sides preserved)"
    if status == "HYPOTHESIS":
        return "STATUS=HYPOTHESIS (not authority)"
    return f"STATUS={status}"


def _entity_map(entities: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(e["id"]): e for e in entities}


def _adj(
    relations: list[dict[str, Any]], types: Iterable[str], *, reverse: bool
) -> dict[str, list[str]]:
    wanted = frozenset(types)
    out: dict[str, set[str]] = defaultdict(set)
    for rel in relations:
        if str(rel.get("type")) not in wanted:
            continue
        src = str(rel["source"])
        dst = str(rel["target"])
        if reverse:
            out[dst].add(src)
        else:
            out[src].add(dst)
    return {k: sorted(v) for k, v in out.items()}


def _bfs(start: str, adj: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    q: deque[str] = deque([start])
    while q:
        node = q.popleft()
        if node in seen:
            continue
        seen.add(node)
        for nxt in adj.get(node, ()):
            if nxt not in seen:
                q.append(nxt)
    seen.discard(start)
    return sorted(seen)


def compute_closures(
    entities: list[dict[str, Any]], relations: list[dict[str, Any]]
) -> dict[str, dict[str, list[str]]]:
    up_adj = _adj(relations, _UPSTREAM_TYPES, reverse=False)
    down_adj = _adj(relations, _DOWNSTREAM_TYPES, reverse=False)
    called_by = _adj(relations, {"CALLS"}, reverse=True)
    result: dict[str, dict[str, list[str]]] = {}
    for ent in entities:
        eid = str(ent["id"])
        direct_up = sorted(up_adj.get(eid, ()))
        direct_down = sorted(set(down_adj.get(eid, ())) | set(called_by.get(eid, ())))
        result[eid] = {
            "direct_upstream": direct_up,
            "transitive_upstream": _bfs(eid, up_adj),
            "direct_downstream": direct_down,
            "transitive_downstream": _bfs(eid, down_adj),
        }
    return result


def _detect_orphans(
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    declared_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    producers: set[str] = set()
    consumers: set[str] = set()
    callers: set[str] = set()
    callees: set[str] = set()
    for rel in relations:
        rtype = str(rel.get("type"))
        src = str(rel["source"])
        dst = str(rel["target"])
        if rtype in {"PRODUCES", "PERSISTS", "EMITS", "WRITES"}:
            producers.add(src)
            consumers.add(dst)
        if rtype in {"CONSUMES", "READS", "LOADS", "FETCHES"}:
            consumers.add(src)
            producers.add(dst)
        if rtype == "CALLS":
            callers.add(src)
            callees.add(dst)
    auto: list[dict[str, Any]] = []
    for ent in entities:
        eid = str(ent["id"])
        kind = str(ent.get("kind"))
        if kind in {"RUNTIME_COMPONENT", "CAPABILITY", "ADAPTER", "HOST", "RUNNER", "TRANSPORT"}:
            if eid not in consumers and eid not in callees and eid not in callers:
                auto.append(
                    {
                        "id": f"GAP_AUTO:NO_CONSUMER:{eid}",
                        "class": "DEFINED_BUT_NO_CONSUMER",
                        "entity": eid,
                        "epistemic_status": "OPEN",
                    }
                )
    seen = {str(g.get("id")) for g in declared_gaps}
    return [g for g in auto if str(g["id"]) not in seen]


def _section(title: str) -> str:
    return f"## {title}\n\n"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(_md_escape(c) for c in row) + " |" for row in rows)
    return (
        f"{head}\n{sep}\n{body}\n\n"
        if rows
        else f"{head}\n{sep}\n| _(none)_ | {' | '.join('_' for _ in headers[1:])} |\n\n"
    )


def _rel_row(rel: dict[str, Any]) -> list[str]:
    return [
        str(rel.get("id") or ""),
        str(rel.get("source") or ""),
        str(rel.get("type") or ""),
        str(rel.get("target") or ""),
        _epi_label(str(rel.get("epistemic_status") or "")),
        ",".join(str(x) for x in (rel.get("evidence_sources") or [])[:3]),
    ]


def generate_views_v1(*, atlas: dict[str, Any], repo_root: Path) -> dict[str, str]:
    entities = sorted(iter_entities(atlas), key=lambda e: str(e.get("id") or ""))
    relations = sorted(iter_relations(atlas), key=lambda r: str(r.get("id") or ""))
    contradictions = sorted(iter_contradictions(atlas), key=lambda c: str(c.get("id") or ""))
    closures = sorted(iter_closures(atlas), key=lambda c: str(c.get("id") or ""))
    lineage = sorted(iter_lineage(atlas), key=lambda c: str(c.get("id") or ""))
    entrypoints = sorted(iter_entrypoints(atlas), key=lambda c: str(c.get("id") or ""))
    configs = sorted(iter_configs(atlas), key=lambda c: str(c.get("id") or ""))
    chains = sorted(iter_safety_chains(atlas), key=lambda c: str(c.get("id") or ""))
    gaps = list(iter_gaps(atlas))
    fcm = sorted(iter_family_child_mmr(atlas), key=lambda c: str(c.get("id") or ""))
    meta = atlas["records"].get("census/census_meta.yaml") or {}
    emap = _entity_map(entities)
    computed = compute_closures(entities, relations)
    auto_gaps = _detect_orphans(entities, relations, gaps)
    all_gaps = sorted(gaps + auto_gaps, key=lambda g: str(g.get("id") or ""))

    struct = [r for r in relations if r.get("graph") == "structural"]
    runtime = [r for r in relations if r.get("graph") == "runtime"]
    authority = [r for r in relations if r.get("graph") == "authority_evidence"]

    views: dict[str, str] = {}

    views["SYSTEM_ATLAS.md"] = _gen_system_atlas(
        meta=meta,
        entities=entities,
        relations=relations,
        contradictions=contradictions,
        closures=closures,
        lineage=lineage,
        configs=configs,
        gaps=all_gaps,
        fcm=fcm,
        entrypoints=entrypoints,
        chains=chains,
        collisions=iter_collisions(atlas),
        atlas=atlas,
        emap=emap,
    )
    views["STRUCTURAL_GRAPH.md"] = _gen_graph(
        "Structural graph — what belongs to what?",
        struct,
        "Membership, hierarchy, supersession. Inverse edges are not inferred.",
    )
    views["RUNTIME_GRAPH.md"] = _gen_graph(
        "Runtime graph — what calls/consumes/produces what?",
        runtime,
        "Control/data/network edges are typed. A CALLS edge does not imply a data dependency.",
    )
    views["AUTHORITY_GRAPH.md"] = _gen_graph(
        "Authority graph — why are we allowed to believe this?",
        authority,
        "Implementation and tests cannot confer authority upward.",
    )
    views["OKX_INTEGRATION_MAP.md"] = _gen_okx_map(entities, meta, atlas)
    views["OKX_FEATURE_MATRIX.md"] = _gen_okx_matrix(entities)
    views["OKX_CHRONOLOGY.md"] = _gen_okx_chronology(atlas)
    views["SAFETY_GOVERNANCE_MAP.md"] = _gen_safety(entities, chains)
    views["DATA_CONTRACT_MAP.md"] = _gen_data_contracts(entities, lineage)
    views["PROVENANCE_TIMELINE.md"] = _gen_provenance(atlas)
    views["BUILD_GUIDANCE.md"] = _gen_guidance(closures, computed, emap)
    views["CONTRADICTION_REGISTER.md"] = _gen_contradictions(contradictions)
    views["MASTER_V2_DOUBLE_PLAY_MAP.md"] = _gen_mv2(entities, relations, fcm, computed)
    arch = atlas["records"].get("census/historical_architecture.yaml") or {}
    arch_rows = [
        [
            str(e.get("id")),
            str(e.get("when") or ""),
            str(e.get("pr") or ""),
            str(e.get("what") or "")[:120],
            str(e.get("current_status") or ""),
        ]
        for e in arch.get("events") or []
    ]
    views["MASTER_V2_DOUBLE_PLAY_MAP.md"] += (
        _section("Git chronology (origin/main after unshallow)")
        + "Owner-bound Master V2 / Double Play same-system relation is not reinterpreted.\n\n"
        + _table(["id", "when", "pr", "what", "status"], arch_rows)
    )
    views["FAMILY_CHILD_MMR_MAP.md"] = _gen_fcm(fcm, entities)
    views["FULL_DEPENDENCY_GRAPH.md"] = _gen_full_dep(entities, computed, relations)
    wiring = atlas["records"].get("census/historical_wiring.yaml") or {}
    w_rows = [
        [
            str(e.get("id")),
            str(e.get("source") or ""),
            str(e.get("relation") or ""),
            str(e.get("target") or "")[:80],
            str(e.get("valid_from") or ""),
            str(e.get("valid_to") or ""),
            _epi_label(str(e.get("epistemic_status") or "")),
        ]
        for e in wiring.get("edges") or []
    ]
    views["FULL_DEPENDENCY_GRAPH.md"] += _section(
        "Historical wiring (time-bounded; origin/main git)"
    ) + _table(
        ["id", "source", "relation", "target", "from", "to", "epistemic"],
        w_rows,
    )
    views["DATA_LINEAGE_MAP.md"] = _gen_lineage(lineage)
    views["CONFIGURATION_WIRING.md"] = _gen_config(configs)
    views["ENTRYPOINT_RUNTIME_TRACES.md"] = _gen_traces(entrypoints)
    views["ORPHAN_AND_WIRING_GAPS.md"] = _gen_gaps(all_gaps)
    views["PROJECT_TERMINOLOGY.md"] = _gen_terminology(entities)
    hist_terms = atlas["records"].get("census/historical_terminology.yaml") or {}
    ht_rows = [
        [
            str(t.get("term")),
            str(t.get("exact_historical_spelling") or ""),
            str(t.get("expansion_if_proven") or "OPEN"),
            str(t.get("status") or ""),
            str(t.get("first_proven_usage") or "none"),
        ]
        for t in hist_terms.get("historical_terms") or []
    ]
    views["PROJECT_TERMINOLOGY.md"] += (
        _section("Historical origin/main archaeology (scoped)")
        + "SSOT_CHILD literal remains absent from origin/main history. OPEN expansions remain OPEN.\n\n"
        + _table(["term", "spelling", "expansion", "status", "first_commit"], ht_rows)
    )
    views["ACRONYM_REGISTER.md"] = _gen_acronyms(entities)
    views["DOD_MAP.md"] = _gen_dod(entities)
    views["SCHEMA_MAP.md"] = _gen_schemas(entities, atlas)
    views["TERMINOLOGY_COLLISIONS.md"] = _gen_term_collisions(iter_collisions(atlas))
    views["ATLAS_CHANGE_IMPACT.md"] = _gen_atlas_change_impact(atlas)
    views["COVERAGE_REPORT.md"] = _gen_coverage(
        meta,
        entities,
        relations,
        contradictions,
        closures,
        all_gaps,
        lineage,
        configs,
        iter_collisions(atlas),
        atlas,
    )
    return views


def _status_bucket(entity: dict[str, Any]) -> str:
    status = str(entity.get("current_status") or "")
    epi = str(entity.get("epistemic_class") or "")
    temporal = str(entity.get("temporal_class") or "")
    if epi == "CONTRADICTED":
        return "CONTRADICTED"
    if epi == "NAVIGATION_ONLY":
        return "ADJUDICATED"
    if status == "REJECTED":
        return "REJECTED"
    if epi == "OPEN" or status == "OPEN":
        return "OPEN"
    if status == "FORENSIC_REFERENCE_ONLY":
        return "FORENSIC_ONLY"
    if status == "SUPERSEDED":
        return "SUPERSEDED"
    if temporal == "HISTORICAL_ONLY" or epi == "HISTORICAL":
        return "HISTORICAL_REFERENCE_ONLY"
    if status in {"CURRENT_CANONICAL", "STILL_CURRENT_AND_CANONICALLY_SUPPORTED"}:
        return "CURRENT_CANONICAL"
    if status == "CURRENT_IMPLEMENTATION_WITHOUT_PROVEN_CANONICAL_SUPPORT":
        return "CURRENT_IMPLEMENTED_NONCANONICAL"
    if epi == "ADJUDICATED":
        return "ADJUDICATED"
    if status == "CURRENT_NONCANONICAL":
        return "CURRENT_IMPLEMENTED_NONCANONICAL"
    if epi == "FORENSIC_RAW":
        return "FORENSIC_ONLY"
    return status or epi or "OPEN"


def _alias(eid: str) -> str:
    return "n_" + eid.replace(":", "_").replace("-", "_")


def _hub_relations(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [
        r
        for r in relations
        if str(r.get("source")) in _HUB_ENTITY_IDS and str(r.get("target")) in _HUB_ENTITY_IDS
    ]
    return sorted(selected, key=lambda r: str(r.get("id") or ""))


def _mermaid_hub_graph(relations: list[dict[str, Any]], emap: dict[str, dict[str, Any]]) -> str:
    selected = _hub_relations(relations)
    nodes = sorted(
        {str(r.get("source")) for r in selected} | {str(r.get("target")) for r in selected}
    )
    lines = ["```mermaid", "flowchart TB"]
    for eid in nodes:
        bucket = _status_bucket(emap.get(eid, {}))
        lines.append(f'  {_alias(eid)}["{eid}<br/>{bucket}"]')
    for rel in selected:
        epi = str(rel.get("epistemic_status") or "")
        label = str(rel.get("type") or "")
        if epi in {"OPEN", "CONTRADICTED", "ADJUDICATED", "HISTORICAL"}:
            label = f"{label} ({epi})"
        lines.append(
            f'  {_alias(str(rel.get("source")))} -->|"{label}"| {_alias(str(rel.get("target")))}'
        )
    lines.append("```")
    return "\n".join(lines) + "\n"


def _drilldown(name: str) -> str:
    return f"[{name}]({name})"


_REPO_ATLAS_BOOL_KEYS = (
    "repo_current_tree_census_complete",
    "repo_git_history_census_complete",
    "repo_schema_census_complete",
    "repo_terminology_inventory_complete",
    "repo_master_v2_census_complete",
    "repo_double_play_census_complete",
    "repo_family_child_census_complete",
    "repo_dod_census_complete",
    "repo_okx_census_complete",
    "repo_atlas_census_complete",
)


def _repo_atlas_flag_text(meta: dict[str, Any]) -> str:
    repo = meta.get("repo_atlas_v1") or {}
    lines = [f"{key.upper()}={str(bool(repo.get(key))).lower()}" for key in _REPO_ATLAS_BOOL_KEYS]
    lines.append(
        "EXTERNAL_FORENSIC_CORPUS_CENSUS_COMPLETE="
        + str(repo.get("external_forensic_corpus_census_complete", "NOT_STARTED"))
    )
    return "\n".join(lines) + "\n"


def _okx_product_type_rows(atlas: dict[str, Any]) -> list[list[str]]:
    block = atlas["records"].get("census/okx_product_types.yaml") or {}
    return [
        [
            str(row.get("product_type") or ""),
            str(row.get("status") or ""),
            str(row.get("canonical_support") or ""),
            str(row.get("runtime_reachability") or ""),
        ]
        for row in (block.get("product_types") or [])
    ]


def _entity_row(entity: dict[str, Any]) -> list[str]:
    return [
        str(entity.get("id") or ""),
        str(entity.get("kind") or ""),
        str(entity.get("name") or "")[:60],
        _status_bucket(entity),
        _epi_label(str(entity.get("epistemic_class") or "")),
    ]


def _gen_system_atlas(
    *,
    meta: dict[str, Any],
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    closures: list[dict[str, Any]],
    lineage: list[dict[str, Any]],
    configs: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    fcm: list[dict[str, Any]],
    entrypoints: list[dict[str, Any]],
    chains: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
    atlas: dict[str, Any],
    emap: dict[str, dict[str, Any]],
) -> str:
    by_kind: dict[str, int] = defaultdict(int)
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        by_kind[str(entity.get("kind"))] += 1
        if str(entity.get("kind")) in _OVERVIEW_KINDS:
            buckets[_status_bucket(entity)].append(entity)
    hub_rels = _hub_relations(relations)
    struct = [r for r in relations if r.get("graph") == "structural"]
    runtime = [r for r in relations if r.get("graph") == "runtime"]
    authority = [r for r in relations if r.get("graph") == "authority_evidence"]
    caps = [e for e in entities if str(e.get("kind")) == "CAPABILITY"]
    gates = [e for e in entities if str(e.get("kind")) in {"GATE", "GUARD", "PERMIT"}]
    schemas = [e for e in entities if str(e.get("kind")) == "SCHEMA"]
    dods = [e for e in entities if str(e.get("kind")) == "DOD"]
    acronyms = [e for e in entities if str(e.get("kind")) == "ACRONYM"]
    contracts = [e for e in entities if str(e.get("kind")) == "DATA_CONTRACT"]
    okx_hosts = [e for e in entities if str(e.get("kind")) == "OKX_HOST"]
    okx_eps = [e for e in entities if str(e.get("kind")) == "VENUE_ENDPOINT"]
    okx_fields = [e for e in entities if str(e.get("kind")) == "VENUE_FIELD"]
    okx_feats = [e for e in entities if str(e.get("kind")) == "OKX_FEATURE"]
    timeline = (atlas.get("records") or {}).get("provenance/timeline.yaml") or {}
    events = sorted(
        timeline.get("events") or [], key=lambda e: str(e.get("sort_key") or e.get("id") or "")
    )
    named_gaps = list(meta.get("named_gaps") or [])
    incompleteness = _incompleteness_record(atlas)
    closed_domains = list(incompleteness.get("closed_domains") or [])
    remaining_domains = list(incompleteness.get("remaining_domains") or [])
    flag_reasons = list(incompleteness.get("completeness_flag_reasons") or [])
    unresolved = [c for c in contradictions if not c.get("resolved")]
    auto_orphans = [g for g in gaps if str(g.get("id") or "").startswith("GAP_AUTO:")]
    declared_gaps = [g for g in gaps if not str(g.get("id") or "").startswith("GAP_AUTO:")]
    bucket_order = (
        "CURRENT_CANONICAL",
        "CURRENT_IMPLEMENTED_NONCANONICAL",
        "ADJUDICATED",
        "HISTORICAL_REFERENCE_ONLY",
        "SUPERSEDED",
        "REJECTED",
        "FORENSIC_ONLY",
        "OPEN",
        "CONTRADICTED",
    )
    drill = "\n".join(f"- {_drilldown(name)}" for name in _DRILLDOWN_VIEW_NAMES)
    parts: list[str] = [
        _HEADER,
        "# Peak_Trade System Atlas\n\n",
        _BANNER,
        "Primary human entrypoint. This is an evidence-bound topology overview, not a business SSOT and not runtime authorization.\n\n",
        "```text\n",
        "SYSTEM_ATLAS_PRIMARY_ENTRYPOINT=docs/system_atlas/generated/SYSTEM_ATLAS.md\n",
        f"SYSTEM_ATLAS_MASTER_VIEW_COMPLETE={str(meta.get('system_atlas_master_view_complete', False)).lower()}\n",
        f"GLOBAL_CENSUS_EXHAUSTED={str(meta.get('global_census_exhausted', False)).lower()}\n",
        f"SYSTEM_ATLAS_DRILLDOWN_LINKS_VALID={str(meta.get('system_atlas_drilldown_links_valid', False)).lower()}\n",
        f"SYSTEM_ATLAS_ALL_MAJOR_DOMAINS_REPRESENTED={str(meta.get('system_atlas_all_major_domains_represented', False)).lower()}\n",
        f"SYSTEM_ATLAS_CURRENT_HISTORICAL_SPLIT_VALID={str(meta.get('system_atlas_current_historical_split_valid', False)).lower()}\n",
        f"SYSTEM_ATLAS_GRAPH_RELATIONS_BACKED_BY_MODEL={str(meta.get('system_atlas_graph_relations_backed_by_model', False)).lower()}\n",
        "```\n\n",
        "Navigation: `README.md` explains Atlas authority. This file is the complete overview. Specialized generated files are drill-down. YAML under `docs/system_atlas/` is the source model. Canonical authority remains the Master Runbook, external to the Atlas.\n\n",
        f"Census SHA: `{meta.get('origin_main_sha', 'OPEN')}`. Worktree dirty records are not origin/main truth.\n\n",
        _section("Integrated current topology (model-backed)"),
        "Every edge below is a stored Atlas relation whose source and target are hub entities. No inferred inverses. OPEN and CONTRADICTED edges keep that label.\n\n",
        _mermaid_hub_graph(relations, emap),
        f"Hub relations shown: `{len(hub_rels)}`. Full graphs: {_drilldown('STRUCTURAL_GRAPH.md')}, {_drilldown('RUNTIME_GRAPH.md')}, {_drilldown('AUTHORITY_GRAPH.md')}, {_drilldown('FULL_DEPENDENCY_GRAPH.md')}.\n\n",
        _table(
            ["id", "source", "type", "target", "epistemic"],
            [
                [
                    str(r.get("id")),
                    str(r.get("source")),
                    str(r.get("type")),
                    str(r.get("target")),
                    _epi_label(str(r.get("epistemic_status") or "")),
                ]
                for r in hub_rels
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[0]),
        "Canonical semantic SSOT is `RUNBOOK:canonical_master_runbook` (`DOCUMENT_CLASS=CANONICAL_MASTER_RUNBOOK`, `RUNTIME_AUTHORIZATION_EFFECT=NONE`). The Map of Truth is `NAVIGATION_ONLY` and must not be read as a second SSOT. Derived-domain runbooks (cybersecurity, presentation, runtime-ops) are not trading SSOT. Forensic persistence declares `AUTHORITY=NONE`. Implementation and tests cannot confer authority upward.\n\n",
        f"Standing fail-closed: `LIVE_AUTHORIZED=false`, `TESTNET_AUTHORIZED=false` unless a scoped Owner-GO plus canonical evidence says otherwise. Drill-down: {_drilldown('AUTHORITY_GRAPH.md')}.\n\n",
        _table(
            ["id", "kind", "name", "bucket", "epistemic"],
            [
                _entity_row(emap[i])
                for i in (
                    "RUNBOOK:canonical_master_runbook",
                    "NAVIGATION_INDEX:map_of_truth",
                    "FORENSIC_REFERENCE:information_corpus_persistence_base",
                    "OWNER_DECISION:cap23_exclusive_selection",
                    "OWNER_DECISION:btc_excluded",
                )
                if i in emap
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[1]),
        "Peak_Trade's trading core is named `Master V2 / Double Play` on the Master Runbook SYSTEM header. They are Modul-Owner of **one** Trading Core (`SEPARATE_*_ALLOWED=false` in architecture text). They are not competing generations.\n\n",
        "Atlas kind `FUNCTIONAL_CORE` and relation type `HAS_FUNCTIONAL_CORE` are census labels. Exact tokens `FUNCTIONAL_CORE` / `inner core` were **not** found on origin/main. The stored edge `REL:s_master_v2_has_dp` is `ADJUDICATED`, not a Master Runbook token. Historical Vollautonomie ordering vs current §4.2 chain is CONTRADICTED (`C-DP-ORDER-001`). `ops.double_play.evaluate_double_play` is quarantined projection-only.\n\n",
        f"Drill-down: {_drilldown('MASTER_V2_DOUBLE_PLAY_MAP.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[2]),
        f"`SYSTEM:peak_trade` `CONTAINS` `SUBSYSTEM:master_v2`. Recorded `HAS_CAPABILITY` edges from the system entity are Caps 1.1, 2.1–2.4, 3.1, 4.1, 7.2, and 11.13.5. The seven `MASTER_V2_CAPABILITY_*.md` spec files (1.1, 2.1–2.4, 3.1, 4.1) are inventoried; Caps 7.2 and 11.13.5 are Master-Runbook capabilities without a numbered MASTER_V2 spec file. Structural relation count: `{len(struct)}`. Drill-down: {_drilldown('STRUCTURAL_GRAPH.md')}.\n\n",
        _table(
            ["id", "kind", "name", "bucket", "epistemic"],
            [
                _entity_row(e)
                for e in entities
                if str(e.get("kind")) in {"SYSTEM", "SUBSYSTEM", "FUNCTIONAL_CORE", "HOST"}
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[3]),
        "**There is no single Families ontology.** The same spellings mean incompatible things. Do not collapse them. `SSOT_CHILD` is not a formal in-repo literal. `HISTORICAL_CHILD_LEDGER` (88 `SRC-*` children) is forensic source-region indexing with `ssot_role=HISTORICAL_FORENSIC_REGION_NOT_CURRENT_SSOT`, not SSOT_CHILD. MMR in the Master Runbook is Maintenance Margin Requirement (venue/margin); an architectural Master-V2 MMR kind was not found in scoped specs.\n\n",
        f"Observed Family senses include: projection-octet `family_id` (8 ids), OKX `instFamily`, `strategy_family`, confirm-token `FAMILY_*`, historical Gate-Familien F1–F6, obligation_families, and `NO_FAMILY_ONTOLOGY`. Drill-down: {_drilldown('FAMILY_CHILD_MMR_MAP.md')}, {_drilldown('TERMINOLOGY_COLLISIONS.md')}.\n\n",
        _table(
            ["id", "parent", "type", "child", "meaning", "epistemic"],
            [
                [
                    str(r.get("id")),
                    str(r.get("parent") or ""),
                    str(r.get("relation_type") or ""),
                    str(r.get("child") or ""),
                    str(r.get("meaning_class") or ""),
                    _epi_label(str(r.get("epistemic_status") or "")),
                ]
                for r in fcm
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[4]),
        "Capabilities are numbered packages with specs under `docs/ops/specs/MASTER_V2_CAPABILITY_*`. Presence of code is not activation.\n\n",
        _table(["id", "kind", "name", "bucket", "epistemic"], [_entity_row(c) for c in caps]),
        f"Drill-down: {_drilldown('BUILD_GUIDANCE.md')}, {_drilldown('FULL_DEPENDENCY_GRAPH.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[5]),
        "Canonical §4.5 chain (analytical host): Governed Futures Universe → Productive Ranking → Persisted Single Selected Future → Native Instrument Binding → Runtime Consumer.\n\n",
        "Stored wiring: Cap 2.1 `PRODUCES` universe; Cap 2.2 `RANKS` universe; Cap 2.3 `SELECTS` ranking; Cap 2.4 `BINDS` selection; Cap 7.2 host `CONSUMES` BoundInstrumentV1. Cap 2.3 is exclusive **for that analytical chain**. Section 11.13.5 canary is a **parallel** hardcoded instrument authority (`SUI-USD_UM_XPERP-310404`) with no Cap 2.3 import on origin/main (`C-CAP23-VS-CANARY-INSTRUMENT-001`). BTC remains productively excluded in Cap 2.1; `BTC_PRODUCTIVE_PROOF=DO_NOT_RUN` is a distinct canary-era flag.\n\n",
        f"Drill-down: {_drilldown('RUNTIME_GRAPH.md')}, {_drilldown('ENTRYPOINT_RUNTIME_TRACES.md')}, {_drilldown('DATA_LINEAGE_MAP.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[6]),
        f"Runtime relation count: `{len(runtime)}`. Entrypoints recorded: `{len(entrypoints)}`. Double Play pure-stack composition `CONSUMES` survival and suitability in current code. Public MD client `FETCHES` `/api/v5/public/instruments`. Bound testnet transport `SIGNS` HMAC. Flatten `GATES` canary; post-action `OBSERVES` flatten is `OPEN` (not proven wired). Live standing gate `DENIES` canary execute.\n\n",
        f"Drill-down: {_drilldown('RUNTIME_GRAPH.md')}, {_drilldown('ENTRYPOINT_RUNTIME_TRACES.md')}.\n\n",
        _table(
            ["id", "name", "class", "network"],
            [
                [
                    str(ep.get("id")),
                    str(ep.get("name") or ""),
                    str(ep.get("entrypoint_class") or ""),
                    str(ep.get("network_io") or "")[:80],
                ]
                for ep in entrypoints
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[7]),
        "Fail-closed is the default. Live/Testnet/orders require scoped Owner-GO. Confirm-tokens are purpose-scoped (flatten execute token is not the generic live token). Flatten transport exists with `DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false`. Kill-switch, max-positions=1, and BTC exclusion are separate gates.\n\n",
        _table(["id", "kind", "name", "bucket", "epistemic"], [_entity_row(g) for g in gates]),
        f"Safety chains recorded: `{len(chains)}`. Drill-down: {_drilldown('SAFETY_GOVERNANCE_MAP.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[8]),
        f"Configuration records: `{len(configs)}`. Config enablement does not confer `LIVE_AUTHORIZED`. Drill-down: {_drilldown('CONFIGURATION_WIRING.md')}.\n\n",
        _table(
            ["id", "key", "source", "default", "status"],
            [
                [
                    str(c.get("id")),
                    str(c.get("key") or ""),
                    str(c.get("source") or ""),
                    str(c.get("default") or "")[:80],
                    str(c.get("current_status") or ""),
                ]
                for c in configs
            ],
        ),
        _section(MASTER_VIEW_SECTION_HEADINGS[9]),
        "SCHEMA is not automatically DATA_CONTRACT or dataclass. BoundInstrumentV1 carries identity/digests, not ctVal/base/quote/settle. Quote currency is derived in Cap 2.1 eligibility (`quoteCcy` else hyphen `instId`; `uly` fills BASE only). Fresh EEA rows often have empty `quoteCcy`; XPERP underscored ids fail the regex (`C-OKX-QUOTE-ULY-001`). Public XPERP `settleCcy=USD` vs account USDC must not be collapsed.\n\n",
        _table(["id", "kind", "name", "bucket", "epistemic"], [_entity_row(c) for c in contracts]),
        f"Lineage records: `{len(lineage)}`. Drill-down: {_drilldown('DATA_CONTRACT_MAP.md')}, {_drilldown('DATA_LINEAGE_MAP.md')}, {_drilldown('SCHEMA_MAP.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[10]),
        "OKX is a first-class venue domain. XPERP is `instType=FUTURES` + `ruleType=xperp`, not a separate instType and not the census organizing center. Productive EEA REST host is `eea.okx.com`. Public MD client often uses `www.okx.com`. WebSocket hosts are configured; no proven live WS client. Signed private REST exists after the 2026-07-17 audit (supersession, not silent overwrite).\n\n",
        "Product types below are Peak_Trade evidence, not generic OKX venue capability.\n\n",
        _table(
            ["product_type", "status", "canonical_support", "runtime_reachability"],
            _okx_product_type_rows(atlas),
        ),
        f"- hosts: `{len(okx_hosts)}`\n- features: `{len(okx_feats)}`\n- endpoints: `{len(okx_eps)}`\n- fields: `{len(okx_fields)}`\n",
        f"- `OKX_CENSUS_COMPLETE={str(meta.get('okx_census_complete', False)).lower()}`\n",
        f"- `REPO_OKX_CENSUS_COMPLETE={str((meta.get('repo_atlas_v1') or {}).get('repo_okx_census_complete', False)).lower()}`\n\n",
        f"Drill-down: {_drilldown('OKX_INTEGRATION_MAP.md')}, {_drilldown('OKX_FEATURE_MATRIX.md')}, {_drilldown('OKX_CHRONOLOGY.md')}.\n\n",
        _section(MASTER_VIEW_SECTION_HEADINGS[11]),
        "Do not treat historical or forensic material as current runtime wiring. Implementation without proven canonical support is not activation. `IMPLEMENTED` is not `ACTIVATED`. `ADJUDICATED` is an Atlas census label, not a Master Runbook token. `FORENSIC_ONLY` is not canonical. `SUPERSEDED`/`REJECTED` remain historical records.\n\n",
    ]
    for bucket in bucket_order:
        rows = [
            _entity_row(e) for e in sorted(buckets.get(bucket, []), key=lambda x: str(x.get("id")))
        ]
        parts.append(f"### {bucket}\n\n")
        parts.append(f"Architectural-kind count in this bucket: `{len(rows)}`.\n\n")
        parts.append(_table(["id", "kind", "name", "bucket", "epistemic"], rows[:40]))
        if len(rows) > 40:
            parts.append(
                f"Truncated to 40 of `{len(rows)}` architectural-kind rows. Remaining kinds are in {_drilldown('COVERAGE_REPORT.md')}.\n\n"
            )
    parts.extend(
        [
            _section(MASTER_VIEW_SECTION_HEADINGS[12]),
            f"Timeline events: `{len(events)}`. Document-internal dates are not git-introduction proof. Drill-down: {_drilldown('PROVENANCE_TIMELINE.md')}.\n\n",
            _table(
                ["id", "when", "what", "epistemic"],
                [
                    [
                        str(e.get("id")),
                        str(e.get("when") or "OPEN"),
                        str(e.get("what") or "")[:100],
                        _epi_label(str(e.get("epistemic_status") or "")),
                    ]
                    for e in events
                ],
            ),
            _section(MASTER_VIEW_SECTION_HEADINGS[13]),
            f"Unresolved contradiction records: `{len(unresolved)}`. Both sides are preserved. Drill-down: {_drilldown('CONTRADICTION_REGISTER.md')}.\n\n",
            _table(
                ["id", "subject", "resolved"],
                [
                    [str(c.get("id")), str(c.get("subject") or "")[:80], str(c.get("resolved"))]
                    for c in contradictions
                ],
            ),
            _section(MASTER_VIEW_SECTION_HEADINGS[14]),
            "Named census gaps (not a closed universe):\n\n",
            "".join(f"- {g}\n" for g in named_gaps) + "\n",
            "Every remaining `*_COMPLETE=false` flag has exactly one primary incompleteness class "
            "(`GENUINELY_UNSEARCHED` | `SEARCHED_BUT_NO_EVIDENCE_FOUND` | `UNRESOLVED_CONTRADICTION` | "
            "`HISTORICAL_SOURCE_UNAVAILABLE` | `TERMINOLOGY_UNRESOLVED`). Closed file-inventory domains are not ontology-solved.\n\n",
            _table(
                ["id", "flag", "primary_class", "additional", "remaining"],
                _incompleteness_table_rows(remaining_domains + flag_reasons),
            ),
            f"Drill-down: {_drilldown('ORPHAN_AND_WIRING_GAPS.md')}, {_drilldown('COVERAGE_REPORT.md')}.\n\n",
            _section(MASTER_VIEW_SECTION_HEADINGS[15]),
            f"Declared gaps: `{len(declared_gaps)}`. Auto-detected `DEFINED_BUT_NO_CONSUMER` orphans: `{len(auto_orphans)}`. Auto-orphans are coverage notes, not proof of unused code. Drill-down: {_drilldown('ORPHAN_AND_WIRING_GAPS.md')}.\n\n",
            _table(
                ["id", "class", "entity", "epistemic"],
                [
                    [
                        str(g.get("id")),
                        str(g.get("class") or ""),
                        str(g.get("entity") or g.get("subject") or ""),
                        _epi_label(str(g.get("epistemic_status") or "OPEN")),
                    ]
                    for g in declared_gaps
                ],
            ),
            _section(MASTER_VIEW_SECTION_HEADINGS[16]),
            "If you change a listed inspect target, also inspect its stored upstream/downstream. Closures do not authorize work. When wiring changes, update the matching YAML under `docs/system_atlas/` (relations, wiring, venue/okx, census), then run `./scripts/pt scripts/ops/generate_system_atlas_v1.py`. Do not hand-edit generated Markdown. Usage: `docs/system_atlas/ATLAS_AUTHORITY_AND_USAGE.md`.\n\n",
            _table(
                ["id", "title", "inspect"],
                [
                    [
                        str(c.get("id")),
                        str(c.get("title") or ""),
                        ", ".join(str(x) for x in (c.get("inspect") or [])),
                    ]
                    for c in closures
                ],
            ),
            f"Drill-down: {_drilldown('BUILD_GUIDANCE.md')}, {_drilldown('FULL_DEPENDENCY_GRAPH.md')}.\n\n",
            _section(MASTER_VIEW_SECTION_HEADINGS[17]),
            f"Acronyms: `{len(acronyms)}`. Terminology collisions: `{len(collisions)}`. Never invent expansions; `OPEN` means unproven. Family/MMR/C1/DoD collisions are preserved. Drill-down: {_drilldown('PROJECT_TERMINOLOGY.md')}, {_drilldown('ACRONYM_REGISTER.md')}, {_drilldown('TERMINOLOGY_COLLISIONS.md')}.\n\n",
            _table(
                ["acronym", "expansion", "status"],
                [
                    [
                        str(a.get("acronym") or a.get("name") or ""),
                        str(a.get("expansion") or "OPEN"),
                        str(a.get("current_status") or ""),
                    ]
                    for a in acronyms
                ],
            ),
            _section(MASTER_VIEW_SECTION_HEADINGS[18]),
            "DoD is a completion contract, not a synonym for tests. Mandatory Capability Closure Standard (§11) is related but not named DoD. Program DoD is Master Runbook §21. Vollautonomie §§37–39 are historical/superseded.\n\n",
            _table(["id", "kind", "name", "bucket", "epistemic"], [_entity_row(d) for d in dods]),
            _table(
                ["id", "kind", "name", "bucket", "epistemic"], [_entity_row(s) for s in schemas]
            ),
            f"Drill-down: {_drilldown('DOD_MAP.md')}, {_drilldown('SCHEMA_MAP.md')}, {_drilldown('DATA_CONTRACT_MAP.md')}.\n\n",
            _section(MASTER_VIEW_SECTION_HEADINGS[19]),
            "```text\n",
            f"CURRENT_ORIGIN_MAIN_SHA={meta.get('origin_main_sha', 'OPEN')}\n",
            f"ENTITY_TOTAL={len(entities)}\n",
            f"HUB_RELATION_COUNT={len(hub_rels)}\n",
            f"STRUCTURAL_RELATION_COUNT={len(struct)}\n",
            f"RUNTIME_RELATION_COUNT={len(runtime)}\n",
            f"AUTHORITY_RELATION_COUNT={len(authority)}\n",
            f"UNRESOLVED_CONTRADICTION_COUNT={len(unresolved)}\n",
            f"OKX_CENSUS_COMPLETE={str(meta.get('okx_census_complete', False)).lower()}\n",
            f"MASTER_V2_CENSUS_COMPLETE={str(meta.get('master_v2_census_complete', False)).lower()}\n",
            f"DOUBLE_PLAY_CENSUS_COMPLETE={str(meta.get('double_play_census_complete', False)).lower()}\n",
            f"FAMILY_CENSUS_COMPLETE={str(meta.get('family_census_complete', False)).lower()}\n",
            f"CHILD_CENSUS_COMPLETE={str(meta.get('child_census_complete', False)).lower()}\n",
            f"SSOT_CHILD_CENSUS_COMPLETE={str(meta.get('ssot_child_census_complete', False)).lower()}\n",
            f"MMR_CENSUS_COMPLETE={str(meta.get('mmr_census_complete', False)).lower()}\n",
            f"SCHEMA_FILE_INVENTORY_COMPLETE={str(meta.get('schema_file_inventory_complete', False)).lower()}\n",
            f"MASTER_V2_CAPABILITY_SPEC_INVENTORY_COMPLETE={str(meta.get('master_v2_capability_spec_inventory_complete', False)).lower()}\n",
            f"MASTER_V2_MODULE_FILE_INVENTORY_COMPLETE={str(meta.get('master_v2_module_file_inventory_complete', False)).lower()}\n",
            f"TERMINOLOGY_CENSUS_COMPLETE={str(meta.get('terminology_census_complete', False)).lower()}\n",
            f"ACRONYM_CENSUS_COMPLETE={str(meta.get('acronym_census_complete', False)).lower()}\n",
            f"DOD_CENSUS_COMPLETE={str(meta.get('dod_census_complete', False)).lower()}\n",
            f"SCHEMA_CENSUS_COMPLETE={str(meta.get('schema_census_complete', False)).lower()}\n",
            f"HISTORICAL_TERMINOLOGY_CENSUS_COMPLETE={str(meta.get('historical_terminology_census_complete', False)).lower()}\n",
            f"OKX_CURRENT_TREE_CENSUS_COMPLETE={str(meta.get('okx_current_tree_census_complete', False)).lower()}\n",
            f"OKX_HISTORICAL_CENSUS_COMPLETE={str(meta.get('okx_historical_census_complete', False)).lower()}\n",
            f"SCHEMA_FIELD_ENUMERATION_COMPLETE={str(meta.get('schema_field_enumeration_complete', False)).lower()}\n",
            f"SYSTEM_ATLAS_MASTER_VIEW_COMPLETE={str(meta.get('system_atlas_master_view_complete', False)).lower()}\n",
            f"GLOBAL_CENSUS_EXHAUSTED={str(meta.get('global_census_exhausted', False)).lower()}\n",
            _repo_atlas_flag_text(meta),
            f"ACRONYM_CENSUS_INVENTORY_COMPLETE={str(meta.get('acronym_census_inventory_complete', False)).lower()}\n",
            f"ACRONYM_EXPANSIONS_RESOLVED={str(meta.get('acronym_expansions_resolved', False)).lower()}\n",
            "```\n\n",
            "Closed census domains (scoped search or file inventory done; not ontology-solved):\n\n",
            _table(
                ["id", "flag", "primary_class", "additional", "remaining"],
                _incompleteness_table_rows(closed_domains),
            ),
            "Remaining census domains:\n\n",
            _table(
                ["id", "flag", "primary_class", "additional", "remaining"],
                _incompleteness_table_rows(remaining_domains),
            ),
            _table(["kind", "count"], [[k, str(v)] for k, v in sorted(by_kind.items())]),
            "One-question test: a new engineer can start here and see what exists, how hubs are wired, what Master V2/Double Play/Families/MMR mean (including polyvalence), where OKX/risk/safety live, which data crosses boundaries, current vs historical, and where to drill for proof. Remaining incompleteness is OPEN acronym expansions plus owner-decision/runtime facts that the Atlas faithfully records. External forensic corpus is `NOT_STARTED` and does not invalidate `REPO_ATLAS_CENSUS_COMPLETE`. Therefore `SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true` while `GLOBAL_CENSUS_EXHAUSTED=false`.\n\n",
            f"Full counters: {_drilldown('COVERAGE_REPORT.md')}.\n\n",
            _section("Drill-down views"),
            drill + "\n",
        ]
    )
    return "".join(parts)


def _gen_graph(title: str, relations: list[dict[str, Any]], note: str) -> str:
    rows = [_rel_row(r) for r in relations]
    return (
        _HEADER
        + f"# {title}\n\n"
        + _BANNER
        + note
        + "\n\n"
        + _table(["id", "source", "type", "target", "epistemic", "evidence"], rows)
    )


def _okx_entities(entities: list[dict[str, Any]], kinds: set[str]) -> list[dict[str, Any]]:
    return [e for e in entities if str(e.get("kind")) in kinds]


def _okx_domain_group(path: str) -> str:
    parts = [p for p in str(path or "").split("/") if p]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v5":
        return parts[2]
    return ""


def _gen_okx_map(
    entities: list[dict[str, Any]],
    meta: dict[str, Any],
    atlas: dict[str, Any],
) -> str:
    hosts = _okx_entities(entities, {"OKX_HOST"})
    feats = _okx_entities(entities, {"OKX_FEATURE"})
    eps = _okx_entities(entities, {"VENUE_ENDPOINT"})
    fields = _okx_entities(entities, {"VENUE_FIELD"})
    ep_cls = atlas["records"].get("census/okx_endpoint_classification.yaml") or {}
    field_c = atlas["records"].get("census/okx_field_census.yaml") or {}
    fix_c = atlas["records"].get("census/okx_fixture_census.yaml") or {}
    auth = atlas["records"].get("venue/okx/authentication.yaml") or {}
    parts = [
        _HEADER,
        "# OKX Integration Map\n\n",
        _BANNER,
        "OKX is a first-class venue domain. XPERP is one product/instrument family, not the organizing center.\n\n",
        f"`OKX_CENSUS_COMPLETE={str(meta.get('okx_census_complete', False)).lower()}`  \n",
        f"`OKX_CENSUS_SCOPE={meta.get('okx_census_scope', 'OPEN')}`\n\n",
        "```text\n",
        f"OKX_RAW_API_PATH_HIT_COUNT={ep_cls.get('okx_raw_api_path_hit_count', 'OPEN')}\n",
        f"OKX_UNIQUE_ENDPOINT_CANDIDATE_COUNT={ep_cls.get('okx_unique_endpoint_candidate_count', 'OPEN')}\n",
        f"OKX_MODELED_ENDPOINT_COUNT={ep_cls.get('okx_modeled_endpoint_count', 'OPEN')}\n",
        f"OKX_GREP_NOISE_COUNT={ep_cls.get('okx_grep_noise_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_ENDPOINT_COUNT={ep_cls.get('okx_unclassified_endpoint_count', 'OPEN')}\n",
        f"OKX_FIELD_TOKEN_COUNT={field_c.get('okx_field_token_count', 'OPEN')}\n",
        f"OKX_MODELED_FIELD_COUNT={field_c.get('okx_modeled_field_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_MATERIAL_FIELD_COUNT={field_c.get('okx_unclassified_material_field_count', 'OPEN')}\n",
        f"OKX_FIXTURE_CANDIDATE_COUNT={fix_c.get('okx_fixture_candidate_count', 'OPEN')}\n",
        f"OKX_CONFIRMED_FIXTURE_COUNT={fix_c.get('okx_confirmed_fixture_count', 'OPEN')}\n",
        f"OKX_RAW_RESPONSE_COUNT={fix_c.get('okx_raw_response_count', 'OPEN')}\n",
        f"OKX_DISTINCT_RESPONSE_SHAPE_COUNT={fix_c.get('okx_distinct_response_shape_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_FIXTURE_COUNT={fix_c.get('okx_unclassified_fixture_count', 'OPEN')}\n",
        f"OKX_FIXTURE_BYTES_OR_STRUCTURE_INSPECTED_COUNT={fix_c.get('okx_fixture_bytes_or_structure_inspected_count', 'OPEN')}\n",
        f"OKX_UNINSPECTED_MATERIAL_FIXTURE_COUNT={fix_c.get('okx_uninspected_material_fixture_count', 'OPEN')}\n",
        f"OKX_PRODUCT_TYPE_CENSUS_COMPLETE={str((atlas['records'].get('census/okx_product_types.yaml') or {}).get('okx_product_type_census_complete', False)).lower()}\n",
        "```\n\n",
        _section("Product types (Peak_Trade evidence)"),
        _table(
            ["product_type", "status", "canonical_support", "runtime_reachability"],
            _okx_product_type_rows(atlas),
        ),
        _section("Hosts"),
        _table(
            ["id", "name", "status", "epistemic"],
            [
                [
                    str(h.get("id")),
                    str(h.get("name") or ""),
                    str(h.get("current_status") or ""),
                    _epi_label(str(h.get("epistemic_class") or "")),
                ]
                for h in hosts
            ],
        ),
        _section("Auth / signing (no secrets)"),
        (
            f"Scheme `{auth.get('scheme')}`; signer `{auth.get('signer')}`; "
            f"demo header `{auth.get('demo_header')}`; "
            f"auth_inventory_complete={str(auth.get('auth_inventory_complete', False)).lower()}. "
            "Credential values are not recorded.\n\n"
        ),
        _section("Features"),
        _table(
            ["id", "category", "status", "auth"],
            [
                [
                    str(f.get("id")),
                    str(f.get("category") or ""),
                    str(f.get("current_status") or ""),
                    str(f.get("auth_required") or ""),
                ]
                for f in feats
            ],
        ),
        _section("Endpoints"),
        _table(
            ["id", "method", "path", "domain", "mutation", "status"],
            [
                [
                    str(e.get("id")),
                    str(e.get("method") or ""),
                    str(e.get("path") or e.get("name") or ""),
                    _okx_domain_group(str(e.get("path") or "")),
                    str(e.get("mutation_class") or ""),
                    str(e.get("current_status") or ""),
                ]
                for e in eps
            ],
        ),
        _section("Fields"),
        _table(
            ["id", "field", "identity_role", "status"],
            [
                [
                    str(f.get("id")),
                    str(f.get("field") or f.get("name") or ""),
                    str(f.get("identity_role") or ""),
                    _epi_label(str(f.get("epistemic_class") or "")),
                ]
                for f in fields
            ],
        ),
        _section("XPERP / uly / quote identity (not census scope)"),
        "See contradiction `C-OKX-QUOTE-ULY-001` and feature `OKX_FEATURE:quote_identity_from_quoteCcy_or_instId`.\n",
    ]
    return "".join(parts)


def _gen_okx_matrix(entities: list[dict[str, Any]]) -> str:
    feats = _okx_entities(entities, {"OKX_FEATURE"})
    rows = [
        [
            str(f.get("name") or f.get("id")),
            str(f.get("first_proven_occurrence") or "OPEN"),
            str(f.get("current_implementation") or ""),
            str(f.get("historical_implementation") or ""),
            str(f.get("product_types") or ""),
            str(f.get("endpoints") or ""),
            str(f.get("auth_required") or ""),
            str(f.get("current_status") or ""),
            str(f.get("canonical_support") or ""),
            str(f.get("runtime_reachable") or ""),
            str(f.get("tested") or ""),
            str(f.get("forensic_evidence") or "")[:80],
            str(f.get("open_gaps") or ""),
        ]
        for f in feats
    ]
    return (
        _HEADER
        + "# OKX Feature Matrix\n\n"
        + _BANNER
        + _table(
            [
                "FEATURE",
                "FIRST_PROVEN_OCCURRENCE",
                "CURRENT_IMPLEMENTATION",
                "HISTORICAL_IMPLEMENTATION",
                "PRODUCT_TYPES",
                "ENDPOINTS",
                "AUTH",
                "CURRENT_STATUS",
                "CANONICAL_SUPPORT",
                "RUNTIME_REACHABLE",
                "TESTED",
                "FORENSIC_EVIDENCE",
                "OPEN_GAPS",
            ],
            rows,
        )
    )


def _gen_okx_chronology(atlas: dict[str, Any]) -> str:
    block = atlas["records"].get("venue/okx/chronology.yaml") or {}
    events = sorted(
        block.get("events") or [], key=lambda e: str(e.get("sort_key") or e.get("id") or "")
    )
    rows = [
        [
            str(e.get("id")),
            str(e.get("when") or "OPEN"),
            str(e.get("what") or ""),
            _epi_label(str(e.get("epistemic_status") or "")),
            str(e.get("evidence") or ""),
        ]
        for e in events
    ]
    hist = atlas["records"].get("census/okx_historical.yaml") or {}
    feat_rows = [
        [
            str(f.get("id")),
            str(f.get("first_proven_date") or "OPEN"),
            str(f.get("current_status") or ""),
            str(f.get("feature_category") or ""),
            str(f.get("auth_implementation") or "")[:80],
        ]
        for f in hist.get("features") or []
    ]
    uly = hist.get("uly_quote_adjudication") or {}
    return (
        _HEADER
        + "# OKX Chronology\n\n"
        + _BANNER
        + "Dates/PRs are listed only when git or document evidence supports them. "
        "Document-internal dates are not introduction proof. "
        "Shallow-clone artefact dates are superseded after unshallow.\n\n"
        + f"GIT_IS_SHALLOW={str(hist.get('git_is_shallow', 'OPEN')).lower()}\n\n"
        + f"OKX_FIRST_PROVEN_NAMED_IMPLEMENTATION={hist.get('first_proven_okx_named_implementation_commit', 'OPEN')}\n\n"
        + f"OKX_NAMED_PATH_DELETIONS_ON_ORIGIN_MAIN={hist.get('okx_named_path_deletions_on_origin_main', 'OPEN')}\n\n"
        + f"XPERP_HISTORICAL_ULY_HANDLER_FOUND={str(uly.get('handler_found', False)).lower()}\n\n"
        + f"XPERP_HISTORICAL_QUOTE_MAPPING_FOUND={str(uly.get('quote_from_uly_found', False)).lower()}\n\n"
        + _table(["id", "when", "what", "epistemic", "evidence"], rows)
        + "\n"
        + _section("Historical feature archaeology")
        + _table(
            ["id", "first_proven", "status", "category", "auth"],
            feat_rows,
        )
    )


def _gen_safety(entities: list[dict[str, Any]], chains: list[dict[str, Any]]) -> str:
    gates = [e for e in entities if str(e.get("kind")) in {"GATE", "GUARD", "PERMIT", "POLICY"}]
    parts = [
        _HEADER,
        "# Safety / Governance Map\n\n",
        _BANNER,
        _section("Mechanisms"),
        _table(
            ["id", "kind", "fail", "status"],
            [
                [
                    str(g.get("id")),
                    str(g.get("kind")),
                    str(g.get("fail_closed") or ""),
                    str(g.get("current_status") or ""),
                ]
                for g in gates
            ],
        ),
        _section("Mutation-path chains (actual wiring; missing edges explicit)"),
    ]
    for chain in chains:
        steps = " -> ".join(str(s) for s in (chain.get("steps") or []))
        missing = ",".join(str(x) for x in (chain.get("missing_edges") or [])) or "(none recorded)"
        parts.append(
            f"### {chain.get('id')}\n\n"
            f"- epistemic: `{_epi_label(str(chain.get('epistemic_status') or ''))}`\n"
            f"- chain: `{steps}`\n"
            f"- missing: `{missing}`\n"
            f"- evidence: `{chain.get('evidence')}`\n\n"
        )
    return "".join(parts)


def _gen_data_contracts(entities: list[dict[str, Any]], lineage: list[dict[str, Any]]) -> str:
    contracts = [e for e in entities if str(e.get("kind")) in {"DATA_CONTRACT", "STATE_FIELD"}]
    return (
        _HEADER
        + "# Data Contract / Identity / Unit Map\n\n"
        + _BANNER
        + _section("Contracts and fields")
        + _table(
            ["id", "kind", "unit", "status"],
            [
                [
                    str(c.get("id")),
                    str(c.get("kind")),
                    str(c.get("unit") or ""),
                    str(c.get("current_status") or ""),
                ]
                for c in contracts
            ],
        )
        + _section("Lineage (see DATA_LINEAGE_MAP.md)")
        + f"Lineage records: {len(lineage)}\n"
    )


def _gen_provenance(atlas: dict[str, Any]) -> str:
    block = atlas["records"].get("provenance/timeline.yaml") or {}
    events = sorted(
        block.get("events") or [], key=lambda e: str(e.get("sort_key") or e.get("id") or "")
    )
    rows = [
        [
            str(e.get("id")),
            str(e.get("when") or "OPEN"),
            str(e.get("what") or ""),
            _epi_label(str(e.get("epistemic_status") or "")),
            str(e.get("commit_or_pr") or ""),
        ]
        for e in events
    ]
    return (
        _HEADER
        + "# Provenance Timeline\n\n"
        + _BANNER
        + _table(["id", "when", "what", "epistemic", "commit_or_pr"], rows)
    )


def _gen_guidance(
    closures: list[dict[str, Any]],
    computed: dict[str, dict[str, list[str]]],
    emap: dict[str, dict[str, Any]],
) -> str:
    parts = [
        _HEADER,
        "# Build Guidance\n\n",
        _BANNER,
        "If you change X, inspect the listed contracts and invariants.\n\n",
    ]
    for c in closures:
        cid = str(c.get("id"))
        inspect = c.get("inspect") or []
        parts.append(f"### {cid} — {c.get('title') or ''}\n\n")
        parts.append(f"- inspect: `{', '.join(str(x) for x in inspect)}`\n")
        parts.append(f"- upstream: `{', '.join(str(x) for x in (c.get('upstream') or []))}`\n")
        parts.append(f"- downstream: `{', '.join(str(x) for x in (c.get('downstream') or []))}`\n")
        parts.append(f"- evidence: `{c.get('evidence')}`\n\n")
        for dep in inspect:
            cl = computed.get(str(dep), {})
            if cl:
                parts.append(
                    f"  - `{dep}` transitive upstream: "
                    f"`{', '.join(cl.get('transitive_upstream') or []) or '(none)'}`\n"
                )
        parts.append("\n")
    return "".join(parts)


def _gen_contradictions(contradictions: list[dict[str, Any]]) -> str:
    parts = [_HEADER, "# Contradiction Register\n\n", _BANNER]
    for c in contradictions:
        parts.append(
            f"### {c.get('id')}\n\n"
            f"- subject: `{c.get('subject')}`\n"
            f"- claim_a ({c.get('status_a')}): {c.get('claim_a')}\n"
            f"- source_a: `{c.get('source_a')}`\n"
            f"- claim_b ({c.get('status_b')}): {c.get('claim_b')}\n"
            f"- source_b: `{c.get('source_b')}`\n"
            f"- resolved: `{c.get('resolved')}`\n"
            f"- adjudication: {c.get('current_adjudication')}\n"
            f"- next_proof: {c.get('next_proof_needed')}\n\n"
        )
    return "".join(parts)


def _gen_mv2(
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    fcm: list[dict[str, Any]],
    computed: dict[str, dict[str, list[str]]],
) -> str:
    mv2 = [
        e
        for e in entities
        if "master_v2" in str(e.get("id")).lower() or str(e.get("kind")) in {"FUNCTIONAL_CORE"}
    ]
    dp_rels = [
        r
        for r in relations
        if "double_play" in str(r.get("source")).lower()
        or "double_play" in str(r.get("target")).lower()
        or "master_v2" in str(r.get("source")).lower()
    ]
    return (
        _HEADER
        + "# Master V2 / Double Play Map\n\n"
        + _BANNER
        + "Owner-bound Atlas relation (exact token `HAS_FUNCTIONAL_CORE` not found on origin/main): Master V2 and Double Play are Modul-Owner of one Trading Core. Census kind `FUNCTIONAL_CORE` is a label, not a Master Runbook token.\n\n"
        + "Not competing generations. Historical Vollautonomie ordering vs current Master Runbook ordering is CONTRADICTED (see C-DP-ORDER-001). Cap23 exclusivity is scoped to the analytical host; canary is a parallel instrument authority (C-CAP23-VS-CANARY-INSTRUMENT-001).\n\n"
        + _section("Entities")
        + _table(
            ["id", "kind", "status", "epistemic"],
            [
                [
                    str(e.get("id")),
                    str(e.get("kind")),
                    str(e.get("current_status") or ""),
                    _epi_label(str(e.get("epistemic_class") or "")),
                ]
                for e in mv2
            ],
        )
        + _section("Relations involving Master V2 / Double Play")
        + _table(
            ["id", "source", "type", "target", "epistemic", "evidence"],
            [_rel_row(r) for r in dp_rels],
        )
        + _section("Family/Child/MMR records (heterogeneous meanings; not collapsed)")
        + _table(
            ["id", "parent", "type", "child", "meaning_class", "epistemic"],
            [
                [
                    str(r.get("id")),
                    str(r.get("parent") or ""),
                    str(r.get("relation_type") or ""),
                    str(r.get("child") or ""),
                    str(r.get("meaning_class") or ""),
                    _epi_label(str(r.get("epistemic_status") or "")),
                ]
                for r in fcm
            ],
        )
    )


def _gen_fcm(fcm: list[dict[str, Any]], entities: list[dict[str, Any]]) -> str:
    terms = [
        e
        for e in entities
        if str(e.get("kind")) in {"FAMILY", "CHILD", "SSOT_CHILD", "MMR", "TERM"}
    ]
    return (
        _HEADER
        + "# Family / Child / MMR Map\n\n"
        + _BANNER
        + "These terms have multiple observed meanings. They are not a single hierarchy.\n\n"
        + _section("Terminology entities")
        + _table(
            ["id", "kind", "status", "do_not_confuse"],
            [
                [
                    str(t.get("id")),
                    str(t.get("kind")),
                    str(t.get("current_status") or ""),
                    str(t.get("do_not_confuse_with") or ""),
                ]
                for t in terms
            ],
        )
        + _section("Observed parent/child records")
        + _table(
            ["id", "parent", "type", "child", "role", "epistemic"],
            [
                [
                    str(r.get("id")),
                    str(r.get("parent") or ""),
                    str(r.get("relation_type") or ""),
                    str(r.get("child") or ""),
                    str(r.get("role") or ""),
                    _epi_label(str(r.get("epistemic_status") or "")),
                ]
                for r in fcm
            ],
        )
    )


def _gen_full_dep(
    entities: list[dict[str, Any]],
    computed: dict[str, dict[str, list[str]]],
    relations: list[dict[str, Any]],
) -> str:
    parts = [
        _HEADER,
        "# Full Dependency Graph\n\n",
        _BANNER,
        "Inverse CALLS edges are derived as CALLED_BY for downstream listing only; they are not stored as independent facts.\n\n",
    ]
    for ent in entities:
        eid = str(ent["id"])
        cl = computed.get(eid, {})
        if not any(cl.values()):
            continue
        parts.append(f"### {eid}\n\n")
        parts.append(
            f"- direct_upstream: `{', '.join(cl.get('direct_upstream') or []) or '(none)'}`\n"
        )
        parts.append(
            f"- transitive_upstream: `{', '.join(cl.get('transitive_upstream') or []) or '(none)'}`\n"
        )
        parts.append(
            f"- direct_downstream: `{', '.join(cl.get('direct_downstream') or []) or '(none)'}`\n"
        )
        parts.append(
            f"- transitive_downstream: `{', '.join(cl.get('transitive_downstream') or []) or '(none)'}`\n\n"
        )
    return "".join(parts)


def _gen_lineage(lineage: list[dict[str, Any]]) -> str:
    rows = [
        [
            str(x.get("id")),
            str(x.get("value") or ""),
            str(x.get("origin") or ""),
            str(x.get("raw_source_field") or ""),
            str(x.get("unit") or ""),
            str(x.get("current_path") or ""),
            _epi_label(str(x.get("epistemic_status") or "")),
        ]
        for x in lineage
    ]
    return (
        _HEADER
        + "# Data Lineage Map\n\n"
        + _BANNER
        + _table(["id", "value", "origin", "raw_field", "unit", "current_path", "epistemic"], rows)
    )


def _gen_config(configs: list[dict[str, Any]]) -> str:
    rows = [
        [
            str(c.get("id")),
            str(c.get("key") or ""),
            str(c.get("source") or ""),
            str(c.get("default") or ""),
            str(c.get("consumers") or ""),
            str(c.get("runtime_effect") or ""),
            str(c.get("current_status") or ""),
        ]
        for c in configs
    ]
    return (
        _HEADER
        + "# Configuration Wiring\n\n"
        + _BANNER
        + _table(["id", "key", "source", "default", "consumers", "runtime_effect", "status"], rows)
    )


def _gen_traces(entrypoints: list[dict[str, Any]]) -> str:
    parts = [_HEADER, "# Entrypoint Runtime Traces\n\n", _BANNER]
    for ep in entrypoints:
        parts.append(f"### {ep.get('id')} — {ep.get('name') or ''}\n\n")
        parts.append(f"- path: `{ep.get('path')}`\n")
        parts.append(f"- class: `{ep.get('entrypoint_class')}`\n")
        parts.append(f"- epistemic: `{_epi_label(str(ep.get('epistemic_status') or ''))}`\n")
        parts.append(f"- network: `{ep.get('network_io')}`\n")
        parts.append(f"- evidence: `{ep.get('evidence')}`\n\n")
        for i, step in enumerate(ep.get("steps") or [], start=1):
            parts.append(
                f"  {i}. `{step.get('caller')}` -> `{step.get('callee')}` "
                f"gate=`{step.get('gate')}` fail=`{step.get('failure_mode')}`\n"
            )
        parts.append("\n")
        missing = ep.get("missing_wiring") or []
        if missing:
            parts.append(f"- missing_wiring: `{', '.join(str(x) for x in missing)}`\n\n")
    return "".join(parts)


def _gen_gaps(gaps: list[dict[str, Any]]) -> str:
    rows = [
        [
            str(g.get("id")),
            str(g.get("class") or ""),
            str(g.get("entity") or g.get("subject") or ""),
            _epi_label(str(g.get("epistemic_status") or "OPEN")),
            str(g.get("notes") or "")[:120],
        ]
        for g in gaps
    ]
    return (
        _HEADER
        + "# Orphan and Wiring Gaps\n\n"
        + _BANNER
        + _table(["id", "class", "entity", "epistemic", "notes"], rows)
    )


def _gen_coverage(
    meta: dict[str, Any],
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    closures: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    lineage: list[dict[str, Any]],
    configs: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
    atlas: dict[str, Any],
) -> str:
    by_kind: dict[str, int] = defaultdict(int)
    for e in entities:
        by_kind[str(e.get("kind"))] += 1
    epi_rel: dict[str, int] = defaultdict(int)
    for r in relations:
        epi_rel[str(r.get("epistemic_status"))] += 1
    okx_feat = sum(1 for e in entities if str(e.get("kind")) == "OKX_FEATURE")
    okx_ep = sum(1 for e in entities if str(e.get("kind")) == "VENUE_ENDPOINT")
    okx_field = sum(1 for e in entities if str(e.get("kind")) == "VENUE_FIELD")
    inc = _incompleteness_record(atlas)
    lines = [
        _HEADER,
        "# Coverage Report\n\n",
        _BANNER,
        "This Atlas does not claim universe completeness because generation succeeded.\n\n",
        "```text\n",
        f"ENTITY_TOTAL={len(entities)}\n",
        f"STRUCTURAL_RELATION_COUNT={sum(1 for r in relations if r.get('graph') == 'structural')}\n",
        f"RUNTIME_RELATION_COUNT={sum(1 for r in relations if r.get('graph') == 'runtime')}\n",
        f"AUTHORITY_RELATION_COUNT={sum(1 for r in relations if r.get('graph') == 'authority_evidence')}\n",
        f"OPEN_RELATION_COUNT={epi_rel.get('OPEN', 0)}\n",
        f"CONTRADICTED_RELATION_COUNT={epi_rel.get('CONTRADICTED', 0)}\n",
        f"HYPOTHESIS_COUNT={epi_rel.get('HYPOTHESIS', 0) + sum(1 for e in entities if e.get('epistemic_class') == 'HYPOTHESIS')}\n",
        f"OKX_FEATURE_TOTAL={okx_feat}\n",
        f"OKX_ENDPOINT_COUNT={okx_ep}\n",
        f"OKX_FIELD_COUNT={okx_field}\n",
        f"UNRESOLVED_CONTRADICTION_COUNT={sum(1 for c in contradictions if not c.get('resolved'))}\n",
        f"CAPABILITY_DEPENDENCY_CLOSURE_COUNT={len(closures)}\n",
        f"ORPHAN_COMPONENT_COUNT={sum(1 for g in gaps if g.get('class') == 'DEFINED_BUT_NO_CONSUMER')}\n",
        f"DATA_LINEAGE_RECORD_COUNT={len(lineage)}\n",
        f"CONFIG_WIRING_RECORD_COUNT={len(configs)}\n",
        f"OKX_CENSUS_COMPLETE={str(meta.get('okx_census_complete', False)).lower()}\n",
        f"MASTER_V2_CENSUS_COMPLETE={str(meta.get('master_v2_census_complete', False)).lower()}\n",
        f"DOUBLE_PLAY_CENSUS_COMPLETE={str(meta.get('double_play_census_complete', False)).lower()}\n",
        f"FAMILY_CENSUS_COMPLETE={str(meta.get('family_census_complete', False)).lower()}\n",
        f"CHILD_CENSUS_COMPLETE={str(meta.get('child_census_complete', False)).lower()}\n",
        f"SSOT_CHILD_CENSUS_COMPLETE={str(meta.get('ssot_child_census_complete', False)).lower()}\n",
        f"MMR_CENSUS_COMPLETE={str(meta.get('mmr_census_complete', False)).lower()}\n",
        f"SCHEMA_FILE_INVENTORY_COMPLETE={str(meta.get('schema_file_inventory_complete', False)).lower()}\n",
        f"MASTER_V2_CAPABILITY_SPEC_INVENTORY_COMPLETE={str(meta.get('master_v2_capability_spec_inventory_complete', False)).lower()}\n",
        f"MASTER_V2_MODULE_FILE_INVENTORY_COMPLETE={str(meta.get('master_v2_module_file_inventory_complete', False)).lower()}\n",
        f"TERMINOLOGY_CENSUS_COMPLETE={str(meta.get('terminology_census_complete', False)).lower()}\n",
        f"ACRONYM_CENSUS_COMPLETE={str(meta.get('acronym_census_complete', False)).lower()}\n",
        f"DOD_CENSUS_COMPLETE={str(meta.get('dod_census_complete', False)).lower()}\n",
        f"SCHEMA_CENSUS_COMPLETE={str(meta.get('schema_census_complete', False)).lower()}\n",
        f"HISTORICAL_TERMINOLOGY_CENSUS_COMPLETE={str(meta.get('historical_terminology_census_complete', False)).lower()}\n",
        f"OKX_CURRENT_TREE_CENSUS_COMPLETE={str(meta.get('okx_current_tree_census_complete', False)).lower()}\n",
        f"OKX_HISTORICAL_CENSUS_COMPLETE={str(meta.get('okx_historical_census_complete', False)).lower()}\n",
        f"SCHEMA_FIELD_ENUMERATION_COMPLETE={str(meta.get('schema_field_enumeration_complete', False)).lower()}\n",
        f"SYSTEM_ATLAS_PRIMARY_ENTRYPOINT={meta.get('system_atlas_primary_entrypoint', 'docs/system_atlas/generated/SYSTEM_ATLAS.md')}\n",
        f"SYSTEM_ATLAS_MASTER_VIEW_COMPLETE={str(meta.get('system_atlas_master_view_complete', False)).lower()}\n",
        f"GLOBAL_CENSUS_EXHAUSTED={str(meta.get('global_census_exhausted', False)).lower()}\n",
        _repo_atlas_flag_text(meta),
        f"SYSTEM_ATLAS_DRILLDOWN_LINKS_VALID={str(meta.get('system_atlas_drilldown_links_valid', False)).lower()}\n",
        f"SYSTEM_ATLAS_ALL_MAJOR_DOMAINS_REPRESENTED={str(meta.get('system_atlas_all_major_domains_represented', False)).lower()}\n",
        f"SYSTEM_ATLAS_CURRENT_HISTORICAL_SPLIT_VALID={str(meta.get('system_atlas_current_historical_split_valid', False)).lower()}\n",
        f"SYSTEM_ATLAS_GRAPH_RELATIONS_BACKED_BY_MODEL={str(meta.get('system_atlas_graph_relations_backed_by_model', False)).lower()}\n",
        "ATLAS_IMPACT_CHECKER=scripts/ops/check_system_atlas_impact_v1.py\n",
        f"PROJECT_NATIVE_TERM_COUNT={sum(1 for e in entities if str(e.get('kind')) in {'TERM', 'ACRONYM', 'DOD', 'SCHEMA'})}\n",
        f"ACRONYM_COUNT={sum(1 for e in entities if str(e.get('kind')) == 'ACRONYM')}\n",
        f"DOD_COUNT={sum(1 for e in entities if str(e.get('kind')) == 'DOD')}\n",
        f"SCHEMA_COUNT={sum(1 for e in entities if str(e.get('kind')) == 'SCHEMA')}\n",
        f"TERMINOLOGY_COLLISION_COUNT={len(collisions)}\n",
        f"UNRESOLVED_TERM_COUNT={sum(1 for e in entities if str(e.get('kind')) in {'TERM', 'ACRONYM', 'DOD', 'SCHEMA'} and e.get('epistemic_class') in {'OPEN', 'CONTRADICTED'})}\n",
        f"GIT_IS_SHALLOW={str(meta.get('git_is_shallow', True)).lower()}\n",
        f"HISTORICAL_FETCH_PERFORMED={str(meta.get('historical_fetch_performed', False)).lower()}\n",
        f"OKX_HISTORICAL_FEATURE_COUNT={len((atlas['records'].get('census/okx_historical.yaml') or {}).get('features') or [])}\n",
        f"HISTORICAL_PROJECT_NATIVE_TERM_COUNT={(atlas['records'].get('census/historical_terminology.yaml') or {}).get('historical_project_native_term_count', 'OPEN')}\n",
        f"HISTORICAL_WIRING_CHANGE_COUNT={(atlas['records'].get('census/historical_wiring.yaml') or {}).get('historical_wiring_change_count', 'OPEN')}\n",
        f"SRC_SCHEMA_CANDIDATE_COUNT={(atlas['records'].get('census/schema_like_src.yaml') or {}).get('src_schema_candidate_count', 'OPEN')}\n",
        f"SRC_ACCEPTED_SCHEMA_COUNT={(atlas['records'].get('census/schema_like_src.yaml') or {}).get('src_accepted_schema_count', 'OPEN')}\n",
        f"SRC_DATA_CONTRACT_COUNT={(atlas['records'].get('census/schema_like_src.yaml') or {}).get('src_data_contract_count', 'OPEN')}\n",
        f"SRC_TYPE_ONLY_COUNT={(atlas['records'].get('census/schema_like_src.yaml') or {}).get('src_type_only_count', 'OPEN')}\n",
        f"SRC_UNADJUDICATED_SCHEMA_CANDIDATE_COUNT={(atlas['records'].get('census/schema_like_src.yaml') or {}).get('src_unadjudicated_schema_candidate_count', 'OPEN')}\n",
        f"OKX_RAW_API_PATH_HIT_COUNT={(atlas['records'].get('census/okx_endpoint_classification.yaml') or {}).get('okx_raw_api_path_hit_count', 'OPEN')}\n",
        f"OKX_UNIQUE_ENDPOINT_CANDIDATE_COUNT={(atlas['records'].get('census/okx_endpoint_classification.yaml') or {}).get('okx_unique_endpoint_candidate_count', 'OPEN')}\n",
        f"OKX_GREP_NOISE_COUNT={(atlas['records'].get('census/okx_endpoint_classification.yaml') or {}).get('okx_grep_noise_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_ENDPOINT_COUNT={(atlas['records'].get('census/okx_endpoint_classification.yaml') or {}).get('okx_unclassified_endpoint_count', 'OPEN')}\n",
        f"OKX_MODELED_ENDPOINT_COUNT={(atlas['records'].get('census/okx_endpoint_classification.yaml') or {}).get('okx_modeled_endpoint_count', 'OPEN')}\n",
        f"OKX_FIELD_TOKEN_COUNT={(atlas['records'].get('census/okx_field_census.yaml') or {}).get('okx_field_token_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_MATERIAL_FIELD_COUNT={(atlas['records'].get('census/okx_field_census.yaml') or {}).get('okx_unclassified_material_field_count', 'OPEN')}\n",
        f"OKX_MODELED_FIELD_COUNT={(atlas['records'].get('census/okx_field_census.yaml') or {}).get('okx_modeled_field_count', 'OPEN')}\n",
        f"OKX_FIXTURE_CANDIDATE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_fixture_candidate_count', 'OPEN')}\n",
        f"OKX_CONFIRMED_FIXTURE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_confirmed_fixture_count', 'OPEN')}\n",
        f"OKX_RAW_RESPONSE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_raw_response_count', 'OPEN')}\n",
        f"OKX_DISTINCT_RESPONSE_SHAPE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_distinct_response_shape_count', 'OPEN')}\n",
        f"OKX_UNCLASSIFIED_FIXTURE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_unclassified_fixture_count', 'OPEN')}\n",
        f"OKX_FIXTURE_BYTES_OR_STRUCTURE_INSPECTED_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_fixture_bytes_or_structure_inspected_count', 'OPEN')}\n",
        f"OKX_UNINSPECTED_MATERIAL_FIXTURE_COUNT={(atlas['records'].get('census/okx_fixture_census.yaml') or {}).get('okx_uninspected_material_fixture_count', 'OPEN')}\n",
        f"ACRONYM_CENSUS_INVENTORY_COMPLETE={str(meta.get('acronym_census_inventory_complete', False)).lower()}\n",
        f"ACRONYM_EXPANSIONS_RESOLVED={str(meta.get('acronym_expansions_resolved', False)).lower()}\n",
        f"ATLAS_LOCALLY_RESOLVABLE_UNSEARCHED_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('locally_resolvable_unsearched_count', 'OPEN')}\n",
        f"ATLAS_REQUIRES_OWNER_DECISION_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('requires_owner_decision_count', 'OPEN')}\n",
        f"ATLAS_REQUIRES_RUNTIME_OBSERVATION_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('requires_runtime_observation_count', 'OPEN')}\n",
        f"ATLAS_REQUIRES_IMPLEMENTATION_CHANGE_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('requires_implementation_change_count', 'OPEN')}\n",
        f"ATLAS_REQUIRES_EXTERNAL_CORPUS_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('requires_external_corpus_count', 'OPEN')}\n",
        f"ATLAS_UNRESOLVED_TERMINOLOGY_COUNT={(atlas['records'].get('census/repo_final_resolution.yaml') or {}).get('unresolved_terminology_count', 'OPEN')}\n",
        f"OKX_PRODUCT_TYPE_CENSUS_COMPLETE={str((atlas['records'].get('census/okx_product_types.yaml') or {}).get('okx_product_type_census_complete', False)).lower()}\n",
        f"OKX_DOCS_CENSUS_COMPLETE={str((meta.get('okx_surface_census') or {}).get('okx_docs_census_complete', False)).lower()}\n",
        f"OKX_TESTS_CENSUS_COMPLETE={str((meta.get('okx_surface_census') or {}).get('okx_tests_census_complete', False)).lower()}\n",
        f"OKX_CONFIG_CENSUS_COMPLETE={str((meta.get('okx_surface_census') or {}).get('okx_config_census_complete', False)).lower()}\n",
        f"OKX_SCRIPTS_CENSUS_COMPLETE={str((meta.get('okx_surface_census') or {}).get('okx_scripts_census_complete', False)).lower()}\n",
        f"OKX_EVIDENCE_CENSUS_COMPLETE={str((meta.get('okx_surface_census') or {}).get('okx_evidence_census_complete', False)).lower()}\n",
        "```\n\n",
        _section("Entity by kind"),
        _table(["kind", "count"], [[k, str(v)] for k, v in sorted(by_kind.items())]),
        _section("Named gaps"),
        "\n".join(f"- `{g}`" for g in (meta.get("named_gaps") or [])) + "\n\n",
        _section("Census incompleteness (five-class)"),
        "Closed domains are scoped search or file inventory, not ontology-complete.\n\n",
        _table(
            ["id", "flag", "primary_class", "additional", "remaining"],
            _incompleteness_table_rows(list(inc.get("closed_domains") or [])),
        ),
        "Remaining domains:\n\n",
        _table(
            ["id", "flag", "primary_class", "additional", "remaining"],
            _incompleteness_table_rows(list(inc.get("remaining_domains") or [])),
        ),
        "Completeness-flag reasons (`completeness_flags.*`):\n\n",
        _table(
            ["id", "flag", "primary_class", "additional", "remaining"],
            _incompleteness_table_rows(list(inc.get("completeness_flag_reasons") or [])),
        ),
    ]
    return "".join(lines)


def _gen_terminology(entities: list[dict[str, Any]]) -> str:
    terms = [
        e
        for e in entities
        if str(e.get("kind"))
        in {"TERM", "ACRONYM", "DOD", "SCHEMA", "FAMILY", "CHILD", "SSOT_CHILD", "MMR"}
    ]
    rows = [
        [
            str(t.get("id")),
            str(t.get("kind")),
            str(t.get("name") or ""),
            str(t.get("current_status") or ""),
            _epi_label(str(t.get("epistemic_class") or "")),
            str(t.get("do_not_confuse_with") or "")[:80],
        ]
        for t in terms
    ]
    return (
        _HEADER
        + "# Project Terminology\n\n"
        + _BANNER
        + "Seed vocabulary is not complete. Status OPEN means expansion/definition is unproven.\n\n"
        + _table(["id", "kind", "name", "status", "epistemic", "do_not_confuse"], rows)
    )


def _gen_acronyms(entities: list[dict[str, Any]]) -> str:
    rows = [
        [
            str(e.get("acronym") or e.get("name") or ""),
            str(e.get("expansion") or "OPEN"),
            str(e.get("expansion_source") or "OPEN"),
            str(e.get("current_status") or ""),
            _epi_label(str(e.get("epistemic_class") or "")),
            str(e.get("do_not_confuse_with") or "")[:80],
        ]
        for e in entities
        if str(e.get("kind")) == "ACRONYM"
    ]
    return (
        _HEADER
        + "# Acronym Register\n\n"
        + _BANNER
        + "Never invent expansions. OPEN if unproven.\n\n"
        + _table(["acronym", "expansion", "source", "status", "epistemic", "do_not_confuse"], rows)
    )


def _gen_dod(entities: list[dict[str, Any]]) -> str:
    rows = [
        [
            str(e.get("id")),
            str(e.get("name") or ""),
            str(e.get("scope") or ""),
            str(e.get("current_status") or ""),
            _epi_label(str(e.get("epistemic_class") or "")),
            str(e.get("authority_sources") or e.get("evidence_sources") or "")[:80],
        ]
        for e in entities
        if str(e.get("kind")) == "DOD"
    ]
    return (
        _HEADER
        + "# Definition of Done Map\n\n"
        + _BANNER
        + "DoD is not collapsed into tests. Capability Closure Standard is a related but distinct construct.\n\n"
        + _table(["id", "name", "scope", "status", "epistemic", "authority"], rows)
    )


def _gen_schemas(entities: list[dict[str, Any]], atlas: dict[str, Any]) -> str:
    rows = [
        [
            str(e.get("id")),
            str(e.get("name") or ""),
            str(e.get("schema_kind") or ""),
            str(e.get("current_status") or ""),
            _epi_label(str(e.get("epistemic_class") or "")),
            str(e.get("evidence_sources") or "")[:80],
        ]
        for e in entities
        if str(e.get("kind")) == "SCHEMA"
    ]
    like = atlas["records"].get("census/schema_like_src.yaml") or {}
    return (
        _HEADER
        + "# Schema Map\n\n"
        + _BANNER
        + "SCHEMA is not automatically DATA_CONTRACT or dataclass. Relations recorded only if proven.\n\n"
        + "```text\n"
        + f"SRC_SCHEMA_CANDIDATE_COUNT={like.get('src_schema_candidate_count', 'OPEN')}\n"
        + f"SRC_ACCEPTED_SCHEMA_COUNT={like.get('src_accepted_schema_count', 'OPEN')}\n"
        + f"SRC_DATA_CONTRACT_COUNT={like.get('src_data_contract_count', 'OPEN')}\n"
        + f"SRC_TYPE_ONLY_COUNT={like.get('src_type_only_count', 'OPEN')}\n"
        + f"SRC_UNADJUDICATED_SCHEMA_CANDIDATE_COUNT={like.get('src_unadjudicated_schema_candidate_count', 'OPEN')}\n"
        + f"SCHEMA_CENSUS_COMPLETE={str(like.get('schema_census_complete', False)).lower()}\n"
        + "```\n\n"
        + "Drill-down census: `docs/system_atlas/census/schema_like_src.yaml`, `docs/system_atlas/census/schema_field_inventory.yaml`.\n\n"
        + _table(["id", "name", "schema_kind", "status", "epistemic", "evidence"], rows)
    )


def _gen_term_collisions(collisions: list[dict[str, Any]]) -> str:
    parts = [
        _HEADER,
        "# Terminology Collisions\n\n",
        _BANNER,
        "Collisions are preserved, not normalized.\n\n",
    ]
    for c in collisions:
        parts.append(
            f"### {c.get('id')}\n\n"
            f"- term: `{c.get('term')}`\n"
            f"- meaning_a: {c.get('meaning_a')}\n"
            f"- source_a: `{c.get('source_a')}`\n"
            f"- meaning_b: {c.get('meaning_b')}\n"
            f"- source_b: `{c.get('source_b')}`\n"
            f"- status: `{_epi_label(str(c.get('epistemic_status') or 'CONTRADICTED'))}`\n\n"
        )
    return "".join(parts)


def _gen_atlas_change_impact(atlas: dict[str, Any]) -> str:
    from scripts.ops.system_atlas_v1.impact_v1 import AtlasImpactReport, render_impact_markdown

    state = atlas["records"].get("provenance/impact_state.yaml") or {}
    report = AtlasImpactReport(
        impact=str(state.get("last_recorded_impact") or "NONE_WITH_PROOF"),
        changed_entities=[str(x) for x in (state.get("changed_entities") or [])],
        changed_relations=[str(x) for x in (state.get("changed_relations") or [])],
        new_relations=[str(x) for x in (state.get("new_relations") or [])],
        removed_relations=[str(x) for x in (state.get("removed_relations") or [])],
        affected_dependency_closures=[
            str(x) for x in (state.get("affected_dependency_closures") or [])
        ],
        affected_okx_surfaces=[str(x) for x in (state.get("affected_okx_surfaces") or [])],
        affected_safety_surfaces=[str(x) for x in (state.get("affected_safety_surfaces") or [])],
        affected_schemas=[str(x) for x in (state.get("affected_schemas") or [])],
        review_required_items=[str(x) for x in (state.get("review_required_items") or [])],
        generated_files_current=True,
        validation_status="OK",
        drift_detected=False,
        notes=[
            str(state.get("note") or "Committed impact snapshot; live PRs use the impact checker."),
            f"introduced_by={state.get('introduced_by') or 'PENDING_CHANGE'}",
            f"modified_by={state.get('modified_by') or 'PENDING_CHANGE'}",
        ],
    )
    return _HEADER + _BANNER + render_impact_markdown(report, impact_state=state)


def write_generated_v1(*, atlas: dict[str, Any], repo_root: Path) -> list[Path]:
    root = atlas_root(repo_root) / "generated"
    root.mkdir(parents=True, exist_ok=True)
    views = generate_views_v1(atlas=atlas, repo_root=repo_root)
    written: list[Path] = []
    for name in GENERATED_VIEW_NAMES:
        path = root / name
        text = views[name]
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def generated_drift_v1(*, atlas: dict[str, Any], repo_root: Path) -> list[str]:
    expected = generate_views_v1(atlas=atlas, repo_root=repo_root)
    root = atlas_root(repo_root) / "generated"
    drift: list[str] = []
    for name, text in expected.items():
        path = root / name
        if not path.is_file():
            drift.append(f"MISSING:{name}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != text:
            drift.append(f"DRIFT:{name}")
    return drift
