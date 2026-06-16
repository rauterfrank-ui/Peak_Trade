"""Offline tests for order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_demo_instrument_rules_binding_contract_v1 import (
    ALLOWED_CREDENTIAL_CLASS,
    AUTHORITY_IMPACT,
    BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE,
    DemoInstrumentRulesBindingVerdictKind,
    REASON_OFFLINE_RULES_NOT_BOUND,
    REQUIRED_DEMO_HOST,
    OrderCapabilityDemoInstrumentRulesBindingInput,
    evaluate_order_capability_demo_instrument_rules_binding,
)
from src.ops.order_capability_demo_instrument_rules_fixture_normalizer_contract_v1 import (
    AUTHORITY_IMPACT as NORMALIZER_AUTHORITY_IMPACT,
    BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE as NORMALIZER_BLOCKER,
    FIXTURE_SCHEMA_VERSION,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED,
    REASON_DEMO_HOST_MISMATCH,
    REASON_FORBIDDEN_ENDPOINT_BATCHORDER,
    REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS,
    REASON_INCOMPLETE_PROVENANCE,
    REASON_LIVE_HOST_REJECTED,
    REASON_MISSING_MIN_SIZE,
    REASON_MISSING_PRICE_PRECISION,
    REASON_MISSING_PRICE_TICK,
    REASON_MISSING_PROVENANCE,
    REASON_MISSING_QTY_PRECISION,
    REASON_MISSING_QTY_STEP,
    REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE,
    REASON_PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE,
    REASON_CANDIDATE_FIELD_REJECTED_MAPPING,
    REASON_TICKSIZE_CONFLICT_UNRESOLVED,
    BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE,
    REASON_SECRET_MATERIAL_REJECTED,
    REASON_SOURCE_NOT_ACCEPTABLE,
    REASON_U5D_NOT_ELEVATED_TO_PROVIDER_TRUTH,
    REASON_UNSAFE_AUTHORITY_FLAGS,
    REASON_VENDOR_DOCS_NOT_VERSIONED,
    DemoInstrumentRulesFixtureNormalizerInput,
    DemoInstrumentRulesFixtureProvenance,
    DemoInstrumentRulesNormalizedFields,
    FixtureNormalizerError,
    FixtureNormalizerVerdictKind,
    FixtureSourceClass,
    classify_source_type_marker,
    compute_canonical_payload_hash,
    compute_deterministic_summary_hash,
    evaluate_demo_instrument_rules_fixture_normalization,
    map_normalizer_to_binding_offline_rules,
    reject_secret_like_mapping,
    serialize_demo_instrument_rules_fixture_normalizer_result,
    validate_demo_instrument_rules_fixture_normalizer_result,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.py"
)

ROOT = Path(__file__).resolve().parents[2]
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
CROSSLINK_PACKAGE_MARKER = "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_NORMALIZER_DOCS_TRUTH_MAP_STATIC_CROSSLINK_GUARD_V1=true"
CONTRACT_REL = "src/ops/order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.py"
TEST_REL = "tests/ops/test_order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.py"
FIXTURE_REL = (
    "tests/fixtures/order_capability/browser_rendered_vendor_docs_pf_xbtusd_candidate.v1.json"
)

TEST_PACKAGE_MARKER = (
    "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_NORMALIZER_CONTRACT_V1_TEST=true"
)
OPERATOR_GO = "GO_ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_SCHEMA_NORMALIZER_CONTRACT_IMPL_TESTS_ONLY_NO_RUN_V1"

U5D_INSTRUMENTS_FIXTURE = (
    "tests/fixtures/u5d_offline_transform_v1/minimal/kraken_futures_instruments.raw.v1.json"
)
FIXED_CAPTURED_AT = "2026-06-10T08:01:30Z"
FIXED_RAW_HASH = "a" * 64
FIXED_NORMALIZED_HASH = "b" * 64
BROWSER_RENDER_GO = (
    "GO_ORDER_CAPABILITY_BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_EXECUTE_WEB_READONLY_V1"
)
BROWSER_RENDER_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "order_capability"
    / "browser_rendered_vendor_docs_pf_xbtusd_candidate.v1.json"
)
BROWSER_RENDER_RAW_HASH = "bb600b9f8cd649d8fb8765a482c2b2f976a0bb63d71ee775462250e6fe6bb47f"


def _complete_rules(**overrides: object) -> DemoInstrumentRulesNormalizedFields:
    base = {
        "min_size": Decimal("0.001"),
        "qty_step": Decimal("0.001"),
        "price_tick": Decimal("0.5"),
        "qty_precision": 3,
        "price_precision": 1,
        "min_notional": None,
        "cap_feasibility_rule": "min_size_times_reference_price",
    }
    base.update(overrides)
    return DemoInstrumentRulesNormalizedFields(**base)


def _complete_provenance(**overrides: object) -> DemoInstrumentRulesFixtureProvenance:
    base = {
        "source_type": "acceptable_synthetic_only_for_tests",
        "source_uri_or_origin": "tests/fixtures/synthetic/demo_rules.v1.json",
        "captured_at": FIXED_CAPTURED_AT,
        "captured_by_flow": "SYNTHETIC_TEST_FIXTURE",
        "network_authorized_by_go_token": "NONE",
        "raw_payload_hash": FIXED_RAW_HASH,
        "normalized_payload_hash": FIXED_NORMALIZED_HASH,
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "venue": "kraken_futures_demo",
        "host": REQUIRED_DEMO_HOST,
        "instrument": DEFAULT_INSTRUMENT,
        "value_redacted": True,
        "no_secret_material": True,
        "repo_versioned": False,
    }
    base.update(overrides)
    return DemoInstrumentRulesFixtureProvenance(**base)


def _synthetic_input(**overrides: object) -> DemoInstrumentRulesFixtureNormalizerInput:
    base = {
        "source_class": FixtureSourceClass.ACCEPTABLE_SYNTHETIC_ONLY_FOR_TESTS,
        "provenance": _complete_provenance(),
        "rules": _complete_rules(),
        "raw_payload": None,
        "cancelallorders": False,
        "batchorder": False,
        "execute_authorized": False,
        "order_authorized": False,
        "cancel_authorized": False,
    }
    base.update(overrides)
    return DemoInstrumentRulesFixtureNormalizerInput(**base)


def _browser_render_disposition_payload(**overrides: object) -> dict[str, object]:
    payload = json.loads(BROWSER_RENDER_FIXTURE.read_text(encoding="utf-8"))
    if overrides:
        payload.update(overrides)
    return payload


def _browser_render_provenance(**overrides: object) -> DemoInstrumentRulesFixtureProvenance:
    base = {
        "source_type": BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE,
        "source_uri_or_origin": (
            "docs.kraken.com/api-reference/instrument-details/get-instruments"
        ),
        "captured_at": FIXED_CAPTURED_AT,
        "captured_by_flow": "browser_render_execute_web_readonly_v1",
        "network_authorized_by_go_token": BROWSER_RENDER_GO,
        "raw_payload_hash": BROWSER_RENDER_RAW_HASH,
        "normalized_payload_hash": FIXED_NORMALIZED_HASH,
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "venue": "kraken_futures_demo",
        "host": REQUIRED_DEMO_HOST,
        "instrument": DEFAULT_INSTRUMENT,
        "value_redacted": True,
        "no_secret_material": True,
        "repo_versioned": True,
    }
    base.update(overrides)
    return DemoInstrumentRulesFixtureProvenance(**base)


def _browser_render_input(**overrides: object) -> DemoInstrumentRulesFixtureNormalizerInput:
    base = {
        "source_class": FixtureSourceClass.ACCEPTABLE_IF_VERSIONED,
        "provenance": _browser_render_provenance(),
        "rules": None,
        "raw_payload": _browser_render_disposition_payload(),
        "cancelallorders": False,
        "batchorder": False,
        "execute_authorized": False,
        "order_authorized": False,
        "cancel_authorized": False,
    }
    base.update(overrides)
    return DemoInstrumentRulesFixtureNormalizerInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert OPERATOR_GO
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_missing_provenance_fail_closed() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input(provenance=None))
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert result.schema_valid is False
    assert REASON_MISSING_PROVENANCE in result.reason_codes
    assert result.provider_truth_bound is False
    assert result.blocker_min_size_not_verified_offline is True
    validate_demo_instrument_rules_fixture_normalizer_result(result)


@pytest.mark.parametrize(
    "source_type",
    [
        "chatgpt_memory",
        "operator_memory",
        "ui_screenshot",
        "unversioned_notes",
        "llm_generated",
    ],
)
def test_not_acceptable_sources_fail_closed(source_type: str) -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(
            source_class=FixtureSourceClass.NOT_ACCEPTABLE,
            provenance=_complete_provenance(source_type=source_type),
        )
    )
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert REASON_SOURCE_NOT_ACCEPTABLE in result.reason_codes
    assert classify_source_type_marker(source_type) == FixtureSourceClass.NOT_ACCEPTABLE


def test_u5d_repo_fixture_not_elevated_to_provider_truth() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(
            source_class=FixtureSourceClass.REPO_VERSIONED_FIXTURE,
            provenance=_complete_provenance(
                source_type="u5d_offline_transform",
                source_uri_or_origin=U5D_INSTRUMENTS_FIXTURE,
                captured_by_flow="U5D_OFFLINE_TRANSFORM",
                repo_versioned=True,
            ),
            rules=_complete_rules(qty_step=None),
        )
    )
    assert result.provider_truth_bound is False
    assert result.min_size_verified_offline is False
    assert REASON_U5D_NOT_ELEVATED_TO_PROVIDER_TRUTH in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_QTY_STEP in result.reason_codes


def test_synthetic_complete_fixture_schema_valid_without_provider_truth() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input())
    assert result.verdict == FixtureNormalizerVerdictKind.SCHEMA_VALID
    assert result.schema_valid is True
    assert result.provider_truth_bound is False
    assert result.min_size_verified_offline is False
    assert result.blocker_min_size_not_verified_offline is True
    assert REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE in result.reason_codes
    validate_demo_instrument_rules_fixture_normalizer_result(result)


def test_demo_endpoint_snapshot_without_go_not_bound() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(
            source_class=FixtureSourceClass.ACCEPTABLE_LATER_WITH_GO,
            provenance=_complete_provenance(
                source_type="demo_public_endpoint_snapshot",
                network_authorized_by_go_token="NONE",
            ),
        )
    )
    assert result.provider_truth_bound is False
    assert REASON_DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


def test_vendor_docs_snapshot_requires_versioning() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(
            source_class=FixtureSourceClass.ACCEPTABLE_IF_VERSIONED,
            provenance=_complete_provenance(
                source_type="vendor_docs_snapshot",
                repo_versioned=False,
            ),
        )
    )
    assert REASON_VENDOR_DOCS_NOT_VERSIONED in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert result.provider_truth_bound is False


@pytest.mark.parametrize(
    "field,reason",
    [
        ("min_size", REASON_MISSING_MIN_SIZE),
        ("qty_step", REASON_MISSING_QTY_STEP),
        ("price_tick", REASON_MISSING_PRICE_TICK),
        ("qty_precision", REASON_MISSING_QTY_PRECISION),
        ("price_precision", REASON_MISSING_PRICE_PRECISION),
    ],
)
def test_missing_rule_fields_block_min_size_verified_offline(field: str, reason: str) -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(rules=_complete_rules(**{field: None}))
    )
    assert result.min_size_verified_offline is False
    assert result.blocker_min_size_not_verified_offline is True
    assert reason in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


def test_demo_host_required_for_schema_valid() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(provenance=_complete_provenance(host=""))
    )
    assert REASON_DEMO_HOST_MISMATCH in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


@pytest.mark.parametrize(
    "host,reason",
    [
        ("futures.kraken.com", REASON_LIVE_HOST_REJECTED),
        ("live-futures.kraken.com", REASON_LIVE_HOST_REJECTED),
        ("private.auth.kraken.com", REASON_LIVE_HOST_REJECTED),
    ],
)
def test_live_prod_private_auth_sources_fail_closed(host: str, reason: str) -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(provenance=_complete_provenance(host=host))
    )
    assert reason in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


def test_secret_like_fields_rejected() -> None:
    reasons = reject_secret_like_mapping({"api_key": "x", "authorization": "Bearer x"})
    assert REASON_SECRET_MATERIAL_REJECTED in reasons
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(raw_payload={"api_secret": "redacted"})
    )
    assert REASON_SECRET_MATERIAL_REJECTED in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


def test_deterministic_summary_hash_stable() -> None:
    inp = _synthetic_input()
    first = evaluate_demo_instrument_rules_fixture_normalization(inp)
    second = evaluate_demo_instrument_rules_fixture_normalization(inp)
    assert first.deterministic_summary_hash == second.deterministic_summary_hash
    assert first.normalized_payload_hash == second.normalized_payload_hash
    expected = compute_deterministic_summary_hash(
        source_class=inp.source_class,
        provenance=inp.provenance,
        rules=inp.rules,
    )
    assert first.deterministic_summary_hash == expected
    payload_hash = compute_canonical_payload_hash(
        {"instrument": DEFAULT_INSTRUMENT, "z": 1, "a": 2}
    )
    assert len(payload_hash) == 64


def test_authority_flags_remain_false_and_no_authority_change() -> None:
    ok = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input())
    bad = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input(provenance=None))
    for result in (ok, bad):
        assert result.authority_impact == NORMALIZER_AUTHORITY_IMPACT == AUTHORITY_IMPACT
        assert result.order_authorized_now is False
        assert result.cancel_authorized_now is False
        assert result.execute_authorized_now is False
        assert result.demo_mutation_execute_allowed_now is False
        assert result.live_authorized_now is False
        assert result.arming_authorized_now is False
        assert result.preflight_lift_authorized_now is False
        assert result.operator_side_qty_price_decision_prep_allowed_next is False
        assert result.cap_feasible_without_provider_rules is False
        validate_demo_instrument_rules_fixture_normalizer_result(result)


def test_cancelallorders_and_batchorder_forbidden() -> None:
    cancel_all = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(cancelallorders=True)
    )
    batch = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input(batchorder=True))
    assert REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS in cancel_all.reason_codes
    assert cancel_all.cancelallorders_allowed is False
    assert REASON_FORBIDDEN_ENDPOINT_BATCHORDER in batch.reason_codes
    assert batch.batchorder_allowed is False


def test_unsafe_authority_flags_fail_closed() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(execute_authorized=True)
    )
    assert REASON_UNSAFE_AUTHORITY_FLAGS in result.reason_codes
    assert result.execute_authorized_now is False


def test_incomplete_provenance_fail_closed() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _synthetic_input(
            provenance=_complete_provenance(source_uri_or_origin="", raw_payload_hash="")
        )
    )
    assert REASON_INCOMPLETE_PROVENANCE in result.reason_codes
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED


def test_serialization_no_forbidden_keys() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input())
    data = serialize_demo_instrument_rules_fixture_normalizer_result(result)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS


def test_validate_result_rejects_tampered_provider_truth() -> None:
    ok = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input())
    bad = type(ok)(
        verdict=ok.verdict,
        schema_valid=ok.schema_valid,
        provider_truth_bound=True,
        min_size_verified_offline=ok.min_size_verified_offline,
        blocker_min_size_not_verified_offline=ok.blocker_min_size_not_verified_offline,
        cap_feasible_without_provider_rules=ok.cap_feasible_without_provider_rules,
        operator_side_qty_price_decision_prep_allowed_next=ok.operator_side_qty_price_decision_prep_allowed_next,
        demo_mutation_execute_allowed_now=ok.demo_mutation_execute_allowed_now,
        order_authorized_now=ok.order_authorized_now,
        cancel_authorized_now=ok.cancel_authorized_now,
        execute_authorized_now=ok.execute_authorized_now,
        live_authorized_now=ok.live_authorized_now,
        arming_authorized_now=ok.arming_authorized_now,
        preflight_lift_authorized_now=ok.preflight_lift_authorized_now,
        authority_impact=ok.authority_impact,
        reason_codes=ok.reason_codes,
        violations=ok.violations,
        blockers=ok.blockers,
        value_redacted=ok.value_redacted,
        no_secret_material=ok.no_secret_material,
        cancelallorders_allowed=ok.cancelallorders_allowed,
        batchorder_allowed=ok.batchorder_allowed,
        deterministic_summary_hash=ok.deterministic_summary_hash,
        normalized_payload_hash=ok.normalized_payload_hash,
    )
    with pytest.raises(FixtureNormalizerError):
        validate_demo_instrument_rules_fixture_normalizer_result(bad)


def test_integration_normalizer_output_feeds_binding_without_authority_lift() -> None:
    normalizer_result = evaluate_demo_instrument_rules_fixture_normalization(_synthetic_input())
    assert normalizer_result.schema_valid is True
    assert normalizer_result.provider_truth_bound is False

    offline_rules = map_normalizer_to_binding_offline_rules(
        normalizer_result,
        rules=_complete_rules(),
        source_ref="synthetic_offline_fixture_only_not_exchange_truth",
    )
    assert offline_rules.offline_bound is False

    binding_result = evaluate_order_capability_demo_instrument_rules_binding(
        OrderCapabilityDemoInstrumentRulesBindingInput(
            demo_host=REQUIRED_DEMO_HOST,
            credential_class=ALLOWED_CREDENTIAL_CLASS,
            instrument=DEFAULT_INSTRUMENT,
            offline_rules=offline_rules,
            cap_max_notional_eur=Decimal("10.0"),
            reference_price_usd=Decimal("100.0"),
            fx_rate_usd_per_eur=Decimal("1.0"),
        )
    )
    assert binding_result.verdict == DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED
    assert REASON_OFFLINE_RULES_NOT_BOUND in binding_result.reason_codes
    assert binding_result.min_size_verified_offline is False
    assert binding_result.blocker_min_size_not_verified_offline is True
    assert BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE in binding_result.blockers
    assert NORMALIZER_BLOCKER in normalizer_result.blockers
    assert binding_result.execute_authorized_now is False
    assert binding_result.operator_side_qty_price_decision_prep_allowed_next is False


def test_no_execution_risk_layer_imports() -> None:
    tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src.execution")
                assert not alias.name.startswith("src.risk_layer")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src.execution")
            assert not node.module.startswith("src.risk_layer")


def test_browser_rendered_vendor_docs_snapshot_source_type_accepted_candidate_only() -> None:
    assert (
        classify_source_type_marker(BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE)
        == FixtureSourceClass.ACCEPTABLE_IF_VERSIONED
    )
    result = evaluate_demo_instrument_rules_fixture_normalization(_browser_render_input())
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert result.provider_truth_bound is False
    assert REASON_PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE in result.reason_codes
    assert REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE in result.reason_codes
    assert REASON_MISSING_MIN_SIZE in result.reason_codes
    assert REASON_MISSING_QTY_STEP in result.reason_codes


def test_browser_rendered_impactmidsize_cannot_map_to_min_size() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(
            rules=_complete_rules(
                min_size=Decimal("1"),
                qty_step=None,
                price_tick=None,
                qty_precision=None,
                price_precision=None,
                cap_feasibility_rule=None,
            )
        )
    )
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert REASON_CANDIDATE_FIELD_REJECTED_MAPPING in result.reason_codes
    assert result.provider_truth_bound is False


def test_browser_rendered_contractsize_cannot_map_to_qty_step() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(
            rules=_complete_rules(
                min_size=None,
                qty_step=Decimal("1"),
                price_tick=None,
                qty_precision=None,
                price_precision=None,
                cap_feasibility_rule=None,
            )
        )
    )
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert REASON_CANDIDATE_FIELD_REJECTED_MAPPING in result.reason_codes
    assert result.provider_truth_bound is False


def test_browser_rendered_contractsize_may_remain_contract_size_candidate() -> None:
    payload = _browser_render_disposition_payload()
    disposition = payload["browser_render_disposition_v1"]
    assert disposition["candidate_fields"]["contract_size_candidate"]["value"] == "1"
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(rules=None, raw_payload=payload)
    )
    assert REASON_CANDIDATE_FIELD_REJECTED_MAPPING not in result.reason_codes
    assert result.provider_truth_bound is False


def test_browser_rendered_ticksize_conflict_fail_closed() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(
            rules=_complete_rules(
                min_size=None,
                qty_step=None,
                price_tick=Decimal("1"),
                qty_precision=None,
                price_precision=None,
                cap_feasibility_rule=None,
            )
        )
    )
    assert result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED
    assert REASON_TICKSIZE_CONFLICT_UNRESOLVED in result.reason_codes
    assert result.provider_truth_bound is False


def test_browser_rendered_missing_min_size_blocks_provider_truth() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(
            rules=_complete_rules(
                min_size=None,
                qty_step=Decimal("0.001"),
                price_tick=Decimal("0.5"),
            )
        )
    )
    assert REASON_MISSING_MIN_SIZE in result.reason_codes
    assert result.min_size_verified_offline is False
    assert result.provider_truth_bound is False


def test_browser_rendered_missing_qty_step_blocks_provider_truth() -> None:
    result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input(
            rules=_complete_rules(
                min_size=Decimal("0.001"),
                qty_step=None,
                price_tick=Decimal("0.5"),
            )
        )
    )
    assert REASON_MISSING_QTY_STEP in result.reason_codes
    assert result.provider_truth_bound is False


def test_browser_rendered_provider_truth_bound_remains_false_no_binding_pass() -> None:
    normalizer_result = evaluate_demo_instrument_rules_fixture_normalization(
        _browser_render_input()
    )
    assert normalizer_result.provider_truth_bound is False
    assert normalizer_result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED

    offline_rules = map_normalizer_to_binding_offline_rules(
        normalizer_result,
        rules=None,
        source_ref=BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE,
    )
    assert offline_rules.offline_bound is False

    binding_result = evaluate_order_capability_demo_instrument_rules_binding(
        OrderCapabilityDemoInstrumentRulesBindingInput(
            demo_host=REQUIRED_DEMO_HOST,
            credential_class=ALLOWED_CREDENTIAL_CLASS,
            instrument=DEFAULT_INSTRUMENT,
            offline_rules=offline_rules,
            cap_max_notional_eur=Decimal("10.0"),
            reference_price_usd=Decimal("100.0"),
            fx_rate_usd_per_eur=Decimal("1.0"),
        )
    )
    assert binding_result.verdict == DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED
    assert REASON_OFFLINE_RULES_NOT_BOUND in binding_result.reason_codes
    assert binding_result.instrument_rules_offline_bound is False
    assert binding_result.min_size_verified_offline is False
    assert BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE in binding_result.blockers


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_order_capability_demo_instrument_rules_fixture_normalizer_crosslink_package_marker_v1() -> (
    None
):
    text = Path(__file__).read_text(encoding="utf-8")
    assert CROSSLINK_PACKAGE_MARKER in text


def test_docs_truth_map_order_capability_demo_instrument_rules_fixture_normalizer_chronicle_v1() -> (
    None
):
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Order-Capability demo instrument rules fixture normalizer DOCS_TRUTH_MAP static crosslink guard v1",
    )
    for required in (
        CONTRACT_REL,
        TEST_REL,
        FIXTURE_REL,
        "#4091",
        "#4094",
        "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_NORMALIZER_CROSSLINK_GUARD_IMPLEMENTED=true",
        "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED=true",
        "BROWSER_RENDERED_VENDOR_DOCS_CANDIDATE_ONLY=true",
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "CANCEL_EXECUTE_AUTHORIZATION_CREATED=false",
        "non-authorizing",
        "parked/read-only",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_order_capability_demo_instrument_rules_fixture_normalizer_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Order-Capability demo instrument rules fixture normalizer DOCS_TRUTH_MAP static crosslink v1"
    )
    section_text = ci_audit[section_start : section_start + 4000]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_NORMALIZER_CROSSLINK_GUARD_IMPLEMENTED=true",
        "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED=true",
        "BROWSER_RENDERED_VENDOR_DOCS_CANDIDATE_ONLY=true",
        "PROVIDER_TRUTH_BOUND=false",
        "PR4091_ANCHOR_REFERENCED=true",
        "PR4094_ANCHOR_REFERENCED=true",
        CONTRACT_REL,
        TEST_REL,
        FIXTURE_REL,
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "CANCEL_EXECUTE_AUTHORIZATION_CREATED=false",
        "READY_FOR_OPERATOR_ARMING_CHANGED=false",
        "non-authorizing",
        "parked/read-only",
    ):
        assert required.lower() in section_text.lower()


def test_order_capability_demo_instrument_rules_fixture_normalizer_contract_referenced_in_docs_v1() -> (
    None
):
    assert CONTRACT_MODULE.is_file()
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert CONTRACT_REL in truth_map
    assert CONTRACT_REL in ci_audit


def test_order_capability_demo_instrument_rules_fixture_normalizer_tests_referenced_in_docs_v1() -> (
    None
):
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert TEST_REL in truth_map
    assert TEST_REL in ci_audit
