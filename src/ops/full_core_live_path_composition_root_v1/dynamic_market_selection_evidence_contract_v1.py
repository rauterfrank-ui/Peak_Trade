"""Dynamic market / selection evidence contract (AUTHORITY=NONE).

Classifies productive observations as STABLE_INVARIANT, DYNAMIC_VALUE, or
DYNAMIC_RELATIONAL_EVIDENCE. Does not mutate Product Runtime decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SELECTED_FUTURE_COUNT,
)

OWNER = "full_core_live_path_composition_root_v1.dynamic_market_selection_evidence_contract_v1"
CONTRACT_AUTHORITY = "NONE"
SCHEMA_VERSION = "dynamic_market_selection_evidence_contract.v1"
ARTIFACT_FILENAME = "dynamic_market_selection_evidence_contract_v1.json"

SEMANTIC_CLASS_STABLE_INVARIANT = "STABLE_INVARIANT"
SEMANTIC_CLASS_DYNAMIC_VALUE = "DYNAMIC_VALUE"
SEMANTIC_CLASS_DYNAMIC_RELATIONAL_EVIDENCE = "DYNAMIC_RELATIONAL_EVIDENCE"

EXPECTED_BEHAVIOR_STABLE = "STABLE"
EXPECTED_BEHAVIOR_MAY_CHANGE = "MAY_CHANGE"

RELATION_PASS = "PASS"
RELATION_FAIL = "FAIL"
RELATION_UNKNOWN = "UNKNOWN_CURRENT"
RELATION_NOT_APPLICABLE = "NOT_APPLICABLE"

PATH_CORRECT_WITH_PASS = "PATH_CORRECT_WITH_PASS"
PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION = "PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION"
RELATIONAL_EVIDENCE_FAILURE = "RELATIONAL_EVIDENCE_FAILURE"
PATH_UNKNOWN_CURRENT = "UNKNOWN_CURRENT"

DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT_RULE = (
    "DYNAMIC_VALUE_CHANGE != SYSTEM_DRIFT; relational mismatch is evidence failure"
)

CORE_RELATIONS_FOR_PATH_INTEGRITY_V1: tuple[str, ...] = (
    "SELECTION_TO_BINDING_IDENTITY",
    "BINDING_TO_MARKET_IDENTITY",
    "BINDING_TO_SIZING_IDENTITY",
    "DECISION_SIDE_PROPAGATION",
    "VENUE_PLAN_CONTEXT_IDENTITY",
    "POST_AUTHORITY_INVARIANT",
    "PRE_EXTERNAL_TERMINAL_INVARIANT",
)

REQUIRED_RELATIONS_V1: tuple[str, ...] = (
    "SELECTION_TO_BINDING_IDENTITY",
    "BINDING_TO_MARKET_IDENTITY",
    "BINDING_TO_CONTRACT_IDENTITY",
    "BINDING_TO_SIZING_IDENTITY",
    "DECISION_SIDE_PROPAGATION",
    "SIZING_OUTCOME_EXPLAINED",
    "PROTECTIVE_STOP_CONTEXT_IDENTITY",
    "VENUE_PLAN_CONTEXT_IDENTITY",
    "FRESH_PRETRADE_CONTEXT_IDENTITY",
    "PRE_EXTERNAL_TERMINAL_INVARIANT",
    "POST_AUTHORITY_INVARIANT",
)


@dataclass(frozen=True)
class DynamicMarketSelectionObservationContextV1:
    """Observation-only correlation surface (does not participate in trading)."""

    run_id: str = ""
    cycle_index: int | None = None
    generation_id: str = ""
    observation_stage: str = ""
    selected_instrument: str = ""
    bound_instrument: Mapping[str, Any] | None = None
    observed_instrument_id: str = ""
    reference_price: str = ""
    sizing_state: Mapping[str, Any] | None = None
    decision_outcome: str = ""
    selected_side: str = ""
    pre_external_reached: bool | None = None
    policy_outcome: str = ""
    contract_spec: Mapping[str, Any] | None = None
    protective_stop_context: Mapping[str, Any] | None = None
    fresh_pretrade_captured: bool | None = None
    source_provenance: str = ""
    observed_at: str = ""


def native_correlation_key_from_instrument_id_v1(instrument_id: str) -> str | None:
    """Map canonical instrument_id to venue native id when pattern is known."""
    token = str(instrument_id or "").strip()
    if not token:
        return None
    last = token.split(":")[-1].lower()
    if last.endswith("-swap"):
        base = last[: -len("-swap")]
        parts = base.split("-")
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"{parts[0].upper()}-{parts[1].upper()}-SWAP"
    return None


def _norm_native(native: str) -> str:
    return str(native or "").strip().upper()


def _identity_match(selected: str, other_native: str, other_instrument_id: str) -> bool | None:
    sel = _norm_native(selected)
    if not sel:
        return None
    if other_native:
        return sel == _norm_native(other_native)
    derived = native_correlation_key_from_instrument_id_v1(other_instrument_id)
    if derived is None:
        return None
    return sel == _norm_native(derived)


def _relation_row(
    *,
    relation_name: str,
    relation_status: str,
    detail: str = "",
    semantic_class: str = SEMANTIC_CLASS_DYNAMIC_RELATIONAL_EVIDENCE,
) -> dict[str, Any]:
    return {
        "relation_name": relation_name,
        "relation_status": relation_status,
        "semantic_class": semantic_class,
        "authority": CONTRACT_AUTHORITY,
        "detail": detail,
    }


def _dynamic_value_observation(
    *,
    field_name: str,
    observed_value: Any,
    observation_stage: str,
    source_provenance: str,
    ctx: DynamicMarketSelectionObservationContextV1,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "cycle_index": ctx.cycle_index,
        "generation_id": ctx.generation_id,
        "observation_stage": observation_stage,
        "semantic_class": SEMANTIC_CLASS_DYNAMIC_VALUE,
        "field_name": field_name,
        "observed_value": observed_value,
        "source_provenance": source_provenance,
        "observed_at": ctx.observed_at,
        "expected_behavior": EXPECTED_BEHAVIOR_MAY_CHANGE,
        "authority": CONTRACT_AUTHORITY,
        "selected_instrument": ctx.selected_instrument,
        "bound_instrument": ctx.bound_instrument.get("venue_native_id")
        if isinstance(ctx.bound_instrument, Mapping)
        else "",
        "observed_instrument": ctx.observed_instrument_id,
    }


def evaluate_relations_v1(
    ctx: DynamicMarketSelectionObservationContextV1,
) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    bound = dict(ctx.bound_instrument or {})
    bound_native = str(bound.get("venue_native_id") or "")
    bound_instrument_id = str(bound.get("instrument_id") or "")

    sel_bind = _identity_match(ctx.selected_instrument, bound_native, bound_instrument_id)
    if sel_bind is True:
        relations.append(
            _relation_row(
                relation_name="SELECTION_TO_BINDING_IDENTITY",
                relation_status=RELATION_PASS,
            )
        )
    elif sel_bind is False:
        relations.append(
            _relation_row(
                relation_name="SELECTION_TO_BINDING_IDENTITY",
                relation_status=RELATION_FAIL,
                detail="selected_instrument does not match bound identity",
            )
        )
    else:
        relations.append(
            _relation_row(
                relation_name="SELECTION_TO_BINDING_IDENTITY",
                relation_status=RELATION_UNKNOWN,
            )
        )

    sizing = dict(ctx.sizing_state or {})
    pre = dict(sizing.get("pre_sizing_risk") or {})
    envelope = dict(sizing.get("scope_capital_envelope") or {})
    ref_price = str(pre.get("reference_price") or ctx.reference_price or "")
    env_inst = str(envelope.get("instrument_id") or ctx.observed_instrument_id or "")

    if ref_price and env_inst:
        market_match = _identity_match(ctx.selected_instrument, "", env_inst)
        if market_match is True and bound_native:
            bound_market = _identity_match(bound_native, "", env_inst)
            if bound_market is False:
                market_match = False
        if market_match is True:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_MARKET_IDENTITY",
                    relation_status=RELATION_PASS,
                )
            )
        elif market_match is False:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_MARKET_IDENTITY",
                    relation_status=RELATION_FAIL,
                    detail="market/sizing instrument identity mismatch",
                )
            )
        else:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_MARKET_IDENTITY",
                    relation_status=RELATION_UNKNOWN,
                )
            )
    else:
        relations.append(
            _relation_row(
                relation_name="BINDING_TO_MARKET_IDENTITY",
                relation_status=RELATION_UNKNOWN,
                detail="missing reference_price or instrument context",
            )
        )

    if ctx.contract_spec:
        spec_native = str(ctx.contract_spec.get("venue_native_id") or "")
        spec_match = _identity_match(ctx.selected_instrument, spec_native, bound_instrument_id)
        if spec_match is True:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_CONTRACT_IDENTITY",
                    relation_status=RELATION_PASS,
                )
            )
        elif spec_match is False:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_CONTRACT_IDENTITY",
                    relation_status=RELATION_FAIL,
                )
            )
        else:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_CONTRACT_IDENTITY",
                    relation_status=RELATION_UNKNOWN,
                )
            )
    else:
        relations.append(
            _relation_row(
                relation_name="BINDING_TO_CONTRACT_IDENTITY",
                relation_status=RELATION_UNKNOWN,
                detail="contract specification not exposed in context",
            )
        )

    if env_inst or bound_instrument_id:
        sizing_match = _identity_match(
            ctx.selected_instrument, bound_native, env_inst or bound_instrument_id
        )
        if sizing_match is True:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_SIZING_IDENTITY",
                    relation_status=RELATION_PASS,
                )
            )
        elif sizing_match is False:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_SIZING_IDENTITY",
                    relation_status=RELATION_FAIL,
                )
            )
        else:
            relations.append(
                _relation_row(
                    relation_name="BINDING_TO_SIZING_IDENTITY",
                    relation_status=RELATION_UNKNOWN,
                )
            )
    else:
        relations.append(
            _relation_row(
                relation_name="BINDING_TO_SIZING_IDENTITY",
                relation_status=RELATION_UNKNOWN,
            )
        )

    decision = str(ctx.decision_outcome or "").lower()
    side = str(ctx.selected_side or "").lower()
    sizing_side = str(pre.get("side") or sizing.get("selected_side") or "").lower()
    if decision and side:
        side_ok = (decision in {"enter_short", "enter_long"}) and (
            (decision == "enter_short" and side == "short")
            or (decision == "enter_long" and side == "long")
        )
        if side_ok and (not sizing_side or sizing_side == side or sizing_side == side.upper()):
            relations.append(
                _relation_row(
                    relation_name="DECISION_SIDE_PROPAGATION",
                    relation_status=RELATION_PASS,
                )
            )
        elif not side_ok:
            relations.append(
                _relation_row(
                    relation_name="DECISION_SIDE_PROPAGATION",
                    relation_status=RELATION_FAIL,
                    detail="decision_outcome and selected_side inconsistent",
                )
            )
        else:
            relations.append(
                _relation_row(
                    relation_name="DECISION_SIDE_PROPAGATION",
                    relation_status=RELATION_UNKNOWN,
                    detail="sizing side not available for propagation check",
                )
            )
    else:
        relations.append(
            _relation_row(
                relation_name="DECISION_SIDE_PROPAGATION",
                relation_status=RELATION_UNKNOWN,
            )
        )

    reason_codes = list(sizing.get("reason_codes") or [])
    outcome = str(sizing.get("outcome") or ctx.policy_outcome or "")
    has_min_qty = any(
        k in sizing or k in pre or (ctx.contract_spec or {}).get("min_quantity")
        for k in ("min_quantity", "venue_min_quantity", "minSz")
    )
    if "BELOW_MIN_QUANTITY" in reason_codes and not has_min_qty:
        relations.append(
            _relation_row(
                relation_name="SIZING_OUTCOME_EXPLAINED",
                relation_status=RELATION_UNKNOWN,
                detail="BELOW_MIN_QUANTITY without persisted min quantity",
            )
        )
    elif outcome in {"BLOCKED", "DENY"} and reason_codes:
        relations.append(
            _relation_row(
                relation_name="SIZING_OUTCOME_EXPLAINED",
                relation_status=RELATION_PASS,
                detail="policy outcome explained by reason_codes",
            )
        )
    elif outcome:
        relations.append(
            _relation_row(
                relation_name="SIZING_OUTCOME_EXPLAINED",
                relation_status=RELATION_PASS if outcome == "PASS" else RELATION_UNKNOWN,
            )
        )
    else:
        relations.append(
            _relation_row(
                relation_name="SIZING_OUTCOME_EXPLAINED",
                relation_status=RELATION_UNKNOWN,
            )
        )

    if ctx.protective_stop_context:
        ps_native = str(ctx.protective_stop_context.get("venue_native_id") or "")
        ps_match = _identity_match(ctx.selected_instrument, ps_native, bound_instrument_id)
        relations.append(
            _relation_row(
                relation_name="PROTECTIVE_STOP_CONTEXT_IDENTITY",
                relation_status=RELATION_PASS
                if ps_match is True
                else RELATION_FAIL
                if ps_match is False
                else RELATION_UNKNOWN,
            )
        )
    else:
        relations.append(
            _relation_row(
                relation_name="PROTECTIVE_STOP_CONTEXT_IDENTITY",
                relation_status=RELATION_UNKNOWN,
                detail="protective stop context not in observation surface",
            )
        )

    if bound_native or bound_instrument_id:
        vp_match = _identity_match(ctx.selected_instrument, bound_native, bound_instrument_id)
        relations.append(
            _relation_row(
                relation_name="VENUE_PLAN_CONTEXT_IDENTITY",
                relation_status=RELATION_PASS
                if vp_match is True
                else RELATION_FAIL
                if vp_match is False
                else RELATION_UNKNOWN,
            )
        )
    else:
        relations.append(
            _relation_row(
                relation_name="VENUE_PLAN_CONTEXT_IDENTITY",
                relation_status=RELATION_UNKNOWN,
            )
        )

    if ctx.fresh_pretrade_captured is True:
        relations.append(
            _relation_row(
                relation_name="FRESH_PRETRADE_CONTEXT_IDENTITY",
                relation_status=RELATION_PASS,
                detail="captured external GET contracts present",
            )
        )
    elif ctx.fresh_pretrade_captured is False:
        relations.append(
            _relation_row(
                relation_name="FRESH_PRETRADE_CONTEXT_IDENTITY",
                relation_status=RELATION_UNKNOWN,
                detail="fresh pretrade capture absent",
            )
        )
    else:
        relations.append(
            _relation_row(
                relation_name="FRESH_PRETRADE_CONTEXT_IDENTITY",
                relation_status=RELATION_UNKNOWN,
            )
        )

    relations.append(
        _relation_row(
            relation_name="PRE_EXTERNAL_TERMINAL_INVARIANT",
            relation_status=RELATION_PASS,
            detail="PRE_EXTERNAL remains terminal; reachability is independent fact",
            semantic_class=SEMANTIC_CLASS_STABLE_INVARIANT,
        )
    )

    post_ok = (
        POST_ALLOWED is False
        and EXTERNAL_EFFECT_AUTHORIZED is False
        and REAL_VENUE_POST_ALLOWED is False
    )
    relations.append(
        _relation_row(
            relation_name="POST_AUTHORITY_INVARIANT",
            relation_status=RELATION_PASS if post_ok else RELATION_FAIL,
            semantic_class=SEMANTIC_CLASS_STABLE_INVARIANT,
        )
    )

    return relations


def stable_invariant_observations_v1(
    ctx: DynamicMarketSelectionObservationContextV1,
) -> list[dict[str, Any]]:
    bound = dict(ctx.bound_instrument or {})
    rows: list[dict[str, Any]] = []
    for field_name, value in (
        ("POST_ALLOWED", POST_ALLOWED),
        ("EXTERNAL_EFFECT_AUTHORIZED", EXTERNAL_EFFECT_AUTHORIZED),
        ("REAL_VENUE_POST_ALLOWED", REAL_VENUE_POST_ALLOWED),
        (
            "MAX_POSITIONS_EFFECTIVE",
            int(bound.get("max_positions_effective") or MAX_POSITIONS_EFFECTIVE),
        ),
        (
            "SELECTED_FUTURE_COUNT",
            int(bound.get("selected_future_count") or SELECTED_FUTURE_COUNT),
        ),
    ):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "semantic_class": SEMANTIC_CLASS_STABLE_INVARIANT,
                "field_name": field_name,
                "observed_value": value,
                "expected_behavior": EXPECTED_BEHAVIOR_STABLE,
                "authority": CONTRACT_AUTHORITY,
                "run_id": ctx.run_id,
                "cycle_index": ctx.cycle_index,
            }
        )
    if ctx.pre_external_reached is not None:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "semantic_class": SEMANTIC_CLASS_STABLE_INVARIANT,
                "field_name": "PRE_EXTERNAL_REACHED",
                "observed_value": ctx.pre_external_reached,
                "expected_behavior": EXPECTED_BEHAVIOR_STABLE,
                "authority": CONTRACT_AUTHORITY,
                "detail": "factual stage reachability; not success criterion",
            }
        )
    return rows


def build_dynamic_value_observations_v1(
    ctx: DynamicMarketSelectionObservationContextV1,
) -> list[dict[str, Any]]:
    stage = ctx.observation_stage or "PRODUCT_RUNTIME"
    prov = ctx.source_provenance or "dynamic_market_selection_evidence_contract_v1"
    rows: list[dict[str, Any]] = []
    if ctx.selected_instrument:
        rows.append(
            _dynamic_value_observation(
                field_name="selected_instrument",
                observed_value=ctx.selected_instrument,
                observation_stage=stage,
                source_provenance=prov,
                ctx=ctx,
            )
        )
    if ctx.reference_price:
        rows.append(
            _dynamic_value_observation(
                field_name="reference_price",
                observed_value=ctx.reference_price,
                observation_stage=stage,
                source_provenance=prov,
                ctx=ctx,
            )
        )
    sizing = dict(ctx.sizing_state or {})
    if sizing:
        for key in ("final_quantity", "outcome"):
            if key in sizing:
                rows.append(
                    _dynamic_value_observation(
                        field_name=key,
                        observed_value=sizing.get(key),
                        observation_stage=stage,
                        source_provenance=prov,
                        ctx=ctx,
                    )
                )
        pre = sizing.get("pre_sizing_risk") or {}
        if isinstance(pre, Mapping):
            for key in ("candidate_quantity_upper_bound", "reference_price"):
                if key in pre:
                    rows.append(
                        _dynamic_value_observation(
                            field_name=key,
                            observed_value=pre.get(key),
                            observation_stage=stage,
                            source_provenance=prov,
                            ctx=ctx,
                        )
                    )
        for code in sizing.get("reason_codes") or ():
            rows.append(
                _dynamic_value_observation(
                    field_name="sizing_reason_code",
                    observed_value=code,
                    observation_stage=stage,
                    source_provenance=prov,
                    ctx=ctx,
                )
            )
    return rows


def path_relational_integrity_v1(relations: Sequence[Mapping[str, Any]]) -> str:
    by_name = {str(r.get("relation_name")): r for r in relations}
    for name in CORE_RELATIONS_FOR_PATH_INTEGRITY_V1:
        rel = by_name.get(name)
        if rel is None:
            continue
        if rel.get("relation_status") == RELATION_FAIL:
            return "FAIL"
    for name in CORE_RELATIONS_FOR_PATH_INTEGRITY_V1:
        rel = by_name.get(name)
        if rel is None:
            continue
        if rel.get("relation_status") == RELATION_UNKNOWN:
            return "UNKNOWN_CURRENT"
    return "PASS"


def classify_ghv_path_evidence_semantics_v1(
    *,
    relations: Sequence[Mapping[str, Any]],
    pre_external_reached: bool | None,
    policy_outcome: str,
) -> dict[str, Any]:
    integrity = path_relational_integrity_v1(relations)
    policy = str(policy_outcome or "").upper()
    if integrity == "FAIL":
        path_class = RELATIONAL_EVIDENCE_FAILURE
    elif integrity == "UNKNOWN_CURRENT":
        path_class = PATH_UNKNOWN_CURRENT
    elif policy in {"BLOCKED", "DENY", "HOLD"}:
        path_class = PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION
    else:
        path_class = PATH_CORRECT_WITH_PASS

    return {
        "PATH_RELATIONAL_INTEGRITY": integrity,
        "POLICY_OUTCOME": policy or "UNKNOWN",
        "PRE_EXTERNAL_REACHED": pre_external_reached,
        "GHV_PATH_EVIDENCE_CLASSIFICATION": path_class,
        "DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT": True,
        "semantic_rule": DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT_RULE,
    }


def build_dynamic_market_selection_evidence_contract_v1(
    ctx: DynamicMarketSelectionObservationContextV1,
) -> dict[str, Any]:
    relations = evaluate_relations_v1(ctx)
    dynamic_values = build_dynamic_value_observations_v1(ctx)
    stable = stable_invariant_observations_v1(ctx)
    policy_outcome = str(ctx.policy_outcome or "")
    sizing = dict(ctx.sizing_state or {})
    if not policy_outcome and sizing.get("outcome"):
        policy_outcome = str(sizing.get("outcome"))
    ghv_semantics = classify_ghv_path_evidence_semantics_v1(
        relations=relations,
        pre_external_reached=ctx.pre_external_reached,
        policy_outcome=policy_outcome,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "authority": CONTRACT_AUTHORITY,
        "run_id": ctx.run_id,
        "cycle_index": ctx.cycle_index,
        "generation_id": ctx.generation_id,
        "observation_stage": ctx.observation_stage,
        "semantic_classes_implemented": [
            SEMANTIC_CLASS_STABLE_INVARIANT,
            SEMANTIC_CLASS_DYNAMIC_VALUE,
            SEMANTIC_CLASS_DYNAMIC_RELATIONAL_EVIDENCE,
        ],
        "dynamic_value_change_is_not_drift_rule": DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT_RULE,
        "stable_invariant_observations": stable,
        "dynamic_value_observations": dynamic_values,
        "relational_evidence": relations,
        "required_relations_v1": list(REQUIRED_RELATIONS_V1),
        "ghv_path_evidence_semantics": ghv_semantics,
    }


def observation_context_from_mapping_v1(
    payload: Mapping[str, Any],
) -> DynamicMarketSelectionObservationContextV1:
    return DynamicMarketSelectionObservationContextV1(
        run_id=str(payload.get("run_id") or ""),
        cycle_index=payload.get("cycle_index")
        if isinstance(payload.get("cycle_index"), int)
        else None,
        generation_id=str(payload.get("generation_id") or ""),
        observation_stage=str(payload.get("observation_stage") or ""),
        selected_instrument=str(payload.get("selected_instrument") or ""),
        bound_instrument=dict(payload["bound_instrument"])
        if isinstance(payload.get("bound_instrument"), Mapping)
        else None,
        observed_instrument_id=str(payload.get("observed_instrument_id") or ""),
        reference_price=str(payload.get("reference_price") or ""),
        sizing_state=dict(payload["sizing_state"])
        if isinstance(payload.get("sizing_state"), Mapping)
        else None,
        decision_outcome=str(payload.get("decision_outcome") or ""),
        selected_side=str(payload.get("selected_side") or ""),
        pre_external_reached=payload.get("pre_external_reached")
        if isinstance(payload.get("pre_external_reached"), bool)
        else None,
        policy_outcome=str(payload.get("policy_outcome") or ""),
        contract_spec=dict(payload["contract_spec"])
        if isinstance(payload.get("contract_spec"), Mapping)
        else None,
        protective_stop_context=dict(payload["protective_stop_context"])
        if isinstance(payload.get("protective_stop_context"), Mapping)
        else None,
        fresh_pretrade_captured=payload.get("fresh_pretrade_captured")
        if isinstance(payload.get("fresh_pretrade_captured"), bool)
        else None,
        source_provenance=str(payload.get("source_provenance") or ""),
        observed_at=str(payload.get("observed_at") or ""),
    )


def _sizing_from_field_provenance(
    field_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    for row in field_rows:
        if row.get("field_name") == "sizing_state" and row.get("stage") == "LIVE_29P_JOIN_OUTPUT":
            value = row.get("value")
            if isinstance(value, Mapping):
                return dict(value)
    return None


def build_observation_context_from_evidence_root_v1(
    evidence_root: Path,
    *,
    field_provenance_rows: Sequence[Mapping[str, Any]] | None = None,
) -> DynamicMarketSelectionObservationContextV1 | None:
    pre_path = evidence_root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    selected = ""
    run_id = ""
    cycle_index: int | None = None
    pre_external: bool | None = None
    if pre_path.is_file():
        pre = json.loads(pre_path.read_text(encoding="utf-8"))
        selected = str(pre.get("NATIVE_ID") or "")
        run_id = str(pre.get("RUN_ID") or "")
        pre_external = str(pre.get("PRE_EXTERNAL_REACHED", "")).lower() == "true"

    manifest_path = (
        evidence_root
        / "ghv_pre_external_continuation_snapshot_v1"
        / "ghv_pre_external_continuation_snapshot_manifest_v1.json"
    )
    bound: dict[str, Any] | None = None
    fresh: bool | None = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(manifest.get("bound_instrument"), Mapping):
            bound = dict(manifest["bound_instrument"])
        if not run_id:
            run_id = str(manifest.get("run_id") or manifest.get("continuous_run_id") or "")
        if cycle_index is None and isinstance(manifest.get("cycle_index"), int):
            cycle_index = int(manifest["cycle_index"])
        gets = manifest.get("captured_external_get_contracts") or {}
        fresh = bool(gets) if isinstance(gets, Mapping) else False

    rows = list(field_provenance_rows or [])
    if not rows:
        fp = evidence_root / "ghv_pre_external_field_provenance_v1.jsonl"
        if fp.is_file():
            for line in fp.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))

    sizing = _sizing_from_field_provenance(rows)
    pre_sizing = dict((sizing or {}).get("pre_sizing_risk") or {})
    envelope = dict((sizing or {}).get("scope_capital_envelope") or {})
    decision = ""
    side = ""
    for row in rows:
        if (
            row.get("stage") == "LIVE_29P_JOIN_OUTPUT"
            and row.get("field_name") == "decision_outcome"
        ):
            decision = str(row.get("value") or "")
        if row.get("stage") == "LIVE_29P_JOIN_OUTPUT" and row.get("field_name") == "selected_side":
            side = str(row.get("value") or "")

    if not selected and bound:
        selected = str(bound.get("venue_native_id") or "")

    if not selected and not sizing and not bound:
        return None

    return DynamicMarketSelectionObservationContextV1(
        run_id=run_id,
        cycle_index=cycle_index,
        observation_stage="LIVE_29P_JOIN_OUTPUT",
        selected_instrument=selected,
        bound_instrument=bound,
        observed_instrument_id=str(envelope.get("instrument_id") or ""),
        reference_price=str(pre_sizing.get("reference_price") or ""),
        sizing_state=sizing,
        decision_outcome=decision,
        selected_side=side,
        pre_external_reached=pre_external,
        policy_outcome=str((sizing or {}).get("outcome") or ""),
        fresh_pretrade_captured=fresh,
        source_provenance=str(evidence_root),
    )


def build_ghv_dynamic_evidence_from_whole_cycle_v1(
    *,
    evidence_root: Path,
    field_provenance_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    ctx = build_observation_context_from_evidence_root_v1(
        evidence_root,
        field_provenance_rows=field_provenance_rows,
    )
    if ctx is None:
        return None
    return build_dynamic_market_selection_evidence_contract_v1(ctx)


def persist_dynamic_market_selection_evidence_contract_v1(
    *,
    evidence_root: Path,
    contract: Mapping[str, Any],
) -> Path:
    evidence_root.mkdir(parents=True, exist_ok=True)
    out = evidence_root / ARTIFACT_FILENAME
    out.write_text(json.dumps(dict(contract), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return out


__all__ = [
    "ARTIFACT_FILENAME",
    "CONTRACT_AUTHORITY",
    "DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT_RULE",
    "OWNER",
    "PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION",
    "PATH_CORRECT_WITH_PASS",
    "RELATIONAL_EVIDENCE_FAILURE",
    "CORE_RELATIONS_FOR_PATH_INTEGRITY_V1",
    "REQUIRED_RELATIONS_V1",
    "SCHEMA_VERSION",
    "SEMANTIC_CLASS_DYNAMIC_RELATIONAL_EVIDENCE",
    "SEMANTIC_CLASS_DYNAMIC_VALUE",
    "SEMANTIC_CLASS_STABLE_INVARIANT",
    "DynamicMarketSelectionObservationContextV1",
    "build_dynamic_market_selection_evidence_contract_v1",
    "build_ghv_dynamic_evidence_from_whole_cycle_v1",
    "build_observation_context_from_evidence_root_v1",
    "classify_ghv_path_evidence_semantics_v1",
    "native_correlation_key_from_instrument_id_v1",
    "observation_context_from_mapping_v1",
    "persist_dynamic_market_selection_evidence_contract_v1",
    "path_relational_integrity_v1",
]
