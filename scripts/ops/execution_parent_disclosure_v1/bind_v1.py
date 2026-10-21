"""Admit an execution disclosure scope beside parent membership. AUTHORITY=NONE.

The registry scope stays the membership scope. Disclosure subjects are a
separate input. They are not copied into functional membership, and this
module does not call GHV, the causal-graph writer, or GHOSV.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    CLASSIFICATION_OBSERVED,
    CLASSIFICATION_UNKNOWN,
    BASELINE_CURRENCY_CURRENT,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
    GIT_READ_COMMANDS,
    INSTRUMENT_IDS,
    OBSERVED_FIELDS,
    PARENT_ID,
    SCHEMA_ID,
    SCHEMA_VERSION,
    STATUS_ADMITTED,
    STATUS_DISCLOSURE_SCOPE_ABSENT,
    STATUS_FAIL_CLOSED,
    STATUS_LOADER_REJECT,
    STATUS_REJECTED,
    STATUS_UNEXPECTED_MEMBERSHIP_ACCEPTED,
    UNKNOWN_FIELDS,
)
from scripts.ops.guardian_parent_slot_loader_v1.load_v1 import load_parent_slots_v1
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    SCOPE_FIELDS,
    STATUS_ACCEPTED,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_EMPTY,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def bind_execution_disclosure_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    disclosure_subjects: list[Any] | None,
    baseline_currency: str,
    authority: str = AUTHORITY,
    activation: str = ACTIVATION,
    membership_ratified: bool = False,
    guardian_ratified: bool = False,
    registry_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Validate the execution slot and admit explicit disclosure subjects."""
    control_reasons = _control_reasons(
        authority=authority,
        activation=activation,
        membership_ratified=membership_ratified,
        guardian_ratified=guardian_ratified,
    )
    if control_reasons:
        return _envelope(STATUS_REJECTED, reasons=control_reasons)
    if baseline_currency != BASELINE_CURRENCY_CURRENT:
        return _envelope(STATUS_FAIL_CLOSED, reasons=["historical_baseline_rejected"])
    if not _full_sha(authoritative_commit_sha) or not _full_sha(authoritative_tree_sha):
        return _envelope(STATUS_FAIL_CLOSED, reasons=["baseline_absent"])

    root = _REPO_ROOT if repo_root is None else repo_root
    actual_tree = _git_read(root, ["show", "-s", "--format=%T", authoritative_commit_sha])
    if actual_tree is None or actual_tree.strip() != authoritative_tree_sha:
        return _envelope(
            STATUS_FAIL_CLOSED,
            reasons=["commit_tree_mismatch"],
            mismatches=["baseline_tree"],
        )

    loaded = load_parent_slots_v1(registry_path)
    if loaded["status"] != STATUS_ACCEPTED:
        return _envelope(
            STATUS_LOADER_REJECT,
            reasons=["loader_rejected"],
            loader_reasons=list(loaded["reasons"]),
        )
    slot = next(
        (item for item in loaded["slots"] if item.get("parent_id") == PARENT_ID),
        None,
    )
    if not isinstance(slot, Mapping):
        return _envelope(STATUS_LOADER_REJECT, reasons=["execution_slot_missing"])
    identity_reasons = _identity_reasons(slot)
    if identity_reasons:
        return _envelope(STATUS_REJECTED, reasons=identity_reasons)

    scope = {field: list(slot["scope"][field]) for field in SCOPE_FIELDS}
    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
        scope=scope,
        repo_root=root,
    )
    binding_status = str(binding.get("status") or "")
    historical = [str(item) for item in binding.get("stale_sources") or []]
    if binding_status == STATUS_ACCEPTED:
        return _envelope(
            STATUS_UNEXPECTED_MEMBERSHIP_ACCEPTED,
            reasons=["membership_binder_accepted"],
            membership_binding_status=binding_status,
            historical_sources=historical,
        )
    if binding_status != STATUS_SCOPE_EMPTY:
        return _envelope(
            binding_status or STATUS_REJECTED,
            reasons=[str(item) for item in binding.get("reasons") or []],
            mismatches=[str(item) for item in binding.get("mismatches") or []],
            membership_binding_status=binding_status or None,
            historical_sources=historical,
        )

    observed, unknown, subject_reason = _parse_subjects(
        disclosure_subjects,
        repo_root=root,
        tree_sha=authoritative_tree_sha,
    )
    if subject_reason == STATUS_DISCLOSURE_SCOPE_ABSENT:
        return _envelope(
            STATUS_DISCLOSURE_SCOPE_ABSENT,
            reasons=["disclosure_subjects_empty"],
            membership_binding_status=STATUS_SCOPE_EMPTY,
            historical_sources=historical,
        )
    if subject_reason is not None:
        return _envelope(
            STATUS_REJECTED,
            reasons=[subject_reason],
            membership_binding_status=STATUS_SCOPE_EMPTY,
            historical_sources=historical,
        )
    return _envelope(
        STATUS_ADMITTED,
        reasons=[],
        membership_binding_status=STATUS_SCOPE_EMPTY,
        historical_sources=historical,
        observed_subjects=observed,
        unknown_subjects=unknown,
        baseline_commit=authoritative_commit_sha,
        baseline_tree=authoritative_tree_sha,
    )


def _control_reasons(
    *,
    authority: str,
    activation: str,
    membership_ratified: bool,
    guardian_ratified: bool,
) -> list[str]:
    reasons: list[str] = []
    if authority != AUTHORITY:
        reasons.append("authority_rejected")
    if activation != ACTIVATION:
        reasons.append("activation_rejected")
    if membership_ratified is not False:
        reasons.append("membership_ratification_rejected")
    if guardian_ratified is not False:
        reasons.append("guardian_ratification_rejected")
    return reasons


def _full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _identity_reasons(slot: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key, expected in INSTRUMENT_IDS.items():
        if slot.get(key) != expected:
            reasons.append(f"instrument_identity_mismatch:{key}")
    if slot.get("authority") != AUTHORITY:
        reasons.append("slot_authority")
    if slot.get("activation") != ACTIVATION:
        reasons.append("slot_activation")
    if slot.get("membership_ratified") is not False:
        reasons.append("slot_membership_ratified")
    if slot.get("guardian_ratified") is not False:
        reasons.append("slot_guardian_ratified")
    if slot.get("calibration_status") != "UNCALIBRATED":
        reasons.append("slot_calibrated")
    scope = slot.get("scope")
    if not isinstance(scope, Mapping):
        reasons.append("slot_scope_missing")
        return reasons
    for field in SCOPE_FIELDS:
        if field not in scope or not isinstance(scope[field], list):
            reasons.append(f"slot_scope_field:{field}")
    return reasons


def _parse_subjects(
    disclosure_subjects: list[Any] | None,
    *,
    repo_root: Path,
    tree_sha: str,
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None, str | None]:
    if not isinstance(disclosure_subjects, list):
        return None, None, "disclosure_subjects_not_list"
    if not disclosure_subjects:
        return None, None, STATUS_DISCLOSURE_SCOPE_ABSENT
    observed: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, subject in enumerate(disclosure_subjects):
        label = f"disclosure_subjects[{index}]"
        if not isinstance(subject, Mapping):
            return None, None, f"{label}_not_object"
        classification = subject.get("classification")
        if classification == CLASSIFICATION_OBSERVED:
            allowed = OBSERVED_FIELDS
        elif classification == CLASSIFICATION_UNKNOWN:
            allowed = UNKNOWN_FIELDS
        else:
            return None, None, f"{label}_classification"
        extra = sorted(set(subject) - allowed)
        if extra:
            return None, None, f"{label}_extra:{extra[0]}"
        subject_id = subject.get("subject_id")
        if not isinstance(subject_id, str) or subject_id.strip() == "":
            return None, None, f"{label}_subject_id"
        if subject_id in seen:
            return None, None, f"subject_id_duplicate:{subject_id}"
        seen.add(subject_id)
        if classification == CLASSIFICATION_UNKNOWN:
            reason = subject.get("unknown_reason")
            if not isinstance(reason, str) or reason.strip() == "":
                return None, None, f"{label}_unknown_reason"
            unknown.append(
                {
                    "subject_id": subject_id,
                    "classification": CLASSIFICATION_UNKNOWN,
                    "unknown_reason": reason,
                    "functional_membership": False,
                }
            )
            continue
        reference_reason = _observed_reference_reason(
            subject, repo_root=repo_root, tree_sha=tree_sha
        )
        if reference_reason is not None:
            return None, None, f"{label}_{reference_reason}"
        observed.append(
            {
                "subject_id": subject_id,
                "classification": CLASSIFICATION_OBSERVED,
                "path": subject["path"],
                "symbol": subject["symbol"],
                "start_line": subject["start_line"],
                "end_line": subject["end_line"],
                "tree_sha": tree_sha,
                "functional_membership": False,
            }
        )
    return observed, unknown, None


def _observed_reference_reason(
    subject: Mapping[str, Any],
    *,
    repo_root: Path,
    tree_sha: str,
) -> str | None:
    path = subject.get("path")
    symbol = subject.get("symbol")
    start_line = _line_number(subject.get("start_line"))
    end_line = _line_number(subject.get("end_line"))
    if not isinstance(path, str) or path.strip() == "" or path.startswith(("/", "\\")):
        return "path"
    if ".." in Path(path).parts:
        return "path"
    if not isinstance(symbol, str) or symbol.strip() == "":
        return "symbol"
    if start_line is None or end_line is None or start_line > end_line:
        return "lines"
    listed = _git_read(repo_root, ["ls-tree", "-r", "--name-only", tree_sha, "--", path])
    if listed is None or listed.strip() != path:
        return "path_absent"
    blob = _git_read(repo_root, ["show", f"{tree_sha}:{path}"])
    if blob is None:
        return "blob_unreadable"
    lines = blob.splitlines()
    if end_line > len(lines):
        return "line_out_of_range"
    window = "\n".join(lines[start_line - 1 : end_line])
    if re.search(rf"\b{re.escape(symbol)}\b", window) is None:
        return "symbol_absent"
    return None


def _line_number(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 1:
        return None
    return value


def _git_read(repo_root: Path, args: list[str]) -> str | None:
    if not args or args[0] not in GIT_READ_COMMANDS:
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _envelope(
    status: str,
    *,
    reasons: list[str],
    mismatches: list[str] | None = None,
    membership_binding_status: str | None = None,
    historical_sources: list[str] | None = None,
    loader_reasons: list[str] | None = None,
    observed_subjects: list[dict[str, Any]] | None = None,
    unknown_subjects: list[dict[str, Any]] | None = None,
    baseline_commit: str = "",
    baseline_tree: str = "",
) -> dict[str, Any]:
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": AUTHORITY,
        "trading_authority": AUTHORITY,
        "safety_authority": AUTHORITY,
        "execution_authority": AUTHORITY,
        "post_authority": AUTHORITY,
        "activation": ACTIVATION,
        "membership_ratified": False,
        "guardian_ratified": False,
        "domain_bound": False,
        "operationally_ready": False,
        "causal_closure_proven": False,
        "current_validated": False,
        "post_allowed": False,
        "external_effect_authorized": False,
        "productive_activation": False,
        "double_play_full_owner_lock": DOUBLE_PLAY_FULL_OWNER_LOCK,
        "parent_id": PARENT_ID,
        "instrument_ids": dict(INSTRUMENT_IDS),
        "parent_assignment_performed": False,
        "adapters_invoked": False,
        "files_written": False,
        "domain_functional_members": [],
        "functional_membership_derived": False,
        "observed_subjects": list(observed_subjects or []),
        "unknown_subjects": list(unknown_subjects or []),
        "membership_binding_status": membership_binding_status,
        "historical_sources": list(historical_sources or []),
        "loader_reasons": list(loader_reasons or []),
        "mismatches": list(mismatches or []),
        "reasons": list(reasons),
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
    }
