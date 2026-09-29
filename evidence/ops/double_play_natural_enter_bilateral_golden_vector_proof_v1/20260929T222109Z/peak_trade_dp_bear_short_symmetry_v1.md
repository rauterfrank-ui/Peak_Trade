# DOUBLE_PLAY_BEAR_SHORT_SYMMETRY_PROOF_V1

STATUS: SHORT_PATH_PROVEN
BASELINE_SHA: 0353b45e8623c0188359fcfb1e50ec8359bcc847

## BEAR=None on LONG

LONG_VECTOR_BEAR_NONE_EXPECTED=True

integrated_offline_trading_logic_replay_v1: single-lane C3 — bull_assessment/bear_assessment init None; only selected_side receives selected_c3.assessment (LONG→bull, else→bear). Opposite assessment stays None. Fixture assert_complete_decision_ssot_layer_trace_v1 requires bear_assessment is None when expected_selected_side=LONG (and bull_assessment is None when SHORT).

## Short vector

SOURCE: `tests/ops/_current_productive_natural_mv2_dp_enter_fixture_v1.py::run_natural_enter_short_sequence_for_bound_v1`
ENTRY_SHORT_OBSERVED: True
PRE_EXTERNAL_REACHED: True
MAX_BEAR_CONFIRMATION: confirmed:2

## Epochs

```json
[
  {
    "epoch": "origin",
    "decision_outcome": "no_action",
    "BEAR_INPUTS": {
      "closes_tail": [
        1070.0,
        1060.0,
        1050.0,
        1040.0,
        1030.0,
        1020.0,
        1010.0,
        1000.0
      ],
      "closes_len": 64,
      "mark_px": 1630.0,
      "scope_event": "noop",
      "momentum": {
        "rsi": 0.0,
        "roc": -0.38650306748466257
      },
      "mark_price_cmc": 1630.0
    },
    "BEAR": null,
    "BULL": null,
    "BEAR_CANDIDATE": null,
    "CONFIRMATION_BEFORE": null,
    "CONFIRMATION_AFTER": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "observe",
        "distinct": 0
      }
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "neutral_observe",
      "outgoing_cursor": "neutral_observe",
      "transition": {
        "allowed": true,
        "reason_code": "NOOP"
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "no_action",
      "previous_direction_state": "neutral",
      "reason_codes": [
        "no_action"
      ]
    },
    "FINAL_DECISION": "no_action",
    "FINAL_SIDE": "neutral_observe"
  },
  {
    "epoch": "downscope_candidate",
    "decision_outcome": "reduce",
    "BEAR_INPUTS": {
      "closes_tail": [
        1070.0,
        1060.0,
        1050.0,
        1040.0,
        1030.0,
        1020.0,
        1010.0,
        1000.0
      ],
      "closes_len": 64,
      "mark_px": 1000.0,
      "scope_event": "downscope_candidate",
      "momentum": {
        "rsi": 0.0,
        "roc": -0.38650306748466257
      },
      "mark_price_cmc": 1000.0
    },
    "BEAR": {
      "side": "short",
      "status": "candidate",
      "signal_strength": 0.63,
      "confidence": 1.0,
      "thresholds": {
        "observe": 0.001,
        "candidate": 0.005,
        "confirmation": 0.01
      },
      "comparison": {
        "vs_observe": true,
        "vs_candidate": true,
        "vs_confirmation": true
      },
      "reason_codes": [
        "c3_confirmation_progress",
        "ACCEPTED_DISTINCT_PROGRESS",
        "assessment_signal_confirmed",
        "confirmation_state_candidate"
      ],
      "feature_refs": [
        "feat-momentum-v1"
      ]
    },
    "BULL": null,
    "BEAR_CANDIDATE": {
      "side": "SHORT",
      "state": "candidate",
      "signal": 0.63
    },
    "CONFIRMATION_BEFORE": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "observe",
        "distinct": 0
      }
    },
    "CONFIRMATION_AFTER": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "candidate",
        "distinct": 1
      }
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "neutral_observe",
      "outgoing_cursor": "neutral_observe",
      "transition": {
        "allowed": true,
        "reason_code": "CANDIDATE_ACK"
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "reduce",
      "previous_direction_state": "neutral",
      "reason_codes": [
        "adverse_scope_exit",
        "adverse_scope_exit_matched"
      ]
    },
    "FINAL_DECISION": "reduce",
    "FINAL_SIDE": "neutral_observe"
  },
  {
    "epoch": "short_arm",
    "decision_outcome": "reduce",
    "BEAR_INPUTS": {
      "closes_tail": [
        1060.0,
        1050.0,
        1040.0,
        1030.0,
        1020.0,
        1010.0,
        1000.0,
        995.0
      ],
      "closes_len": 65,
      "mark_px": 995.0,
      "scope_event": "downscope_confirmed",
      "momentum": {
        "rsi": 0.0,
        "roc": -0.3895705521472393
      },
      "mark_price_cmc": 995.0
    },
    "BEAR": {
      "side": "short",
      "status": "confirmed",
      "signal_strength": 0.6381909547738693,
      "confidence": 1.0,
      "thresholds": {
        "observe": 0.001,
        "candidate": 0.005,
        "confirmation": 0.01
      },
      "comparison": {
        "vs_observe": true,
        "vs_candidate": true,
        "vs_confirmation": true
      },
      "reason_codes": [
        "c3_confirmation_progress",
        "ACCEPTED_DISTINCT_CONFIRMED",
        "assessment_signal_confirmed",
        "confirmation_state_confirmed"
      ],
      "feature_refs": [
        "feat-momentum-v1"
      ]
    },
    "BULL": null,
    "BEAR_CANDIDATE": {
      "side": "SHORT",
      "state": "confirmed",
      "signal": 0.6381909547738693
    },
    "CONFIRMATION_BEFORE": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "candidate",
        "distinct": 1
      }
    },
    "CONFIRMATION_AFTER": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "confirmed",
        "distinct": 2
      }
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "short_armed_neutral_start",
      "outgoing_cursor": "short_armed_neutral_start",
      "transition": {
        "allowed": true,
        "reason_code": "NEUTRAL_TO_SHORT_ARMED"
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "reduce",
      "previous_direction_state": "short_armed",
      "reason_codes": [
        "adverse_scope_exit",
        "adverse_scope_exit_matched"
      ]
    },
    "FINAL_DECISION": "reduce",
    "FINAL_SIDE": "short_armed_neutral_start"
  },
  {
    "epoch": "enter_short",
    "decision_outcome": "enter_short",
    "BEAR_INPUTS": {
      "closes_tail": [
        1050.0,
        1040.0,
        1030.0,
        1020.0,
        1010.0,
        1000.0,
        995.0,
        990.0
      ],
      "closes_len": 66,
      "mark_px": 990.0,
      "scope_event": "upscope_candidate",
      "momentum": {
        "rsi": 0.0,
        "roc": -0.39263803680981596
      },
      "mark_price_cmc": 990.0
    },
    "BEAR": {
      "side": "short",
      "status": "confirmed",
      "signal_strength": 0.6464646464646465,
      "confidence": 1.0,
      "thresholds": {
        "observe": 0.001,
        "candidate": 0.005,
        "confirmation": 0.01
      },
      "comparison": {
        "vs_observe": true,
        "vs_candidate": true,
        "vs_confirmation": true
      },
      "reason_codes": [
        "c3_confirmation_progress",
        "ACCEPTED_DISTINCT_HOLD_CONFIRMED",
        "assessment_signal_confirmed",
        "confirmation_state_confirmed"
      ],
      "feature_refs": [
        "feat-momentum-v1"
      ]
    },
    "BULL": null,
    "BEAR_CANDIDATE": {
      "side": "SHORT",
      "state": "confirmed",
      "signal": 0.6464646464646465
    },
    "CONFIRMATION_BEFORE": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "confirmed",
        "distinct": 2
      }
    },
    "CONFIRMATION_AFTER": {
      "bull": {
        "state": "observe",
        "distinct": 0
      },
      "bear": {
        "state": "confirmed",
        "distinct": 2
      }
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "short_armed_neutral_start",
      "outgoing_cursor": "short_armed_neutral_start",
      "transition": {
        "allowed": true,
        "reason_code": "CANDIDATE_ACK"
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "enter_short",
      "previous_direction_state": "short_armed",
      "reason_codes": [
        "entry_short_eligible"
      ]
    },
    "FINAL_DECISION": "enter_short",
    "FINAL_SIDE": "SHORT"
  }
]
```

## Enter epoch flat

```json
{
  "BEAR_INPUTS": {
    "closes_tail": [
      1050.0,
      1040.0,
      1030.0,
      1020.0,
      1010.0,
      1000.0,
      995.0,
      990.0
    ],
    "closes_len": 66,
    "mark_px": 990.0,
    "scope_event": "upscope_candidate",
    "momentum": {
      "rsi": 0.0,
      "roc": -0.39263803680981596
    },
    "mark_price_cmc": 990.0
  },
  "BEAR_SIGNAL": 0.6464646464646465,
  "BEAR_THRESHOLDS": {
    "observe": 0.001,
    "candidate": 0.005,
    "confirmation": 0.01
  },
  "BEAR_CANDIDATE": {
    "side": "SHORT",
    "state": "confirmed",
    "signal": 0.6464646464646465
  },
  "CONFIRMATION_BEFORE": {
    "bull": {
      "state": "observe",
      "distinct": 0
    },
    "bear": {
      "state": "confirmed",
      "distinct": 2
    }
  },
  "CONFIRMATION_AFTER": {
    "bull": {
      "state": "observe",
      "distinct": 0
    },
    "bear": {
      "state": "confirmed",
      "distinct": 2
    }
  },
  "SIDESTATE_SWITCH": {
    "next_side_state": "short_armed_neutral_start",
    "outgoing_cursor": "short_armed_neutral_start",
    "transition": {
      "allowed": true,
      "reason_code": "CANDIDATE_ACK"
    }
  },
  "ENTRY_POLICY": {
    "decision_outcome": "enter_short",
    "previous_direction_state": "short_armed",
    "reason_codes": [
      "entry_short_eligible"
    ]
  },
  "FINAL_DECISION": "enter_short",
  "FINAL_SIDE": "SHORT",
  "BULL_ON_SHORT_PATH": null
}
```
