"""FIND_COMPLETELY pass v2 ledger/candidate/coverage persist helpers.

ATLAS_AUTHORITY=NONE. No disposition. No identity fusion. No current-system comparison.
"""

from __future__ import annotations

from typing import Any


def _record(
    *,
    rid: str,
    name: str,
    historical_names: list[str],
    aliases: list[str],
    presence: str,
    discovered_from: list[str],
    evidence: list[str],
    paths: list[str],
    claims: list[dict[str, Any]],
    questions: list[str],
    notes: str,
    relations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "identity": {
            "reconciliation_id": rid,
            "canonical_record_name": name,
            "historical_names": historical_names,
            "aliases": aliases,
        },
        "discovery": {
            "discovery_status": "EVIDENCE_BOUND",
            "current_presence": presence,
            "discovered_from": discovered_from,
            "discovery_evidence": evidence,
            "first_bound_ref": "origin/main",
            "historical_paths": paths,
            "historical_refs": ["origin/main"],
            "historical_commits": [],
            "claims": claims,
        },
        "understanding": {
            "purpose_understood": False,
            "purpose_statement": "",
            "historical_problem_statement": "",
            "inputs": [],
            "outputs": [],
            "dependencies": [],
            "consumers": [],
            "authority_role": "",
            "safety_role": "",
            "runtime_role": "",
            "invariants": [],
        },
        "relations": {"items": relations or []},
        "current_comparison": {
            "current_equivalent": "",
            "current_paths": [],
            "capability_overlap": "",
            "semantic_compatibility": "",
            "authority_compatibility": "",
            "safety_compatibility": "",
            "runtime_compatibility": "",
            "conflicts": [],
            "gaps": [],
        },
        "adjudication": {
            "lifecycle_state": "EVIDENCE_BOUND",
            "disposition": "",
            "positive_reason": "",
            "evidence_refs": [],
            "contradictions": [],
            "unresolved_questions": questions,
        },
        "integration": {
            "reintegration_required": False,
            "adaptation_required": False,
            "implementation_status": "",
            "implementation_refs": [],
        },
        "audit": {
            "created_from_evidence": True,
            "last_adjudicated_against_sha": "",
            "notes": notes,
        },
    }


def _psa(target: str, evidence: str) -> dict[str, Any]:
    return {
        "relation_type": "POSSIBLE_SAME_AS",
        "target_id": target,
        "unresolved_target": "",
        "evidence": [evidence],
        "epistemic_status": "HYPOTHESIS",
    }


def pass_v2_records() -> list[dict[str, Any]]:
    """New evidence-bound records. Fail-open: no unproven identity merge."""
    return [
        _record(
            rid="RCN-000025",
            name="Gate-Familien F1-F6 forensic heading family",
            historical_names=["Gate-Familien", "F1", "F2", "F3", "F4", "F5", "F6"],
            aliases=[],
            presence="CURRENTLY_PRESENT",
            discovered_from=["SURF:atlas_index", "SURF:forensic_corpus"],
            evidence=["docs/system_atlas/census/historical_terminology.yaml"],
            paths=["docs/system_atlas/census/historical_terminology.yaml"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Atlas historical_terminology records Gate-Familien as a historical forensic F1-F6 heading.",
                    "evidence": ["docs/system_atlas/census/historical_terminology.yaml"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Whether F1-F6 named a runtime gate family remains uninvestigated. Atlas status is navigation only.",
                    "evidence": [],
                },
            ],
            questions=["Are F1-F6 a standalone historical component versus headings only?"],
            notes="Promoted from CAND:gate_familien_f1_f6. Purpose not investigated. Not fused with dashboard family_id.",
        ),
        _record(
            rid="RCN-000026",
            name="NestedStructuralChild forensic structure type",
            historical_names=["NestedStructuralChild"],
            aliases=[],
            presence="CURRENTLY_PRESENT",
            discovered_from=["SURF:forensic_corpus", "SURF:atlas_index"],
            evidence=[
                "forensic/post_step32_knowledge_integration_v0/05_adjudicated_findings.md",
                "docs/system_atlas/census/historical_terminology.yaml",
            ],
            paths=["forensic/post_step32_knowledge_integration_v0/"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Literal NestedStructuralChild exists in committed forensic extracts.",
                    "evidence": [
                        "forensic/post_step32_knowledge_integration_v0/05_adjudicated_findings.md"
                    ],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Forensic type versus a lost runtime child component is unresolved.",
                    "evidence": [],
                },
            ],
            questions=["Is this only a forensic structure label?"],
            notes="Terminology/forensic hit. Atlas says not SSOT_CHILD. Not fused with CAND:ssot_child_literal.",
        ),
        _record(
            rid="RCN-000027",
            name="Market depth v0 readmodel/runtime",
            historical_names=[
                "market_depth_readmodel_v0",
                "market_depth_runtime_v0",
                "market_depth_api_v0",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=[
                "src/webui/market_depth_api_v0.py",
                "src/webui/market_depth_readmodel_v0",
                "src/webui/market_depth_runtime_v0.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted src/webui market_depth v0 paths appear in the all-refs deletion census and on non-main tip trees.",
                    "evidence": ["src/webui/market_depth_readmodel_v0"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Identity versus later dashboard packages is unresolved.",
                    "evidence": [],
                },
            ],
            questions=["Standalone depth component versus product_surface_v1?"],
            notes="Split from CAND:market_dashboard_v0_depth_tape_funnel. Fail-open versus other v0 modules.",
            relations=[_psa("RCN-000009", "deleted dashboard generation hypothesis")],
        ),
        _record(
            rid="RCN-000028",
            name="Market tape v0 readmodel",
            historical_names=["market_tape_readmodel_v0"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=["src/webui/market_tape_readmodel_v0"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Path family src/webui/market_tape_readmodel_v0 is in the deletion census and absent from origin/main.",
                    "evidence": ["src/webui/market_tape_readmodel_v0"],
                }
            ],
            questions=["Standalone tape component versus later dashboard packages?"],
            notes="Split from grouped v0 candidate. Not fused with depth/funnel.",
            relations=[_psa("RCN-000027", "adjacent deleted v0 dashboard modules")],
        ),
        _record(
            rid="RCN-000029",
            name="Market ranking funnel v0",
            historical_names=[
                "market_ranking_funnel_readmodel_v0",
                "market_ranking_funnel_runtime_v0",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=[
                "src/webui/market_ranking_funnel_readmodel_v0",
                "src/webui/market_ranking_funnel_runtime_v0.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted ranking-funnel v0 paths are in the deletion census.",
                    "evidence": ["src/webui/market_ranking_funnel_readmodel_v0"],
                }
            ],
            questions=["Relation to later landscape ranking displays?"],
            notes="Fail-open versus other v0 modules.",
            relations=[_psa("RCN-000009", "deleted dashboard generation hypothesis")],
        ),
        _record(
            rid="RCN-000030",
            name="Market futures OHLCV v0",
            historical_names=[
                "market_futures_ohlcv_readmodel_v0",
                "market_futures_ohlcv_runtime_v0",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=[
                "src/webui/market_futures_ohlcv_readmodel_v0",
                "src/webui/market_futures_ohlcv_runtime_v0.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted futures OHLCV v0 paths are in the deletion census.",
                    "evidence": ["src/webui/market_futures_ohlcv_readmodel_v0"],
                }
            ],
            questions=["Standalone OHLCV component versus later dashboard packages?"],
            notes="Fail-open versus other v0 modules.",
            relations=[_psa("RCN-000012", "v0 dashboard generation hypothesis")],
        ),
        _record(
            rid="RCN-000031",
            name="Market instrument eligibility v0",
            historical_names=["market_instrument_eligibility_v0"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=["src/webui/market_instrument_eligibility_v0.py"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/webui/market_instrument_eligibility_v0.py is in the deletion census.",
                    "evidence": ["src/webui/market_instrument_eligibility_v0.py"],
                }
            ],
            questions=["Standalone eligibility module versus later ranking/universe producers?"],
            notes="Single named vanished module. Not fused.",
            relations=[_psa("RCN-000009", "deleted dashboard generation hypothesis")],
        ),
        _record(
            rid="RCN-000032",
            name="Market active paper run runtime v0",
            historical_names=["market_active_paper_run_runtime_v0"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=["src/webui/market_active_paper_run_runtime_v0.py"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/webui/market_active_paper_run_runtime_v0.py is in the deletion census.",
                    "evidence": ["src/webui/market_active_paper_run_runtime_v0.py"],
                }
            ],
            questions=["Relation to paper-shadow runtimes?"],
            notes="Named vanished module. Purpose not investigated.",
            relations=[_psa("RCN-000012", "v0 dashboard generation hypothesis")],
        ),
        _record(
            rid="RCN-000033",
            name="Market dashboard current state v0",
            historical_names=[
                "market_dashboard_current_state_runtime_v0",
                "market_dashboard_current_state_snapshot_v0",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=[
                "src/webui/market_dashboard_current_state_runtime_v0.py",
                "src/webui/market_dashboard_current_state_snapshot_v0.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted current-state v0 modules are in the deletion census.",
                    "evidence": ["src/webui/market_dashboard_current_state_runtime_v0.py"],
                }
            ],
            questions=["Predecessor of later landscape current-state?"],
            notes="Fail-open versus Landscape V2 package.",
            relations=[_psa("RCN-000001", "later landscape naming hypothesis")],
        ),
        _record(
            rid="RCN-000034",
            name="Deleted market dashboard product runbooks",
            historical_names=[
                "Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0",
                "Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3",
                "MARKET_DASHBOARD_PRODUCT_SURFACE_V1",
                "MARKET_DASHBOARD_READMODELS_V1",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_docs", "SURF:historical_path_family_docs"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=[
                "docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md",
                "docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md",
                "docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md",
                "docs/webui/MARKET_DASHBOARD_READMODELS_V1.md",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Named product/webui dashboard runbooks are in the deletion census and absent from origin/main as those paths.",
                    "evidence": [
                        "docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md"
                    ],
                }
            ],
            questions=[
                "Documentation of RCN-000009/000010/000011 or a distinct product definition?"
            ],
            notes="Promoted from CAND:deleted_market_dashboard_product_runbooks. Not fused with code packages.",
            relations=[
                _psa("RCN-000009", "product_surface_v1 documentation hypothesis"),
                _psa("RCN-000011", "visual operator runbook naming"),
            ],
        ),
        _record(
            rid="RCN-000035",
            name="Composition Landmark Master Runbook v1.3",
            historical_names=["Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_docs"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=["docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted composition-landmark runbook path is in the docs deletion census.",
                    "evidence": [
                        "docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md"
                    ],
                }
            ],
            questions=["Distinct from Landscape V2 master runbook RCN-000002?"],
            notes="Fail-open versus RCN-000002 and RCN-000034.",
            relations=[_psa("RCN-000002", "master runbook naming hypothesis")],
        ),
        _record(
            rid="RCN-000036",
            name="archive/full_files_stand_02.12.2025 export tree",
            historical_names=["full_files_stand_02.12.2025", "peak_trade_export"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_code", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=[
                "archive/full_files_stand_02.12.2025/INSTALLATION.txt",
                "archive/full_files_stand_02.12.2025/peak_trade_export",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Historical archive export tree exists in reachable history and on non-main tip trees; absent from origin/main.",
                    "evidence": [
                        "archive/full_files_stand_02.12.2025/peak_trade_export/src/backtest/engine.py"
                    ],
                }
            ],
            questions=["Same snapshot as archive/PeakTradeRepo or a different export?"],
            notes="Inner python modules listed in tree census. Not fused with RCN-000014.",
            relations=[_psa("RCN-000014", "both are nested archive trees")],
        ),
        _record(
            rid="RCN-000037",
            name="archive/legacy_docs",
            historical_names=["legacy_docs", "README.before_phase58"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_docs"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["archive/legacy_docs/README.before_phase58.md"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "archive/legacy_docs/README.before_phase58.md exists in reachable history and is absent from origin/main.",
                    "evidence": ["archive/legacy_docs/README.before_phase58.md"],
                }
            ],
            questions=["What documents did this archive hold besides the README?"],
            notes="Path inventory hit. Contents not mined for purpose.",
        ),
        _record(
            rid="RCN-000038",
            name="archive/legacy_scripts run_regime_experiments",
            historical_names=["run_regime_experiments.sh"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:tooling_corpus", "SURF:archived_code"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["archive/legacy_scripts/run_regime_experiments.sh"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Deleted legacy script archive/legacy_scripts/run_regime_experiments.sh is in reachable history.",
                    "evidence": ["archive/legacy_scripts/run_regime_experiments.sh"],
                }
            ],
            questions=["Standalone tooling component versus later regime sweep scripts?"],
            notes="Single archived script. Purpose not investigated.",
        ),
        _record(
            rid="RCN-000039",
            name="src/infra/health historical package",
            historical_names=["infra.health", "health_checker"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches", "SURF:historical_path_family_src"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["src/infra/health"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/infra/health exists on non-main unique tip trees and is absent from origin/main src/infra (which has escalation/runbooks only).",
                    "evidence": ["src/infra/health/health_checker.py"],
                }
            ],
            questions=["Deleted, renamed, or never merged to origin/main?"],
            notes="Tip-tree discovery. Not fused with current src/infra/escalation.",
        ),
        _record(
            rid="RCN-000040",
            name="src/infra/backup historical package",
            historical_names=["infra.backup", "backup_manager"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["src/infra/backup"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/infra/backup exists on non-main unique tip trees and is absent from origin/main.",
                    "evidence": ["src/infra/backup/backup_manager.py"],
                }
            ],
            questions=["Relation to disaster-recovery docs/scripts?"],
            notes="Fail-open versus other infra tip packages.",
        ),
        _record(
            rid="RCN-000041",
            name="src/infra/monitoring historical package",
            historical_names=["infra.monitoring"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["src/infra/monitoring"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/infra/monitoring exists on non-main unique tip trees and is absent from origin/main.",
                    "evidence": ["src/infra/monitoring/metrics.py"],
                }
            ],
            questions=["Relation to current src/obs or src/observability?"],
            notes="Name similarity to observability is not identity.",
        ),
        _record(
            rid="RCN-000042",
            name="src/infra/resilience historical package",
            historical_names=["infra.resilience", "circuit_breaker"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["src/infra/resilience"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "src/infra/resilience exists on non-main unique tip trees and is absent from origin/main.",
                    "evidence": ["src/infra/resilience/circuit_breaker.py"],
                }
            ],
            questions=["Relation to current resilience docs/tests?"],
            notes="Fail-open versus other infra packages.",
        ),
        _record(
            rid="RCN-000043",
            name="pre_economic_zero_order observer/arming tip modules",
            historical_names=[
                "pre_economic_zero_order_decision_cycle_observer_v1",
                "pre_economic_zero_order_economic_evidence_v1",
                "pre_economic_zero_order_wallclock_arming_v1",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=[
                "src/ops/pre_economic_zero_order_decision_cycle_observer_v1.py",
                "src/ops/pre_economic_zero_order_economic_evidence_v1.py",
                "src/ops/pre_economic_zero_order_wallclock_arming_v1.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "These three modules exist on non-main tip trees. origin/main has a different pre_economic_zero_order_evidence_session_* family.",
                    "evidence": ["src/ops/pre_economic_zero_order_wallclock_arming_v1.py"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Rename/absorption into evidence_session_* is not proven.",
                    "evidence": [],
                },
            ],
            questions=[
                "Same family as current evidence_session modules or a distinct observer/arming stack?"
            ],
            notes="Fail-open versus current origin/main pre_economic_zero_order_evidence_session_* files.",
        ),
        _record(
            rid="RCN-000044",
            name="PeakTradeRepo nested backtest engine",
            historical_names=["archive/PeakTradeRepo/src/backtest"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_code"],
            evidence=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
            paths=[
                "archive/PeakTradeRepo/src/backtest/engine.py",
                "archive/PeakTradeRepo/src/backtest/results.py",
                "archive/PeakTradeRepo/src/backtest/stats.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Inner archive file inventory lists three backtest modules under archive/PeakTradeRepo.",
                    "evidence": ["archive/PeakTradeRepo/src/backtest/engine.py"],
                }
            ],
            questions=["Same component as later src/backtest or a distinct nested snapshot?"],
            notes="Inner file of RCN-000014. Not fused with current src/backtest. Purpose not investigated.",
            relations=[_psa("RCN-000014", "files live inside the nested archive tree")],
        ),
        _record(
            rid="RCN-000045",
            name="PeakTradeRepo nested position_sizer",
            historical_names=["archive/PeakTradeRepo/src/risk/position_sizer.py"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_code"],
            evidence=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
            paths=["archive/PeakTradeRepo/src/risk/position_sizer.py"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Inner archive file inventory lists src/risk/position_sizer.py inside PeakTradeRepo.",
                    "evidence": ["archive/PeakTradeRepo/src/risk/position_sizer.py"],
                }
            ],
            questions=[
                "Identity versus deleted position_sizer_old_backup or current sizer modules?"
            ],
            notes="Fail-open versus CAND:position_sizer_old_backup. Name is not identity.",
            relations=[_psa("RCN-000014", "files live inside the nested archive tree")],
        ),
        _record(
            rid="RCN-000046",
            name="PeakTradeRepo nested ma_crossover strategy",
            historical_names=["archive/PeakTradeRepo/src/strategies/ma_crossover.py"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_code"],
            evidence=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
            paths=["archive/PeakTradeRepo/src/strategies/ma_crossover.py"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "Inner archive file inventory lists src/strategies/ma_crossover.py inside PeakTradeRepo.",
                    "evidence": ["archive/PeakTradeRepo/src/strategies/ma_crossover.py"],
                }
            ],
            questions=["Same strategy as later ma_crossover implementations?"],
            notes="Fail-open versus archive/full_files_stand export ma_crossover.",
            relations=[
                _psa("RCN-000014", "files live inside the nested archive tree"),
                _psa("RCN-000036", "export tree also lists src/strategies/ma_crossover.py"),
            ],
        ),
        _record(
            rid="RCN-000047",
            name="evidence/market_dashboard_reset pack",
            historical_names=["market_dashboard_reset"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:evidence_corpus", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["evidence/market_dashboard_reset/pr_a"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "evidence/market_dashboard_reset/pr_a exists on non-main tip trees and is absent from origin/main evidence/ top-level.",
                    "evidence": ["evidence/market_dashboard_reset/pr_a"],
                }
            ],
            questions=[
                "Same deletion event as evidence/market_dashboard_deletion or a different reset pack?"
            ],
            notes="Fail-open versus RCN-000013.",
            relations=[_psa("RCN-000013", "dashboard evidence-pack naming hypothesis")],
        ),
        _record(
            rid="RCN-000048",
            name="docs/20_phases historical path family",
            historical_names=["docs/20_phases"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_docs", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["docs/20_phases"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "docs/20_phases/PHASE_*.md paths exist on non-main tip trees. origin/main currently has many PHASE_*.md files at docs/ root, not under docs/20_phases/.",
                    "evidence": ["docs/20_phases/PHASE_16A_EXECUTION_PIPELINE.md"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Rename from docs/20_phases/ to docs/ is not proven. No RENAMED_TO asserted.",
                    "evidence": [],
                },
            ],
            questions=["Path move versus a distinct document set?"],
            notes="Path-family census. Not a current-system comparison. Purpose of the family not investigated.",
        ),
        _record(
            rid="RCN-000049",
            name="docs/00_overview historical path family",
            historical_names=["docs/00_overview"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_docs", "SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=["docs/00_overview"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "docs/00_overview paths exist on non-main tip trees. Matching filenames currently exist at docs/ root on origin/main.",
                    "evidence": ["docs/00_overview/PEAK_TRADE_OVERVIEW.md"],
                },
                {
                    "claim_class": "OPEN_QUESTION",
                    "text": "Rename is not proven.",
                    "evidence": [],
                },
            ],
            questions=["Path move versus distinct overview documents?"],
            notes="Fail-open versus current docs/ root files with similar names.",
        ),
        _record(
            rid="RCN-000050",
            name="step29m strategy/research family",
            historical_names=[
                "step29m_bollinger_bands_v2",
                "step29m_momentum_1h_v2",
                "step29m_trend_following_v2",
            ],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:local_branches"],
            evidence=["docs/system_atlas/reconciliation/inventories/tree_content_census.yaml"],
            paths=[
                "src/strategies/step29m_bollinger_bands_v2.py",
                "src/strategies/step29m_momentum_1h_v2.py",
                "src/strategies/step29m_trend_following_v2.py",
                "src/research/step29m_candidate_specific_research_scope_implementation_v0.py",
            ],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "step29m strategy/research modules exist on non-main tip trees and are absent from origin/main.",
                    "evidence": ["src/strategies/step29m_bollinger_bands_v2.py"],
                }
            ],
            questions=[
                "One research workstream or three distinct strategies? Grouping is path-prefix only."
            ],
            notes="Path-prefix grouping is not identity fusion of the three strategy files with each other as one component; record is the named workstream family. Individual files remain listed.",
        ),
        _record(
            rid="RCN-000051",
            name="archive/noch_einordnen",
            historical_names=["noch_einordnen"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:archived_docs", "SURF:archived_code"],
            evidence=["git log --all -- archive/noch_einordnen"],
            paths=["archive/noch_einordnen/README.md"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "archive/noch_einordnen/README.md exists in reachable added-path history.",
                    "evidence": ["archive/noch_einordnen/README.md"],
                }
            ],
            questions=["What was queued in this archive?"],
            notes="Named archive bucket. Not exhausted beyond the README path.",
        ),
        _record(
            rid="RCN-000052",
            name="docs/webui/observability deleted family",
            historical_names=["docs/webui/observability"],
            aliases=[],
            presence="CURRENTLY_ABSENT",
            discovered_from=["SURF:historical_path_family_docs", "SURF:archived_docs"],
            evidence=["docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"],
            paths=["docs/webui/observability"],
            claims=[
                {
                    "claim_class": "FORENSIC_RAW_FACT",
                    "text": "docs/webui/observability is a deleted-path family (31 files in census) and also appears on non-main tip trees.",
                    "evidence": [
                        "docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"
                    ],
                }
            ],
            questions=[
                "Same observability stack as deleted docs/observability Grafana family RCN-000020?"
            ],
            notes="Fail-open versus RCN-000020. Path prefix differs.",
            relations=[_psa("RCN-000020", "observability documentation naming hypothesis")],
        ),
    ]


def coverage_row(
    *,
    surface_id: str,
    surface_type: str,
    searched: bool,
    method: str,
    scope_count: int,
    evidence_reference: str,
    exhaustion_proven: bool,
    remaining_gap: str,
    exhaustion_unproven_reason: str,
    limitations: str,
) -> dict[str, Any]:
    return {
        "surface_id": surface_id,
        "surface_type": surface_type,
        "searched": searched,
        "method": method,
        "scope_count": scope_count,
        "evidence_reference": evidence_reference,
        "exhaustion_proven": exhaustion_proven,
        "remaining_gap": remaining_gap,
        "exhaustion_unproven_reason": exhaustion_unproven_reason,
        "search_executed": searched,
        "search_method": method,
        "result_count": scope_count,
        "evidence_ref": evidence_reference,
        "coverage_status": "EXHAUSTION_PROVEN" if exhaustion_proven else "EXHAUSTION_UNPROVEN",
        "limitations": limitations,
    }
