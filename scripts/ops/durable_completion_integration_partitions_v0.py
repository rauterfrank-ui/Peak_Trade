"""Fachliche Required-Coverage-Partitionen für den Completion-Integration-Testowner (v0).

Deterministische Node-Klassifikation per pytest-Collect + Name-Regeln.
Kein Cross-Call-State; rein statische Inventar- und Expansionshilfe für CI-Selector.
"""

from __future__ import annotations

import re
import subprocess
import sys
from functools import lru_cache
from typing import Final

INTEGRATION_TEST_OWNER: Final = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

COMPLETION_FACADE_PATH: Final = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

CORE_ALWAYS_PARTITIONS: Final[tuple[str, ...]] = (
    "core_invariants",
    "core_smoke",
    "core_digest",
)

ALL_PARTITIONS: Final[tuple[str, ...]] = (
    *CORE_ALWAYS_PARTITIONS,
    "core_baseline_input",
    "core_kwargs",
    "core_cross_chain",
    "pe21_reconciliation",
    "pe31_review",
    "pe22_risk_killswitch",
    "pe23_capital",
    "pe24_pilot",
    "pe25_closure",
    "pe35_handoff_recovery",
    "pe37_traceability",
    "pe38_readiness",
    "wallclock",
)

_NODE_ID_RE = re.compile(r"<Function (test_[^>]+)>")


def _base_node_id(node_id: str) -> str:
    return node_id.split("[", 1)[0]


def classify_integration_node_id(node_id: str) -> str:
    """Map a collected pytest node id (test_name or test_name[param]) to one partition."""
    base = _base_node_id(node_id)

    if base in {
        "test_package_marker_present",
        "test_canonical_owners_referenced_not_duplicated",
        "test_global_safety_flags_remain_blocked",
        "test_contract_version_constants",
        "test_default_safety_snapshot_matches_required_invariants",
        "test_bounded_durable_run_required_paths_covered",
        "test_completion_required_paths_bind_to_canonical_testnet_contract",
        "test_generic_bounded_required_paths_not_testnet_completion_source_of_truth",
        "test_full_testnet_artifact_set_passes",
    }:
        return "core_invariants"

    if base.startswith("test_completion_integration_input_digest_"):
        if "pe21" in base:
            return "pe21_reconciliation"
        if "pe31" in base:
            return "pe31_review"
        return "core_digest"

    if base in {
        "test_deterministic_identical_inputs_same_payload_and_digest",
        "test_coherent_static_completion_happy_path_passes",
        "test_valid_static_proof_remains_non_authorizing",
        "test_no_input_mutation_from_evaluation",
        "test_current_lifecycle_state_passes",
        "test_manifest_digest_matches_canonical_entries",
        "test_run_identity_digest_matches_canonical_inputs",
    }:
        return "core_smoke"

    if base.startswith("test_reconciliation_result_") or any(
        base.startswith(prefix)
        for prefix in (
            "test_missing_reconciliation",
            "test_empty_reconciliation",
            "test_wrong_reconciliation",
            "test_alias_reconciliation",
            "test_malformed_reconciliation",
            "test_uppercase_reconciliation",
            "test_duplicate_reconciliation",
            "test_contradictory_reconciliation",
            "test_fill_state",
        )
    ):
        return "pe21_reconciliation"

    if "wallclock" in base:
        return "wallclock"

    if "pe38" in base:
        return "pe38_readiness"

    if base.startswith("test_pe35_") or "pe35_pe21" in base or "semantics_remain_bound" in base:
        return "pe35_handoff_recovery"

    if (
        base.startswith("test_pe37_")
        or base == "test_completion_proof_chain_traceability_drift_fails"
    ):
        return "pe37_traceability"

    if "pe25" in base:
        return "pe25_closure"

    if "pe31" in base:
        return "pe31_review"

    if "pe22" in base:
        return "pe22_risk_killswitch"

    if "pe23" in base:
        return "pe23_capital"

    if "pe24" in base:
        return "pe24_pilot"

    if "pe21" in base:
        return "pe21_reconciliation"

    if base.startswith("test_completion_proof_chain_"):
        for tag, partition in (
            ("pe31", "pe31_review"),
            ("pe22", "pe22_risk_killswitch"),
            ("pe23", "pe23_capital"),
            ("pe24", "pe24_pilot"),
            ("pe25", "pe25_closure"),
            ("pe35", "pe35_handoff_recovery"),
            ("pe37", "pe37_traceability"),
            ("pe38", "pe38_readiness"),
            ("wallclock", "wallclock"),
        ):
            if tag in base:
                return partition
        return "core_cross_chain"

    if base in {
        "test_unknown_extra_fields_fail",
        "test_authority_override_fields_fail",
        "test_completion_claim_without_proof_chain_fails",
    }:
        return "core_kwargs"

    if base.startswith("test_gap") or base == "test_completion_true_with_incomplete_evidence_fails":
        return "core_cross_chain"

    if base.startswith("test_planned_or_simulated") or base.startswith(
        "test_invalid_proof_lifecycle_states_fail"
    ):
        return "core_cross_chain"

    return "core_baseline_input"


@lru_cache(maxsize=1)
def collect_integration_owner_node_ids() -> tuple[str, ...]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", INTEGRATION_TEST_OWNER, "--collect-only", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in {0, 5}:
        raise RuntimeError(
            f"pytest collect failed for {INTEGRATION_TEST_OWNER}: {proc.stderr or proc.stdout}"
        )
    nodes: list[str] = []
    for line in proc.stdout.splitlines():
        match = _NODE_ID_RE.search(line)
        if match:
            nodes.append(match.group(1))
    return tuple(nodes)


@lru_cache(maxsize=1)
def integration_partition_inventory() -> dict[str, tuple[str, ...]]:
    by_partition: dict[str, list[str]] = {name: [] for name in ALL_PARTITIONS}
    unknown: list[str] = []
    for node_id in collect_integration_owner_node_ids():
        partition = classify_integration_node_id(node_id)
        if partition not in by_partition:
            unknown.append(node_id)
            continue
        by_partition[partition].append(node_id)
    if unknown:
        raise RuntimeError(f"unmapped integration nodes: {unknown[:5]}")
    return {key: tuple(sorted(values)) for key, values in by_partition.items() if values}


def integration_owner_node_count() -> int:
    return len(collect_integration_owner_node_ids())


def partition_union_node_count(partitions: frozenset[str]) -> int:
    inventory = integration_partition_inventory()
    seen: set[str] = set()
    for partition in partitions:
        if partition not in inventory:
            raise KeyError(f"unknown partition: {partition}")
        seen.update(inventory[partition])
    return len(seen)


def expand_partitions_to_pytest_targets(partitions: frozenset[str]) -> tuple[str, ...]:
    inventory = integration_partition_inventory()
    node_ids: set[str] = set()
    for partition in sorted(partitions):
        if partition not in inventory:
            raise KeyError(f"unknown partition: {partition}")
        node_ids.update(inventory[partition])
    return tuple(sorted(f"{INTEGRATION_TEST_OWNER}::{node_id}" for node_id in sorted(node_ids)))


def _file_text(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")


def partitions_for_changed_files(changed_files: list[str]) -> frozenset[str] | None:
    """Return required partition ids, empty set for graph-only, None for full integration owner."""
    from pathlib import Path

    files = frozenset(changed_files)
    partitions: set[str] = set(CORE_ALWAYS_PARTITIONS)

    if INTEGRATION_TEST_OWNER in files:
        return None

    if COMPLETION_FACADE_PATH in files:
        return None

    integration_scoped = False
    graph_only = True

    path_rules: tuple[tuple[str, str], ...] = (
        (
            "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
            "pe21_reconciliation",
        ),
        (
            "src/ops/bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
            "pe31_review",
        ),
        (
            "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
            "pe22_risk_killswitch",
        ),
        (
            "src/ops/bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py",
            "pe23_capital",
        ),
        (
            "src/ops/bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py",
            "pe24_pilot",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py",
            "pe25_closure",
        ),
        (
            "src/ops/bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py",
            "pe35_handoff_recovery",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py",
            "pe35_handoff_recovery",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py",
            "pe38_readiness",
        ),
        (
            "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
            "wallclock",
        ),
        (
            "src/ops/wallclock_session_evidence_v0.py",
            "wallclock",
        ),
    )

    validator_rules: tuple[tuple[str, str], ...] = (
        (
            "src/ops/durable_completion_validation/validators/reconciliation.py",
            "pe21_reconciliation",
        ),
        ("src/ops/durable_completion_validation/validators/recovery.py", "pe35_handoff_recovery"),
        ("src/ops/durable_completion_validation/validators/traceability.py", "pe37_traceability"),
        ("src/ops/durable_completion_validation/validators/operator_closure.py", "pe25_closure"),
        ("src/ops/durable_completion_validation/validators/event_stream.py", "pe38_readiness"),
    )

    for path, partition in path_rules:
        if path in files:
            partitions.add(partition)
            integration_scoped = True
            graph_only = False

    for path, partition in validator_rules:
        if path in files:
            partitions.add(partition)
            partitions.add("core_cross_chain")
            integration_scoped = True
            graph_only = False

    dc_prefix = "src/ops/durable_completion_validation/"
    for path in files:
        if not path.startswith(dc_prefix):
            continue
        name = Path(path).name
        if name == "graph.py":
            continue
        if name in {"models.py", "identity.py", "__init__.py"}:
            if name == "__init__.py":
                return None
            integration_scoped = True
            graph_only = False
            partitions.update({"core_cross_chain", "core_baseline_input"})
            continue
        if name.startswith("validators/") or path.endswith(".py") and "/validators/" in path:
            continue

    if not integration_scoped:
        return frozenset()

    if len(partitions - set(CORE_ALWAYS_PARTITIONS)) > 3:
        partitions.update({"core_baseline_input", "core_kwargs", "core_cross_chain"})

    return frozenset(partitions)


def estimate_partition_seconds(partitions: frozenset[str]) -> int:
    """Conservative serial estimate from historical ~21s/evaluate, ~0.5s static."""
    inventory = integration_partition_inventory()
    owner_text = _file_text(INTEGRATION_TEST_OWNER)
    evaluate_calls = owner_text.count(
        "evaluate_durable_run_primary_evidence_completion_integration("
    )
    eval_ratio = evaluate_calls / max(integration_owner_node_count(), 1)

    total = 0.0
    for partition in partitions:
        nodes = inventory.get(partition, ())
        eval_estimate = len(nodes) * eval_ratio
        total += eval_estimate * 21 + (len(nodes) - eval_estimate) * 0.5
    return int(total)
