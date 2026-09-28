# PRE_LIVE_FRESH_STATE_AND_SLICE_BASELINE_CONVERGENCE_V1

```text
RUNTIME_AUTHORIZATION_EFFECT=PRE_LIVE_MECHANICAL_CONVERGENCE_ONLY
MAP_ATLAS_AUTHORITY=NONE
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Purpose

Mechanically converge the CURRENT Actual-Venue-POST slice baseline pin to live
`origin/main`, mint an isolated fresh Cap-24 productivity root (without
overwriting the stale default auto-read tree), prove fresh-root isolation for
later POST, and stop before Actual-Venue-POST Owner-GO / venue HTTP POST.

## Baseline pin authority

`EXPECTED_BASELINE_ORIGIN_MAIN_SHA` in
`current_productive_actual_venue_post_baseline_v1.py` is a
**VERSIONED_POST_SLICE_MERGE_STABLE_ORIGIN_MAIN_PIN**. It MUST match live
`origin/main` and synchronized `HEAD` before POST-slice mutation.
Legitimate updates occur only via merge-stable closure on `origin/main` (here:
post-#6945 → `1e859eaa79f48308cf7037656c6465191ed9993b`).

Decision JSON baseline fields and admission policy MUST track the module pin
(single runtime source for the constant; policy imports the module).

## Owner-GO

| Token | Effect |
|-------|--------|
| `PRE_LIVE_FRESH_STATE_AND_SLICE_BASELINE_CONVERGENCE_V1` | This WP orchestrator |
| `CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1` | Cap-24 canonical write sub-step only (injected acquisition; no venue I/O) |

Does **not** authorize Actual-Venue-POST, K1 PRE-POST perform, permit mint, or
external effects.

## Fresh roots

Under `runtime&#47;current_productive&#47;pre_live_fresh_cap24&#47;<baseline8>_<ts>&#47;`:

- `cap24_productivity&#47;` — Cap-24 writer output + manifest
- `lane_state&#47;` — reserved for downstream PRE_EXTERNAL / handoff binding
- `post_durable_store&#47;` — reserved for future POST durable artifacts

Historical `first_real_okx_europe_venue_post_*` stores MUST NOT be reused.

## Evidence

Local runs write under
`evidence&#47;ops&#47;pre_live_fresh_state_and_slice_baseline_convergence_v1&#47;<ts>&#47;`
(untracked by default).

```text
BASELINE_ORIGIN_MAIN_SHA=1e859eaa79f48308cf7037656c6465191ed9993b
```
