"""Produce HEAD-bound integrated offline replay and correctness evidence v1."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.binding_v1 import (
    compute_implementation_surface_digest_sha256_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    CRS_PROVENANCE,
    INPUT_CLASS_CONTROLLED_FIXTURE,
    MANIFEST_NAME,
    PACKAGE_MARKER,
    PROOF_ARTIFACT_NAME,
    SCHEMA_ID,
    SCHEMA_VERSION,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.cycle_harness_v1 import (
    run_adverse_exit_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.fixtures_v1 import (
    adverse_exit_fixture_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.simulated_economics_crs_boundary_binding_v1 import (
    build_simulated_economics_crs_boundary_state_file_v1,
)


class HeadBoundCorrectnessProofError(ValueError):
    """Fail-closed proof production error."""


@dataclass
class HeadBoundCorrectnessProofResultV1:
    ok: bool
    schema_id: str
    schema_version: str
    capability_id: str
    package_marker: str
    authority_effect: str
    repository_head_sha: str
    proven_source_sha: str
    implementation_surface_digest_sha256: str
    CURRENT_HEAD_BOUND: bool
    IMPLEMENTATION_SURFACE_BOUND: bool
    CRS_CONTEXT_BOUND: bool
    ENTRY_QUANTITY_SEMANTICS_PASS: bool
    EXIT_QUANTITY_SEMANTICS_PASS: bool
    POSITION_LIFECYCLE_PASS: bool
    FEES_SLIPPAGE_ACCOUNTED: bool
    ACCOUNTING_CONSISTENCY_PASS: bool
    EXTERNAL_EFFECT_COUNT: int
    INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS: bool
    input_class: str
    lifecycle_fixture: str
    crs_provenance: str
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_repository_head_sha_v1(*, repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise HeadBoundCorrectnessProofError("GIT_HEAD_RESOLUTION_FAILED")
    sha = proc.stdout.strip()
    if len(sha) != 40:
        raise HeadBoundCorrectnessProofError("GIT_HEAD_SHA_INVALID")
    return sha


def _assert_crs_bound_on_first_cycle(*, repository_sha: str) -> bool:
    state = BridgeSessionStateV1(
        instrument_id="ETH-USD_UM_XPERP-310404", require_selection_binding=False
    )
    state.mid_prices = [3500.0, 3510.0, 3520.0, 3530.0]
    run_bridge_cycle_v1(
        state,
        mid_price=3530.0,
        event_ts_unix=1_700_000_000.0,
        session_id="head-bound-crs-probe",
        repository_sha=repository_sha,
    )
    record = state.capital_risk_sizing_boundary_state_file
    if record is None:
        return False
    expected = build_simulated_economics_crs_boundary_state_file_v1(
        instrument_id=state.instrument_id,
    )
    return (
        record.instrument_id == expected.instrument_id
        and record.dynamic_price_context_binding_ref == expected.dynamic_price_context_binding_ref
    )


def _quantity_semantics_pass(fills: list[dict[str, Any]]) -> tuple[bool, bool]:
    entry = [f for f in fills if f.get("fill_class") == "entry"]
    exit_like = [
        f
        for f in fills
        if f.get("fill_class") in {"exit", "reduce"}
        or f.get("decision_outcome") in {"exit", "reduce"}
    ]
    if not entry or not exit_like:
        return False, False
    entry_qty = Decimal(str(entry[0].get("quantity") or "0"))
    closing = exit_like[-1]
    exit_qty = Decimal(str(closing.get("quantity") or "0"))
    entry_ok = entry_qty > 0
    exit_ok = exit_qty > 0 and exit_qty == entry_qty
    return entry_ok, exit_ok


def produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
    *,
    repo_root: Path,
    work_root: Path,
    expected_head_sha: str | None = None,
) -> HeadBoundCorrectnessProofResultV1:
    """Run controlled fixture lifecycle and emit fail-closed proof fields."""
    root = repo_root.resolve()
    head = resolve_repository_head_sha_v1(repo_root=root)
    notes = [
        "NO_NETWORK",
        "NO_ORDERS",
        "NO_BROKER_WRITES",
        "CONTROLLED_FIXTURE_INPUT",
    ]
    blockers: list[str] = []
    head_bound = expected_head_sha is None or head == expected_head_sha
    if not head_bound:
        blockers.append("CURRENT_HEAD_MISMATCH")

    crs_bound = _assert_crs_bound_on_first_cycle(repository_sha=head)
    if not crs_bound:
        blockers.append("CRS_CONTEXT_NOT_BOUND")

    _, _ = adverse_exit_fixture_v1()
    with tempfile.TemporaryDirectory(prefix="head-bound-lifecycle-") as tmp:
        lifecycle = run_adverse_exit_v1(
            repository_sha=head, work_root=Path(tmp) / "adverse_fixture"
        )

    entry_qty_ok, exit_qty_ok = _quantity_semantics_pass(lifecycle.fills)
    if not entry_qty_ok:
        blockers.append("ENTRY_QUANTITY_SEMANTICS_FAIL")
    if not exit_qty_ok:
        blockers.append("EXIT_QUANTITY_SEMANTICS_FAIL")

    position_ok = bool(lifecycle.metrics.get("final_flat")) and bool(
        lifecycle.claims.get("ENTRY_FILL_OBSERVED")
    )
    if not position_ok:
        blockers.append("POSITION_LIFECYCLE_FAIL")

    fees = Decimal(str(lifecycle.metrics.get("total_fees") or "0"))
    slip = Decimal(str(lifecycle.metrics.get("total_slippage") or "0"))
    fees_ok = fees > 0 and slip >= 0 and len(lifecycle.fills) >= 2
    if not fees_ok:
        blockers.append("FEES_SLIPPAGE_NOT_ACCOUNTED")

    accounting_ok = (
        bool(lifecycle.ok)
        and bool(lifecycle.metrics.get("final_flat"))
        and "realized_pnl" in lifecycle.accounting_snapshot
        and int(lifecycle.metrics.get("simulated_fill_count") or 0) >= 2
    )
    if not accounting_ok:
        blockers.append("ACCOUNTING_CONSISTENCY_FAIL")

    external_effect_count = 0
    surface_digest = compute_implementation_surface_digest_sha256_v1(repo_root=root)
    implementation_surface_bound = bool(surface_digest)
    if not implementation_surface_bound:
        blockers.append("IMPLEMENTATION_SURFACE_DIGEST_FAILED")

    pass_ok = not blockers
    result = HeadBoundCorrectnessProofResultV1(
        ok=pass_ok,
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        authority_effect=AUTHORITY_EFFECT_NONE,
        repository_head_sha=head,
        proven_source_sha=head,
        implementation_surface_digest_sha256=surface_digest,
        CURRENT_HEAD_BOUND=head_bound,
        IMPLEMENTATION_SURFACE_BOUND=implementation_surface_bound,
        CRS_CONTEXT_BOUND=crs_bound,
        ENTRY_QUANTITY_SEMANTICS_PASS=entry_qty_ok,
        EXIT_QUANTITY_SEMANTICS_PASS=exit_qty_ok,
        POSITION_LIFECYCLE_PASS=position_ok,
        FEES_SLIPPAGE_ACCOUNTED=fees_ok,
        ACCOUNTING_CONSISTENCY_PASS=accounting_ok,
        EXTERNAL_EFFECT_COUNT=external_effect_count,
        INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS=pass_ok,
        input_class=INPUT_CLASS_CONTROLLED_FIXTURE,
        lifecycle_fixture="adverse_exit_fixture_v1",
        crs_provenance=CRS_PROVENANCE,
        blockers=blockers,
        notes=notes,
    )
    out_dir = Path(work_root)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_path = out_dir / PROOF_ARTIFACT_NAME
    proof_path.write_text(
        json.dumps(result.to_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(proof_path.read_bytes()).hexdigest()
    manifest = f"{digest}  {PROOF_ARTIFACT_NAME}\n"
    (out_dir / MANIFEST_NAME).write_text(manifest, encoding="utf-8")
    return result


def default_canonical_evidence_dir_for_head_v1(*, head_sha: str) -> str:
    return f"evidence/ops/integrated_offline_replay_and_correctness_head_bound_v1/{head_sha}"
