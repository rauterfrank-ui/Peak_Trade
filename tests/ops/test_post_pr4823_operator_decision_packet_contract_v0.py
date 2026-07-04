"""Contract tests for post-PR4823 operator decision packet v0.

Verifies documentation-only operator decision packet content without authorizing
promotion, runtime, economic evaluation execution, or automatic research continuation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DECISION_PACKET = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "POST_PR4823_OPERATOR_DECISION_PACKET_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0.md"
)


def _read_packet() -> str:
    assert OPERATOR_DECISION_PACKET.is_file(), (
        f"missing operator decision packet: {OPERATOR_DECISION_PACKET}"
    )
    return OPERATOR_DECISION_PACKET.read_text(encoding="utf-8")


def test_operator_decision_packet_exists() -> None:
    body = _read_packet()
    assert (
        "docs_token: DOCS_TOKEN_POST_PR4823_OPERATOR_DECISION_PACKET_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
        in body
    )
    assert "STATUS: OPERATOR_DECISION_PACKET" in body
    assert "non-authorizing" in body.lower()


def test_current_state_flags() -> None:
    body = _read_packet()
    assert "NO_NEW_CANDIDATE_HOLD" in body
    assert re.search(r"\|\s*`NO_NEW_CANDIDATE_HOLD`\s*\|\s*`ACTIVE`\s*\|", body)
    assert "FINAL_RESEARCH_FLEET" in body
    assert "trend_following,bollinger_bands,momentum_1h" in body
    assert "FINAL_RESEARCH_FLEET_BINDINGS_RATIFIED" in body
    assert re.search(r"\|\s*`FINAL_RESEARCH_FLEET_EVALUATION_VERDICT`\s*\|\s*`FAIL`\s*\|", body)
    assert re.search(r"\|\s*`ECONOMIC_EVALUATION_AUTHORIZED`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`RUNTIME_REWIRE_ADMISSIBLE`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`LIVE_AUTHORIZED`\s*\|\s*`false`\s*\|", body)


def test_futures_only_non_bitcoin_scope() -> None:
    body = _read_packet()
    assert re.search(r"\|\s*`FUTURES_ONLY`\s*\|\s*`true`\s*\|", body)
    assert re.search(r"\|\s*`BITCOIN_DIRECTION_ALLOWED`\s*\|\s*`false`\s*\|", body)


def test_unmodified_re_execution_forbidden() -> None:
    body = _read_packet()
    assert "NOT_ADMISSIBLE" in body
    assert "RETRY_UNCHANGED_BINDING_ALLOWED=false" in body
    assert "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0" in body
    assert "Unveränderte Final-Fleet-Re-Execution" in body or "unveränderte Fleet" in body.lower()


def test_layered_semantics_and_scope_not_authorization() -> None:
    body = _read_packet()
    assert "Layered Semantics" in body
    assert "Scope-Ratifikation" in body
    assert "keine** Evaluation-Autorisierung" in body or "keine Evaluation-Autorisierung" in body
    assert "PR #4823" in body


def test_safe_next_action_requests_new_scope_go() -> None:
    body = _read_packet()
    assert (
        "SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
        in body
    )
