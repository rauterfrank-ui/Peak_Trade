#!/usr/bin/env python3
"""
Bounded-pilot operator preflight packet (read-only orchestration).

Orchestrates existing entrypoints only:
- ``scripts/ops/check_bounded_pilot_readiness.run_bounded_pilot_readiness``
- ``scripts/ops/snapshot_operator_stop_signals.build_stop_signal_snapshot``

Emits one fixed JSON object for operators. No new gate semantics, no state writes,
no live authorization.

Exit codes:
  0 — readiness GREEN and stop-signal snapshot has no hard read/parse errors
  1 — blocked (readiness not GREEN and/or stop-signal artifact/KS file in error)
  2 — orchestration / unexpected failure building the packet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONTRACT_ID = "bounded_pilot_operator_preflight_packet_v1"
LIFECYCLE_STATIC_PROOF_HANDOFF_MODE = (
    "bounded_pilot_operator_preflight_packet_lifecycle_static_proof_handoff_v0"
)
READINESS_CANONICAL_OWNER = "bounded_pilot_readiness_v1"
PROOF_STATUS_VALID = "valid"
PROOF_STATUS_REJECTED = "rejected"
_HASH_ALGORITHM = "sha256"


@dataclass(frozen=True)
class OperatorPreflightPacketLifecycleStaticProofHandoffBinding:
    source_revision: str
    canonical_owner: str
    lifecycle_static_proof_identity: str
    lifecycle_static_proof_digest: str
    pe32_proof_identity: str
    pe32_proof_digest: str
    pe26_assembly_identity: str
    pe26_assembly_digest: str
    pe26_traceability_identity: str
    blocker_state: str
    proof_status: str


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256_hex(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_lifecycle_static_proof_identity(
    *,
    source_revision: str,
    canonical_owner: str,
    pe32_proof_identity: str,
    pe26_assembly_identity: str,
    pe26_traceability_identity: str,
    composition_mode: str,
) -> str:
    """Deterministic lifecycle static proof identity from injected binding semantics."""
    return _sha256_hex(
        {
            "hash_algorithm": _HASH_ALGORITHM,
            "composition_mode": composition_mode,
            "canonical_owner": canonical_owner,
            "source_revision": source_revision,
            "pe32_proof_identity": pe32_proof_identity,
            "pe26_assembly_identity": pe26_assembly_identity,
            "pe26_traceability_identity": pe26_traceability_identity,
        }
    )


def compute_lifecycle_static_proof_digest(
    *,
    binding: OperatorPreflightPacketLifecycleStaticProofHandoffBinding,
    composition: dict[str, Any],
) -> str:
    """Deterministic digest over canonical lifecycle static proof handoff bindings."""
    payload = {
        "hash_algorithm": _HASH_ALGORITHM,
        "handoff_mode": LIFECYCLE_STATIC_PROOF_HANDOFF_MODE,
        "source_revision": binding.source_revision,
        "canonical_owner": binding.canonical_owner,
        "lifecycle_static_proof_identity": binding.lifecycle_static_proof_identity,
        "pe32_proof_identity": binding.pe32_proof_identity,
        "pe32_proof_digest": binding.pe32_proof_digest,
        "pe26_assembly_identity": binding.pe26_assembly_identity,
        "pe26_assembly_digest": binding.pe26_assembly_digest,
        "pe26_traceability_identity": binding.pe26_traceability_identity,
        "blocker_state": binding.blocker_state,
        "proof_status": binding.proof_status,
        "composition_mode": composition.get("composition_mode"),
        "composition_pass": composition.get("composition_pass"),
        "fail_reasons": composition.get("fail_reasons") or [],
    }
    return _sha256_hex(payload)


def build_lifecycle_static_proof_handoff_binding(
    composition_input: Any,
    composition: dict[str, Any],
) -> OperatorPreflightPacketLifecycleStaticProofHandoffBinding:
    """Build handoff binding from evaluated composition (reuse readiness owner semantics)."""
    from scripts.ops.check_bounded_pilot_readiness import (
        CANONICAL_BLOCKER_STATE,
        STATIC_PROOF_COMPOSITION_MODE,
    )

    binding = composition_input.binding
    composition_pass = composition.get("composition_pass") is True
    proof_status = PROOF_STATUS_VALID if composition_pass else PROOF_STATUS_REJECTED
    lifecycle_identity = compute_lifecycle_static_proof_identity(
        source_revision=binding.source_revision,
        canonical_owner=READINESS_CANONICAL_OWNER,
        pe32_proof_identity=binding.pe32_proof_identity,
        pe26_assembly_identity=binding.pe26_assembly_identity,
        pe26_traceability_identity=binding.pe26_traceability_identity,
        composition_mode=STATIC_PROOF_COMPOSITION_MODE,
    )
    handoff_binding = OperatorPreflightPacketLifecycleStaticProofHandoffBinding(
        source_revision=binding.source_revision,
        canonical_owner=READINESS_CANONICAL_OWNER,
        lifecycle_static_proof_identity=lifecycle_identity,
        lifecycle_static_proof_digest="",
        pe32_proof_identity=binding.pe32_proof_identity,
        pe32_proof_digest=binding.pe32_proof_digest,
        pe26_assembly_identity=binding.pe26_assembly_identity,
        pe26_assembly_digest=binding.pe26_assembly_digest,
        pe26_traceability_identity=binding.pe26_traceability_identity,
        blocker_state=CANONICAL_BLOCKER_STATE,
        proof_status=proof_status,
    )
    digest = compute_lifecycle_static_proof_digest(
        binding=handoff_binding,
        composition=composition,
    )
    return OperatorPreflightPacketLifecycleStaticProofHandoffBinding(
        source_revision=handoff_binding.source_revision,
        canonical_owner=handoff_binding.canonical_owner,
        lifecycle_static_proof_identity=handoff_binding.lifecycle_static_proof_identity,
        lifecycle_static_proof_digest=digest,
        pe32_proof_identity=handoff_binding.pe32_proof_identity,
        pe32_proof_digest=handoff_binding.pe32_proof_digest,
        pe26_assembly_identity=handoff_binding.pe26_assembly_identity,
        pe26_assembly_digest=handoff_binding.pe26_assembly_digest,
        pe26_traceability_identity=handoff_binding.pe26_traceability_identity,
        blocker_state=handoff_binding.blocker_state,
        proof_status=handoff_binding.proof_status,
    )


def validate_injected_lifecycle_static_proof_handoff_binding(
    injected_binding: OperatorPreflightPacketLifecycleStaticProofHandoffBinding,
    *,
    composition_input: Any,
    composition: dict[str, Any],
) -> list[str]:
    """Fail-closed drift guard for explicitly injected handoff binding."""
    from scripts.ops.check_bounded_pilot_readiness import CANONICAL_BLOCKER_STATE

    fail_reasons: list[str] = []
    expected = build_lifecycle_static_proof_handoff_binding(composition_input, composition)
    if injected_binding.source_revision != expected.source_revision:
        fail_reasons.append("handoff_binding: source_revision mismatch")
    if injected_binding.canonical_owner != expected.canonical_owner:
        fail_reasons.append("handoff_binding: canonical_owner mismatch")
    if injected_binding.lifecycle_static_proof_identity != expected.lifecycle_static_proof_identity:
        fail_reasons.append("handoff_binding: lifecycle_static_proof_identity mismatch")
    if injected_binding.lifecycle_static_proof_digest != expected.lifecycle_static_proof_digest:
        fail_reasons.append("handoff_binding: lifecycle_static_proof_digest mismatch")
    if injected_binding.pe32_proof_identity != expected.pe32_proof_identity:
        fail_reasons.append("handoff_binding: pe32_proof_identity mismatch")
    if injected_binding.pe32_proof_digest != expected.pe32_proof_digest:
        fail_reasons.append("handoff_binding: pe32_proof_digest mismatch")
    if injected_binding.pe26_assembly_identity != expected.pe26_assembly_identity:
        fail_reasons.append("handoff_binding: pe26_assembly_identity mismatch")
    if injected_binding.pe26_assembly_digest != expected.pe26_assembly_digest:
        fail_reasons.append("handoff_binding: pe26_assembly_digest mismatch")
    if injected_binding.pe26_traceability_identity != expected.pe26_traceability_identity:
        fail_reasons.append("handoff_binding: pe26_traceability_identity mismatch")
    if injected_binding.blocker_state != CANONICAL_BLOCKER_STATE:
        fail_reasons.append("handoff_binding: blocker_state must be canonically blocked")
    elif injected_binding.blocker_state != expected.blocker_state:
        fail_reasons.append("handoff_binding: blocker_state mismatch")
    if injected_binding.proof_status != expected.proof_status:
        fail_reasons.append("handoff_binding: proof_status mismatch")
    return fail_reasons


def _handoff_binding_to_dict(
    binding: OperatorPreflightPacketLifecycleStaticProofHandoffBinding,
) -> dict[str, Any]:
    return {
        "handoff_mode": LIFECYCLE_STATIC_PROOF_HANDOFF_MODE,
        "source_revision": binding.source_revision,
        "canonical_owner": binding.canonical_owner,
        "lifecycle_static_proof_identity": binding.lifecycle_static_proof_identity,
        "lifecycle_static_proof_digest": binding.lifecycle_static_proof_digest,
        "pe32_proof_identity": binding.pe32_proof_identity,
        "pe32_proof_digest": binding.pe32_proof_digest,
        "pe26_assembly_identity": binding.pe26_assembly_identity,
        "pe26_assembly_digest": binding.pe26_assembly_digest,
        "pe26_traceability_identity": binding.pe26_traceability_identity,
        "blocker_state": binding.blocker_state,
        "proof_status": binding.proof_status,
        "preflight_remains_blocked": True,
        "authority_lift": False,
        "pilot_readiness_operationally_granted": False,
    }


def compute_packet_identity(
    *,
    contract: str,
    readiness_ok: bool,
    stop_snapshot_ok: bool,
    lifecycle_handoff: dict[str, Any] | None,
) -> str:
    """Deterministic packet identity including optional lifecycle static proof handoff."""
    payload: dict[str, Any] = {
        "hash_algorithm": _HASH_ALGORITHM,
        "contract": contract,
        "readiness_ok": readiness_ok,
        "stop_snapshot_ok": stop_snapshot_ok,
    }
    if lifecycle_handoff is not None:
        payload["lifecycle_static_proof_handoff"] = {
            "lifecycle_static_proof_identity": lifecycle_handoff.get(
                "lifecycle_static_proof_identity"
            ),
            "lifecycle_static_proof_digest": lifecycle_handoff.get("lifecycle_static_proof_digest"),
            "source_revision": lifecycle_handoff.get("source_revision"),
            "canonical_owner": lifecycle_handoff.get("canonical_owner"),
            "proof_status": lifecycle_handoff.get("proof_status"),
        }
    return _sha256_hex(payload)


def compute_packet_digest(
    *,
    contract: str,
    readiness_bundle: dict[str, Any],
    stop_snapshot: dict[str, Any] | None,
    summary: dict[str, Any],
    lifecycle_handoff: dict[str, Any] | None,
    packet_identity: str,
) -> str:
    """Deterministic packet digest over canonical packet bindings (excludes volatile metadata)."""
    payload: dict[str, Any] = {
        "hash_algorithm": _HASH_ALGORITHM,
        "contract": contract,
        "packet_identity": packet_identity,
        "bounded_pilot_readiness": {
            "contract": readiness_bundle.get("contract"),
            "ok": readiness_bundle.get("ok"),
            "blocked_at": readiness_bundle.get("blocked_at"),
            "static_readiness_proof_coherent": readiness_bundle.get(
                "static_readiness_proof_coherent"
            ),
        },
        "stop_signal_snapshot_contract": (stop_snapshot or {}).get("contract"),
        "summary": {
            "readiness_ok": summary.get("readiness_ok"),
            "stop_snapshot_ok": summary.get("stop_snapshot_ok"),
            "packet_ok": summary.get("packet_ok"),
            "blocked": summary.get("blocked") or [],
        },
    }
    if lifecycle_handoff is not None:
        payload["lifecycle_static_proof_handoff"] = lifecycle_handoff
    return _sha256_hex(payload)


def _build_lifecycle_static_proof_handoff_section(
    composition_input: Any,
    composition: dict[str, Any] | None,
    *,
    injected_binding: OperatorPreflightPacketLifecycleStaticProofHandoffBinding | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    if composition_input is None or composition is None:
        return None, []
    handoff_binding = build_lifecycle_static_proof_handoff_binding(composition_input, composition)
    fail_reasons: list[str] = []
    if injected_binding is not None:
        fail_reasons.extend(
            validate_injected_lifecycle_static_proof_handoff_binding(
                injected_binding,
                composition_input=composition_input,
                composition=composition,
            )
        )
    handoff = _handoff_binding_to_dict(handoff_binding)
    handoff["composition"] = composition
    if fail_reasons:
        handoff["handoff_pass"] = False
        handoff["fail_reasons"] = sorted(dict.fromkeys(fail_reasons))
    else:
        handoff["handoff_pass"] = composition.get("composition_pass") is True
        handoff["fail_reasons"] = []
    return handoff, fail_reasons


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _try_git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode != 0:
            return None
        line = (out.stdout or "").strip()
        return line or None
    except (OSError, subprocess.SubprocessError):
        return None


def _stop_snapshot_hard_ok(snapshot: dict[str, Any]) -> tuple[bool, list[str]]:
    """True when no read/parse ``error`` status on wired stop-signal sources."""
    blocked: list[str] = []
    art = snapshot.get("incident_stop_artifact") or {}
    if art.get("status") == "error":
        blocked.append(
            "stop_signal_snapshot.incident_stop_artifact: error "
            f"({art.get('error') or 'read/parse failure'})"
        )
    ks = snapshot.get("kill_switch_file") or {}
    if ks.get("status") == "error":
        blocked.append(
            "stop_signal_snapshot.kill_switch_file: error "
            f"({ks.get('error') or 'read/parse failure'})"
        )
    return (len(blocked) == 0, blocked)


def build_operator_preflight_packet(
    repo_root: Path,
    config_path: Path,
    *,
    run_tests: bool = False,
    lifecycle_static_proof: Any | None = None,
    lifecycle_static_proof_handoff_binding: (
        OperatorPreflightPacketLifecycleStaticProofHandoffBinding | None
    ) = None,
    lifecycle_handoff_extra_fields: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    """
    Build the packet dict and intended exit code (0/1/2).

    Always runs readiness and stop snapshot when possible so partial failures stay visible.

    When ``lifecycle_static_proof`` is provided, passes it to the canonical readiness owner
    and binds lifecycle static proof handoff fields fail-closed into the packet identity.
    """
    from scripts.ops.check_bounded_pilot_readiness import (
        evaluate_lifecycle_static_proof_composition,
        run_bounded_pilot_readiness,
    )
    from scripts.ops.snapshot_operator_stop_signals import build_stop_signal_snapshot

    meta: dict[str, Any] = {
        "generated_at_utc": _utc_now_iso(),
        "repo_root": str(repo_root.resolve()),
        "git_head": _try_git_head(repo_root),
    }

    lifecycle_handoff_blocked: list[str] = []
    if lifecycle_static_proof is not None and lifecycle_handoff_extra_fields:
        preflight_composition = evaluate_lifecycle_static_proof_composition(
            lifecycle_static_proof,
            extra_fields=lifecycle_handoff_extra_fields,
        )
        if not preflight_composition.get("composition_pass"):
            lifecycle_handoff_blocked.extend(
                f"lifecycle_static_proof_handoff: {reason}"
                for reason in preflight_composition.get("fail_reasons") or []
            )

    readiness_bundle: dict[str, Any]
    readiness_ok: bool
    try:
        readiness_ok, readiness_bundle = run_bounded_pilot_readiness(
            repo_root,
            config_path,
            run_tests=run_tests,
            lifecycle_static_proof=lifecycle_static_proof,
        )
    except Exception as e:
        packet = {
            "contract": CONTRACT_ID,
            "metadata": meta,
            "bounded_pilot_readiness": {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "orchestrator_error": str(e),
            },
            "stop_signal_snapshot": None,
            "summary": {
                "readiness_ok": False,
                "stop_snapshot_ok": False,
                "packet_ok": False,
                "blocked": [f"bounded_pilot_readiness: exception ({e})"],
                "notes": [],
            },
        }
        return packet, 2

    stop_snapshot: dict[str, Any] | None = None
    stop_ok = False
    stop_blocked: list[str] = []
    notes: list[str] = []
    stop_build_exc: str | None = None
    try:
        stop_snapshot = build_stop_signal_snapshot(repo_root)
        stop_ok, stop_blocked = _stop_snapshot_hard_ok(stop_snapshot)
        snap_notes = stop_snapshot.get("consistency_notes") or []
        if isinstance(snap_notes, list):
            notes.extend(str(x) for x in snap_notes)
    except Exception as e:
        stop_build_exc = str(e)
        stop_snapshot = {
            "contract": "operator_stop_signal_snapshot_v1",
            "orchestrator_error": stop_build_exc,
        }
        stop_ok = False
        stop_blocked = [f"stop_signal_snapshot: exception ({stop_build_exc})"]

    blocked: list[str] = []
    if lifecycle_handoff_blocked:
        blocked.extend(lifecycle_handoff_blocked)
    if not readiness_ok:
        rb = readiness_bundle.get("blocked_at")
        msg = readiness_bundle.get("message") or "readiness not GREEN"
        blocked.append(f"bounded_pilot_readiness: {msg}" + (f" (at={rb})" if rb else ""))
    blocked.extend(stop_blocked)

    composition = readiness_bundle.get("lifecycle_static_proof")
    lifecycle_handoff, handoff_fail_reasons = _build_lifecycle_static_proof_handoff_section(
        lifecycle_static_proof,
        composition if isinstance(composition, dict) else None,
        injected_binding=lifecycle_static_proof_handoff_binding,
    )
    if handoff_fail_reasons:
        blocked.extend(f"lifecycle_static_proof_handoff: {r}" for r in handoff_fail_reasons)
    if lifecycle_handoff is not None and not lifecycle_handoff.get("handoff_pass"):
        for reason in lifecycle_handoff.get("fail_reasons") or []:
            if not reason.startswith("lifecycle_static_proof_handoff:"):
                blocked.append(f"lifecycle_static_proof_handoff: {reason}")

    packet_ok = bool(
        readiness_ok
        and stop_ok
        and stop_build_exc is None
        and not lifecycle_handoff_blocked
        and not handoff_fail_reasons
        and (lifecycle_handoff is None or lifecycle_handoff.get("handoff_pass") is True)
    )

    summary = {
        "readiness_ok": readiness_ok,
        "stop_snapshot_ok": stop_ok,
        "packet_ok": packet_ok,
        "blocked": blocked,
        "notes": notes,
    }
    if lifecycle_handoff is not None:
        summary["lifecycle_static_proof_handoff_ok"] = lifecycle_handoff.get("handoff_pass") is True

    packet_identity = compute_packet_identity(
        contract=CONTRACT_ID,
        readiness_ok=readiness_ok,
        stop_snapshot_ok=stop_ok,
        lifecycle_handoff=lifecycle_handoff,
    )
    packet_digest = compute_packet_digest(
        contract=CONTRACT_ID,
        readiness_bundle=readiness_bundle,
        stop_snapshot=stop_snapshot,
        summary=summary,
        lifecycle_handoff=lifecycle_handoff,
        packet_identity=packet_identity,
    )

    packet = {
        "contract": CONTRACT_ID,
        "metadata": meta,
        "packet_identity": packet_identity,
        "packet_digest": packet_digest,
        "bounded_pilot_readiness": readiness_bundle,
        "stop_signal_snapshot": stop_snapshot,
        "summary": summary,
    }
    if lifecycle_handoff is not None:
        packet["lifecycle_static_proof_handoff"] = lifecycle_handoff

    if stop_build_exc is not None:
        return packet, 2
    if not packet_ok:
        return packet, 1
    return packet, 0


def _print_text(packet: dict[str, Any], *, exit_code: int) -> None:
    s = packet.get("summary") or {}
    print(
        f"packet_ok={s.get('packet_ok')} readiness_ok={s.get('readiness_ok')} "
        f"stop_snapshot_ok={s.get('stop_snapshot_ok')} exit={exit_code}"
    )
    for b in s.get("blocked") or []:
        print(f"  BLOCKED: {b}", file=sys.stderr)
    notes = s.get("notes") or []
    if notes:
        print("--- notes ---")
        for n in notes:
            print(f"  - {n}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Emit a single bounded-pilot operator preflight JSON packet "
            "(read-only; orchestrates readiness + stop-signal snapshot)."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full packet as JSON on stdout",
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
        help="Pass through to bounded pilot readiness: run baseline pytest (slow)",
    )
    args = parser.parse_args()

    from scripts.ops.check_bounded_pilot_readiness import resolve_bounded_pilot_config_path

    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.is_dir() else Path.cwd())
    if not repo_root.is_dir():
        err = {
            "contract": CONTRACT_ID,
            "error": f"repo root not a directory: {repo_root}",
        }
        print(json.dumps(err, indent=2))
        return 2

    config_path = resolve_bounded_pilot_config_path(repo_root, args.config)

    try:
        packet, code = build_operator_preflight_packet(
            repo_root,
            config_path,
            run_tests=args.run_tests,
        )
    except Exception as e:
        fallback = {
            "contract": CONTRACT_ID,
            "error": str(e),
        }
        print(json.dumps(fallback, indent=2))
        return 2

    if args.json:
        print(json.dumps(packet, indent=2))
    else:
        _print_text(packet, exit_code=code)

    return code


if __name__ == "__main__":
    raise SystemExit(main())
