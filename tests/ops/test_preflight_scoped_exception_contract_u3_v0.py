"""Static contract tests for scoped preflight exception (U3 pattern) v0 in Preflight §2a.1."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
GLB_REGISTER = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

U3_TOKENS = (
    "SCOPED_PREFLIGHT_EXCEPTION_U3_V0=true",
    "ADAPTER_EXECUTE_EVIDENCE_ONLY=true",
    "PREFLIGHT_MAY_REMAIN_BLOCKED_AFTER_RUN=true",
    "SCOPED_EXCEPTION_NON_GENERALIZABLE=true",
    "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true",
)


def _section_2a1() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8").split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def test_section_2a1_u3_scoped_exception_subsection_exists() -> None:
    section = _section_2a1()
    assert "Scoped preflight exception (U3 pattern) v0" in section
    for token in U3_TOKENS:
        assert token in section


def test_u3_scoped_exception_is_evidence_only() -> None:
    section = _section_2a1()
    assert "evidence-only" in section.lower()
    assert "ADAPTER_EXECUTE_EVIDENCE_ONLY=true" in section
    assert "review inputs only" in section.lower()


def test_u3_does_not_clear_preflight_or_hold() -> None:
    section = _section_2a1()
    collapsed = section.replace("**", "")
    assert "status=BLOCKED" in section
    assert "activation_authorized=false" in section
    assert "may remain unchanged" in section
    assert "does not clear global HOLD" in collapsed
    assert "active global HOLD" in collapsed


def test_u3_does_not_close_glb_or_grant_runtime_authority() -> None:
    section = _section_2a1()
    collapsed = section.replace("**", "")
    assert "does not close GLB-014/GLB-015" in collapsed
    assert "does not grant Live/Testnet/broker authority" in collapsed
    assert "does not start scheduler" in collapsed
    assert "P67/P72 workload" in section


def test_u3_cross_refs_glb015_without_mandatory_archive_paths() -> None:
    section = _section_2a1()
    assert "GLB-015 §6.5" in section
    assert "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md" in section
    assert "historical examples" in section
    assert "not mandatory runtime inputs" in section
    assert "U3_SCOPED_PREFLIGHT_EXCEPTION_RECORD.md" in section


def test_u3_executing_approval_records_scoped_non_generalizable() -> None:
    section = _section_2a1()
    assert "Stage-3 executing approval chain" in section
    assert "scoped and non-generalizable" in section
    assert "each future bounded attempt requires its own explicit operator record" in section


def test_u3_no_automatic_rerun_extension() -> None:
    section = _section_2a1()
    collapsed = section.replace("**", "")
    assert "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true" in section
    assert "does not authorize automatic 24h or 72h reruns" in collapsed


def test_glb015_section_references_u3_bounded_closeouts() -> None:
    text = GLB_REGISTER.read_text(encoding="utf-8")
    section = text.split("### 6.5 GLB-015", 1)[1].split("## 7.", 1)[0]
    collapsed = section.replace("**", "")
    assert "bounded adapter closeouts" in section
    assert "does not clear Preflight BLOCKED" in collapsed


def test_shadow_adapter_requires_approval_record_on_execute() -> None:
    text = SHADOW_ADAPTER.read_text(encoding="utf-8")
    assert "execute requires --approval-record" in text
    assert "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true" in text
    assert "Does not grant Live/broker/exchange approval" in text


def test_docs_truth_map_records_u3_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "U3 pattern" in text or "scoped preflight exception" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
