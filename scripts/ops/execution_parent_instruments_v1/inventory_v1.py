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
)

FORWARD_ORIGIN: Final = "execution.decision.runtime_cycle"
REVERSE_ORIGIN: Final = "execution.boundary.trading_replay"
DIRECT_DEPTH: Final = 1
TRANSITIVE_DEPTH: Final = 2
