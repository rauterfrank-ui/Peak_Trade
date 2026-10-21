"""Bounded execution disclosure inventory. Not functional membership."""

from __future__ import annotations

from typing import Final

OBSERVED_SUBJECTS: Final = (
    {
        "subject_id": "execution.decision.runtime_cycle",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1."
            "current_productive_master_v2_runtime_cycle_v1."
            "run_current_productive_master_v2_runtime_cycle_v1"
        ),
        "symbol": "run_current_productive_master_v2_runtime_cycle_v1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_master_v2_runtime_cycle_v1.py"
        ),
        "start_line": 566,
        "end_line": 1131,
        "source_sha256": "3f7d5f4439f884be049cee68046b9bbb4005c2e48f52134181ffa9b41609017e",
        "domain": "EXECUTION_HOST",
    },
    {
        "subject_id": "execution.boundary.trading_replay",
        "qualified_symbol": (
            "src.trading.master_v2.integrated_offline_trading_logic_replay_v1."
            "run_integrated_offline_trading_logic_replay_v1"
        ),
        "symbol": "run_integrated_offline_trading_logic_replay_v1",
        "path": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "start_line": 1419,
        "end_line": 2309,
        "source_sha256": "ffa6cd4c49e377f6f971020a7bbd5957b78188ea0c28d05c8fdbf78a2e971044",
        "domain": "TRADING_BOUNDARY_REFERENCE",
    },
    {
        "subject_id": "execution.pre_external.offline_path",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1.path_v1."
            "run_full_core_live_path_offline_v1"
        ),
        "symbol": "run_full_core_live_path_offline_v1",
        "path": "src/ops/full_core_live_path_composition_root_v1/path_v1.py",
        "start_line": 64,
        "end_line": 184,
        "source_sha256": "2835bbf4bf5c0ef8e1f892658564815b7ef68f0895c80194e5a1e4ec612caaf0",
        "domain": "PRE_EXTERNAL",
    },
    {
        "subject_id": "execution.order_preparation.translate_venue_plan",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1.venue_translation_v1."
            "translate_core_live_intent_to_venue_plan_v1"
        ),
        "symbol": "translate_core_live_intent_to_venue_plan_v1",
        "path": "src/ops/full_core_live_path_composition_root_v1/venue_translation_v1.py",
        "start_line": 77,
        "end_line": 161,
        "source_sha256": "bd551f0712a329e6ea03da40e78a07ce7f7f3740adf726a4758379947d971d0b",
        "domain": "ORDER_PREPARATION",
    },
    {
        "subject_id": "execution.pre_external.halt",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1.execution_boundary_v1."
            "halt_at_live_execution_boundary_v1"
        ),
        "symbol": "halt_at_live_execution_boundary_v1",
        "path": "src/ops/full_core_live_path_composition_root_v1/execution_boundary_v1.py",
        "start_line": 81,
        "end_line": 248,
        "source_sha256": "9903eb24a073c805f1cec631228c359fa78eb94c5ac03c692fb8f8e2f485f99b",
        "domain": "PRE_EXTERNAL",
    },
    {
        "subject_id": "execution.host_send.test_transport_seam",
        "qualified_symbol": (
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_envelope_bound_single_use_external_effect_send_seam_v1."
            "execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1"
        ),
        "symbol": "execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py"
        ),
        "start_line": 315,
        "end_line": 561,
        "source_sha256": "c729b1bb8368788393e99b131da8322541ae18791fa7428b5d913de9f84aa607",
        "domain": "HOST_SEND_TEST_TRANSPORT",
    },
    {
        "subject_id": "execution.submission.send_seam",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1."
            "envelope_bound_external_effect_send_seam_v1."
            "attempt_envelope_bound_external_effect_send_v1"
        ),
        "symbol": "attempt_envelope_bound_external_effect_send_v1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "envelope_bound_external_effect_send_seam_v1.py"
        ),
        "start_line": 115,
        "end_line": 231,
        "source_sha256": "bf26f7608b7b46031e2f9ff43a929463d520c4c1f87063425b39f83f66cbb6e3",
        "domain": "SUBMISSION_BOUNDARY",
    },
    {
        "subject_id": "execution.pre_external.fresh_runtime_applicability",
        "qualified_symbol": (
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_fresh_runtime_to_pre_external_effect_applicability_v1."
            "execute_current_productive_fresh_runtime_to_pre_external_effect_applicability_v1"
        ),
        "symbol": "execute_current_productive_fresh_runtime_to_pre_external_effect_applicability_v1",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py"
        ),
        "start_line": 452,
        "end_line": 829,
        "source_sha256": "7326d2844abcb4360ea03aebcb20a5040763dbea342e5badd6b760d467ee9082",
        "domain": "PRE_EXTERNAL",
    },
    {
        "subject_id": "execution.submission.one_shot_join",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1."
            "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1."
            "attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1"
        ),
        "symbol": (
            "attempt_current_productive_one_shot_fresh_envelope_permit_mint_"
            "durable_consume_and_post_join_v1"
        ),
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
        ),
        "start_line": 436,
        "end_line": 576,
        "source_sha256": "c235f5a030b0d03326df63365ba15a9fc139b15eb20a8d0e2837e28a5e162ea3",
        "domain": "SUBMISSION_BOUNDARY",
    },
    {
        "subject_id": "execution.authority.external_effect_authorized",
        "qualified_symbol": (
            "src.ops.full_core_live_path_composition_root_v1.constants_v1."
            "EXTERNAL_EFFECT_AUTHORIZED"
        ),
        "symbol": "EXTERNAL_EFFECT_AUTHORIZED",
        "path": "src/ops/full_core_live_path_composition_root_v1/constants_v1.py",
        "start_line": 369,
        "end_line": 371,
        "source_sha256": "f83bbc875c04571e6089d16853e25aa10bc7bdf61673da3ff4306d4925a8412a",
        "domain": "AUTHORITY_BOUNDARY",
    },
)

UNKNOWN_SUBJECT: Final = {
    "subject_id": "execution.submission.decision_link.unknown",
    "qualified_symbol": "UNKNOWN",
    "classification": "UNKNOWN",
    "unknown_reason": "no proven call from the decision cycle to submission",
}

CALL_EDGES: Final = (
    {
        "edge_id": "execution.decision.runtime_cycle.CALLS.trading_replay",
        "source_subject_id": "execution.decision.runtime_cycle",
        "target_subject_id": "execution.boundary.trading_replay",
        "callee_symbol": "run_integrated_offline_trading_logic_replay_v1",
        "evidence_line": 1015,
        "boundary_reference": True,
    },
    {
        "edge_id": "execution.pre_external.offline_path.CALLS.translate_venue_plan",
        "source_subject_id": "execution.pre_external.offline_path",
        "target_subject_id": "execution.order_preparation.translate_venue_plan",
        "callee_symbol": "translate_core_live_intent_to_venue_plan_v1",
        "evidence_line": 94,
        "boundary_reference": False,
    },
    {
        "edge_id": "execution.pre_external.offline_path.CALLS.halt",
        "source_subject_id": "execution.pre_external.offline_path",
        "target_subject_id": "execution.pre_external.halt",
        "callee_symbol": "halt_at_live_execution_boundary_v1",
        "evidence_line": 137,
        "boundary_reference": False,
    },
    {
        "edge_id": "execution.host_send.test_transport_seam.CALLS.send_seam",
        "source_subject_id": "execution.host_send.test_transport_seam",
        "target_subject_id": "execution.submission.send_seam",
        "callee_symbol": "attempt_envelope_bound_external_effect_send_v1",
        "evidence_line": 364,
        "boundary_reference": False,
        "edge_type": "CALLS",
    },
    {
        "edge_id": "execution.pre_external.fresh_runtime_applicability.CALLS.decision_cycle",
        "source_subject_id": "execution.pre_external.fresh_runtime_applicability",
        "target_subject_id": "execution.decision.runtime_cycle",
        "callee_symbol": "run_current_productive_master_v2_runtime_cycle_v1",
        "evidence_line": 827,
        "boundary_reference": False,
        "edge_type": "CALLS",
    },
    {
        "edge_id": "execution.submission.one_shot_join.CALLS.send_seam",
        "source_subject_id": "execution.submission.one_shot_join",
        "target_subject_id": "execution.submission.send_seam",
        "callee_symbol": "attempt_envelope_bound_external_effect_send_v1",
        "evidence_line": 570,
        "boundary_reference": False,
        "edge_type": "CALLS",
    },
    {
        "edge_id": "execution.submission.send_seam.READS_STATE.external_effect_authorized",
        "source_subject_id": "execution.submission.send_seam",
        "target_subject_id": "execution.authority.external_effect_authorized",
        "callee_symbol": "",
        "line_token": "EXTERNAL_EFFECT_AUTHORIZED",
        "evidence_line": 134,
        "boundary_reference": False,
        "edge_type": "READS_STATE",
    },
)

UNKNOWN_EDGES: Final = (
    {
        "edge_id": "execution.decision.runtime_cycle.edge.offline_path.unknown",
        "classification": "UNKNOWN",
        "unknown_reason": "no src caller links the decision cycle to the offline pre-external path",
        "functional_membership": False,
    },
    {
        "edge_id": "execution.decision.runtime_cycle.edge.submission.unknown",
        "classification": "UNKNOWN",
        "unknown_reason": "no proven call from the decision cycle to submission",
        "functional_membership": False,
    },
    {
        "edge_id": "execution.pre_external.fresh_runtime_applicability.edge.submission.unknown",
        "classification": "UNKNOWN",
        "unknown_reason": (
            "the pre-external applicability function calls the decision cycle "
            "and does not call the submission seam"
        ),
        "functional_membership": False,
    },
)

FORWARD_ORIGIN: Final = "execution.decision.runtime_cycle"
REVERSE_ORIGIN: Final = "execution.boundary.trading_replay"
MISSION_ID: Final = "EXECUTION_DECISION_TO_SUBMISSION_BOUNDARY"
MISSION_START: Final = "execution.decision.runtime_cycle"
MISSION_END: Final = "execution.submission.send_seam"
PRE_EXTERNAL_CALL_EDGE: Final = (
    "execution.pre_external.fresh_runtime_applicability.CALLS.decision_cycle"
)
ONE_SHOT_CALL_EDGE: Final = "execution.submission.one_shot_join.CALLS.send_seam"
AUTHORITY_READ_EDGE: Final = "execution.submission.send_seam.READS_STATE.external_effect_authorized"
DIRECT_DEPTH: Final = 1
TRANSITIVE_DEPTH: Final = 2

POLICY_GUARDS: Final = (
    {
        "guard_id": "execution.submission.send_seam.policy.external_effect_remains_false",
        "subject_id": "execution.submission.send_seam",
        "evidence_line": 135,
        "token": "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE",
        "finding_kind": "POLICY",
        "category": "BOUNDARY",
        "observed_state": "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE",
    },
    {
        "guard_id": "execution.submission.send_seam.policy.real_venue_post_forbidden",
        "subject_id": "execution.submission.send_seam",
        "evidence_line": 177,
        "token": "STANDING_REAL_VENUE_POST_FORBIDDEN",
        "finding_kind": "POLICY",
        "category": "BOUNDARY",
        "observed_state": "STANDING_REAL_VENUE_POST_FORBIDDEN",
    },
    {
        "guard_id": "execution.pre_external.halt.state.hard_stop_before_wire",
        "subject_id": "execution.pre_external.halt",
        "evidence_line": 101,
        "token": "HARD_STOP_BEFORE_WIRE",
        "finding_kind": "STATE",
        "category": "BOUNDARY",
        "observed_state": "HARD_STOP_BEFORE_WIRE",
    },
    {
        "guard_id": "execution.pre_external.halt.policy.external_effect_false_halts",
        "subject_id": "execution.pre_external.halt",
        "evidence_line": 236,
        "token": "EXTERNAL_EFFECT_AUTHORIZED is False",
        "finding_kind": "POLICY",
        "category": "BOUNDARY",
        "observed_state": "HALT_REQUIRES_EXTERNAL_EFFECT_AUTHORIZED_FALSE",
    },
)

ABSENCE_CHECKS: Final = (
    {
        "check_id": "decision_window_omits_send_seam",
        "subject_id": "execution.decision.runtime_cycle",
        "absent_symbol": "attempt_envelope_bound_external_effect_send_v1",
    },
    {
        "check_id": "decision_window_omits_offline_path",
        "subject_id": "execution.decision.runtime_cycle",
        "absent_symbol": "run_full_core_live_path_offline_v1",
    },
    {
        "check_id": "pre_external_window_omits_send_seam",
        "subject_id": "execution.pre_external.fresh_runtime_applicability",
        "absent_symbol": "attempt_envelope_bound_external_effect_send_v1",
    },
)
