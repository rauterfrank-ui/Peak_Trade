"""Exact venue metadata GET persist for current SUI pretrade MAX_SIZE v1.

Static/docs/evidence guards. Reuses existing owner tests. No core runtime
mutation. No live authority. No consumer implementation. No unit invention.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md"
)
PRIOR_6147 = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md"
)
LIMIT_GATES_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md"
)
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
EXPOSURE = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exposure_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
EVIDENCE_DIR = (
    REPO_ROOT
    / "evidence/ops/exact_venue_metadata_get_current_sui_pretrade_max_size_v1/20260829T182239Z"
)
SNAPSHOT = EVIDENCE_DIR / "GET_SNAPSHOT.sanitized.json"
CLAIMS = EVIDENCE_DIR / "claims.json"
MANIFEST = EVIDENCE_DIR / "MANIFEST.sha256"
EXPECTED_BODY_SHA256 = "038f2bf82f18f2d42ed26dca281cc7733e4ef7d07206fd0b19637189ec3e4cd2"
EXPECTED_ORIGIN_MAIN_SHA = "0b9f15a0086d58ec100fe7fb173d9fa12acdf5ea"
OWNER_GO = "PEAK_TRADE_EXACT_VENUE_METADATA_GET_FOR_CURRENT_SUI_PRETRADE_MAX_SIZE_V1"
SEE_ALSO = (
    "SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE="
    "docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md"
)


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_spec_is_subordinate_and_does_not_grant_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "NO_LIVE_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "NETWORK_GET_PERFORMED=true" in spec
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "AUTH_REQUIRED=false" in spec
    assert "AUTH_HEADER_SENT=false" in spec
    assert f"OWNER_GO={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md"
        in section
    )
    for text in (spec, section):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "CURRENT_RAW_MAXLMTSZ_OBSERVED=true" in text
        assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in text
        assert "MAX_SIZE_UNIT=UNBOUND" in text
        assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in text
        assert "MAX_SIZE_CONSUMER_BOUND=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
    assert "THIS_SLICE_NETWORK_GET_PERFORMED=true" in section
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_UNIT" in spec
    assert "NEXT_DISTINCT_SURFACE=MAX_SIZE_UNIT" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert (
        "SOURCE_ADJUDICATION_RESULT=CURRENT_RAW_MAXLMTSZ_OBSERVED_PARTIAL_MAX_SIZE_REMAINS" in spec
    )


def test_historical_6147_get_not_performed_remains() -> None:
    prior = PRIOR_6147.read_text(encoding="utf-8")
    assert "NETWORK_GET_PERFORMED=false" in prior
    assert "NETWORK_GET=NOT_THIS_SLICE" in prior
    assert "PUBLIC_VENUE_GET=NOT_THIS_SLICE" in prior
    assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in prior
    assert SEE_ALSO in prior
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in LIMIT_GATES_SPEC.read_text(
        encoding="utf-8"
    )


def test_query_contract_and_venue_binding() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    query = public_instruments_query_path_v1()
    assert query == ("/api/v5/public/instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404")
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"
    assert "TARGET_HOST=eea.okx.com" in spec
    assert "TARGET_INST_TYPE=FUTURES" in spec
    assert "TARGET_INSTRUMENT=SUI-USD_UM_XPERP-310404" in spec
    assert "QUERY_CONTRACT_REVALIDATION=PASS" in spec
    assert "ALTERNATE_VENUE_USED=false" in spec
    assert "KRAKEN_USED=false" in spec
    assert "BTC_INSTRUMENT_USED=false" in spec
    assert "SWAP_INST_TYPE_USED=false" in spec
    assert "SIGNED_CANARY_CLIENT_USED=false" in spec


def test_evidence_pack_exact_instrument_and_maxlmtsz() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    wire = snapshot["payload"]["wire_body"]
    assert hashlib.sha256(wire.encode("utf-8")).hexdigest() == EXPECTED_BODY_SHA256
    assert snapshot["http_evidence"]["body_sha256"] == EXPECTED_BODY_SHA256
    assert claims["RESPONSE_BODY_SHA256"] == EXPECTED_BODY_SHA256
    assert snapshot["http_evidence"]["http_status"] == 200
    assert snapshot["payload"]["code"] == "0"
    assert snapshot["payload"]["msg"] == ""
    assert snapshot["payload"]["row_count"] == 1
    assert len(snapshot["payload"]["data"]) == 1
    row = snapshot["payload"]["data"][0]
    assert row["instId"] == "SUI-USD_UM_XPERP-310404"
    assert row["instType"] == "FUTURES"
    assert row["maxLmtSz"] == "100000000"
    assert row["maxMktSz"] == "100000"
    assert row["state"] == "live"
    assert row["baseCcy"] == ""
    assert row["quoteCcy"] == ""
    assert "maxAvailSize" not in row
    assert snapshot["adjudication"]["EXACT_INSTID_MATCH_COUNT"] == 1
    assert snapshot["adjudication"]["CURRENT_RAW_MAXLMTSZ_OBSERVED"] is True
    assert snapshot["adjudication"]["CURRENT_REUSABLE_MAXLMTSZ_PROVEN"] is False
    assert snapshot["adjudication"]["MAXLMTSZ_RAW_VALUE_PARITY_WITH_Z2AR"] is True
    assert snapshot["adjudication"]["MAXMKTSZ_RAW_VALUE_PARITY_WITH_Z2AR"] is True
    assert snapshot["adjudication"]["Z2BD_WINDOW_REUSED"] is False
    assert snapshot["AUTH_HEADER_SENT"] is False
    assert snapshot["SECRET_VALUES_INCLUDED"] is False
    dumped = json.dumps(snapshot)
    assert "Set-Cookie" not in dumped
    assert "__cf_bm" not in dumped
    assert "Authorization" not in dumped


def test_manifest_verifies() -> None:
    lines = [ln for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln.strip()]
    names = []
    for line in lines:
        digest, name = line.split("  ", 1)
        path = EVIDENCE_DIR / name
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        names.append(name)
    assert "GET_SNAPSHOT.sanitized.json" in names
    assert "claims.json" in names
    assert "MANIFEST.sha256" not in names


def test_max_size_firewall_and_consumer_unbound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "MAX_SIZE_UNIT=UNBOUND" in spec
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND_NONE_APPLIED_NONE_PROVEN" in spec
    assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in spec
    assert "MAX_SIZE_CONSUMER_BOUND=false" in spec
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in spec
    assert "RUNTIME_ALIGNMENT_REQUIRED=false" in spec
    assert "MAXLMTSZ_NOT_PROVEN_CONTRACTS=true" in spec
    assert "MAXLMTSZ_NOT_PROVEN_BASE_SUI=true" in spec
    assert "MAXLMTSZ_NOT_PROVEN_NOTIONAL=true" in spec
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source
    assert extract_instrument_constraints_v1 is not None


def test_required_metadata_edge_counts_remain_partial() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "REQUIRED_METADATA_EDGE_COUNT=8" in spec
    assert "BOUND_METADATA_EDGE_COUNT=0" in spec
    assert "PARTIAL_METADATA_EDGE_COUNT=2" in spec
    assert "UNBOUND_METADATA_EDGE_COUNT=6" in spec
    assert "CONFLICTED_METADATA_EDGE_COUNT=0" in spec
    assert "PARTIAL_EDGE_IDS=MAX_SIZE,INSTRUMENT_STATE" in spec
    assert (
        "UNBOUND_EDGE_IDS=MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN"
        in spec
    )
    assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in spec
    assert "EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_UNIT" in spec
    assert "CURRENT_STATUS=PROVEN" not in spec


def test_kraken_and_live_flags_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_EXCLUSION_CLOSED=true" in spec
    assert "KRAKEN_METADATA_REUSED=false" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1_PRESERVED=true" in parent
    assert "PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert SEE_ALSO in LIMIT_GATES_SPEC.read_text(encoding="utf-8")
