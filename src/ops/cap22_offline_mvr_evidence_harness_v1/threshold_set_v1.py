"""Injected Policy-B offline threshold-set contract.

The set is an experimental offline evidence grid only. No threshold is
economically optimal, productively valid, or Owner-ratified by this slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND,
    POLICY_B_SINGLE_THRESHOLD_RATIFIED,
    POLICY_B_TEST_ONLY_VALUES_USED,
    POLICY_B_THRESHOLD_MODE,
    POLICY_B_THRESHOLD_SET_ID,
    POLICY_B_THRESHOLD_SET_RATIFIED,
    POLICY_B_THRESHOLD_SET_VERSION,
    POLICY_B_THRESHOLD_UNITS,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.reason_codes_v1 import (
    OfflineMvrHarnessFailureCodeV1,
)
from src.ops.economic_md_input_producer_v1.models_v1 import canonical_json_dumps, sha256_hex

TEST_ONLY_NON_CANONICAL_THRESHOLD_LABEL = "TEST_ONLY_NON_CANONICAL"
TEST_ONLY_NON_CANONICAL_THRESHOLD_VALUES: tuple[str, ...] = (
    "0.0001",
    "0.0005",
    "0.001",
    "0.005",
    "0.01",
)


class PolicyBThresholdSetError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class PolicyBThresholdMemberV1:
    threshold_id: str
    relative_spread_threshold: Decimal
    units: str
    canonical: bool
    test_only: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical": self.canonical,
            "relative_spread_threshold": format(self.relative_spread_threshold, "f"),
            "test_only": self.test_only,
            "threshold_id": self.threshold_id,
            "units": self.units,
        }


@dataclass(frozen=True)
class InjectedPolicyBThresholdSetV1:
    threshold_set_id: str
    threshold_set_version: str
    threshold_mode: str
    units: str
    ratified: bool
    single_threshold_ratified: bool
    authoritative_scale_found: bool
    test_only_values_used: bool
    members: tuple[PolicyBThresholdMemberV1, ...]
    payload_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authoritative_scale_found": self.authoritative_scale_found,
            "members": [row.to_dict() for row in self.members],
            "payload_digest": self.payload_digest,
            "single_threshold_ratified": self.single_threshold_ratified,
            "test_only_values_used": self.test_only_values_used,
            "threshold_mode": self.threshold_mode,
            "threshold_set_id": self.threshold_set_id,
            "threshold_set_ratified": self.ratified,
            "threshold_set_version": self.threshold_set_version,
            "units": self.units,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("payload_digest", None)
        return payload

    def compute_payload_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_payload_digest(self) -> "InjectedPolicyBThresholdSetV1":
        return InjectedPolicyBThresholdSetV1(
            threshold_set_id=self.threshold_set_id,
            threshold_set_version=self.threshold_set_version,
            threshold_mode=self.threshold_mode,
            units=self.units,
            ratified=self.ratified,
            single_threshold_ratified=self.single_threshold_ratified,
            authoritative_scale_found=self.authoritative_scale_found,
            test_only_values_used=self.test_only_values_used,
            members=self.members,
            payload_digest=self.compute_payload_digest(),
        )


def _parse_positive_threshold(raw: Any) -> Decimal:
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
            "THRESHOLD_NOT_DECIMAL",
        ) from exc
    if value <= 0:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
            "THRESHOLD_NOT_POSITIVE",
        )
    return value


def parse_injected_policy_b_threshold_set_v1(
    payload: Mapping[str, Any] | InjectedPolicyBThresholdSetV1 | None,
) -> InjectedPolicyBThresholdSetV1:
    if payload is None:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value
        )
    if isinstance(payload, InjectedPolicyBThresholdSetV1):
        parsed = payload
    else:
        raw_members = payload.get("members") or payload.get("thresholds") or ()
        if not isinstance(raw_members, Sequence) or not raw_members:
            raise PolicyBThresholdSetError(
                OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value,
                "EMPTY_THRESHOLD_SET",
            )
        members: list[PolicyBThresholdMemberV1] = []
        seen_ids: set[str] = set()
        seen_values: set[Decimal] = set()
        for index, row in enumerate(raw_members):
            if isinstance(row, Mapping):
                raw_value = row.get("relative_spread_threshold", row.get("threshold"))
                threshold_id = str(row.get("threshold_id") or f"injected_threshold_{index + 1:02d}")
                canonical = bool(row.get("canonical", False))
                test_only = bool(row.get("test_only", True))
                units = str(row.get("units") or POLICY_B_THRESHOLD_UNITS)
            else:
                raw_value = row
                threshold_id = f"injected_threshold_{index + 1:02d}"
                canonical = False
                test_only = True
                units = POLICY_B_THRESHOLD_UNITS
            if canonical is True:
                raise PolicyBThresholdSetError(
                    OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
                    "CANONICAL_THRESHOLD_FORBIDDEN",
                )
            if units != POLICY_B_THRESHOLD_UNITS:
                raise PolicyBThresholdSetError(
                    OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
                    "UNITS_MISMATCH",
                )
            value = _parse_positive_threshold(raw_value)
            if threshold_id in seen_ids or value in seen_values:
                raise PolicyBThresholdSetError(
                    OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
                    "DUPLICATE_THRESHOLD",
                )
            seen_ids.add(threshold_id)
            seen_values.add(value)
            members.append(
                PolicyBThresholdMemberV1(
                    threshold_id=threshold_id,
                    relative_spread_threshold=value,
                    units=units,
                    canonical=False,
                    test_only=test_only,
                )
            )
        members.sort(key=lambda row: (row.relative_spread_threshold, row.threshold_id))
        parsed = InjectedPolicyBThresholdSetV1(
            threshold_set_id=str(payload.get("threshold_set_id") or POLICY_B_THRESHOLD_SET_ID),
            threshold_set_version=str(
                payload.get("threshold_set_version") or POLICY_B_THRESHOLD_SET_VERSION
            ),
            threshold_mode=str(payload.get("threshold_mode") or POLICY_B_THRESHOLD_MODE),
            units=POLICY_B_THRESHOLD_UNITS,
            ratified=False,
            single_threshold_ratified=False,
            authoritative_scale_found=False,
            test_only_values_used=True,
            members=tuple(members),
            payload_digest="",
        ).with_payload_digest()
    if parsed.ratified or parsed.single_threshold_ratified or parsed.authoritative_scale_found:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
            "THRESHOLD_SET_MUST_REMAIN_UNRATIFIED",
        )
    if parsed.threshold_mode != POLICY_B_THRESHOLD_MODE:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_INVALID.value,
            "THRESHOLD_MODE_MISMATCH",
        )
    if not parsed.members:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value,
            "EMPTY_THRESHOLD_SET",
        )
    return parsed.with_payload_digest()


def injected_test_only_non_canonical_policy_b_threshold_set_v1() -> InjectedPolicyBThresholdSetV1:
    """Fixture grid. Explicitly non-canonical. Not Owner economic truth."""
    members = tuple(
        PolicyBThresholdMemberV1(
            threshold_id=f"test_only_{value.replace('.', 'p')}",
            relative_spread_threshold=Decimal(value),
            units=POLICY_B_THRESHOLD_UNITS,
            canonical=False,
            test_only=True,
        )
        for value in TEST_ONLY_NON_CANONICAL_THRESHOLD_VALUES
    )
    return InjectedPolicyBThresholdSetV1(
        threshold_set_id=POLICY_B_THRESHOLD_SET_ID,
        threshold_set_version=POLICY_B_THRESHOLD_SET_VERSION,
        threshold_mode=POLICY_B_THRESHOLD_MODE,
        units=POLICY_B_THRESHOLD_UNITS,
        ratified=POLICY_B_THRESHOLD_SET_RATIFIED,
        single_threshold_ratified=POLICY_B_SINGLE_THRESHOLD_RATIFIED,
        authoritative_scale_found=AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND,
        test_only_values_used=POLICY_B_TEST_ONLY_VALUES_USED,
        members=members,
        payload_digest="",
    ).with_payload_digest()
