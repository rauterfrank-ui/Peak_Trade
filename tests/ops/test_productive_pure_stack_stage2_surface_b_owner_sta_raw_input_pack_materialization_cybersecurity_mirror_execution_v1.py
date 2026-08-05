"""Cybersecurity mirror contracts for raw input-pack materialization execution."""

from __future__ import annotations

from pathlib import Path

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1.constants_v1 import (
    CYBERSECURITY_MIRROR_REL,
    OWNER_DECISION_REL,
    OWNER_GO,
    OWNER_GO_BASE_SHA,
    STATUS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MIRROR_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    f"OWNER_GO={OWNER_GO}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"STATUS_SURFACE={STATUS}",
    f"OWNER_DECISION={OWNER_DECISION_REL}",
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_CREATED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "ORDERS_TESTNET_LIVE=false",
    "INVENTED_VALUES=false",
)


def test_materialization_execution_cybersecurity_mirror_markers_v1() -> None:
    text = (REPO_ROOT / CYBERSECURITY_MIRROR_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_MIRROR_MARKERS:
        assert marker in text, marker
