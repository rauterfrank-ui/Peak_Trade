"""Static contract for Cybersecurity Visibility repo-static histogram scheduler-boundary crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
touches runtime, scheduler, daemon, adapter, hooks, launchctl, Notion, Market,
broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.ci.cybersecurity_visibility_retained_risk_row_assertions_v0 import (
    assert_retained_r001_r002_r007_pending_or_derived_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

HISTOGRAM_CLASSIFICATION = "scheduler_or_runtime_boundary"
HISTOGRAM_ROW_RX = re.compile(
    rf"^\| `{re.escape(HISTOGRAM_CLASSIFICATION)}` \| (\d+) \| (.+) \|$",
    re.MULTILINE,
)
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)

REQUIRED_SCHEDULER_REUSE_OWNERS: tuple[str, ...] = (
    "tests/ops/test_scheduler_boundary_hard_block_contract_v0.py",
    "tests/ops/test_p67_library_scheduler_boundary_opt_in_v0.py",
)
GROUPING_REFLECTION_GUARD_MODULE = "tests/ci/test_csc_rchain_v1_grouping_reflection_contract_v0.py"
ACCEPTED_SUBGROUP_002_INFRA = "CSC-RCHAIN-v1-002-infra"
ACCEPTED_SUBGROUP_002_INTEGRATION = "CSC-RCHAIN-v1-002-integration"
ACCEPTED_SUBGROUP_002_P101 = "CSC-RCHAIN-v1-002-p101"
ACCEPTED_SUBGROUP_002_P117 = "CSC-RCHAIN-v1-002-p117"
ACCEPTED_SUBGROUP_002_P50 = "CSC-RCHAIN-v1-002-p50"
GOVERNED_REFLECTION_SUBGROUP_003F_A = "CSC-RCHAIN-v1-003f-A"
OPERATOR_ACCEPT_003F_A_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_a_slice_1_v0_20260602T202456Z"
)
NARROWING_BASENAMES_003F_A: tuple[str, ...] = (
    "network_gate.py",
    "shadow_session_scheduler_v1.py",
    "run_shadowloop_pack_v1.py",
)
CANDIDATE_IDS_003F_A: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000264",
    "CSC-LOSSLESS-v1-000265",
    "CSC-LOSSLESS-v1-000266",
    "CSC-LOSSLESS-v1-000267",
    "CSC-LOSSLESS-v1-000268",
    "CSC-LOSSLESS-v1-000293",
    "CSC-LOSSLESS-v1-000294",
    "CSC-LOSSLESS-v1-000308",
    "CSC-LOSSLESS-v1-000309",
    "CSC-LOSSLESS-v1-000310",
    "CSC-LOSSLESS-v1-000311",
    "CSC-LOSSLESS-v1-000312",
    "CSC-LOSSLESS-v1-000313",
    "CSC-LOSSLESS-v1-000314",
    "CSC-LOSSLESS-v1-000315",
    "CSC-LOSSLESS-v1-000316",
    "CSC-LOSSLESS-v1-000326",
    "CSC-LOSSLESS-v1-000327",
    "CSC-LOSSLESS-v1-000328",
    "CSC-LOSSLESS-v1-000329",
)
GOVERNED_REFLECTION_SUBGROUP_003F_C = "CSC-RCHAIN-v1-003f-C"
OPERATOR_ACCEPT_003F_C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_c_slice_1_v0_20260602T203750Z"
)
NARROWING_BASENAMES_003F_C: tuple[str, ...] = (
    "live_session_registry.py",
    "armstrong_cycle_strategy.py",
    "el_karoui_vol_model_strategy.py",
    "engine.py",
)
CANDIDATE_IDS_003F_C: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000262",
    "CSC-LOSSLESS-v1-000263",
    "CSC-LOSSLESS-v1-000285",
    "CSC-LOSSLESS-v1-000286",
    "CSC-LOSSLESS-v1-000334",
    "CSC-LOSSLESS-v1-000335",
    "CSC-LOSSLESS-v1-000336",
    "CSC-LOSSLESS-v1-000337",
    "CSC-LOSSLESS-v1-000338",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003F_C: tuple[str, ...] = (
    "strategy run authorized",
    "backtest run authorized",
    "sweep job started",
    "live session started",
)
GOVERNED_REFLECTION_SUBGROUP_003F_D = "CSC-RCHAIN-v1-003f-D"
OPERATOR_ACCEPT_003F_D_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_d_slice_1_v0_20260602T204916Z"
)
NARROWING_BASENAMES_003F_D: tuple[str, ...] = (
    "PEAK_TRADE_PROJECT_SUMMARY.md",
    "Peak_Trade_setup_notes.md",
    "architecture.md",
    "live_track.py",
    "ops_cockpit.py",
)
CANDIDATE_IDS_003F_D: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000269",
    "CSC-LOSSLESS-v1-000270",
    "CSC-LOSSLESS-v1-000271",
    "CSC-LOSSLESS-v1-000323",
    "CSC-LOSSLESS-v1-000324",
    "CSC-LOSSLESS-v1-000325",
    "CSC-LOSSLESS-v1-000345",
    "CSC-LOSSLESS-v1-000346",
    "CSC-LOSSLESS-v1-000347",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003F_D: tuple[str, ...] = (
    "live track authorized",
    "ops cockpit enabled",
    "webui deploy authorized",
    "docs owner changed",
)
GOVERNED_REFLECTION_SUBGROUP_003C = "CSC-RCHAIN-v1-003c"
OPERATOR_ACCEPT_003C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003c_slice_1_v0_20260602T210125Z"
)
NARROWING_BASENAMES_003C: tuple[str, ...] = (
    "ai_activation_gate_v1.py",
    "live_mode_gate.py",
    "README.md",
    "rules.py",
    "strategy_switch_sanity_check.py",
)
CANDIDATE_IDS_003C: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000287",
    "CSC-LOSSLESS-v1-000288",
    "CSC-LOSSLESS-v1-000289",
    "CSC-LOSSLESS-v1-000290",
    "CSC-LOSSLESS-v1-000291",
    "CSC-LOSSLESS-v1-000292",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003C: tuple[str, ...] = (
    "ai activation authorized",
    "live mode enabled",
    "policy critic enabled",
    "governance policy changed",
    "strategy switch authorized",
)
GOVERNED_REFLECTION_SUBGROUP_003B = "CSC-RCHAIN-v1-003b"
OPERATOR_ACCEPT_003B_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003b_slice_1_v0_20260602T212003Z"
)
NARROWING_BASENAMES_003B: tuple[str, ...] = (
    "live_session.py",
    "orchestrator.py",
    "pipeline.py",
    "__init__.py",
    "registry.py",
)
CANDIDATE_IDS_003B: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000276",
    "CSC-LOSSLESS-v1-000277",
    "CSC-LOSSLESS-v1-000278",
    "CSC-LOSSLESS-v1-000279",
    "CSC-LOSSLESS-v1-000280",
    "CSC-LOSSLESS-v1-000281",
    "CSC-LOSSLESS-v1-000282",
    "CSC-LOSSLESS-v1-000283",
    "CSC-LOSSLESS-v1-000284",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003B: tuple[str, ...] = (
    "live session authorized",
    "orchestrator enabled",
    "pipeline execution enabled",
    "venue activated",
    "execution enabled",
)
GOVERNED_REFLECTION_SUBGROUP_003F_B = "CSC-RCHAIN-v1-003f-B"
OPERATOR_ACCEPT_003F_B_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_b_slice_1_v0_20260602T212936Z"
)
NARROWING_BASENAMES_003F_B: tuple[str, ...] = (
    "kraken_live.py",
    "kraken_testnet.py",
    "markers_v0.py",
    "observation_harness_v0.py",
    "base.py",
)
CANDIDATE_IDS_003F_B: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000272",
    "CSC-LOSSLESS-v1-000273",
    "CSC-LOSSLESS-v1-000274",
    "CSC-LOSSLESS-v1-000275",
    "CSC-LOSSLESS-v1-000330",
    "CSC-LOSSLESS-v1-000331",
    "CSC-LOSSLESS-v1-000332",
    "CSC-LOSSLESS-v1-000333",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003F_B: tuple[str, ...] = (
    "kraken live authorized",
    "testnet trading enabled",
    "shadow proof executed",
    "exchange api authorized",
    "provider activated",
    "real order placed",
)
GOVERNED_REFLECTION_SUBGROUP_003D = "CSC-RCHAIN-v1-003d"
OPERATOR_ACCEPT_003D_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003d_slice_1_v0_20260602T214239Z"
)
NARROWING_BASENAMES_003D: tuple[str, ...] = (
    "base.py",
    "exchange.py",
    "paper.py",
    "shadow.py",
    "testnet_executor.py",
)
CANDIDATE_IDS_003D: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000317",
    "CSC-LOSSLESS-v1-000318",
    "CSC-LOSSLESS-v1-000319",
    "CSC-LOSSLESS-v1-000320",
    "CSC-LOSSLESS-v1-000321",
    "CSC-LOSSLESS-v1-000322",
)
FORBIDDEN_AUTHORIZATION_PHRASES_003D: tuple[str, ...] = (
    "order placement authorized",
    "routing enabled",
    "session armed",
    "paper order sent",
    "shadow order sent",
    "testnet order enabled",
)

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "scheduler start authorized",
    "runtime start authorized",
    "testnet approved",
    "live approved",
    "operator bypass",
    "ready_for_start=true",
    "preflight_blocked_lifted=true",
)


def _ci_audit_text() -> str:
    assert CI_AUDIT_KNOWN_ISSUES.is_file()
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _histogram_section(text: str) -> str:
    start = text.find("**Interim classification histogram")
    assert start != -1, "histogram section missing"
    end = text.find("**Lossless recovery still required")
    assert end != -1, "histogram section end missing"
    return text[start:end]


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def _csc_rchain_accepted_groups_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1 accepted groups reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-A governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003f_a_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-A governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-C governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003f_c_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-C governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-D governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003f_d_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-D governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003c governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003c_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003c governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003b governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003b_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003b governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-B governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003f_b_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-B governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003d governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003d_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003d governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


GOVERNED_REFLECTION_SUBGROUP_005C = "CSC-RCHAIN-v1-005c"
OPERATOR_ACCEPT_005C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice1_v0_20260602T220533Z"
)
NARROWING_BASENAMES_005C: tuple[str, ...] = (
    "run_backtest.py",
    "run_donchian_realistic.py",
    "run_ma_realistic.py",
    "run_momentum_realistic.py",
    "run_rsi_realistic.py",
)
CANDIDATE_IDS_005C: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000238",
    "CSC-LOSSLESS-v1-000239",
    "CSC-LOSSLESS-v1-000240",
    "CSC-LOSSLESS-v1-000242",
    "CSC-LOSSLESS-v1-000243",
    "CSC-LOSSLESS-v1-000247",
    "CSC-LOSSLESS-v1-000248",
    "CSC-LOSSLESS-v1-000252",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "live trading enabled",
    "testnet session authorized",
    "shadow execution authorized",
    "backtest execute authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-2)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_2 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice2_v0_20260602T221918Z"
)
NARROWING_BASENAMES_005C_SLICE2: tuple[str, ...] = (
    "health_dashboard.py",
    "run_full_portfolio.py",
    "run_offline_realtime_ma_crossover.py",
    "run_strategy_from_config.py",
    "run_sweep_strategy.py",
)
CANDIDATE_IDS_005C_SLICE2: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000250",
    "CSC-LOSSLESS-v1-000251",
    "CSC-LOSSLESS-v1-000159",
    "CSC-LOSSLESS-v1-000245",
    "CSC-LOSSLESS-v1-000249",
    "CSC-LOSSLESS-v1-000255",
    "CSC-LOSSLESS-v1-000256",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE2: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "live trading enabled",
    "testnet session authorized",
    "shadow execution authorized",
    "dashboard server start authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_slice2_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-2)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-3 Testnet)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_3_TESTNET = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice3_testnet_v0_20260602T223444Z"
)
NARROWING_BASENAMES_005C_SLICE3_TESTNET: tuple[str, ...] = (
    "shadow_testnet_readiness_scorecard.py",
    "orchestrate_testnet_runs.py",
    "run_testnet_session.py",
    "smoke_test_testnet_stack.py",
    "testnet_orchestrator_cli.py",
)
CANDIDATE_IDS_005C_SLICE3_TESTNET: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000158",
    "CSC-LOSSLESS-v1-000236",
    "CSC-LOSSLESS-v1-000257",
    "CSC-LOSSLESS-v1-000258",
    "CSC-LOSSLESS-v1-000259",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE3_TESTNET: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "testnet execution authorized",
    "testnet session authorized",
    "orchestrator dispatch authorized",
    "smoke test execution authorized",
    "readiness clearance granted",
    "shadow runtime authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_slice3_testnet_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-3 Testnet)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-4 Live-Named A)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_4_LIVE_NAMED_A = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice4_live_named_a_v0_20260602T224627Z"
)
NARROWING_BASENAMES_005C_SLICE4_LIVE_NAMED_A: tuple[str, ...] = (
    "check_live_readiness.py",
    "check_docs_no_live_enable_patterns.sh",
    "live_pilot_scorecard.py",
    "live_alerts_cli.py",
    "live_monitor_cli.py",
)
CANDIDATE_IDS_005C_SLICE4_LIVE_NAMED_A: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000155",
    "CSC-LOSSLESS-v1-000156",
    "CSC-LOSSLESS-v1-000157",
    "CSC-LOSSLESS-v1-000160",
    "CSC-LOSSLESS-v1-000161",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE4_LIVE_NAMED_A: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "live execution authorized",
    "live readiness clearance",
    "live arming authorized",
    "pilot clearance granted",
    "alert dispatch authorized",
    "monitor serve authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_slice4_live_named_a_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-4 Live-Named A)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-5 Live-Named B)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_5_LIVE_NAMED_B = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice5_live_named_b_v0_20260602T225455Z"
)
NARROWING_BASENAMES_005C_SLICE5_LIVE_NAMED_B: tuple[str, ...] = (
    "live_operator_status.py",
    "live_ops.py",
    "live_web_server.py",
    "report_live_sessions.py",
    "run_live_beta_drill.py",
)
CANDIDATE_IDS_005C_SLICE5_LIVE_NAMED_B: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000162",
    "CSC-LOSSLESS-v1-000163",
    "CSC-LOSSLESS-v1-000164",
    "CSC-LOSSLESS-v1-000237",
    "CSC-LOSSLESS-v1-000246",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE5_LIVE_NAMED_B: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "live execution authorized",
    "live ops approved",
    "operator status cleared",
    "web server start authorized",
    "beta drill authorized",
    "drill execution authorized",
    "live drill arming approved",
    "live session report clearance",
    "cli invocation approved",
)


def _csc_rchain_005c_slice5_live_named_b_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-5 Live-Named B)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-6 AIOps-Shadow)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_6_AIOPS_SHADOW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice6_aiops_shadow_v0_20260602T230331Z"
)
NARROWING_BASENAMES_005C_SLICE6_AIOPS_SHADOW: tuple[str, ...] = (
    "run_paper_trading_session.py",
    "run_prj_features_smoke.py",
    "run_shadow_session.py",
    "run_shadow_execution.py",
)
CANDIDATE_IDS_005C_SLICE6_AIOPS_SHADOW: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000152",
    "CSC-LOSSLESS-v1-000153",
    "CSC-LOSSLESS-v1-000154",
    "CSC-LOSSLESS-v1-000254",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE6_AIOPS_SHADOW: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "shadow execution authorized",
    "shadow runtime authorized",
    "shadow runtime start authorized",
    "aiops approved",
    "autonomy enabled",
    "decision authority granted",
    "paper trading session cleared",
    "execution authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_slice6_aiops_shadow_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-6 AIOps-Shadow)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-7 Execution-Workflow)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_005C_SLICE_7_EXECUTION_WORKFLOW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice7_execution_workflow_v0_20260602T231105Z"
)
NARROWING_BASENAMES_005C_SLICE7_EXECUTION_WORKFLOW: tuple[str, ...] = (
    "run_execution_session.py",
    "run_autonomous_workflow.py",
)
CANDIDATE_IDS_005C_SLICE7_EXECUTION_WORKFLOW: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000244",
    "CSC-LOSSLESS-v1-000241",
)
FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE7_EXECUTION_WORKFLOW: tuple[str, ...] = (
    "script execution authorized",
    "scheduler start authorized",
    "execution session authorized",
    "execution session start authorized",
    "execution started",
    "workflow dispatch approved",
    "workflow dispatch authorized",
    "autonomous workflow enabled",
    "autonomous authority granted",
    "execution authorized",
    "cli invocation approved",
)


def _csc_rchain_005c_slice7_execution_workflow_guard_block(text: str) -> str:
    start = text.index(
        "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-7 Execution-Workflow)"
    )
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def test_cybersecurity_visibility_repo_static_histogram_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_V0=true"
        in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "24"
    notes_cell = match.group(2)
    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert f"Reuse `{owner_path}`" in notes_cell
        assert (REPO_ROOT / owner_path).is_file(), f"missing reuse owner module: {owner_path}"

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert owner_path in reuse_paths

    assert_retained_r001_r002_r007_pending_or_derived_evidence(_risk_table_rows(text))

    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert owner_path in text

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text

    guard_block = _csc_rchain_accepted_groups_guard_block(text)
    assert ACCEPTED_SUBGROUP_002_INFRA in guard_block
    assert ACCEPTED_SUBGROUP_002_INTEGRATION in guard_block
    assert ACCEPTED_SUBGROUP_002_P101 in guard_block
    assert ACCEPTED_SUBGROUP_002_P117 in guard_block
    assert ACCEPTED_SUBGROUP_002_P50 in guard_block
    assert GROUPING_REFLECTION_GUARD_MODULE in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT=23" in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT=258" in guard_block
    assert "CSC_RCHAIN_V1_HYBRID_AUTHORITY_POINTER_ACTIVE=true" in guard_block
    assert (
        "csc_rchain_v1_external_full_authority_bundle_draft_and_wiring_check_readonly_v0_20260601T104257Z"
        in guard_block
    )
    assert "CSC_RCHAIN_V1_002_P63_ACCEPTED=false" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE=true" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT=238" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_SUBSET_OF_PARK=true" in guard_block
    assert (
        "csc_rchain_v1_post_ops_closeout_contracts_batch_authority_refresh_and_next_batch_ranking_readonly_v0_20260601T133828Z"
        in guard_block
    )
    assert "reviewed-prepared-only" in guard_block.lower()
    assert (
        "does **not** authorize observability/logging/decision-context/execution/runtime/scheduler/shadow/online-readiness"
        in guard_block
    )
    assert "CSC-RCHAIN-v1-002-infra" in guard_block
    assert "parent **002** remains PARK" in guard_block
    assert "network escalation is authorized" not in collapsed
    assert "network enablement" not in collapsed
    assert "live enablement (`LIVE=1` appears only as refusal-test context)" in text
    assert "kill-switch bypass" in text
    assert "p101 stop-playbook semantics changes" in text
    assert "exec-evidence collection enablement" in text
    assert "launchctl execution enablement" in text
    assert "p117 ops-loop semantics changes" in text
    assert "AI model enablement authorization" in text
    assert "AI model policy semantics changes" in text
    assert "PEAKTRADE_STAGE=testnet` enablement" in text

    accepted_line = next(
        line
        for line in guard_block.splitlines()
        if line.startswith("CSC_RCHAIN_V1_ACCEPTED_GROUPS=")
    )
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_C not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_D not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003C not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003B not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_B not in accepted_line


def test_csc_rchain_v1_003f_a_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003f_a_guard_block(text)

    assert "CSC_RCHAIN_V1_003F_A_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_A_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003F_A_CANDIDATE_COUNT=20" in block
    assert "CSC_RCHAIN_V1_003F_A_EXTERNAL_ACCEPT_READY_COUNT=17" in block
    assert "CSC_RCHAIN_V1_003F_A_NARROWING_REQUIRED_COUNT=3" in block
    assert "CSC_RCHAIN_V1_003F_A_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-A-SLICE-1" in block
    assert "NO_AWS_NO_NETWORK_OPS=true" in block
    assert "NO_SHADOW_SCHEDULER_EXECUTION=true" in block
    assert "NO_SHADOWLOOP_START=true" in block
    assert "NETWORK_GATE_VISIBILITY_ONLY=true" in block
    assert OPERATOR_ACCEPT_003F_A_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block

    for basename in NARROWING_BASENAMES_003F_A:
        assert basename in block
    assert "CSC-LOSSLESS-v1-000264" in block
    assert "000293`–`000294" in block
    assert "000312`–`000316" in block
    assert "000326`–`000329" in block
    assert len(CANDIDATE_IDS_003F_A) == 20

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "scheduler start authorized" not in collapsed
    assert "shadowloop start authorized" not in collapsed


def test_csc_rchain_v1_003f_c_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003f_c_guard_block(text)

    assert "CSC_RCHAIN_V1_003F_C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003F_C_CANDIDATE_COUNT=9" in block
    assert "CSC_RCHAIN_V1_003F_C_EXTERNAL_ACCEPT_READY_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003F_C_NARROWING_REQUIRED_COUNT=4" in block
    assert "CSC_RCHAIN_V1_003F_C_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-C-SLICE-1" in block
    assert "NO_LIVE_SESSION_RUN=true" in block
    assert "NO_STRATEGY_EXECUTION=true" in block
    assert "NO_SWEEP_JOB_EXECUTION=true" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003F_C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block

    for basename in NARROWING_BASENAMES_003F_C:
        assert basename in block
    assert "CSC-LOSSLESS-v1-000262" in block
    assert "000334`–`000335" in block
    assert "000337`–`000338" in block
    assert len(CANDIDATE_IDS_003F_C) == 9

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003F_C:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003F_A_GOVERNED_REFLECTION_SLICE1_V0=true" in text
    assert "CSC_RCHAIN_V1_003F_C_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_003f_d_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003f_d_guard_block(text)

    assert "CSC_RCHAIN_V1_003F_D_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_D_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003F_D_CANDIDATE_COUNT=9" in block
    assert "CSC_RCHAIN_V1_003F_D_EXTERNAL_ACCEPT_READY_COUNT=4" in block
    assert "CSC_RCHAIN_V1_003F_D_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003F_D_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-D-SLICE-1" in block
    assert "DOCS_PATH_ENCODING_REQUIRED=true" in block
    assert "NO_LIVE_TRACK_AUTHORITY=true" in block
    assert "NO_OPS_COCKPIT_ENABLEMENT=true" in block
    assert "NO_MARKET_AIRPORT_TOUCH=true" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003F_D_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_D in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block

    for basename in NARROWING_BASENAMES_003F_D:
        assert basename in block
    assert "src&#47;docs&#47;" in block
    assert "CSC-LOSSLESS-v1-000269" in block
    assert "000323`–`000325" in block
    assert "000345`–`000347" in block
    assert len(CANDIDATE_IDS_003F_D) == 9

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003F_D:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003F_A_GOVERNED_REFLECTION_SLICE1_V0=true" in text
    assert "CSC_RCHAIN_V1_003F_C_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_003c_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003c_guard_block(text)

    assert "CSC_RCHAIN_V1_003C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003C_CANDIDATE_COUNT=6" in block
    assert "CSC_RCHAIN_V1_003C_EXTERNAL_ACCEPT_READY_COUNT=1" in block
    assert "CSC_RCHAIN_V1_003C_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003C_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003C-SLICE-1" in block
    assert "NO_AI_ACTIVATION_AUTHORITY=true" in block
    assert "NO_LIVE_MODE_ENABLEMENT=true" in block
    assert "NO_POLICY_CRITIC_ENABLEMENT=true" in block
    assert "NO_STRATEGY_SWITCH_AUTHORITY=true" in block
    assert "GOVERNANCE_BEHAVIOR_CHANGED=false" in block
    assert "AI_AUTHORITY_CHANGED=false" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003B_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003F_B_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "tests&#47;governance" in block
    assert "governance" in block.lower()

    for basename in NARROWING_BASENAMES_003C:
        assert basename in block
    assert "CSC-LOSSLESS-v1-000287" in block
    assert "000290`–`000291" in block
    assert len(CANDIDATE_IDS_003C) == 6

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003C:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003F_D_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_003b_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003b_guard_block(text)

    assert "CSC_RCHAIN_V1_003B_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003B_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003B_CANDIDATE_COUNT=9" in block
    assert "CSC_RCHAIN_V1_003B_EXTERNAL_ACCEPT_READY_COUNT=1" in block
    assert "CSC_RCHAIN_V1_003B_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003B_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003B-SLICE-1" in block
    assert "NO_LIVE_SESSION_AUTHORITY=true" in block
    assert "NO_ORCHESTRATOR_ENABLEMENT=true" in block
    assert "NO_PIPELINE_ENABLEMENT=true" in block
    assert "NO_VENUE_ADAPTER_AUTHORITY=true" in block
    assert "EXECUTION_VISIBILITY_ONLY=true" in block
    assert "EXECUTION_AUTHORITY_CHANGED=false" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003F_B_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003B_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003B in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "execution" in block.lower()

    for basename in NARROWING_BASENAMES_003B:
        assert basename in block
    assert len(CANDIDATE_IDS_003B) == 9
    assert "CSC-LOSSLESS-v1-000276" in block
    assert "000277`–`000284" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003B:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003C_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_003f_b_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003f_b_guard_block(text)

    assert "CSC_RCHAIN_V1_003F_B_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_B_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003F_B_CANDIDATE_COUNT=8" in block
    assert "CSC_RCHAIN_V1_003F_B_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_003F_B_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003F_B_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-B-SLICE-1" in block
    assert "NO_EXCHANGE_LIVE_AUTHORITY=true" in block
    assert "NO_EXCHANGE_TESTNET_ENABLEMENT=true" in block
    assert "NO_SHADOW_PROOF_EXECUTION=true" in block
    assert "EXCHANGE_VISIBILITY_ONLY=true" in block
    assert "SHADOW_NO_ORDER_PROOF_VISIBILITY_ONLY=true" in block
    assert "EXCHANGE_BEHAVIOR_CHANGED=false" in block
    assert "SHADOW_BEHAVIOR_CHANGED=false" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003B_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003D_ORDERS_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003F_B_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_B in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "exchange" in block.lower()
    assert "shadow-no-order-proof" in block.lower() or "shadow" in block.lower()

    for basename in NARROWING_BASENAMES_003F_B:
        assert basename in block
    assert len(CANDIDATE_IDS_003F_B) == 8
    assert "CSC-LOSSLESS-v1-000272" in block
    assert "000272`–`000275" in block
    assert "000330`–`000333" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003F_B:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003B_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_003d_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003d_guard_block(text)

    assert "CSC_RCHAIN_V1_003D_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003D_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003D_CANDIDATE_COUNT=6" in block
    assert "CSC_RCHAIN_V1_003D_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_003D_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_003D_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003D-SLICE-1" in block
    assert "NO_ORDER_PLACEMENT_AUTHORITY=true" in block
    assert "NO_ROUTING_AUTHORITY=true" in block
    assert "NO_SESSION_AUTHORITY=true" in block
    assert "NO_PAPER_ORDER_AUTHORITY=true" in block
    assert "NO_SHADOW_ORDER_SEND=true" in block
    assert "NO_TESTNET_ORDER_ENABLEMENT=true" in block
    assert "ORDERS_VISIBILITY_ONLY=true" in block
    assert "ROUTING_NO_AUTHORITY_VISIBILITY_ONLY=true" in block
    assert "SESSION_NO_AUTHORITY_VISIBILITY_ONLY=true" in block
    assert "ORDERS_BEHAVIOR_CHANGED=false" in block
    assert "ROUTING_BEHAVIOR_CHANGED=false" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003B_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_B_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_003D_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003D in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "orders" in block.lower()
    assert "routing-no-authority" in block.lower() or "routing" in block.lower()

    for basename in NARROWING_BASENAMES_003D:
        assert basename in block
    assert len(CANDIDATE_IDS_003D) == 6
    assert "CSC-LOSSLESS-v1-000317" in block
    assert "000318`–`000322" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_003D:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003F_B_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_CANDIDATE_COUNT=8" in block
    assert "CSC_RCHAIN_V1_005C_EXTERNAL_ACCEPT_READY_COUNT=3" in block
    assert "CSC_RCHAIN_V1_005C_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-1" in block
    assert "NO_SCRIPT_EXECUTION_AUTHORITY=true" in block
    assert "NO_SCHEDULER_EXECUTION_AUTHORITY=true" in block
    assert "RESEARCH_BACKTEST_OFFLINE_CLI_VISIBILITY_ONLY=true" in block
    assert "SCRIPT_BEHAVIOR_CHANGED=false" in block
    assert "CSC_PARENT005A_EXCLUDED=true" in block
    assert "CSC_PARENT005B_EXCLUDED=true" in block
    assert "RUN_SCHEDULER_000253_EXCLUDED_FROM_SLICE1=true" in block
    assert "CSC_RCHAIN_V1_003D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003A_LIVE_EXCLUDED=true" in block
    assert "CSC_RCHAIN_V1_003E_MASTER_V2_EXCLUDED=true" in block
    assert OPERATOR_ACCEPT_005C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "research" in block.lower()
    assert "backtest" in block.lower()

    for basename in NARROWING_BASENAMES_005C:
        assert basename in block
    assert len(CANDIDATE_IDS_005C) == 8
    assert "CSC-LOSSLESS-v1-000238" in block
    assert "000238`–`000240" in block
    assert "000242`–`000243" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_003D_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice2_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice2_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE2_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_CANDIDATE_COUNT=7" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_EXTERNAL_ACCEPT_READY_COUNT=2" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-2" in block
    assert "OFFLINE_REMAINDER_CLI_VISIBILITY_ONLY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_2 in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "offline remainder" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE2:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE2) == 7
    assert "CSC-LOSSLESS-v1-000250" in block
    assert "000250`–`000251" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE2:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE1_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice3_testnet_scheduler_boundary_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice3_testnet_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE3_TESTNET_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_CANDIDATE_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_DUAL_TESTNET_SHADOW_MARKER_COUNT=1" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-3-TESTNET" in block
    assert "TESTNET_NAMED_CLI_VISIBILITY_ONLY=true" in block
    assert "NO_TESTNET_EXECUTION_AUTHORITY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_3_TESTNET in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "testnet-named" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE3_TESTNET:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE3_TESTNET) == 5
    assert "CSC-LOSSLESS-v1-000158" in block
    assert "000236" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE3_TESTNET:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE2_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice4_live_named_a_scheduler_boundary_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice4_live_named_a_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE4_LIVE_NAMED_A_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_CANDIDATE_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-4-LIVE-NAMED-A" in block
    assert "LIVE_NAMED_CLI_VISIBILITY_ONLY=true" in block
    assert "NO_LIVE_EXECUTION_AUTHORITY=true" in block
    assert "NO_LIVE_READINESS_CLEARANCE_AUTHORITY=true" in block
    assert "NO_LIVE_ARMING_AUTHORITY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_4_LIVE_NAMED_A in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "live-named" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE4_LIVE_NAMED_A:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE4_LIVE_NAMED_A) == 5
    assert "CSC-LOSSLESS-v1-000155" in block
    assert "000160" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE4_LIVE_NAMED_A:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE3_TESTNET_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice5_live_named_b_scheduler_boundary_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice5_live_named_b_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE5_LIVE_NAMED_B_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE5_CANDIDATE_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_SLICE5_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_005C_SLICE5_NARROWING_REQUIRED_COUNT=5" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-5-LIVE-NAMED-B" in block
    assert "LIVE_NAMED_B_CLI_VISIBILITY_ONLY=true" in block
    assert "NO_LIVE_EXECUTION_AUTHORITY=true" in block
    assert "NO_LIVE_OPS_AUTHORITY=true" in block
    assert "NO_LIVE_WEB_SERVE_AUTHORITY=true" in block
    assert "NO_LIVE_DRILL_EXECUTION_AUTHORITY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_5_LIVE_NAMED_B in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "live-named b" in block.lower() or "live-named" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE5_LIVE_NAMED_B:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE5_LIVE_NAMED_B) == 5
    assert "CSC-LOSSLESS-v1-000162" in block
    assert "000246" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE5_LIVE_NAMED_B:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE4_LIVE_NAMED_A_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice6_aiops_shadow_scheduler_boundary_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice6_aiops_shadow_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE6_AIOPS_SHADOW_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE6_CANDIDATE_COUNT=4" in block
    assert "CSC_RCHAIN_V1_005C_SLICE6_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_005C_SLICE6_NARROWING_REQUIRED_COUNT=4" in block
    assert "CSC_RCHAIN_V1_005C_DUAL_MARKER_CANDIDATE_COUNT=2" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-6-AIOPS-SHADOW" in block
    assert "AIOPS_SHADOW_CLI_VISIBILITY_ONLY=true" in block
    assert "NO_SHADOW_EXECUTION_AUTHORITY=true" in block
    assert "NO_SHADOW_RUNTIME_START_AUTHORITY=true" in block
    assert "NO_AIOPS_AUTHORITY=true" in block
    assert "NO_AUTONOMY_AUTHORITY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE5_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_6_AIOPS_SHADOW in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "aiops" in block.lower()
    assert "shadow" in block.lower()
    assert "dual" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE6_AIOPS_SHADOW:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE6_AIOPS_SHADOW) == 4
    assert "CSC-LOSSLESS-v1-000152" in block
    assert "000254" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE6_AIOPS_SHADOW:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE5_LIVE_NAMED_B_V0=true" in text


def test_csc_rchain_v1_005c_governed_reflection_slice7_execution_workflow_scheduler_boundary_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_005c_slice7_execution_workflow_guard_block(text)

    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE7_EXECUTION_WORKFLOW_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE7_CANDIDATE_COUNT=2" in block
    assert "CSC_RCHAIN_V1_005C_SLICE7_EXTERNAL_ACCEPT_READY_COUNT=0" in block
    assert "CSC_RCHAIN_V1_005C_SLICE7_NARROWING_REQUIRED_COUNT=2" in block
    assert "CSC_RCHAIN_V1_005C_FINAL_SCRIPT_SLICE=true" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-7-EXECUTION-WORKFLOW" in block
    assert "EXECUTION_WORKFLOW_CLI_VISIBILITY_ONLY=true" in block
    assert "NO_EXECUTION_SESSION_START_AUTHORITY=true" in block
    assert "NO_WORKFLOW_DISPATCH_AUTHORITY=true" in block
    assert "NO_AUTONOMOUS_AUTHORITY=true" in block
    assert "NO_EXECUTION_AUTHORITY=true" in block
    assert "NO_WORKFLOW_AUTHORITY=true" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE4_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE5_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE6_REOPENED=false" in block
    assert OPERATOR_ACCEPT_005C_SLICE_7_EXECUTION_WORKFLOW in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "execution" in block.lower()
    assert "workflow" in block.lower()

    for basename in NARROWING_BASENAMES_005C_SLICE7_EXECUTION_WORKFLOW:
        assert basename in block
    assert len(CANDIDATE_IDS_005C_SLICE7_EXECUTION_WORKFLOW) == 2
    assert "CSC-LOSSLESS-v1-000244" in block
    assert "000241" in block
    assert "36/37" in block

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed
    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES_005C_SLICE7_EXECUTION_WORKFLOW:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE6_AIOPS_SHADOW_V0=true" in text


def test_cybersecurity_visibility_repo_static_histogram_scheduler_boundary_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert (
        "Cybersecurity Visibility repo-static histogram scheduler-boundary owner crosslink v0"
        in truth_map
    )
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_V0=true"
        in truth_map
        or "scheduler-boundary owner crosslink" in collapsed
    )
    assert "non-authorizing" in collapsed
    assert "input_jsonl_provided=false" in collapsed or "INPUT_JSONL_PROVIDED=false" in truth_map
