"""Phase 7 Canonical Reality Gap Store v1 (research evidence only).

Append-only historical memory of expected-versus-observed research gaps.
This layer reuses Phase 1 Canonical Experiment Identity, Phase 2
``experiment_id`` / ``REJECTED_REALITY_GAP``, and the Phase 3
``REALITY_GAP_GATE`` mapping. It has no runtime, order, live, funding,
canary, promotion, or config-write authority.

Observed-surface labels are not execution authorization. Missing fee,
slippage, funding, or other gap values are never defaulted to zero.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import (
    ARTIFACT_KIND_REPO_RELATIVE,
    ARTIFACT_KIND_STORE_RELATIVE,
    CANONICAL_DISPOSITIONS,
    derive_experiment_id_v1,
)
from src.experiments.canonical_failure_memory_v1 import FAILURE_CLASS_TO_FAILED_GATE
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_reality_gap_store_v1"
REALITY_GAP_DOMAIN: Final[str] = "peak_trade.canonical_reality_gap_store.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVIDENCE_KIND_EXPERIMENT_RECORD: Final[str] = "EXPERIMENT_RECORD"
ARTIFACT_KIND_REPO_RELATIVE_REF: Final[str] = ARTIFACT_KIND_REPO_RELATIVE
ARTIFACT_KIND_STORE_RELATIVE_REF: Final[str] = ARTIFACT_KIND_STORE_RELATIVE

REALITY_GAP_STORE_PRESENT: Final[bool] = True
REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY: Final[bool] = False
REALITY_GAP_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
REALITY_GAP_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
REALITY_GAP_CAN_PROMOTE: Final[bool] = False
REALITY_GAP_CAN_PROMOTE_TO_LIVE: Final[bool] = False
REALITY_GAP_CAN_INCREASE_RISK: Final[bool] = False
REALITY_GAP_CAN_INCREASE_LEVERAGE: Final[bool] = False
REALITY_GAP_CAN_FUND: Final[bool] = False
REALITY_GAP_CAN_SUBMIT_ORDER: Final[bool] = False
REALITY_GAP_CAN_ARM: Final[bool] = False
REALITY_GAP_CAN_ENABLE: Final[bool] = False
REALITY_GAP_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
REALITY_GAP_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
REALITY_GAP_CAN_AUTHORIZE_CANARY: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
OBSERVED_SURFACE_IS_NOT_AUTHORIZATION: Final[bool] = True
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

EXPECTED_SURFACE_RESEARCH: Final[str] = "RESEARCH"
OBSERVED_SURFACE_SHADOW: Final[str] = "SHADOW"
OBSERVED_SURFACE_PAPER_EXCHANGE: Final[str] = "PAPER_EXCHANGE"
OBSERVED_SURFACE_TESTNET: Final[str] = "TESTNET"
OBSERVED_SURFACE_LIVE: Final[str] = "LIVE"
CANONICAL_OBSERVED_SURFACES: Final[tuple[str, ...]] = (
    OBSERVED_SURFACE_SHADOW,
    OBSERVED_SURFACE_PAPER_EXCHANGE,
    OBSERVED_SURFACE_TESTNET,
    OBSERVED_SURFACE_LIVE,
)

DISPOSITION_WITHIN_THRESHOLD: Final[str] = "WITHIN_THRESHOLD"
DISPOSITION_REJECTED_REALITY_GAP: Final[str] = "REJECTED_REALITY_GAP"
FAILED_GATE_NOT_TRIGGERED: Final[str] = "NOT_TRIGGERED"
FAILED_GATE_REALITY_GAP: Final[str] = FAILURE_CLASS_TO_FAILED_GATE[DISPOSITION_REJECTED_REALITY_GAP]
DIMENSION_WITHIN_THRESHOLD: Final[str] = "WITHIN_THRESHOLD"
DIMENSION_EXCEEDS_THRESHOLD: Final[str] = "EXCEEDS_THRESHOLD"

if DISPOSITION_REJECTED_REALITY_GAP not in CANONICAL_DISPOSITIONS:
    raise RuntimeError("REJECTED_REALITY_GAP must remain a Phase 2 disposition")

GAP_DIMENSIONS: Final[tuple[str, ...]] = (
    "fee",
    "slippage",
    "funding",
    "fill",
    "latency",
    "spread",
    "pnl",
)
GAP_DIMENSION_IDENTITY_BINDINGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "fee": "fee_model_digest",
        "slippage": "slippage_model_digest",
        "funding": "funding_model_digest",
    }
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
        "compatible",
        "zero",
    }
)
_CORE_LOGIC_DIGEST_FIELDS: Final[tuple[str, ...]] = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)
_EVIDENCE_KINDS: Final[tuple[str, ...]] = (
    EVIDENCE_KIND_EXPERIMENT_RECORD,
    ARTIFACT_KIND_REPO_RELATIVE_REF,
    ARTIFACT_KIND_STORE_RELATIVE_REF,
)

_LOGGER = logging.getLogger(__name__)


class RealityGapValidationError(ValueError):
    """Fail-closed Canonical Reality Gap Store v1 validation error."""


class RealityGapRecordConflictError(RealityGapValidationError):
    """Same reality_gap_record_id with divergent canonical historical content."""


@dataclass(frozen=True)
class RealityGapDimensionV1:
    name: str
    expected: float
    observed: float
    threshold: float
    unit: str


@dataclass(frozen=True)
class CanonicalRealityGapRecordRequestV1:
    experiment_identity: Mapping[str, Any]
    observed_surface: str
    metric_definitions: str
    threshold_policy_digest: str
    gap_dimensions: Sequence[RealityGapDimensionV1]
    evidence_refs: Sequence[Mapping[str, Any]]
    created_at: str
    expected_surface: str = EXPECTED_SURFACE_RESEARCH
    experiment_id: str | None = None


def build_canonical_reality_gap_record_v1(
    request: CanonicalRealityGapRecordRequestV1,
) -> Mapping[str, Any]:
    identity = _require_identity(request.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if request.experiment_id is not None:
        provided = _require_sha256("experiment_id", request.experiment_id)
        if provided != experiment_id:
            raise RealityGapValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    expected_surface = _require_expected_surface(request.expected_surface)
    observed_surface = _require_observed_surface(request.observed_surface)
    created_at = _require_created_at(request.created_at)
    metric_definitions = _require_token("metric_definitions", request.metric_definitions)
    threshold_policy_digest = _require_sha256(
        "threshold_policy_digest", request.threshold_policy_digest
    )
    dimension_results = _evaluate_dimensions(request.gap_dimensions, identity)
    exceeds = any(item["status"] == DIMENSION_EXCEEDS_THRESHOLD for item in dimension_results)
    overall_disposition = (
        DISPOSITION_REJECTED_REALITY_GAP if exceeds else DISPOSITION_WITHIN_THRESHOLD
    )
    failed_gate = FAILED_GATE_REALITY_GAP if exceeds else FAILED_GATE_NOT_TRIGGERED
    evidence_refs = _canonicalize_evidence_refs(request.evidence_refs, experiment_id)
    body = {
        "canonical_trading_decision_core_bound": True,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "dimension_results": dimension_results,
        "evidence_refs": evidence_refs,
        "expected_surface": expected_surface,
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "failed_gate": failed_gate,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "metric_definitions": metric_definitions,
        "observed_surface": observed_surface,
        "observed_surface_is_not_authorization": OBSERVED_SURFACE_IS_NOT_AUTHORIZATION,
        "overall_disposition": overall_disposition,
        "promotion_authority": PROMOTION_AUTHORITY,
        "reality_gap_can_arm": REALITY_GAP_CAN_ARM,
        "reality_gap_can_authorize_canary": REALITY_GAP_CAN_AUTHORIZE_CANARY,
        "reality_gap_can_create_confirm_token": REALITY_GAP_CAN_CREATE_CONFIRM_TOKEN,
        "reality_gap_can_enable": REALITY_GAP_CAN_ENABLE,
        "reality_gap_can_fund": REALITY_GAP_CAN_FUND,
        "reality_gap_can_increase_leverage": REALITY_GAP_CAN_INCREASE_LEVERAGE,
        "reality_gap_can_increase_risk": REALITY_GAP_CAN_INCREASE_RISK,
        "reality_gap_can_mutate_live_config": REALITY_GAP_CAN_MUTATE_LIVE_CONFIG,
        "reality_gap_can_promote": REALITY_GAP_CAN_PROMOTE,
        "reality_gap_can_promote_to_live": REALITY_GAP_CAN_PROMOTE_TO_LIVE,
        "reality_gap_can_submit_order": REALITY_GAP_CAN_SUBMIT_ORDER,
        "reality_gap_can_use_confirm_token": REALITY_GAP_CAN_USE_CONFIRM_TOKEN,
        "reality_gap_can_write_live_config": REALITY_GAP_CAN_WRITE_LIVE_CONFIG,
        "reality_gap_domain": REALITY_GAP_DOMAIN,
        "reality_gap_store_has_runtime_authority": REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY,
        "reality_gap_store_present": REALITY_GAP_STORE_PRESENT,
        "record_schema_version": SCHEMA_VERSION,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "self_learning_self_authorizing_separation": (SELF_LEARNING_SELF_AUTHORIZING_SEPARATION),
        "threshold_policy_digest": threshold_policy_digest,
    }
    reality_gap_record_id = derive_reality_gap_record_id_v1(body)
    record = dict(body)
    record["reality_gap_record_id"] = reality_gap_record_id
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_reality_gap_record_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_reality_gap_store_v1 built identity=%s disposition=%s surface=%s",
        reality_gap_record_id,
        overall_disposition,
        observed_surface,
    )
    return frozen


def derive_reality_gap_record_id_v1(record_without_ids: Mapping[str, Any]) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{REALITY_GAP_DOMAIN}.reality_gap_record_id",
        "payload": _plain_mapping(record_without_ids),
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def validate_canonical_reality_gap_record_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise RealityGapValidationError("reality gap record must be a mapping")
    record = _plain_mapping(record)
    if record.get("record_schema_version") != SCHEMA_VERSION:
        raise RealityGapValidationError("record_schema_version mismatch")
    if record.get("reality_gap_domain") != REALITY_GAP_DOMAIN:
        raise RealityGapValidationError("reality_gap_domain mismatch")
    if record.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise RealityGapValidationError("non-COMPLETE reality gap records are forbidden")
    if record.get("digest_algorithm") != DIGEST_ALGORITHM:
        raise RealityGapValidationError("digest_algorithm mismatch")
    if record.get("reality_gap_store_present") is not True:
        raise RealityGapValidationError("reality_gap_store_present must be true")
    if record.get("reality_gap_store_has_runtime_authority") is not False:
        raise RealityGapValidationError("reality_gap_store_has_runtime_authority must be false")
    if record.get("reality_gap_can_mutate_live_config") is not False:
        raise RealityGapValidationError("reality_gap_can_mutate_live_config must be false")
    if record.get("reality_gap_can_write_live_config") is not False:
        raise RealityGapValidationError("reality_gap_can_write_live_config must be false")
    if record.get("reality_gap_can_promote") is not False:
        raise RealityGapValidationError("reality_gap_can_promote must be false")
    if record.get("reality_gap_can_promote_to_live") is not False:
        raise RealityGapValidationError("reality_gap_can_promote_to_live must be false")
    if record.get("reality_gap_can_increase_risk") is not False:
        raise RealityGapValidationError("reality_gap_can_increase_risk must be false")
    if record.get("reality_gap_can_increase_leverage") is not False:
        raise RealityGapValidationError("reality_gap_can_increase_leverage must be false")
    if record.get("reality_gap_can_fund") is not False:
        raise RealityGapValidationError("reality_gap_can_fund must be false")
    if record.get("reality_gap_can_submit_order") is not False:
        raise RealityGapValidationError("reality_gap_can_submit_order must be false")
    if record.get("reality_gap_can_arm") is not False:
        raise RealityGapValidationError("reality_gap_can_arm must be false")
    if record.get("reality_gap_can_enable") is not False:
        raise RealityGapValidationError("reality_gap_can_enable must be false")
    if record.get("reality_gap_can_create_confirm_token") is not False:
        raise RealityGapValidationError("reality_gap_can_create_confirm_token must be false")
    if record.get("reality_gap_can_use_confirm_token") is not False:
        raise RealityGapValidationError("reality_gap_can_use_confirm_token must be false")
    if record.get("reality_gap_can_authorize_canary") is not False:
        raise RealityGapValidationError("reality_gap_can_authorize_canary must be false")
    if record.get("learning_may_autonomously_replace_core_logic") is not False:
        raise RealityGapValidationError(
            "learning_may_autonomously_replace_core_logic must be false"
        )
    if record.get("observed_surface_is_not_authorization") is not True:
        raise RealityGapValidationError("observed_surface_is_not_authorization must be true")
    if record.get("self_learning_self_authorizing_separation") is not True:
        raise RealityGapValidationError("self_learning_self_authorizing_separation must be true")
    if record.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise RealityGapValidationError("promotion_authority must be NONE")
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise RealityGapValidationError("runtime_authority_impact must be NONE")
    if record.get("canonical_trading_decision_core_bound") is not True:
        raise RealityGapValidationError("canonical_trading_decision_core_bound must be true")

    identity = _require_identity(record.get("experiment_identity"))
    experiment_id = _require_sha256("experiment_id", record.get("experiment_id"))
    expected_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if experiment_id != expected_id:
        raise RealityGapValidationError(
            "experiment_id is not bound to the Canonical Experiment Identity digest"
        )
    _require_expected_surface(record.get("expected_surface"))
    _require_observed_surface(record.get("observed_surface"))
    _require_created_at(record.get("created_at"))
    _require_token("metric_definitions", record.get("metric_definitions"))
    _require_sha256("threshold_policy_digest", record.get("threshold_policy_digest"))
    _canonicalize_evidence_refs(record.get("evidence_refs"), experiment_id)
    for field_name in _CORE_LOGIC_DIGEST_FIELDS:
        _require_sha256(field_name, identity.get(field_name))
    dimension_results = _require_dimension_results(record.get("dimension_results"), identity)
    exceeds = any(item["status"] == DIMENSION_EXCEEDS_THRESHOLD for item in dimension_results)
    overall = record.get("overall_disposition")
    failed_gate = record.get("failed_gate")
    if exceeds:
        if overall != DISPOSITION_REJECTED_REALITY_GAP:
            raise RealityGapValidationError(
                "overall_disposition must be REJECTED_REALITY_GAP when a gap exceeds threshold"
            )
        if failed_gate != FAILED_GATE_REALITY_GAP:
            raise RealityGapValidationError("failed_gate must be REALITY_GAP_GATE")
    else:
        if overall != DISPOSITION_WITHIN_THRESHOLD:
            raise RealityGapValidationError(
                "overall_disposition must be WITHIN_THRESHOLD when every gap is within threshold"
            )
        if failed_gate != FAILED_GATE_NOT_TRIGGERED:
            raise RealityGapValidationError("failed_gate must be NOT_TRIGGERED")

    body = {
        key: value
        for key, value in record.items()
        if key not in {"reality_gap_record_id", "integrity"}
    }
    expected_record_id = derive_reality_gap_record_id_v1(body)
    if record.get("reality_gap_record_id") != expected_record_id:
        raise RealityGapValidationError("reality_gap_record_id is not bound to canonical content")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    integrity = record.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != (
        expected_integrity
    ):
        raise RealityGapValidationError("integrity.content_sha256 mismatch")


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def freeze_canonical_reality_gap_record_v1(record: Mapping[str, Any]) -> Mapping[str, Any]:
    validate_canonical_reality_gap_record_v1(record)
    return _freeze(canonical_record_payload(record))


def _evaluate_dimensions(
    dimensions: Sequence[RealityGapDimensionV1] | Any,
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(dimensions, Sequence) or isinstance(dimensions, (str, bytes)):
        raise RealityGapValidationError("gap_dimensions must be a sequence")
    if not dimensions:
        raise RealityGapValidationError("at least one gap dimension is required")
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for index, item in enumerate(dimensions):
        if not isinstance(item, RealityGapDimensionV1):
            raise RealityGapValidationError(
                f"gap_dimensions[{index}] must be a RealityGapDimensionV1"
            )
        name = _require_dimension_name(item.name)
        if name in seen:
            raise RealityGapValidationError(f"duplicate gap dimension is forbidden: {name}")
        seen.add(name)
        expected = _require_finite_number(f"gap_dimensions[{index}].expected", item.expected)
        observed = _require_finite_number(f"gap_dimensions[{index}].observed", item.observed)
        threshold = _require_finite_number(f"gap_dimensions[{index}].threshold", item.threshold)
        if threshold < 0:
            raise RealityGapValidationError(f"gap_dimensions[{index}].threshold must be >= 0")
        unit = _require_token(f"gap_dimensions[{index}].unit", item.unit)
        delta = observed - expected
        abs_delta = abs(delta)
        status = (
            DIMENSION_EXCEEDS_THRESHOLD if abs_delta > threshold else DIMENSION_WITHIN_THRESHOLD
        )
        result: dict[str, Any] = {
            "abs_delta": abs_delta,
            "delta": delta,
            "expected": expected,
            "name": name,
            "observed": observed,
            "status": status,
            "threshold": threshold,
            "unit": unit,
        }
        identity_field = GAP_DIMENSION_IDENTITY_BINDINGS.get(name)
        if identity_field is not None:
            result["identity_digest_field"] = identity_field
            result["identity_digest"] = _require_sha256(
                identity_field, identity.get(identity_field)
            )
        results.append(result)
    return results


def _require_dimension_results(value: Any, identity: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RealityGapValidationError("dimension_results must be a sequence")
    if not value:
        raise RealityGapValidationError("at least one gap dimension is required")
    rebuilt: list[RealityGapDimensionV1] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RealityGapValidationError(f"dimension_results[{index}] must be a mapping")
        rebuilt.append(
            RealityGapDimensionV1(
                name=str(item.get("name")),
                expected=_require_finite_number(
                    f"dimension_results[{index}].expected", item.get("expected")
                ),
                observed=_require_finite_number(
                    f"dimension_results[{index}].observed", item.get("observed")
                ),
                threshold=_require_finite_number(
                    f"dimension_results[{index}].threshold", item.get("threshold")
                ),
                unit=str(item.get("unit")),
            )
        )
    expected_results = _evaluate_dimensions(rebuilt, identity)
    actual = [_plain_mapping(item) for item in value]
    if actual != expected_results:
        raise RealityGapValidationError("dimension_results are not canonically derived")
    return expected_results


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RealityGapValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise RealityGapValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise RealityGapValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise RealityGapValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise RealityGapValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise RealityGapValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _require_expected_surface(value: Any) -> str:
    token = _require_token("expected_surface", value)
    if token != EXPECTED_SURFACE_RESEARCH:
        raise RealityGapValidationError("expected_surface must be RESEARCH")
    return token


def _require_observed_surface(value: Any) -> str:
    token = _require_token("observed_surface", value)
    if token not in CANONICAL_OBSERVED_SURFACES:
        raise RealityGapValidationError("observed_surface is unknown or unsupported")
    return token


def _require_dimension_name(value: Any) -> str:
    token = _require_token("gap dimension name", value)
    if token not in GAP_DIMENSIONS:
        raise RealityGapValidationError(f"gap dimension is unknown or unsupported: {token}")
    return token


def _require_finite_number(field_name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RealityGapValidationError(f"{field_name} must be an explicit finite number")
    number = float(value)
    if not math.isfinite(number):
        raise RealityGapValidationError(f"non-finite numeric values are forbidden in {field_name}")
    return number


def _canonicalize_evidence_refs(value: Any, experiment_id: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RealityGapValidationError("evidence_refs must be a sequence")
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    experiment_bound = False
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RealityGapValidationError(f"evidence_refs[{index}] must be a mapping")
        kind = item.get("kind")
        if kind not in _EVIDENCE_KINDS:
            raise RealityGapValidationError(f"evidence_refs[{index}].kind is unsupported")
        digest = _require_sha256(f"evidence_refs[{index}].digest", item.get("digest"))
        if kind == EVIDENCE_KIND_EXPERIMENT_RECORD:
            ref = _require_sha256(f"evidence_refs[{index}].ref", item.get("ref"))
            if ref == experiment_id:
                experiment_bound = True
        else:
            ref = _require_relative_artifact_ref(f"evidence_refs[{index}].ref", item.get("ref"))
        extra_keys = set(str(key) for key in item.keys()) - {"kind", "ref", "digest"}
        if extra_keys:
            raise RealityGapValidationError(
                f"evidence_refs[{index}] has unsupported keys: {sorted(extra_keys)}"
            )
        key = (str(kind), ref)
        if key in seen:
            raise RealityGapValidationError("duplicate evidence_refs are forbidden")
        seen.add(key)
        refs.append({"digest": digest, "kind": kind, "ref": ref})
    if not experiment_bound:
        raise RealityGapValidationError(
            "evidence_refs must include the bound EXPERIMENT_RECORD experiment_id"
        )
    return refs


def _require_relative_artifact_ref(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RealityGapValidationError(f"{field_name} must be a non-empty relative ref")
    ref = value.strip()
    if ref.strip().lower() in _UNAVAILABLE_TOKENS:
        raise RealityGapValidationError(f"{field_name} cannot use implicit unavailable tokens")
    if "\x00" in ref:
        raise RealityGapValidationError(f"{field_name} contains a NUL byte")
    if ref.startswith("/") or ref.startswith("\\") or ref.startswith("~"):
        raise RealityGapValidationError(f"{field_name} absolute or home paths are forbidden")
    if ":" in ref.split("/", 1)[0] and len(ref.split("/", 1)[0]) <= 2:
        raise RealityGapValidationError(f"{field_name} drive-qualified paths are forbidden")
    parts = ref.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RealityGapValidationError(
            f"{field_name} path traversal or empty segments are forbidden"
        )
    if "\\" in ref:
        raise RealityGapValidationError(f"{field_name} must use store-/repo-relative POSIX paths")
    return ref


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


__all__ = [
    "CANONICAL_OBSERVED_SURFACES",
    "CanonicalRealityGapRecordRequestV1",
    "DIGEST_ALGORITHM",
    "DISPOSITION_REJECTED_REALITY_GAP",
    "DISPOSITION_WITHIN_THRESHOLD",
    "EVIDENCE_KIND_EXPERIMENT_RECORD",
    "EXPECTED_SURFACE_RESEARCH",
    "FAILED_GATE_NOT_TRIGGERED",
    "FAILED_GATE_REALITY_GAP",
    "GAP_DIMENSIONS",
    "GAP_DIMENSION_IDENTITY_BINDINGS",
    "OBSERVED_SURFACE_IS_NOT_AUTHORIZATION",
    "OBSERVED_SURFACE_LIVE",
    "OBSERVED_SURFACE_PAPER_EXCHANGE",
    "OBSERVED_SURFACE_SHADOW",
    "OBSERVED_SURFACE_TESTNET",
    "PROMOTION_AUTHORITY",
    "REALITY_GAP_CAN_MUTATE_LIVE_CONFIG",
    "REALITY_GAP_CAN_PROMOTE",
    "REALITY_GAP_DOMAIN",
    "REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY",
    "REALITY_GAP_STORE_PRESENT",
    "RECORD_COMPLETENESS_COMPLETE",
    "RUNTIME_AUTHORITY_IMPACT",
    "RealityGapDimensionV1",
    "RealityGapRecordConflictError",
    "RealityGapValidationError",
    "SCHEMA_VERSION",
    "build_canonical_reality_gap_record_v1",
    "canonical_record_payload",
    "derive_reality_gap_record_id_v1",
    "freeze_canonical_reality_gap_record_v1",
    "validate_canonical_reality_gap_record_v1",
]
