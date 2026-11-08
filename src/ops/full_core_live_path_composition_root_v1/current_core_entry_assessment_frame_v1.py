"""Carry current original assessment outputs through the existing cursor writer."""

import hashlib
import json

SCHEMA = "current_core_entry_assessment_frame.v1"
_COMPONENTS = {
    "parent",
    "entry",
    "composition",
    "bull_assessment",
    "bear_assessment",
    "bull_survival",
    "bear_survival",
    "bull_suitability",
    "bear_suitability",
}


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def build_current_core_entry_assessment_frame_v1(*, replay, confirmation_state):
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        serialize_canonical_trading_decision_evidence_canonical,
    )
    from trading.master_v2.directional_assessment_v1 import (
        serialize_directional_assessment_canonical,
    )
    from trading.master_v2.survival_assessment_v1 import serialize_survival_result_canonical
    from trading.master_v2.suitability_binding_v1 import serialize_suitability_result_canonical
    from trading.master_v2.double_play_composition_matrix_v1 import (
        serialize_composition_result_canonical,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        serialize_entry_exit_policy_decision_canonical,
    )

    mid = replay.intermediate
    if mid is None or confirmation_state is None:
        return None

    def component(value, serializer):
        if value is None:
            return None
        canonical = serializer(value)
        if hashlib.sha256(canonical.encode()).hexdigest() != value.semantic_digest:
            raise ValueError("CORE_ASSESSMENT_FRAME_COMPONENT_DIGEST_MISMATCH")
        return dict(canonical=canonical, semantic_digest=value.semantic_digest)

    values = {
        "parent": component(
            replay.evidence, serialize_canonical_trading_decision_evidence_canonical
        ),
        "entry": component(mid.entry_exit_decision, serialize_entry_exit_policy_decision_canonical),
        "composition": component(mid.composition_result, serialize_composition_result_canonical),
    }
    for side in ["bull", "bear"]:
        for kind, serializer in [
            ("assessment", serialize_directional_assessment_canonical),
            ("survival", serialize_survival_result_canonical),
            ("suitability", serialize_suitability_result_canonical),
        ]:
            name = side + "_" + kind
            values[name] = component(getattr(mid, name), serializer)
    body = dict(
        schema=SCHEMA,
        instrument_id=replay.evidence.instrument_id,
        trading_epoch=replay.evidence.trading_epoch,
        confirmation_state_digest=confirmation_state.state_digest(),
        components=values,
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": _digest(body)}


def read_current_core_entry_assessment_frame_v1(cursor):
    frame = cursor.entry_assessment_frame
    if (
        not isinstance(frame, dict)
        or set(frame)
        != {
            "schema",
            "instrument_id",
            "trading_epoch",
            "confirmation_state_digest",
            "components",
            "runtime_authorization_effect",
            "digest",
        }
        or frame["schema"] != SCHEMA
        or frame["digest"] != _digest({k: v for k, v in frame.items() if k != "digest"})
        or frame["runtime_authorization_effect"] != "NONE"
        or frame["instrument_id"] != cursor.instrument_id
        or type(frame["trading_epoch"]) is not int
        or frame["trading_epoch"] != cursor.last_evaluated_trading_epoch
        or cursor.cap61_confirmation_state is None
        or frame["confirmation_state_digest"] != cursor.cap61_confirmation_state.state_digest()
        or not isinstance(frame["components"], dict)
        or set(frame["components"]) != _COMPONENTS
    ):
        raise ValueError("CURRENT_CORE_ASSESSMENT_FRAME_UNPROVEN")
    bodies = {}
    for name, value in frame["components"].items():
        if value is None:
            bodies[name] = None
            continue
        if (
            not isinstance(value, dict)
            or set(value) != {"canonical", "semantic_digest"}
            or type(value["canonical"]) is not str
            or hashlib.sha256(value["canonical"].encode()).hexdigest() != value["semantic_digest"]
        ):
            raise ValueError("CURRENT_CORE_ASSESSMENT_COMPONENT_UNPROVEN")
        body = json.loads(value["canonical"])
        if (
            not isinstance(body, dict)
            or body.get("instrument_id") != cursor.instrument_id
            or type(body.get("trading_epoch")) is not int
            or body["trading_epoch"] != frame["trading_epoch"]
            or any(
                body.get(k) != "NONE"
                for k in ["authority_effect", "runtime_effect", "order_effect"]
            )
            or (
                name in {"parent", "entry"}
                and any(
                    body.get(k) is not False for k in ["execution_eligible", "adapter_compatible"]
                )
            )
        ):
            raise ValueError("CURRENT_CORE_ASSESSMENT_COMPONENT_IDENTITY_MISMATCH")
        bodies[name] = body
    parent, entry, composition = (bodies[n] for n in ["parent", "entry", "composition"])
    if (
        any(x is None for x in [parent, entry, composition])
        or parent["entry_exit_policy_ref"] != entry["policy_decision_id"]
        or parent["composition_result_ref"] != composition["composition_id"]
        or entry["composition_result_ref"] != composition["composition_id"]
    ):
        raise ValueError("CURRENT_CORE_ASSESSMENT_PARENT_MISMATCH")
    return bodies


def inspect_current_core_entry_assessment_v1(*, cursor, intent_side, original_strategy):
    bodies = read_current_core_entry_assessment_frame_v1(cursor)
    entry, comp = bodies["entry"], bodies["composition"]
    side = intent_side.lower()
    if (
        bodies["parent"]["decision_outcome"] != "enter_" + side
        or entry["decision_outcome"] != "enter_" + side
        or entry["entry_eligibility"] != "eligible"
        or entry["selected_side"] != side
        or comp["selected_side"] != side
        or comp["composition_status"] != side + "_selected"
    ):
        raise ValueError("CURRENT_CORE_ASSESSMENT_ENTRY_NOT_ADMITTED")
    prefix = "bull" if intent_side == "LONG" else "bear"
    assessment, survival, suitability = (
        bodies[prefix + "_" + n] for n in ["assessment", "survival", "suitability"]
    )
    if (
        any(x is None for x in [assessment, survival, suitability])
        or assessment["status"] != "confirmed"
        or survival["status"] != "pass"
        or suitability["status"] != "pass"
        or suitability["selected_strategy_id"] != original_strategy
        or bodies["parent"]["selected_strategy_ref"] != original_strategy
    ):
        raise ValueError("CURRENT_CORE_ASSESSMENT_SELECTED_CHAIN_NOT_ADMITTED")
    for name, body, ident in [
        ("assessment", assessment, "assessment_id"),
        ("survival", survival, "survival_id"),
        ("suitability", suitability, "suitability_id"),
    ]:
        ref = comp[prefix + "_" + name + "_ref"]
        component = cursor.entry_assessment_frame["components"][prefix + "_" + name]
        if (
            body["side"] != side
            or ref is None
            or ref[ident] != body[ident]
            or ref["semantic_digest"] != component["semantic_digest"]
            or ref["trading_epoch"] != body["trading_epoch"]
            or ref["side"] != side
            or ref["status"] != body["status"]
            or bodies["parent"][prefix + "_" + name + "_ref"] != body[ident]
        ):
            raise ValueError("CURRENT_CORE_ASSESSMENT_REFERENCE_MISMATCH")
    for body, upstream, name, ident in [
        (survival, assessment, "directional_assessment", "assessment_id"),
        (suitability, assessment, "directional_assessment", "assessment_id"),
        (suitability, survival, "survival_result", "survival_id"),
    ]:
        component = cursor.entry_assessment_frame["components"][
            prefix + ("_assessment" if name == "directional_assessment" else "_survival")
        ]
        if (
            body[name + "_id"] != upstream[ident]
            or body[name + "_digest"] != component["semantic_digest"]
            or body[name + "_epoch"] != upstream["trading_epoch"]
            or body[name + "_side"] != side
            or body[name + "_status"] != upstream["status"]
        ):
            raise ValueError("CURRENT_CORE_ASSESSMENT_REFERENCE_MISMATCH")
    return dict(
        scope="CURRENT_ORIGINAL_ASSESSMENT_OUTPUT_VETO_ONLY",
        decision_id=bodies["parent"]["decision_id"],
        selected_strategy=original_strategy,
        frame_digest=cursor.entry_assessment_frame["digest"],
        runtime_authorization_effect="NONE",
        economic_input_provenance="NOT_ASSESSED",
    )


def bind_current_core_entry_frame_reference_v1(*, cursor, parent):
    bodies = read_current_core_entry_assessment_frame_v1(cursor)
    if (
        bodies["parent"]["decision_id"] != parent.decision_id
        or bodies["parent"]["trading_epoch"] != parent.trading_epoch
        or bodies["entry"]["policy_decision_id"] != parent.entry_exit_policy_ref
        or bodies["parent"]["selected_strategy_ref"] != parent.selected_strategy_ref
    ):
        raise ValueError("ORIGINAL_CORE_ASSESSMENT_PARENT_MISMATCH")
    result = dict(
        schema="original_core_entry_frame_reference.v1",
        decision_id=parent.decision_id,
        trading_epoch=parent.trading_epoch,
        entry_policy_id=parent.entry_exit_policy_ref,
        selected_strategy=parent.selected_strategy_ref,
        initial_frame_digest=cursor.entry_assessment_frame["digest"],
    )
    validate_current_core_entry_frame_reference_v1(
        result, decision_id=parent.decision_id, trading_epoch=parent.trading_epoch
    )
    return result


def validate_current_core_entry_frame_reference_v1(ref, *, decision_id, trading_epoch):
    fields = {
        "schema",
        "decision_id",
        "trading_epoch",
        "entry_policy_id",
        "selected_strategy",
        "initial_frame_digest",
    }
    if (
        not isinstance(ref, dict)
        or set(ref) != fields
        or ref.get("schema") != "original_core_entry_frame_reference.v1"
        or type(ref["trading_epoch"]) is not int
        or ref["trading_epoch"] != trading_epoch
        or ref["decision_id"] != decision_id
        or any(
            type(ref[k]) is not str or not ref[k] or ref[k] != ref[k].strip()
            for k in fields - {"trading_epoch"}
        )
        or len(ref["initial_frame_digest"]) != 64
        or any(c not in "0123456789abcdef" for c in ref["initial_frame_digest"])
    ):
        raise ValueError("ORIGINAL_CORE_ASSESSMENT_REFERENCE_INVALID")
