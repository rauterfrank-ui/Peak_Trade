"""B2 CURRENT_OFFLINE_MD_BRIDGE_V1 and CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1 tests."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any, Callable

import pytest

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    COMPARISON_CLASS_CONTRACT_TEST_MECHANICS,
    COMPARISON_CLASS_CONTROLLED_FIXTURE,
    COMPARISON_CLASS_PRODUCTIVE_CURRENT,
)
from src.ops.integrated_offline_economic_evidence_v1.current_offline_decision_equivalence_v1 import (
    DecisionEquivalenceVerificationContextV1,
    verify_current_offline_decision_equivalence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.current_offline_md_bridge_v1 import (
    verify_current_offline_md_bridge_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)
from tests.ops.b2_offline_economic_fixture_v1 import (
    build_decision_equivalence_document_v1,
    build_md_bridge_document_v1,
    write_minimal_productive_b2_fixtures,
)
from tests.ops.test_integrated_offline_economic_evidence_b1_identity_v1 import (
    EXPECTED_SHA,
    _minimal_productive_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = write_minimal_productive_b2_fixtures(REPO_ROOT)


def _d(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _valid_md_doc() -> dict[str, Any]:
    return build_md_bridge_document_v1(
        dataset_digest=_FIXTURES["dataset_digest"],
        mapping_digest=_FIXTURES["mapping_digest"],
    )


def _valid_de_doc(*, md_digest: str | None = None) -> dict[str, Any]:
    return build_decision_equivalence_document_v1(
        md_attestation_digest=md_digest or _FIXTURES["md_digest"],
        decision_config_digest=_d("decision_cfg"),
        registry_digest=_d("registry"),
        capital_digest=_d("capital"),
    )


def _productive_de_context(
    *, md_ok: bool = True, identity_ok: bool = True
) -> DecisionEquivalenceVerificationContextV1:
    return DecisionEquivalenceVerificationContextV1(
        identity_binding_verified=identity_ok,
        md_bridge_verified=md_ok,
        declared_equivalence_class=COMPARISON_CLASS_PRODUCTIVE_CURRENT,
    )


def test_md_bridge_positive_mechanics() -> None:
    result = verify_current_offline_md_bridge_v1(bridge_document=_valid_md_doc())
    assert result.bridge_verified is True
    assert not result.blockers


def test_decision_equivalence_contract_test_mechanics() -> None:
    doc = _valid_de_doc()
    doc["equivalence_class"] = COMPARISON_CLASS_CONTRACT_TEST_MECHANICS
    result = verify_current_offline_decision_equivalence_v1(
        equivalence_document=doc,
        context=DecisionEquivalenceVerificationContextV1(
            declared_equivalence_class=COMPARISON_CLASS_CONTRACT_TEST_MECHANICS,
        ),
    )
    assert result.equivalence_verified is True


def test_b2_wired_productive_identity_content_verified() -> None:
    doc = _minimal_productive_index()
    from src.ops.integrated_offline_economic_evidence_v1.canonical_identity_verifier_v1 import (
        verify_canonical_identity_binding_v1,
    )

    result = verify_canonical_identity_binding_v1(
        index_document=doc,
        repo_root=REPO_ROOT,
        expected_proven_source_sha=EXPECTED_SHA,
        expected_canonical_decision_config_digest_sha256=_d("decision_cfg"),
        expected_component_versions_digest_sha256=_d("components"),
        expected_policy_versions_digest_sha256=_d("policies"),
        expected_trading_logic_implementation_binding_digest_sha256=_d("impl_bind"),
        expected_suitability_registry_snapshot_digest_sha256=_d("registry"),
        cap23_residency_gate_enabled=False,
    )
    assert result.verified is True
    assert result.md_bridge_content_verified is True
    assert result.decision_equivalence_content_verified is True


@pytest.mark.parametrize(
    "mutator,needle",
    [
        (
            lambda d: d["current_offline_md_semantics_v1"].update(
                {"canonical_instrument_id": "ETH-ALT"}
            ),
            "CANONICAL_INSTRUMENT_MISMATCH",
        ),
        (
            lambda d: (
                d["current_offline_md_semantics_v1"].update(
                    {"display_symbol": "ETH", "canonical_instrument_id": "ETH-A"}
                )
                or d["offline_dataset_semantics_v1"].update(
                    {"display_symbol": "ETH", "canonical_instrument_id": "ETH-B"}
                )
            ),
            "SAME_DISPLAY_SYMBOL",
        ),
        (
            lambda d: d.update({"dataset_content_digest_sha256": _d("wrong")}),
            "DATASET_CONTENT_DIGEST",
        ),
        (
            lambda d: d.update({"instrument_mapping_digest_sha256": _d("wrong")}),
            "INSTRUMENT_MAPPING_DIGEST",
        ),
        (
            lambda d: d["current_offline_md_semantics_v1"].update({"timeframe": "5m"}),
            "MD_SEMANTIC_MISMATCH:TIMEFRAME",
        ),
        (
            lambda d: d["current_offline_md_semantics_v1"].update(
                {"timestamp_semantics": "wallclock_open"}
            ),
            "MD_SEMANTIC_MISMATCH:TIMESTAMP_SEMANTICS",
        ),
        (lambda d: d.pop("dataset_content_digest_sha256"), "DATASET_CONTENT_DIGEST"),
        (
            lambda d: d["time_range_coverage_v1"].update(
                {"required_end_time": "2026-02-01T00:00:00Z"}
            ),
            "INSUFFICIENT_TIME_RANGE",
        ),
    ],
    ids=[
        "canonical_instrument",
        "display_symbol",
        "dataset_digest",
        "mapping_digest",
        "timeframe",
        "timestamp_semantics",
        "missing_digest",
        "coverage",
    ],
)
def test_md_bridge_adversarial(mutator: Callable[[dict[str, Any]], None], needle: str) -> None:
    doc = _valid_md_doc()
    mutator(doc)
    result = verify_current_offline_md_bridge_v1(
        bridge_document=doc,
        expected_dataset_content_digest_sha256=_FIXTURES["dataset_digest"],
        expected_instrument_mapping_digest_sha256=_FIXTURES["mapping_digest"],
    )
    assert result.bridge_verified is False
    assert any(needle in b for b in result.blockers)


def test_md_bridge_missing_attestation_via_repo() -> None:
    result = verify_current_offline_md_bridge_v1(
        repo_root=REPO_ROOT,
        artifact_relpath="tests/fixtures/ops/missing_md_bridge.json",
    )
    assert result.bridge_verified is False


@pytest.mark.parametrize(
    "mutator,needle",
    [
        (
            lambda d: d["comparison_rows"][0]["decision_input_binding_v1"].update(
                {"decision_config_digest_sha256": _d("other")}
            ),
            "FINGERPRINT_MISMATCH",
        ),
        (
            lambda d: d["comparison_rows"][0]["decision_input_binding_v1"].update(
                {"strategy_registry_snapshot_digest_sha256": _d("other")}
            ),
            "FINGERPRINT_MISMATCH",
        ),
        (
            lambda d: d["comparison_rows"][0]["decision_input_binding_v1"].update(
                {"productive_gate_bindings_digest_sha256": _d("other")}
            ),
            "FINGERPRINT_MISMATCH",
        ),
        (
            lambda d: d["comparison_rows"][0]["decision_input_binding_v1"].update(
                {"capital_context_digest_sha256": _d("other")}
            ),
            "FINGERPRINT_MISMATCH",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update(
                {"selected_strategy_ref": "other"}
            ),
            "SELECTED_STRATEGY_REF",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update({"decision": "HOLD"}),
            "DECISION",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update({"side": "flat"}),
            "SIDE",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update(
                {"double_play_transition": "EXIT"}
            ),
            "DOUBLE_PLAY",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update(
                {"risk_result": "DENY"}
            ),
            "RISK_RESULT",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update(
                {"sizing_result": "ZERO"}
            ),
            "SIZING_RESULT",
        ),
        (
            lambda d: d["comparison_rows"][0]["current_decision_v1"].update(
                {"canonical_order_intent_present": True}
            ),
            "CANONICAL_ORDER_INTENT_PRESENT",
        ),
        (lambda d: d.update({"comparison_rows": []}), "EMPTY_COMPARISON"),
        (
            lambda d: d["comparison_rows"][0].update({"side_comparison_unresolved": True}),
            "UNRESOLVED_REQUIRED",
        ),
        (
            lambda d: d.update(
                {
                    "equivalence_class": COMPARISON_CLASS_CONTROLLED_FIXTURE,
                    "productive_current_claimed": True,
                }
            ),
            "CONTROLLED_FIXTURE_ESCALATED",
        ),
        (lambda d: d.update({"head_bound_correctness_substitution": True}), "HEAD_BOUND"),
        (lambda d: d.update({"step29m_economic_validity_proven": True}), "STEP29M"),
        (lambda d: d.update({"ghv_substitution": True}), "GHV"),
        (lambda d: d.update({"natural_enter_substitution": True}), "NATURAL_ENTER"),
        (lambda d: d.update({"aggregate_equivalence_pass": True}), "AGGREGATE"),
    ],
    ids=[
        "decision_config",
        "strategy_registry",
        "productive_gate",
        "capital_context",
        "selected_strategy",
        "decision",
        "side",
        "double_play",
        "risk",
        "sizing",
        "order_intent",
        "empty_rows",
        "unresolved_row",
        "fixture_escalation",
        "head_bound_sub",
        "step29m_sub",
        "ghv_sub",
        "natural_enter_sub",
        "manual_aggregate",
    ],
)
def test_decision_equivalence_adversarial(
    mutator: Callable[[dict[str, Any]], None], needle: str
) -> None:
    doc = _valid_de_doc()
    mutator(doc)
    eq_class = str(doc.get("equivalence_class") or COMPARISON_CLASS_PRODUCTIVE_CURRENT)
    ctx = DecisionEquivalenceVerificationContextV1(
        identity_binding_verified=True,
        md_bridge_verified=True,
        declared_equivalence_class=eq_class,
    )
    if eq_class == COMPARISON_CLASS_CONTRACT_TEST_MECHANICS:
        ctx = DecisionEquivalenceVerificationContextV1(
            declared_equivalence_class=COMPARISON_CLASS_CONTRACT_TEST_MECHANICS,
        )
    result = verify_current_offline_decision_equivalence_v1(
        equivalence_document=doc,
        context=ctx,
    )
    assert result.equivalence_verified is False
    assert any(needle.split("_")[0] in b or needle in b for b in result.blockers)


def test_productive_decision_equivalence_requires_md_bridge_context() -> None:
    doc = _valid_de_doc()
    result = verify_current_offline_decision_equivalence_v1(
        equivalence_document=doc,
        context=_productive_de_context(md_ok=False),
    )
    assert result.equivalence_verified is False
    assert any("MD_BRIDGE" in b for b in result.blockers)


def test_productive_decision_equivalence_requires_identity_context() -> None:
    doc = _valid_de_doc()
    result = verify_current_offline_decision_equivalence_v1(
        equivalence_document=doc,
        context=_productive_de_context(identity_ok=False),
    )
    assert result.equivalence_verified is False
    assert any("IDENTITY_BINDING" in b for b in result.blockers)


def test_integrated_still_not_complete_without_domains() -> None:
    doc = _minimal_productive_index()
    result = verify_integrated_offline_economic_evidence_v1(
        repo_root=REPO_ROOT,
        index_document=doc,
        expected_proven_source_sha=EXPECTED_SHA,
    )
    assert result.verified is False
    assert result.canonical_identity_verified is True


def test_empty_set_pass_impossible() -> None:
    doc = copy.deepcopy(_valid_de_doc())
    doc["comparison_rows"] = []
    result = verify_current_offline_decision_equivalence_v1(equivalence_document=doc)
    assert result.equivalence_verified is False
    assert result.required_row_count == 0
