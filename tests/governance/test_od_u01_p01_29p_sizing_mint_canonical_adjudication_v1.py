"""OD U01/P01 → 29P sizing-mint join adjudication contracts."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG as NUMERIC_ADJ,
)
from src.governance.od_account_equity_sizing_source_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG as SIZING_ADJ,
)
from src.governance.od_u01_p01_29p_sizing_mint_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG,
    DL_MINT_KEYS,
    build_adjudication_report_v1,
    load_adjudication_v1,
    validate_adjudication_against_repo_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    ELIGIBILITY_FACT_ID,
    P01_FACT_ID,
    P01_DOES_NOT_APPLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    POLICY_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    CANONICAL_SEMANTIC_TOKEN,
    SCHEMA_CLASS as U01_ADAPTER_CLASS,
)

REPO = Path(__file__).resolve().parents[2]


def test_u01_p01_mint_adjudication_loads_and_validates() -> None:
    adj = load_adjudication_v1(REPO)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=REPO, adjudication=adj)
    assert ok, reasons
    report = build_adjudication_report_v1(repo_root=REPO)
    assert report["VALIDATION_OK"] is True
    assert report["DECISION_CASE"] == "D"
    assert report["DEPENDENCY_GATE"] == "PASS"
    assert report["MINT_JOIN_STATUS"] == "PROVEN_CURRENT"


def test_dl_mint_laws_indexed() -> None:
    laws = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))["domain_laws"]
    assert set(laws) == set(DL_MINT_KEYS)
    assert laws["DL-MINT-08"] == "UNKNOWN_CURRENT"
    assert laws["DL-MINT-16"] == "UNKNOWN_CURRENT"
    assert sum(v == "PROVEN_CURRENT" for v in laws.values()) == 15


def test_u01_p01_align_with_6960_6961_without_reopening() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    numeric = json.loads((REPO / NUMERIC_ADJ).read_text(encoding="utf-8"))
    sizing = json.loads((REPO / SIZING_ADJ).read_text(encoding="utf-8"))
    assert numeric["transform_id"] == sizing["available_for_sizing"]["transformation_id"]
    assert payload["29p_numeric_input_binding_status"] == "PROVEN_CURRENT"
    pre = numeric["productive_mint_preconditions"]
    assert pre["u01_eligibility"] == "RESOLVED_NORMATIVE_OD_U01_P01_29P_SIZING_MINT_V1"
    assert pre["p01_directive"] == "RESOLVED_NORMATIVE_OD_U01_P01_29P_SIZING_MINT_V1"
    assert numeric["successor_u01_p01_mint_adjudication"] == (
        "OD_U01_P01_29P_SIZING_MINT_CANONICAL_ADJUDICATION_V1"
    )


def test_semantic_ids_match_runtime_constants() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert payload["u01"]["semantic_id"] == ELIGIBILITY_FACT_ID
    assert payload["p01"]["semantic_id"] == P01_FACT_ID
    assert payload["p01"]["policy_id"] == POLICY_ID
    assert payload["u01"]["canonical_semantic_token"] == CANONICAL_SEMANTIC_TOKEN
    assert payload["u01"]["adapter_schema_class"] == U01_ADAPTER_CLASS
    assert payload["p01"]["does_not_apply_when"] == "ALWAYS_CURRENT_PRODUCTIVE_STANDING_POLICY"
    assert P01_DOES_NOT_APPLY in json.dumps(payload["p01"])
