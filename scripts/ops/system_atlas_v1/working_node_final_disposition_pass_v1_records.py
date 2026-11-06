"""Working-node owner-final dispositions. Additive persist. Not RCN census.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reopen the 53-record RCN census, fuse identities, reintegrate,
or authorize implementation.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

PASS_ID = "WORKING_NODE_FINAL_DISPOSITION_PASS_V1"
BOUND_REF = "origin/main"
BOUND_SHA = "b6bcdfbd62205d3be9ca30105735132ac9e7aaec"
OWNER_GO = "PEAK_TRADE_RECONSOLIDATION_CANONICAL_FINAL_DISPOSITION_PERSISTENCE_V1"
IDENTITY_UNIVERSE = "RELATIONAL_WORKING_NODE_NOT_RCN_CENSUS"
EXPECTED_COUNT = 99
EXPECTED_RETAIN = 78
EXPECTED_ADAPT = 12
EXPECTED_COVERED = 5
EXPECTED_HVBI = 3
EXPECTED_REJECT = 1
EXPECTED_ACCEPTED = 95
EXPECTED_CHANGED = 4
EXPECTED_SAFETY_CRITICAL = 37

OWNER_TO_TAXONOMY = {
    "RETAIN_AS_IS": "RETAIN_AS_IS",
    "ADAPT": "ADAPT_AND_REINTEGRATE",
    "ALREADY_COVERED": "CAPABILITY_ALREADY_COVERED",
    "HISTORICALLY_VALID_BUT_INCOMPATIBLE": "HISTORICALLY_VALID_BUT_INCOMPATIBLE",
    "REJECT_WITH_POSITIVE_REASON": "REJECT_FOR_CURRENT_SYSTEM",
}

STRUCT_PATHS: dict[str, list[str]] = {
    "WN-SRC-AI": ["src/ai"],
    "WN-SRC-AI-ORCH": ["src/ai_orchestration"],
    "WN-SRC-AIOPS": ["src/aiops"],
    "WN-SRC-ANALYTICS": ["src/analytics"],
    "WN-SRC-AUTONOMOUS": ["src/autonomous"],
    "WN-SRC-BACKTEST": ["src/backtest"],
    "WN-CORE-PEAK-CONFIG": ["src/core/peak_config.py"],
    "WN-CORE-BACKUP-RECOVERY": ["src/core/backup_recovery.py"],
    "WN-CORE-REGIME": ["src/core/regime.py"],
    "WN-CORE-RISK": ["src/core/risk.py", "src/core/position_sizing.py"],
    "WN-CORE-RESILIENCE": ["src/core/resilience.py"],
    "WN-CORE-ENVIRONMENT": ["src/core/environment.py"],
    "WN-SRC-FEATURES": ["src/features"],
    "WN-SRC-FORWARD": ["src/forward"],
    "WN-SRC-GOVERNANCE-PROMOTION": ["src/governance/promotion_loop"],
    "WN-PROMOTION-ECONOMIC-GATE": ["src/governance/promotion_loop/promotion_economic_gate_v1.py"],
    "WN-SRC-INGRESS": ["src/ingress"],
    "WN-SRC-KNOWLEDGE": ["src/knowledge"],
    "WN-SRC-LEVELUP": ["src/levelup"],
    "WN-SRC-LIVE-EVAL": ["src/live_eval"],
    "WN-SRC-MACRO-REGIMES": ["src/macro_regimes"],
    "WN-SRC-MARKET-SENTINEL": ["src/market_sentinel"],
    "WN-SRC-MARKETS-CME": ["src/markets"],
    "WN-SRC-META-LEARNING-LOOP": ["src/meta/learning_loop"],
    "WN-SRC-META-INFOSTREAM": ["src/meta/infostream"],
    "WN-SRC-NOTIFICATIONS": ["src/notifications"],
    "WN-SRC-OBS": ["src/obs"],
    "WN-SRC-OBSERVABILITY": ["src/observability"],
    "WN-SRC-ORDERS": ["src/orders"],
    "WN-SRC-PORTFOLIO": ["src/portfolio"],
    "WN-SRC-R-AND-D": ["src/r_and_d"],
    "WN-SRC-REGIME": ["src/regime"],
    "WN-SRC-REPORTING": ["src/reporting"],
    "WN-SRC-RISK": ["src/risk"],
    "WN-SRC-RISK-LAYER": ["src/risk_layer"],
    "WN-RISK-LAYER-KILL-SWITCH": ["src/risk_layer/kill_switch"],
    "WN-SRC-SCHEDULER": ["src/scheduler"],
    "WN-SRC-SHADOW-NO-ORDER": ["src/shadow_no_order_proof"],
    "WN-SRC-SIM": ["src/sim"],
    "WN-SRC-STRATEGIES": ["src/strategies"],
    "WN-SRC-SWEEPS": ["src/sweeps"],
    "WN-SRC-THEORY": ["src/theory"],
    "WN-SRC-TRADING-MV2": ["src/trading/master_v2"],
    "WN-DP": ["src/ops/double_play"],
    "WN-SRC-TRIGGER-TRAINING": ["src/trigger_training"],
    "WN-SRC-WEBUI": ["src/webui"],
    "WN-LIVE-WEB": ["src/live/web"],
    "WN-LIVE-SAFETY": ["src/live/safety.py"],
    "WN-LIVE-GATES": ["src/live/live_gates.py"],
    "WN-LIVE-ALERT-PIPELINE": ["src/live/alert_pipeline.py"],
    "WN-LIVE-DATA-QUALITY-GATE": ["src/live/data_quality_gate.py"],
    "WN-LIVE-TESTNET-ORCH": ["src/live/testnet_orchestrator.py"],
    "WN-LIVE-EXEC-BRIDGE": ["src/live/execution_bridge.py"],
    "WN-LIVE-SHADOW-SESSION": ["src/live/shadow_session.py"],
    "WN-INFRA-ESCALATION": ["src/infra/escalation"],
    "WN-INFRA-RUNBOOKS": ["src/infra/runbooks"],
    "WN-EXECUTION-PIPELINE": ["src/execution_pipeline"],
    "WN-EXECUTION-SIMPLE": ["src/execution_simple"],
    "WN-EXECUTION": ["src/execution"],
    "WN-EXEC-ALERTING": ["src/execution/alerting"],
    "WN-OPS-GATES": ["src/ops/gates"],
    "WN-OPS-WIRING": ["src/ops/wiring"],
    "WN-OPS-RECON": ["src/ops/recon"],
    "WN-OPS-TEST-HEALTH": ["src/ops/test_health_runner.py"],
    "WN-CAP11": ["src/ops/capability_11_1_execution_domain_and_order_lifecycle_contracts_v1"],
    "WN-EXP-MONTE-CARLO": ["src/experiments/monte_carlo.py"],
    "WN-EXP-STRESS-TESTS": ["src/experiments/stress_tests.py"],
    "WN-EXP-I16-ADMISSION": [
        "src/experiments/canonical_experiment_identity_to_package_n_i16_promotion_admission_v1.py"
    ],
    "WN-SCRIPT-SERVE-LIVE-DASH": ["scripts/serve_live_dashboard.py"],
    "WN-SCRIPT-LIVE-WEB-SERVER": ["scripts/live_web_server.py"],
    "WN-SCRIPT-TELEMETRY-ALERTS": ["scripts/telemetry_alerts.py"],
    "WN-MV2-PROMOTION-OFFLINE-ADAPTER": [
        "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py"
    ],
    "WN-MV2-PROMOTION-BT-ADAPTER": [
        "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py"
    ],
    "WN-RESEARCH-CS-PANEL-WIRING": [
        "src/research/cross_sectional_panel_economic_evaluation_wiring_v0.py"
    ],
}

HIST_PATHS: dict[str, list[str]] = {
    "WN-HIST-INFRA-HEALTH": ["src/infra/health"],
    "WN-HIST-INFRA-BACKUP": ["src/infra/backup"],
    "WN-HIST-INFRA-MONITORING": ["src/infra/monitoring"],
    "WN-HIST-INFRA-RESILIENCE": ["src/infra/resilience"],
    "WN-HIST-OPS-MV2-MINSEL": ["src/ops/master_v2_minimal_selector_v1"],
    "WN-HIST-WEBUI-DASH-PRODUCT": ["src/webui/market_dashboard_product_surface_v1"],
    "WN-HIST-WEBUI-DASH-READMODELS": ["src/webui/market_dashboard_readmodels_v1"],
    "WN-HIST-WEBUI-VISUAL-OPS": ["src/webui/market_visual_operator_surface_v1"],
    "WN-HIST-REGIME-SEQUENCER": ["archive/legacy_scripts"],
    "WN-HIST-NESTED-PEAKTRADEREPO": ["archive/PeakTradeRepo"],
}

RES_MATCHERS: tuple[tuple[str, Any], ...] = (
    ("WN-RES-ENTRY-EFF-MR", lambda n: "entry_effective_mr" in n),
    ("WN-RES-ADX", lambda n: n.startswith("adx") or "_adx_" in n),
    ("WN-RES-BULL-BEAR-BIND", lambda n: n == "owner_bindings" or "bull_bear" in n),
    ("WN-RES-META-LABEL", lambda n: n == "ml" or "meta_label" in n),
    ("WN-RES-OPEN-MR-BACKLOG", lambda n: "regime_gated_standaside" in n or "open_mr" in n),
    ("WN-RES-NEW-LISTINGS", lambda n: "new_listing" in n or n == "new_listings"),
    ("WN-RES-BOLLINGER", lambda n: "bollinger" in n),
    ("WN-RES-VOL-MAXAGE", lambda n: "max_age" in n or "volatility_max" in n),
    (
        "WN-RES-VOL-BREAKOUT",
        lambda n: any(
            x in n
            for x in (
                "volatility_breakout",
                "volatility_decay",
                "term_structure",
                "volatility_contraction",
                "volatility_compression",
                "vol_regime",
                "volatility_regime",
                "volatility_expansion",
            )
        ),
    ),
    (
        "WN-RES-CS-RS",
        lambda n: any(x in n for x in ("relative_strength", "cross_sectional")),
    ),
    ("WN-RES-PIT-OKX", lambda n: any(x in n for x in ("pit_", "okx_panel", "chronological_pit"))),
    ("WN-RES-MOMENTUM-1H", lambda n: "momentum" in n),
    (
        "WN-RES-OFFLINE-PANEL-EVAL",
        lambda n: any(x in n for x in ("evaluation_runner", "offline_panel", "panel_eval")),
    ),
    ("WN-RES-LINEAR-DIAG", lambda n: "linear" in n),
    (
        "WN-RES-MR-FILTERS",
        lambda n: any(x in n for x in ("rsi_exhaustion", "mr_eligibility", "mr_filter")),
    ),
)

EVALUATE_SAFETY_CRITICAL = frozenset(
    {
        "WN-CAP11",
        "WN-CORE-BACKUP-RECOVERY",
        "WN-CORE-ENVIRONMENT",
        "WN-CORE-RISK",
        "WN-DP",
        "WN-EXECUTION",
        "WN-EXECUTION-PIPELINE",
        "WN-EXECUTION-SIMPLE",
        "WN-HIST-INFRA-BACKUP",
        "WN-HIST-INFRA-HEALTH",
        "WN-HIST-INFRA-MONITORING",
        "WN-HIST-INFRA-RESILIENCE",
        "WN-HIST-NESTED-PEAKTRADEREPO",
        "WN-HIST-OPS-MV2-MINSEL",
        "WN-LIVE-DATA-QUALITY-GATE",
        "WN-LIVE-EXEC-BRIDGE",
        "WN-LIVE-GATES",
        "WN-LIVE-SAFETY",
        "WN-LIVE-SHADOW-SESSION",
        "WN-LIVE-TESTNET-ORCH",
        "WN-OPS-GATES",
        "WN-OPS-RECON",
        "WN-OPS-WIRING",
        "WN-PROMOTION-ECONOMIC-GATE",
        "WN-RISK-LAYER-KILL-SWITCH",
        "WN-SRC-AUTONOMOUS",
        "WN-SRC-GOVERNANCE-PROMOTION",
        "WN-SRC-MARKETS-CME",
        "WN-SRC-META-LEARNING-LOOP",
        "WN-SRC-ORDERS",
        "WN-SRC-PORTFOLIO",
        "WN-SRC-RISK",
        "WN-SRC-RISK-LAYER",
        "WN-SRC-SCHEDULER",
        "WN-SRC-SHADOW-NO-ORDER",
        "WN-SRC-TRADING-MV2",
        "WN-SRC-REGIME",
    }
)

# index|wn|proposed_owner|final_owner|reason
_ROW_TABLE = """
A01|WN-SRC-TRADING-MV2|RETAIN_AS_IS|RETAIN_AS_IS|unique canonical core; retain is justified
A02|WN-DP|RETAIN_AS_IS|RETAIN_AS_IS|justified quarantine marker, not inner core
A03|WN-CORE-PEAK-CONFIG|RETAIN_AS_IS|RETAIN_AS_IS|justified config primitive
A04|WN-CORE-ENVIRONMENT|RETAIN_AS_IS|RETAIN_AS_IS|required safety-chain input
A05|WN-LIVE-SAFETY|RETAIN_AS_IS|RETAIN_AS_IS|live safety owner; retain does not enable live
A06|WN-OPS-GATES|RETAIN_AS_IS|RETAIN_AS_IS|required gate primitives
A07|WN-OPS-WIRING|RETAIN_AS_IS|RETAIN_AS_IS|required guard wiring
A08|WN-RISK-LAYER-KILL-SWITCH|RETAIN_AS_IS|RETAIN_AS_IS|unique durable kill-switch
A09|WN-SRC-RISK-LAYER|RETAIN_AS_IS|RETAIN_AS_IS|justified canonical risk_layer package; overlap with src.risk is not SAME_AS
A10|WN-SRC-RISK|RETAIN_AS_IS|RETAIN_AS_IS|unique VaR/CMES residual vs risk_layer; library role not live path
A11|WN-CORE-RISK|RETAIN_AS_IS|RETAIN_AS_IS|distinct backtest risk contract; not live sizer
A12|WN-PROMOTION-ECONOMIC-GATE|RETAIN_AS_IS|RETAIN_AS_IS|bound economic predicate; no live implication in this WN alone
A13|WN-EXECUTION|RETAIN_AS_IS|RETAIN_AS_IS|production gated execution identity
A14|WN-EXECUTION-PIPELINE|RETAIN_AS_IS|RETAIN_AS_IS|distinct NO-LIVE plan-only contract
A15|WN-EXECUTION-SIMPLE|REJECT_WITH_POSITIVE_REASON|REJECT_WITH_POSITIVE_REASON|superseded by WN-EXECUTION + WN-EXECUTION-PIPELINE; parallel pipeline creates harmful authority ambiguity
A16|WN-SRC-ORDERS|RETAIN_AS_IS|RETAIN_AS_IS|order construction types; structure is not submit
A17|WN-LIVE-EXEC-BRIDGE|RETAIN_AS_IS|RETAIN_AS_IS|observation bridge not transport
A18|WN-LIVE-TESTNET-ORCH|ADAPT|ADAPT|preserve lifecycle orchestration only behind explicit Testnet Owner-GO and unique runtime entrypoint
A19|WN-LIVE-GATES|ADAPT|ADAPT|preserve eligibility predicates; eligibility is not a permit
A20|WN-LIVE-SHADOW-SESSION|RETAIN_AS_IS|RETAIN_AS_IS|session type retained; productive CLI remains guarded
A21|WN-SRC-SHADOW-NO-ORDER|RETAIN_AS_IS|RETAIN_AS_IS|no-order proof slice
A22|WN-CAP11|RETAIN_AS_IS|RETAIN_AS_IS|unauthorized contract family; retain is not Cap-11 GO
A23|WN-LIVE-DATA-QUALITY-GATE|RETAIN_AS_IS|RETAIN_AS_IS|justified MD hard gate
A24|WN-SRC-STRATEGIES|RETAIN_AS_IS|RETAIN_AS_IS|strategy resolution owner
A25|WN-SRC-FEATURES|RETAIN_AS_IS|RETAIN_AS_IS|canonical Features step
A26|WN-SRC-INGRESS|RETAIN_AS_IS|RETAIN_AS_IS|public MD ingress
A27|WN-SRC-REGIME|ADAPT|ADAPT|preserve regime detection for research/shadow; do not preserve StrategySwitchingPolicy as competing DP authority
A28|WN-CORE-REGIME|RETAIN_AS_IS|RETAIN_AS_IS|distinct scoring primitive vs src.regime switching
A29|WN-SRC-MACRO-REGIMES|RETAIN_AS_IS|RETAIN_AS_IS|not a switch owner; research/config overlay justified
A30|WN-SRC-MARKETS-CME|RETAIN_AS_IS|RETAIN_AS_IS|research/data calendar library; CME versus OKX is not reject
A31|WN-SRC-MARKET-SENTINEL|RETAIN_AS_IS|RETAIN_AS_IS|orthogonal outlook; not decision owner
A32|WN-SRC-PORTFOLIO|ADAPT|ADAPT|preserve allocation analytics only; no productive multi-symbol/multi-position orchestration
A33|WN-SRC-FORWARD|RETAIN_AS_IS|RETAIN_AS_IS|paper/forward structures; not submit path
A34|WN-SRC-GOVERNANCE-PROMOTION|ADAPT|ADAPT|preserve promotion/economic governance; promotion is not live authorization
A35|WN-SRC-META-LEARNING-LOOP|ADAPT|ADAPT|preserve ConfigPatch proposal capability; self-learning is not self-authorizing
A36|WN-MV2-PROMOTION-OFFLINE-ADAPTER|RETAIN_AS_IS|RETAIN_AS_IS|explicit offline adapter
A37|WN-MV2-PROMOTION-BT-ADAPTER|RETAIN_AS_IS|RETAIN_AS_IS|backtest binding wrap
A38|WN-SRC-BACKTEST|RETAIN_AS_IS|RETAIN_AS_IS|required simulation engine including walkforward
A39|WN-SRC-SIM|RETAIN_AS_IS|RETAIN_AS_IS|simulation modules; justified non-live role
A40|WN-SRC-R-AND-D|RETAIN_AS_IS|RETAIN_AS_IS|read-only local artifacts; not trading path
A41|WN-SRC-SWEEPS|RETAIN_AS_IS|RETAIN_AS_IS|research sweep infra
A42|WN-SRC-THEORY|RETAIN_AS_IS|RETAIN_AS_IS|orthogonal math library with unique models
A43|WN-SRC-LEVELUP|RETAIN_AS_IS|RETAIN_AS_IS|evidence-first contracts; authority-neutral
A44|WN-SRC-TRIGGER-TRAINING|RETAIN_AS_IS|RETAIN_AS_IS|justified operator-training; must remain offline/non-authority
A45|WN-EXP-MONTE-CARLO|RETAIN_AS_IS|RETAIN_AS_IS|research harness; not live
A46|WN-EXP-STRESS-TESTS|RETAIN_AS_IS|RETAIN_AS_IS|research harness; not live
A47|WN-EXP-I16-ADMISSION|RETAIN_AS_IS|RETAIN_AS_IS|research harness; not live
A48|WN-RESEARCH-CS-PANEL-WIRING|RETAIN_AS_IS|RETAIN_AS_IS|research wiring not CS-RS identity
A49|WN-RES-ENTRY-EFF-MR|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A50|WN-RES-ADX|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A51|WN-RES-BULL-BEAR-BIND|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; not DP compute
A52|WN-RES-META-LABEL|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A53|WN-RES-OPEN-MR-BACKLOG|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A54|WN-RES-NEW-LISTINGS|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A55|WN-RES-BOLLINGER|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A56|WN-RES-VOL-MAXAGE|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; VOLATILITY_NUMERIC_MAX_AGE_ENFORCING=false
A57|WN-RES-VOL-BREAKOUT|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A58|WN-RES-CS-RS|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A59|WN-RES-PIT-OKX|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A60|WN-RES-MOMENTUM-1H|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A61|WN-RES-OFFLINE-PANEL-EVAL|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A62|WN-RES-LINEAR-DIAG|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A63|WN-RES-MR-FILTERS|RETAIN_AS_IS|RETAIN_AS_IS|unique preregistered hypothesis/harness; AUTHORITY_EFFECT=NONE
A64|WN-SRC-WEBUI|RETAIN_AS_IS|RETAIN_AS_IS|Landscape V2 authorized read-only GET /market; DASHBOARD_AUTHORITY_EFFECT=NONE
A65|WN-LIVE-WEB|RETAIN_AS_IS|RETAIN_AS_IS|parallel T8 shadow/paper monitor; not Landscape duplicate of purpose
A66|WN-SCRIPT-SERVE-LIVE-DASH|RETAIN_AS_IS|RETAIN_AS_IS|primary LIVE-WEB runner
A67|WN-SCRIPT-LIVE-WEB-SERVER|ALREADY_COVERED|ALREADY_COVERED|duplicate CLI not a second web capability; classification is not required deletion
A68|WN-SRC-OBS|RETAIN_AS_IS|RETAIN_AS_IS|optional OTel; distinct from observability logging
A69|WN-SRC-OBSERVABILITY|RETAIN_AS_IS|RETAIN_AS_IS|structured logging/metrics for live execution monitoring
A70|WN-SRC-REPORTING|RETAIN_AS_IS|RETAIN_AS_IS|observation/reporting; not decision owner
A71|WN-SRC-ANALYTICS|RETAIN_AS_IS|RETAIN_AS_IS|Master-V2 analytics
A72|WN-SRC-NOTIFICATIONS|RETAIN_AS_IS|RETAIN_AS_IS|forward-signal notify layer; parallel alerting is not SAME_AS
A73|WN-LIVE-ALERT-PIPELINE|RETAIN_AS_IS|RETAIN_AS_IS|live-track alerts default escalation off; distinct from telemetry
A74|WN-EXEC-ALERTING|RETAIN_AS_IS|RETAIN_AS_IS|telemetry alert state machine
A75|WN-SCRIPT-TELEMETRY-ALERTS|RETAIN_AS_IS|RETAIN_AS_IS|dry-run-default CLI for EXEC-ALERTING
A76|WN-SRC-LIVE-EVAL|RETAIN_AS_IS|RETAIN_AS_IS|post-session evaluation
A77|WN-SRC-META-INFOSTREAM|RETAIN_AS_IS|RETAIN_AS_IS|intel pipeline; not self-authorizing trading
A78|WN-INFRA-ESCALATION|RETAIN_AS_IS|RETAIN_AS_IS|optional on-call; default off
A79|WN-INFRA-RUNBOOKS|RETAIN_AS_IS|RETAIN_AS_IS|incident doc registry
A80|WN-CORE-BACKUP-RECOVERY|RETAIN_AS_IS|ADAPT|ungated restore is a known material adaptation requirement; RETAIN_AS_IS would treat an unsafe recovery path as complete
A81|WN-CORE-RESILIENCE|RETAIN_AS_IS|RETAIN_AS_IS|justified library; generic health_check is not historical domain health
A82|WN-SRC-SCHEDULER|ADAPT|ADAPT|preserve generic scheduling; do not start deauthorized productive runtime entrypoints
A83|WN-SRC-AUTONOMOUS|ADAPT|ADAPT|preserve research-workflow automation; no trading-decision autonomy or second MV2/DP authority
A84|WN-SRC-AI-ORCH|RETAIN_AS_IS|RETAIN_AS_IS|SoD/ForbiddenAutonomyError; orthogonal AI-ops
A85|WN-SRC-AIOPS|RETAIN_AS_IS|RETAIN_AS_IS|AI-ops toolchain; not live trading
A86|WN-SRC-AI|RETAIN_AS_IS|RETAIN_AS_IS|model-invocation utilities; distinct from L1-L4 orch
A87|WN-SRC-KNOWLEDGE|RETAIN_AS_IS|RETAIN_AS_IS|research KB; not runtime authority
A88|WN-OPS-RECON|RETAIN_AS_IS|RETAIN_AS_IS|canonical recon gate; SAFETY CRITICAL
A89|WN-OPS-TEST-HEALTH|RETAIN_AS_IS|RETAIN_AS_IS|CI/test-health runner
A90|WN-HIST-INFRA-HEALTH|ADAPT|ADAPT|preserve domain-specific operational health concept; no old CCXT Kraken or live-enable semantics
A91|WN-HIST-INFRA-BACKUP|ADAPT|HISTORICALLY_VALID_BUT_INCOMPATIBLE|historical gzip/caller-dict/retention residuals are not a required current strategic capability; unsafe as recovery owner
A92|WN-HIST-INFRA-MONITORING|ADAPT|ALREADY_COVERED|current split observability/alerting/escalation architecture covers the strategic capability; historical unified facade is not a required strategic residual
A93|WN-HIST-INFRA-RESILIENCE|ADAPT|ADAPT|preserve RateLimiter + Fallback capability if implemented; integrate into current core resilience, no second resilience SSOT
A94|WN-HIST-OPS-MV2-MINSEL|HISTORICALLY_VALID_BUT_INCOMPATIBLE|HISTORICALLY_VALID_BUT_INCOMPATIBLE|incompatibility is unique selection owner, not revert history
A95|WN-HIST-WEBUI-DASH-PRODUCT|ALREADY_COVERED|ALREADY_COVERED|coverage from Landscape semantics, not tombstone alone
A96|WN-HIST-WEBUI-DASH-READMODELS|ALREADY_COVERED|ALREADY_COVERED|Landscape semantics cover consumer-snapshot purpose
A97|WN-HIST-WEBUI-VISUAL-OPS|ADAPT|ADAPT|preserve evidence-bound visual operator concepts inside Landscape V2; do not resurrect tombstoned historical package
A98|WN-HIST-REGIME-SEQUENCER|ADAPT|ALREADY_COVERED|current backtest/sweeps/Monte-Carlo/stress/regime research composition covers the strategic experiment-orchestration capability
A99|WN-HIST-NESTED-PEAKTRADEREPO|HISTORICALLY_VALID_BUT_INCOMPATIBLE|HISTORICALLY_VALID_BUT_INCOMPATIBLE|preserve archival evidence; no runtime restoration; HVBI is not deletion of git history
"""

ADAPT_DETAILS: dict[str, dict[str, str]] = {
    "WN-SRC-AUTONOMOUS": {
        "preserve_capability": "research-workflow automation (monitors/workflow engine for research jobs)",
        "do_not_restore_or_preserve": "trading-decision autonomy / second MV2/DP authority / auto-wire to execution",
        "target_current_architectural_home": "research/ops workflow runner, not canonical decision path",
        "adaptation_boundary": "unwired to MV2 compute; no order submit",
    },
    "WN-SRC-PORTFOLIO": {
        "preserve_capability": "capital-allocation / weight analytics as research/backtest helpers",
        "do_not_restore_or_preserve": "productive multi-symbol/multi-strategy orchestration",
        "target_current_architectural_home": "research/backtest analytics under single-future constraint",
        "adaptation_boundary": "MULTI_FUTURE_RUNTIME_AUTHORIZED=false",
    },
    "WN-LIVE-GATES": {
        "preserve_capability": "strategy eligibility predicates as non-authorizing checks",
        "do_not_restore_or_preserve": "portfolio/multi-position eligibility; ops.double_play as compute owner; eligibility-as-execution-permit",
        "target_current_architectural_home": "live/safety or ops.gates as predicate consumers of MV2/DP packets",
        "adaptation_boundary": "eligibility != permit; single-future only",
    },
    "WN-SRC-GOVERNANCE-PROMOTION": {
        "preserve_capability": "promotion candidate/decision governance + economic gating",
        "do_not_restore_or_preserve": "implication that promotion = to live without Owner-GO",
        "target_current_architectural_home": "governance.promotion_loop as offline/proposal layer feeding MV2 economic gate",
        "adaptation_boundary": "promotion != LIVE_ENABLED",
    },
    "WN-SRC-META-LEARNING-LOOP": {
        "preserve_capability": "ConfigPatch learning proposals / evaluation snippets",
        "do_not_restore_or_preserve": "self-authorizing config or runtime mutation",
        "target_current_architectural_home": "proposal producer into promotion economic gate; never direct writer to live config",
        "adaptation_boundary": "SELF_LEARNING_NOT_SELF_AUTHORIZING=true",
    },
    "WN-LIVE-TESTNET-ORCH": {
        "preserve_capability": "shadow/testnet lifecycle orchestration under unique entrypoint",
        "do_not_restore_or_preserve": "unauthorized testnet start; parallel productive CLI",
        "target_current_architectural_home": "governed unique runtime entrypoint / Master-V2 legacy-entrypoint guard",
        "adaptation_boundary": "no start without explicit Testnet Owner-GO; no real orders",
    },
    "WN-SRC-SCHEDULER": {
        "preserve_capability": "generic job scheduling",
        "do_not_restore_or_preserve": "productive invocation of deauthorized legacy execution/testnet/shadow CLIs",
        "target_current_architectural_home": "scheduler as ops job runner behind MV2 legacy-entrypoint guard",
        "adaptation_boundary": "scheduler != trading authority",
    },
    "WN-SRC-REGIME": {
        "preserve_capability": "regime detection for research/shadow",
        "do_not_restore_or_preserve": "StrategySwitchingPolicy as live/competing switch authority",
        "target_current_architectural_home": "research/shadow feature input to MV2; not DP compute",
        "adaptation_boundary": "detection != switch owner",
    },
    "WN-HIST-INFRA-HEALTH": {
        "preserve_capability": "DOMAIN_SPECIFIC_OPERATIONAL_HEALTH (module probes with explicit fail states)",
        "do_not_restore_or_preserve": "CCXT Kraken exchange_check; old enable_live_trading flags; hist package identity as live gate",
        "target_current_architectural_home": "ops.gates / core.resilience HealthCheck registrations bound to current OKX/no-order predicates",
        "adaptation_boundary": "no multi-venue ccxt; no live enablement semantics",
    },
    "WN-HIST-INFRA-RESILIENCE": {
        "preserve_capability": "RateLimiter (token bucket) + Fallback around external calls, plus CB/retry semantics already partly in core",
        "do_not_restore_or_preserve": "Kraken-scoped hist package; async registry as second resilience SSOT",
        "target_current_architectural_home": "src/core/resilience.py extensions",
        "adaptation_boundary": "no venue-specific Kraken assumptions; no second CB owner",
    },
    "WN-HIST-WEBUI-VISUAL-OPS": {
        "preserve_capability": "offline evidence-bound visual operator zone (linear diagnostics, decision-funnel display, AI activity state)",
        "do_not_restore_or_preserve": "tombstoned package identity market_visual_operator_surface_v1",
        "target_current_architectural_home": "Landscape V2 read-only slots / presenter (WN-SRC-WEBUI)",
        "adaptation_boundary": "DASHBOARD_AUTHORITY_EFFECT=NONE; no package resurrection",
    },
    "WN-CORE-BACKUP-RECOVERY": {
        "preserve_capability": "config/state/data snapshot utility",
        "do_not_restore_or_preserve": "productive ungated restore as system recovery owner",
        "target_current_architectural_home": "core.backup_recovery as non-productive snapshot helper until recon/KS/guards are explicit preconditions",
        "adaptation_boundary": "RECON_REQUIRED KILL_SWITCH_REQUIRED EXECUTION_GUARDS_REQUIRED before any productive restore",
    },
}

COVERING: dict[str, dict[str, str]] = {
    "WN-SCRIPT-LIVE-WEB-SERVER": {
        "covering_working_node_id": "WN-SCRIPT-SERVE-LIVE-DASH",
        "coverage_reason": "both call src.live.web.app.create_app",
        "unique_residual_capability": "NONE_PROVEN",
    },
    "WN-HIST-WEBUI-DASH-PRODUCT": {
        "covering_working_node_id": "WN-SRC-WEBUI",
        "coverage_reason": "Landscape V2 is current authorized GET /market product shell; tombstone is supporting evidence not to restore identity",
        "unique_residual_capability": "NONE_PROVEN",
    },
    "WN-HIST-WEBUI-DASH-READMODELS": {
        "covering_working_node_id": "WN-SRC-WEBUI",
        "coverage_reason": "Landscape projection family replaces fail-closed consumer snapshots; schema IDs replaced not absorbed",
        "unique_residual_capability": "NONE_PROVEN",
    },
    "WN-HIST-INFRA-MONITORING": {
        "covering_working_node_id": "WN-SRC-OBSERVABILITY",
        "coverage_reason": "structured logging+metrics currently owned; alerting/incident/escalation covered in parallel by WN-EXEC-ALERTING, WN-LIVE-ALERT-PIPELINE, WN-INFRA-ESCALATION",
        "unique_residual_capability": "NONE_PROVEN",
    },
    "WN-HIST-REGIME-SEQUENCER": {
        "covering_working_node_id": "WN-SRC-SWEEPS",
        "coverage_reason": "composition with WN-SRC-BACKTEST, WN-EXP-MONTE-CARLO, WN-EXP-STRESS-TESTS, WN-SRC-REGIME; historical script called research_cli sweep/stress/walkforward/montecarlo",
        "unique_residual_capability": "NONE_PROVEN",
    },
}

OVERRIDE_CHANGE_REASONS: dict[str, str] = {
    "WN-CORE-BACKUP-RECOVERY": "current restore lacks recon/kill-switch/execution-guard preconditions",
    "WN-HIST-INFRA-BACKUP": "historical gzip/caller-dict/retention residuals are not a required current strategic capability; unsafe as recovery owner",
    "WN-HIST-INFRA-MONITORING": "current split observability/alerting/escalation architecture covers the strategic capability; historical unified facade is not a required strategic residual",
    "WN-HIST-REGIME-SEQUENCER": "current backtest/sweeps/Monte-Carlo/stress/regime research composition covers the strategic experiment-orchestration capability",
}

REJECT_POSITIVE_REASON = (
    "superseded by WN-EXECUTION + WN-EXECUTION-PIPELINE; MV2 explicitly "
    "deauthorizes it; parallel pipeline creates harmful authority ambiguity"
)


def research_paths(*, repo_root: Path) -> dict[str, list[str]]:
    research_root = repo_root / "src" / "research"
    grouped: dict[str, list[str]] = defaultdict(list)
    if not research_root.is_dir():
        return {key: [] for key, _ in RES_MATCHERS}
    for path in sorted(research_root.iterdir()):
        if not path.is_dir() or path.name == "__pycache__":
            continue
        name = path.name
        if name.startswith("p") and name[1:].isdigit() and 8 <= int(name[1:]) <= 21:
            continue
        for key, matcher in RES_MATCHERS:
            if matcher(name):
                grouped[key].append(str(path.relative_to(repo_root)))
                break
    return {key: grouped.get(key, []) for key, _ in RES_MATCHERS}


def primary_paths(wn: str, *, repo_root: Path) -> list[str]:
    if wn in STRUCT_PATHS:
        return list(STRUCT_PATHS[wn])
    if wn in HIST_PATHS:
        return list(HIST_PATHS[wn])
    return list(research_paths(repo_root=repo_root).get(wn, []))


def parsed_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in _ROW_TABLE.strip().splitlines():
        index, wn, proposed, final, reason = raw.split("|", 4)
        rows.append(
            {
                "adjudication_index": index,
                "working_node_id": wn,
                "proposed_disposition_owner_label": proposed,
                "final_disposition_owner_label": final,
                "final_reason": reason,
            }
        )
    return rows


def working_node_final_disposition_records(*, repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in parsed_rows():
        wn = row["working_node_id"]
        proposed_owner = row["proposed_disposition_owner_label"]
        final_owner = row["final_disposition_owner_label"]
        proposed_tax = OWNER_TO_TAXONOMY[proposed_owner]
        final_tax = OWNER_TO_TAXONOMY[final_owner]
        accepted = proposed_owner == final_owner
        historical = wn in HIST_PATHS
        record: dict[str, Any] = {
            "working_node_id": wn,
            "adjudication_index": row["adjudication_index"],
            "canonical_record_name": wn,
            "temporal_class": "HISTORICAL_ONLY" if historical else "CURRENT",
            "primary_paths": primary_paths(wn, repo_root=repo_root),
            "current_presence": "CURRENTLY_ABSENT" if historical else "CURRENTLY_PRESENT",
            "proposed_disposition_owner_label": proposed_owner,
            "final_disposition_owner_label": final_owner,
            "proposed_disposition": proposed_tax,
            "final_disposition": final_tax,
            "proposal_accepted": accepted,
            "lifecycle_state": "DISPOSITION_DECIDED",
            "implementation_authorized": False,
            "reintegration_performed": False,
            "runtime_mutation_performed": False,
            "identity_fusion_performed": False,
            "rcn_ledger_mutated": False,
            "safety_critical": wn in EVALUATE_SAFETY_CRITICAL,
            "final_reason": row["final_reason"],
            "positive_reason": row["final_reason"],
        }
        if not accepted:
            record["change_reason"] = OVERRIDE_CHANGE_REASONS[wn]
        if final_tax == "ADAPT_AND_REINTEGRATE":
            record.update(ADAPT_DETAILS[wn])
        if final_tax == "CAPABILITY_ALREADY_COVERED":
            record.update(COVERING[wn])
        if final_tax == "REJECT_FOR_CURRENT_SYSTEM":
            record["positive_reason"] = REJECT_POSITIVE_REASON
            record["rejection_is_not_based_on_age_or_absence"] = True
        records.append(record)
    return records
