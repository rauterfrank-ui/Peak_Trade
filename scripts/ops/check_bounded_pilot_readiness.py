#!/usr/bin/env python3
"""
Canonical bounded-pilot readiness / preflight (read-only).

Bundles:
- `scripts/check_live_readiness.py` — stage `live` technical checks (config, risk, exchange, API env)
- `scripts.ops.pilot_go_no_go_eval_v1.py` — Ops Cockpit Go/No-Go rows
- Optional explicit PE-32 / PE-26 lifecycle static proof composition (offline, non-authorizing)

Does not invoke a session, does not set handoff env, does not authorize live trading.
Fail-closed: any failed live-readiness check, non-GO verdict, or invalid lifecycle proof
composition blocks.

Exit codes:
  0 — preflight GREEN (live readiness + GO_FOR_NEXT_PHASE_ONLY)
  1 — blocked (readiness, go/no-go, or lifecycle static proof composition)
  2 — script error (e.g. cockpit build failure)

Reference: docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONTRACT_ID = "bounded_pilot_readiness_v1"
STATIC_PROOF_COMPOSITION_MODE = "bounded_pilot_readiness_lifecycle_static_proof_composition_v0"
CANONICAL_BLOCKER_STATE = "blocked"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_EXTRA_FIELD_FRAGMENTS = (
    "secret",
    "credential",
    "api_key",
    "password",
    "token",
    "command",
    "action",
    "authority",
    "decision",
    "closure",
    "execution_authorized",
    "live_authorized",
    "pilot_start",
    "promotion",
    "network_allowed",
    "orders_allowed",
)


def resolve_bounded_pilot_config_path(repo_root: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    env_path = os.environ.get("PEAK_TRADE_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return repo_root / "config" / "config.toml"


@dataclass(frozen=True)
class LifecycleStaticProofCompositionBinding:
    source_revision: str
    pe32_canonical_owner: str
    pe32_proof_identity: str
    pe32_proof_digest: str
    pe32_lifecycle_chain_identity: str
    pe32_blocker_state: str
    pe26_canonical_owner: str
    pe26_assembly_identity: str
    pe26_assembly_digest: str
    pe26_source_revision: str
    pe26_traceability_identity: str


@dataclass(frozen=True)
class LifecycleStaticProofCompositionInput:
    pe32_integration_input: Any
    pe26_assembly_input: Any
    binding: LifecycleStaticProofCompositionBinding
    bound_traceability_identities: tuple[str, ...] = ()
    bound_admission_identities: tuple[str, ...] = ()
    extra_traceability_fields: tuple[str, ...] = ()
    injected_traceability_overrides: dict[str, Any] | None = None


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _reject_forbidden_extra_fields(extra_fields: dict[str, Any]) -> list[str]:
    fail_reasons: list[str] = []
    for field_name in extra_fields:
        lowered = field_name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_EXTRA_FIELD_FRAGMENTS):
            fail_reasons.append(f"forbidden extra field: {field_name}")
        else:
            fail_reasons.append(f"unknown extra field: {field_name}")
    return fail_reasons


def _validate_binding_shape(binding: LifecycleStaticProofCompositionBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.source_revision:
        fail_reasons.append("binding: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append("binding: source_revision must be full 40-char lowercase commit SHA")
    if not binding.pe32_canonical_owner:
        fail_reasons.append("binding: pe32_canonical_owner required")
    if not binding.pe32_proof_identity:
        fail_reasons.append("binding: pe32_proof_identity required")
    if not binding.pe32_proof_digest:
        fail_reasons.append("binding: pe32_proof_digest required")
    elif not _valid_sha256_digest(binding.pe32_proof_digest):
        fail_reasons.append("binding: pe32_proof_digest must be 64-char lowercase sha256 hex")
    if not binding.pe32_lifecycle_chain_identity:
        fail_reasons.append("binding: pe32_lifecycle_chain_identity required")
    elif not _valid_sha256_digest(binding.pe32_lifecycle_chain_identity):
        fail_reasons.append(
            "binding: pe32_lifecycle_chain_identity must be 64-char lowercase sha256 hex"
        )
    if not binding.pe32_blocker_state:
        fail_reasons.append("binding: pe32_blocker_state required")
    elif binding.pe32_blocker_state != CANONICAL_BLOCKER_STATE:
        fail_reasons.append(f"binding: pe32_blocker_state must be {CANONICAL_BLOCKER_STATE!r}")
    if not binding.pe26_canonical_owner:
        fail_reasons.append("binding: pe26_canonical_owner required")
    if not binding.pe26_assembly_identity:
        fail_reasons.append("binding: pe26_assembly_identity required")
    if not binding.pe26_assembly_digest:
        fail_reasons.append("binding: pe26_assembly_digest required")
    elif not _valid_sha256_digest(binding.pe26_assembly_digest):
        fail_reasons.append("binding: pe26_assembly_digest must be 64-char lowercase sha256 hex")
    if not binding.pe26_source_revision:
        fail_reasons.append("binding: pe26_source_revision required")
    elif not _valid_commit_sha(binding.pe26_source_revision):
        fail_reasons.append(
            "binding: pe26_source_revision must be full 40-char lowercase commit SHA"
        )
    if not binding.pe26_traceability_identity:
        fail_reasons.append("binding: pe26_traceability_identity required")
    elif not _valid_sha256_digest(binding.pe26_traceability_identity):
        fail_reasons.append(
            "binding: pe26_traceability_identity must be 64-char lowercase sha256 hex"
        )
    return fail_reasons


def _validate_pe32_blocker_semantics(pe32_input: Any) -> list[str]:
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS,
    )

    fail_reasons: list[str] = []
    snapshot = pe32_input.blocker_register_snapshot
    if snapshot.global_blocker_lift_authorized:
        fail_reasons.append("blocker_state: global_blocker_lift_authorized must be false")
    if snapshot.preflight_lift_authorized:
        fail_reasons.append("blocker_state: preflight_lift_authorized must be false")
    if not snapshot.snapshot_complete:
        fail_reasons.append("blocker_state: blocker register snapshot must be complete")
    present_ids = {entry.blocker_id for entry in snapshot.entries}
    for blocker_id in REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS:
        if blocker_id not in present_ids:
            fail_reasons.append(f"blocker_state: required blocker {blocker_id} missing")
    for entry in snapshot.entries:
        if entry.blocker_state != "BLOCKED":
            fail_reasons.append(
                f"blocker_state: {entry.blocker_id} must be BLOCKED, got {entry.blocker_state!r}"
            )
        if entry.lift_authorized:
            fail_reasons.append(f"blocker_state: {entry.blocker_id} lift_authorized must be false")
    return fail_reasons


def _validate_pe32_pe26_composition_coherence(
    *,
    pe32_input: Any,
    pe26_input: Any,
    binding: LifecycleStaticProofCompositionBinding,
    pe32_result: dict[str, Any],
    pe26_result: dict[str, Any],
    pe32_owner: str,
    pe26_owner: str,
) -> list[str]:
    fail_reasons: list[str] = []

    if binding.source_revision != pe32_input.source_revision:
        fail_reasons.append("binding: source_revision mismatch with PE-32 input")
    if binding.source_revision != pe26_input.source_revision:
        fail_reasons.append("binding: source_revision mismatch with PE-26 input")
    if pe32_input.source_revision != pe26_input.source_revision:
        fail_reasons.append("composition: PE-32 and PE-26 source_revision mismatch")

    if binding.pe26_source_revision != pe26_input.source_revision:
        fail_reasons.append("binding: pe26_source_revision mismatch with PE-26 input")
    if binding.pe26_source_revision != binding.source_revision:
        fail_reasons.append("binding: pe26_source_revision mismatch with shared source_revision")

    if binding.pe32_canonical_owner != pe32_owner:
        fail_reasons.append("binding: pe32_canonical_owner mismatch")
    if pe32_input.contract_versions.pe26_assembly != pe26_owner:
        fail_reasons.append("composition: PE-32 pe26_assembly owner mismatch with PE-26 owner")
    if binding.pe26_canonical_owner != pe26_owner:
        fail_reasons.append("binding: pe26_canonical_owner mismatch")
    if pe26_input.contract_versions.integration != pe26_owner:
        fail_reasons.append("composition: PE-26 integration owner mismatch")

    if binding.pe32_proof_identity != pe32_input.integration_id:
        fail_reasons.append("binding: pe32_proof_identity mismatch with PE-32 integration_id")

    computed_pe32_digest = pe32_result.get("integration_proof_digest")
    if computed_pe32_digest is None:
        fail_reasons.append("composition: PE-32 integration_proof_digest unavailable")
    elif binding.pe32_proof_digest != computed_pe32_digest:
        fail_reasons.append("binding: pe32_proof_digest mismatch with PE-32 evaluation")

    lifecycle_chain_identity = pe32_input.lifecycle_matrix_proof.lifecycle_state_digest
    if binding.pe32_lifecycle_chain_identity != lifecycle_chain_identity:
        fail_reasons.append(
            "binding: pe32_lifecycle_chain_identity mismatch with PE-32 lifecycle_state_digest"
        )

    if binding.pe26_assembly_identity != pe26_input.assembly_id:
        fail_reasons.append("binding: pe26_assembly_identity mismatch with PE-26 assembly_id")

    computed_pe26_digest = pe26_result.get("assembly_result_digest")
    if computed_pe26_digest is None:
        fail_reasons.append("composition: PE-26 assembly_result_digest unavailable")
    elif binding.pe26_assembly_digest != computed_pe26_digest:
        fail_reasons.append("binding: pe26_assembly_digest mismatch with PE-26 evaluation")

    traceability_identity = pe26_input.pe37_traceability_proof.traceability_identity
    if binding.pe26_traceability_identity != traceability_identity:
        fail_reasons.append(
            "binding: pe26_traceability_identity mismatch with PE-26 traceability proof"
        )
    if pe26_result.get("traceability_identity") != traceability_identity:
        fail_reasons.append("composition: PE-26 traceability_identity evaluation mismatch")

    if pe32_input.adapter_id != pe26_input.adapter_id:
        fail_reasons.append("composition: adapter_id mismatch between PE-32 and PE-26")
    if pe32_input.instrument != pe26_input.instrument:
        fail_reasons.append("composition: instrument mismatch between PE-32 and PE-26")
    if pe32_input.market_type != pe26_input.market_type:
        fail_reasons.append("composition: market_type mismatch between PE-32 and PE-26")
    if (
        pe32_input.lifecycle_matrix_proof.lifecycle_matrix_digest
        != pe26_input.lifecycle_matrix_proof.lifecycle_matrix_digest
    ):
        fail_reasons.append("composition: lifecycle_matrix_digest mismatch between PE-32 and PE-26")

    pe32_pe25_digest = pe32_result.get("pe25_closure_result_digest")
    pe26_pe25_digest = pe26_input.pe25_operator_closure_proof.closure_result_digest
    if pe32_pe25_digest != pe26_pe25_digest:
        fail_reasons.append("composition: PE-32→PE-26 PE-25 closure_result_digest mismatch")

    if (
        pe32_result.get("assigned_lifecycle_phase")
        != pe32_input.lifecycle_matrix_proof.assigned_lifecycle_phase
    ):
        fail_reasons.append("composition: PE-32 lifecycle phase binding mismatch")

    return fail_reasons


def evaluate_lifecycle_static_proof_composition(
    composition_input: LifecycleStaticProofCompositionInput,
    *,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-32 / PE-26 lifecycle static proof composition (offline, fail-closed)."""
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        CONTRACT_VERSION as PE26_CONTRACT_VERSION,
        evaluate_preflight_execution_readiness_assembly_lifecycle_integration,
    )
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        CONTRACT_VERSION as PE32_CONTRACT_VERSION,
        evaluate_readiness_decision_lifecycle_integration,
    )

    fail_reasons: list[str] = []
    if composition_input.pe32_integration_input is None:
        fail_reasons.append("pe32_integration_input required")
    if composition_input.pe26_assembly_input is None:
        fail_reasons.append("pe26_assembly_input required")
    if extra_fields:
        fail_reasons.extend(_reject_forbidden_extra_fields(extra_fields))

    binding = composition_input.binding
    fail_reasons.extend(_validate_binding_shape(binding))

    if (
        composition_input.pe32_integration_input is None
        or composition_input.pe26_assembly_input is None
    ):
        return {
            "composition_mode": STATIC_PROOF_COMPOSITION_MODE,
            "composition_pass": False,
            "static_readiness_proof_coherent": False,
            "pe32_integration_pass": False,
            "pe26_integration_pass": False,
            "preflight_remains_blocked": True,
            "authority_lift": False,
            "pilot_readiness_operationally_granted": False,
            "fail_reasons": _sorted_unique(fail_reasons),
        }

    pe32_input = composition_input.pe32_integration_input
    pe26_input = composition_input.pe26_assembly_input

    pe32_result = evaluate_readiness_decision_lifecycle_integration(pe32_input)
    pe26_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        pe26_input,
        bound_traceability_identities=composition_input.bound_traceability_identities,
        bound_admission_identities=composition_input.bound_admission_identities,
        extra_traceability_fields=composition_input.extra_traceability_fields,
        injected_traceability_overrides=composition_input.injected_traceability_overrides,
    )

    if not pe32_result.get("integration_pass"):
        fail_reasons.extend(f"pe32: {reason}" for reason in pe32_result.get("fail_reasons", []))
    if not pe26_result.get("integration_pass"):
        fail_reasons.extend(f"pe26: {reason}" for reason in pe26_result.get("fail_reasons", []))

    fail_reasons.extend(_validate_pe32_blocker_semantics(pe32_input))
    fail_reasons.extend(
        _validate_pe32_pe26_composition_coherence(
            pe32_input=pe32_input,
            pe26_input=pe26_input,
            binding=binding,
            pe32_result=pe32_result,
            pe26_result=pe26_result,
            pe32_owner=PE32_CONTRACT_VERSION,
            pe26_owner=PE26_CONTRACT_VERSION,
        )
    )

    fail_reasons = _sorted_unique(fail_reasons)
    composition_pass = not fail_reasons

    return {
        "composition_mode": STATIC_PROOF_COMPOSITION_MODE,
        "composition_pass": composition_pass,
        "static_readiness_proof_coherent": composition_pass,
        "pe32_integration_pass": pe32_result.get("integration_pass") is True,
        "pe26_integration_pass": pe26_result.get("integration_pass") is True,
        "pe32_canonical_owner": PE32_CONTRACT_VERSION,
        "pe26_canonical_owner": PE26_CONTRACT_VERSION,
        "pe32_proof_identity": binding.pe32_proof_identity,
        "pe32_proof_digest": binding.pe32_proof_digest if composition_pass else None,
        "pe32_lifecycle_chain_identity": binding.pe32_lifecycle_chain_identity,
        "pe26_assembly_identity": binding.pe26_assembly_identity,
        "pe26_assembly_digest": binding.pe26_assembly_digest if composition_pass else None,
        "pe26_traceability_identity": binding.pe26_traceability_identity,
        "source_revision": binding.source_revision,
        "preflight_remains_blocked": True,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
        "operator_decision_authorized": False,
        "operator_closure_authorized": False,
        "execution_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "live_authorized": False,
        "authority_lift": False,
        "pilot_readiness_operationally_granted": False,
        "network_used": False,
        "credentials_used": False,
        "exchange_api_called": False,
        "fail_reasons": fail_reasons,
    }


def _readiness_summary(report: Any) -> dict[str, Any]:
    from scripts.check_live_readiness import ReadinessReport

    assert isinstance(report, ReadinessReport)
    return {
        "stage": report.stage,
        "all_passed": report.all_passed,
        "passed_count": report.passed_count,
        "failed_count": report.failed_count,
        "failed_checks": [
            {"name": c.name, "message": c.message, "details": c.details}
            for c in report.checks
            if not c.passed
        ],
        "warning_count": report.warning_count,
    }


def run_bounded_pilot_readiness(
    repo_root: Path,
    config_path: Path,
    *,
    run_tests: bool = False,
    lifecycle_static_proof: LifecycleStaticProofCompositionInput | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Run live-stage readiness checks, then pilot go/no-go eval.

    When ``lifecycle_static_proof`` is provided, additionally requires a coherent
    PE-32 / PE-26 static proof composition. This remains non-authorizing.

    Returns:
        (ok, bundle) where bundle is JSON-serializable and includes `contract`.
    """
    from scripts.check_live_readiness import run_readiness_checks
    from scripts.ops.pilot_go_no_go_eval_v1 import evaluate
    from src.webui.ops_cockpit import build_ops_cockpit_payload

    bundle: dict[str, Any] = {"contract": CONTRACT_ID}

    try:
        readiness_report = run_readiness_checks(
            stage="live",
            config_path=config_path,
            run_tests=run_tests,
        )
    except Exception as e:
        bundle["ok"] = False
        bundle["blocked_at"] = "live_readiness"
        bundle["message"] = f"live readiness evaluation error: {e}"
        return False, bundle

    bundle["live_readiness"] = _readiness_summary(readiness_report)
    if not readiness_report.all_passed:
        bundle["ok"] = False
        bundle["blocked_at"] = "live_readiness"
        bundle["message"] = f"live readiness failed ({readiness_report.failed_count} check(s))"
        return False, bundle

    try:
        payload = build_ops_cockpit_payload(repo_root=repo_root)
    except Exception as e:
        bundle["ok"] = False
        bundle["blocked_at"] = "cockpit_payload"
        bundle["message"] = f"failed to build ops cockpit payload: {e}"
        return False, bundle

    go_no_go = evaluate(payload)
    bundle["go_no_go"] = go_no_go
    verdict = go_no_go.get("verdict")
    if verdict != "GO_FOR_NEXT_PHASE_ONLY":
        bundle["ok"] = False
        bundle["blocked_at"] = "go_no_go"
        bundle["message"] = f"go/no-go not GREEN: verdict={verdict}"
        return False, bundle

    if lifecycle_static_proof is not None:
        composition = evaluate_lifecycle_static_proof_composition(lifecycle_static_proof)
        bundle["lifecycle_static_proof"] = composition
        bundle["static_readiness_proof_coherent"] = composition["composition_pass"]
        if not composition["composition_pass"]:
            bundle["ok"] = False
            bundle["blocked_at"] = "lifecycle_static_proof"
            bundle["message"] = (
                "bounded_pilot preflight blocked: lifecycle static proof composition failed"
            )
            return False, bundle
    else:
        bundle["static_readiness_proof_coherent"] = None

    bundle["ok"] = True
    bundle["blocked_at"] = None
    bundle["message"] = "bounded_pilot preflight GREEN: live readiness + GO_FOR_NEXT_PHASE_ONLY"
    return True, bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Canonical bounded-pilot preflight: live readiness + pilot go/no-go "
            "(read-only, no session invoke)"
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full result as JSON on stdout",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (default: inferred from script location)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Config path (default: PEAK_TRADE_CONFIG_PATH or config/config.toml)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Pass through to live readiness: run baseline pytest (slow)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.exists() else Path.cwd())
    config_path = resolve_bounded_pilot_config_path(repo_root, args.config)

    try:
        ok, bundle = run_bounded_pilot_readiness(
            repo_root,
            config_path,
            run_tests=args.run_tests,
        )
    except Exception as e:
        err = {"contract": CONTRACT_ID, "ok": False, "error": str(e)}
        if args.json:
            print(json.dumps(err, indent=2))
        else:
            print(f"ERR: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(bundle.get("message", ""))
        if not ok:
            blocked = bundle.get("blocked_at")
            if blocked == "live_readiness":
                lr = bundle.get("live_readiness") or {}
                for fc in lr.get("failed_checks") or []:
                    print(f"  [readiness] {fc.get('name')}: {fc.get('message')}", file=sys.stderr)
            elif blocked == "go_no_go":
                gng = bundle.get("go_no_go") or {}
                for r in gng.get("rows") or []:
                    if r.get("status") != "PASS":
                        print(
                            f"  [go/no-go] Row {r.get('row')} {r.get('area')}: {r.get('status')}",
                            file=sys.stderr,
                        )
            elif blocked == "lifecycle_static_proof":
                composition = bundle.get("lifecycle_static_proof") or {}
                for reason in composition.get("fail_reasons") or []:
                    print(f"  [lifecycle-proof] {reason}", file=sys.stderr)
            print("Preflight not GREEN. Do not invoke bounded pilot.", file=sys.stderr)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
