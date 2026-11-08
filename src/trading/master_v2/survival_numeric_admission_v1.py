"""Numeric input admission before immutable Survival v1, never positive authority."""

from dataclasses import dataclass, replace
import json
import math

from trading.master_v2 import survival_assessment_v1 as original


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def compute_expected_roundtrip_cost(costs):
    values = (
        costs.entry_fee,
        costs.expected_entry_slippage,
        costs.exit_fee,
        costs.expected_exit_slippage,
    )
    if type(costs.funding_cost_required) is not bool or any(not _finite_number(v) for v in values):
        return None
    if costs.expected_funding_cost is not None and not _finite_number(costs.expected_funding_cost):
        return None
    result = original.compute_expected_roundtrip_cost(costs)
    return result if result is None or _finite_number(result) else None


def compute_net_expected_edge(*, expected_gross_edge, expected_roundtrip_cost):
    if not _finite_number(expected_gross_edge) or not _finite_number(expected_roundtrip_cost):
        return None
    result = original.compute_net_expected_edge(
        expected_gross_edge=expected_gross_edge, expected_roundtrip_cost=expected_roundtrip_cost
    )
    return result if result is None or _finite_number(result) else None


def serialize_survival_result_strict_v1(result):
    canonical = original.serialize_survival_result_canonical(result)

    def reject(value):
        raise ValueError("SURVIVAL_NUMERIC_OUTPUT_NONFINITE:" + value)

    json.loads(canonical, parse_constant=reject)
    return canonical


@dataclass(frozen=True)
class SurvivalNumericAdmissionV1:
    input: original.SurvivalAssessmentInputV1
    policy: original.SurvivalAssessmentPolicyV1
    blocked_reasons: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def __iter__(self):
        yield self.input
        yield self.policy


def admit_survival_numeric_policy_v1(policy):
    policy_blocks = []
    if not _finite_number(policy.min_net_edge) or policy.min_net_edge < 0:
        policy_blocks.append("policy_min_net_edge_invalid")
    ratio_names = (
        "min_volatility_survival_ratio",
        "min_sequence_survival_ratio",
        "min_drawdown_survival_ratio",
        "min_liquidation_buffer_ratio",
    )
    if any(not _finite_number(getattr(policy, name)) for name in ratio_names):
        policy_blocks.append("policy_ratio_threshold_invalid")
    if type(policy.validity_epochs) is not int or policy.validity_epochs <= 0:
        policy_blocks.append("policy_validity_epochs_invalid")
    if policy_blocks:
        # Only a non-admitting evaluation uses this serializable policy shape.
        # It never grants Entry or supplies a retained-plan expiry policy.
        safe_policy = replace(
            policy, min_net_edge=0, validity_epochs=1, **{n: 0 for n in ratio_names}
        )
        return safe_policy, tuple(policy_blocks)
    return policy, ()


def admit_survival_numeric_inputs_v1(inp, policy):
    """Return original arguments or an explicit non-admitting original input gate."""
    safe_policy, policy_blocks = admit_survival_numeric_policy_v1(policy)
    if policy_blocks:
        return SurvivalNumericAdmissionV1(
            replace(inp, input_complete=False),
            safe_policy,
            policy_blocks,
            ("policy_validation_failed",),
        )

    invalid = []
    for name, value in vars(inp.cost_inputs).items():
        valid = (
            type(value) is bool
            if name == "funding_cost_required"
            else value is None or _finite_number(value)
        )
        if not valid:
            invalid.append("cost_input_invalid:" + name)
    for name, value in vars(inp.metric_inputs).items():
        valid = value is None or (
            type(value) is bool if name == "data_completeness_complete" else _finite_number(value)
        )
        if not valid:
            invalid.append("metric_input_invalid:" + name)
    if invalid:
        return SurvivalNumericAdmissionV1(
            replace(inp, input_complete=False),
            policy,
            tuple(dict.fromkeys(reason.split(":")[0] for reason in invalid)),
            tuple(invalid),
        )

    # Reuse original arithmetic; no second economic formula or threshold.
    roundtrip = original.compute_expected_roundtrip_cost(inp.cost_inputs)
    net = original.compute_net_expected_edge(
        expected_gross_edge=inp.cost_inputs.expected_gross_edge, expected_roundtrip_cost=roundtrip
    )
    if any(value is not None and not _finite_number(value) for value in (roundtrip, net)):
        return SurvivalNumericAdmissionV1(
            replace(inp, input_complete=False),
            policy,
            ("cost_arithmetic_nonfinite",),
            ("cost_arithmetic_nonfinite",),
        )
    return SurvivalNumericAdmissionV1(inp, policy)


def annotate_survival_numeric_admission_v1(result, admission):
    if admission.blocked_reasons:
        if result.status is not original.SurvivalAssessmentStatus.BLOCKED:
            raise ValueError("SURVIVAL_ORIGINAL_NUMERIC_INPUT_GATE_NOT_BLOCKED")
        if any(
            value is not None
            for value in (
                result.expected_gross_edge,
                result.expected_roundtrip_cost,
                result.net_expected_edge,
            )
        ):
            raise ValueError("SURVIVAL_ORIGINAL_BLOCKED_RECORD_CONTAINS_NUMBERS")
        result = original.with_computed_survival_result_digest(
            replace(
                result,
                blocked_reasons=admission.blocked_reasons,
                reason_codes=admission.reason_codes,
                semantic_digest="",
            )
        )
    serialize_survival_result_strict_v1(result)
    return result


def evaluate_survival_with_numeric_admission_v1(inp, policy):
    admission = admit_survival_numeric_inputs_v1(inp, policy)
    return annotate_survival_numeric_admission_v1(
        original.evaluate_survival_assessment_v1(*admission), admission
    )
