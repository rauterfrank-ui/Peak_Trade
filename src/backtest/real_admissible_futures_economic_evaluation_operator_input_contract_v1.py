"""
Real admissible futures economic evaluation operator input contract v1 (STEP 29M).

Fail-closed, offline, non-authorizing contract that specifies and validates the
operator inputs required before any real admissible futures economic evaluation.
Does not fetch data, run evaluation, or claim profitability.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DATASET_SCHEMA_VERSION,
    DEFAULT_DATASET_VERSION,
)
from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EXECUTION_MODEL_VERSION,
    FEE_MODEL_VERSION,
    SLIPPAGE_MODEL_VERSION,
)
from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_VERSION,
    canonical_economic_validity_policy_v1,
)
from src.backtest.funding_model_v1 import FUNDING_MODEL_VERSION

CONTRACT_VERSION = "real_admissible_futures_economic_evaluation_operator_input_contract_v1"
CONTRACT_OWNER = "backtest.real_admissible_futures_economic_evaluation_operator_input_contract_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/real_admissible_futures_economic_evaluation_operator_input_contract_v1.json"
)
RUNNER_OWNER = "scripts.ops.run_economic_viability_evidence_evaluation_v1"

_URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_FORBIDDEN_PROVENANCE_SUBSTRINGS = frozenset(
    {"kraken", "fixture", "webui", "probe", "preview", "transport"}
)
_FORBIDDEN_SOURCE_TYPES = frozenset(
    {
        "spot",
        "synthetic_spot",
        "synthetic_contract_fixture",
        "test_fixture",
        "preview",
        "preview_data",
        "probe",
        "probe_data",
        "transport_fixture",
        "transport",
        "webui_fixture",
        "webui",
    }
)
_FORBIDDEN_GENERATION_MARKERS = frozenset(
    {
        "deterministic_test_fixture",
        "test_fixture",
        "probe",
        "preview",
        "transport_fixture",
        "webui_fixture",
    }
)


class OperatorInputContractError(ValueError):
    """Fail-closed operator input contract error."""


class OperatorInputResolutionClass(str, Enum):
    CANONICALLY_BOUND = "CANONICALLY_BOUND"
    DETERMINISTICALLY_DERIVABLE = "DETERMINISTICALLY_DERIVABLE"
    OPERATOR_REQUIRED = "OPERATOR_REQUIRED"
    BLOCKED_NO_EVIDENCE = "BLOCKED_NO_EVIDENCE"
    POLICY_GAP = "POLICY_GAP"


class OperatorInputReadinessVerdict(str, Enum):
    OPERATOR_INPUT_CONTRACT_COMPLETE = "OPERATOR_INPUT_CONTRACT_COMPLETE"
    REAL_ADMISSIBLE_EVIDENCE_ALREADY_PRESENT_BUT_UNBOUND = (
        "REAL_ADMISSIBLE_EVIDENCE_ALREADY_PRESENT_BUT_UNBOUND"
    )
    NO_REAL_ADMISSIBLE_EVIDENCE_PRESENT = "NO_REAL_ADMISSIBLE_EVIDENCE_PRESENT"
    BLOCKED_BY_CANONICAL_POLICY_GAP = "BLOCKED_BY_CANONICAL_POLICY_GAP"


@dataclass(frozen=True)
class OperatorInputFieldSpecV1:
    field_name: str
    data_type: str
    required: bool
    resolved: bool
    resolution_class: OperatorInputResolutionClass
    canonical_default: Any
    source_owner: str
    rationale: str
    safety_effect: str
    economic_effect: str
    constraints: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "data_type": self.data_type,
            "required": self.required,
            "resolved": self.resolved,
            "resolution_class": self.resolution_class.value,
            "canonical_default": self.canonical_default,
            "source_owner": self.source_owner,
            "rationale": self.rationale,
            "safety_effect": self.safety_effect,
            "economic_effect": self.economic_effect,
            "constraints": dict(self.constraints),
        }


@dataclass(frozen=True)
class OperatorInputReadinessResultV1:
    contract_version: str
    owner: str
    verdict: OperatorInputReadinessVerdict
    admissibility_verdict: str
    operator_input_contract_complete: bool
    real_evaluation_permitted: bool
    profitability_claim_allowed: bool
    unresolved_operator_fields: tuple[str, ...]
    blocked_no_evidence_fields: tuple[str, ...]
    policy_gap_fields: tuple[str, ...]
    resolved_field_count: int
    required_field_count: int
    reason_codes: tuple[str, ...]
    futures_only: bool
    bitcoin_direction_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "owner": self.owner,
            "verdict": self.verdict.value,
            "admissibility_verdict": self.admissibility_verdict,
            "operator_input_contract_complete": self.operator_input_contract_complete,
            "real_evaluation_permitted": self.real_evaluation_permitted,
            "profitability_claim_allowed": self.profitability_claim_allowed,
            "unresolved_operator_fields": list(self.unresolved_operator_fields),
            "blocked_no_evidence_fields": list(self.blocked_no_evidence_fields),
            "policy_gap_fields": list(self.policy_gap_fields),
            "resolved_field_count": self.resolved_field_count,
            "required_field_count": self.required_field_count,
            "reason_codes": list(self.reason_codes),
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
        }


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def default_contract_config_path(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / CONTRACT_CONFIG_REL_PATH


def load_operator_input_contract_v1(
    path: Optional[Path] = None,
    *,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    contract_path = path or default_contract_config_path(repo_root)
    if not contract_path.is_file():
        raise OperatorInputContractError(f"contract_file_missing:{contract_path}")
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OperatorInputContractError(f"contract_invalid_json:{contract_path}") from exc
    if not isinstance(payload, dict):
        raise OperatorInputContractError("contract_not_object")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise OperatorInputContractError("contract_version_mismatch")
    if payload.get("owner") != CONTRACT_OWNER:
        raise OperatorInputContractError("contract_owner_mismatch")
    fields = payload.get("fields")
    if not isinstance(fields, list) or not fields:
        raise OperatorInputContractError("contract_fields_missing")
    return payload


def parse_operator_input_field_specs_v1(
    contract: Mapping[str, Any],
) -> tuple[OperatorInputFieldSpecV1, ...]:
    specs: list[OperatorInputFieldSpecV1] = []
    for raw in contract["fields"]:
        if not isinstance(raw, Mapping):
            raise OperatorInputContractError("contract_field_not_object")
        field_name = str(raw.get("field_name", "")).strip()
        if not field_name:
            raise OperatorInputContractError("contract_field_name_missing")
        try:
            resolution_class = OperatorInputResolutionClass(str(raw["resolution_class"]))
        except (KeyError, ValueError) as exc:
            raise OperatorInputContractError(
                f"contract_resolution_class_invalid:{field_name}"
            ) from exc
        specs.append(
            OperatorInputFieldSpecV1(
                field_name=field_name,
                data_type=str(raw.get("data_type", "")),
                required=bool(raw.get("required", True)),
                resolved=bool(raw.get("resolved", False)),
                resolution_class=resolution_class,
                canonical_default=raw.get("canonical_default"),
                source_owner=str(raw.get("source_owner", "")),
                rationale=str(raw.get("rationale", "")),
                safety_effect=str(raw.get("safety_effect", "")),
                economic_effect=str(raw.get("economic_effect", "")),
                constraints=dict(raw.get("constraints", {})),
            )
        )
    return tuple(specs)


def _reject_url_path(path_str: str, *, field_name: str) -> None:
    if _URL_SCHEME_RE.match(path_str.strip()):
        raise OperatorInputContractError(f"{field_name}_url_forbidden")
    parsed = urlparse(path_str)
    if parsed.scheme and parsed.scheme not in {"", "file"}:
        raise OperatorInputContractError(f"{field_name}_url_forbidden")


def _contains_forbidden_token(value: str, forbidden: frozenset[str]) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in forbidden)


def validate_canonical_safety_invariants_v1(contract: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    if contract.get("futures_only") is not True:
        violations.append("futures_only_not_true")
    if contract.get("bitcoin_direction_allowed") is not False:
        violations.append("bitcoin_direction_allowed_not_false")
    if contract.get("real_evaluation_permitted") is not False:
        violations.append("real_evaluation_permitted_not_false")
    if contract.get("profitability_claim_allowed") is not False:
        violations.append("profitability_claim_allowed_not_false")
    if contract.get("kraken_fixture_leak_into_canonical_economic_path") is not False:
        violations.append("kraken_fixture_leak_not_false")
    if contract.get("venue_specific_canonical_economic_path_allowed") is not False:
        violations.append("venue_specific_canonical_path_not_false")
    if contract.get("runtime_effect") is not False:
        violations.append("runtime_effect_not_false")
    if contract.get("order_effect") is not False:
        violations.append("order_effect_not_false")
    if contract.get("network_effect") is not False:
        violations.append("network_effect_not_false")
    if contract.get("live_authorized") is not False:
        violations.append("live_authorized_not_false")
    return violations


def validate_bound_canonical_defaults_v1() -> list[str]:
    violations: list[str] = []
    policy = canonical_economic_validity_policy_v1()
    if not policy.is_version_bound():
        violations.append("economic_validity_policy_unbound")
    if not policy.thresholds_configured():
        violations.append("economic_validity_policy_thresholds_unconfigured")
    if policy.policy_version != ECONOMIC_VALIDITY_POLICY_VERSION:
        violations.append("economic_validity_policy_version_mismatch")
    if mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID != "inst-eth-usdt-perp":
        violations.append("mv2_required_instrument_changed")
    if COST_MODEL_VERSION != "backtest_cost_v0":
        violations.append("cost_model_version_changed")
    if FEE_MODEL_VERSION != "backtest_fee_taker_symmetric_v0":
        violations.append("fee_model_version_changed")
    if SLIPPAGE_MODEL_VERSION != "backtest_slippage_symmetric_v0":
        violations.append("slippage_model_version_changed")
    if FUNDING_MODEL_VERSION != "backtest_funding_perpetual_interval_v1":
        violations.append("funding_model_version_changed")
    if EXECUTION_MODEL_VERSION != "paper_market_context_v0":
        violations.append("execution_model_version_changed")
    if DEFAULT_DATASET_VERSION != "v1":
        violations.append("dataset_version_changed")
    if DATASET_SCHEMA_VERSION != "v1":
        violations.append("dataset_schema_version_changed")
    return violations


def evaluate_operator_input_readiness_v1(
    contract: Optional[Mapping[str, Any]] = None,
    *,
    repo_root: Optional[Path] = None,
) -> OperatorInputReadinessResultV1:
    payload = dict(contract or load_operator_input_contract_v1(repo_root=repo_root))
    specs = parse_operator_input_field_specs_v1(payload)
    reason_codes: list[str] = []
    reason_codes.extend(validate_canonical_safety_invariants_v1(payload))
    reason_codes.extend(validate_bound_canonical_defaults_v1())

    unresolved_operator = tuple(
        spec.field_name
        for spec in specs
        if spec.required
        and spec.resolution_class is OperatorInputResolutionClass.OPERATOR_REQUIRED
        and not spec.resolved
    )
    blocked_no_evidence = tuple(
        spec.field_name
        for spec in specs
        if spec.required
        and spec.resolution_class is OperatorInputResolutionClass.BLOCKED_NO_EVIDENCE
        and not spec.resolved
    )
    policy_gaps = tuple(
        spec.field_name
        for spec in specs
        if spec.required
        and spec.resolution_class is OperatorInputResolutionClass.POLICY_GAP
        and not spec.resolved
    )
    resolved_count = sum(1 for spec in specs if spec.resolved)
    required_count = sum(1 for spec in specs if spec.required)

    if policy_gaps:
        verdict = OperatorInputReadinessVerdict.BLOCKED_BY_CANONICAL_POLICY_GAP
        reason_codes.append("policy_gap_fields_present")
    elif payload.get("admissibility_verdict") == (
        "REAL_ADMISSIBLE_EVIDENCE_ALREADY_PRESENT_BUT_UNBOUND"
    ):
        verdict = OperatorInputReadinessVerdict.REAL_ADMISSIBLE_EVIDENCE_ALREADY_PRESENT_BUT_UNBOUND
        reason_codes.append("real_evidence_present_but_unbound")
    elif unresolved_operator or blocked_no_evidence:
        verdict = OperatorInputReadinessVerdict.OPERATOR_INPUT_CONTRACT_COMPLETE
        if blocked_no_evidence:
            reason_codes.append("no_real_admissible_evidence_present")
        if unresolved_operator:
            reason_codes.append("operator_inputs_unresolved")
    else:
        verdict = OperatorInputReadinessVerdict.OPERATOR_INPUT_CONTRACT_COMPLETE

    contract_complete = (
        payload.get("operator_input_contract_complete") is True
        and not policy_gaps
        and payload.get("verdict")
        == OperatorInputReadinessVerdict.OPERATOR_INPUT_CONTRACT_COMPLETE.value
    )
    if not contract_complete:
        reason_codes.append("operator_input_contract_incomplete")

    return OperatorInputReadinessResultV1(
        contract_version=CONTRACT_VERSION,
        owner=CONTRACT_OWNER,
        verdict=verdict,
        admissibility_verdict=str(payload.get("admissibility_verdict", "")),
        operator_input_contract_complete=contract_complete,
        real_evaluation_permitted=False,
        profitability_claim_allowed=False,
        unresolved_operator_fields=unresolved_operator,
        blocked_no_evidence_fields=blocked_no_evidence,
        policy_gap_fields=policy_gaps,
        resolved_field_count=resolved_count,
        required_field_count=required_count,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        futures_only=True,
        bitcoin_direction_allowed=False,
    )


def _require_positive_cost(value: Any, *, field_name: str) -> float:
    if value is None:
        raise OperatorInputContractError(f"{field_name}_missing")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise OperatorInputContractError(f"{field_name}_invalid") from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise OperatorInputContractError(f"{field_name}_implicit_zero_forbidden")
    return numeric


def validate_staged_operator_inputs_v1(
    operator_inputs: Mapping[str, Any],
    *,
    repo_root: Optional[Path] = None,
    allow_real_evaluation: bool = False,
) -> list[str]:
    """Validate a concrete operator staging payload (fail-closed for real evaluation)."""
    if allow_real_evaluation:
        raise OperatorInputContractError("real_evaluation_not_permitted_in_this_contract")

    violations: list[str] = []
    readiness = evaluate_operator_input_readiness_v1(repo_root=repo_root)
    if readiness.policy_gap_fields:
        violations.append("policy_gap_blocks_staging")
    if readiness.unresolved_operator_fields:
        violations.extend(
            f"operator_field_unresolved:{name}" for name in readiness.unresolved_operator_fields
        )

    instrument_id = str(operator_inputs.get("instrument_id", mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID))
    if instrument_id != mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID:
        violations.append("instrument_id_not_mv2_required")
    if _contains_forbidden_token(instrument_id, _FORBIDDEN_INSTRUMENT_SUBSTRINGS):
        violations.append("instrument_id_forbidden_token")

    source_type = str(operator_inputs.get("provenance_source_type", "")).lower().strip()
    if source_type in _FORBIDDEN_SOURCE_TYPES:
        violations.append(f"provenance_source_type_forbidden:{source_type}")

    provenance_ref = str(operator_inputs.get("provenance_ref", "")).strip()
    if not provenance_ref:
        violations.append("provenance_ref_missing")
    elif provenance_ref.lower().startswith("tests/") or "/tests/" in provenance_ref.lower():
        violations.append("provenance_ref_test_path_forbidden")
    elif _contains_forbidden_token(provenance_ref, _FORBIDDEN_PROVENANCE_SUBSTRINGS):
        violations.append("provenance_ref_forbidden_token")

    generation_method = str(operator_inputs.get("provenance_generation_method", "")).lower()
    for marker in _FORBIDDEN_GENERATION_MARKERS:
        if marker in generation_method:
            violations.append(f"provenance_generation_method_forbidden:{marker}")

    venue_id = str(operator_inputs.get("provenance_venue_id", "")).strip()
    if not venue_id:
        violations.append("provenance_venue_id_missing")
    elif _contains_forbidden_token(venue_id, _FORBIDDEN_PROVENANCE_SUBSTRINGS):
        violations.append("provenance_venue_id_forbidden_token")

    for path_field in (
        "dataset_path",
        "dataset_manifest_path",
        "evaluation_config_path",
        "evidence_output_dir",
    ):
        raw = operator_inputs.get(path_field)
        if raw is None:
            continue
        path_str = str(raw).strip()
        if not path_str:
            violations.append(f"{path_field}_empty")
            continue
        try:
            _reject_url_path(path_str, field_name=path_field)
        except OperatorInputContractError:
            violations.append(f"{path_field}_url_forbidden")

    if "fee_bps" in operator_inputs:
        try:
            _require_positive_cost(operator_inputs["fee_bps"], field_name="fee_bps")
        except OperatorInputContractError as exc:
            violations.append(str(exc))
    if "slippage_bps" in operator_inputs:
        try:
            _require_positive_cost(operator_inputs["slippage_bps"], field_name="slippage_bps")
        except OperatorInputContractError as exc:
            violations.append(str(exc))

    if operator_inputs.get("profitability_claim_allowed") is True:
        violations.append("profitability_claim_forbidden")
    if operator_inputs.get("real_evaluation_performed") is True:
        violations.append("real_evaluation_performed_forbidden")
    if operator_inputs.get("economic_validity_result") == "PASS":
        violations.append("economic_validity_pass_claim_forbidden_without_real_evaluation")

    return violations


def assert_operator_input_contract_ready_v1(
    *,
    repo_root: Optional[Path] = None,
) -> OperatorInputReadinessResultV1:
    result = evaluate_operator_input_readiness_v1(repo_root=repo_root)
    if not result.operator_input_contract_complete:
        raise OperatorInputContractError(
            f"operator_input_contract_not_ready:{','.join(result.reason_codes)}"
        )
    if result.real_evaluation_permitted:
        raise OperatorInputContractError("real_evaluation_permitted_forbidden")
    if result.profitability_claim_allowed:
        raise OperatorInputContractError("profitability_claim_allowed_forbidden")
    return result


def contract_implementation_digest() -> str:
    return _stable_digest(
        {
            "owner": CONTRACT_OWNER,
            "contract_version": CONTRACT_VERSION,
            "runner_owner": RUNNER_OWNER,
        }
    )


def serialize_operator_input_contract_manifest_v1(
    *,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    contract = load_operator_input_contract_v1(repo_root=repo_root)
    readiness = evaluate_operator_input_readiness_v1(contract, repo_root=repo_root)
    specs = parse_operator_input_field_specs_v1(contract)
    return {
        "contract_version": CONTRACT_VERSION,
        "owner": CONTRACT_OWNER,
        "implementation_digest": contract_implementation_digest(),
        "readiness": readiness.to_dict(),
        "field_count": len(specs),
        "resolved_fields": [spec.field_name for spec in specs if spec.resolved],
        "unresolved_operator_fields": list(readiness.unresolved_operator_fields),
        "blocked_no_evidence_fields": list(readiness.blocked_no_evidence_fields),
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "real_evaluation_permitted": False,
        "profitability_claim_allowed": False,
    }
