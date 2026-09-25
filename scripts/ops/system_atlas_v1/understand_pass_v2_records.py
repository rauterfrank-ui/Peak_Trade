"""UNDERSTAND pass v2 payloads for remaining OPEN/PARTIAL records only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
No EVALUATE. No disposition. No identity fusion.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.system_atlas_v1.understand_pass_v1_records import (
    DELETION_COMMIT,
    DELETION_PARENT,
    _hist,
    _open,
    _raw,
    _rel,
    understood,
)

UNDERSTAND_BOUND_SHA = "a70bed0dc1586bedb58642fe7f6c6fef760b2478"
ARCHIVE_REMOVE = "75722feea8c342c56ef93f796983467f33f98f25"
ARCHIVE_PARENT = f"{ARCHIVE_REMOVE}^"
RISK_TOUCH = "f834429531cef0a6e9897c30fc792620d4f8dffa"
RISK_PARENT = "6e1ce02727f1719f8a9a5d1f001bb3e0c59411c7"
OBS_PURGE = "1c71a4eab503b2b4d06fb310a1b85b9a127e8495"
ZERO_ORDER = "00417f6ea5b6a79732b5a96fc132f158436a56a9"
STEP29M = "34574e1392af7bbfab20ce87854ee47bf5fbbe76"
INFRA = "12188014cb93a78555bbdf5cbaaf60906f6755a5"
HEALTH = "781713e9b2304733c399979273c588fec8cc7eab"
TIDY_DOCS = "42c3f443d84c4f27110083c86d0c99db61a022ed"
TODO_REMOVE = "9ede5aca0918d2778e07f0ec6f2fa9a3a18e5865"
PTR_BOUND = "cf2253aa60ffdbfd77356e33e611cd85ea53b849"
NOCH_TOUCH = "24001182de0209dabac4d6296bc7738eec442107"
WEBUI_OBS_TREE = "7a320ff950d5118e27fcff20c42e56803c57ac37"
HUB_DOC = "1cf4c2714b79ddbaeb367b44f945097bf54905fb"

PTR_ENGINE_BLOB = "19aaa49470aa766a9f813b672278fe2bcbdac3e3"
PTR_SIZER_BLOB = "439a60c8176d2990ea8e199443283f2b3e0f9a33"
PTR_MA_BLOB = "83bb67757202b250a8273faac1b1e3dd794f8493"
EXPORT_ENGINE_BLOB = "0d9869d743175c85f3e0286fc45b3b17f9d3d695"
EXPORT_MA_BLOB = "c89dad61caad99c51bd2e219d66af5956ecf28a9"

RISK_EXECUTION_IDS = ("RCN-000019", "RCN-000043", "RCN-000045", "RCN-000050")
GATE_GOVERNANCE_IDS = ("RCN-000003", "RCN-000015", "RCN-000016", "RCN-000025", "RCN-000035")
ARCHIVE_IDS = (
    "RCN-000014",
    "RCN-000036",
    "RCN-000037",
    "RCN-000038",
    "RCN-000044",
    "RCN-000045",
    "RCN-000046",
    "RCN-000051",
)
OBS_INFRA_IDS = (
    "RCN-000020",
    "RCN-000039",
    "RCN-000040",
    "RCN-000041",
    "RCN-000042",
    "RCN-000052",
)


def _mark(row: dict[str, Any]) -> dict[str, Any]:
    row["evidence_exhausted"] = True
    row.setdefault("historical_lifecycle", [])
    return row


def remaining_records() -> list[dict[str, Any]]:
    rows = [
        understood(
            rid="RCN-000014",
            historical_purpose=(
                "Nested archive/PeakTradeRepo tree (16 files) bound at tree_sha "
                "8da09657…. README describes a Peak_Trade backtest/strategy stack; "
                "recovered nested .py files in that same tree are one-line placeholders."
            ),
            problem="Preserve a nested historical Peak_Trade snapshot inside archive/.",
            inputs=[],
            outputs=["16 archived files including README, docs, placeholder src modules, tests"],
            dependencies=[],
            consumers=["RCN-000044", "RCN-000045", "RCN-000046 nested path records"],
            authority_role="Archive snapshot; not runtime authority",
            safety_role="Not an order path",
            runtime_role="Archived tree; removed from origin/main by 75722fee (#573)",
            invariants=["Inner file inventory complete at 16 files"],
            claims=[
                _raw(
                    "inner_archive_peaktraderepo.yaml: file_count=16 including "
                    "src/backtest/engine.py, src/risk/position_sizer.py, "
                    "src/strategies/ma_crossover.py.",
                    "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
                ),
                _raw(
                    "Parent blob README: Gesamtübersicht; Option A rewrites ma_crossover "
                    "to state signals 0/1.",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/README.md",
                ),
                _raw(
                    "Parent blob src/backtest/engine.py is '# Engine placeholder'.",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/backtest/engine.py",
                    f"blob:{PTR_ENGINE_BLOB}",
                ),
                _claim_contradiction(),
                _hist(
                    "Removed from tracked tree by docs: governance/audit runbooks + "
                    "remove obsolete archive/ (#573).",
                    ARCHIVE_REMOVE,
                ),
            ],
            open_questions=[
                "Whether a fuller PeakTradeRepo snapshot existed before these placeholder blobs is not reconstructed.",
            ],
            extra_relations=[
                _rel(
                    "ARCHIVES",
                    "RCN-000044",
                    "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
                ),
                _rel(
                    "ARCHIVES",
                    "RCN-000045",
                    "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
                ),
                _rel(
                    "ARCHIVES",
                    "RCN-000046",
                    "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
                ),
            ],
            historical_blobs=[PTR_ENGINE_BLOB, PTR_SIZER_BLOB, PTR_MA_BLOB],
            historical_commits=[PTR_BOUND, ARCHIVE_REMOVE],
            evidence_refs=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
                f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/README.md",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000018",
            historical_purpose=(
                "Derived conservation HISTORICAL_CHILD_LEDGER.yaml: 88 child regions "
                "(SRC-000001..) sliced from the SHA-256-bound Temporary Forensic "
                "Working Runbook. AUTHORITY NONE; not canonical selection."
            ),
            problem="Index forensic working-runbook children without promoting them.",
            inputs=["Source blob SHA-256 a5a468f7… line ranges"],
            outputs=["88 child_id rows with source_region_sha256 and ssot_role"],
            dependencies=["RCN-000022 historical_reference tree"],
            consumers=["Forensic navigation"],
            authority_role="AUTHORITY: NONE; CANONICAL_SELECTION=false",
            safety_role="TRADING_AUTHORITY=false",
            runtime_role="Derived YAML index; not importable runtime",
            invariants=["count: 88 children"],
            claims=[
                _raw(
                    "HISTORICAL_CHILD_LEDGER.yaml header PURPOSE=FORENSIC_HISTORICAL_REFERENCE; count: 88.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/conservation/HISTORICAL_CHILD_LEDGER.yaml",
                ),
            ],
            open_questions=[
                "1:1 mapping of 88 SRC children onto RCN ledger records is not proven and is not a census reopen.",
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000022",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/conservation/HISTORICAL_CHILD_LEDGER.yaml",
                ),
            ],
            historical_blobs=["a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"],
            historical_commits=[],
            evidence_refs=[
                "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/conservation/HISTORICAL_CHILD_LEDGER.yaml",
            ],
            clusters=["archives_legacy"],
        ),
        understood(
            rid="RCN-000019",
            historical_purpose=(
                "Historical top-level src/risk_layer modules: KillSwitch (emergency "
                "sticky block on daily loss/drawdown/volatility), LiquidityGate "
                "(pre-trade microstructure OK/WARN/BLOCK), StressGate (scenario shocks), "
                "VaRGate (portfolio VaR vs thresholds), plus RiskMetrics and "
                "MicrostructureMetrics extractors. Gate outputs are OK/WARN/BLOCK statuses, "
                "not order submission."
            ),
            problem="Provide operational risk-gate evaluation interfaces for trading decisions.",
            inputs=["PeakConfig; RiskMetrics; MicrostructureMetrics; portfolio positions/returns"],
            outputs=["KillSwitchStatus; LiquiditySeverity; Stress/VaR gate status dataclasses"],
            dependencies=["src.core.peak_config; src.risk.portfolio_var (VaRGate docstring)"],
            consumers=["Historical RiskGate orchestration (named in VaRGate docstring)"],
            authority_role="Policy/gate evaluator; docstring does not submit orders",
            safety_role="KillSwitch sticky until reset; LiquidityGate missing metrics → OK default",
            runtime_role="Historical top-level modules; package prefix src/risk_layer/ still present as kill_switch/ and other packages",
            invariants=[
                "CURRENTLY_PARTIAL is mechanical path presence, not identity with later packages"
            ],
            claims=[
                _raw(
                    "Parent blob kill_switch.py: Emergency safety stop; sticky until reset.",
                    f"{RISK_PARENT}:src/risk_layer/kill_switch.py",
                ),
                _raw(
                    "Parent blob liquidity_gate.py: Pre-Trade Microstructure Guards; "
                    "safe defaults missing metrics → OK.",
                    f"{RISK_PARENT}:src/risk_layer/liquidity_gate.py",
                ),
                _raw(
                    "Parent blob var_gate.py: VaR evaluation gate; integrates "
                    "src/risk/portfolio_var.py; gate interface for RiskGate orchestration.",
                    f"{RISK_PARENT}:src/risk_layer/var_gate.py",
                ),
                _raw(
                    "Parent blob stress_gate.py: Scenario-based stress testing gate.",
                    f"{RISK_PARENT}:src/risk_layer/stress_gate.py",
                ),
                _open(
                    "Identity between deleted top-level kill_switch.py and any later "
                    "src/risk_layer/kill_switch package is unproven (not fused).",
                    RISK_TOUCH,
                ),
            ],
            open_questions=[
                "Rename/move of top-level modules into src/risk_layer/kill_switch/ is unproven identity.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[RISK_TOUCH, RISK_PARENT],
            evidence_refs=[
                f"{RISK_PARENT}:src/risk_layer/kill_switch.py",
                f"{RISK_PARENT}:src/risk_layer/liquidity_gate.py",
                f"{RISK_PARENT}:src/risk_layer/var_gate.py",
                f"{RISK_PARENT}:src/risk_layer/stress_gate.py",
                f"{RISK_PARENT}:src/risk_layer/metrics.py",
            ],
            clusters=["risk_execution"],
        ),
        understood(
            rid="RCN-000020",
            historical_purpose=(
                "docs/observability Grafana/OTLP local observability stack runbook family "
                "(Collector, Tempo, Loki, Prometheus, Grafana UI) plus WP0D structured "
                "logging field catalog. Purged by security commit 1c71a4ea (#1578)."
            ),
            problem="Document a minimal local observability stack and standard log fields.",
            inputs=["scripts/obs/up.sh / down.sh; OTLP extras"],
            outputs=["Operator runbook for Grafana:3000, Prometheus:9090, Tempo, Loki"],
            dependencies=[],
            consumers=["Local operator observability"],
            authority_role="Documentation; not a trading authority",
            safety_role="Local stack; credentials via .env/GRAFANA_AUTH named in runbook",
            runtime_role="Deleted docs family; not a runtime package",
            invariants=[],
            claims=[
                _raw(
                    "Parent blob OBS_STACK_RUNBOOK.md: minimal local observability stack "
                    "OTLP Collector, Tempo, Loki, Prometheus, Grafana.",
                    f"{OBS_PURGE}^:docs/observability/OBS_STACK_RUNBOOK.md",
                ),
                _raw(
                    "Parent blob LOGGING_FIELDS.md: WP0D structured logging fields "
                    "(trace_id, session_id, strategy_id, env).",
                    f"{OBS_PURGE}^:docs/observability/LOGGING_FIELDS.md",
                ),
                _hist(
                    "Purged by security: purge Grafana artifacts and switch dashboard "
                    "output to neutral .metrics (#1578).",
                    OBS_PURGE,
                ),
            ],
            open_questions=[
                "Whether a later Grafana stack exists under another path is not answered here (EVALUATE-forbidden).",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[OBS_PURGE],
            evidence_refs=[
                f"{OBS_PURGE}^:docs/observability/OBS_STACK_RUNBOOK.md",
                f"{OBS_PURGE}^:docs/observability/LOGGING_FIELDS.md",
            ],
            clusters=["observability_infra"],
        ),
        understood(
            rid="RCN-000025",
            historical_purpose=(
                "Historical forensic heading family 'Gate-Familien' F1–F6: a terminology "
                "label in Atlas historical_terminology.yaml pointing at forensic working "
                "runbook preservation. Not proven as a standalone runtime component."
            ),
            problem="Record the historical spelling Gate-Familien / F1–F6 as a heading family.",
            inputs=["Forensic working runbook preservation copies"],
            outputs=["Terminology census row entity_kind=FAMILY, status=HISTORICAL_ONLY"],
            dependencies=["RCN-000022 forensic working runbook extract (heading source)"],
            consumers=["Atlas terminology navigation"],
            authority_role="Heading/index only; not a gate authority",
            safety_role="Not a runtime gate",
            runtime_role="Terminology census file currently present",
            invariants=["meaning: Historical forensic F1–F6 heading"],
            claims=[
                _raw(
                    "historical_terminology.yaml: Gate-Familien meaning Historical forensic "
                    "F1–F6 heading; entity_kind FAMILY; status HISTORICAL_ONLY.",
                    "docs/system_atlas/census/historical_terminology.yaml",
                ),
            ],
            open_questions=[
                "Whether F1–F6 named distinct runtime gate packages exist as other RCN records is not proven from this heading row.",
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000022",
                    "docs/system_atlas/census/historical_terminology.yaml",
                    epistemic_status="HYPOTHESIS",
                ),
            ],
            historical_blobs=[],
            historical_commits=["e94ff20c8ffb6f7e69152bcb9e2972165897cc43"],
            evidence_refs=["docs/system_atlas/census/historical_terminology.yaml"],
            clusters=["governance_gates"],
        ),
        understood(
            rid="RCN-000026",
            historical_purpose=(
                "Forensic lossless structure type NestedStructuralChild: 153 of the "
                "P19-493 KR-8/KR-9 independent-byte records in post_step32 adjudicated "
                "findings. Explicitly not SSOT_CHILD. Structure type / catalog class, "
                "not a trading component."
            ),
            problem="Keep NestedStructuralChild distinct from SSOT_CHILD and carrier index.",
            inputs=["PRODUCT_A / TARGET forensic collection"],
            outputs=[
                "Adjudicated finding F_P19_493 count split 153 NestedStructuralChild + 340 MarkedVerbatimRegion"
            ],
            dependencies=[],
            consumers=["Forensic reconstruction method"],
            authority_role="ARTIFACT_AUTHORITY=NONE; SECOND_SSOT=false",
            safety_role="Must not be moved into the carrier index (finding text)",
            runtime_role="Forensic type label in post_step32 collection",
            invariants=["not SSOT_CHILD (historical_terminology.yaml)"],
            claims=[
                _raw(
                    "05_adjudicated_findings.md F_P19_493: 153 NestedStructuralChild + 340 "
                    "MarkedVerbatimRegion; must not be fused with broader PARENT_SPAN 4105.",
                    "forensic/post_step32_knowledge_integration_v0/05_adjudicated_findings.md",
                ),
                _raw(
                    "historical_terminology.yaml: NestedStructuralChild = Forensic lossless "
                    "structure type; not SSOT_CHILD; FORENSIC_REFERENCE_ONLY.",
                    "docs/system_atlas/census/historical_terminology.yaml",
                ),
            ],
            open_questions=[],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=["b81d5181c04c2a3dc156d089fc8790ed4419782b"],
            evidence_refs=[
                "forensic/post_step32_knowledge_integration_v0/05_adjudicated_findings.md",
                "docs/system_atlas/census/historical_terminology.yaml",
            ],
            clusters=["archives_legacy"],
        ),
        understood(
            rid="RCN-000035",
            historical_purpose=(
                "Peak_Trade Visual Operator Dashboard Runbook v1.3 Composition+Landmark "
                "edition: one full-page composition, landmarks as information architecture, "
                "dashboard as consumer of canonical core. Header STATUS=HISTORICAL_PRE_RESET "
                "and superseded for Architecture Reset/Rebuild scope. Deleted with product "
                "stack b5b81728."
            ),
            problem="Define pre-reset visual operator dashboard as a single composition with landmarks.",
            inputs=[],
            outputs=["Product runbook markdown (composition + technical discovery)"],
            dependencies=[],
            consumers=["Pre-reset dashboard implementers/audits (stated)"],
            authority_role="Historical pre-reset runbook; MAY_NOT_OVERRIDE_ACTIVE_RESET_SSOT=true",
            safety_role="Dashboard exclusively consumer; no second fachliche Wahrheit (stated)",
            runtime_role="Documentation; deleted with product stack",
            invariants=["STATUS=HISTORICAL_PRE_RESET"],
            claims=[
                _raw(
                    "Parent blob title: Visual Operator Dashboard Runbook v1.3 Canonical "
                    "Composition + Technical Discovery; Ziel = eine zusammenhängende "
                    "Full-Page-Komposition.",
                    f"{DELETION_PARENT}:docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md",
                ),
                _raw(
                    "Header SUPERSEDED_FOR_ARCHITECTURE_RESET_REBUILD=true; "
                    "ACTIVE_FOR_ARCHITECTURE_RESET_REBUILD_SCOPE=false.",
                    f"{DELETION_PARENT}:docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md",
                ),
                _hist(
                    "Deleted by b5b81728 with the market dashboard product stack.", DELETION_COMMIT
                ),
            ],
            open_questions=[
                "Distinct from Landscape V2 master runbook RCN-000002; POSSIBLE_SAME_AS remains hypothesis.",
            ],
            extra_relations=[
                _rel(
                    "DOCUMENTS",
                    "RCN-000011",
                    f"{DELETION_PARENT}:docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md",
                    epistemic_status="HYPOTHESIS",
                ),
            ],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md",
            ],
            clusters=["governance_gates", "landscape_dashboard"],
        ),
        understood(
            rid="RCN-000036",
            historical_purpose=(
                "Dated archive/full_files_stand_02.12.2025 export: INSTALLATION.txt for "
                "peak_trade_phase1_phase2.tar.gz unpack plus peak_trade_export/ containing "
                "a BacktestEngine with commission/slippage, MaCrossoverStrategy, and "
                "FixedFractionalPositionSizer implementations (non-placeholder blobs)."
            ),
            problem="Hold a Phase 1+2 complete file export for installation/demo.",
            inputs=["peak_trade_phase1_phase2.tar.gz (named in INSTALLATION.txt)"],
            outputs=["20 archived files under archive/full_files_stand_02.12.2025/"],
            dependencies=[],
            consumers=["Historical install/demo path"],
            authority_role="Export snapshot; not current authority",
            safety_role="Demo scripts named; not an order path in recovered INSTALLATION.txt",
            runtime_role="Archived export; removed by #573",
            invariants=[
                "Export engine blob 0d9869d7 ≠ PeakTradeRepo placeholder engine 19aaa494",
            ],
            claims=[
                _raw(
                    "INSTALLATION.txt: PEAK_TRADE INSTALLATION Phase 1 + Phase 2 Complete; "
                    "unpack peak_trade_phase1_phase2.tar.gz.",
                    f"{ARCHIVE_PARENT}:archive/full_files_stand_02.12.2025/INSTALLATION.txt",
                ),
                _raw(
                    "Export BacktestEngine docstring: Position-basierte Backtests with "
                    "commission and slippage.",
                    f"{ARCHIVE_PARENT}:archive/full_files_stand_02.12.2025/peak_trade_export/src/backtest/engine.py",
                    f"blob:{EXPORT_ENGINE_BLOB}",
                ),
                _raw(
                    "Export MaCrossoverStrategy: Long bei Fast > Slow; register_strategy.",
                    f"{ARCHIVE_PARENT}:archive/full_files_stand_02.12.2025/peak_trade_export/src/strategies/ma_crossover.py",
                    f"blob:{EXPORT_MA_BLOB}",
                ),
            ],
            open_questions=[
                "Different tree and different blobs from archive/PeakTradeRepo; POSSIBLE_SAME_AS remains hypothesis.",
            ],
            extra_relations=[],
            historical_blobs=[EXPORT_ENGINE_BLOB, EXPORT_MA_BLOB],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/full_files_stand_02.12.2025/INSTALLATION.txt",
                f"{ARCHIVE_PARENT}:archive/full_files_stand_02.12.2025/peak_trade_export/src/backtest/engine.py",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000037",
            historical_purpose=(
                "archive/legacy_docs held a single recovered file README.before_phase58.md: "
                "project README describing a modular crypto trading/backtest stack "
                "(data layer, backtest engine, strategy registry, position sizing, risk, "
                "paper/live pipeline) as of 'Phase 1-4'."
            ),
            problem="Retain a pre-phase-58 project README in archive/legacy_docs.",
            inputs=[],
            outputs=["README.before_phase58.md"],
            dependencies=[],
            consumers=["Historical project onboarding text"],
            authority_role="Archived README; not SSOT",
            safety_role="Disclaimer: educational/research; never unaffordable capital",
            runtime_role="Docs archive; removed by #573",
            invariants=["Tree listing recovers only this one file"],
            claims=[
                _raw(
                    "README.before_phase58.md: Modularer Trading- und Backtest-Stack; "
                    "Phase 1-4; Data Layer, Backtest Engine, Strategy Registry, Risk, "
                    "Forward/Paper Trading.",
                    f"{ARCHIVE_PARENT}:archive/legacy_docs/README.before_phase58.md",
                ),
            ],
            open_questions=[],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/legacy_docs/README.before_phase58.md",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000038",
            historical_purpose=(
                "archive/legacy_scripts/run_regime_experiments.sh: bash sequencer for a "
                "BTCUSDT regime-analysis experiment series (pytest regime-aware portfolio, "
                "run_portfolio_backtest.py with --run-name/--tag, crash stress tests)."
            ),
            problem="Run a structured 7-experiment / 3-phase regime analysis sequence.",
            inputs=["config/config.toml; pytest tests/test_regime_aware_portfolio.py"],
            outputs=["Named backtest runs under reports/regime_* (commented)"],
            dependencies=["scripts/run_portfolio_backtest.py (invoked)"],
            consumers=["Operator running regime experiments"],
            authority_role="Offline experiment driver; not live order authority",
            safety_role="set -e; comments warn about unsupported --override-scale",
            runtime_role="Archived shell script; removed by #573",
            invariants=[],
            claims=[
                _raw(
                    "Script header: Regime-Analyse Experiment-Serie (BTCUSDT); 7 Experimente "
                    "in 3 Phasen; pytest + run_portfolio_backtest.py.",
                    f"{ARCHIVE_PARENT}:archive/legacy_scripts/run_regime_experiments.sh",
                ),
            ],
            open_questions=[
                "Relation to later regime-sweep scripts is unproven identity.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/legacy_scripts/run_regime_experiments.sh",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000039",
            historical_purpose=(
                "src/infra/health: central health-check package with HealthChecker/"
                "HealthStatus ampel (GREEN/YELLOW/RED) and checks for backtest, exchange, "
                "live, portfolio, risk. CLI: python -m src.infra.health.health_checker."
            ),
            problem="Provide a central module health-check / status ampel.",
            inputs=["Per-module BaseHealthCheck implementations"],
            outputs=["HealthCheckResult / HealthStatus"],
            dependencies=[],
            consumers=["CLI health_checker"],
            authority_role="Monitoring/status; not order authority",
            safety_role="LiveHealthCheck exists as a check class name; not proven as live arming",
            runtime_role="Historical package; currently absent on origin/main",
            invariants=[],
            claims=[
                _raw(
                    "__init__.py: Zentrale Health-Check-Komponenten; Ampel GREEN/YELLOW/RED.",
                    f"{HEALTH}:src/infra/health/__init__.py",
                ),
                _raw(
                    "health_checker.py: CLI python -m src.infra.health.health_checker; "
                    "imports Backtest/Exchange/Live/Portfolio/Risk health checks.",
                    f"{HEALTH}:src/infra/health/health_checker.py",
                ),
            ],
            open_questions=[
                "Deleted vs never merged to later origin/main is a presence fact, not disposition."
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[HEALTH],
            evidence_refs=[
                f"{HEALTH}:src/infra/health/__init__.py",
                f"{HEALTH}:src/infra/health/health_checker.py",
            ],
            clusters=["observability_infra"],
        ),
        understood(
            rid="RCN-000040",
            historical_purpose=(
                "src/infra/backup: automatic backups and recovery for portfolio states, "
                "trading history, and configurations (BackupManager, RecoveryManager)."
            ),
            problem="Persist and recover portfolio/trading-history/config snapshots.",
            inputs=["BackupConfig"],
            outputs=["Backup artifacts via BackupManager; recovery via RecoveryManager"],
            dependencies=[],
            consumers=["get_backup_manager / get_recovery_manager callers"],
            authority_role="Infra backup/recovery; not trading permission",
            safety_role="Recovery manager named; not an order path",
            runtime_role="Historical package; currently absent",
            invariants=[],
            claims=[
                _raw(
                    "__init__.py: Automatische Backups und Recovery für Portfolio-States, "
                    "Trading-History und Konfigurationen.",
                    f"{INFRA}:src/infra/backup/__init__.py",
                ),
            ],
            open_questions=[
                "Relation to later disaster-recovery docs/scripts is unproven identity."
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[INFRA],
            evidence_refs=[f"{INFRA}:src/infra/backup/__init__.py"],
            clusters=["observability_infra"],
        ),
        understood(
            rid="RCN-000041",
            historical_purpose=(
                "src/infra/monitoring: structured logging, performance metrics collector, "
                "and AlertManager (AlertLevel) package."
            ),
            problem="Provide structured logs, metrics, and alerts inside infra.",
            inputs=["Application log/metric events"],
            outputs=["get_logger; MetricsCollector; AlertManager"],
            dependencies=[],
            consumers=["Historical runtime modules importing this package"],
            authority_role="Monitoring/alerting; not trading permission",
            safety_role="AlertManager is notification, not kill-switch (not claimed as such)",
            runtime_role="Historical package; currently absent",
            invariants=[],
            claims=[
                _raw(
                    "__init__.py: Strukturiertes Logging, Performance-Metriken und Alert-System.",
                    f"{INFRA}:src/infra/monitoring/__init__.py",
                ),
            ],
            open_questions=[
                "Relation to deleted docs/observability or later src/obs is unproven identity."
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[INFRA],
            evidence_refs=[f"{INFRA}:src/infra/monitoring/__init__.py"],
            clusters=["observability_infra"],
        ),
        understood(
            rid="RCN-000042",
            historical_purpose=(
                "src/infra/resilience: CircuitBreaker, retry_with_backoff, Fallback, "
                "and RateLimiter helpers."
            ),
            problem="Provide circuit-breaker, retry, fallback, and rate-limit primitives.",
            inputs=["Wrapped callables / RateLimiterConfig / CircuitBreakerConfig"],
            outputs=["circuit_breaker decorator; retry; fallback; rate_limit"],
            dependencies=[],
            consumers=["Historical callers of get_circuit_breaker / retry"],
            authority_role="Infra resilience primitives; not trading permission",
            safety_role="CircuitBreakerOpenError fail-closed for wrapped calls",
            runtime_role="Historical package; currently absent",
            invariants=[],
            claims=[
                _raw(
                    "__init__.py: Circuit-Breaker, Retry-Logic, Fallback-Strategien und Rate-Limiting.",
                    f"{INFRA}:src/infra/resilience/__init__.py",
                ),
            ],
            open_questions=["Relation to later resilience docs/tests is unproven identity."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[INFRA],
            evidence_refs=[f"{INFRA}:src/infra/resilience/__init__.py"],
            clusters=["observability_infra"],
        ),
        understood(
            rid="RCN-000043",
            historical_purpose=(
                "Pre-Economic Zero-Order v1 observer/arming/evidence trio: wallclock "
                "arming lease (two-stage GO+lease, never places orders), economic "
                "evidence schema for hypothetical zero-order decisions, and "
                "decision-cycle observer of Master-V2 / Bull-Bear / Double-Play / "
                "Risk-Sizing / Killstate emitting hypothetical economics. Never grants "
                "downstream Economic/Shadow/Paper/Testnet/Live authority."
            ),
            problem="Observe a zero-order wallclock session and persist hypothetical economics.",
            inputs=[
                "Operator-GO + AuthorizationContractV1",
                "transition_state via bull_bear_state_switch_scenario_binding_adapter_v0",
                "landscape Availability for switch freshness",
            ],
            outputs=[
                "economic_decisions.jsonl; session_economic_summary.json; HypotheticalDecisionRecordV1"
            ],
            dependencies=["RCN-000004 Master V2 double_play_state / adapter"],
            consumers=["Pre-economic zero-order evidence session (historical)"],
            authority_role="Observer/evidence/arming lease; never submits orders (docstrings)",
            safety_role="Fail-closed two-stage arming; FORBIDDEN_TRUTH_CLAIMS in arming module",
            runtime_role="Historical ops modules; currently absent on origin/main",
            invariants=["Never claims ECONOMIC_VALIDITY_PASS / profitability / Shadow readiness"],
            claims=[
                _raw(
                    "wallclock_arming_v1: never places orders and never grants "
                    "Economic/Shadow/Paper/Testnet/Live.",
                    f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_wallclock_arming_v1.py",
                ),
                _raw(
                    "economic_evidence_v1: hypothetical zero-order decision economics only.",
                    f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_economic_evidence_v1.py",
                ),
                _raw(
                    "decision_cycle_observer_v1: Never submits orders. Never grants "
                    "downstream authority. Imports trading.master_v2.double_play_state.",
                    f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_decision_cycle_observer_v1.py",
                ),
            ],
            open_questions=[
                "Same family as later evidence_session modules is unproven identity.",
            ],
            extra_relations=[
                _rel(
                    "IMPORTS",
                    "RCN-000004",
                    f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_decision_cycle_observer_v1.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[ZERO_ORDER],
            evidence_refs=[
                f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_wallclock_arming_v1.py",
                f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_economic_evidence_v1.py",
                f"{ZERO_ORDER}:src/ops/pre_economic_zero_order_decision_cycle_observer_v1.py",
            ],
            clusters=["risk_execution", "master_v2_double_play"],
        ),
        understood(
            rid="RCN-000044",
            historical_purpose=(
                "Nested archive/PeakTradeRepo/src/backtest/engine.py recovered blob is "
                "the one-line comment '# Engine placeholder' (blob 19aaa494). It is not "
                "the implemented BacktestEngine in the 02.12.2025 export (blob 0d9869d7)."
            ),
            problem="Placeholder nested backtest module inside PeakTradeRepo archive tree.",
            inputs=[],
            outputs=["Placeholder file only"],
            dependencies=["RCN-000014 containing tree"],
            consumers=[],
            authority_role="Archive placeholder; not an execution engine",
            safety_role="No order path in recovered blob",
            runtime_role="Archived placeholder",
            invariants=["blob 19aaa494 ≠ export engine 0d9869d7"],
            claims=[
                _raw(
                    "Parent blob is '# Engine placeholder'.",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/backtest/engine.py",
                    f"blob:{PTR_ENGINE_BLOB}",
                ),
            ],
            open_questions=[
                "Not proven SAME_AS later src/backtest; placeholder vs implemented export engine.",
            ],
            extra_relations=[
                _rel(
                    "DEPENDS_ON",
                    "RCN-000014",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/backtest/engine.py",
                ),
            ],
            historical_blobs=[PTR_ENGINE_BLOB],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/backtest/engine.py",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000045",
            historical_purpose=(
                "Nested archive/PeakTradeRepo/src/risk/position_sizer.py recovered blob "
                "is '# Position sizer placeholder' (blob 439a60c8). Distinct from the "
                "02.12.2025 export FixedFractionalPositionSizer module."
            ),
            problem="Placeholder nested position sizer inside PeakTradeRepo archive tree.",
            inputs=[],
            outputs=["Placeholder file only"],
            dependencies=["RCN-000014"],
            consumers=[],
            authority_role="Archive placeholder; not a sizing authority",
            safety_role="No sizing math in recovered blob",
            runtime_role="Archived placeholder",
            invariants=["blob 439a60c8 is the nested placeholder"],
            claims=[
                _raw(
                    "Parent blob is '# Position sizer placeholder'.",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/risk/position_sizer.py",
                    f"blob:{PTR_SIZER_BLOB}",
                ),
            ],
            open_questions=[
                "Identity versus later sizer modules or position_sizer_old_backup is unproven; no SAME_AS.",
            ],
            extra_relations=[
                _rel(
                    "DEPENDS_ON",
                    "RCN-000014",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/risk/position_sizer.py",
                ),
            ],
            historical_blobs=[PTR_SIZER_BLOB],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/risk/position_sizer.py",
            ],
            clusters=["archive_peaktraderepo", "risk_execution"],
        ),
        understood(
            rid="RCN-000046",
            historical_purpose=(
                "Nested archive/PeakTradeRepo/src/strategies/ma_crossover.py recovered "
                "blob is '# MA Strategy placeholder' (blob 83bb6775). Distinct from "
                "export MaCrossoverStrategy blob c89dad61 and from README claims in the "
                "same PeakTradeRepo tree."
            ),
            problem="Placeholder nested MA strategy inside PeakTradeRepo archive tree.",
            inputs=[],
            outputs=["Placeholder file only"],
            dependencies=["RCN-000014"],
            consumers=[],
            authority_role="Archive placeholder; not a strategy owner",
            safety_role="No signal logic in recovered blob",
            runtime_role="Archived placeholder",
            invariants=["blob 83bb6775 ≠ export ma blob c89dad61"],
            claims=[
                _raw(
                    "Parent blob is '# MA Strategy placeholder'.",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/strategies/ma_crossover.py",
                    f"blob:{PTR_MA_BLOB}",
                ),
            ],
            open_questions=["Not proven SAME_AS later ma_crossover implementations."],
            extra_relations=[
                _rel(
                    "DEPENDS_ON",
                    "RCN-000014",
                    f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/strategies/ma_crossover.py",
                ),
            ],
            historical_blobs=[PTR_MA_BLOB],
            historical_commits=[ARCHIVE_REMOVE],
            evidence_refs=[
                f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/strategies/ma_crossover.py",
            ],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000047",
            historical_purpose=(
                "evidence/market_dashboard_reset/pr_a is a PR-A architecture-reset "
                "evidence pack (2026-07-17): git_state, file_inventory of then-active "
                "GET /market presenters/templates, allowlists, recovery logs. Distinct "
                "from the later complete deletion pack RCN-000013 (777 deleted paths)."
            ),
            problem="Record the architecture-reset worktree inventories before later product-stack deletion.",
            inputs=["Worktree on fix/market-dashboard-architecture-reset-v1 at cf416c03"],
            outputs=["TSV inventories, git_state, recovery/, validation logs"],
            dependencies=[],
            consumers=["Reset/deletion forensics"],
            authority_role="Evidence pack; not runtime",
            safety_role="forbidden_scope_list / preserve_list present as inventories",
            runtime_role="Absent path family after b5b81728",
            invariants=["Pack asserts a reset inventory, not the 777-path deletion manifest"],
            claims=[
                _raw(
                    "git_state.txt: branch=fix/market-dashboard-architecture-reset-v1 "
                    "head=cf416c03; timestamp 20260717T075706Z.",
                    f"{DELETION_PARENT}:evidence/market_dashboard_reset/pr_a/git_state.txt",
                ),
                _raw(
                    "file_inventory.tsv classifies src/webui/market_surface.py as "
                    "PRESENTER CANONICAL_MARKET_ROUTE_OWNER active_on_market=yes.",
                    f"{DELETION_PARENT}:evidence/market_dashboard_reset/pr_a/file_inventory.tsv",
                ),
                _hist("Path family deleted with product stack b5b81728.", DELETION_COMMIT),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000013 remains hypothesis: reset pack vs later deletion pack are different evidence events.",
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000023",
                    f"{DELETION_PARENT}:evidence/market_dashboard_reset/pr_a/file_inventory.tsv",
                ),
            ],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:evidence/market_dashboard_reset/pr_a/git_state.txt",
                f"{DELETION_PARENT}:evidence/market_dashboard_reset/pr_a/file_inventory.tsv",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000048",
            historical_purpose=(
                "docs/20_phases path family: numbered phase markdowns (e.g. Phase 16A "
                "ExecutionPipeline core package: orders from strategies through "
                "Environment/Safety to Executor + RunLogger; LIVE blocked in Phase 16A)."
            ),
            problem="Document sequential product/engineering phases as markdown files.",
            inputs=[],
            outputs=["Phase_*.md files under docs/20_phases"],
            dependencies=[],
            consumers=["Historical phase navigation"],
            authority_role="Phase documentation; Phase 16A text blocks LIVE",
            safety_role="LIVE-Mode hart blockiert (Phase 16A recovered header)",
            runtime_role="Docs family; currently absent",
            invariants=[],
            claims=[
                _raw(
                    "PHASE_16A_EXECUTION_PIPELINE.md: ExecutionPipeline takes orders from "
                    "strategies/portfolios through Environment & Safety to Executor; "
                    "ohne Live-Support; LIVE hart blockiert.",
                    f"{TIDY_DOCS}:docs/20_phases/PHASE_16A_EXECUTION_PIPELINE.md",
                ),
            ],
            open_questions=["Path move versus later runbook locations is unproven identity."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[TIDY_DOCS],
            evidence_refs=[
                f"{TIDY_DOCS}:docs/20_phases/PHASE_16A_EXECUTION_PIPELINE.md",
            ],
            clusters=["governance_gates"],
        ),
        understood(
            rid="RCN-000049",
            historical_purpose=(
                "docs/00_overview path family historically held overview/roadmap/status/"
                "workflow notes plus a TODO board (PEAK_TRADE_OVERVIEW.md redirected to "
                "ARCHITECTURE.md; TODO board later removed by 9ede5aca). Distinct path "
                "family from src/docs (RCN-000053)."
            ),
            problem="Hold overview and TODO-board documents at docs/00_overview.",
            inputs=[],
            outputs=["Overview/status/roadmap/TODO-board markdown/HTML"],
            dependencies=[],
            consumers=["Historical onboarding/TODO generation"],
            authority_role="Overview docs; PEAK_TRADE_OVERVIEW.md says use ARCHITECTURE.md",
            safety_role="Not runtime",
            runtime_role="Docs family; currently absent",
            invariants=[],
            claims=[
                _raw(
                    "PEAK_TRADE_OVERVIEW.md: Architektur & Überblick; Hinweis konsolidiert "
                    "zu ARCHITECTURE.md.",
                    f"{TIDY_DOCS}:docs/00_overview/PEAK_TRADE_OVERVIEW.md",
                ),
                _hist(
                    "TODO board removed by Remove TODO Board implementation completely.",
                    TODO_REMOVE,
                ),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS src/docs RCN-000053 remains hypothesis; different path families.",
            ],
            extra_relations=[
                _rel(
                    "POSSIBLE_SAME_AS",
                    "RCN-000053",
                    f"{TIDY_DOCS}:docs/00_overview/PEAK_TRADE_OVERVIEW.md",
                    epistemic_status="HYPOTHESIS",
                ),
            ],
            historical_blobs=[],
            historical_commits=[TODO_REMOVE, TIDY_DOCS],
            evidence_refs=[f"{TIDY_DOCS}:docs/00_overview/PEAK_TRADE_OVERVIEW.md"],
            clusters=["archives_legacy"],
        ),
        understood(
            rid="RCN-000050",
            historical_purpose=(
                "STEP29M candidate-specific offline v2 research family: three versioned "
                "strategy modules (bollinger_bands, momentum_1h, trend_following) plus "
                "research-scope implementation v0. Each v2 keeps parent v1 as immutable "
                "negative baseline; no economic evaluation, no runtime authority, no "
                "policy relaxation. Grouping is path-prefix plus shared research owner; "
                "the three STRATEGY_IDs remain distinct."
            ),
            problem="Diagnose named terminal failure classes offline without forcing trades or relaxing gates.",
            inputs=["OHLCV DataFrame; parent v1 strategy owners"],
            outputs=["v2 strategy signals + eligibility/guard traces; research-scope runner"],
            dependencies=["src.strategies.bollinger / momentum / trend_following v1 owners"],
            consumers=["STEP29M research-scope implementation v0"],
            authority_role="Offline research; no runtime authority (research module docstring)",
            safety_role="Does not relax survival/suitability/risk/safety/economic policy gates (bollinger v2)",
            runtime_role="Historical strategies/research modules; currently absent",
            invariants=["Parent v1 remains immutable negative baseline"],
            claims=[
                _raw(
                    "step29m_bollinger_bands_v2.py: offline-only diagnostic-first; no forcing "
                    "trades or relaxing policy gates.",
                    f"{STEP29M}:src/strategies/step29m_bollinger_bands_v2.py",
                ),
                _raw(
                    "step29m_momentum_1h_v2.py: offline-only; SPARSE_SAMPLE_SINGLE_TRADE_DOMINANCE guards.",
                    f"{STEP29M}:src/strategies/step29m_momentum_1h_v2.py",
                ),
                _raw(
                    "step29m_trend_following_v2.py: offline-only; preserves v1 entry semantics.",
                    f"{STEP29M}:src/strategies/step29m_trend_following_v2.py",
                ),
                _raw(
                    "research scope v0: No economic evaluation, no runtime authority, no policy relaxation.",
                    "cef8881d417752dfea044c44b0014bf59190545f:src/research/step29m_candidate_specific_research_scope_implementation_v0.py",
                ),
            ],
            open_questions=[
                "Ledger record groups three strategies by path prefix; they are not fused into one identity.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[STEP29M],
            evidence_refs=[
                f"{STEP29M}:src/strategies/step29m_bollinger_bands_v2.py",
                f"{STEP29M}:src/strategies/step29m_momentum_1h_v2.py",
                f"{STEP29M}:src/strategies/step29m_trend_following_v2.py",
                "cef8881d417752dfea044c44b0014bf59190545f:src/research/step29m_candidate_specific_research_scope_implementation_v0.py",
            ],
            clusters=["risk_execution"],
        ),
        understood(
            rid="RCN-000051",
            historical_purpose=(
                "archive/noch_einordnen held a single README.md whose recovered text "
                "matches the PeakTradeRepo README (Option A–F Gesamtübersicht). Queued "
                "archive folder; not a second proven source tree."
            ),
            problem="Queue unclassified archive material (folder name noch_einordnen).",
            inputs=[],
            outputs=["README.md only in recovered tree"],
            dependencies=[],
            consumers=[],
            authority_role="Queue folder; not runtime",
            safety_role="Not an order path",
            runtime_role="Archived; last touch 24001182",
            invariants=["Recovered tree listing is README.md only"],
            claims=[
                _raw(
                    "Parent blob README.md starts Peak_Trade System – Gesamtübersicht "
                    "with Option A Strategy-Fix (State-Signale).",
                    f"{NOCH_TOUCH}^:archive/noch_einordnen/README.md",
                ),
            ],
            open_questions=[
                "Text overlap with PeakTradeRepo README is not SAME_AS without blob-identity proof.",
            ],
            extra_relations=[
                _rel(
                    "POSSIBLE_SAME_AS",
                    "RCN-000014",
                    f"{NOCH_TOUCH}^:archive/noch_einordnen/README.md",
                    epistemic_status="HYPOTHESIS",
                ),
            ],
            historical_blobs=[],
            historical_commits=[NOCH_TOUCH],
            evidence_refs=[f"{NOCH_TOUCH}^:archive/noch_einordnen/README.md"],
            clusters=["archive_peaktraderepo"],
        ),
        understood(
            rid="RCN-000052",
            historical_purpose=(
                "docs/webui/observability family: Observability Hub v0 read-only HTML "
                "surface (GET /observability) bundling links to existing GET endpoints "
                "without orders, activation, capital/scope release, kill-switch override, "
                "or workflow trigger; plus Paper/Shadow read-model contracts and futures "
                "universe/source contracts."
            ),
            problem="Provide a display-only operator observability hub and related contracts.",
            inputs=["Existing GET endpoints / template status stub"],
            outputs=["Hub HTML docs; contract markdowns; PROMETHEUS_LOCAL_SCRAPE.yml"],
            dependencies=[],
            consumers=["Operator WebUI observability route (documented)"],
            authority_role="Read-only / display-only; no new authority (hub doc)",
            safety_role="Explicit non-offer: no orders, no live activation, no kill-switch override",
            runtime_role="Deleted docs family (last tree 7a320ff9)",
            invariants=["No client polling on hub HTML (stated)"],
            claims=[
                _raw(
                    "OBSERVABILITY_HUB_V0.md: read-only/display-only HTML; keine Orders; "
                    "keine Testnet-/Live-Aktivierung; kein KillSwitch-Override.",
                    f"{HUB_DOC}:docs/webui/observability/OBSERVABILITY_HUB_V0.md",
                ),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS Grafana docs/observability RCN-000020 remains hypothesis (different stack/docs generation).",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[WEBUI_OBS_TREE, HUB_DOC],
            evidence_refs=[
                f"{HUB_DOC}:docs/webui/observability/OBSERVABILITY_HUB_V0.md",
            ],
            clusters=["observability_infra"],
        ),
    ]
    return [_mark(row) for row in rows]


def _claim_contradiction() -> dict[str, Any]:
    return {
        "claim_class": "CONTRADICTION",
        "text": (
            "PeakTradeRepo README describes a rewritten ma_crossover with state signals, "
            "while the nested ma_crossover.py blob in the same tree is a one-line placeholder."
        ),
        "evidence": [
            f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/README.md",
            f"{ARCHIVE_PARENT}:archive/PeakTradeRepo/src/strategies/ma_crossover.py",
        ],
        "used_as_fact": False,
    }


def v2_clusters() -> list[dict[str, Any]]:
    return [
        {
            "cluster_id": "risk_execution",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Historical risk-layer gates, zero-order observer, nested sizer placeholder, STEP29M research strategies.",
            "record_ids": list(RISK_EXECUTION_IDS),
        },
        {
            "cluster_id": "governance_gates",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Runbook indexes, selector, superseded Vollautonomie, Gate-Familien heading, composition landmark, phase docs.",
            "record_ids": list(GATE_GOVERNANCE_IDS) + ["RCN-000048"],
        },
        {
            "cluster_id": "archives_legacy",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Forensic indexes, NestedStructuralChild type, historical child ledger, overview docs, src/docs.",
            "record_ids": ["RCN-000018", "RCN-000026", "RCN-000049"],
        },
        {
            "cluster_id": "archive_peaktraderepo",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Nested PeakTradeRepo, 02.12.2025 export, legacy_docs/scripts, noch_einordnen. Not one snapshot.",
            "record_ids": list(ARCHIVE_IDS),
        },
        {
            "cluster_id": "observability_infra",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Grafana obs docs, WebUI observability hub docs, infra health/backup/monitoring/resilience.",
            "record_ids": list(OBS_INFRA_IDS),
        },
    ]
