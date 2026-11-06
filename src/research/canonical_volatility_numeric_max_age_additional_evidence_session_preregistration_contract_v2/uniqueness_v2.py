"""Campaign/session uniqueness guards for additional evidence sessions (v2)."""

from __future__ import annotations

from typing import AbstractSet, Any, Iterable, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    CANDIDATE_SCHEMA_VERSION,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    EXISTING_EXHAUSTED_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
    sha256_hex_text,
)


def assert_session_id_not_exhausted_v2(session_id: str) -> None:
    sid = str(session_id).strip()
    if not sid:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("session_id_required")
    if sid in EXISTING_EXHAUSTED_SESSION_IDS:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "session_id_reuses_exhausted_s01_or_s02"
        )
    if EXISTING_EXHAUSTED_CAMPAIGN_ID in sid and ("_s01_" in sid or "_s02_" in sid):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "session_id_reuses_exhausted_campaign_session_slot"
        )


def assert_campaign_id_not_exhausted_v2(campaign_id: str) -> None:
    cid = str(campaign_id).strip()
    if not cid:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("campaign_id_required")
    if cid == EXISTING_EXHAUSTED_CAMPAIGN_ID:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "campaign_id_reuses_exhausted_s01_s02_campaign"
        )


def assert_session_id_not_terminal_used_v2(
    session_id: str,
    *,
    terminal_session_ids: AbstractSet[str] | Sequence[str] | None = None,
) -> None:
    used = set(terminal_session_ids or ())
    used.update(EXISTING_EXHAUSTED_SESSION_IDS)
    if str(session_id) in used:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "session_id_already_terminal_used"
        )


def assert_unique_session_ids_v2(session_ids: Iterable[str]) -> tuple[str, ...]:
    cleaned = [str(s).strip() for s in session_ids]
    if any(not s for s in cleaned):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("session_id_blank")
    if len(cleaned) != len(set(cleaned)):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("session_ids_not_unique")
    for sid in cleaned:
        assert_session_id_not_exhausted_v2(sid)
    return tuple(cleaned)


def deterministic_additional_campaign_id_v2(*, code_baseline_sha: str) -> str:
    material = "|".join(
        [
            "additional_evidence_session_preregistration_candidate",
            "v2",
            code_baseline_sha,
            "not_exhausted_campaign",
        ]
    )
    suffix = sha256_hex_text(material)[:16]
    campaign_id = f"cv_maxage_additional_evidence_campaign_v2_{suffix}"
    assert_campaign_id_not_exhausted_v2(campaign_id)
    return campaign_id


def deterministic_additional_session_id_v2(
    *,
    campaign_id: str,
    session_index: int,
) -> str:
    assert_campaign_id_not_exhausted_v2(campaign_id)
    if int(session_index) < 1:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "session_index_must_be_positive"
        )
    material = "|".join(
        [
            campaign_id,
            f"session_index={int(session_index)}",
            CANDIDATE_SCHEMA_VERSION,
        ]
    )
    suffix = sha256_hex_text(material)[:12]
    session_id = f"{campaign_id}_s{int(session_index) + 2:02d}_{suffix}"
    assert_session_id_not_exhausted_v2(session_id)
    return session_id


def assert_candidate_uniqueness_matrix_v2(
    candidates: Sequence[Mapping[str, Any]],
    *,
    terminal_session_ids: AbstractSet[str] | Sequence[str] | None = None,
) -> None:
    if len(candidates) < 2:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "minimum_two_additional_sessions_required_for_uniqueness_matrix"
        )
    ids = [str(c.get("session_id", "")) for c in candidates]
    assert_unique_session_ids_v2(ids)
    for candidate in candidates:
        assert_campaign_id_not_exhausted_v2(str(candidate.get("campaign_id", "")))
        assert_session_id_not_terminal_used_v2(
            str(candidate.get("session_id", "")),
            terminal_session_ids=terminal_session_ids,
        )
