"""Env/schema boundary for Workflow Dashboard V1."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_workflow_dashboard_env_constants_in_runtime_module() -> None:
    from src.webui.workflow_dashboard_runtime_v1 import ENV_ARCHIVE_ROOT, ENV_ENABLED

    assert ENV_ENABLED == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED"
    assert ENV_ARCHIVE_ROOT == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"


def test_observability_hub_doc_documents_workflow_dashboard() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED" in doc
    assert "workflow_dashboard_readmodel.v1" in doc
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in doc


def test_universe_selection_contract_doc_exists() -> None:
    doc_path = PROJECT_ROOT / "docs/webui/observability/UNIVERSE_SELECTION_READMODEL_V1.md"
    assert doc_path.is_file()
    doc = doc_path.read_text(encoding="utf-8")
    assert "schema_name" in doc
    assert "universe_selection_readmodel.v1" in doc
    assert "readmodels&#47;universe_selection_readmodel.v1.json" in doc
    assert "BTC/USD" in doc
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in doc


def test_observability_hub_links_universe_selection_contract() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "UNIVERSE_SELECTION_READMODEL_V1.md" in doc
    assert "universe_selection_readmodel.v1" in doc


REAL_SOURCE_CHARTER_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md"
)
GOVERNED_SNAPSHOT_TEMPLATE_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md"
)
UNIVERSE_SELECTION_DOC = (
    PROJECT_ROOT / "docs" / "webui" / "observability" / "UNIVERSE_SELECTION_READMODEL_V1.md"
)


def test_futures_universe_real_source_charter_doc_exists_and_markers() -> None:
    assert REAL_SOURCE_CHARTER_DOC.is_file()
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
    assert "U2B_IMPLEMENTABLE_IMMEDIATELY=false" in doc
    assert "U2B_BLOCKED" in doc
    assert "Evidence != Approval/Lift/Live" in doc
    assert "market_ranking_funnel_readmodel.v0" in doc
    assert "FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false" in doc
    assert "MANIFEST_VERIFY_RC=0" in doc
    assert "SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true" in doc
    assert "FuturesProducerPacket" in doc
    assert "futures_universe_upstream_adapter_v1" in doc


def test_universe_selection_readmodel_links_real_source_charter() -> None:
    doc = UNIVERSE_SELECTION_DOC.read_text(encoding="utf-8")
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc
    assert "Real-Source Charter" in doc
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc


def test_governed_metadata_snapshot_template_doc_exists_and_markers() -> None:
    assert GOVERNED_SNAPSHOT_TEMPLATE_DOC.is_file()
    doc = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    assert "OPERATOR_TRUTH_GO_GRANTED=false" in doc
    assert "GOVERNED_SNAPSHOT_ACCEPTED=false" in doc
    assert "SNAPSHOT_DATA_CREATED=false" in doc
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
    assert "LIVE_TRADING_AUTHORIZED=false" in doc
    assert "Evidence != Approval/Lift/Live" in doc
    assert "governed_metadata/{bundle_id}/" in doc
    assert "MANIFEST_VERIFY_RC=0" in doc
    assert "freshness_state=fresh" in doc
    assert "futures_producer_packet_governed.v1" in doc
    assert "market_ranking_funnel_readmodel.v0" in doc
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc


def test_real_source_charter_links_governed_snapshot_template() -> None:
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md" in doc


MARKET_DATA_SOURCE_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md"
)


def test_real_futures_market_data_source_contract_linked_from_charter() -> None:
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md" in doc
    assert MARKET_DATA_SOURCE_DOC.is_file()


def test_u2b_truth_promotion_bounded_prep_stop_conditions_in_template() -> None:
    doc = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    markers = (
        "TRUTH_PROMOTION_EXECUTED=false",
        "OBSERVABILITY_TRUTH_PROMOTION_BOUNDED_PREP_ONLY=true",
        "OPERATOR_TRUTH_GO_RECORD_REQUIRED=true",
        "TRUTH_PROMOTION_STOP_S1_STRICT_INSTRUMENT_COMPLETE=active_when_zero_without_policy",
        "TRUTH_PROMOTION_STOP_S2_MIN_NOTIONAL_MISSING=active_when_all_packets_missing",
        "TRUTH_PROMOTION_STOP_S3_OPERATOR_TRUTH_GO_RECORD=active_until_durable_record",
        "TRUTH_PROMOTION_STOP_S5_TRUTH_GO_GRANTED=false",
        "MISSING_TRUTH_FAIL_CLOSED_INTENTIONAL=true",
    )
    for marker in markers:
        assert marker in doc
    assert "S1" in doc and "S2" in doc and "S3" in doc and "S5" in doc
    assert "LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH" in doc
    assert "Not observability truth promotion execution" in doc


def test_u2b_canonical_candidate_lineage_documented_in_template() -> None:
    doc = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    assert (
        "CANONICAL_GOVERNED_CANDIDATE_BUNDLE_ID="
        "u2c_kraken_governed_snapshot_candidate_post_pr4067_v1_20260608T234112Z"
    ) in doc
    assert "post_pr4067_v1_20260608T234112Z" in doc
    assert "332 packets" in doc
    assert "futures_producer_packet_governed.v1" in doc


def test_u2b_operator_truth_go_record_required_before_promotion() -> None:
    doc = GOVERNED_SNAPSHOT_TEMPLATE_DOC.read_text(encoding="utf-8")
    assert "Operator Truth-GO Decision Record" in doc
    assert "OPERATOR_TRUTH_GO_RECORD_REQUIRED=true" in doc
    assert "template alone is insufficient" in doc
    assert "observability_truth_allowed=true" in doc
    assert "Separate bounded Truth-Promotion GO token" in doc
