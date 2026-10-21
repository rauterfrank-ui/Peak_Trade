"""Offline contract tests for the read-only H1 decision-publication consumer."""

from __future__ import annotations

import ast
import hashlib
import socket
from dataclasses import replace
from pathlib import Path

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    EVIDENCE_SCHEMA_VERSION,
    CanonicalTradingDecisionEvidenceV1,
    compute_canonical_trading_decision_evidence_semantic_digest,
    derive_decision_id,
)

from src.ops.canonical_decision_archive_sibling_exporter_v1.constants_v1 import (
    REQUIRED_EVIDENCE_FIELDS,
    SOURCE_EVIDENCE_SCHEMA_VERSION,
)
from src.ops.h1_decision_publication_consumer_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    PUBLICATION_REQUIRED_FIELDS,
    REASON_ACCEPTED,
    REASON_CONTRADICTORY_DECISION_FIELDS,
    REASON_DIGEST_MISMATCH,
    REASON_EPOCH_MISMATCH,
    REASON_INSTRUMENT_MISMATCH,
    REASON_MISSING_REQUIRED_FIELD,
)
from src.ops.h1_decision_publication_consumer_v1.read_v1 import read_decision_publication_v1

_PACKAGE = Path("src/ops/h1_decision_publication_consumer_v1")
_FORBIDDEN_IMPORT_PREFIXES = (
    "trading.master_v2.double_play",
    "trading.master_v2.integrated_offline",
    "src.trading.master_v2.double_play",
    "src.trading.master_v2.integrated_offline",
    "src.execution",
    "execution",
    "src.risk",
    "risk",
)
_FORBIDDEN_CALLS = ("socket", "urlopen", "write_text", "mkdir", "subprocess")


def _publication(
    *,
    outcome: str,
    instrument_id: str = "ETH-USDT-SWAP",
    trading_epoch: int = 7,
    **overrides: object,
) -> CanonicalTradingDecisionEvidenceV1:
    replay_id = "h1-foundation-01-replay"
    input_digest = hashlib.sha256(b"h1-foundation-01-input").hexdigest()
    decision_id = derive_decision_id(
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        input_digest=input_digest,
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        market_context_ref="market-context-ref",
        scope_initialization_ref="scope-init-ref",
        scope_event_ref="scope-event-ref",
        bull_assessment_ref="bull-assessment-ref",
        bear_assessment_ref="bear-assessment-ref",
        state_switch_ref="state-switch-ref",
        bull_survival_ref="bull-survival-ref",
        bear_survival_ref="bear-survival-ref",
        bull_suitability_ref="bull-suitability-ref",
        bear_suitability_ref="bear-suitability-ref",
        composition_result_ref="composition-ref",
        entry_exit_policy_ref="entry-exit-ref",
        current_scope_ref="current-scope-ref",
        next_scope_ref="next-scope-ref",
        previous_direction_state="flat",
        next_direction_state="flat",
        selected_side="NONE",
        selected_strategy_ref="strategy-ref",
        decision_outcome=outcome,
        entry_or_exit_policy_ref="entry-exit-ref",
        reason_codes=("publication_observed",),
        decision_precedence_trace=("published",),
        component_versions={"canonical_trading_decision_evidence": "v1"},
        policy_versions={"evidence_schema": "v1"},
        config_digest=hashlib.sha256(b"h1-foundation-01-config").hexdigest(),
        implementation_digest=hashlib.sha256(b"h1-foundation-01-implementation").hexdigest(),
        input_digest=input_digest,
        semantic_digest="0" * 64,
        execution_eligible=False,
        authority_effect="NONE",
        order_effect="NONE",
    )
    if overrides:
        evidence = replace(evidence, **overrides)
    digest = compute_canonical_trading_decision_evidence_semantic_digest(evidence)
    return replace(evidence, semantic_digest=digest)


def _snapshot(evidence: CanonicalTradingDecisionEvidenceV1) -> tuple[object, ...]:
    return (
        evidence.decision_id,
        evidence.instrument_id,
        evidence.trading_epoch,
        evidence.decision_outcome,
        evidence.execution_eligible,
        evidence.authority_effect,
        evidence.order_effect,
        evidence.semantic_digest,
        evidence.reason_codes,
    )


def test_public_evidence_contract_fields_remain_the_publication_boundary() -> None:
    assert SOURCE_EVIDENCE_SCHEMA_VERSION == EVIDENCE_SCHEMA_VERSION
    assert set(REQUIRED_EVIDENCE_FIELDS).issubset(PUBLICATION_REQUIRED_FIELDS)


def test_valid_publication_is_unchanged() -> None:
    evidence = _publication(outcome="exit")
    before = _snapshot(evidence)
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is True
    assert result.reason_code == REASON_ACCEPTED
    assert result.evidence is evidence
    assert _snapshot(evidence) == before
    assert result.decision_outcome == "exit"


def test_no_action_publication_is_preserved() -> None:
    evidence = _publication(outcome="no_action")
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is True
    assert result.decision_outcome == "no_action"
    assert evidence.decision_outcome == "no_action"
    assert evidence.execution_eligible is False


def test_exit_publication_is_preserved() -> None:
    evidence = _publication(outcome="exit")
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is True
    assert result.decision_outcome == "exit"
    assert result.evidence is evidence


def test_missing_required_field_fails_closed() -> None:
    evidence = _publication(outcome="no_action")
    payload = {
        "decision_id": evidence.decision_id,
        "replay_id": evidence.replay_id,
        "instrument_id": evidence.instrument_id,
        "trading_epoch": evidence.trading_epoch,
        "next_direction_state": evidence.next_direction_state,
        "evidence_schema_version": evidence.evidence_schema_version,
        "input_digest": evidence.input_digest,
        "semantic_digest": evidence.semantic_digest,
    }
    result = read_decision_publication_v1(
        payload,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is False
    assert result.reason_code == REASON_MISSING_REQUIRED_FIELD
    assert result.evidence is None


def test_contradictory_decision_fields_fail_closed() -> None:
    evidence = _publication(outcome="no_action")
    publication = {
        "decision_outcome": "exit",
        "decision_id": evidence.decision_id,
        "evidence": {
            "decision_outcome": evidence.decision_outcome,
            "decision_id": evidence.decision_id,
        },
    }
    result = read_decision_publication_v1(
        publication,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is False
    assert result.reason_code == REASON_CONTRADICTORY_DECISION_FIELDS
    assert result.evidence is None
    assert evidence.decision_outcome == "no_action"


def test_instrument_mismatch_fails_closed() -> None:
    evidence = _publication(outcome="exit", instrument_id="ETH-USDT-SWAP")
    before = _snapshot(evidence)
    result = read_decision_publication_v1(
        evidence,
        instrument_id="BTC-USDT-SWAP",
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is False
    assert result.reason_code == REASON_INSTRUMENT_MISMATCH
    assert result.evidence is evidence
    assert _snapshot(evidence) == before


def test_epoch_mismatch_fails_closed() -> None:
    evidence = _publication(outcome="exit", trading_epoch=7)
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=6,
    )
    assert result.accepted is False
    assert result.reason_code == REASON_EPOCH_MISMATCH
    assert evidence.trading_epoch == 7


def test_digest_mismatch_fails_closed() -> None:
    evidence = _publication(outcome="exit")
    tampered = replace(evidence, semantic_digest="1" * 64)
    before = _snapshot(tampered)
    result = read_decision_publication_v1(
        tampered,
        instrument_id=tampered.instrument_id,
        trading_epoch=tampered.trading_epoch,
    )
    assert result.accepted is False
    assert result.reason_code == REASON_DIGEST_MISMATCH
    assert result.evidence is tampered
    assert _snapshot(tampered) == before


def test_consumer_takes_no_trading_authority() -> None:
    evidence = _publication(
        outcome="exit",
        authority_effect="GRANT",
        order_effect="SUBMIT",
        execution_eligible=True,
    )
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    assert result.accepted is True
    assert result.consumer_authority_effect == AUTHORITY_EFFECT == "NONE"
    assert result.consumer_order_effect == "NONE"
    assert result.external_effect_authorized is False
    assert result.post_allowed is False
    assert result.trading_authority_change is False
    assert result.productive_cycle_binding == "NONE"
    assert evidence.authority_effect == "GRANT"
    assert evidence.execution_eligible is True
    assert evidence.order_effect == "SUBMIT"


def test_read_creates_no_state_or_external_effect(tmp_path: Path, monkeypatch) -> None:
    evidence = _publication(outcome="no_action")
    before = tuple(sorted(path.name for path in tmp_path.iterdir()))

    def _refuse_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("external effect")

    def _refuse_write(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("state write")

    monkeypatch.setattr(socket, "create_connection", _refuse_network)
    monkeypatch.setattr(Path, "write_text", _refuse_write)
    monkeypatch.setattr(Path, "write_bytes", _refuse_write)
    monkeypatch.setattr(Path, "mkdir", _refuse_write)
    result = read_decision_publication_v1(
        evidence,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
    )
    after = tuple(sorted(path.name for path in tmp_path.iterdir()))
    assert result.accepted is True
    assert result.state_write == "NONE"
    assert result.external_effect_authorized is False
    assert after == before


def test_consumer_package_does_not_import_protected_producers() -> None:
    for path in _PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                assert not name.startswith(_FORBIDDEN_IMPORT_PREFIXES)
            if isinstance(node, ast.Call):
                rendered = ast.unparse(node.func)
                assert not any(token in rendered for token in _FORBIDDEN_CALLS)
