"""CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1 schema + verifier (B2)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    COMPARISON_CLASS_CONTRACT_TEST_MECHANICS,
    COMPARISON_CLASS_CONTROLLED_FIXTURE,
    COMPARISON_CLASS_PRODUCTIVE_CURRENT,
    DECISION_EQUIVALENCE_ARTIFACT,
    DECISION_EQUIVALENCE_SCHEMA_ID,
    DECISION_EQUIVALENCE_SCHEMA_VERSION,
    DECISION_EQUIVALENCE_VERIFIER_ID,
    FIELD_COMPARISON_DIGEST_EQUIVALENT,
    FIELD_COMPARISON_EXACT,
    FIELD_COMPARISON_NOT_APPLICABLE,
    FIELD_COMPARISON_SEMANTICALLY_EQUIVALENT,
    SUPPORTED_COMPARISON_CLASSES,
)
from src.ops.integrated_offline_economic_evidence_v1.decision_input_fingerprint_v1 import (
    compute_decision_input_fingerprint_digest_sha256_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    load_json_object,
    safe_resolve_under_repo,
)

_SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")

_ROW_COMPARABLE_FIELDS: tuple[str, ...] = (
    "decision",
    "side",
    "selected_strategy_ref",
    "scope_gge_outcome",
    "suitability_ranking_outcome",
    "double_play_transition",
    "risk_result",
    "sizing_result",
    "canonical_order_intent_present",
)

_FORBIDDEN_SUBSTITUTION_KEYS: tuple[str, ...] = (
    "offline_replay_pass_authority",
    "head_bound_correctness_substitution",
    "head_bound_correctness_pass",
    "fixture_parity_authority",
    "ghv_substitution",
    "natural_enter_substitution",
    "step29m_economic_validity_proven",
    "step29m_status_substitution",
)


@dataclass
class DecisionEquivalenceVerificationResultV1:
    equivalence_verified: bool
    required_row_count: int = 0
    failed_required_row_count: int = 0
    unresolved_required_row_count: int = 0
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equivalence_verified": self.equivalence_verified,
            "required_row_count": self.required_row_count,
            "failed_required_row_count": self.failed_required_row_count,
            "unresolved_required_row_count": self.unresolved_required_row_count,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "verifier_id": DECISION_EQUIVALENCE_VERIFIER_ID,
            "artifact_name": DECISION_EQUIVALENCE_ARTIFACT,
        }


@dataclass(frozen=True)
class DecisionEquivalenceVerificationContextV1:
    identity_binding_verified: bool = False
    md_bridge_verified: bool = False
    declared_equivalence_class: str | None = None


def _classify_field_comparison(
    *,
    field_name: str,
    left: Any,
    right: Any,
) -> tuple[str, bool]:
    if left is None and right is None:
        return FIELD_COMPARISON_NOT_APPLICABLE, True
    if left is None or right is None:
        return FIELD_COMPARISON_EXACT, False
    ls, rs = str(left), str(right)
    if ls == rs:
        if field_name.endswith("_digest_sha256") or "_digest" in field_name:
            return FIELD_COMPARISON_DIGEST_EQUIVALENT, True
        return FIELD_COMPARISON_EXACT, True
    if field_name.endswith("_digest_sha256") and _SHA64.match(ls) and _SHA64.match(rs):
        return FIELD_COMPARISON_DIGEST_EQUIVALENT, False
    return FIELD_COMPARISON_SEMANTICALLY_EQUIVALENT, False


def _verify_row(
    *,
    row: Mapping[str, Any],
    row_index: int,
    blockers: list[str],
) -> tuple[int, int]:
    prefix = f"ROW_{row_index}"
    required = row.get("required", True) is not False
    if not required:
        return 0, 0

    for key in ("canonical_instrument_id", "observation_id", "epoch_id"):
        if not str(row.get(key) or "").strip():
            blockers.append(f"{prefix}:{key.upper()}_MISSING")

    binding = row.get("decision_input_binding_v1")
    if not isinstance(binding, Mapping):
        blockers.append(f"{prefix}:DECISION_INPUT_BINDING_V1_MISSING")
        return 1, 0

    expected_fp = str(row.get("decision_input_fingerprint_digest_sha256") or "")
    recomputed = compute_decision_input_fingerprint_digest_sha256_v1(binding=dict(binding))
    if not _SHA64.match(expected_fp):
        blockers.append(f"{prefix}:DECISION_INPUT_FINGERPRINT_INVALID")
    elif expected_fp.lower() != recomputed.lower():
        blockers.append(f"{prefix}:DECISION_INPUT_FINGERPRINT_MISMATCH")

    current = row.get("current_decision_v1")
    offline = row.get("offline_decision_v1")
    if not isinstance(current, Mapping) or not isinstance(offline, Mapping):
        blockers.append(f"{prefix}:DECISION_SIDE_MISSING")
        return 1, 0

    row_failed = 0
    row_unresolved = 0
    for field_name in _ROW_COMPARABLE_FIELDS:
        classification, ok = _classify_field_comparison(
            field_name=field_name,
            left=current.get(field_name),
            right=offline.get(field_name),
        )
        if classification == FIELD_COMPARISON_NOT_APPLICABLE:
            continue
        if not ok:
            row_failed += 1
            blockers.append(f"{prefix}:FIELD_MISMATCH:{field_name.upper()}")
        if row.get(f"{field_name}_comparison_unresolved") is True:
            row_unresolved += 1
            blockers.append(f"{prefix}:UNRESOLVED_REQUIRED:{field_name.upper()}")

    if row_failed:
        return 1, row_unresolved
    return 0, row_unresolved


def verify_current_offline_decision_equivalence_v1(
    *,
    repo_root: Path | None = None,
    artifact_relpath: str | None = None,
    equivalence_document: Mapping[str, Any] | None = None,
    context: DecisionEquivalenceVerificationContextV1 | None = None,
) -> DecisionEquivalenceVerificationResultV1:
    blockers: list[str] = []
    notes = ["B2_DECISION_EQUIVALENCE_VERIFIER", f"VERIFIER_ID={DECISION_EQUIVALENCE_VERIFIER_ID}"]
    ctx = context or DecisionEquivalenceVerificationContextV1()

    doc: dict[str, Any] = {}
    if equivalence_document is not None:
        doc = dict(equivalence_document)
    elif repo_root is not None and artifact_relpath:
        target = safe_resolve_under_repo(repo_root=repo_root.resolve(), relpath=artifact_relpath)
        if target is None:
            blockers.append("ARTIFACT_RELPATH_FORBIDDEN")
        else:
            loaded, load_blockers = load_json_object(target)
            blockers.extend(load_blockers)
            doc = loaded
    else:
        blockers.append("EQUIVALENCE_DOCUMENT_MISSING")

    failed_required = 0
    unresolved_required = 0
    required_row_count = 0

    if doc:
        if doc.get("schema_id") != DECISION_EQUIVALENCE_SCHEMA_ID:
            blockers.append("SCHEMA_ID_MISMATCH")
        if str(doc.get("schema_version") or "") != DECISION_EQUIVALENCE_SCHEMA_VERSION:
            blockers.append("SCHEMA_VERSION_MISMATCH")
        if doc.get("authority_effect") != AUTHORITY_EFFECT_NONE:
            blockers.append("AUTHORITY_EFFECT_NOT_NONE")
        if doc.get("verifier_id") != DECISION_EQUIVALENCE_VERIFIER_ID:
            blockers.append("VERIFIER_ID_MISMATCH")

        for forbidden in _FORBIDDEN_SUBSTITUTION_KEYS:
            if doc.get(forbidden) is True:
                blockers.append(f"FORBIDDEN_SUBSTITUTION:{forbidden.upper()}")

        eq_class = str(doc.get("equivalence_class") or "")
        if eq_class not in SUPPORTED_COMPARISON_CLASSES:
            blockers.append("EQUIVALENCE_CLASS_UNSUPPORTED")
        if ctx.declared_equivalence_class and eq_class != ctx.declared_equivalence_class:
            blockers.append("EQUIVALENCE_CLASS_ESCALATION_OR_MISMATCH")

        if (
            eq_class == COMPARISON_CLASS_CONTROLLED_FIXTURE
            and doc.get("productive_current_claimed") is True
        ):
            blockers.append("FORBIDDEN_CONTROLLED_FIXTURE_ESCALATED_TO_PRODUCTIVE")

        if eq_class == COMPARISON_CLASS_PRODUCTIVE_CURRENT:
            if not ctx.identity_binding_verified:
                blockers.append("PRODUCTIVE_EQUIVALENCE_IDENTITY_BINDING_NOT_VERIFIED")
            if not ctx.md_bridge_verified:
                blockers.append("PRODUCTIVE_EQUIVALENCE_MD_BRIDGE_NOT_VERIFIED")
            gates = doc.get("productive_gate_binding_v1")
            if not isinstance(gates, Mapping):
                blockers.append("PRODUCTIVE_GATE_BINDING_V1_MISSING")
            else:
                for gate_key in (
                    "g17_typed_volatility_binding_mode",
                    "cap61_observation_acceptance_binding_mode",
                    "confirmation_progression_binding_mode",
                ):
                    if not str(gates.get(gate_key) or "").strip():
                        blockers.append(f"PRODUCTIVE_GATE:{gate_key.upper()}_MISSING")

        if doc.get("aggregate_equivalence_pass") is True:
            blockers.append("FORBIDDEN_MANUAL_AGGREGATE_EQUIVALENCE_PASS")

        rows = doc.get("comparison_rows")
        if not isinstance(rows, list):
            blockers.append("COMPARISON_ROWS_MISSING")
            rows = []
        if not rows:
            blockers.append("FORBIDDEN_EMPTY_COMPARISON_ROW_SET")

        for idx, row in enumerate(rows):
            if not isinstance(row, Mapping):
                blockers.append(f"ROW_{idx}:MALFORMED")
                failed_required += 1
                continue
            if row.get("required", True) is not False:
                required_row_count += 1
            fail_inc, unresolved_inc = _verify_row(
                row=row,
                row_index=idx,
                blockers=blockers,
            )
            failed_required += fail_inc
            unresolved_required += unresolved_inc

        if eq_class == COMPARISON_CLASS_CONTRACT_TEST_MECHANICS:
            notes.append("CONTRACT_TEST_MECHANICS_SCOPE")

    unique = sorted(set(blockers))
    equivalence_verified = (
        not unique and required_row_count > 0 and failed_required == 0 and unresolved_required == 0
    )
    if doc.get("equivalence_verified") is True and not equivalence_verified:
        notes.append("IGNORED_SELF_ASSERTED_EQUIVALENCE_VERIFIED_BOOLEAN")

    return DecisionEquivalenceVerificationResultV1(
        equivalence_verified=equivalence_verified,
        required_row_count=required_row_count,
        failed_required_row_count=failed_required,
        unresolved_required_row_count=unresolved_required,
        blockers=unique,
        notes=notes,
    )
