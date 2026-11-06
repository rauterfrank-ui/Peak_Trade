"""OD 29P normative pack seal — Owner ratification (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "OD-29P-NORMATIVE-PACK-V1"
ADJUDICATION_CONFIG: Final[str] = "config/governance/od_29p_normative_pack_v1.json"
U01_P01_ADJ: Final[str] = (
    "config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json"
)
PRODUCER: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_available_for_sizing_producer_v1.py"
)
RISK_CAPITAL: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_29p_risk_capital_model_v1.py"
)
LIVE_SCOPE: Final[str] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_29p_live_account_bound_and_instrument_scope_v1.py"
)
TREASURY: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_treasury_single_source_capital_handoff_v1.py"
)
ADMISSIBILITY: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/step_29p_capital_risk_admissibility_v1.py"
)
PRE_EXTERNAL_PROOF: Final[str] = (
    "src/ops/pre_external_to_external_effect_boundary_bounded_wp_v1/proof_v1.py"
)

DL_SEAL_KEYS: Final[tuple[str, ...]] = tuple(f"DL-SEAL-{i:02d}" for i in range(1, 11))


@dataclass(frozen=True)
class Od29PNormativePackV1:
    payload: Mapping[str, Any]

    def to_report_v1(self) -> dict[str, Any]:
        laws = self.payload.get("domain_laws", {})
        return {
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "OWNER_DECISION_ID": self.payload.get("owner_decision_id"),
            "DEPENDENCY_GATE": self.payload.get("dependency_gate"),
            "29P_NORMATIVE_PACK_COMPLETE": self.payload.get("pack_identity", {}).get(
                "29p_normative_pack_complete"
            ),
            "29P_NORMATIVE_PACK_IDENTITY_STATUS": self.payload.get("pack_identity", {}).get(
                "29p_normative_pack_identity_status"
            ),
            "SEALED_NORMATIVE_EPOCH_STATUS": self.payload.get("normative_epoch", {}).get(
                "sealed_normative_common_epoch_status"
            ),
            "VENUE_NUMBER_PIN_STATUS": self.payload.get("venue_account_binding", {}).get(
                "unk_sealed_venue_number_29p_status"
            ),
            "DOMAIN_LAWS_RATIFIED": [k for k, v in laws.items() if v == "RATIFIED_CURRENT"],
            "EXTERNAL_EFFECT_AUTHORIZED": self.payload.get("external_effect_authorized"),
            "POST_ALLOWED": self.payload.get("post_allowed"),
        }


def load_adjudication_v1(repo_root: Path) -> Od29PNormativePackV1:
    path = repo_root / ADJUDICATION_CONFIG
    return Od29PNormativePackV1(payload=json.loads(path.read_text(encoding="utf-8")))


def validate_adjudication_against_repo_v1(
    *,
    repo_root: Path,
    adjudication: Od29PNormativePackV1 | None = None,
) -> tuple[bool, tuple[str, ...]]:
    adj = adjudication or load_adjudication_v1(repo_root)
    p = adj.payload
    reasons: list[str] = []
    if p.get("owner_decision_id") != WORKPACKAGE_ID:
        reasons.append("OWNER_DECISION_ID_MISMATCH")
    if p.get("dependency_gate") != "PASS":
        reasons.append("DEPENDENCY_GATE_MUST_PASS")
    if p.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_MUST_BE_NONE")
    if p.get("external_effect_authorized") is not False:
        reasons.append("EXTERNAL_EFFECT_MUST_BE_FALSE")
    if p.get("post_allowed") is not False:
        reasons.append("POST_ALLOWED_MUST_BE_FALSE")
    pack = p.get("pack_identity", {})
    if pack.get("29p_normative_pack_complete") is not True:
        reasons.append("29P_PACK_MUST_BE_COMPLETE")
    if pack.get("29p_normative_pack_identity_status") != "RATIFIED_CURRENT":
        reasons.append("PACK_IDENTITY_MUST_BE_RATIFIED")
    if pack.get("foreign_authority_minted") is not False:
        reasons.append("FOREIGN_AUTHORITY_MUST_NOT_BE_MINTED")
    if pack.get("new_pack_id_digest_uuid_introduced") is not False:
        reasons.append("NEW_PACK_ID_MUST_NOT_BE_INTRODUCED")
    epoch = p.get("normative_epoch", {})
    if epoch.get("second_independent_clock_introduced") is not False:
        reasons.append("SECOND_CLOCK_MUST_NOT_BE_INTRODUCED")
    if epoch.get("sealed_normative_common_epoch_status") != "RATIFIED_CURRENT":
        reasons.append("SEALED_EPOCH_MUST_BE_RATIFIED")
    venue = p.get("venue_account_binding", {})
    if venue.get("arbitrary_venue_ordinal_introduced") is not False:
        reasons.append("VENUE_ORDINAL_MUST_NOT_BE_INTRODUCED")
    if venue.get("unk_sealed_venue_number_29p_status") == "UNKNOWN_CURRENT":
        reasons.append("VENUE_NUMBER_PIN_MUST_NOT_REMAIN_UNKNOWN")
    treasury = p.get("treasury_to_admission_representation", {})
    if treasury.get("treasury_mints_risk_admissible") is not False:
        reasons.append("TREASURY_MUST_NOT_MINT_RISK_ADMISSIBLE")
    replay = p.get("replay", {})
    for key in (
        "replay_can_mint_freshness",
        "replay_can_mint_29p_current",
        "replay_can_mint_sealed_pack_identity",
    ):
        if replay.get(key) is not False:
            reasons.append(f"{key}_MUST_BE_FALSE")
    laws = p.get("domain_laws", {})
    if set(laws) != set(DL_SEAL_KEYS):
        reasons.append("DOMAIN_LAW_KEYS_MISMATCH")
    if not all(laws.get(k) == "RATIFIED_CURRENT" for k in DL_SEAL_KEYS):
        reasons.append("ALL_DL_SEAL_MUST_BE_RATIFIED")

    u01_p01 = json.loads((repo_root / U01_P01_ADJ).read_text(encoding="utf-8"))
    if u01_p01.get("29p_normative_pack_complete") is not True:
        reasons.append("U01_P01_PACK_NOT_MARKED_COMPLETE")
    if u01_p01.get("29p_normative_pack_identity_status") != "RATIFIED_CURRENT":
        reasons.append("U01_P01_PACK_IDENTITY_NOT_RATIFIED")

    producer = (repo_root / PRODUCER).read_text(encoding="utf-8")
    for token in (
        "ELIGIBILITY_SCOPE_OR_EPOCH_MISMATCH",
        "bound_venue_identity",
        "bound_account_identity",
        "decision_epoch",
        "observed_at_as_of",
    ):
        if token not in producer:
            reasons.append(f"PRODUCER_TOKEN_MISSING_{token}")

    risk = (repo_root / RISK_CAPITAL).read_text(encoding="utf-8")
    if "produce_current_productive_29p_risk_capital_v1" not in risk:
        reasons.append("RISK_CAPITAL_PRODUCER_MISSING")

    scope = (repo_root / LIVE_SCOPE).read_text(encoding="utf-8")
    if "BoundInstrument" not in scope and "bound_instrument" not in scope.lower():
        reasons.append("CAP24_INSTRUMENT_SCOPE_MISSING")

    handoff = (repo_root / TREASURY).read_text(encoding="utf-8")
    if "evaluate_step_29p_capital_risk_admissibility_v1" not in handoff:
        reasons.append("TREASURY_ADMISSIBILITY_EVAL_MISSING")
    if "risk_admissible" not in handoff:
        reasons.append("TREASURY_RISK_ADMISSIBLE_REFERENCE_MISSING")

    adm = (repo_root / ADMISSIBILITY).read_text(encoding="utf-8")
    if "STEP_29P_RISK_ADMISSIBILITY" not in adm and "risk_admissible" not in adm:
        reasons.append("ADMISSIBILITY_MODULE_MISSING")

    pre = (repo_root / PRE_EXTERNAL_PROOF).read_text(encoding="utf-8")
    if "PRE_EXTERNAL" not in pre and "pre_external" not in pre.lower():
        reasons.append("PRE_EXTERNAL_PROOF_SURFACE_MISSING")

    return (len(reasons) == 0, tuple(reasons))


def build_adjudication_report_v1(*, repo_root: Path) -> dict[str, Any]:
    adj = load_adjudication_v1(repo_root)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=repo_root, adjudication=adj)
    report = adj.to_report_v1()
    report["VALIDATION_OK"] = ok
    report["VALIDATION_REASONS"] = list(reasons)
    return report
