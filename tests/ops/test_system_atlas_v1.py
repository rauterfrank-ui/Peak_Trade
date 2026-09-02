"""System Atlas v1 contracts. ATLAS_AUTHORITY=NONE. Offline. No network."""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from scripts.ops.system_atlas_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    GENERATED_VIEW_NAMES,
    PACKAGE_MARKER,
)
from scripts.ops.system_atlas_v1.generate_v1 import (
    MASTER_VIEW_SECTION_HEADINGS,
    _HUB_ENTITY_IDS,
    _alias,
    generate_views_v1,
    generated_drift_v1,
    historical_nonlive_repo_paths,
)
from scripts.ops.system_atlas_v1.load_v1 import iter_entities, iter_relations, load_atlas_v1
from scripts.ops.system_atlas_v1.validate_v1 import AtlasValidationError, validate_atlas_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
ATLAS_ROOT = REPO_ROOT / "docs" / "system_atlas"


@pytest.fixture(scope="module")
def atlas() -> dict:
    return load_atlas_v1(repo_root=REPO_ROOT)


def test_package_marker_and_authority() -> None:
    assert PACKAGE_MARKER == "SYSTEM_ATLAS_V1=true"
    assert ATLAS_AUTHORITY == "NONE"


def test_readme_declares_atlas_authority_none() -> None:
    text = (ATLAS_ROOT / "README.md").read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in text
    usage = (ATLAS_ROOT / "ATLAS_AUTHORITY_AND_USAGE.md").read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in usage
    assert "ATLAS_MUST_NOT_CREATE_AUTHORITY=true" in usage
    recon = (ATLAS_ROOT / "reconciliation" / "README.md").read_text(encoding="utf-8")
    assert "RECONCILIATION_AUTHORITY=NONE" in recon
    assert "CREATES_CANONICAL_AUTHORITY=false" in recon


def test_atlas_loads_and_validates(atlas: dict) -> None:
    warnings = validate_atlas_v1(atlas)
    assert warnings == []


def test_generated_views_are_deterministic(atlas: dict) -> None:
    a = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    b = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    assert a.keys() == b.keys()
    assert set(a) == set(GENERATED_VIEW_NAMES)
    for name in GENERATED_VIEW_NAMES:
        assert a[name] == b[name]
        assert "ATLAS_AUTHORITY=NONE" in a[name]
        assert "GENERATED/DO_NOT_EDIT" in a[name]


def test_generated_views_up_to_date(atlas: dict) -> None:
    drift = generated_drift_v1(atlas=atlas, repo_root=REPO_ROOT)
    assert drift == []


def test_historical_nonlive_paths_are_model_driven(atlas: dict) -> None:
    wiring = atlas["records"]["census/historical_wiring.yaml"]
    edges = list(wiring.get("edges") or [])
    relations = {str(edge.get("relation") or "") for edge in edges}
    assert "REMOVED_CONSUMER" in relations
    assert "RESTORED" in relations
    nonlive = historical_nonlive_repo_paths(atlas)
    for edge in edges:
        source = str(edge.get("source") or "")
        if source.endswith(".py"):
            assert source in nonlive


def test_generated_views_independent_of_checkout_path_existence(
    atlas: dict, tmp_path: Path
) -> None:
    nonlive = historical_nonlive_repo_paths(atlas)
    assert nonlive, "historical wiring must declare at least one file-like source"
    present_root = tmp_path / "path_present"
    for rel in nonlive:
        target = present_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# checkout-presence stub\n", encoding="utf-8")
    absent_root = tmp_path / "path_absent"
    absent_root.mkdir()
    views_absent = generate_views_v1(atlas=atlas, repo_root=absent_root)
    views_present = generate_views_v1(atlas=atlas, repo_root=present_root)
    assert views_absent.keys() == views_present.keys()
    for name in GENERATED_VIEW_NAMES:
        assert views_absent[name] == views_present[name]
    sample = next(iter(nonlive))
    encoded = sample.replace("/", "&#47;")
    joined = "".join(
        views_absent[name] for name in ("RUNTIME_GRAPH.md", "FULL_DEPENDENCY_GRAPH.md")
    )
    assert encoded in joined
    assert sample not in joined
    live_control = "src/trading/master_v2/double_play_composition.py"
    assert live_control not in nonlive
    assert live_control in views_absent["RUNTIME_GRAPH.md"]


def test_terminology_and_dod_and_schema_entities_present(atlas: dict) -> None:
    entities = iter_entities(atlas)
    kinds = {str(e.get("kind")) for e in entities}
    ids = {str(e.get("id")) for e in entities}
    assert "DOD" in kinds
    assert "SCHEMA" in kinds
    assert "ACRONYM" in kinds
    assert "DOD:program_final" in ids
    assert "SCHEMA:gfu_snapshot_v1" in ids
    assert "ACRONYM:SSOT" in ids
    assert "DATA_CONTRACT:bound_instrument_v1" in ids
    assert "SCHEMA:bound_instrument_dataclass_v1" in ids
    assert "SCHEMA:bound_instrument_dataclass_v1" != "DATA_CONTRACT:bound_instrument_v1"


def test_duplicate_entity_id_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    catalog = mutated["records"]["entities/catalog.yaml"]
    catalog["entities"].append(dict(catalog["entities"][0]))
    with pytest.raises(AtlasValidationError, match="ENTITY_ID_DUPLICATE"):
        validate_atlas_v1(mutated)


def test_missing_relation_target_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["relations/structural.yaml"]["relations"].append(
        {
            "id": "REL:test_missing_target",
            "source": "SYSTEM:peak_trade",
            "type": "CONTAINS",
            "target": "SYSTEM:does_not_exist",
            "epistemic_status": "OPEN",
        }
    )
    with pytest.raises(AtlasValidationError, match="RELATION_TARGET_MISSING"):
        validate_atlas_v1(mutated)


def test_canonical_without_source_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["entities/catalog.yaml"]["entities"].append(
        {
            "id": "SYSTEM:fake_canonical",
            "kind": "SYSTEM",
            "name": "fake",
            "epistemic_class": "CANONICAL_AUTHORITY",
            "current_canonical": False,
            "current_status": "OPEN",
            "authority_sources": [],
        }
    )
    with pytest.raises(AtlasValidationError, match="CANONICAL_AUTHORITY_WITHOUT_SOURCE"):
        validate_atlas_v1(mutated)


def test_open_rendered_as_proven_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["relations/runtime.yaml"]["relations"].append(
        {
            "id": "REL:test_open_proven",
            "source": "SYSTEM:peak_trade",
            "type": "CALLS",
            "target": "SUBSYSTEM:master_v2",
            "epistemic_status": "OPEN",
            "render_as_proven": True,
        }
    )
    with pytest.raises(AtlasValidationError, match="OPEN_RENDERED_AS_PROVEN"):
        validate_atlas_v1(mutated)


def test_hypothesis_used_as_canonical_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["entities/catalog.yaml"]["entities"].append(
        {
            "id": "SYSTEM:hypothesis_as_auth",
            "kind": "SYSTEM",
            "name": "hyp",
            "epistemic_class": "HYPOTHESIS",
            "current_canonical": False,
            "current_status": "OPEN",
            "used_as_canonical_authority": True,
        }
    )
    with pytest.raises(AtlasValidationError, match="HYPOTHESIS_USED_AS_CANONICAL"):
        validate_atlas_v1(mutated)


def test_contradiction_lost_side_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["contradictions/register.yaml"]["contradictions"].append(
        {
            "id": "C-TEST-LOST",
            "claim_a": "only one side",
            "source_a": "a.md",
        }
    )
    with pytest.raises(AtlasValidationError, match="CONTRADICTION_LOST_SIDE"):
        validate_atlas_v1(mutated)


def test_current_canonical_without_external_authority_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["entities/catalog.yaml"]["entities"].append(
        {
            "id": "SYSTEM:atlas_only_canonical",
            "kind": "SYSTEM",
            "name": "atlas only",
            "epistemic_class": "ADJUDICATED",
            "current_canonical": True,
            "current_status": "CURRENT_CANONICAL",
            "authority_sources": ["docs/system_atlas/README.md"],
        }
    )
    with pytest.raises(AtlasValidationError, match="CURRENT_CANONICAL_WITHOUT_EXTERNAL_AUTHORITY"):
        validate_atlas_v1(mutated)


def test_historical_rendered_current_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["entities/catalog.yaml"]["entities"].append(
        {
            "id": "SYSTEM:historical_current",
            "kind": "SYSTEM",
            "name": "hist",
            "epistemic_class": "HISTORICAL",
            "current_canonical": True,
            "current_status": "CURRENT_CANONICAL",
            "temporal_class": "HISTORICAL_ONLY",
            "authority_sources": ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
        }
    )
    with pytest.raises(AtlasValidationError, match="HISTORICAL_RENDERED_CURRENT"):
        validate_atlas_v1(mutated)


def test_navigation_treated_as_authority_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["entities/catalog.yaml"]["entities"].append(
        {
            "id": "NAVIGATION_INDEX:fake_nav",
            "kind": "NAVIGATION_INDEX",
            "name": "nav",
            "epistemic_class": "NAVIGATION_ONLY",
            "current_canonical": False,
            "current_status": "CURRENT_NONCANONICAL",
            "semantic_authority": True,
        }
    )
    with pytest.raises(AtlasValidationError, match="NAVIGATION_TREATED_AS_AUTHORITY"):
        validate_atlas_v1(mutated)


def test_okx_census_complete_without_flags_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["census/census_meta.yaml"]["okx_census_complete"] = True
    mutated["records"]["census/census_meta.yaml"]["completeness_flags"][
        "raw_response_fixture_search_complete"
    ] = False
    with pytest.raises(AtlasValidationError, match="OKX_CENSUS_COMPLETE_WITHOUT_FLAGS"):
        validate_atlas_v1(mutated)


def test_build_guidance_missing_entity_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["guidance/capability_dependency_closures.yaml"]["closures"].append(
        {
            "id": "CLOSURE:missing",
            "title": "missing",
            "inspect": ["SYSTEM:not_in_catalog"],
        }
    )
    with pytest.raises(AtlasValidationError, match="BUILD_GUIDANCE_MISSING_ENTITY"):
        validate_atlas_v1(mutated)


_MASTER_VIEW_BUCKETS = (
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


def test_readme_declares_primary_entrypoint_navigation() -> None:
    text = (ATLAS_ROOT / "README.md").read_text(encoding="utf-8")
    assert "SYSTEM_ATLAS_PRIMARY_ENTRYPOINT=docs/system_atlas/generated/SYSTEM_ATLAS.md" in text
    assert "SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true" in text
    usage = (ATLAS_ROOT / "ATLAS_AUTHORITY_AND_USAGE.md").read_text(encoding="utf-8")
    assert "complete primary human overview" in usage
    assert "canonical authority" in usage.lower()


def test_system_atlas_master_view_is_complete_overview_not_index(atlas: dict) -> None:
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    text = views["SYSTEM_ATLAS.md"]
    assert "SYSTEM_ATLAS_PRIMARY_ENTRYPOINT=docs/system_atlas/generated/SYSTEM_ATLAS.md" in text
    assert "SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true" in text
    assert (
        "GLOBAL_CENSUS_EXHAUSTED=false" in text
        or "GLOBAL_CENSUS_EXHAUSTED=false" in views["COVERAGE_REPORT.md"]
    )
    assert "SYSTEM_ATLAS_DRILLDOWN_LINKS_VALID=true" in text
    assert "SYSTEM_ATLAS_ALL_MAJOR_DOMAINS_REPRESENTED=true" in text
    assert "SYSTEM_ATLAS_CURRENT_HISTORICAL_SPLIT_VALID=true" in text
    assert "SYSTEM_ATLAS_GRAPH_RELATIONS_BACKED_BY_MODEL=true" in text
    for heading in MASTER_VIEW_SECTION_HEADINGS:
        assert f"## {heading}" in text
    for bucket in _MASTER_VIEW_BUCKETS:
        assert f"### {bucket}" in text
    for name in GENERATED_VIEW_NAMES:
        if name == "SYSTEM_ATLAS.md":
            continue
        assert f"[{name}]({name})" in text
    assert "```mermaid" in text
    assert "flowchart TB" in text
    assert "HAS_FUNCTIONAL_CORE" in text
    assert "SSOT_CHILD" in text
    assert "Maintenance Margin Requirement" in text
    assert "eea.okx.com" in text
    assert "C-CAP23-VS-CANARY-INSTRUMENT-001" in text
    assert "C-OKX-QUOTE-ULY-001" in text
    assert "C-DP-ORDER-001" in text
    assert "LIVE_AUTHORIZED=false" in text


def test_system_atlas_mermaid_edges_are_model_backed(atlas: dict) -> None:
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    text = views["SYSTEM_ATLAS.md"]
    alias_to_id = {_alias(eid): eid for eid in _HUB_ENTITY_IDS}
    pairs: set[tuple[str, str, str]] = set()
    for rel in iter_relations(atlas):
        src = str(rel.get("source") or "")
        dst = str(rel.get("target") or "")
        rtype = str(rel.get("type") or "")
        if src in _HUB_ENTITY_IDS and dst in _HUB_ENTITY_IDS:
            pairs.add((src, rtype, dst))
    edges = re.findall(r'(\w+) -->\|"([^"]+)"\| (\w+)', text)
    assert edges, "master view mermaid must contain model-backed edges"
    for src_alias, label, dst_alias in edges:
        src = alias_to_id[src_alias]
        dst = alias_to_id[dst_alias]
        rtype = label.split(" (", 1)[0]
        assert (src, rtype, dst) in pairs
        assert src in _HUB_ENTITY_IDS
        assert dst in _HUB_ENTITY_IDS


def test_incompleteness_register_covers_all_complete_flags(atlas: dict) -> None:
    inc = atlas["records"]["census/incompleteness.yaml"]
    meta = atlas["records"]["census/census_meta.yaml"]
    classes = set(inc["incompleteness_classes"])
    assert classes == {
        "GENUINELY_UNSEARCHED",
        "SEARCHED_BUT_NO_EVIDENCE_FOUND",
        "UNRESOLVED_CONTRADICTION",
        "HISTORICAL_SOURCE_UNAVAILABLE",
        "TERMINOLOGY_UNRESOLVED",
    }
    remaining_ids = {str(r["id"]) for r in inc["remaining_domains"]}
    closed_ids = {str(r["id"]) for r in inc["closed_domains"]}
    assert remaining_ids.isdisjoint(closed_ids)
    for row in inc["remaining_domains"]:
        assert row["flag"] is False
        assert str(row["remaining"]).strip()
        assert meta[row["id"]] is False
    for row in inc["closed_domains"]:
        assert row["flag"] is True
        assert meta[row["id"]] is True
    reason_ids = {str(r["id"]) for r in inc["completeness_flag_reasons"]}
    assert reason_ids == set(meta["completeness_flags"])
    for row in inc["completeness_flag_reasons"]:
        assert bool(row["flag"]) is bool(meta["completeness_flags"][row["id"]])
        assert str(row["remaining"]).strip()


def test_schema_json_files_are_inventoried(atlas: dict) -> None:
    entities = iter_entities(atlas)
    schema_sources = {
        str(e.get("source") or "")
        for e in entities
        if str(e.get("kind")) == "SCHEMA" and str(e.get("schema_kind")) == "json_schema"
    }
    files = sorted((REPO_ROOT / "docs" / "ops" / "schemas").glob("*.schema.json"))
    assert len(files) == 10
    assert len(schema_sources) == 10
    for path in files:
        assert str(path.relative_to(REPO_ROOT)) in schema_sources


def test_capability_spec_and_hub_entities_present(atlas: dict) -> None:
    ids = {str(e.get("id")) for e in iter_entities(atlas)}
    for eid in (
        "CAPABILITY:cap_1_1_reconciliation",
        "CAPABILITY:cap_3_1_futures_accounting",
        "CAPABILITY:cap_4_1_pre_activation_closure",
        "CAPABILITY:cap_7_2_stateful_no_order",
        "CAPABILITY:cap_11_13_5_live_canary",
    ):
        assert eid in ids
        assert eid in _HUB_ENTITY_IDS
    rel_targets = {
        (str(r.get("source")), str(r.get("type")), str(r.get("target")))
        for r in iter_relations(atlas)
    }
    assert (
        "SYSTEM:peak_trade",
        "HAS_CAPABILITY",
        "CAPABILITY:cap_1_1_reconciliation",
    ) in rel_targets
    inv = atlas["records"]["census/master_v2_module_inventory.yaml"]
    assert inv["python_file_count"] == 102
    assert inv["capability_spec_file_count"] == 7
    assert inv["file_inventory_complete"] is True
    assert inv["entity_mapping_complete"] is True
    sem = atlas["records"]["census/master_v2_semantic_map.yaml"]
    assert sem["python_file_count_inventoried"] == 102
    assert sem["python_file_count_semantically_mapped"] == 102
    assert sem["unmapped_file_count"] == 0


def test_incompleteness_rendered_in_master_and_coverage(atlas: dict) -> None:
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    master = views["SYSTEM_ATLAS.md"]
    coverage = views["COVERAGE_REPORT.md"]
    for token in (
        "GENUINELY_UNSEARCHED",
        "SEARCHED_BUT_NO_EVIDENCE_FOUND",
        "UNRESOLVED_CONTRADICTION",
        "HISTORICAL_SOURCE_UNAVAILABLE",
        "TERMINOLOGY_UNRESOLVED",
        "SCHEMA_FILE_INVENTORY_COMPLETE=true",
        "MASTER_V2_MODULE_FILE_INVENTORY_COMPLETE=true",
        "SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true",
        "Caps 1.1, 2.1–2.4, 3.1, 4.1, 7.2, and 11.13.5",
    ):
        assert token in master
    assert "Census incompleteness (five-class)" in coverage
    assert "okx_census_complete" in coverage
    assert "ssot_child_census_complete" in coverage


def test_incompleteness_missing_reason_fails(atlas: dict) -> None:
    mutated = copy.deepcopy(atlas)
    mutated["records"]["census/incompleteness.yaml"]["completeness_flag_reasons"] = []
    with pytest.raises(AtlasValidationError, match="INCOMPLETENESS_FLAG_REASON_MISSING"):
        validate_atlas_v1(mutated)


def test_historical_okx_census_after_unshallow(atlas: dict) -> None:
    meta = atlas["records"]["census/census_meta.yaml"]
    hist = atlas["records"]["census/okx_historical.yaml"]
    terms = atlas["records"]["census/historical_terminology.yaml"]
    assert meta["git_is_shallow"] is False
    assert meta["historical_fetch_performed"] is True
    assert meta["okx_historical_census_complete"] is True
    assert meta["okx_census_complete"] is True
    assert meta["historical_terminology_census_complete"] is True
    assert hist["okx_named_path_deletions_on_origin_main"] == 0
    assert hist["xperp_historical_quote_mapping_found"] is False
    assert hist["xperp_historical_uly_handler_found"] is True
    assert hist["c_okx_quote_uly_status_changed"] is False
    assert terms["ssot_child_literal_found_in_origin_main_history"] is False
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    chrono = views["OKX_CHRONOLOGY.md"]
    assert "5c588999731757f19cfb2ef9b85055af0eca760e" in chrono
    assert "XPERP_HISTORICAL_QUOTE_MAPPING_FOUND=false" in chrono
    assert "OKX_HISTORICAL_CENSUS_COMPLETE=true" in views["COVERAGE_REPORT.md"]
    assert "GIT_IS_SHALLOW=false" in views["COVERAGE_REPORT.md"]


def test_local_census_closure_surfaces(atlas: dict) -> None:
    meta = atlas["records"]["census/census_meta.yaml"]
    like = atlas["records"]["census/schema_like_src.yaml"]
    ep = atlas["records"]["census/okx_endpoint_classification.yaml"]
    fields = atlas["records"]["census/okx_field_census.yaml"]
    fixtures = atlas["records"]["census/okx_fixture_census.yaml"]
    assert meta["schema_census_complete"] is True
    assert meta["terminology_census_complete"] is True
    assert meta["acronym_census_complete"] is False
    assert meta["okx_census_complete"] is True
    assert meta["completeness_flags"]["endpoint_inventory_complete"] is True
    assert meta["completeness_flags"]["field_inventory_complete"] is True
    assert meta["completeness_flags"]["auth_inventory_complete"] is True
    assert meta["completeness_flags"]["raw_response_fixture_search_complete"] is True
    assert meta["completeness_flags"]["product_type_inventory_complete"] is True
    assert like["src_unadjudicated_schema_candidate_count"] == 0
    assert like["src_schema_candidate_count"] == 1626
    assert like["src_accepted_schema_count"] == 5
    assert ep["okx_raw_api_path_hit_count"] == 69
    assert ep["okx_unique_endpoint_candidate_count"] == 48
    assert ep["okx_modeled_endpoint_count"] == 49
    assert ep["okx_grep_noise_count"] == 21
    assert ep["okx_unclassified_endpoint_count"] == 0
    assert len(ep["candidates"]) == 69
    assert fields["okx_field_token_count"] == 42
    assert fields["okx_modeled_field_count"] == 40
    assert fields["okx_unclassified_material_field_count"] == 0
    assert fixtures["okx_unclassified_fixture_count"] == 0
    assert fixtures["raw_response_fixture_search_complete"] is True
    assert fixtures["okx_fixture_bytes_or_structure_inspected_count"] == 147
    assert fixtures["okx_uninspected_material_fixture_count"] == 0
    assert fixtures["okx_confirmed_fixture_count"] == 16
    assert fixtures["okx_raw_response_count"] == 2
    assert fixtures["okx_distinct_response_shape_count"] == 6
    ids = {str(e.get("id")) for e in iter_entities(atlas)}
    assert "SCHEMA:ranking_snapshot_v1" in ids
    assert "VENUE_FIELD:baseCcy" in ids
    assert "OKX_RESPONSE_SHAPE:mark_price_row" in ids
    assert "OKX_RESPONSE_SHAPE:ticker_row" in ids
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    assert "SRC_SCHEMA_CANDIDATE_COUNT=1626" in views["COVERAGE_REPORT.md"]
    assert "OKX_RAW_API_PATH_HIT_COUNT=69" in views["OKX_INTEGRATION_MAP.md"]
    assert "SCHEMA_CENSUS_COMPLETE=true" in views["SCHEMA_MAP.md"]
    assert "TERMINOLOGY_CENSUS_COMPLETE=true" in views["SYSTEM_ATLAS.md"]
    assert "SCHEMA_CENSUS_COMPLETE=true" in views["SYSTEM_ATLAS.md"]


def test_repo_atlas_v1_final_closure(atlas: dict) -> None:
    meta = atlas["records"]["census/census_meta.yaml"]
    repo = meta["repo_atlas_v1"]
    surface = meta["okx_surface_census"]
    products = atlas["records"]["census/okx_product_types.yaml"]
    resolution = atlas["records"]["census/repo_final_resolution.yaml"]
    overview = atlas["records"]["venue/okx/overview.yaml"]
    assert overview["okx_census_complete"] is True
    assert meta["okx_census_complete"] is True
    assert meta["acronym_census_inventory_complete"] is True
    assert meta["acronym_expansions_resolved"] is False
    assert meta["acronym_census_complete"] is False
    assert meta["global_census_exhausted"] is False
    assert repo["repo_atlas_census_complete"] is True
    assert repo["repo_okx_census_complete"] is True
    assert repo["repo_current_tree_census_complete"] is True
    assert repo["repo_git_history_census_complete"] is True
    assert repo["repo_schema_census_complete"] is True
    assert repo["repo_terminology_inventory_complete"] is True
    assert repo["repo_master_v2_census_complete"] is True
    assert repo["repo_double_play_census_complete"] is True
    assert repo["repo_family_child_census_complete"] is True
    assert repo["repo_dod_census_complete"] is True
    assert repo["external_forensic_corpus_census_complete"] == "NOT_STARTED"
    assert surface["okx_docs_census_complete"] is True
    assert surface["okx_tests_census_complete"] is True
    assert surface["okx_config_census_complete"] is True
    assert surface["okx_scripts_census_complete"] is True
    assert surface["okx_evidence_census_complete"] is True
    assert surface["okx_product_type_census_complete"] is True
    assert products["okx_product_type_census_complete"] is True
    statuses = {
        str(row.get("product_type")): str(row.get("status")) for row in products["product_types"]
    }
    assert statuses["SWAP"] == "IMPLEMENTED"
    assert statuses["FUTURES"] == "IMPLEMENTED"
    assert statuses["SPOT"] == "UNSUPPORTED"
    assert statuses["MARGIN"] == "SEARCHED_BUT_NO_EVIDENCE_FOUND"
    assert statuses["OPTION"] == "SEARCHED_BUT_NO_EVIDENCE_FOUND"
    assert statuses["xperp"] == "PARTIALLY_IMPLEMENTED"
    assert resolution["locally_resolvable_unsearched_count"] == 0
    assert resolution["requires_external_corpus_count"] == 0
    assert resolution["requires_owner_decision_count"] == 7
    assert resolution["requires_runtime_observation_count"] == 1
    assert resolution["requires_implementation_change_count"] == 2
    assert resolution["unresolved_terminology_count"] == 14
    open_acronyms = [
        row
        for row in atlas["records"]["ontology/acronyms.yaml"]["acronyms"]
        if row.get("expansion") == "OPEN"
    ]
    assert {str(row.get("acronym")) for row in open_acronyms} == {
        "EEA",
        "OKX",
        "XPERP",
        "C1",
        "C2",
        "C3",
        "PRE",
        "PENDING",
    }
    for row in open_acronyms:
        assert row.get("search_scope")
        assert row.get("current_usage")
        assert row.get("historical_usage")
        assert row.get("evidence_sources")
        assert row.get("meaning")
    views = generate_views_v1(atlas=atlas, repo_root=REPO_ROOT)
    atlas_md = views["SYSTEM_ATLAS.md"]
    coverage = views["COVERAGE_REPORT.md"]
    okx_map = views["OKX_INTEGRATION_MAP.md"]
    assert "REPO_ATLAS_CENSUS_COMPLETE=true" in atlas_md
    assert "REPO_OKX_CENSUS_COMPLETE=true" in atlas_md
    assert "EXTERNAL_FORENSIC_CORPUS_CENSUS_COMPLETE=NOT_STARTED" in atlas_md
    assert "ACRONYM_CENSUS_INVENTORY_COMPLETE=true" in atlas_md
    assert "ACRONYM_EXPANSIONS_RESOLVED=false" in atlas_md
    assert "generate_system_atlas_v1.py" in atlas_md
    assert "OKX_CENSUS_COMPLETE=true" in atlas_md
    assert "SEARCHED_BUT_NO_EVIDENCE_FOUND" in atlas_md
    assert "REPO_ATLAS_CENSUS_COMPLETE=true" in coverage
    assert "OKX_UNINSPECTED_MATERIAL_FIXTURE_COUNT=0" in coverage
    assert "OKX_PRODUCT_TYPE_CENSUS_COMPLETE=true" in okx_map
    assert "PARTIALLY_IMPLEMENTED" in okx_map
    remaining_ids = {
        str(row.get("id"))
        for row in atlas["records"]["census/incompleteness.yaml"]["remaining_domains"]
    }
    assert remaining_ids == {"acronym_census_complete"}


def test_census_navigation_rebind_distinct_from_domain_payloads(atlas: dict) -> None:
    meta = atlas["records"]["census/census_meta.yaml"]
    assert meta["origin_main_sha"] == "14e8a58f32dcb6b521be6b2559b388bf27360194"
    assert meta["navigation_rebind_sha"] == "14e8a58f32dcb6b521be6b2559b388bf27360194"
    assert meta["navigation_rebind_kind"] == "FRESH_NAVIGATION_REBIND_NOT_DOMAIN_RECENSUS"
    assert meta["domain_census_payloads_bound_sha"] == "615de3b307132b73a60df33fd3bedfac811c8cce"
    assert meta["origin_main_sha"] != meta["domain_census_payloads_bound_sha"]
    assert meta["domain_census_payloads_fresh_exhaustive_recensus"] is False
    inv = atlas["records"]["census/master_v2_module_inventory.yaml"]
    assert inv["origin_main_sha"] == meta["origin_main_sha"]
    assert inv["domain_census_payloads_fresh_exhaustive_recensus"] is False


def test_hist_selector_policy_reverted_uses_proven_6166_sha(atlas: dict) -> None:
    events = atlas["records"]["census/historical_architecture.yaml"]["events"]
    by_id = {str(row["id"]): row for row in events}
    revert = by_id["HIST:selector_policy_reverted"]
    assert revert["commit"] == "afbae518b67eb1b789c835e219db37f5b15f308b"
    assert revert["pr"] == "#6166"
    wp = by_id["HIST:wp_fa_07"]
    assert wp["commit"] == "615de3b307132b73a60df33fd3bedfac811c8cce"
    assert wp["pr"] == "#6209"


def test_ddo_navigation_is_observation_only_without_authority(atlas: dict) -> None:
    entities = {str(e["id"]): e for e in iter_entities(atlas)}
    required = (
        "PHASE:ddo_offline_foundation",
        "RUNTIME_COMPONENT:ddo_capture_v0",
        "RUNTIME_COMPONENT:ddo_ledger_v0",
        "RUNTIME_COMPONENT:ddo_experiment_identity_binding",
        "HOST:wallclock_decision_economics_cycle",
        "RUNTIME_COMPONENT:recon_startup_gate_v1",
        "RUNTIME_COMPONENT:simulated_execution_port_v1",
        "EXPERIMENT:canonical_experiment_identity_v1",
    )
    for eid in required:
        assert eid in entities
        notes = str(entities[eid].get("notes") or "")
        assert entities[eid].get("current_canonical") is False
        if eid.startswith("PHASE:") or eid.startswith("RUNTIME_COMPONENT:ddo_"):
            assert "AUTHORITY_OWNER=NONE" in notes
            assert "PRODUCTIVE_AI_AUTHORITY_COUNT=0" in notes
            assert "SECOND_TRADING_AUTHORITY=false" in notes
            assert "SECOND_RISK_AUTHORITY=false" in notes
            assert "SECOND_SAFETY_AUTHORITY=false" in notes
            assert "SECOND_PROMOTION_AUTHORITY=false" in notes
            assert "RUNTIME_LINEAGE_PARTIAL=true" in notes
    rels = list(iter_relations(atlas))
    ddo_out = [r for r in rels if str(r.get("source")) == "RUNTIME_COMPONENT:ddo_capture_v0"]
    types = {str(r.get("type")) for r in ddo_out}
    assert "OBSERVES" in types
    assert "PERSISTS" in types
    assert "PRODUCES" not in types
    assert "CONSUMES" not in types
    assert "AUTHORIZES" not in types
    assert "BINDS" not in types
    observes = {(str(r["target"]),) for r in ddo_out if str(r.get("type")) == "OBSERVES"}
    assert ("CAPABILITY:cap_2_1_gfu",) in observes
    assert ("SELECTOR:productive_futures_ranking",) in observes
    assert ("SELECTOR:single_selected_future_policy",) in observes
    assert ("BINDER:bound_instrument_v1",) in observes
    assert ("RUNTIME_COMPONENT:recon_startup_gate_v1",) in observes
    assert ("RUNTIME_COMPONENT:simulated_execution_port_v1",) in observes
    rel_triples = {(str(r.get("source")), str(r.get("type")), str(r.get("target"))) for r in rels}
    assert (
        "RUNTIME_COMPONENT:ddo_experiment_identity_binding",
        "REFERENCE_OF",
        "EXPERIMENT:canonical_experiment_identity_v1",
    ) in rel_triples
    assert (
        "FORENSIC_REFERENCE:information_corpus_persistence_base",
        "HAS_CHILD",
        "CHILD:nested_structural_child",
    ) in rel_triples
    forbidden_targets = {
        "RUNTIME_COMPONENT:dp_composition",
        "RUNTIME_COMPONENT:dp_survival",
        "GATE:flatten_execute_authority",
        "CAPABILITY:cap_11_13_5_live_canary",
    }
    for r in ddo_out:
        assert str(r.get("target")) not in forbidden_targets
    kraken = entities["ADAPTER:kraken_live_client"]
    assert kraken["current_status"] == "REMOVED"
    assert kraken["temporal_class"] == "HISTORICAL_ONLY"
    assert "#6203" in str(kraken.get("notes") or "")
    gaps = atlas["records"]["wiring/gaps.yaml"]["gaps"]
    gap_ids = {str(g.get("id")) for g in gaps}
    assert "GAP:ddo_declared_seams_without_host_decorator" in gap_ids
