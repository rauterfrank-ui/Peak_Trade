"""OD 29P fresh-trusted numeric venue bind adjudication (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "OD_29P_FRESH_TRUSTED_NUMERIC_VENUE_BIND_CANONICAL_ADJUDICATION_V1"
ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1.json"
)
PRIOR_SIZING_ADJ: Final[str] = (
    "config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json"
)
FRESH_GET_SPEC: Final[str] = (
    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_"
    "FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1.md"
)
WHOLE_CORE_Q0: Final[str] = "config/governance/whole_core_completion_egress_q0_authority_v1.json"
AVAILABLE_MARGIN_MODULE: Final[str] = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/available_margin_observation_v1.py"
)

DL_NUMERIC_KEYS: Final[tuple[str, ...]] = tuple(f"DL-NUMERIC-{i:02d}" for i in range(1, 13))


@dataclass(frozen=True)
class Od29PNumericVenueBindAdjudicationV1:
    payload: Mapping[str, Any]

    def to_report_v1(self) -> dict[str, Any]:
        laws = self.payload.get("domain_laws", {})
        return {
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "DECISION_CASE": self.payload.get("decision_case"),
            "INDEPENDENCE_GATE": self.payload.get("independence_gate"),
            "NUMERIC_VENUE_BIND_RESOLVED": self.payload.get("numeric_venue_bind_resolved"),
            "FRESH_TRUSTED_GET_CONTRACT_STATUS": self.payload.get(
                "fresh_trusted_get_contract_status"
            ),
            "RAW_FIELD": self.payload.get("raw_field"),
            "OUTPUT_SEMANTIC_ID": self.payload.get("output_semantic_id"),
            "UNK_SEALED_VENUE_NUMBER_29P_STATUS": self.payload.get(
                "unk_sealed_venue_number_29p_status"
            ),
            "DOMAIN_LAWS_PROVEN_CURRENT": [k for k, v in laws.items() if v == "PROVEN_CURRENT"],
            "REPLAY_CAN_MINT_FRESHNESS": self.payload.get("replay_can_mint_freshness"),
        }


def load_adjudication_v1(repo_root: Path) -> Od29PNumericVenueBindAdjudicationV1:
    path = repo_root / ADJUDICATION_CONFIG
    return Od29PNumericVenueBindAdjudicationV1(payload=json.loads(path.read_text(encoding="utf-8")))


def validate_adjudication_against_repo_v1(
    *,
    repo_root: Path,
    adjudication: Od29PNumericVenueBindAdjudicationV1 | None = None,
) -> tuple[bool, tuple[str, ...]]:
    adj = adjudication or load_adjudication_v1(repo_root)
    p = adj.payload
    reasons: list[str] = []
    if p.get("decision_case") not in {"A", "D"}:
        reasons.append("DECISION_CASE_MUST_BE_A_OR_D")
    if p.get("independence_gate") != "PASS":
        reasons.append("INDEPENDENCE_GATE_MUST_PASS")
    if p.get("numeric_venue_bind_resolved") is not True:
        reasons.append("NUMERIC_VENUE_BIND_MUST_BE_RESOLVED")
    if p.get("unk_sealed_venue_number_29p_status") != "UNKNOWN_CURRENT":
        reasons.append("SEALED_29P_MUST_REMAIN_UNKNOWN")
    if p.get("replay_can_mint_freshness") is not False:
        reasons.append("REPLAY_CAN_MINT_FRESHNESS_MUST_BE_FALSE")
    prior = json.loads((repo_root / PRIOR_SIZING_ADJ).read_text(encoding="utf-8"))
    if prior.get("available_for_sizing", {}).get("observation_surface") != p.get("raw_field"):
        reasons.append("RAW_FIELD_MUST_MATCH_6960_OBSERVATION_SURFACE")
    if prior.get("available_for_sizing", {}).get("transformation_id") != p.get("transform_id"):
        reasons.append("TRANSFORM_MUST_MATCH_6960")
    spec = (repo_root / FRESH_GET_SPEC).read_text(encoding="utf-8")
    if p.get("raw_field") not in spec:
        reasons.append("RAW_FIELD_NOT_IN_FRESH_GET_SPEC")
    q0 = json.loads((repo_root / WHOLE_CORE_Q0).read_text(encoding="utf-8"))
    f02 = q0.get("f02_fresh_trusted_q0", {})
    if f02.get("economic_field") != p.get("raw_field"):
        reasons.append("F02_ECONOMIC_FIELD_MISMATCH")
    margin = (repo_root / AVAILABLE_MARGIN_MODULE).read_text(encoding="utf-8")
    if "USD_USDC_EQUIVALENCE_ASSUMED = False" not in margin:
        reasons.append("USD_USDC_EQUIVALENCE_MUST_BE_FALSE_IN_MARGIN_MODULE")
    laws = p.get("domain_laws", {})
    if not all(laws.get(k) == "PROVEN_CURRENT" for k in DL_NUMERIC_KEYS):
        reasons.append("ALL_DL_NUMERIC_MUST_BE_PROVEN_CURRENT")
    return (len(reasons) == 0, tuple(reasons))


def build_adjudication_report_v1(*, repo_root: Path) -> dict[str, Any]:
    adj = load_adjudication_v1(repo_root)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=repo_root, adjudication=adj)
    report = adj.to_report_v1()
    report["VALIDATION_OK"] = ok
    report["VALIDATION_REASONS"] = list(reasons)
    return report
