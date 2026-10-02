"""Integrated Paper-Shadow economic evidence bundle (HEAD-bound, offline) v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    PROOF_ARTIFACT_NAME,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.verifier_v1 import (
    verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.bundle_verifier_v1 import (
    verify_integrated_paper_shadow_observation_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (
    run_integrated_paper_shadow_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.evidence_v1 import (
    write_observation_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    attest_capability_sources_no_order_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    CAPABILITY_ID as OBS_CAPABILITY_ID,
)
from src.ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1 import (
    plan_observation_session_lifecycle_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    verify_full_economic_reconstruction_v1,
)

BUNDLE_SCHEMA_ID = "ops.integrated_paper_shadow_economic_evidence_bundle_head_bound_v1"
BUNDLE_ARTIFACT = "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE_BUNDLE.json"
BUNDLE_MANIFEST = "evidence_manifest.sha256"

PREDECESSOR_MD_EVIDENCE_RELPATH = (
    "evidence/ops/integrated_paper_shadow_productive_6h_technical_closeout"
)


def _relative_or_absolute(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


@dataclass
class EconomicEvidenceBundleResultV1:
    verified: bool
    schema_id: str
    INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE: bool
    INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
    *,
    repo_root: Path,
    bundle_root: Path,
    correctness_evidence_root: Path,
) -> EconomicEvidenceBundleResultV1:
    root = repo_root.resolve()
    bundle_root = Path(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    notes = ["OFFLINE_BOUNDED", "NO_NETWORK", "NO_ORDERS"]

    correctness = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=correctness_evidence_root,
        repo_root=root,
        require_current_head=True,
    )
    if not correctness.verified:
        blockers.extend(f"CORRECTNESS:{b}" for b in correctness.blockers)

    bridge_dir = bundle_root / "controlled_wallclock_bridge"
    bridge_dir.mkdir(parents=True, exist_ok=True)
    mids = [3500.0, 3510.0, 3520.0, 3550.0, 3600.0, 3650.0, 3700.0, 3750.0]
    state, cycles = run_bridge_cycles_from_mids_v1(
        mids,
        session_id="head-bound-economic-bridge",
        require_selection_binding=False,
    )
    bridge_payload = {
        "cycles": len(cycles),
        "fill_count": len(state.fill_ledger),
        "portfolio_snapshot": dict(state.portfolio.snapshot()),
        "orders_authorized": False,
        "execution_eligible": False,
        "input_class": "CONTROLLED_MID_SEQUENCE",
    }
    bridge_path = bridge_dir / "bridge_summary.json"
    bridge_path.write_text(
        json.dumps(bridge_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    reconstruction = verify_full_economic_reconstruction_v1(
        cycle_ledger=state.cycle_ledger,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
    )
    recon_path = bridge_dir / "full_economic_reconstruction_verifier.json"
    recon_path.write_text(
        json.dumps(reconstruction.to_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not reconstruction.ok:
        blockers.extend(f"BRIDGE_RECON:{b}" for b in reconstruction.blockers)

    obs_dir = bundle_root / "observation_offline_cycle"
    lifecycle = plan_observation_session_lifecycle_v1()
    cycle = run_integrated_paper_shadow_observation_cycle_v1(
        mode="observation",
        reference_price=Decimal("3500"),
        intended_side="HOLD",
    )
    head_sha = str(correctness.proof.get("repository_head_sha") if correctness.proof else "")
    no_order = attest_capability_sources_no_order_v1(
        repo_root=root,
        relative_paths=[
            "src/ops/integrated_paper_shadow_observation_session_v1/entrypoint_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/no_order_guard_v1.py",
        ],
    )
    write_observation_evidence_bundle_v1(
        evidence_root=obs_dir,
        cycle=cycle,
        lifecycle=lifecycle,
        no_order=no_order,
        config_snapshot={"orders_allowed": False, "mode": "observation"},
        code_identity={"capability_id": OBS_CAPABILITY_ID, "repository_head_sha": head_sha},
        session_identity={"session_id": "head-bound-offline-observation", "offline": True},
    )
    obs_verify = verify_integrated_paper_shadow_observation_evidence_bundle_v1(
        evidence_root=obs_dir,
        require_cycle_pass=True,
    )
    if not obs_verify.verified:
        blockers.extend(f"OBSERVATION:{b}" for b in obs_verify.blockers)

    proof = correctness.proof or {}
    bundle_doc = {
        "schema_id": BUNDLE_SCHEMA_ID,
        "schema_version": "v1",
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "repository_head_sha": proof.get("repository_head_sha"),
        "decision_provenance": "run_integrated_offline_trading_logic_replay_v1",
        "strategy_intent_owner": "trading.master_v2.double_play_entry_exit_policy_v0",
        "capital_risk_context_provenance": proof.get("crs_provenance"),
        "correctness_evidence_relpath": _relative_or_absolute(root, correctness_evidence_root),
        "predecessor_market_data_evidence_relpath": PREDECESSOR_MD_EVIDENCE_RELPATH,
        "predecessor_reuse_only": True,
        "controlled_wallclock_bridge_dir": "controlled_wallclock_bridge",
        "observation_offline_cycle_dir": "observation_offline_cycle",
        "bridge_reconstruction_pass": reconstruction.ok,
        "observation_bundle_verified": obs_verify.verified,
        "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE": reconstruction.ok and obs_verify.verified,
        "orders_submitted": False,
        "broker_writes_performed": False,
        "network_used": False,
        "credentials_used": False,
    }
    bundle_path = bundle_root / BUNDLE_ARTIFACT
    bundle_path.write_text(
        json.dumps(bundle_doc, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    lines = []
    for rel in (
        BUNDLE_ARTIFACT,
        "controlled_wallclock_bridge/bridge_summary.json",
        "controlled_wallclock_bridge/full_economic_reconstruction_verifier.json",
    ):
        p = bundle_root / rel
        if p.is_file():
            lines.append(f"{_sha256_file(p)}  {rel}")
    (bundle_root / BUNDLE_MANIFEST).write_text(
        "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
    )

    verified = not blockers and bundle_doc["INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE"] is True
    if not verified and not blockers:
        blockers.append("BUNDLE_INTEGRITY_FAIL_CLOSED")

    return EconomicEvidenceBundleResultV1(
        verified=verified,
        schema_id=BUNDLE_SCHEMA_ID,
        INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE=bundle_doc[
            "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE"
        ],
        INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED=verified,
        blockers=sorted(set(blockers)),
        notes=notes,
    )


def verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
    *,
    bundle_root: Path,
    repo_root: Path,
    correctness_evidence_root: Path,
) -> EconomicEvidenceBundleResultV1:
    blockers: list[str] = []
    bundle_path = Path(bundle_root) / BUNDLE_ARTIFACT
    if not bundle_path.is_file():
        return EconomicEvidenceBundleResultV1(
            verified=False,
            schema_id=BUNDLE_SCHEMA_ID,
            INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE=False,
            INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED=False,
            blockers=["BUNDLE_ARTIFACT_MISSING"],
        )
    doc = json.loads(bundle_path.read_text(encoding="utf-8"))
    if doc.get("INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE") is not True:
        blockers.append("INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE_NOT_TRUE")
    correctness = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=correctness_evidence_root,
        repo_root=repo_root,
        require_current_head=True,
    )
    if not correctness.verified:
        blockers.extend(f"CORRECTNESS:{b}" for b in correctness.blockers)
    obs_verify = verify_integrated_paper_shadow_observation_evidence_bundle_v1(
        evidence_root=Path(bundle_root) / "observation_offline_cycle",
        require_cycle_pass=True,
    )
    if not obs_verify.verified:
        blockers.extend(f"OBSERVATION:{b}" for b in obs_verify.blockers)
    recon_path = (
        Path(bundle_root) / "controlled_wallclock_bridge/full_economic_reconstruction_verifier.json"
    )
    if recon_path.is_file():
        recon = json.loads(recon_path.read_text(encoding="utf-8"))
        if recon.get("ok") is not True:
            blockers.append("BRIDGE_RECONSTRUCTION_NOT_OK")
    else:
        blockers.append("BRIDGE_RECONSTRUCTION_MISSING")
    verified = not blockers
    return EconomicEvidenceBundleResultV1(
        verified=verified,
        schema_id=BUNDLE_SCHEMA_ID,
        INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE=doc.get(
            "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE"
        )
        is True,
        INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED=verified,
        blockers=sorted(set(blockers)),
        notes=["VERIFY_ONLY"],
    )
