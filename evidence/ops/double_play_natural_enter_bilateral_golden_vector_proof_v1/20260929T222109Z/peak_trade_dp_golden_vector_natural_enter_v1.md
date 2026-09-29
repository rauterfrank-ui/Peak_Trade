# DOUBLE_PLAY_GOLDEN_VECTOR_NATURAL_ENTER_PROOF_V1

generated_at_utc: 2026-09-29T22:13:01Z
BASELINE_SHA: 0688318245043065a32c6b68e072147291993a87
STATUS: GOLDEN_VECTOR_ENTER_PROVEN

## Golden Vector

- SOURCE: `tests&#47;ops&#47;_current_productive_natural_mv2_dp_enter_fixture_v1.py::run_natural_enter_long_sequence_for_governed_pre_external_v1`
- HARNESS: `evidence&#47;ops&#47;double_play_productive_host_e2e_golden_vector_v1&#47;20260929T220100Z&#47;e2e_forensic_harness_v1.py::_forensic_productive_enter_long &#47; contract FORENSIC_PRODUCTIVE_ENTER_LONG`
- EXPECTS_ENTER: True
- EXPECTED_SIDE/DECISION/CONFIRMATION: LONG / enter_long / CONFIRMED
- CURRENT_DECISION/SIDE: enter_long / LONG
- NATURAL_ENTER_PASS: True
- PRE_EXTERNAL_REACHED: True

## Causal epochs

```json
[
  {
    "epoch_label": "origin",
    "decision_outcome": "no_action",
    "INPUTS": {
      "closes_tail": [
        1560.0,
        1570.0,
        1580.0,
        1590.0,
        1600.0,
        1610.0,
        1620.0,
        1630.0
      ],
      "closes_len": 64,
      "mark_px": 1000.0,
      "incoming_side_state": null
    },
    "SCOPE": {
      "event_type": "noop",
      "mark_price": 1000.0,
      "momentum_feature_set": {
        "rsi": 99.9,
        "roc": 0.63
      },
      "runtime_scope_after_anchor": 1000.0
    },
    "BULL": null,
    "BEAR": null,
    "CANDIDATE": {
      "side": null,
      "state": null,
      "reason": "no_candidate"
    },
    "CONFIRMATION": {
      "before": null,
      "after": {
        "bull": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        },
        "bear": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        }
      },
      "epoch": "origin",
      "reset": false
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "neutral_observe",
      "outgoing_cursor_side_state": "neutral_observe",
      "transition_decision": {
        "allowed": true,
        "reason_code": "NOOP",
        "live_authorization_granted": false
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "no_action",
      "previous_direction_state": "neutral",
      "reason_codes": [
        "no_action"
      ]
    },
    "COMPOSITION": {
      "composition_status": "no_action"
    },
    "FINAL_DECISION": "no_action",
    "FINAL_REASON": [
      "no_action"
    ]
  },
  {
    "epoch_label": "upscope_candidate",
    "decision_outcome": "observe",
    "INPUTS": {
      "closes_tail": [
        1560.0,
        1570.0,
        1580.0,
        1590.0,
        1600.0,
        1610.0,
        1620.0,
        1630.0
      ],
      "closes_len": 64,
      "mark_px": 1630.0,
      "incoming_side_state": null
    },
    "SCOPE": {
      "event_type": "upscope_candidate",
      "mark_price": 1630.0,
      "momentum_feature_set": {
        "rsi": 99.9,
        "roc": 0.63
      },
      "runtime_scope_after_anchor": 1000.0
    },
    "BULL": {
      "side": "long",
      "status": "candidate",
      "signal_strength": 0.38650306748466257,
      "confidence": 1.0,
      "operands": {
        "signal_strength": 0.38650306748466257,
        "feature_refs": [
          "feat-momentum-v1"
        ],
        "reason_codes": [
          "c3_confirmation_progress",
          "ACCEPTED_DISTINCT_PROGRESS",
          "assessment_signal_confirmed",
          "confirmation_state_candidate"
        ]
      },
      "thresholds": {
        "observe": 0.001,
        "candidate": 0.005,
        "confirmation": 0.01
      },
      "comparison": {
        "signal_vs_observe": true,
        "signal_vs_candidate": true,
        "signal_vs_confirmation": true,
        "result_status": "candidate"
      }
    },
    "BEAR": null,
    "CANDIDATE": {
      "side": "LONG",
      "state": "candidate",
      "reason": "bull_status=candidate signal=0.38650306748466257"
    },
    "CONFIRMATION": {
      "before": {
        "bull": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        },
        "bear": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        }
      },
      "after": {
        "bull": {
          "assessment_state": "candidate",
          "distinct_count": 1,
          "latest_epoch": "MarketObservationEpoch(value=2)"
        },
        "bear": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        }
      },
      "epoch": "upscope_candidate",
      "reset": false
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "neutral_observe",
      "outgoing_cursor_side_state": "neutral_observe",
      "transition_decision": {
        "allowed": true,
        "reason_code": "CANDIDATE_ACK",
        "live_authorization_granted": false
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "observe",
      "previous_direction_state": "neutral",
      "reason_codes": [
        "observe_only"
      ]
    },
    "COMPOSITION": {
      "composition_status": "observe"
    },
    "FINAL_DECISION": "observe",
    "FINAL_REASON": [
      "observe_only"
    ]
  },
  {
    "epoch_label": "enter",
    "decision_outcome": "enter_long",
    "INPUTS": {
      "closes_tail": [
        1570.0,
        1580.0,
        1590.0,
        1600.0,
        1610.0,
        1620.0,
        1630.0,
        1635.0
      ],
      "closes_len": 65,
      "mark_px": 1635.0,
      "incoming_side_state": null
    },
    "SCOPE": {
      "event_type": "upscope_confirmed",
      "mark_price": 1635.0,
      "momentum_feature_set": {
        "rsi": 99.9,
        "roc": 0.635
      },
      "runtime_scope_after_anchor": 1000.0
    },
    "BULL": {
      "side": "long",
      "status": "confirmed",
      "signal_strength": 0.38837920489296635,
      "confidence": 1.0,
      "operands": {
        "signal_strength": 0.38837920489296635,
        "feature_refs": [
          "feat-momentum-v1"
        ],
        "reason_codes": [
          "c3_confirmation_progress",
          "ACCEPTED_DISTINCT_CONFIRMED",
          "assessment_signal_confirmed",
          "confirmation_state_confirmed"
        ]
      },
      "thresholds": {
        "observe": 0.001,
        "candidate": 0.005,
        "confirmation": 0.01
      },
      "comparison": {
        "signal_vs_observe": true,
        "signal_vs_candidate": true,
        "signal_vs_confirmation": true,
        "result_status": "confirmed"
      }
    },
    "BEAR": null,
    "CANDIDATE": {
      "side": "LONG",
      "state": "confirmed",
      "reason": "bull_status=confirmed signal=0.38837920489296635"
    },
    "CONFIRMATION": {
      "before": {
        "bull": {
          "assessment_state": "candidate",
          "distinct_count": 1,
          "latest_epoch": "MarketObservationEpoch(value=2)"
        },
        "bear": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        }
      },
      "after": {
        "bull": {
          "assessment_state": "confirmed",
          "distinct_count": 2,
          "latest_epoch": "MarketObservationEpoch(value=3)"
        },
        "bear": {
          "assessment_state": "observe",
          "distinct_count": 0,
          "latest_epoch": "MarketObservationEpoch(value=0)"
        }
      },
      "epoch": "enter",
      "reset": false
    },
    "SIDESTATE_SWITCH": {
      "next_side_state": "long_armed_neutral_start",
      "outgoing_cursor_side_state": "long_armed_neutral_start",
      "transition_decision": {
        "allowed": true,
        "reason_code": "NEUTRAL_TO_LONG_ARMED",
        "live_authorization_granted": false
      }
    },
    "ENTRY_POLICY": {
      "decision_outcome": "enter_long",
      "previous_direction_state": "long_armed",
      "reason_codes": [
        "entry_long_eligible"
      ]
    },
    "COMPOSITION": {
      "composition_status": "long_selected"
    },
    "FINAL_DECISION": "enter_long",
    "FINAL_REASON": [
      "entry_long_eligible"
    ]
  }
]
```

## Live wiring

```json
{
  "fresh_live_get_performed": true,
  "live_selected_future": "0G-USDT-SWAP",
  "live_bound_instrument": "0G-USDT-SWAP",
  "live_to_dp_boundary_reached": true,
  "dp_required_fields_present": true,
  "dp_input_schema_match": true,
  "dp_input_provenance_valid": true,
  "get_count": 4,
  "post_count": 0,
  "path": "acquire_eea_universe_inventory_v1 \u2192 run_cap21_to_cap23_persist_productive_v1 \u2192 run_single_selected_future_runtime_binding_gate_v1",
  "error": null,
  "golden_dp_fields_reference": {
    "mark_price": true,
    "momentum_feature_set": true,
    "instrument_id": true,
    "price_path_closes": true,
    "side_state_cursor": true,
    "confirmation_carrier": true,
    "runtime_scope_state": true,
    "typed_vol_joined_via_g17": true
  },
  "acquisition_ok": true,
  "acquisition_provenance": {
    "ACQUISITION_OWNER": "CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_ACQUISITION_V1",
    "HOST": "eea.okx.com",
    "VENUE": "okx_eea",
    "SOURCE_KIND": "okx_eea_public_instruments",
    "NETWORK_METHODS": [
      "GET",
      "GET",
      "GET",
      "GET"
    ],
    "ENDPOINTS": [
      "/api/v5/public/instruments?instType=FUTURES",
      "/api/v5/public/mark-price?instType=FUTURES",
      "/api/v5/public/instruments?instType=SWAP",
      "/api/v5/public/mark-price?instType=SWAP"
    ],
    "POST_COUNT": "0",
    "INST_TYPES": [
      "FUTURES",
      "SWAP"
    ],
    "INSTID_FORCED": false,
    "CREDENTIALS_USED": false,
    "CAP21_NETWORK_OWNER": false,
    "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": false,
    "INSTRUMENTS_DIGEST": "f68fc3e1c24c56b9e170a63b6883e3db19aefd3a422060f2ae1b163a389a8cf8",
    "MARK_PRICE_DIGEST": "44512e5e28e9355435e242cec66c937c99a6c1141a85b58ffacce1d5947291b7",
    "INSTRUMENT_ROW_COUNT": 743,
    "MARK_PRICE_ROW_COUNT": 743,
    "VENUE_LIVE_CONTACT": true,
    "FAILURE_CODES": [],
    "SOFT_FAILURE_CODES": []
  },
  "endpoints_used": [
    "/api/v5/public/instruments?instType=FUTURES",
    "/api/v5/public/mark-price?instType=FUTURES",
    "/api/v5/public/instruments?instType=SWAP",
    "/api/v5/public/mark-price?instType=SWAP"
  ],
  "cap21_23_ok": true,
  "cap21_23_status": "PASS",
  "binding_ok": true,
  "bound_canonical_instrument_id": "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
  "live_mark_price": "0.3289",
  "live_mark_map_size": 743,
  "live_fields": {
    "mark_price": true,
    "momentum_feature_set": false,
    "instrument_id": true,
    "price_path_closes": false,
    "side_state_cursor": false,
    "confirmation_carrier": false,
    "runtime_scope_state": false,
    "typed_vol_joined_via_g17": false,
    "venue_instrument_id": true,
    "acquisition_provenance": true,
    "selection_present": true,
    "binding_present": true
  },
  "note": "Live proves Cap24 identity+mark provenance into DP host boundary; golden vector CMC feature values are deterministic fixtures and must not be substituted."
}
```

## Final

- FIRST_DIVERGENT_STAGE/FIELD: NONE / NONE
- LIVE_SELECTED/BOUND: 0G-USDT-SWAP / 0G-USDT-SWAP
- LIVE_TO_DP_BOUNDARY_REACHED: True
- DP_REQUIRED_FIELDS_PRESENT: True
- DP_INPUT_SCHEMA_MATCH: True
- DP_INPUT_PROVENANCE_VALID: True
- GET_COUNT/POST_COUNT: 4 / 0
- NEXT_MINIMAL_ACTION: Deterministic Natural-Enter intact; live Cap24→DP identity/mark boundary populated. Optional next: Owner-GO bounded PRE_EXTERNAL continuous Fresh-C1 cycle (no POST) — do not wait for live-market ENTER.
