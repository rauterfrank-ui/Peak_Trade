"""Offline verifier for wallclock observation evidence bundles."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from math import isfinite
from pathlib import Path
from typing import Any

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    bind_host_cycle_capture_context_v0,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    require_current_double_play_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    LEDGER_FILENAME_DEFAULT,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    EVIDENCE_SCHEMA_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    TerminalVerdict,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    APPEND_ONLY,
    REQUIRED_IMMUTABLE,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.constants_v1 import (
    BRIDGE_CYCLE_LEDGER_FILENAME,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.ledger_summary_aggregator_v1 import (
    load_bridge_cycle_ledger_v1,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.outcome_completeness_verifier_v1 import (
    verify_wallclock_outcome_completeness_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    build_explicit_mid_price_basis_v2,
)

VERIFIER_ID = "ops.paper_shadow_wallclock_evidence_verifier_v1"
RESULT_PASS = "WALLCLOCK_OBSERVATION_EVIDENCE_VERIFIED"
RESULT_FAIL = "WALLCLOCK_OBSERVATION_EVIDENCE_INVALID"
RESULT_ABORT_VERIFIED = "WALLCLOCK_OBSERVATION_ABORT_VERIFIED"
_MANIFEST_REQUIRED_FILES = frozenset(
    {
        "integrity_manifest.json",
        "terminal_verdict.json",
        "observation_cycle_counters.json",
        "market_data_sequence.jsonl",
        BRIDGE_CYCLE_LEDGER_FILENAME,
    }
)


@dataclass
class WallclockEvidenceVerificationResultV1:
    result: str
    verified: bool
    verdict: str = ""
    incomplete: bool = False
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE
    economic_validity_pass: bool = False
    promotion_pass: bool = False
    ddo_readback: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _typed_cycle_market_time(cycle: dict, mark: dict, session: dict) -> float:
    """Rebuild the bridge's price reference and return the recorded DDO host clock."""
    timing = cycle["shadow_decision_timing"]
    event = timing["mark_event_ts_unix"]
    receive = timing["mark_receive_ts_unix"]
    available = timing["decision_input_available_ts_unix"]
    decided = timing["decision_cycle_ts_unix"]
    if (
        not all(
            type(value) in (int, float) and isfinite(value)
            for value in (event, receive, available, decided)
        )
        or not receive <= available <= decided
    ):
        raise ValueError("DDO_MARKET_DECISION_CLOCK_INVALID")
    if (
        event != mark["event_ts_unix"]
        or receive != mark["mark_receive_ts_unix"]
        or cycle["session_id"] != session["session_id"]
        or cycle["instrument_id"] != session["canonical_instrument_id"]
        or mark["canonical_instrument_id"] != session["canonical_instrument_id"]
        or mark["venue_instrument_id"] != session["venue_instrument_id"]
        or mark["mapping_digest"] != session["mapping_digest"]
        or mark["mid_price"] != mark["mark_px"]
    ):
        raise ValueError("DDO_MARKET_CYCLE_BINDING_MISMATCH")
    price = mark["mid_price"]
    local_receive = mark["receive_ts_unix"]
    if (
        type(price) not in (int, float)
        or not isfinite(price)
        or type(local_receive) not in (int, float)
        or not isfinite(local_receive)
    ):
        raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
    basis = build_explicit_mid_price_basis_v2(
        mid_price=float(price),
        event_ts_unix=float(mark["event_ts_unix"]),
        receive_ts_unix=float(local_receive),
    )
    if (
        cycle["market_data_reference"] != basis.market_data_reference
        or cycle["price_basis"] != basis.to_dict()
    ):
        raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
    return float(decided)


def _verify_typed_cycle_bindings(
    root, manifest_names, typed_cycles, records, complete_cycles, blockers
) -> int:
    if not typed_cycles:
        return 0
    validated = 0
    try:
        if not {"session_manifest.json", "repo_sha.txt"} <= manifest_names:
            raise ValueError("DDO_SESSION_MANIFEST_NOT_BOUND")
        session = json.loads((root / "session_manifest.json").read_bytes())
        session_revision = (root / "repo_sha.txt").read_text(encoding="utf-8").strip()
        if not isinstance(session, dict):
            raise ValueError("DDO_SESSION_MANIFEST_INVALID")
        marks = {}
        for mark in load_bridge_cycle_ledger_v1(root / "market_data_sequence.jsonl"):
            seq = mark["sequence"]
            if type(seq) is not int or seq <= 0 or seq in marks:
                raise ValueError("DDO_MARKET_SEQUENCE_INVALID")
            marks[seq] = mark
    except (OSError, KeyError, ValueError, TypeError) as exc:
        blockers.append(f"DDO_MARKET_READBACK:{type(exc).__name__}")
    else:
        previous_sequence = previous_index = 0
        binding = DdoCaptureBindingV0(enabled=True, precise_host_decision_time=True)
        for cycle in typed_cycles:
            capture = cycle.get("ddo_capture")
            if not isinstance(capture, dict):
                continue
            try:
                index = cycle["cycle_index"]
                sequence = cycle["shadow_decision_timing"]["market_sequence"]
                if (
                    type(sequence) is not int
                    or sequence <= previous_sequence
                    or type(index) is not int
                    or index <= previous_index
                ):
                    raise ValueError("DDO_MARKET_OR_CYCLE_SEQUENCE_INVALID")
                decided = _typed_cycle_market_time(cycle, marks[sequence], session)
                bind_host_cycle_capture_context_v0(
                    binding,
                    event_ts_unix=decided,
                    session_id=session["session_id"],
                    cycle_index=index,
                    repository_sha=session_revision,
                )
                previous_sequence, previous_index = sequence, index
                capture_id = capture["cycle_id"]
                if capture_id != binding.capture_cycle_id:
                    raise ValueError("DDO_CAPTURE_CYCLE_ID_MISMATCH")
                refs = capture["record_ids"]
                if (
                    not isinstance(refs, list)
                    or not refs
                    or any(
                        not isinstance(ref, str)
                        or ref not in records
                        or records[ref]["cycle_id"] != capture_id
                        for ref in refs
                    )
                    or len(refs) != len(set(refs))
                ):
                    raise ValueError("DDO_CAPTURE_RECORD_CYCLE_MISMATCH")
                bundles = complete_cycles.get(capture_id, [])
                if len(bundles) != 1:
                    raise ValueError("DDO_TYPED_CYCLE_BUNDLE_REQUIRED")
                bundle = bundles[0]
                if (
                    bundle.decision_event_ref not in refs
                    or bundle.instrument_id != cycle["instrument_id"]
                ):
                    raise ValueError("DDO_TYPED_CYCLE_DECISION_MISMATCH")
                if any(
                    records[ref]["cycle_id"] != capture_id
                    or records[ref]["event_time_utc"] != binding.capture_event_time_utc
                    for ref in (
                        bundle.decision_event_ref,
                        bundle.observation_ref,
                        bundle.input_evidence_ref,
                    )
                ):
                    raise ValueError("DDO_TYPED_CYCLE_DECISION_CLOCK_MISMATCH")
            except (KeyError, TypeError, OverflowError, OSError):
                blockers.append("DDO_TYPED_CYCLE_EVIDENCE_INVALID")
            except ValueError as exc:
                blockers.append(
                    str(exc) if str(exc).startswith("DDO_") else "DDO_TYPED_CYCLE_EVIDENCE_INVALID"
                )
            else:
                validated += 1
    return validated


def _read_ddo_capture(root: Path, manifest_names: set[str]) -> dict[str, Any] | None:
    cycles = load_bridge_cycle_ledger_v1(root / BRIDGE_CYCLE_LEDGER_FILENAME)
    capture_cycles = [row for row in cycles if "ddo_capture" in row]
    typed_cycles = [
        row for row in cycles if row.get("canonical_market_context_typed_estimate_present") is True
    ]
    if not capture_cycles and not typed_cycles:
        return None
    captures = [row["ddo_capture"] for row in capture_cycles]
    result: dict[str, Any] = {
        "decision_bundles_readable": False,
        "capture_cycles": len(captures),
        "durability_failed_cycles": sum(
            not isinstance(row, dict)
            or row.get("durable_ok") is not True
            or bool(row.get("unpersisted_record_count"))
            for row in captures
        ),
        "typed_volatility_cycles": len(typed_cycles),
        "typed_volatility_cycles_with_double_play_bundle": 0,
        "complete_double_play_bundles": 0,
        "blockers": [],
    }
    blockers = result["blockers"]
    if result["durability_failed_cycles"]:
        blockers.append("DDO_CAPTURE_DURABILITY_FAILURE")
    if any(not isinstance(row.get("ddo_capture"), dict) for row in typed_cycles):
        blockers.append("DDO_TYPED_CYCLE_CAPTURE_REQUIRED")
    for row in cycles:
        hot_path = row.get("canonical_volatility_hot_path_evidence")
        if isinstance(hot_path, dict) and (
            (hot_path.get("volatility_value") is not None)
            is not row.get("canonical_market_context_typed_estimate_present")
        ):
            blockers.append("DDO_TYPED_CYCLE_VOLATILITY_FLAG_MISMATCH")
    if LEDGER_FILENAME_DEFAULT not in manifest_names:
        blockers.append("DDO_LEDGER_NOT_IN_MANIFEST")
        return result

    try:
        ledger_path = root / LEDGER_FILENAME_DEFAULT
        if not ledger_path.is_file() or ledger_path.is_symlink():
            blockers.append("DDO_LEDGER_MISSING_OR_UNSAFE")
            return result
        records = {
            row["record_id"]: row
            for row in AppendOnlyDdoLedgerV0(ledger_path.absolute()).read_all()
        }
        if any(
            not isinstance(ref, str) or ref not in records
            for row in captures
            if isinstance(row, dict) and isinstance(row.get("record_ids"), list)
            for ref in row["record_ids"]
        ):
            blockers.append("DDO_CAPTURE_RECORD_MISSING")
        by_decision = {}
        complete_cycles = {}
        for row in records.values():
            if row["schema_name"] in {
                SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
                SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
            }:
                by_decision.setdefault(row["decision_event_ref"], {})[row["record_id"]] = row
        for ref, siblings in by_decision.items():
            try:
                bundle = require_current_double_play_bundle_v1(
                    records_by_id={ref: records[ref], **siblings}, decision_event_ref=ref
                )
                if bundle.input_evidence_ref is None:
                    blockers.append("DDO_DOUBLE_PLAY_INPUT_MISSING")
                else:
                    result["complete_double_play_bundles"] += 1
                    complete_cycles.setdefault(records[ref]["cycle_id"], []).append(bundle)
            except (DdoError, KeyError) as exc:
                blockers.append(f"DDO_DOUBLE_PLAY_READBACK:{type(exc).__name__}")
    except (DdoError, OSError, ValueError) as exc:
        blockers.append(f"DDO_LEDGER_READBACK:{type(exc).__name__}")
    else:
        result["typed_volatility_cycles_with_double_play_bundle"] = _verify_typed_cycle_bindings(
            root, manifest_names, typed_cycles, records, complete_cycles, blockers
        )
    if not result["complete_double_play_bundles"]:
        blockers.append("DDO_NO_COMPLETE_DOUBLE_PLAY_BUNDLE")
    result["blockers"] = sorted(set(blockers))
    result["decision_bundles_readable"] = not blockers
    return result


def verify_wallclock_evidence_bundle_v1(
    *,
    evidence_root: Path,
) -> WallclockEvidenceVerificationResultV1:
    notes = [
        f"VERIFIER_ID={VERIFIER_ID}",
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "VERIFIER_NO_NETWORK",
        "VERIFIER_NO_MUTATION",
    ]
    blockers: list[str] = []
    root = evidence_root
    if not root.is_dir():
        return WallclockEvidenceVerificationResultV1(
            result=RESULT_FAIL,
            verified=False,
            blockers=["EVIDENCE_ROOT_MISSING"],
            notes=notes,
        )

    manifest_path = root / "evidence_manifest.sha256"
    manifest_digests: dict[str, str] = {}
    if manifest_path.is_symlink() or not manifest_path.is_file():
        blockers.append("EVIDENCE_MANIFEST_MISSING")
    else:
        try:
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                digest, sep, name = line.partition("  ")
                if (
                    not sep
                    or name in {"", ".", "..", manifest_path.name}
                    or any(char in name for char in ("/", "\\", "\x00"))
                    or name in manifest_digests
                ):
                    blockers.append("EVIDENCE_MANIFEST_MALFORMED")
                    continue
                manifest_digests[name] = digest
                path = root / name
                if path.is_symlink():
                    blockers.append(f"MANIFEST_FILE_UNSAFE:{name}")
                elif not path.is_file():
                    blockers.append(f"MANIFEST_FILE_MISSING:{name}")
                elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    blockers.append(f"EVIDENCE_TAMPER:{name}")
        except (OSError, UnicodeError):
            blockers.append("EVIDENCE_MANIFEST_UNREADABLE")

    blockers.extend(
        f"EVIDENCE_MANIFEST_ENTRY_REQUIRED:{name}"
        for name in sorted(_MANIFEST_REQUIRED_FILES - manifest_digests.keys())
    )
    if not blockers:
        try:
            inner = json.loads((root / "integrity_manifest.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            blockers.append("INTEGRITY_MANIFEST_UNREADABLE")
        else:
            outer = {
                name: digest
                for name, digest in manifest_digests.items()
                if name != "integrity_manifest.json"
            }
            if not isinstance(inner, dict) or inner.get("digests") != outer:
                blockers.append("EVIDENCE_MANIFEST_DIGEST_MAP_MISMATCH")

    for name in REQUIRED_IMMUTABLE:
        if not (root / name).is_file():
            # terminal/integrity required always; others may be incomplete abort
            if name in {
                "terminal_verdict.json",
                "integrity_manifest.json",
                "evidence_manifest.sha256",
            }:
                blockers.append(f"REQUIRED_MISSING:{name}")

    if blockers:
        return WallclockEvidenceVerificationResultV1(
            result=RESULT_FAIL, verified=False, blockers=sorted(set(blockers)), notes=notes
        )

    verdict = ""
    incomplete = False
    terminal_path = root / "terminal_verdict.json"
    if terminal_path.is_file():
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
        verdict = str(terminal.get("verdict") or "")
        incomplete = bool(terminal.get("incomplete"))
        if terminal.get("economic_validity_pass") is True:
            blockers.append("ECONOMIC_VALIDITY_SIDE_EFFECT_FORBIDDEN")
        if terminal.get("promotion_pass") is True:
            blockers.append("PROMOTION_SIDE_EFFECT_FORBIDDEN")
        if terminal.get("paper_execution") is True:
            blockers.append("PAPER_EXECUTION_CLAIM_FORBIDDEN")
        if terminal.get("orders_submitted") is True:
            blockers.append("ORDERS_SUBMITTED_CLAIM_FORBIDDEN")
        if terminal.get("schema_id") != EVIDENCE_SCHEMA_ID:
            blockers.append("EVIDENCE_SCHEMA_MISMATCH")
        # Safety ABORT must never be remapped to FAIL
        if verdict == TerminalVerdict.FAIL.value and incomplete:
            blockers.append("FAIL_WITH_INCOMPLETE_FORBIDDEN")
        kill_path = root / "killstate_events.jsonl"
        if kill_path.is_file() and kill_path.read_text(encoding="utf-8").strip():
            if verdict == TerminalVerdict.FAIL.value:
                blockers.append("SAFETY_ABORT_REMAPPED_TO_FAIL")
            if verdict == TerminalVerdict.PASS.value:
                blockers.append("SAFETY_EVENTS_WITH_PASS")

    outcome = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    if not outcome.verified:
        blockers.extend(f"OUTCOME_COMPLETENESS:{b}" for b in outcome.blockers)
    else:
        notes.extend(
            [
                "OUTCOME_COMPLETENESS_VERIFIED=true",
                "VERIFIER_VALIDATES_OUTCOME_COMPLETENESS=true",
                "VERIFIER_CAN_PASS_WITH_UNACCOUNTED_OUTCOMES=false",
            ]
        )
        notes.extend(outcome.notes)

    unique = sorted(set(blockers))
    if unique:
        return WallclockEvidenceVerificationResultV1(
            result=RESULT_FAIL,
            verified=False,
            verdict=verdict,
            incomplete=incomplete,
            blockers=unique,
            notes=notes,
        )

    ddo_readback = _read_ddo_capture(root, set(manifest_digests))
    if verdict == TerminalVerdict.ABORT.value:
        result = RESULT_ABORT_VERIFIED
    else:
        result = RESULT_PASS
    return WallclockEvidenceVerificationResultV1(
        result=result,
        verified=True,
        verdict=verdict,
        incomplete=incomplete,
        notes=notes + [f"APPEND_ONLY={list(APPEND_ONLY)}"],
        ddo_readback=ddo_readback,
    )
