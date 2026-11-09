"""Read-only law/policy projection of the frozen source inventory."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LAW = "config/governance/current_law_impact_map_v1/source_v1.json"
TECHNICAL_ADMISSION = "config/governance/technical_canonical_wiring_authorization_v1.json"
NUMERIC_ADMISSION_PATHS = (
    "src/trading/master_v2/survival_numeric_admission_v1.py",
    "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_explicit_financial_context_v1.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
    "tests/trading/master_v2/test_survival_numeric_admission_v1.py",
)
NUMERIC_ADMISSION_ID = "CURRENT_NUMERIC_INPUT_ADMISSION_AND_EXPLICIT_OFFLINE_FINANCIAL_CONTEXT_V1"

# Frank's separate 2026-11-09 approval covers this exact reviewed four-file
# development bundle. Frozen records/tags and all other policy admission stay
# intact. A new binding hash alone cannot authorize another implementation.
ORDERED_FUNDING_EPISODE_DELTAS = {
    "src/ops/exit_policy_producer_binding_v1/position_episode_binding_v1.py": (
        "51c52f3caec87fd051343c1b47053da5f06dfd5812acca878c0f0d2bf5fe5a5d",
        "bf1c90a45a80171b5d3b1ed192a9348fe89271e71be490cff92fa2076e82569d",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_entry_source_v1.py": (
        "300cb76643cb95e05c9abe2d5d53a09fadbead1724b414a4c5c4759ea47817b1",
        "946c35e6c540024679f1a8fb53c9e4b557e5f41ec13972557a1a8f89f52ea769",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py": (
        "853f2fb7fb2eede7b78673944e2118d82b4dadedf4bf0f93327ee9a850a8beed",
        "5b726daeddef92b7697e3a1ac8920bd0b1735b6913def8e41eeeb8f2817db86e",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_close_v1.py": (
        "dd743daba0b43e378cd0c20811d6d6d1f9933a2af91ac58838061fe1c9f0597c",
        "c69cc8a4510de49eee30f241d71759fe54138049ba89731f30ca65ef95c8948f",
    ),
}


# Frank's 2026-11-09 instruction adds one fixed slot/incumbent/replacement
# transaction, 1800 seconds from nomination, its cancellation/restart, and the
# original GGE/Scope/C3/financial path. This is an exact development bundle;
# it neither rewrites frozen inventories/tags nor grants an external effect.
RESERVED_SLOT_ROTATION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "84051cc3949a6736f1252cd425822397b7f80d7924f052746c3823d3c86450cf",
        "bc04c096f9d20fa7dd360523f3d1f5d77f0d62e5e5afd5f32aefee69fc4609d3",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py": (
        "4e174b0048e8de66c5405235512f9da00e7da75b9a7c627b71096b4b888986f8",
        "0e109341649d82a539e6395e784967645a0907b5bc49f41f4e40dff05da96df4",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/bounded_slot_post_close_v1.py": (
        "42fac4a77874917184c0ad436b46d5860924c7c76b73e2dc030cf7cc5129428f",
        "34cbb33104b490f8eb8d2bd536e3e96e9a2f988099ca289c4bcf679517b49a9d",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/constants_v1.py": (
        "536e4827dfea87bcdcfee11234a38d0fb3589f6dd7ae2b073461ed0383c88664",
        "68f9648d45a566ca224575a5dec28c649c36ef93c238daf4883a27dd3d7e8d5a",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "d7c213281a98075f54f1560bd8bd7e7b09f16f3c572f7c916043a691dad48477",
        "8a40e60459b3da835de3cb8d1649c1677043ce53c0825773b83c6fa7ee3aaf01",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/post_close_continuation_v1.py": (
        "adabcae2f9547c0cbf026f971138b31ba8712e8d16c51c0ebe37e2863dd24b1b",
        "fec15a06cc3504c4b37d6029dfa30980ddd3d74b22634712cdb56ef968b8a45c",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/rotation_plan_v1.py": (
        None,
        "9f7322ff1fc357c3b828df4f6c0c73e74db0ee52350d7d90be434ed93255b96c",
    ),
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "5a12b8b0d2f69e74b43ae7e35cf93cdb44b7826f5b86b474d45387ee173d0647",
        "46b4680a588851cd78812be41aa960d73fb4b39130f4c05d7d1cfc7036cb84de",
    ),
    "src/ops/exit_policy_producer_binding_v1/host_binding_v1.py": (
        "70a0fbe3bb90a9ae4bf9cfcda05f57964d0681a5a859e5df6dd36ad8766c22cb",
        "f49f6fd6befc2552f6fdd3e8b74f46558ac1b8675a2656d3c241a74207691ae4",
    ),
    "src/ops/exit_policy_producer_binding_v1/models_v1.py": (
        "d63f2f8ca211c2f613449d95a260f3e261672a6539e6e29152417f3ca6094e24",
        "589dec4be5f00b4909c3aa511a600dfc63a31c92b018b20e9f437faa8334e9bc",
    ),
    "src/ops/exit_policy_producer_binding_v1/persistence_v1.py": (
        "77685dcbd323ebf8e1e35eada804add2cf7d795a05b4b9b8984cd2498f1fb396",
        "adc66058a39f3c84e84fc47ca45fc60f6e99f4605e06dc79d58153fc5de76826",
    ),
    "src/ops/exit_policy_producer_binding_v1/producers_v1.py": (
        "dbeb04582421be8b9891fafd810e5fedf0f4465647fbefa6e34b54b482784f8e",
        "f4b9f591c3e99038c033a0899111d2bcb203eed76b4aec70b0b6396410d78b99",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py": (
        "ceda614f8f65ff18fd9be973968938bb78c41bbea91d9434d844c2626c85c48a",
        "196e7da42a39e625ea4de756df9fc1b3f6533f97a4df7392ae9f94f854bedace",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py": (
        "c04f97c4fe0f405757661a715774ca4debf28d3d00c10c7077e5ed866e1c96d6",
        "ca2c078daeb147d6a2888add896dfc9c6785bfb2a1465a87bfe1aeba6f5869ff",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_close_feedback_v1.py": (
        "a93c61c73ebbbc11402456b2fe4fa36ec3e761b49b3b24309c9f45bf353d944f",
        "12b03e787f3edf42d4171e83e477a98f6b13d0354ce4129e8db3f64c31ef94c4",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_rotation_close_v1.py": (
        None,
        "843de05030c1a4bbb7420762c60fe3e16bfbdbe89b01a184ffe4f857969b69a2",
    ),
    "src/ops/mf_membership_context_artifact_contract_v1.py": (
        "8dda221cd46158140531e0a1cebce689ffe135ee821975fb5d712bf5380ef2be",
        "c813cae3d80dae5338c3bf4a96fe025265dcf0c3b696eb08bce5f8ad6bd6aca8",
    ),
    "src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py": (
        "976131456817f30d0c8c6df37b6a986644ca0ddadfe14aa11918eef9901f808c",
        "370d4a90b668218569faeff5997c1bd759e20af47cbd91ca1116245f9fba4a3d",
    ),
    "src/ops/single_selected_future_policy_v1/producer_v1.py": (
        "fdceed28a977a871f826909320eedc7d72ec268cc8532e9218a83c48d89e06b8",
        "e1adca9f8633cb75cf2f3ff557261839577d852464ee2eed40f54eda00f56c78",
    ),
}


# Frank requested the open test-slot loss close and continuation of BWP1.
# This exact two-adapter successor carries an original-budget proof to the
# existing per-cycle safety input. The reviewed rotation parent, native Core,
# funding episode adapters, startup, recovery and external-effect rights remain.
OPEN_TEST_SLOT_LOSS_PROTECTION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "bc04c096f9d20fa7dd360523f3d1f5d77f0d62e5e5afd5f32aefee69fc4609d3",
        "9a2d6867a1bc4ccc6a9ab53e9d719d69945d5cdf7c435d62228443492ef2dec0",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py": (
        "0e109341649d82a539e6395e784967645a0907b5bc49f41f4e40dff05da96df4",
        "214b7b0ddfe42517b801098d87e60bb6df3adffada3a43cf33d6c73f0aa56c06",
    ),
}


# Current Scope/price-source instruction and the explicit PR/merge request:
# retain source clocks through these three outer adapters. This is a complete
# exact successor of the reviewed loss-protection bundle, not an admission for
# native Core changes, other policy bodies or a development hash by itself.
CURRENT_SCOPE_MARK_ADMISSION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "9a2d6867a1bc4ccc6a9ab53e9d719d69945d5cdf7c435d62228443492ef2dec0",
        "5d8847e963b1d158621f497ec33b351eb6c49b48e02f3442954bf8221e44e7af",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "8a40e60459b3da835de3cb8d1649c1677043ce53c0825773b83c6fa7ee3aaf01",
        "91011736f288bd20d5744a883223a34b283f9fa6ff9ed044fe108e76bc53d665",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py": (
        "ca2c078daeb147d6a2888add896dfc9c6785bfb2a1465a87bfe1aeba6f5869ff",
        "c5f842663435ae1240c79b70bb087afc2e5d208949c6c49bfbb46d4bd3c1a425",
    ),
}


def validate_reserved_slot_rotation_bundle(root: Path, policies: list[dict] | None = None) -> None:
    frozen = {} if policies is None else {row["path"]: row["frozen_sha256"] for row in policies}
    actual = {}
    for path, (before, _after) in RESERVED_SLOT_ROTATION_DELTAS.items():
        if path in frozen and frozen[path] != before:
            raise ValueError("RESERVED_SLOT_ROTATION_BASELINE_INVALID:" + path)
        candidate = root / path
        actual[path] = (
            hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None
        )
    before = {path: pair[0] for path, pair in RESERVED_SLOT_ROTATION_DELTAS.items()}
    after = {path: pair[1] for path, pair in RESERVED_SLOT_ROTATION_DELTAS.items()}
    protected_after = dict(after)
    for path, (parent, successor) in OPEN_TEST_SLOT_LOSS_PROTECTION_DELTAS.items():
        if path not in after or after[path] != parent:
            raise ValueError("OPEN_TEST_SLOT_LOSS_PROTECTION_PARENT_INVALID:" + path)
        protected_after[path] = successor
    scope_bound_after = dict(protected_after)
    for path, (parent, successor) in CURRENT_SCOPE_MARK_ADMISSION_DELTAS.items():
        if path not in protected_after or protected_after[path] != parent:
            raise ValueError("CURRENT_SCOPE_MARK_ADMISSION_PARENT_INVALID:" + path)
        scope_bound_after[path] = successor
    if actual not in (before, after, protected_after, scope_bound_after):
        raise ValueError("RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED")


def validate_ordered_funding_episode_bundle(root: Path, policies: list[dict]) -> None:
    """Accept the original bundle or the separately reviewed exact successor."""
    frozen = {row["path"]: row["frozen_sha256"] for row in policies}
    actual = {}
    for path, (before, _after) in ORDERED_FUNDING_EPISODE_DELTAS.items():
        if frozen.get(path) != before:
            raise ValueError("ORDERED_FUNDING_EPISODE_BASELINE_INVALID:" + path)
        actual[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    if any(actual[path] != before for path, (before, _) in ORDERED_FUNDING_EPISODE_DELTAS.items()):
        for path, (_before, after) in ORDERED_FUNDING_EPISODE_DELTAS.items():
            if actual[path] != after:
                raise ValueError("ORDERED_FUNDING_EPISODE_REVIEWED_BUNDLE_REQUIRED:" + path)


def validate_numeric_technical_admission_delta(original: bytes, current: bytes) -> None:
    """Admit only the owner-requested six-file extension of the frozen contract.

    Hash rebinding alone cannot change a prior grant, an invariant, an effect,
    or add a seventh file. The original frozen inventory stays authoritative
    for the baseline; this is a separately bound development delta.
    """
    before, after = json.loads(original), json.loads(current)
    mutable = {"allowed_paths", "authorized_surface_notes"}
    if (
        set(before) != set(after)
        or any(after[k] != v for k, v in before.items() if k not in mutable)
        or any(p in before["allowed_paths"] for p in NUMERIC_ADMISSION_PATHS)
        or after["allowed_paths"] != before["allowed_paths"] + list(NUMERIC_ADMISSION_PATHS)
        or not isinstance(after["authorized_surface_notes"], list)
        or len(after["authorized_surface_notes"]) != len(before["authorized_surface_notes"]) + 1
        or after["authorized_surface_notes"][:-1] != before["authorized_surface_notes"]
        or type(after["authorized_surface_notes"][-1]) is not str
        or not after["authorized_surface_notes"][-1].startswith(NUMERIC_ADMISSION_ID + ": ")
    ):
        raise ValueError("POLICY_TECHNICAL_ADMISSION_DELTA_INVALID")


def policy_scope_kind(path: str) -> str | None:
    if path.startswith("config/governance/current_law_impact_map_v1/") or path in {
        "config/ops/docs_truth_map.yaml",
        "config/ops/repo_truth_claims.yaml",
        "config/governance/current_system_census_graph_v1/README.md",
    }:
        return None
    if path.startswith(".cursor/rules/"):
        return "DEVELOPMENT_GUIDANCE"
    if path.startswith("policy_packs/"):
        return "DEVELOPMENT_CHECK_POLICY"
    if path.startswith(("config/", "src/")) and (
        re.search(
            r"policy|policies|governance|(?:^|[_/])law(?:[_/.]|$)|(?:^|[_/])rule(?:[_/.]|$)",
            path,
            re.I,
        )
        or path.startswith(("src/risk/", "src/risk_layer/"))
    ):
        if path.startswith(
            (
                "config/governance/current_system_census_graph_v1/",
                "config/governance/current_system_interaction_authority_map_v1/",
            )
        ):
            return "DOCUMENTARY_INDEX_DATA"
        return "MACHINE_CONFIGURATION" if path.startswith("config/") else "SOURCE_INTERFACE"
    return None


def load_policies(root: Path, doc: dict) -> list[dict]:
    meta = doc["policy_inventory"]
    if (
        set(meta) != {"path", "sha256", "count", "schema"}
        or meta["path"] != "docs/system_atlas/source/current-policies.jsonl.gz"
        or meta["schema"] != "peaktrade.frozen_policy_inventory.v1"
        or type(meta["count"]) is not int
        or not isinstance(meta["sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", meta["sha256"]) is None
    ):
        raise ValueError("POLICY_INVENTORY_CONTRACT_INVALID")
    raw = (root / meta["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("POLICY_INVENTORY_DIGEST_MISMATCH")
    rows = [json.loads(x) for x in gzip.decompress(raw).splitlines()]
    if len(rows) != meta["count"] or len({x["path"] for x in rows}) != len(rows):
        raise ValueError("POLICY_INVENTORY_COUNT_MISMATCH")
    return rows


def link(path: str, label: str | None = None) -> str:
    return f"[{label or path}](../../../../{path})"


def render_law_views(doc: dict, root: Path = ROOT) -> dict[str, str]:
    policies = load_policies(root, doc)
    header = (
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. FROZEN_LAW_POLICY_VIEW AUTHORITY=NONE -->\n\n"
        "```text\nLAW_IMPACT_MAP_AUTHORITY=NONE\nLAW_REFERENCE_IS_NORMATIVE=false\n"
        f"SOURCE_TAG={doc['source_tag']}\nSOURCE_COMMIT={doc['baseline_sha']}\n"
        "RUNTIME_AUTHORIZATION_EFFECT=NONE\n```\n\n"
    )
    intro = (
        "Diese abgeleitete Sicht zeigt Regelquellen, statische Referenzen und Prüfbedarf. "
        "Die Definition und Durchsetzung einer Regel gehören zu ihrem Originalowner. "
        "Ein Pfad, Import oder Stringliteral belegt keine ausgeführte Consumerkette.\n\n"
        "Einstiege: "
        + link("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md", "Master Runbook")
        + " · "
        + link("docs/system_atlas/generated/SYSTEM_ATLAS.md", "System Atlas")
        + ".\n\n"
    )
    law = ["# Regelquellen\n\n", header, intro]
    for item in sorted(doc["law_references"], key=lambda x: x["law_id"]):
        law += [
            f"## {item['law_id']}\n\n",
            link(item["canonical_source"]) + "\n\n",
            f"Quellanker: `{item['canonical_anchor']}`. SHA256: `{item['source_sha256']}`. "
            f"Index: `{item['index_status']}`.\n\n",
        ]
    objects = ["# Zuordnung zu Fachverträgen\n\n", header, intro]
    objects.append(
        "Die Einträge bezeichnen zu prüfende Fachverträge. Ihre Funktion wird durch "
        "diese Dokumenterzeugung nicht erneut ausgeführt oder als betriebsbereit bestätigt.\n\n"
    )
    for obj in sorted(doc["semantic_objects"], key=lambda x: x["id"]):
        objects += [
            f"## {obj['id']}\n\n",
            f"Rolle: `{obj['semantic_class']}`. Prüfumfang: `{obj['current_status']}`.\n\n",
        ]
        for path in obj.get("code_surfaces", []) + obj.get("config_surfaces", []):
            objects.append("- " + link(path) + "\n")
        objects.append(
            "\nRegelreferenzen: " + ", ".join(f"`{x}`" for x in obj["law_ref_ids"]) + ".\n\n"
        )
    unknown = ["# Offene Beziehungen und Unterschiede\n\n", header, intro]
    unknown.append("## UNKNOWN_RELATION — offene Zuordnungen\n\n")
    for item in doc["unknown_relations"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['unknown_class']}`. {item['statement']}\n\n"]
    for item in doc["semantic_divergence_index"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['adjudication']}`. {item['statement']}\n\n"]
        for path in item.get("evidence_refs", []):
            if (root / path).is_file():
                unknown.append("- " + link(path) + "\n")
        unknown.append("\n")
    census = ["# Policy- und Regeldateien des Freeze\n\n", header, intro]
    census += [
        f"**{len(policies)} Dateien** im ausgewiesenen Suchumfang. "
        "Die vollständigen Referenzstellen und Quelldigests stehen im "
        "[maschinenlesbaren Katalog](../../../system_atlas/source/current-policies.jsonl.gz).\n\n",
        "Suchumfang: versionierte Quell-/Konfigurationspfade mit policy/policies/governance/law/rule, "
        "Risk-Verzeichnisse, Policy Packs und Entwicklungsregeln. Die Quellen der "
        "Dokumentprojektion und die beiden Dokumentgate-Selektoren werden gesondert geprüft. "
        "Der Katalog weist damit diesen Dateiumfang vollständig aus; die semantische "
        "Wirksamkeit jeder Regel bleibt eine Prüfung ihres konkreten Consumers.\n\n",
        "`SOURCE` bezeichnet eine Referenz aus einer Quelldatei, `TOOL` eine aus Werkzeugcode "
        "und `TEST` eine aus Tests. Ein eindeutiger Dateinamenliteral bleibt eine statische "
        "Fundstelle. Keine entdeckte Referenz ist kein Beweis für Nichtverwendung.\n\n",
    ]
    for kind in sorted({p["kind"] for p in policies}):
        census.append(f"## {kind}\n\n")
        for p in policies:
            if p["kind"] != kind:
                continue
            census += [
                "- "
                + link(p["path"])
                + f" · `{p['parse_status']}` · SHA256 `{p['frozen_sha256']}`\n",
                f"  Referenzstellen: SOURCE {p['source_reference_count']}, "
                f"TOOL {p['tool_reference_count']}, TEST {p['test_reference_count']}. "
                f"`{p['reference_status']}`.\n",
            ]
            refs = [r for r in p["static_references"] if r["scope"] == "SOURCE"][:3]
            for ref in refs:
                census.append(
                    "  "
                    + link(ref["path"], ref["path"] + ":" + str(ref["line"]))
                    + f" · `{ref['kind']}`.\n"
                )
        census.append("\n")
    census.append("## Weiterer semantischer Prüfbedarf\n\n")
    for row in doc.get("unclassified_current_surfaces", []):
        census.append("- UNCLASSIFIED: " + link(row["path"]) + "\n")
    for row in doc.get("semantic_divergence_index", []):
        census.append(f"- `{row['id']}`: `{row['adjudication']}`; siehe offene Beziehungen.\n")
    no_refs = sum(not p["static_references"] for p in policies)
    impact = ["# Law Impact Map — Regeln und Änderungsfolgen\n\n", header, intro]
    impact += [
        f"## Bestand\n\n{len(doc['law_references'])} explizite Regelreferenzen, "
        f"{len(doc['semantic_objects'])} Fachverträge und {len(policies)} indexierte Policy-/Regeldateien. "
        f"{no_refs} dieser Dateien haben im erfassten Pythonbestand keine entdeckte statische Referenz.\n\n",
        "- [Regelquellen](law_reference_index_v1.md): Originalowner, Anker und aktueller Digest.\n",
        "- [Fachverträge](semantic_object_index_v1.md): Code-/Configzuordnung ohne neue Freigabe.\n",
        "- [Vollständiger Dateiumfang](surface_census_v1.md): typisierte Policydateien und Referenzstellen.\n",
        "- [Offene Beziehungen](unknown_and_conflict_v1.md): konkrete Unterschiede und Prüfbedarf.\n\n",
        "## Prüfung einer Änderung\n\n",
        "1. Geänderte Originalregel mit dem gebundenen Quellstand vergleichen.\n",
        "2. Direkte Regelreferenzen, statische Import-/Pfadfundstellen und zugeordnete Fachverträge ermitteln.\n",
        "3. Zahlen-, Einheiten-, Zeit-, Identitäts- und Zustandsvertrag am tatsächlichen Consumer prüfen.\n",
        "4. Betroffene Prüfungen mit Originalinputs ausführen; unklassifizierte Folgen als offen belassen.\n",
        "5. Quellenbindung und diese abgeleiteten Ansichten gemeinsam nachführen.\n\n",
        "## Aussagegrenze\n\n",
        "Die jetzige Dokumentprüfung kontrolliert Dateibestand, Syntax strukturierter Quellen, "
        "Digests, Quellanker, Referenzziele und deterministische Ausgabe. Sie erteilt kein "
        "Gesamturteil über die fachliche Richtigkeit sämtlicher Policies und bestätigt keinen "
        "durchgängigen Betrieb. Numerischer Wertverbrauch, Risikoentscheidung, Permit, "
        "Venuewirkung und produktives Apply brauchen jeweils ihre eigenen Nachweise.\n",
    ]
    impact.append("\n## Erhaltene maschinell genutzte Dokumente\n\n")
    impact.append(
        "Diese Dateien sind Originaleingaben oder Schreibziele bestehender Module. Ihre Erhaltung macht sie zu keiner zusätzlichen aktuellen Systemlandkarte. Die jeweiligen Verwendungen sind statische Codebefunde.\n\n"
    )
    for item in doc.get("consumed_documents", []):
        impact.append("- " + link(item["path"]) + f" · `{item['role']}`.\n")
        for ref in [x for x in item["static_references"] if x["scope"] == "SOURCE"]:
            impact.append("  " + link(ref["path"], ref["path"] + ":" + str(ref["line"])) + ".\n")
    return {
        "law_reference_index": "".join(law).rstrip() + "\n",
        "semantic_object_index": "".join(objects).rstrip() + "\n",
        "unknown_and_conflict": "".join(unknown).rstrip() + "\n",
        "surface_census": "".join(census).rstrip() + "\n",
        "law_change_impact": "".join(impact).rstrip() + "\n",
    }


def policy_impact_for_paths(doc: dict, paths: list[str], root: Path = ROOT) -> dict:
    changed = set(paths)
    direct, source_refs, test_refs, tool_refs = set(), set(), set(), set()
    for policy in load_policies(root, doc):
        refs = policy["static_references"]
        if policy["path"] in changed or any(r["path"] in changed for r in refs):
            direct.add(policy["path"])
            for ref in refs:
                target = (
                    source_refs
                    if ref["scope"] == "SOURCE"
                    else test_refs
                    if ref["scope"] == "TEST"
                    else tool_refs
                )
                target.add(ref["path"])
    return {
        "policies": sorted(direct),
        "source_references": sorted(source_refs),
        "test_references": sorted(test_refs),
        "tool_references": sorted(tool_refs),
        "runtime_effect_inferred": False,
    }


def validate_policy_inventory(root: Path, doc: dict) -> dict:
    model = json.loads((root / "docs/system_atlas/source/current-model.json").read_bytes())
    if doc["baseline_sha"] != model["source_commit"] or doc["source_tag"] != model["source_tag"]:
        raise ValueError("LAW_POLICY_SOURCE_BINDING_MISMATCH")
    resolved = subprocess.check_output(
        ["git", "rev-parse", doc["source_tag"] + "^{commit}"], cwd=root, text=True
    ).strip()
    if resolved != doc["baseline_sha"]:
        raise ValueError("LAW_POLICY_TAG_MISMATCH")
    inventory = [
        json.loads(x)
        for x in gzip.decompress(
            (root / "docs/system_atlas/source/current-files.jsonl.gz").read_bytes()
        ).splitlines()
    ]
    frozen = {p["path"]: p for p in inventory}
    policies = load_policies(root, doc)
    validate_ordered_funding_episode_bundle(root, policies)
    validate_reserved_slot_rotation_bundle(root, policies)
    if {p["path"] for p in policies} != {p for p in frozen if policy_scope_kind(p)}:
        raise ValueError("POLICY_SCOPE_COVERAGE_MISMATCH")
    tree = {}
    for entry in subprocess.check_output(["git", "ls-tree", "-r", "-z", resolved], cwd=root).split(
        b"\0"
    ):
        if entry:
            meta, path = entry.split(b"\t", 1)
            tree[path.decode()] = meta.decode().split()[2]
    development_policy_files = []
    for policy in policies:
        path = policy["path"]
        raw = (root / path).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        original = raw
        if actual != policy["frozen_sha256"]:
            if (
                path
                not in {
                    "config/governance/clean_core_seal_manifest_v1.json",
                    "src/ops/single_selected_future_policy_v1/selection_v1.py",
                    TECHNICAL_ADMISSION,
                }
                and path not in ORDERED_FUNDING_EPISODE_DELTAS
                and path not in RESERVED_SLOT_ROTATION_DELTAS
            ):
                raise ValueError("POLICY_SOURCE_DRIFT:" + path)
            binding = json.loads(
                (root / "docs/system_atlas/source/development-binding-v1.json").read_bytes()
            )
            rows = [row for row in binding["files"] if row["path"] == path]
            if (
                binding.get("schema") != "peaktrade.atlas_development_binding.v1"
                or binding.get("authority") != "NONE"
                or binding.get("runtime_authorization_effect") != "NONE"
                or binding.get("frozen_source_commit") != resolved
                or len(rows) != 1
                or rows[0]["before_sha256"] != policy["frozen_sha256"]
                or rows[0]["sha256"] != actual
            ):
                raise ValueError("POLICY_DEVELOPMENT_BINDING_INVALID:" + path)
            original = subprocess.check_output(["git", "show", resolved + ":" + path], cwd=root)
            if path == TECHNICAL_ADMISSION:
                validate_numeric_technical_admission_delta(original, raw)
            development_policy_files.append(path)
        original_digest = hashlib.sha256(original).hexdigest()
        if original_digest != policy["frozen_sha256"] or original_digest != frozen[path]["sha256"]:
            raise ValueError("POLICY_SOURCE_DRIFT:" + path)
        git_digest = hashlib.sha1(
            b"blob " + str(len(original)).encode() + b"\0" + original
        ).hexdigest()
        if git_digest != policy["git_blob_oid"] or git_digest != tree[path]:
            raise ValueError("POLICY_GIT_OBJECT_MISMATCH:" + path)
        if policy["kind"] != policy_scope_kind(path):
            raise ValueError("POLICY_KIND_MISMATCH:" + path)
        for ref in policy["static_references"]:
            if ref["path"] not in frozen or not (root / ref["path"]).is_file() or ref["line"] < 1:
                raise ValueError("POLICY_REFERENCE_MISSING:" + ref["path"])
    for item in doc.get("consumed_documents", []):
        raw = (root / item["path"]).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != item["sha256"] or actual != frozen[item["path"]]["sha256"]:
            raise ValueError("CONSUMED_DOCUMENT_DRIFT:" + item["path"])
        git_digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if git_digest != tree[item["path"]]:
            raise ValueError("CONSUMED_DOCUMENT_GIT_MISMATCH:" + item["path"])
    return {
        "policy_files": len(policies),
        "static_reference_sites": sum(len(p["static_references"]) for p in policies),
        "no_static_reference_discovered": sum(not p["static_references"] for p in policies),
        "by_kind": dict(Counter(p["kind"] for p in policies)),
        "runtime_effect_inferred": False,
        "retained_consumed_documents": len(doc.get("consumed_documents", [])),
        "development_policy_files": development_policy_files,
    }
