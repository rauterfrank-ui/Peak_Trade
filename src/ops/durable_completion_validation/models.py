"""Shared validation models for durable completion proof binding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    fail_reasons: tuple[str, ...] = ()


@dataclass
class ValidationContext:
    integration_input: Any
    pe31_result: dict[str, Any] | None = None
    pe35_result: dict[str, Any] | None = None
    pe37_result: dict[str, Any] | None = None
    pe25_result: dict[str, Any] | None = None
    admission_result: dict[str, Any] | None = None
    completed_validators: set[str] = field(default_factory=set)
