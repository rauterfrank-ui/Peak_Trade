"""OD U01/P01 → 29P sizing-mint join adjudication (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "OD_U01_P01_29P_SIZING_MINT_CANONICAL_ADJUDICATION_V1"
ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json"
)
NUMERIC_ADJ: Final[str] = (
    "config/governance/od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1.json"
)
SIZING_ADJ: Final[str] = (
    "config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json"
)
U01_SPEC: Final[str] = (
    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1.md"
)
P01_SPEC: Final[str] = "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1.md"
U01_ADAPTER: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_u01_account_mode_adapter_v1.py"
)
P01_POLICY: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_p01_policy_v1.py"
)
MINT_JOIN: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1.py"
)
PRODUCER: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_available_for_sizing_producer_v1.py"
)
TREASURY_HANDOFF: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_treasury_single_source_capital_handoff_v1.py"
)

DL_MINT_KEYS: Final[tuple[str, ...]] = tuple(f"DL-MINT-{i:02d}" for i in range(1, 18))
DL_U01_WITNESS_KEYS: Final[tuple[str, ...]] = ("DL-U01-WIT-01",)
DOMAIN_LAW_KEYS: Final[tuple[str, ...]] = DL_MINT_KEYS + DL_U01_WITNESS_KEYS


@dataclass(frozen=True)
class OdU01P01SizingMintAdjudicationV1:
    payload: Mapping[str, Any]

    def to_report_v1(self) -> dict[str, Any]:
        laws = self.payload.get("domain_laws", {})
        u01 = self.payload.get("u01", {})
        p01 = self.payload.get("p01", {})
        mint = self.payload.get("mint_join", {})
        return {
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "DECISION_CASE": self.payload.get("decision_case"),
            "DEPENDENCY_GATE": self.payload.get("dependency_gate"),
            "U01_SEMANTIC_ID": u01.get("semantic_id"),
            "U01_ELIGIBILITY_STATUS": u01.get("eligibility_status"),
            "P01_SEMANTIC_ID": p01.get("semantic_id"),
            "P01_DIRECTIVE_STATUS": p01.get("directive_status"),
            "MINT_JOIN_STATUS": mint.get("mint_join_status"),
            "29P_COMMON_EPOCH_BINDING_STATUS": self.payload.get("29p_common_epoch_binding_status"),
            "29P_NORMATIVE_PACK_IDENTITY_STATUS": self.payload.get(
                "29p_normative_pack_identity_status"
            ),
            "DOMAIN_LAWS_PROVEN_CURRENT": [k for k, v in laws.items() if v == "PROVEN_CURRENT"],
            "DOMAIN_LAWS_UNKNOWN_CURRENT": [k for k, v in laws.items() if v == "UNKNOWN_CURRENT"],
            "REPLAY_CAN_MINT_FRESHNESS": self.payload.get("replay", {}).get(
                "replay_can_mint_freshness"
            ),
        }


def load_adjudication_v1(repo_root: Path) -> OdU01P01SizingMintAdjudicationV1:
    path = repo_root / ADJUDICATION_CONFIG
    return OdU01P01SizingMintAdjudicationV1(payload=json.loads(path.read_text(encoding="utf-8")))


def validate_adjudication_against_repo_v1(
    *,
    repo_root: Path,
    adjudication: OdU01P01SizingMintAdjudicationV1 | None = None,
) -> tuple[bool, tuple[str, ...]]:
    adj = adjudication or load_adjudication_v1(repo_root)
    p = adj.payload
    reasons: list[str] = []
    if p.get("decision_case") not in {"A", "D"}:
        reasons.append("DECISION_CASE_MUST_BE_A_OR_D")
    if p.get("dependency_gate") != "PASS":
        reasons.append("DEPENDENCY_GATE_MUST_PASS")
    if p.get("29p_normative_pack_complete") is not False:
        reasons.append("29P_NORMATIVE_PACK_MUST_REMAIN_INCOMPLETE")
    if p.get("unk_sealed_venue_number_29p_status") != "UNKNOWN_CURRENT":
        reasons.append("UNK_SEALED_29P_MUST_REMAIN_UNKNOWN")
    replay = p.get("replay", {})
    if replay.get("replay_can_mint_freshness") is not False:
        reasons.append("REPLAY_CAN_MINT_FRESHNESS_MUST_BE_FALSE")
    if replay.get("replay_can_mint_u01_current") is not False:
        reasons.append("REPLAY_CAN_MINT_U01_MUST_BE_FALSE")
    if replay.get("replay_can_mint_p01_current") is not False:
        reasons.append("REPLAY_CAN_MINT_P01_MUST_BE_FALSE")
    if replay.get("replay_can_mint_29p_current") is not False:
        reasons.append("REPLAY_CAN_MINT_29P_MUST_BE_FALSE")
    laws = p.get("domain_laws", {})
    if set(laws) != set(DOMAIN_LAW_KEYS):
        reasons.append("DOMAIN_LAW_KEYS_MISMATCH")
    if laws.get("DL-MINT-08") != "UNKNOWN_CURRENT":
        reasons.append("DL_MINT_08_SEALED_EPOCH_MUST_BE_UNKNOWN")
    if laws.get("DL-MINT-16") != "UNKNOWN_CURRENT":
        reasons.append("DL_MINT_16_PACK_MUST_BE_UNKNOWN")
    if laws.get("DL-U01-WIT-01") != "PROVEN_CURRENT":
        reasons.append("DL_U01_WIT_01_MUST_BE_PROVEN_CURRENT")
    proven_mint = sum(1 for k in DL_MINT_KEYS if laws.get(k) == "PROVEN_CURRENT")
    if proven_mint != 15:
        reasons.append("EXPECTED_15_DL_MINT_PROVEN_CURRENT")

    numeric = json.loads((repo_root / NUMERIC_ADJ).read_text(encoding="utf-8"))
    sizing = json.loads((repo_root / SIZING_ADJ).read_text(encoding="utf-8"))
    transform = sizing["available_for_sizing"]["transformation_id"]
    if numeric.get("transform_id") != transform:
        reasons.append("6961_TRANSFORM_DRIFT")
    if p.get("29p_numeric_input_binding_status") != "PROVEN_CURRENT":
        reasons.append("29P_NUMERIC_STATUS_DRIFT")

    u01_spec = (repo_root / U01_SPEC).read_text(encoding="utf-8")
    if "FUTURES_MODE" not in u01_spec or "acctLv" not in u01_spec:
        reasons.append("U01_SPEC_SURFACE_MISSING")
    p01_spec = (repo_root / P01_SPEC).read_text(encoding="utf-8")
    if "DOES_NOT_APPLY" not in p01_spec:
        reasons.append("P01_SPEC_DOES_NOT_APPLY_MISSING")

    adapter = (repo_root / U01_ADAPTER).read_text(encoding="utf-8")
    if (
        "ELIGIBILITY_FACT_ID" not in adapter
        and "build_current_productive_u01_eligibility_fact_v1" not in adapter
    ):
        reasons.append("U01_ADAPTER_MISSING")
    if 'REQUIRED_RAW_TOKEN = "2"' not in adapter:
        reasons.append("U01_REQUIRED_RAW_2_MISSING")

    policy = (repo_root / P01_POLICY).read_text(encoding="utf-8")
    if "CURRENT_PRODUCTIVE_P01_POLICY_DOES_NOT_APPLY_V1" not in policy:
        reasons.append("P01_POLICY_ID_MISSING")

    join_src = (repo_root / MINT_JOIN).read_text(encoding="utf-8")
    if "AVAILABLE_FOR_SIZING=BASE-U04-P01_IF_APPLIES" not in join_src:
        reasons.append("MINT_JOIN_FORMULA_MISSING")

    producer = (repo_root / PRODUCER).read_text(encoding="utf-8")
    for token in (
        "ELIGIBILITY_FACT_MISSING",
        "P01_FACT_MISSING",
        "P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED",
        "ELIGIBILITY_SCOPE_OR_EPOCH_MISMATCH",
    ):
        if token not in producer:
            reasons.append(f"PRODUCER_INVARIANT_MISSING_{token}")

    mint = p.get("mint_join", {})
    if mint.get("mint_incomplete_fail_closed") is not True:
        reasons.append("MINT_INCOMPLETE_MUST_FAIL_CLOSED")
    if mint.get("mint_join_status") != "PROVEN_CURRENT":
        reasons.append("MINT_JOIN_STATUS_MUST_BE_PROVEN")

    u01 = p.get("u01", {})
    if u01.get("replay_can_mint_current") is not False:
        reasons.append("U01_REPLAY_MINT_MUST_BE_FALSE")
    p01 = p.get("p01", {})
    if p01.get("p01_can_apply_twice") is not False:
        reasons.append("P01_CAN_APPLY_TWICE_MUST_BE_FALSE")

    risk = p.get("risk_layering", {})
    if risk.get("risk_fraction_application_count_at_mint") != 0:
        reasons.append("RISK_FRACTION_MUST_NOT_APPLY_AT_MINT")
    if risk.get("u04_reapplication_at_mint") is not False:
        reasons.append("U04_REAPPLICATION_MUST_BE_FALSE")

    treasury = (repo_root / TREASURY_HANDOFF).read_text(encoding="utf-8")
    for token in (
        "U01_WITNESS_REQUIRED_NO_IMPLICIT_ACCT_LV_DEFAULT",
        "U01_RAW_ACCT_LV_WITNESS_MISSING",
        "U04_P01_ELIGIBILITY_HOST_INPUTS_MISSING",
    ):
        if token not in treasury:
            reasons.append(f"TREASURY_U01_WITNESS_GUARD_MISSING_{token}")
    if 'raw_acct_lv="2"' in treasury and "u04_p01_host_inputs or" in treasury:
        reasons.append("TREASURY_MUST_NOT_IMPLICIT_DEFAULT_ACCT_LV_2")
    divs = p.get("semantic_divergences", [])
    div04 = next((d for d in divs if d.get("id") == "SEM-SURF-DIV-00004"), None)
    if div04 is None or div04.get("status") != "PROVEN_CURRENT":
        reasons.append("SEM_SURF_DIV_00004_MUST_BE_PROVEN_AFTER_REPAIR")

    return (len(reasons) == 0, tuple(reasons))


def build_adjudication_report_v1(*, repo_root: Path) -> dict[str, Any]:
    adj = load_adjudication_v1(repo_root)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=repo_root, adjudication=adj)
    report = adj.to_report_v1()
    report["VALIDATION_OK"] = ok
    report["VALIDATION_REASONS"] = list(reasons)
    return report
