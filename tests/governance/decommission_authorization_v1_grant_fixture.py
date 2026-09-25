"""In-memory inactive semantics-neutral decommission grant template for unit tests.

Production repository may ship without a persisted grant JSON; exact-file admission
machinery is validated via this template and in-test active grants.
"""

from __future__ import annotations

import copy
from typing import Any

INACTIVE_DECOMMISSION_GRANT: dict[str, Any] = {
    "TOKEN_ALONE_IS_INSUFFICIENT": True,
    "allowed_paths": [],
    "allowed_surface_classes": [],
    "authority_effect": "NONE",
    "authorization_token": "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1",
    "authorized_evidence_digest": "",
    "authorized_path_prefixes": [],
    "authorized_scope_class": "SEMANTICS_NEUTRAL_DECOMMISSION_ONLY",
    "blanket_allowlist": False,
    "bound_boundary_contract": "config/governance/economic_diagnostic_optimization_boundary_v0.json",
    "bound_boundary_guard": "src/governance/economic_diagnostic_optimization_boundary_v0.py",
    "branch_protection_bypass": False,
    "branch_specific_exception": False,
    "broad_master_v2_grant": False,
    "canonical_governance_owner": "docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md",
    "claim_epistemics": {
        "AUTHORIZED_EVIDENCE_DIGEST": "MACHINE_VALIDATED",
        "DECOMMISSION_PREDICATES": "MACHINE_VALIDATED",
        "EXACT_FILE_SCOPE": "MACHINE_VALIDATED",
        "FAIL_CLOSED_SEMANTICS_WEAKENED": "MACHINE_VALIDATED",
        "PRODUCTIVE_REACHABILITY_INCREASED": "MACHINE_VALIDATED",
        "TRADING_SEMANTICS_CHANGED": "MACHINE_VALIDATED",
    },
    "class_attestation": "docs/ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md",
    "contract_version": "semantics_neutral_decommission_authorization_v1",
    "decommission_predicates": {
        "require_at_least_one": [
            "DELETED_COMPONENT_REFERENCE_REMOVED",
            "NEGATIVE_TEST_TOKEN_NEUTRALIZED",
            "NONCANONICAL_LITERAL_NEUTRALIZED",
            "OBSOLETE_REFERENCE_REMOVED",
            "REMOVED_TARGET_NO_LONGER_EXISTS",
            "WHOLE_FILE_RETIRED",
        ]
    },
    "directory_grant": False,
    "economic_evaluation": False,
    "evidence_digest_algorithm": "sha256",
    "evidence_digest_canonicalization": "decommission_evidence_digest_v1",
    "fail_closed_validation_rules": [
        "TOKEN_ALONE_IS_INSUFFICIENT",
        "EXACT_FILE_SCOPE_ONLY",
        "NO_DIRECTORY_OR_BROAD_MASTER_V2_GRANT",
        "NO_PR_NUMBER_OR_BRANCH_HARDCODE",
        "NO_REQUIRED_CHECK_WAIVER",
        "EMPTY_ALLOWED_PATHS_WHEN_GRANT_INACTIVE",
        "EMPTY_EVIDENCE_DIGEST_WHEN_GRANT_INACTIVE",
        "DIFF_EVIDENCE_REQUIRED_WHEN_GRANT_ACTIVE",
        "AUTHORIZED_EVIDENCE_DIGEST_REQUIRED_WHEN_GRANT_ACTIVE",
        "AT_LEAST_ONE_DECOMMISSION_PREDICATE_REQUIRED",
    ],
    "forbidden_effects": {
        "AUTHORITY_EFFECT": "NONE",
        "CREDENTIAL_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "RUNTIME_EFFECT": "NONE",
        "SCHEDULER_EFFECT": "NONE",
    },
    "grant_active": False,
    "mutation_purpose_class": "SEMANTICS_NEUTRAL_DECOMMISSION",
    "notes": [
        "Test fixture only; production grant JSON is optional when no active exact-file slice is bound.",
    ],
    "parallel_ssot_created": False,
    "pr_specific_exception": False,
    "required_capability_invariants": {
        "CANARY_CAPABILITY_INCREASED": False,
        "LIVE_CAPABILITY_INCREASED": False,
        "NEW_EXECUTION_AUTHORITY_CREATED": False,
        "NEW_RISK_AUTHORITY_CREATED": False,
        "NEW_SELECTION_AUTHORITY_CREATED": False,
        "NEW_TRADING_AUTHORITY_CREATED": False,
        "PRODUCTIVE_REACHABILITY_INCREASED": False,
        "TESTNET_CAPABILITY_INCREASED": False,
    },
    "required_check_waiver": False,
    "required_semantic_invariants": {
        "AUTHORITY_EFFECT": "NONE",
        "CREDENTIAL_EFFECT": "NONE",
        "ECONOMIC_SEMANTICS_CHANGED": False,
        "EXECUTION_SEMANTICS_CHANGED": False,
        "FAIL_CLOSED_SEMANTICS_WEAKENED": False,
        "ORDER_EFFECT": "NONE",
        "PLANNING_SEMANTICS_CHANGED": False,
        "RISK_SEMANTICS_CHANGED": False,
        "RUNTIME_EFFECT": "NONE",
        "SCHEDULER_EFFECT": "NONE",
        "SELECTION_SEMANTICS_CHANGED": False,
        "TRADING_SEMANTICS_CHANGED": False,
    },
    "runtime_activation": False,
    "runtime_effect": "NONE",
    "scope_id": "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1",
}


def inactive_decommission_grant_copy() -> dict[str, Any]:
    return copy.deepcopy(INACTIVE_DECOMMISSION_GRANT)
