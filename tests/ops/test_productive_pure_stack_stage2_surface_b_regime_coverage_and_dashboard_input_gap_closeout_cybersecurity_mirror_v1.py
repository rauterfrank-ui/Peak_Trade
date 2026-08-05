"""Cybersecurity mirror markers for regime-coverage dashboard input-gap closeout."""

from __future__ import annotations

from pathlib import Path

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1.constants_v1 import (
    CYBERSECURITY_MIRROR_REL,
    NEXT_STEP_ID,
    OBSERVATION_PACK_DIGEST,
    PRODUCER_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MIRROR_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR",
    f"OWNER_GO={NEXT_STEP_ID}",
    f"NEXT_STEP_ID={NEXT_STEP_ID}",
    f"OBSERVATION_PACK_DIGEST={OBSERVATION_PACK_DIGEST}",
    f"PRODUCER_DIGEST={PRODUCER_DIGEST}",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY_FLIP=false",
    "RUNTIME_IMPLEMENTED_FLIP=false",
    "DASHBOARD_LOGIC_CHANGE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "TRADING_LOGIC_CHANGE=false",
    "ORDERS_TESTNET_LIVE=false",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "FAIL_CLOSED=true",
)


def test_cybersecurity_mirror_execution_markers_v1() -> None:
    text = (REPO_ROOT / CYBERSECURITY_MIRROR_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_MIRROR_MARKERS:
        assert marker in text, marker
