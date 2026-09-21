"""Canonical volatility productive campaign R1 recovery + active binding v1."""

from __future__ import annotations

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    assert_exactly_one_active_binding_file_v1,
    build_active_campaign_binding_v1,
    load_active_campaign_binding_v1,
    parse_active_campaign_binding_v1,
    verify_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    ACTIVE_BINDING_REL_PATH,
    CAPABILITY_ID,
    DISPOSITION_REL_PATH,
    OWNER_POLICY,
    PACKAGE_MARKER,
    R1_MATERIALIZED_REPOSITORY_SHA,
    R1_PREREGISTRATION_REL_PATH,
    TOMBSTONE_ABANDONED_CAMPAIGN_ID,
    TOMBSTONE_ABANDONED_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.disposition_v1 import (
    assert_campaign_not_tombstone_v1,
    assert_old_campaign_cannot_complete_v1,
    assert_session_not_tombstone_v1,
    build_abandoned_campaign_disposition_v1,
    load_abandoned_campaign_disposition_v1,
    verify_abandoned_campaign_disposition_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.gate_v1 import (
    assert_late_age_session_has_s01_persistence_v1,
    assert_not_additional_evidence_routing_v1,
    assert_runtime_matches_active_binding_v1,
    resolve_active_campaign_binding_for_runtime_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ActiveCampaignBindingV1,
    AbandonedCampaignDispositionV1,
    ProductiveCampaignR1RecoveryError,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.preregistration_v1 import (
    build_r1_active_preregistration_payload_v1,
    verify_r1_active_preregistration_payload_v1,
)

__all__ = [
    "ACTIVE_BINDING_REL_PATH",
    "ActiveCampaignBindingV1",
    "AbandonedCampaignDispositionV1",
    "CAPABILITY_ID",
    "DISPOSITION_REL_PATH",
    "OWNER_POLICY",
    "PACKAGE_MARKER",
    "ProductiveCampaignR1RecoveryError",
    "R1_MATERIALIZED_REPOSITORY_SHA",
    "R1_PREREGISTRATION_REL_PATH",
    "TOMBSTONE_ABANDONED_CAMPAIGN_ID",
    "TOMBSTONE_ABANDONED_SESSION_IDS",
    "assert_campaign_not_tombstone_v1",
    "assert_exactly_one_active_binding_file_v1",
    "assert_late_age_session_has_s01_persistence_v1",
    "assert_not_additional_evidence_routing_v1",
    "assert_old_campaign_cannot_complete_v1",
    "assert_runtime_matches_active_binding_v1",
    "assert_session_not_tombstone_v1",
    "build_abandoned_campaign_disposition_v1",
    "build_active_campaign_binding_v1",
    "build_r1_active_preregistration_payload_v1",
    "derive_r1_campaign_identity_v1",
    "load_abandoned_campaign_disposition_v1",
    "load_active_campaign_binding_v1",
    "parse_active_campaign_binding_v1",
    "resolve_active_campaign_binding_for_runtime_v1",
    "verify_abandoned_campaign_disposition_v1",
    "verify_active_campaign_binding_v1",
    "verify_r1_active_preregistration_payload_v1",
]
