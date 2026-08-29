"""Docs/SSOT contract: Master names existing C4 post-confirmation binding."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
C4_SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/MV2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1.md"
)
C4_RUNTIME_MODULE = (
    REPO_ROOT
    / "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_c4_named_master_ssot_pointer_matches_existing_spec_and_runtime() -> None:
    assert C4_SPEC_PATH.is_file()
    assert C4_RUNTIME_MODULE.is_file()
    assert REPLAY_MODULE.is_file()

    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "C4_NAMED_MASTER_SSOT_POINTER=true" in section
    assert "CAPABILITY_ID=POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1" in section
    assert (
        "SPEC=docs/ops/specs/MV2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1.md"
        in section
    )
    assert (
        "RUNTIME_BINDING_SURFACE=trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1"
        in section
    )
    assert "CONSUMER=trading.master_v2.integrated_offline_trading_logic_replay_v1" in section
    assert "BINDING_FOR=Survival → Suitability → Composition" in section
    assert "C4_NEW_STAGE=false" in section
    assert "C4_NEW_OWNER=false" in section
    assert "SECOND_COMPUTE_OWNER=false" in section
    assert "SECOND_COMPUTE_OWNER_EXISTS=false" in section

    spec = C4_SPEC_PATH.read_text(encoding="utf-8")
    assert "CAPABILITY_ID=POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1" in spec
    assert "PRIMARY_OWNER=integrated_offline_trading_logic_replay_v1" in spec

    runtime = C4_RUNTIME_MODULE.read_text(encoding="utf-8")
    assert "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1" in runtime
    replay = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "post_confirmation_survival_suitability_composition_binding_v1" in replay
    assert "assert_c4_c3_assessment_identity_binding_v1" in replay
