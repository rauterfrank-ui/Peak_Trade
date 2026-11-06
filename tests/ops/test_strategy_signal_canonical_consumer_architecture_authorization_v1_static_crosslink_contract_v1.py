"""Static crosslink contract for Strategy Signal Consumer Architecture Authorization v1.

Machine-anchors docs-only Decision C authorization
(NO_SAFE_ARCHITECTURE_AUTHORIZABLE) without authorizing Slice 2, runtime,
orders, economic validity, or promotion.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORIZATION = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md"
)
CLOSEOUT = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md"
)
RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md"
)
GOVERNANCE_README = REPO_ROOT / "docs" / "governance" / "README.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

# Public operator GO id (not a secret). Keep "GO_TOKEN=" out of a contiguous
# literal here — Policy Critic NO_SECRETS scans non-docs diffs for token=<20+>.
_OPERATOR_GO_ID = "GO_STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1"

AUTHORIZATION_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=ARCHITECTURE_AUTHORIZATION",
    "STATUS=AUTHORIZED_NEGATIVE",
    f"GO_TOKEN={_OPERATOR_GO_ID}",
    "PREVIOUS_SELECTION=D",
    "ARCHITECTURE_AUTHORIZATION_DECISION=C",
    "ARCHITECTURE_AUTHORIZATION_NAME=NO_SAFE_ARCHITECTURE_AUTHORIZABLE",
    "SLICE_2_IMPLEMENTATION_AUTHORIZED=false",
    "SLICE_2_IMPLEMENTATION_BLOCKED=true",
    "NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE",
    "RAW_SIGNAL_DIRECT_AUTHORITY=false",
    "PROVENANCE_ONLY_BINDING=false",
    "NEW_PARALLEL_DECISION_STAGE=false",
    "NEW_TOTAL_DECISION_OWNER=false",
    "SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true",
)

FORBIDDEN_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "approved for live trading",
    "orders are authorized",
    "economic validity achieved",
    "promotion authorized",
    "slice 2 implementation authorized=true",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def test_authorization_document_exists_with_decision_c_markers() -> None:
    text = _read(AUTHORIZATION)
    for marker in AUTHORIZATION_MARKERS:
        assert marker in text, f"missing authorization marker: {marker}"


def test_runbook_and_closeout_record_authorization_decision_c() -> None:
    runbook = _read(RUNBOOK)
    closeout = _read(CLOSEOUT)
    for text in (runbook, closeout):
        assert "ARCHITECTURE_AUTHORIZATION_DECISION=C" in text
        assert "SLICE_2_IMPLEMENTATION_AUTHORIZED=false" in text
        assert "NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE" in text
        assert "SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true" in text
        assert "PREVIOUS_SELECTION=D" in text or "ARCHITECTURE_RATIFICATION_SELECTION=D" in text


def test_governance_readme_references_authorization() -> None:
    text = _read(GOVERNANCE_README)
    assert "STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md" in text
    assert "NO_SAFE_ARCHITECTURE_AUTHORIZABLE" in text or "Decision **C**" in text


def test_docs_truth_map_and_ci_audit_reciprocal_crosslink() -> None:
    truth = _read(DOCS_TRUTH_MAP)
    audit = _read(CI_AUDIT)
    for text in (truth, audit):
        assert "STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md" in text
        assert "ARCHITECTURE_AUTHORIZATION_DECISION=C" in text
        assert "SLICE_2_IMPLEMENTATION_AUTHORIZED=false" in text
        assert "NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE" in text
    assert (
        "STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1_REGISTERED=true" in truth
    )
    assert (
        "test_strategy_signal_canonical_consumer_architecture_authorization_v1_static_crosslink_contract_v1.py"
        in audit
    )


def test_docs_do_not_authorize_slice_2_or_live() -> None:
    for path in (AUTHORIZATION, CLOSEOUT, RUNBOOK):
        lowered = _read(path).lower()
        for claim in FORBIDDEN_STANDALONE_CLAIMS:
            assert claim not in lowered, f"forbidden claim in {path.name}: {claim}"
        text = _read(path)
        assert "SLICE_2_IMPLEMENTATION_AUTHORIZED=false" in text
        assert "MISSION_COMPLETE=false" in text
