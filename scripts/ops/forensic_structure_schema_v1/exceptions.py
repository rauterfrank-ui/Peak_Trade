"""Fail-closed contract violations. Partial pretty output is never success."""

from __future__ import annotations


class TransformationContractViolation(Exception):
    """Raised when a named contract rule is violated.

    ``rule`` is a concrete C*/D*/SW-R*/DR-* or STAGE_* identifier.
    """

    def __init__(self, rule: str, message: str) -> None:
        if not rule or not isinstance(rule, str):
            raise ValueError("violation rule id is required")
        self.rule = rule
        self.message = message
        super().__init__(f"{rule}: {message}")

    def as_record(self) -> dict[str, str]:
        return {
            "kind": "TRANSFORMATION_CONTRACT_VIOLATION",
            "rule": self.rule,
            "message": self.message,
            "output_must_not_be_treated_as_valid": "true",
        }
