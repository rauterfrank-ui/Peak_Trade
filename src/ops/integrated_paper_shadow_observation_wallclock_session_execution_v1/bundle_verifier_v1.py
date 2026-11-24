"""Offline verifier for wallclock observation evidence bundles."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
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
    require_event_time_utc,
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
    EXECUTION_CLASS_ANALYTICAL,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    TerminalVerdict,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    APPEND_ONLY,
    REQUIRED_IMMUTABLE,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
    RANKED_SWAP_SCOPES,
    recorded_i17_shadow_instrument_v1,
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

# These sealed I17 captures used the explicit Mark input, but the price-basis
# serializer still retained its ticker-default label. Reconstruct those bytes;
# do not relabel their history or admit that label for current producers.
# Both revisions retain session_runtime_v1.py SHA256
# 9dfc1e22ce45da5275ad2d9905c3d1584183b374701ecbf617bc358a72378590.
_RECORDED_COLLAPSED_MARK_CAPTURE_REVISIONS = frozenset(
    {
        "755d4d5a3f6f2756885bd00f14b5758e76e18442",
        "05243d30437dbaeb5e62ce8c9b0e453cec801ab9",
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
    selected_shadow_decision: dict[str, Any] | None = None

    @property
    def typed_ddo_requirement_met(self) -> bool:
        readback = self.ddo_readback or {}
        return (
            self.verified
            and self.verdict == TerminalVerdict.PASS.value
            and not self.incomplete
            and readback.get("decision_bundles_readable") is True
            and readback.get("typed_volatility_cycles_with_double_play_bundle", 0)
            == readback.get("typed_volatility_cycles", 0)
            > 0
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.selected_shadow_decision is None:
            payload.pop("selected_shadow_decision")
        return payload


@dataclass
class _ShadowDecisionSelection:
    ref: str | None
    decision: dict[str, Any] | None = None


def _typed_cycle_market_time(
    cycle: dict, mark: dict, session: dict, *, repository_sha: str | None = None
) -> float:
    """Rebuild the original price reference and recover the decision's own clock."""
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
    quote = mark.get("price_basis_quote")
    bid = ask = None
    if quote is not None:
        if (
            not isinstance(quote, dict)
            or quote.get("endpoint") != "/api/v5/market/books"
            or not isinstance(quote.get("body_sha256"), str)
            or len(quote["body_sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in quote["body_sha256"])
        ):
            raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
        bid, ask = quote["bid_px"], quote["ask_px"]
        if (
            not all(
                type(value) in (int, float) and isfinite(value) and value > 0
                for value in (bid, ask)
            )
            or ask < bid
        ):
            raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
        acquired = datetime.fromisoformat(quote["acquired_at_utc"].replace("Z", "+00:00"))
        book_event = quote["event_ts_unix"]
        if (
            acquired.utcoffset() is None
            or type(book_event) not in (int, float)
            or not isfinite(book_event)
            or book_event <= 0
            or not book_event <= acquired.timestamp() <= available
        ):
            raise ValueError("DDO_MARKET_DECISION_CLOCK_INVALID")
    if (
        mark.get("mark_price_field") != "markPx"
        or mark.get("mark_price_endpoint") != "/api/v5/public/mark-price"
    ):
        raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
    price_field = mark["mark_price_field"]
    if repository_sha in _RECORDED_COLLAPSED_MARK_CAPTURE_REVISIONS:
        if (
            quote is not None
            or session.get("mark_price_field") != "markPx"
            or session.get("mark_price_endpoint") != "/api/v5/public/mark-price"
            or session.get("canonical_instrument_id") != "ETH-USD_UM_XPERP-310404"
            or session.get("venue_instrument_id") != "ETH-USD_UM_XPERP-310404"
            or session.get("lane_id") is not None
            or session.get("n5_assignment") is not None
        ):
            raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
        price_field = "last"
    basis = build_explicit_mid_price_basis_v2(
        mid_price=float(price),
        event_ts_unix=float(mark["event_ts_unix"]),
        receive_ts_unix=float(local_receive),
        price_field=price_field,
        bid_px=bid,
        ask_px=ask,
        quote_source="ticker" if quote is None else "public_book",
    )
    if (
        cycle["market_data_reference"] != basis.market_data_reference
        or cycle["price_basis"] != basis.to_dict()
    ):
        raise ValueError("DDO_MARKET_PRICE_REFERENCE_MISMATCH")
    if "canonical_decision_time_utc" in timing:
        stamp = require_event_time_utc(
            timing["canonical_decision_time_utc"], "canonical_decision_time_utc"
        )
        instant = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
        if not isfinite(instant) or instant < decided:
            raise ValueError("DDO_MARKET_DECISION_CLOCK_INVALID")
        return instant
    return float(decided)


def _verify_typed_cycle_bindings(
    root,
    manifest_names,
    typed_cycles,
    records,
    complete_cycles,
    blockers,
    selection: _ShadowDecisionSelection | None,
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
        if (
            session.get("venue_instrument_id")
            in {s.native_id for s in (SOPH_I17, *RANKED_SWAP_SCOPES)}
            or session.get("lane_id") is not None
        ):
            scope = recorded_i17_shadow_instrument_v1(
                (session.get("venue_instrument_id"),), session.get("lane_id")
            )
            if "venue_instrument_binding.json" not in manifest_names:
                raise ValueError("DDO_SHADOW_SESSION_SCOPE_MISMATCH")
            venue = json.loads((root / "venue_instrument_binding.json").read_bytes())
            if scope.instrument_type == "SWAP":
                from src.ops.ranked_shadow_slot4_successor_v1 import recorded_shadow_rank_matches_v1

                original = session.get("n5_assignment")
                if (
                    not isinstance(original, dict)
                    or original != venue.get("n5_assignment")
                    or original.get("lane_id") != scope.lane_id
                    or not recorded_shadow_rank_matches_v1(original, scope)
                    or original.get("venue_native_id") != scope.native_id
                    or original.get("canonical_instrument_id") != scope.canonical_id
                    or not all(
                        original.get(key)
                        for key in (
                            "transition_id",
                            "selection_id",
                            "universe_snapshot_id",
                            "ranking_snapshot_id",
                        )
                    )
                    or not all(
                        re.fullmatch("[0-9a-f]{64}", str(original.get(key)))
                        for key in ("selection_digest", "ranking_digest")
                    )
                ):
                    raise ValueError("DDO_SHADOW_N5_ORIGINAL_MISMATCH")
            if (
                scope.native_id not in {s.native_id for s in (SOPH_I17, *RANKED_SWAP_SCOPES)}
                or session.get("canonical_instrument_id") != scope.canonical_id
                or venue.get("mapping_source") != f"I17_SHADOW_{scope.lane_id}_INSTRUMENT_SCOPE"
                or any(
                    venue.get(key) != session.get(key)
                    for key in (
                        "lane_id",
                        "canonical_instrument_id",
                        "venue_instrument_id",
                        "mapping_digest",
                    )
                )
            ):
                raise ValueError("DDO_SHADOW_SESSION_SCOPE_MISMATCH")
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
                decided = _typed_cycle_market_time(
                    cycle, marks[sequence], session, repository_sha=session_revision
                )
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
                if selection is not None and (
                    bundle.decision_event_ref == selection.ref
                    or (selection.ref is None and selection.decision is None)
                ):
                    if (
                        session.get("capability_id") != CAPABILITY_ID
                        or session.get("execution_class") != EXECUTION_CLASS_ANALYTICAL
                        or session.get("paper_execution") is not False
                    ):
                        blockers.append("DDO_SHADOW_SESSION_SCOPE_MISMATCH")
                        continue
                    timing = cycle["shadow_decision_timing"]
                    selection.decision = {
                        "session_id": session["session_id"],
                        "repository_sha": session_revision,
                        "cycle_id": capture_id,
                        "cycle_index": index,
                        "decision_event_ref": bundle.decision_event_ref,
                        "observation_ref": bundle.observation_ref,
                        "input_evidence_ref": bundle.input_evidence_ref,
                        "decision_event_time_utc": records[bundle.decision_event_ref][
                            "event_time_utc"
                        ],
                        "decision_semantic_digest": bundle.semantic_digest,
                        "decision_input_digest": bundle.input_digest,
                        "market_sequence": sequence,
                        "market_data_reference": cycle["market_data_reference"],
                        "mark_event_ts_unix": timing["mark_event_ts_unix"],
                        "mark_receive_ts_unix": timing["mark_receive_ts_unix"],
                        "decision_input_available_ts_unix": timing[
                            "decision_input_available_ts_unix"
                        ],
                        "canonical_instrument_id": session["canonical_instrument_id"],
                        "venue_instrument_id": session["venue_instrument_id"],
                        "mapping_digest": session["mapping_digest"],
                        **({"lane_id": session["lane_id"]} if session.get("lane_id") else {}),
                        **(
                            {"n5_assignment": session["n5_assignment"]}
                            if session.get("n5_assignment")
                            else {}
                        ),
                    }
    return validated


def _read_ddo_capture(
    root: Path, manifest_names: set[str], selection: _ShadowDecisionSelection | None
) -> dict[str, Any] | None:
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
            root, manifest_names, typed_cycles, records, complete_cycles, blockers, selection
        )
    if not result["complete_double_play_bundles"]:
        blockers.append("DDO_NO_COMPLETE_DOUBLE_PLAY_BUNDLE")
    result["blockers"] = sorted(set(blockers))
    result["decision_bundles_readable"] = not blockers
    return result


def verify_wallclock_evidence_bundle_v1(
    *,
    evidence_root: Path,
    select_shadow_decision_ref: str | None = None,
    select_first_typed_shadow_decision: bool = False,
) -> WallclockEvidenceVerificationResultV1:
    if select_first_typed_shadow_decision and select_shadow_decision_ref is not None:
        raise ValueError("SHADOW_DECISION_SELECTION_MODE_CONFLICT")
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
            manifest_bytes = manifest_path.read_bytes()
            for line in manifest_bytes.decode("utf-8").splitlines():
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

    selection = (
        None
        if select_shadow_decision_ref is None and not select_first_typed_shadow_decision
        else _ShadowDecisionSelection(select_shadow_decision_ref)
    )
    ddo_readback = _read_ddo_capture(root, set(manifest_digests), selection)
    if verdict == TerminalVerdict.ABORT.value:
        result = RESULT_ABORT_VERIFIED
    else:
        result = RESULT_PASS
    verification = WallclockEvidenceVerificationResultV1(
        result=result,
        verified=True,
        verdict=verdict,
        incomplete=incomplete,
        notes=notes + [f"APPEND_ONLY={list(APPEND_ONLY)}"],
        ddo_readback=ddo_readback,
    )
    if verification.typed_ddo_requirement_met and selection and selection.decision is not None:
        try:
            unchanged = manifest_path.read_bytes() == manifest_bytes and all(
                not (root / name).is_symlink()
                and hashlib.sha256((root / name).read_bytes()).hexdigest() == manifest_digests[name]
                for name in (
                    "session_manifest.json",
                    "repo_sha.txt",
                    "market_data_sequence.jsonl",
                    BRIDGE_CYCLE_LEDGER_FILENAME,
                    LEDGER_FILENAME_DEFAULT,
                )
            )
        except OSError:
            unchanged = False
        if not unchanged:
            verification.result = RESULT_FAIL
            verification.verified = False
            verification.blockers.append("SHADOW_EVIDENCE_CHANGED_DURING_READBACK")
            return verification
        verification.selected_shadow_decision = {
            **selection.decision,
            "shadow_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        }
    return verification
