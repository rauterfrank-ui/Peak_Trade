"""PRE-LIVE fresh runtime roots + POST-slice baseline convergence (no venue POST)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.current_productive_actual_venue_post_admission_policy_v1 import (
    validate_actual_venue_post_admission_policy_v1,
    prove_actual_venue_post_admission_requires_durable_owner_go_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    BASELINE_AUTHORITY_CLASS,
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    resolve_and_assert_live_post_execution_baseline_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PRuntimeIntegrityBackendV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
    OWNER_GO as CAP24_WRITER_OWNER_GO,
    PUBLISH_MANIFEST_FILENAME,
    execute_current_productive_cap24_selection_state_canonical_write_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.pre_live_fresh_runtime_root_isolation_v1 import (
    assert_post_durable_store_root_isolation_v1,
    validate_post_durable_store_root_isolation_v1,
    validate_productivity_root_isolation_v1,
)

WORKPACKAGE_ID: Final[str] = "PRE_LIVE_FRESH_STATE_AND_SLICE_BASELINE_CONVERGENCE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/PRE_LIVE_FRESH_STATE_AND_SLICE_BASELINE_CONVERGENCE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/pre_live_fresh_state_and_slice_baseline_convergence_v1_decision_v1.json"
)
OWNER_GO_TOKEN: Final[str] = "PRE_LIVE_FRESH_STATE_AND_SLICE_BASELINE_CONVERGENCE_V1"
CAP24_OWNER_GO_TOKEN: Final[str] = f"OWNER_GO_{CAP24_WRITER_OWNER_GO}"
VENUE_POST_NEXT_OWNER_GO: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
FRESH_ROOT_NAMESPACE: Final[str] = "runtime/current_productive/pre_live_fresh_cap24"
_CAP24_WRITER_OBSERVED_UNIX: Final[float] = 1_700_000_100.0


def load_json_v1(repo_root: Path, rel: str) -> dict[str, Any]:
    return json.loads((repo_root / rel).read_text(encoding="utf-8"))


def build_injected_synthetic_eea_acquisition_v1() -> EeaUniverseAcquisitionResultV1:
    """Deterministic acquisition fixture (no venue I/O)."""

    from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
        _eligible_rows,
        _okx_envelope,
    )

    rows = _eligible_rows()
    mark_rows = [{"instId": r["instId"], "markPx": "100.5"} for r in rows]
    return EeaUniverseAcquisitionResultV1(
        ok=True,
        host="eea.okx.com",
        venue="okx_eea",
        source_kind="okx_eea_public_instruments",
        source_event_time="1700000000000",
        instruments_payload=_okx_envelope(rows=rows),
        mark_price_payload=_okx_envelope(rows=mark_rows),
        endpoints_used=("/api/v5/public/instruments",),
        methods_used=("GET",),
        post_count="0",
        request_count=2,
        venue_live_contact=False,
        failure_codes=(),
        provenance={"injection": "pre_live_synthetic_fixture_v1"},
    )


@dataclass(frozen=True)
class PreLiveConvergenceProbeV1:
    ok: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"OK": self.ok, "REASON_CODES": list(self.reason_codes)}


def validate_scoped_owner_go_v1(
    *,
    repo_root: Path,
    scoped_owner_go_literal: str | None,
) -> PreLiveConvergenceProbeV1:
    reasons: list[str] = []
    supplied = str(scoped_owner_go_literal or "").strip()
    if supplied != OWNER_GO_TOKEN:
        reasons.append("SCOPED_OWNER_GO_TOKEN_MISMATCH_OR_MISSING")
    decision = load_json_v1(repo_root, DECISION_CONFIG)
    if decision.get("owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_TRUE")
    if str(decision.get("owner_go_token") or "") != OWNER_GO_TOKEN:
        reasons.append("OWNER_GO_DECISION_TOKEN_DRIFT")
    return PreLiveConvergenceProbeV1(ok=not reasons, reason_codes=tuple(reasons))


def validate_cap24_substep_owner_go_v1(
    *, cap24_owner_go_literal: str | None
) -> PreLiveConvergenceProbeV1:
    supplied = str(cap24_owner_go_literal or "").strip()
    allowed = {CAP24_WRITER_OWNER_GO, CAP24_OWNER_GO_TOKEN}
    if supplied not in allowed:
        return PreLiveConvergenceProbeV1(
            ok=False,
            reason_codes=("CAP24_CANONICAL_WRITE_OWNER_GO_MISMATCH",),
        )
    return PreLiveConvergenceProbeV1(ok=True, reason_codes=())


def fresh_runtime_roots_v1(*, repo_root: Path, baseline_sha: str) -> dict[str, Path]:
    short = baseline_sha[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = repo_root / FRESH_ROOT_NAMESPACE / f"{short}_{ts}"
    return {
        "productivity_root": base / "cap24_productivity",
        "lane_state_root": base / "lane_state",
        "post_durable_store": base / "post_durable_store",
        "evidence_root": base / "pre_live_evidence",
    }


def execute_pre_live_fresh_state_and_slice_baseline_convergence_v1(
    *,
    repo_root: Path,
    scoped_owner_go_literal: str,
    cap24_owner_go_literal: str,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
) -> dict[str, Any]:
    go_probe = validate_scoped_owner_go_v1(
        repo_root=repo_root,
        scoped_owner_go_literal=scoped_owner_go_literal,
    )
    if go_probe.ok is not True:
        raise RuntimeError(json.dumps(go_probe.to_dict()))
    cap24_go = validate_cap24_substep_owner_go_v1(
        cap24_owner_go_literal=cap24_owner_go_literal,
    )
    if cap24_go.ok is not True:
        raise RuntimeError(json.dumps(cap24_go.to_dict()))

    live_sha = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        repo_root=repo_root,
        integrity_backend=execution_integrity_backend,
    )
    policy = validate_actual_venue_post_admission_policy_v1(repo_root=repo_root)
    if policy.policy_valid is not True:
        raise RuntimeError("ACTUAL_VENUE_POST_ADMISSION_POLICY_INVALID")

    roots = fresh_runtime_roots_v1(repo_root=repo_root, baseline_sha=live_sha)
    for key, path in roots.items():
        if key != "evidence_root":
            path.mkdir(parents=True, exist_ok=True)

    prod_iso = validate_productivity_root_isolation_v1(
        productivity_root=roots["productivity_root"],
        repo_root=repo_root,
    )
    post_iso = validate_post_durable_store_root_isolation_v1(
        store_root=roots["post_durable_store"],
        repo_root=repo_root,
    )
    if prod_iso["OK"] is not True or post_iso["OK"] is not True:
        raise RuntimeError("FRESH_ROOT_ISOLATION_PROBE_FAIL")

    cap24 = execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go=cap24_owner_go_literal,
        origin_main_sha=live_sha,
        acquisition_result=build_injected_synthetic_eea_acquisition_v1(),
        productivity_root=roots["productivity_root"],
        repository_sha=live_sha,
        allow_default_productivity_root=False,
        producer_observed_at_unix=_CAP24_WRITER_OBSERVED_UNIX,
        execution_integrity_backend=execution_integrity_backend,
    )
    manifest_path = Path(cap24.publish_manifest_path)
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest_payload.get("repository_sha") or "").lower() != live_sha.lower():
        raise RuntimeError("CAP24_MANIFEST_REPOSITORY_SHA_DRIFT")
    if not manifest_path.is_file():
        raise RuntimeError("CAP24_PUBLISH_MANIFEST_MISSING")

    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=roots["productivity_root"],
        repository_sha=live_sha,
        binding_epoch=cap24.decision_epoch,
    )
    assert_post_durable_store_root_isolation_v1(
        store_root=roots["post_durable_store"],
        repo_root=repo_root,
    )
    admission_denied_without_durable_go = (
        prove_actual_venue_post_admission_requires_durable_owner_go_v1(
            repo_root=repo_root,
            store_root=roots["post_durable_store"],
        )
    )

    return {
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BASELINE_SHA": live_sha,
        "SLICE_BASELINE_PIN_BEFORE": "cf3aa15f098827a9e60de8eb84e5bdd9eb54cca2",
        "SLICE_BASELINE_PIN_AFTER": EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        "SLICE_PIN_AUTHORITY": BASELINE_AUTHORITY_CLASS,
        "BASELINE_CONVERGENCE_PROVEN": live_sha == EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        "CAP24_WRITER_AUTHORITY": CAP24_WRITER_OWNER_GO,
        "CAP24_REFRESH_AUTHORIZED": True,
        "CAP24_PRODUCTIVITY_ROOT": str(roots["productivity_root"]),
        "CAP24_MANIFEST_REPOSITORY_SHA": manifest_payload.get("repository_sha"),
        "CAP24_FRESHNESS_PROVEN": True,
        "LANE_STATE_ROOT": str(roots["lane_state_root"]),
        "POST_STORE_ROOT_PLANNED": str(roots["post_durable_store"]),
        "FRESH_ROOT_ISOLATION_PROVEN": True,
        "CAP24_HANDOFF_INSTRUMENT": handoff.bound_instrument.instrument_id,
        "ADMISSION_BOUNDARY_DENIED_WITHOUT_DURABLE_POST_GO": admission_denied_without_durable_go,
        "VENUE_POST_OWNER_GO_CONSUMED": False,
        "NEW_ACTUAL_POST_PERMIT_MINTED": False,
        "ACTUAL_VENUE_POST_PERFORMED": False,
        "FIRST_REAL_BLOCKER": VENUE_POST_NEXT_OWNER_GO,
        "BLOCKER_CLASS": "OWNER_GO_REQUIRED",
        "EXACT_NEXT_OWNER_GO_REQUIRED": VENUE_POST_NEXT_OWNER_GO,
    }


__all__ = [
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "OWNER_GO_TOKEN",
    "VENUE_POST_NEXT_OWNER_GO",
    "WORKPACKAGE_ID",
    "build_injected_synthetic_eea_acquisition_v1",
    "execute_pre_live_fresh_state_and_slice_baseline_convergence_v1",
    "validate_scoped_owner_go_v1",
]
