"""Cybersecurity mirror contracts for raw input-pack materialization decision."""

from __future__ import annotations

from pathlib import Path

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    OWNER_DECISION_REL,
    OWNER_GO_BASE_SHA,
    RECORDED_OWNER_VALUE,
    STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MIRROR_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "STATUS=DOCUMENTARY_MIRROR_OF_OWNER_STA_DECISION_SURFACE",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"CAPABILITY_SCOPE={CAPABILITY_SCOPE}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={RECORDED_OWNER_VALUE}",
    f"STATUS_SURFACE={STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED}",
    f"OWNER_DECISION={OWNER_DECISION_REL}",
    f"MACHINE_MANIFEST={DECISIONS_MANIFEST_REL}",
    "PACK_MATERIALIZATION=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    "AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true",
    "AUTHORIZE_DETAIL_FIELDS_COMPLETE=false",
    "PROVABLE_INSTANCE_FIELDS_CLOSED=true",
    "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true",
    "SILENT_DEFAULTS=false",
)

FORBIDDEN_MIRROR_CLAIMS: tuple[str, ...] = (
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "NOTION_SSOT=true",
    "SILENT_DEFAULTS=true",
)


def test_materialization_cybersecurity_mirror_markers_v1() -> None:
    text = (REPO_ROOT / CYBERSECURITY_MIRROR_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_MIRROR_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_MIRROR_CLAIMS:
        assert claim not in text, claim
