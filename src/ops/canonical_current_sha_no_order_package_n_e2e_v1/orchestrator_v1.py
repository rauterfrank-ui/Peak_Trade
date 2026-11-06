"""Thin current-SHA no-order → Package-N → EG-I82 owner wiring orchestrator.

Calls existing Cap 7.1/7.2, Package-N, I16, I17, I52, I56, I61, I65, and
EG-I82 APIs. Does not mutate trading logic, owner join semantics, or
activation/promotion. Never sets COMPLETE_CURRENT_SYSTEM_E2E_PROVEN=true.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.analytics.explorer import parse_experiment_summary_with_identity_join_v1
from src.experiments.eg_i82_end_to_end_live_owner_graph_attestation_v1 import (
    attest_eg_i82_end_to_end_live_owner_graph_v1,
)
from src.experiments.eg_i82_join_verifier_v1 import verify_eg_i82_cross_lane_join_v1
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    experiment_config_from_mapping,
    produce_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    produce_experiment_lineage_ref_v1,
)
from src.ingress.capsules.evidence_capsule_builder import build_evidence_capsule
from src.ingress.capsules.evidence_capsule import parse_evidence_capsule_with_identity_join_v1
from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.levelup.v0_io import write_manifest as write_levelup_manifest
from src.levelup.v0_models import (
    EvidenceBundleRefV0,
    LevelUpManifestV0,
    SliceContractV0,
    parse_levelup_manifest_with_identity_join_v1,
)
from src.live_eval.live_session_eval import (
    compute_metrics,
    parse_live_session_metrics_with_identity_join_v1,
)
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.constants_v1 import (
    CAMPAIGN_ID,
    COMPLETE_CURRENT_SYSTEM_E2E_PROVEN,
    CONFIG_RELPATH,
    CONTRACT_ID,
    DETERMINISTIC_TS_MS,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    I65_RUN_TYPE,
    OUT_OPS_PREFIX,
    PRODUCTION_INSTRUMENT_ID,
    RUN_ID_PATTERN,
)
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.i61_fill_mapper_v1 import (
    map_cap71_fills_to_i61_fills_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    CAPABILITY_ID as I17_CAPABILITY_ID,
    PREREGISTRATION_SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    parse_preregistration_contract_v1,
    parse_preregistration_contract_with_identity_join_v1,
    validate_preregistration_contract_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    EVIDENCE_FILENAME as CAP71_EVIDENCE_FILENAME,
    FILL_LEDGER_FILENAME,
    INTENT_LEDGER_FILENAME,
    MANIFEST_FILENAME,
    NO_ORDER_PROOF_FILENAME as CAP71_NO_ORDER_PROOF_FILENAME,
    RESULT_FILENAME as CAP71_RESULT_FILENAME,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.cycle_harness_v1 import (
    build_capability_evidence_v1 as build_cap71_evidence_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.persistence_v1 import (
    write_manifest as write_cap71_manifest,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    EVIDENCE_FILENAME as CAP72_EVIDENCE_FILENAME,
    NO_ORDER_PROOF_FILENAME as CAP72_NO_ORDER_PROOF_FILENAME,
    RESULT_FILENAME as CAP72_RESULT_FILENAME,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.cycle_harness_v1 import (
    build_capability_evidence_v1 as build_cap72_evidence_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    write_manifest as write_cap72_manifest,
)
from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)


class CanonicalCurrentShaNoOrderPackageNE2EError(ValueError):
    """Fail-closed current-SHA no-order Package-N wiring error."""


@dataclass
class CanonicalCurrentShaNoOrderPackageNE2EResultV1:
    ok: bool
    contract_id: str
    run_id: str
    repository_sha: str
    evidence_root: str
    package_n_sha256: str
    source_experiment_id: str
    combined_evidence_digest: str
    owner_identities: dict[str, str] = field(default_factory=dict)
    package_n_same_across_all_owners: bool = False
    manifest_verify_ok: bool = False
    complete_current_system_e2e_proven: bool = COMPLETE_CURRENT_SYSTEM_E2E_PROVEN
    network_effect: str = "NONE"
    order_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "contract_id": self.contract_id,
            "run_id": self.run_id,
            "repository_sha": self.repository_sha,
            "evidence_root": self.evidence_root,
            "package_n_sha256": self.package_n_sha256,
            "source_experiment_id": self.source_experiment_id,
            "combined_evidence_digest": self.combined_evidence_digest,
            "owner_identities": dict(self.owner_identities),
            "package_n_same_across_all_owners": self.package_n_same_across_all_owners,
            "manifest_verify_ok": self.manifest_verify_ok,
            "COMPLETE_CURRENT_SYSTEM_E2E_PROVEN": False,
            "complete_current_system_e2e_proven": False,
            "NETWORK_EFFECT": self.network_effect,
            "ORDER_EFFECT": self.order_effect,
        }


def _reject(message: str) -> None:
    raise CanonicalCurrentShaNoOrderPackageNE2EError(message)


def combined_evidence_digest_v1(cap71_digest: str, cap72_digest: str) -> str:
    """sha256(cap71.evidence_digest || cap72.evidence_digest)."""
    if not cap71_digest or not cap72_digest:
        _reject("source_experiment_id mismatch: evidence digest missing")
    return hashlib.sha256(f"{cap71_digest}{cap72_digest}".encode("ascii")).hexdigest()


def evidence_root_for_run_v1(repo_root: Path, run_id: str) -> Path:
    return Path(repo_root) / OUT_OPS_PREFIX / EVIDENCE_DIRNAME / run_id


def validate_isolated_run_root_v1(repo_root: Path, run_root: Path) -> Path:
    """Fail-closed isolated out/ops run-root contract."""
    repo = Path(repo_root).resolve()
    root = Path(run_root).resolve()
    if is_under_tmp(root) or is_under_tmp(repo):
        _reject("tmp runtime root forbidden")
    posix = root.as_posix()
    if "docs/evidence" in posix or (repo / "docs" / "evidence") in root.parents:
        _reject("docs/evidence write forbidden")
    if "tests/fixtures" in posix:
        _reject("fixture I17 rejected")
    expected_parent = (repo / OUT_OPS_PREFIX / EVIDENCE_DIRNAME).resolve()
    if root.parent != expected_parent:
        _reject("run root must be under out/ops/")
    try:
        root.relative_to(repo / OUT_OPS_PREFIX)
    except ValueError:
        _reject("run root must be under out/ops/")
    if root.exists():
        _reject("pre-existing evidence root")
    return root


def require_matching_shas_v1(
    expected: str,
    cap71_sha: str,
    cap72_sha: str,
) -> None:
    if expected != cap71_sha:
        _reject("repository SHA mismatch")
    if cap71_sha != cap72_sha:
        _reject("Cap7.1/7.2 SHA mismatch")


def require_source_experiment_id_v1(manifest: Mapping[str, Any], expected: str) -> None:
    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        _reject("source_experiment_id mismatch")
    actual = provenance.get("source_experiment_id")
    if actual != expected:
        _reject("source_experiment_id mismatch")
    identity = manifest.get("experiment_identity_id")
    if actual == identity:
        _reject("source_experiment_id mismatch")


def require_identical_package_n_v1(owner_identities: Mapping[str, str], expected: str) -> None:
    if not owner_identities:
        _reject("divergent Package-N across owners")
    for owner, identity in owner_identities.items():
        if identity != expected:
            _reject(f"divergent Package-N across owners: {owner}")


def require_current_run_i17_v1(payload: Mapping[str, Any]) -> None:
    if bool(payload.get("fixture_non_authoritative")):
        _reject("fixture I17 rejected")
    evidence_root = str(payload.get("evidence_root") or "")
    if "tests/fixtures" in evidence_root.replace("\\", "/"):
        _reject("fixture I17 rejected")
    if str(payload.get("expected_repository_sha") or "") != EXPECTED_ORIGIN_MAIN_SHA:
        _reject("repository SHA mismatch")


def require_i56_artifacts_nonempty_v1(capsule: Mapping[str, Any]) -> None:
    artifacts = capsule.get("artifacts") or []
    if not isinstance(artifacts, list) or len(artifacts) < 1:
        _reject("empty I56 capsule rejected")


def require_i61_metrics_nonempty_v1(metrics: Mapping[str, Any]) -> None:
    if int(metrics.get("total_fills") or 0) == 0:
        _reject("empty I61 fills rejected")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _persist_cap71(cap71_dir: Path, evidence: Any) -> dict[str, Any]:
    payload = evidence.to_dict()
    claims = payload["claims"]
    metrics = payload["metrics"]
    _write_json(cap71_dir / CAP71_EVIDENCE_FILENAME, payload)
    _write_json(
        cap71_dir / CAP71_RESULT_FILENAME,
        {
            "ok": evidence.ok,
            "capability_id": evidence.capability_id,
            "repository_sha": evidence.repository_sha,
            "evidence_digest": payload["evidence_digest"],
        },
    )
    _write_jsonl(cap71_dir / FILL_LEDGER_FILENAME, list(metrics.get("fills") or []))
    _write_jsonl(cap71_dir / INTENT_LEDGER_FILENAME, list(metrics.get("intents") or []))
    _write_json(
        cap71_dir / CAP71_NO_ORDER_PROOF_FILENAME,
        {
            "NETWORK_SESSION_STARTED": bool(claims.get("NETWORK_SESSION_STARTED")),
            "ORDER_SIDE_EFFECT_OCCURRED": bool(claims.get("ORDER_SIDE_EFFECT_OCCURRED")),
            "AUTHORIZATION_CONSUMED": bool(claims.get("AUTHORIZATION_CONSUMED")),
        },
    )
    write_cap71_manifest(
        cap71_dir,
        (
            CAP71_EVIDENCE_FILENAME,
            CAP71_RESULT_FILENAME,
            FILL_LEDGER_FILENAME,
            INTENT_LEDGER_FILENAME,
            CAP71_NO_ORDER_PROOF_FILENAME,
        ),
    )
    return payload


def _persist_cap72(cap72_dir: Path, evidence: Any) -> dict[str, Any]:
    payload = evidence.to_dict()
    claims = payload["claims"]
    _write_json(cap72_dir / CAP72_EVIDENCE_FILENAME, payload)
    _write_json(
        cap72_dir / CAP72_RESULT_FILENAME,
        {
            "ok": evidence.ok,
            "capability_id": evidence.capability_id,
            "repository_sha": evidence.repository_sha,
            "evidence_digest": payload["evidence_digest"],
        },
    )
    _write_json(
        cap72_dir / CAP72_NO_ORDER_PROOF_FILENAME,
        {
            "NETWORK_SESSION_STARTED": bool(claims.get("NETWORK_SESSION_STARTED")),
            "ORDER_SIDE_EFFECT_OCCURRED": bool(claims.get("ORDER_SIDE_EFFECT_OCCURRED")),
            "REAL_EXECUTION_ADAPTER_CONSTRUCTED": bool(
                claims.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED")
            ),
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": bool(
                claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE")
            ),
        },
    )
    write_cap72_manifest(
        cap72_dir,
        (
            CAP72_EVIDENCE_FILENAME,
            CAP72_RESULT_FILENAME,
            CAP72_NO_ORDER_PROOF_FILENAME,
        ),
    )
    return payload


def _require_no_order_offline(cap71: Mapping[str, Any], cap72: Mapping[str, Any]) -> None:
    for payload, label in ((cap71, "Cap7.1"), (cap72, "Cap7.2")):
        claims = payload.get("claims") if isinstance(payload.get("claims"), Mapping) else payload
        if bool(claims.get("NETWORK_SESSION_STARTED")):
            _reject(f"{label} network session started")
        if bool(claims.get("ORDER_SIDE_EFFECT_OCCURRED")):
            _reject(f"{label} order side effect")
        if bool(claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE")):
            _reject(f"{label} credential access reachable")
        if bool(claims.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED")):
            _reject(f"{label} real execution adapter constructed")
        if bool(claims.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED")):
            _reject(f"{label} public-md network session observed")


def _build_i17_prereg(
    *,
    run_id: str,
    repository_sha: str,
    evidence_root_rel: str,
) -> dict[str, Any]:
    earliest_start = 1_700_000_000.0
    expires_at = earliest_start + 3600.0
    token = f"{CONFIRM_TOKEN_PREFIX}{secrets.token_hex(24)}"
    fingerprint = fingerprint_confirm_token(token)
    payload = {
        "contract_version": "v1",
        "schema_version": PREREGISTRATION_SCHEMA_VERSION,
        "capability_id": I17_CAPABILITY_ID,
        "session_id": run_id,
        "purpose": "CURRENT_RUN_OFFLINE_NO_ORDER_PACKAGE_N_WIRING_IDENTITY_CONSUMER",
        "venue": "OKX",
        "market_type": "FUTURES",
        "instrument_allowlist": [PRODUCTION_INSTRUMENT_ID],
        "instrument_denylist": [],
        "strategy_portfolio_id": "master_v2_double_play_single_future_v1",
        "strategy_component_identities": [
            "src.ops.simulated_entry_reduce_exit_actionability_evidence_v1",
            "src.ops.single_future_stateful_no_order_runtime_activation_v1",
        ],
        "config_identity": CONFIG_RELPATH,
        "code_identity": "src/ops/canonical_current_sha_no_order_package_n_e2e_v1/",
        "expected_repository_sha": repository_sha,
        "observation_mode": "observation",
        "no_order_invariant": True,
        "network_policy": "offline_only",
        "network_scope": "",
        "session_execution_scope": "",
        "credential_policy": "deny",
        "planned_duration_seconds": 1800,
        "earliest_start": earliest_start,
        "expires_at": expires_at,
        "evidence_root": evidence_root_rel,
        "evidence_target_paths": [
            "MANIFEST.sha256",
            "cap71/MANIFEST.sha256",
            "cap72/MANIFEST.sha256",
        ],
        "required_evidence_schema_versions": [
            "simulated_entry_reduce_exit_actionability_evidence.v1",
            "single_future_stateful_no_order_runtime_activation.v1",
        ],
        "killstate_policy": "ipso_killstate_v1",
        "timeout_policy": "hard_timeout_v1",
        "lock_policy": "single_session_lock_v1",
        "retry_policy": "no_retry_v1",
        "no_auto_promotion": True,
        "no_testnet": True,
        "no_live": True,
        "no_orders": True,
        "operator_identity": "canonical_current_sha_no_order_package_n_e2e_operator_v1",
        "approval_identity": "OWNER_GO_U_E2E_R2",
        "confirm_token_hash_reference": f"sha256:{fingerprint}",
        "confirm_token_binding_sha256": "0" * 64,
        "enabled": True,
        "armed": False,
        "arming_state": "enabled",
        "single_use": True,
        "consumed": False,
        "revoked": False,
        "revocation_state": "none",
        "fixture_non_authoritative": False,
        "notes": ["HASHES_ONLY_CONFIRM_TOKEN", "NO_PAPER_SHADOW_SESSION"],
    }
    require_current_run_i17_v1(payload)
    draft = parse_preregistration_contract_v1(payload)
    payload["confirm_token_binding_sha256"] = compute_confirm_token_binding_sha256(
        session_id=run_id,
        scope_digest=draft.scope_digest(),
        expires_at=expires_at,
        repository_sha=repository_sha,
        confirm_token=token,
    )
    del token
    require_current_run_i17_v1(payload)
    contract = parse_preregistration_contract_v1(payload)
    validation = validate_preregistration_contract_v1(
        contract,
        expected_repository_sha=repository_sha,
    )
    if not validation.ok:
        _reject(f"I17 preregistration validation failed: {validation.blockers}")
    return payload


def _artifact_pointers(run_root: Path, relative_files: tuple[str, ...]) -> list[ArtifactPointer]:
    pointers: list[ArtifactPointer] = []
    for rel in relative_files:
        path = run_root / rel
        if not path.is_file():
            _reject(f"empty I56 capsule rejected: missing {rel}")
        pointers.append(ArtifactPointer(path=rel, sha256=_sha256_file(path)))
    if not pointers:
        _reject("empty I56 capsule rejected")
    return pointers


def run_canonical_current_sha_no_order_package_n_e2e_v1(
    *,
    repo_root: Path,
    run_id: str,
    repository_sha: str,
) -> CanonicalCurrentShaNoOrderPackageNE2EResultV1:
    """Wire Cap 7.1/7.2 → Package-N → six EG-I82 owners in one isolated session."""
    if repository_sha != EXPECTED_ORIGIN_MAIN_SHA:
        _reject("repository SHA mismatch")
    if not re.fullmatch(RUN_ID_PATTERN, run_id):
        _reject("malformed run_id")
    repo = Path(repo_root).resolve()
    run_root = validate_isolated_run_root_v1(repo, evidence_root_for_run_v1(repo, run_id))
    run_root.mkdir(parents=True, exist_ok=False)
    evidence_root_rel = f"{OUT_OPS_PREFIX}/{EVIDENCE_DIRNAME}/{run_id}"

    cap72_dir = run_root / "cap72"
    cap71_dir = run_root / "cap71"
    owners_dir = run_root / "owners"
    cap72_dir.mkdir()
    cap71_dir.mkdir()
    owners_dir.mkdir()

    cap72_work = cap72_dir / "work"
    cap72_evidence = build_cap72_evidence_v1(repository_sha=repository_sha, work_root=cap72_work)
    cap72_payload = _persist_cap72(cap72_dir, cap72_evidence)
    if cap72_work.exists():
        shutil.rmtree(cap72_work)

    cap71_work = cap71_dir / "work"
    cap71_evidence = build_cap71_evidence_v1(repository_sha=repository_sha, work_root=cap71_work)
    cap71_payload = _persist_cap71(cap71_dir, cap71_evidence)
    if cap71_work.exists():
        shutil.rmtree(cap71_work)

    if not cap71_evidence.ok or not cap72_evidence.ok:
        _reject("Cap7.1/7.2 evidence not ok")
    require_matching_shas_v1(
        repository_sha,
        str(cap71_payload["repository_sha"]),
        str(cap72_payload["repository_sha"]),
    )
    _require_no_order_offline(cap71_payload, cap72_payload)

    combined = combined_evidence_digest_v1(
        str(cap71_payload["evidence_digest"]),
        str(cap72_payload["evidence_digest"]),
    )
    config_path = repo / CONFIG_RELPATH
    raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    if str(raw_config.get("base_params", {}).get("repository_sha")) != repository_sha:
        _reject("repository SHA mismatch")
    config = experiment_config_from_mapping(raw_config)
    package_dir = run_root / "package_n"
    produce_experiment_identity_manifest_v1(
        config,
        package_dir,
        source_experiment_id=combined,
    )
    manifest = json.loads((package_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    require_source_experiment_id_v1(manifest, combined)
    package_n = str(manifest["experiment_identity_id"])
    legacy_alias = str(manifest["legacy_aliases"]["legacy_experiment_id_md5_12"])
    content_sha256 = str(manifest["integrity"]["content_sha256"])

    i16_producer = produce_experiment_lineage_ref_v1(
        manifest_dir=package_dir,
        run_id=run_id,
        campaign_id=CAMPAIGN_ID,
        session_id=run_id,
    )

    i17_live = _build_i17_prereg(
        run_id=run_id,
        repository_sha=repository_sha,
        evidence_root_rel=evidence_root_rel,
    )
    _write_json(owners_dir / "i17_preregistration.json", i17_live)

    i52_manifest = LevelUpManifestV0(
        title="Current-SHA no-order Package-N wiring",
        slices=(
            SliceContractV0(
                slice_id="E2E-R2-WIRING",
                title="Cap 7.1/7.2 no-order evidence bound to Package-N",
                contract_summary="Offline no-order wiring proof; not a system E2E closeout.",
                evidence=EvidenceBundleRefV0(relative_dir=evidence_root_rel),
            ),
        ),
    )
    write_levelup_manifest(owners_dir / "i52_levelup_manifest.json", i52_manifest)
    i52_live = i52_manifest.model_dump(mode="python")

    pointers = _artifact_pointers(
        run_root,
        (
            f"cap71/{MANIFEST_FILENAME}",
            f"cap72/{MANIFEST_FILENAME}",
        ),
    )
    binding_rel = "owners/cap71_cap72_manifest_binding.json"
    binding_payload = {
        "cap71_manifest": f"cap71/{MANIFEST_FILENAME}",
        "cap71_manifest_sha256": pointers[0].sha256,
        "cap72_manifest": f"cap72/{MANIFEST_FILENAME}",
        "cap72_manifest_sha256": pointers[1].sha256,
        "combined_evidence_digest": combined,
    }
    _write_json(owners_dir / "cap71_cap72_manifest_binding.json", binding_payload)
    i56_artifact = ArtifactPointer(path=binding_rel, sha256=_sha256_file(run_root / binding_rel))
    feature_view = FeatureView(
        run_id=run_id,
        ts_ms=DETERMINISTIC_TS_MS,
        counts={"sealed_manifests": 2, "binding_artifacts": 1},
        facts={"instrument_id": PRODUCTION_INSTRUMENT_ID, "repository_sha": repository_sha},
        artifacts=[i56_artifact],
    )
    capsule = build_evidence_capsule(
        capsule_id=f"capsule-{run_id}",
        run_id=run_id,
        ts_ms=DETERMINISTIC_TS_MS,
        feature_view=feature_view,
        labels={"wiring_proof": 1},
    )
    i56_live = capsule.to_dict()
    require_i56_artifacts_nonempty_v1(i56_live)
    _write_json(owners_dir / "i56_capsule.json", i56_live)

    i61_fills = map_cap71_fills_to_i61_fills_v1(list(cap71_payload["metrics"].get("fills") or []))
    i61_live = compute_metrics(i61_fills)
    require_i61_metrics_nonempty_v1(i61_live)
    _write_json(owners_dir / "i61_metrics.json", i61_live)

    metrics71 = cap71_payload["metrics"]
    i65_live = {
        "experiment_id": run_id,
        "run_type": I65_RUN_TYPE,
        "run_name": str(raw_config["name"]),
        "strategy_name": str(raw_config["strategy_name"]),
        "symbol": PRODUCTION_INSTRUMENT_ID,
        "metrics": {
            "total_return": metrics71.get("REALIZED_PNL"),
            "num_trades": metrics71.get("SIMULATED_FILL_COUNT"),
            "entry_fills": metrics71.get("ENTRY_FILL_COUNT"),
            "exit_fills": metrics71.get("EXIT_FILL_COUNT"),
            "total_fees": metrics71.get("TOTAL_FEES"),
            "total_slippage": metrics71.get("TOTAL_SLIPPAGE"),
        },
        "params": {"repository_sha": repository_sha},
    }
    _write_json(owners_dir / "i65_summary.json", i65_live)

    owners = {
        "I16": {
            "manifest": manifest,
            "artifact_path": ARTIFACT_FILENAME,
            "run_id": run_id,
            "campaign_id": CAMPAIGN_ID,
            "session_id": run_id,
            "ref": i16_producer.ref,
        },
        "I17": {
            "live": i17_live,
            "experiment_identity_id": package_n,
            "run_id": run_id,
            "legacy_alias_md5_12": legacy_alias,
            "content_sha256": content_sha256,
        },
        "I52": {
            "live": i52_live,
            "experiment_identity_id": package_n,
            "run_id": run_id,
            "campaign_id": CAMPAIGN_ID,
            "session_id": run_id,
            "legacy_alias_md5_12": legacy_alias,
            "content_sha256": content_sha256,
            "evidence_ref": evidence_root_rel,
        },
        "I56": {
            "live": i56_live,
            "experiment_identity_id": package_n,
            "campaign_id": CAMPAIGN_ID,
            "session_id": run_id,
            "legacy_alias_md5_12": legacy_alias,
        },
        "I61": {
            "live": i61_live,
            "experiment_identity_id": package_n,
            "run_id": run_id,
            "campaign_id": CAMPAIGN_ID,
            "session_id": run_id,
            "legacy_alias_md5_12": legacy_alias,
            "content_sha256": content_sha256,
            "evidence_ref": evidence_root_rel,
        },
        "I65": {
            "live": i65_live,
            "experiment_identity_id": package_n,
            "campaign_id": CAMPAIGN_ID,
            "session_id": run_id,
            "legacy_alias_md5_12": legacy_alias,
            "content_sha256": content_sha256,
            "evidence_ref": evidence_root_rel,
        },
    }
    i17_join = parse_preregistration_contract_with_identity_join_v1(
        i17_live,
        experiment_identity_id=package_n,
        run_id=run_id,
        legacy_alias_md5_12=legacy_alias,
        content_sha256=content_sha256,
    ).join
    i52_join = parse_levelup_manifest_with_identity_join_v1(
        i52_live,
        experiment_identity_id=package_n,
        run_id=run_id,
        campaign_id=CAMPAIGN_ID,
        session_id=run_id,
        legacy_alias_md5_12=legacy_alias,
        content_sha256=content_sha256,
        evidence_ref=evidence_root_rel,
    ).join
    i56_join = parse_evidence_capsule_with_identity_join_v1(
        i56_live,
        experiment_identity_id=package_n,
        campaign_id=CAMPAIGN_ID,
        session_id=run_id,
        legacy_alias_md5_12=legacy_alias,
    ).join
    i61_join = parse_live_session_metrics_with_identity_join_v1(
        i61_live,
        experiment_identity_id=package_n,
        run_id=run_id,
        campaign_id=CAMPAIGN_ID,
        session_id=run_id,
        legacy_alias_md5_12=legacy_alias,
        content_sha256=content_sha256,
        evidence_ref=evidence_root_rel,
    ).join
    i65_join = parse_experiment_summary_with_identity_join_v1(
        i65_live,
        experiment_identity_id=package_n,
        campaign_id=CAMPAIGN_ID,
        session_id=run_id,
        legacy_alias_md5_12=legacy_alias,
        content_sha256=content_sha256,
        evidence_ref=evidence_root_rel,
    ).join
    owner_identities = {
        "I16": i16_producer.join.experiment_identity_id,
        "I17": i17_join.experiment_identity_id,
        "I52": i52_join.experiment_identity_id,
        "I56": i56_join.experiment_identity_id,
        "I61": i61_join.experiment_identity_id,
        "I65": i65_join.experiment_identity_id,
    }
    require_identical_package_n_v1(owner_identities, package_n)
    attestation = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    if attestation.package_n_sha256 != package_n:
        _reject("divergent Package-N across owners")
    verify_eg_i82_cross_lane_join_v1(
        {
            "I16": i16_producer.join,
            "I17": i17_join,
            "I52": i52_join,
            "I56": i56_join,
            "I61": i61_join,
            "I65": i65_join,
        }
    )

    _write_json(owners_dir / "eg_i82_attestation.json", attestation.to_canonical_mapping())
    _write_json(
        run_root / "RUN_METADATA.json",
        {
            "run_id": run_id,
            "repository_sha": repository_sha,
            "package_n_sha256": package_n,
            "source_experiment_id": combined,
            "COMPLETE_CURRENT_SYSTEM_E2E_PROVEN": False,
            "NETWORK_EFFECT": "NONE",
            "ORDER_EFFECT": "NONE",
        },
    )
    write_manifest_sha256(run_root)
    verify_ok, verify_msg = verify_manifest_sha256(run_root)
    if not verify_ok:
        _reject(f"manifest verification failed: {verify_msg}")

    return CanonicalCurrentShaNoOrderPackageNE2EResultV1(
        ok=True,
        contract_id=CONTRACT_ID,
        run_id=run_id,
        repository_sha=repository_sha,
        evidence_root=str(run_root),
        package_n_sha256=package_n,
        source_experiment_id=combined,
        combined_evidence_digest=combined,
        owner_identities=owner_identities,
        package_n_same_across_all_owners=True,
        manifest_verify_ok=True,
        complete_current_system_e2e_proven=False,
    )
