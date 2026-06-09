"""Docs/env boundary for Real Futures Market Data Source Contract v1 (U5 charter)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MARKET_DATA_SOURCE_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md"
)
REAL_SOURCE_CHARTER_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md"
)


def test_real_futures_market_data_source_contract_doc_exists_and_markers() -> None:
    assert MARKET_DATA_SOURCE_DOC.is_file()
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_WIRING_AUTHORIZED=false" in doc
    assert "PROVIDER_PROBE_AUTHORIZED=false" in doc
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
    assert "Evidence != Approval/Lift/Live" in doc
    assert "FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false" in doc
    assert "SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true" in doc
    assert "kraken_futures_public_market_data_only" in doc
    assert "/derivatives/api/v3/instruments" in doc
    assert "/derivatives/api/v3/tickers" in doc
    assert "api.kraken.com" in doc
    assert "market_ranking_funnel_readmodel.v0" in doc
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc


def test_real_source_charter_links_market_data_source_contract() -> None:
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md" in doc


def test_market_data_source_contract_forbids_dummy_substitution() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    forbidden = (
        "market_surface_dummy",
        "get_market_dummy",
        "btc_usd_dummy_default",
        "fixture_only=true",
    )
    for marker in forbidden:
        assert marker in doc


def test_market_data_source_contract_no_runtime_wiring_claims() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "PROVIDER_POLLING_DAEMON_AUTHORIZED=false" in doc
    assert "DASHBOARD_PROVIDER_WIRING_AUTHORIZED=false" in doc
    assert "no daemon" in doc.lower() or "no daemon" in doc
    assert "scheduler" in doc.lower()


def test_market_data_source_contract_links_u5b_probe_module() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "probe_kraken_futures_public_market_data_v1.py" in doc
    assert "CONFIRM_VIEW_ONLY_PUBLIC_MARKET_DATA_PROBE_V1" in doc
    assert "test_probe_kraken_futures_public_market_data_v1.py" in doc


GOVERNED_SNAPSHOT_TEMPLATE_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md"
)


def test_u5c_transform_contract_section_exists_and_markers() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "## 12. U5C Transform Contract to U2c Governed Snapshot Candidate" in doc
    assert "TRANSFORM_EXECUTED=false" in doc
    assert "U2C_SNAPSHOT_DIRECTLY_INTAKE_READY=false" in doc
    assert "GOVERNED_SNAPSHOT_ACCEPTED=false" in doc
    assert "SNAPSHOT_INTAKE_EXECUTED=false" in doc
    assert "LOADER_RUN_EXECUTED=false" in doc
    assert "READMODEL_WRITE_EXECUTED=false" in doc
    assert "DASHBOARD_WIRING_EXECUTED=false" in doc
    assert "kraken_futures_public_market_data_probe_report.v1.json" in doc
    assert "kraken_futures_instruments_raw.v1.json" in doc
    assert "kraken_futures_tickers_raw.v1.json" in doc
    assert "futures_producer_packet_governed.v1.json" in doc
    assert "FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md" in doc


def test_u5b_probe_report_alone_not_u2c_intake_ready() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "U5b probe report alone is not U2c intake-ready" in doc
    assert "U2C_SNAPSHOT_DIRECTLY_INTAKE_READY=false" in doc
    assert "top20_candidate_preview" in doc
    assert "insufficient" in doc.lower()


def test_u5c_requires_raw_instruments_tickers_artifacts() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "Raw instruments payload artifact" in doc
    assert "Raw tickers payload artifact" in doc
    assert "kraken_futures_instruments_raw.v1.json" in doc
    assert "kraken_futures_tickers_raw.v1.json" in doc
    assert "report-only direct U2c intake" in doc


def test_u5c_alphabetical_top20_preview_not_governed_top20() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "alphabetical preview only" in doc
    assert "top20_ranking_candidate" in doc
    assert "must **never** become governed" in doc


def test_u5c_forbids_btc_usd_substitution() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "BTC&#47;USD" in doc
    assert "INELIGIBLE_SPOT_SYMBOL" in doc
    assert "no BTC&#47;USD substitution" in doc


def test_u5c_forbids_dummy_ranking() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "Dummy ranking rows" in doc or "dummy ranking" in doc.lower()
    assert "btc_usd_dummy_default" in doc
    assert "Missing Truth" in doc


def test_u5c_no_selected_tradable_future() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "no_selected_tradable_future" in doc
    assert "Selected tradable future without operator acceptance" in doc
    assert "no strategy score" in doc.lower() or "Strategy score" in doc


def test_u5c_readmodel_dashboard_gates_separate() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "Readmodel write before U2b loader validation PASS" in doc
    assert "Dashboard display from raw U5b evidence" in doc
    assert "Readmodel Write GO" in doc
    assert "Dashboard Wiring GO" in doc


def test_u5c_trading_logic_no_touch_markers() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "src&#47;execution&#47;**" in doc
    assert "src&#47;risk&#47;**" in doc
    assert "src&#47;governance&#47;**" in doc
    assert "Master V2" in doc
    assert "Double Play" in doc
    assert "Risk-KillSwitch" in doc
    assert "Execution-Live-Gates" in doc
    assert "TRANSFORM_EXECUTED=false" in doc


def test_u5c_reuse_no_parallel_owner_markers() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "no parallel surfaces" in doc.lower() or "no parallel SSOT" in doc
    assert "not** a second snapshot SSOT" in doc
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc
    assert "UNIVERSE_SELECTION_READMODEL_V1.md" in doc
    assert "futures_producer_packet_real_metadata_source_v1.py" in doc
    template = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md" in template
    assert "U5c transform contract" in template


def test_governed_snapshot_template_links_u5c_transform_contract() -> None:
    doc = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    assert "U5c transform contract" in doc
    assert "not** direct report-only intake" in doc


def test_u5d_offline_transform_script_referenced_in_contract() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "transform_kraken_futures_raw_to_u2c_candidate_v1.py" in doc
    assert "CONFIRM_U5D_OFFLINE_TRANSFORM_VALIDATION_V1" in doc or "U5d" in doc
    assert "test_transform_kraken_futures_raw_to_u2c_candidate_v1.py" in doc
    assert "u5d_u2c_candidate_validation_v1" in doc or "U5d offline" in doc


def test_real_futures_contract_documents_public_view_min_notional_permanent_block() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "### 12.12 Kraken Public View — min_notional Permanent Block" in doc
    markers = (
        "KRAKEN_PUBLIC_MIN_NOTIONAL_PROVIDER_FIELD_PRESENT=false",
        "PROVIDER_AUTHENTIC_MIN_NOTIONAL_SOURCE_FOUND=false",
        "OFFLINE_MIN_NOTIONAL_ENRICHMENT_FEASIBLE=false",
        "STRICT_UPSTREAM_REMAINS_BLOCKED_FOR_PUBLIC_VIEW=true",
        "MISSING_PROVIDER_METADATA_NOT_IN_PUBLIC_VIEW=min_notional",
        "IMPACT_MID_SIZE_MAPS_TO_MIN_QTY_NOT_MIN_NOTIONAL=true",
        "PRICE_QTY_MIN_NOTIONAL_HEURISTIC_FORBIDDEN=true",
        "CVC_DIAGNOSTIC_PATH_NON_TRUTH_ONLY=true",
    )
    for marker in markers:
        assert marker in doc
    assert "impactMidSize" in doc
    assert "kraken_instruments.impactMidSize" in doc
    assert "bundle_to_upstream_input" in doc
    forbidden = (
        "Dummy `min_notional`",
        "impactMidSize` relabelled as `min_notional`",
        "instrument.complete` force",
    )
    for phrase in forbidden:
        assert phrase in doc
    assert "observability_truth_allowed=false" in doc
