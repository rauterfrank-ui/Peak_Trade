"""Order-Capability demo instrument rules fixture normalizer contract (v1).

Pure offline deterministic fixture/schema normalization and provenance validation
for later demo instrument rules binding. Does not claim provider truth, authorize
network, secrets, orders, cancel, live, preflight lift, or execute.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from src.ops.bounded_futures_private_readonly_contract_v0 import DEMO_FUTURES_HOST
from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_demo_instrument_rules_binding_contract_v1 import (
    AUTHORITY_IMPACT,
    BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE,
    DemoInstrumentOfflineRulesBound,
    FORBIDDEN_SERIALIZATION_KEYS,
)

PACKAGE_MARKER = "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_FIXTURE_NORMALIZER_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_demo_instrument_rules_fixture_normalizer_result.v1"
FIXTURE_SCHEMA_VERSION = "order_capability_demo_instrument_rules_fixture.v1"
REQUIRED_DEMO_HOST = DEMO_FUTURES_HOST
DEFAULT_VENUE = "kraken_futures_demo"

FORBIDDEN_HOST_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
        "futures.kraken.com",
        "private",
        "auth",
    }
)
NOT_ACCEPTABLE_SOURCE_MARKERS = frozenset(
    {
        "chatgpt",
        "llm",
        "memory",
        "operator_memory",
        "screenshot",
        "ui_screenshot",
        "unversioned_notes",
        "notion_chat",
        "private_endpoint",
        "auth_endpoint",
        "live_credentials",
        "prod_credentials",
    }
)

REASON_MISSING_PROVENANCE = "MISSING_PROVENANCE"
REASON_SOURCE_NOT_ACCEPTABLE = "SOURCE_NOT_ACCEPTABLE"
REASON_U5D_NOT_ELEVATED_TO_PROVIDER_TRUTH = "U5D_NOT_ELEVATED_TO_PROVIDER_TRUTH"
REASON_DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED = "DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED"
REASON_VENDOR_DOCS_NOT_VERSIONED = "VENDOR_DOCS_NOT_VERSIONED"
REASON_DEMO_HOST_MISMATCH = "DEMO_HOST_MISMATCH"
REASON_LIVE_HOST_REJECTED = "LIVE_HOST_REJECTED"
REASON_MISSING_MIN_SIZE = "MISSING_MIN_SIZE"
REASON_MISSING_QTY_STEP = "MISSING_QTY_STEP"
REASON_MISSING_PRICE_TICK = "MISSING_PRICE_TICK"
REASON_MISSING_QTY_PRECISION = "MISSING_QTY_PRECISION"
REASON_MISSING_PRICE_PRECISION = "MISSING_PRICE_PRECISION"
REASON_MISSING_CAP_FEASIBILITY_RULE = "MISSING_CAP_FEASIBILITY_RULE"
REASON_SECRET_MATERIAL_REJECTED = "SECRET_MATERIAL_REJECTED"
REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS = "FORBIDDEN_ENDPOINT_CANCELALLORDERS"
REASON_FORBIDDEN_ENDPOINT_BATCHORDER = "FORBIDDEN_ENDPOINT_BATCHORDER"
REASON_UNSAFE_AUTHORITY_FLAGS = "UNSAFE_AUTHORITY_FLAGS"
REASON_INCOMPLETE_PROVENANCE = "INCOMPLETE_PROVENANCE"
REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE = "PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE"
REASON_TICKSIZE_CONFLICT_UNRESOLVED = "TICKSIZE_CONFLICT_UNRESOLVED"
REASON_CANDIDATE_FIELD_REJECTED_MAPPING = "CANDIDATE_FIELD_REJECTED_MAPPING"
REASON_PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE = (
    "PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE"
)

BROWSER_RENDER_DISPOSITION_KEY = "browser_render_disposition_v1"
REJECTED_MAPPING_IMPACT_MID_TO_MIN_SIZE = "impactMidSize→min_size"
REJECTED_MAPPING_CONTRACT_SIZE_TO_QTY_STEP = "contractSize→qty_step"
BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE = "browser_rendered_vendor_docs_snapshot"


class FixtureNormalizerError(ValueError):
    """Fail-closed fixture normalizer evaluation or validation error."""


class FixtureSourceClass(str, Enum):
    ACCEPTABLE_LATER_WITH_GO = "ACCEPTABLE_LATER_WITH_GO"
    ACCEPTABLE_IF_VERSIONED = "ACCEPTABLE_IF_VERSIONED"
    ACCEPTABLE_SYNTHETIC_ONLY_FOR_TESTS = "ACCEPTABLE_SYNTHETIC_ONLY_FOR_TESTS"
    REPO_VERSIONED_FIXTURE = "REPO_VERSIONED_FIXTURE"
    NOT_ACCEPTABLE = "NOT_ACCEPTABLE"


class FixtureNormalizerVerdictKind(str, Enum):
    SCHEMA_VALID = "SCHEMA_VALID"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class DemoInstrumentRulesFixtureProvenance:
    source_type: str
    source_uri_or_origin: str
    captured_at: str
    captured_by_flow: str
    network_authorized_by_go_token: str
    raw_payload_hash: str
    normalized_payload_hash: str
    schema_version: str
    venue: str
    host: str
    instrument: str
    value_redacted: bool = True
    no_secret_material: bool = True
    repo_versioned: bool = False


@dataclass(frozen=True)
class DemoInstrumentRulesNormalizedFields:
    min_size: Decimal | None = None
    qty_step: Decimal | None = None
    price_tick: Decimal | None = None
    qty_precision: int | None = None
    price_precision: int | None = None
    min_notional: Decimal | None = None
    cap_feasibility_rule: str | None = None


@dataclass(frozen=True)
class DemoInstrumentRulesFixtureNormalizerInput:
    source_class: FixtureSourceClass
    provenance: DemoInstrumentRulesFixtureProvenance | None = None
    rules: DemoInstrumentRulesNormalizedFields | None = None
    raw_payload: dict[str, Any] | None = None
    cancelallorders: bool = False
    batchorder: bool = False
    execute_authorized: bool = False
    order_authorized: bool = False
    cancel_authorized: bool = False


@dataclass(frozen=True)
class DemoInstrumentRulesFixtureNormalizerResult:
    verdict: FixtureNormalizerVerdictKind
    schema_valid: bool
    provider_truth_bound: bool
    min_size_verified_offline: bool
    blocker_min_size_not_verified_offline: bool
    cap_feasible_without_provider_rules: bool
    operator_side_qty_price_decision_prep_allowed_next: bool
    demo_mutation_execute_allowed_now: bool
    order_authorized_now: bool
    cancel_authorized_now: bool
    execute_authorized_now: bool
    live_authorized_now: bool
    arming_authorized_now: bool
    preflight_lift_authorized_now: bool
    authority_impact: str
    reason_codes: tuple[str, ...]
    violations: tuple[str, ...]
    blockers: tuple[str, ...]
    value_redacted: bool
    no_secret_material: bool
    cancelallorders_allowed: bool
    batchorder_allowed: bool
    deterministic_summary_hash: str
    normalized_payload_hash: str


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_host(host: str) -> str:
    normalized = _normalize(host)
    if normalized.startswith("https://"):
        normalized = normalized[len("https://") :]
    if normalized.startswith("http://"):
        normalized = normalized[len("http://") :]
    return normalized.split("/", 1)[0]


def _contains_forbidden_marker(value: str, markers: frozenset[str]) -> bool:
    normalized = _normalize(value)
    return any(marker in normalized for marker in markers)


def _positive_decimal(value: Decimal | None) -> bool:
    if value is None:
        return False
    try:
        return value > 0
    except Exception:
        return False


def classify_source_type_marker(source_type: str) -> FixtureSourceClass:
    normalized = _normalize(source_type).replace(" ", "_")
    if not normalized or _contains_forbidden_marker(normalized, NOT_ACCEPTABLE_SOURCE_MARKERS):
        return FixtureSourceClass.NOT_ACCEPTABLE
    if normalized in {"u5d_as_provider_truth", "provider_truth_from_u5d"}:
        return FixtureSourceClass.NOT_ACCEPTABLE
    if normalized in {
        "acceptable_later_with_go",
        "demo_public_endpoint_snapshot",
        "public_demo_endpoint_snapshot",
    }:
        return FixtureSourceClass.ACCEPTABLE_LATER_WITH_GO
    if normalized in {
        "acceptable_if_versioned",
        "vendor_docs_snapshot",
        "exchange_docs_snapshot",
        "browser_rendered_vendor_docs_snapshot",
    }:
        return FixtureSourceClass.ACCEPTABLE_IF_VERSIONED
    if normalized in {
        "acceptable_synthetic_only_for_tests",
        "synthetic_test_only",
        "synthetic_offline_fixture_only_not_exchange_truth",
    }:
        return FixtureSourceClass.ACCEPTABLE_SYNTHETIC_ONLY_FOR_TESTS
    if normalized in {
        "repo_versioned_fixture",
        "u5d_offline_transform",
        "u5d_repo_fixture",
    }:
        return FixtureSourceClass.REPO_VERSIONED_FIXTURE
    return FixtureSourceClass.NOT_ACCEPTABLE


def compute_canonical_payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_deterministic_summary_hash(
    *,
    source_class: FixtureSourceClass,
    provenance: DemoInstrumentRulesFixtureProvenance | None,
    rules: DemoInstrumentRulesNormalizedFields | None,
) -> str:
    summary: dict[str, Any] = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "source_class": source_class.value,
        "provenance": None,
        "rules": None,
    }
    if provenance is not None:
        summary["provenance"] = {
            "captured_at": provenance.captured_at,
            "captured_by_flow": provenance.captured_by_flow,
            "host": provenance.host,
            "instrument": provenance.instrument,
            "network_authorized_by_go_token": provenance.network_authorized_by_go_token,
            "normalized_payload_hash": provenance.normalized_payload_hash,
            "raw_payload_hash": provenance.raw_payload_hash,
            "repo_versioned": provenance.repo_versioned,
            "schema_version": provenance.schema_version,
            "source_type": provenance.source_type,
            "source_uri_or_origin": provenance.source_uri_or_origin,
            "venue": provenance.venue,
        }
    if rules is not None:
        summary["rules"] = {
            "cap_feasibility_rule": rules.cap_feasibility_rule,
            "min_notional": str(rules.min_notional) if rules.min_notional is not None else None,
            "min_size": str(rules.min_size) if rules.min_size is not None else None,
            "price_precision": rules.price_precision,
            "price_tick": str(rules.price_tick) if rules.price_tick is not None else None,
            "qty_precision": rules.qty_precision,
            "qty_step": str(rules.qty_step) if rules.qty_step is not None else None,
        }
    return compute_canonical_payload_hash(summary)


def reject_secret_like_mapping(mapping: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in mapping:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            reasons.append(REASON_SECRET_MATERIAL_REJECTED)
        lowered = key.lower()
        if lowered.startswith("authorization") or lowered in {"env", "env_value", "auth_header"}:
            reasons.append(REASON_SECRET_MATERIAL_REJECTED)
    return reasons


def _validate_provenance_complete(
    provenance: DemoInstrumentRulesFixtureProvenance | None,
) -> list[str]:
    if provenance is None:
        return [REASON_MISSING_PROVENANCE]
    reasons: list[str] = []
    required_strings = (
        provenance.source_type,
        provenance.source_uri_or_origin,
        provenance.captured_at,
        provenance.captured_by_flow,
        provenance.network_authorized_by_go_token,
        provenance.raw_payload_hash,
        provenance.normalized_payload_hash,
        provenance.schema_version,
        provenance.venue,
        provenance.host,
        provenance.instrument,
    )
    if not all(str(value).strip() for value in required_strings):
        reasons.append(REASON_INCOMPLETE_PROVENANCE)
    if not provenance.value_redacted or not provenance.no_secret_material:
        reasons.append(REASON_SECRET_MATERIAL_REJECTED)
    return reasons


def _validate_host_for_provider_truth_claim(
    provenance: DemoInstrumentRulesFixtureProvenance,
) -> list[str]:
    normalized = _normalize_host(provenance.host)
    if not normalized:
        return [REASON_DEMO_HOST_MISMATCH]
    if normalized == REQUIRED_DEMO_HOST:
        return []
    if _contains_forbidden_marker(normalized, FORBIDDEN_HOST_MARKERS):
        return [REASON_LIVE_HOST_REJECTED]
    return [REASON_DEMO_HOST_MISMATCH]


def _validate_rules_complete(rules: DemoInstrumentRulesNormalizedFields | None) -> list[str]:
    if rules is None:
        return [
            REASON_MISSING_MIN_SIZE,
            REASON_MISSING_QTY_STEP,
            REASON_MISSING_PRICE_TICK,
            REASON_MISSING_QTY_PRECISION,
            REASON_MISSING_PRICE_PRECISION,
            REASON_MISSING_CAP_FEASIBILITY_RULE,
        ]
    reasons: list[str] = []
    if not _positive_decimal(rules.min_size):
        reasons.append(REASON_MISSING_MIN_SIZE)
    if not _positive_decimal(rules.qty_step):
        reasons.append(REASON_MISSING_QTY_STEP)
    if not _positive_decimal(rules.price_tick):
        reasons.append(REASON_MISSING_PRICE_TICK)
    if rules.qty_precision is None or rules.qty_precision < 0:
        reasons.append(REASON_MISSING_QTY_PRECISION)
    if rules.price_precision is None or rules.price_precision < 0:
        reasons.append(REASON_MISSING_PRICE_PRECISION)
    has_cap_rule = rules.min_notional is not None or bool(
        (rules.cap_feasibility_rule or "").strip()
    )
    if not has_cap_rule:
        reasons.append(REASON_MISSING_CAP_FEASIBILITY_RULE)
    return reasons


def _validate_source_class_policy(
    *,
    source_class: FixtureSourceClass,
    provenance: DemoInstrumentRulesFixtureProvenance | None,
) -> list[str]:
    reasons: list[str] = []
    if source_class == FixtureSourceClass.NOT_ACCEPTABLE:
        reasons.append(REASON_SOURCE_NOT_ACCEPTABLE)
        return reasons

    if source_class == FixtureSourceClass.REPO_VERSIONED_FIXTURE:
        reasons.append(REASON_U5D_NOT_ELEVATED_TO_PROVIDER_TRUTH)
        reasons.append(REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE)

    if source_class == FixtureSourceClass.ACCEPTABLE_SYNTHETIC_ONLY_FOR_TESTS:
        reasons.append(REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE)

    if source_class == FixtureSourceClass.ACCEPTABLE_LATER_WITH_GO:
        token = provenance.network_authorized_by_go_token if provenance else ""
        if not token or token.upper() in {"NONE", ""}:
            reasons.append(REASON_DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED)
        reasons.append(REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE)

    if source_class == FixtureSourceClass.ACCEPTABLE_IF_VERSIONED:
        if provenance is None or not provenance.repo_versioned:
            reasons.append(REASON_VENDOR_DOCS_NOT_VERSIONED)
        reasons.append(REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE)

    if provenance is not None:
        classified = classify_source_type_marker(provenance.source_type)
        if classified == FixtureSourceClass.NOT_ACCEPTABLE:
            reasons.append(REASON_SOURCE_NOT_ACCEPTABLE)
        if _contains_forbidden_marker(provenance.source_type, NOT_ACCEPTABLE_SOURCE_MARKERS):
            reasons.append(REASON_SOURCE_NOT_ACCEPTABLE)
        if _contains_forbidden_marker(
            provenance.source_uri_or_origin, NOT_ACCEPTABLE_SOURCE_MARKERS
        ):
            reasons.append(REASON_SOURCE_NOT_ACCEPTABLE)

    return reasons


def _validate_unsafe_flags(inp: DemoInstrumentRulesFixtureNormalizerInput) -> list[str]:
    if inp.execute_authorized or inp.order_authorized or inp.cancel_authorized:
        return [REASON_UNSAFE_AUTHORITY_FLAGS]
    return []


def _validate_forbidden_endpoints(inp: DemoInstrumentRulesFixtureNormalizerInput) -> list[str]:
    reasons: list[str] = []
    if inp.cancelallorders:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS)
    if inp.batchorder:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_BATCHORDER)
    return reasons


def _is_browser_rendered_vendor_docs_source(
    provenance: DemoInstrumentRulesFixtureProvenance | None,
) -> bool:
    if provenance is None:
        return False
    normalized = _normalize(provenance.source_type).replace(" ", "_")
    return normalized == BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE


def _candidate_decimal_value(candidate: object) -> Decimal | None:
    if not isinstance(candidate, dict):
        return None
    value = candidate.get("value")
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except Exception:
        return None
    return parsed if parsed > 0 else None


def _validate_browser_rendered_candidate_disposition(
    *,
    raw_payload: dict[str, Any] | None,
    rules: DemoInstrumentRulesNormalizedFields | None,
    provenance: DemoInstrumentRulesFixtureProvenance | None,
) -> list[str]:
    """Fail-closed guards for browser-rendered vendor doc candidate evidence."""
    if not _is_browser_rendered_vendor_docs_source(provenance):
        return []

    reasons: list[str] = [REASON_PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE]
    if raw_payload is None:
        return reasons

    disposition = raw_payload.get(BROWSER_RENDER_DISPOSITION_KEY)
    if not isinstance(disposition, dict):
        return reasons

    rejected = disposition.get("rejected_mappings")
    rejected_mappings = rejected if isinstance(rejected, list) else []

    candidates = disposition.get("candidate_fields")
    candidate_fields = candidates if isinstance(candidates, dict) else {}

    impact_mid_size = _candidate_decimal_value(candidate_fields.get("impact_mid_size_candidate"))
    contract_size = _candidate_decimal_value(candidate_fields.get("contract_size_candidate"))

    if rules is not None:
        if (
            REJECTED_MAPPING_IMPACT_MID_TO_MIN_SIZE in rejected_mappings
            and rules.min_size is not None
            and impact_mid_size is not None
            and rules.min_size == impact_mid_size
        ):
            reasons.append(REASON_CANDIDATE_FIELD_REJECTED_MAPPING)
        if (
            REJECTED_MAPPING_CONTRACT_SIZE_TO_QTY_STEP in rejected_mappings
            and rules.qty_step is not None
            and contract_size is not None
            and rules.qty_step == contract_size
        ):
            reasons.append(REASON_CANDIDATE_FIELD_REJECTED_MAPPING)

    if disposition.get("ticksize_conflict") is True:
        if rules is not None and rules.price_tick is not None:
            if not disposition.get("ticksize_conflict_resolved"):
                reasons.append(REASON_TICKSIZE_CONFLICT_UNRESOLVED)

    return reasons


def _immutable_authority_result(
    *,
    verdict: FixtureNormalizerVerdictKind,
    schema_valid: bool,
    reason_codes: list[str],
    deterministic_summary_hash: str,
    normalized_payload_hash: str,
    value_redacted: bool,
    no_secret_material: bool,
    cancelallorders: bool,
    batchorder: bool,
) -> DemoInstrumentRulesFixtureNormalizerResult:
    deduped = tuple(dict.fromkeys(reason_codes))
    blockers: list[str] = []
    if not schema_valid or REASON_PROVIDER_TRUTH_NOT_CLAIMED_IN_THIS_SLICE in deduped:
        blockers.append(BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE)
    elif any(
        code
        in {
            REASON_MISSING_MIN_SIZE,
            REASON_MISSING_QTY_STEP,
            REASON_MISSING_PRICE_TICK,
            REASON_MISSING_QTY_PRECISION,
            REASON_MISSING_PRICE_PRECISION,
        }
        for code in deduped
    ):
        blockers.append(BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE)
    else:
        blockers.append(BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE)

    return DemoInstrumentRulesFixtureNormalizerResult(
        verdict=verdict,
        schema_valid=schema_valid,
        provider_truth_bound=False,
        min_size_verified_offline=False,
        blocker_min_size_not_verified_offline=True,
        cap_feasible_without_provider_rules=False,
        operator_side_qty_price_decision_prep_allowed_next=False,
        demo_mutation_execute_allowed_now=False,
        order_authorized_now=False,
        cancel_authorized_now=False,
        execute_authorized_now=False,
        live_authorized_now=False,
        arming_authorized_now=False,
        preflight_lift_authorized_now=False,
        authority_impact=AUTHORITY_IMPACT,
        reason_codes=deduped,
        violations=deduped,
        blockers=tuple(dict.fromkeys(blockers)),
        value_redacted=value_redacted,
        no_secret_material=no_secret_material,
        cancelallorders_allowed=False,
        batchorder_allowed=False,
        deterministic_summary_hash=deterministic_summary_hash,
        normalized_payload_hash=normalized_payload_hash,
    )


def evaluate_demo_instrument_rules_fixture_normalization(
    inp: DemoInstrumentRulesFixtureNormalizerInput,
) -> DemoInstrumentRulesFixtureNormalizerResult:
    """Evaluate fixture provenance and normalized rule fields without claiming provider truth."""
    reasons: list[str] = []

    reasons.extend(_validate_unsafe_flags(inp))
    reasons.extend(_validate_forbidden_endpoints(inp))

    if inp.raw_payload is not None:
        reasons.extend(reject_secret_like_mapping(inp.raw_payload))

    reasons.extend(
        _validate_browser_rendered_candidate_disposition(
            raw_payload=inp.raw_payload,
            rules=inp.rules,
            provenance=inp.provenance,
        )
    )

    reasons.extend(_validate_provenance_complete(inp.provenance))
    reasons.extend(
        _validate_source_class_policy(source_class=inp.source_class, provenance=inp.provenance)
    )

    if inp.provenance is not None:
        reasons.extend(_validate_host_for_provider_truth_claim(inp.provenance))
        if not inp.provenance.value_redacted or not inp.provenance.no_secret_material:
            reasons.append(REASON_SECRET_MATERIAL_REJECTED)

    rule_reasons = _validate_rules_complete(inp.rules)
    reasons.extend(rule_reasons)

    deterministic_summary_hash = compute_deterministic_summary_hash(
        source_class=inp.source_class,
        provenance=inp.provenance,
        rules=inp.rules,
    )
    normalized_payload_hash = (
        inp.provenance.normalized_payload_hash
        if inp.provenance is not None and inp.provenance.normalized_payload_hash.strip()
        else deterministic_summary_hash
    )

    schema_blocking_reasons = {
        REASON_MISSING_PROVENANCE,
        REASON_INCOMPLETE_PROVENANCE,
        REASON_SOURCE_NOT_ACCEPTABLE,
        REASON_SECRET_MATERIAL_REJECTED,
        REASON_UNSAFE_AUTHORITY_FLAGS,
        REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS,
        REASON_FORBIDDEN_ENDPOINT_BATCHORDER,
        REASON_DEMO_HOST_MISMATCH,
        REASON_LIVE_HOST_REJECTED,
        REASON_DEMO_ENDPOINT_SNAPSHOT_GO_NOT_AUTHORIZED,
        REASON_VENDOR_DOCS_NOT_VERSIONED,
        REASON_TICKSIZE_CONFLICT_UNRESOLVED,
        REASON_CANDIDATE_FIELD_REJECTED_MAPPING,
        REASON_PROVIDER_TRUTH_NOT_CLAIMED_FROM_RENDERED_DOC_EXAMPLE,
    }
    schema_valid = not rule_reasons and not any(code in schema_blocking_reasons for code in reasons)

    if schema_valid:
        return _immutable_authority_result(
            verdict=FixtureNormalizerVerdictKind.SCHEMA_VALID,
            schema_valid=True,
            reason_codes=reasons,
            deterministic_summary_hash=deterministic_summary_hash,
            normalized_payload_hash=normalized_payload_hash,
            value_redacted=True,
            no_secret_material=True,
            cancelallorders=inp.cancelallorders,
            batchorder=inp.batchorder,
        )

    return _immutable_authority_result(
        verdict=FixtureNormalizerVerdictKind.FAIL_CLOSED,
        schema_valid=False,
        reason_codes=reasons,
        deterministic_summary_hash=deterministic_summary_hash,
        normalized_payload_hash=normalized_payload_hash,
        value_redacted=True,
        no_secret_material=True,
        cancelallorders=inp.cancelallorders,
        batchorder=inp.batchorder,
    )


def map_normalizer_to_binding_offline_rules(
    result: DemoInstrumentRulesFixtureNormalizerResult,
    *,
    rules: DemoInstrumentRulesNormalizedFields | None,
    source_ref: str,
) -> DemoInstrumentOfflineRulesBound:
    """Map normalizer output to binding contract offline rules without authority lift."""
    if rules is None or not result.schema_valid or result.provider_truth_bound:
        return DemoInstrumentOfflineRulesBound(
            min_size=None,
            qty_step=None,
            price_tick=None,
            qty_precision=None,
            price_precision=None,
            min_notional=None,
            offline_bound=False,
            source_ref=source_ref,
        )
    return DemoInstrumentOfflineRulesBound(
        min_size=rules.min_size,
        qty_step=rules.qty_step,
        price_tick=rules.price_tick,
        qty_precision=rules.qty_precision,
        price_precision=rules.price_precision,
        min_notional=rules.min_notional,
        offline_bound=False,
        source_ref=source_ref,
    )


def serialize_demo_instrument_rules_fixture_normalizer_result(
    result: DemoInstrumentRulesFixtureNormalizerResult,
) -> dict[str, Any]:
    validate_demo_instrument_rules_fixture_normalizer_result(result)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": result.verdict.value,
        "schema_valid": result.schema_valid,
        "provider_truth_bound": result.provider_truth_bound,
        "min_size_verified_offline": result.min_size_verified_offline,
        "blocker_min_size_not_verified_offline": result.blocker_min_size_not_verified_offline,
        "cap_feasible_without_provider_rules": result.cap_feasible_without_provider_rules,
        "operator_side_qty_price_decision_prep_allowed_next": (
            result.operator_side_qty_price_decision_prep_allowed_next
        ),
        "demo_mutation_execute_allowed_now": result.demo_mutation_execute_allowed_now,
        "order_authorized_now": result.order_authorized_now,
        "cancel_authorized_now": result.cancel_authorized_now,
        "execute_authorized_now": result.execute_authorized_now,
        "live_authorized_now": result.live_authorized_now,
        "arming_authorized_now": result.arming_authorized_now,
        "preflight_lift_authorized_now": result.preflight_lift_authorized_now,
        "authority_impact": result.authority_impact,
        "reason_codes": list(result.reason_codes),
        "violations": list(result.violations),
        "blockers": list(result.blockers),
        "value_redacted": result.value_redacted,
        "no_secret_material": result.no_secret_material,
        "cancelallorders_allowed": result.cancelallorders_allowed,
        "batchorder_allowed": result.batchorder_allowed,
        "deterministic_summary_hash": result.deterministic_summary_hash,
        "normalized_payload_hash": result.normalized_payload_hash,
        "required_demo_host": REQUIRED_DEMO_HOST,
        "default_instrument_reference": DEFAULT_INSTRUMENT,
    }
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise FixtureNormalizerError(
                f"serialized result must not include forbidden key {key!r}"
            )
    return data


def validate_demo_instrument_rules_fixture_normalizer_result(
    result: DemoInstrumentRulesFixtureNormalizerResult,
) -> None:
    if result.authority_impact != AUTHORITY_IMPACT:
        raise FixtureNormalizerError("authority_impact must remain NO_AUTHORITY_CHANGE")
    if result.provider_truth_bound:
        raise FixtureNormalizerError("provider_truth_bound must remain false in this slice")
    if result.min_size_verified_offline:
        raise FixtureNormalizerError("min_size_verified_offline must remain false in this slice")
    if not result.blocker_min_size_not_verified_offline:
        raise FixtureNormalizerError("blocker_min_size_not_verified_offline must remain true")
    if result.cap_feasible_without_provider_rules:
        raise FixtureNormalizerError("cap_feasible_without_provider_rules must remain false")
    if (
        result.order_authorized_now
        or result.cancel_authorized_now
        or result.execute_authorized_now
        or result.demo_mutation_execute_allowed_now
        or result.live_authorized_now
        or result.arming_authorized_now
        or result.preflight_lift_authorized_now
        or result.operator_side_qty_price_decision_prep_allowed_next
    ):
        raise FixtureNormalizerError("authority flags must remain false")
    if not result.value_redacted or not result.no_secret_material:
        raise FixtureNormalizerError("value_redacted and no_secret_material must remain true")
    if result.cancelallorders_allowed or result.batchorder_allowed:
        raise FixtureNormalizerError("cancelallorders and batchorder must remain disallowed")
    if result.verdict == FixtureNormalizerVerdictKind.SCHEMA_VALID and not result.schema_valid:
        raise FixtureNormalizerError("SCHEMA_VALID requires schema_valid=true")
    if result.verdict == FixtureNormalizerVerdictKind.FAIL_CLOSED and result.schema_valid:
        raise FixtureNormalizerError("FAIL_CLOSED requires schema_valid=false")
