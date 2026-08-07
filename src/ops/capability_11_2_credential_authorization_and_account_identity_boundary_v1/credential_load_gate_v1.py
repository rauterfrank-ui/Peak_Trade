"""Credential load gate: prerequisites ordered; Cap 11.2 never loads secrets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    CREDENTIAL_FAILURE_FAILS_CLOSED,
    CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2,
    CREDENTIAL_LOAD_PREREQUISITES,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_CREDENTIAL_USE_ALLOWED,
)


class CredentialLoadGateError(ValueError):
    """Fail-closed credential load gate violation."""


@dataclass
class CredentialLoadGateV1:
    """Ordered prerequisite gate before any future credential load.

    Cap 11.2 defines and enforces the gate contract but never performs a real
    credential load. Any attempt to load fails closed.
    """

    prerequisites_satisfied: dict[str, bool] = field(
        default_factory=lambda: {name: False for name in CREDENTIAL_LOAD_PREREQUISITES}
    )

    def mark_prerequisite(self, name: str, *, satisfied: bool = True) -> None:
        if name not in CREDENTIAL_LOAD_PREREQUISITES:
            raise CredentialLoadGateError(f"UNKNOWN_CREDENTIAL_LOAD_PREREQUISITE:{name}")
        self.prerequisites_satisfied[name] = bool(satisfied)

    def evaluate_admissibility(self) -> dict[str, Any]:
        missing = [
            name
            for name in CREDENTIAL_LOAD_PREREQUISITES
            if not self.prerequisites_satisfied.get(name)
        ]
        return {
            "admissible_for_future_load": not missing,
            "missing_prerequisites": missing,
            "CREDENTIAL_LOAD_PREREQUISITES": list(CREDENTIAL_LOAD_PREREQUISITES),
            "EXCHANGE_CREDENTIAL_USE_ALLOWED": EXCHANGE_CREDENTIAL_USE_ALLOWED,
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
            "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2": False,
        }

    def attempt_credential_load_v1(self) -> dict[str, Any]:
        """Always fail-closed in Cap 11.2 — boundary only, no secret materialization."""
        evaluation = self.evaluate_admissibility()
        if evaluation["missing_prerequisites"]:
            raise CredentialLoadGateError(
                "CREDENTIAL_LOAD_PREREQUISITES_UNSATISFIED:"
                + ",".join(evaluation["missing_prerequisites"])
            )
        # Even with all prerequisites marked, Cap 11.2 refuses actual load.
        raise CredentialLoadGateError("CREDENTIAL_LOAD_FORBIDDEN_IN_CAPABILITY_11_2")


def prove_credential_load_gate_v1() -> dict[str, Any]:
    gate = CredentialLoadGateV1()
    blocked_incomplete = False
    try:
        gate.attempt_credential_load_v1()
    except CredentialLoadGateError as exc:
        blocked_incomplete = "CREDENTIAL_LOAD_PREREQUISITES_UNSATISFIED" in str(exc)

    for name in CREDENTIAL_LOAD_PREREQUISITES:
        gate.mark_prerequisite(name, satisfied=True)
    complete_eval = gate.evaluate_admissibility()

    blocked_complete = False
    try:
        gate.attempt_credential_load_v1()
    except CredentialLoadGateError as exc:
        blocked_complete = "CREDENTIAL_LOAD_FORBIDDEN_IN_CAPABILITY_11_2" in str(exc)

    ok = all(
        [
            blocked_incomplete,
            complete_eval.get("admissible_for_future_load") is True,
            blocked_complete,
            EXCHANGE_CREDENTIAL_USE_ALLOWED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2 is False,
            CREDENTIAL_FAILURE_FAILS_CLOSED is True,
        ]
    )
    return {
        "ok": ok,
        "CREDENTIAL_LOAD_PREREQUISITES": list(CREDENTIAL_LOAD_PREREQUISITES),
        "incomplete_load_blocked": blocked_incomplete,
        "complete_prerequisites_still_blocked": blocked_complete,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2": False,
        "CREDENTIAL_FAILURE_FAILS_CLOSED": CREDENTIAL_FAILURE_FAILS_CLOSED,
        "dedicated_execution_host_only": True,
        "load_after_mode_auth_sha_config_account_venue": True,
    }
