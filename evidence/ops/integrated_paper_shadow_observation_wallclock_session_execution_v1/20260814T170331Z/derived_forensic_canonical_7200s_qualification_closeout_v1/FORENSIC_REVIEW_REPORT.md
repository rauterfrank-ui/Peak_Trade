# EG-I17-SHADOW Canonical 7200s Qualification Closeout

```text
DOCUMENT_CLASS=I17_PRODUCTIVE_SHADOW_CANONICAL_7200S_QUALIFICATION_CLOSEOUT_V1
GENERATED_AT_UTC=2026-08-14T19:08:00Z
AUTHORITY=OWNER_GO_I17_CANONICAL_7200S_CLOSEOUT_ONLY
SYNTHETIC_TERMINAL_VERDICT=false
SYNTHETIC_SEAL=false
RUNTIME_ARTIFACTS_MUTATED=false
```

## 0. Bound identities

```text
SESSION_ID=pso_wallclock_prod_71ebbd4fb8a057504c944bfb8de83fe3
PRIMARY_PID=29215
PROCESS_START_TIME=2026-08-14T17:03:55Z
PROCESS_ENDED_AT=2026-08-14T19:03:57Z
WALLCLOCK_MS=7202714
PLANNED_DURATION_SECONDS=7200
DURATION_CLASS=CANONICAL_QUALIFICATION
EXIT_CODE=0
STATE=TIMED_OUT
ORIGIN_MAIN_SHA=9f09d6d18484e35e788f5e4eaada2c598926b77f
AUTHORIZATION_ARTIFACT_STATE=CONSUMED
SESSION_LOCK_PRESENT=false
```

`TIMED_OUT` is the natural planned-duration end in
`session_runtime_v1` (`now_wall - started_wall >= planned_duration_seconds`).
It is not External Abort, killstate, or harness abort. Harness status=succeeded.

## 1. Reconstruction (existing artifacts only)

- Market-data: 3152 contiguous sequences on ETH-USD_UM_XPERP-310404; receive span 7198.13s inside the 7202.714s wallclock window; max gap 3.23s; gaps>10s=0 (contract max_gap=10s).
- Heartbeats: 1052; `n` contiguous 1..1052.
- Decision cycles: 3152; runtime_events 3152; outcome completeness 3152/3152 unaccounted=0.
- Intents: intent_action=NONE 3152; intended_side=HOLD 3152; intended_quantity=0 3152; safety_blocked=true 3152 (analytical observe-only HOLD, not wallclock killstate).
- Transport: one `transport_opened` host=eea.okx.com. reconnect_events=0. stale_events=0.
- Killstate: killstate_events.jsonl empty; shutdown killstate.active=false.
- Fills: simulated_fills / fill_trace / bridge_fill_ledger all empty.
- Finalize artifacts: all REQUIRED_IMMUTABLE present; evidence_manifest.sha256 verifies; integrity_manifest present; session.lock released.
- Bundle verifier (offline, no mutation): `WALLCLOCK_OBSERVATION_EVIDENCE_VERIFIED` / verdict=PASS / verified=true / blockers=[].
- Authority: session_manifest.authority_effect=NONE; execution_class=ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION; paper_execution=false; GO/artifact orders/live/testnet=false.
- ECONOMIC_VALIDITY_PASS=false and PROMOTION_PASS=false are required non-side-effects of the wallclock verifier (`ECONOMIC_VALIDITY_SIDE_EFFECT_FORBIDDEN` / `PROMOTION_SIDE_EFFECT_FORBIDDEN`). They are **not** I17 qualitative qualification criteria (`I17_CANONICAL_QUALITATIVE_ACCEPTANCE_REQUIREMENTS`).

## 2. Proofs / refutations

| Claim | Verdict | Evidence |
|---|---|---|
| Planned runtime 7200s | PROVEN | prereg/GO/issuance/planned_actual_timestamps all 7200; duration_class=CANONICAL_QUALIFICATION |
| Wallclock >= 7200s | PROVEN | harness elapsed_ms=7202714; EXIT_CODE=0 |
| Natural wallclock end | PROVEN | STATE=TIMED_OUT; incomplete=false; killstate=false; no Traceback; lock released |
| Terminal verdict PASS (runtime-written) | PROVEN | evidence/terminal_verdict.json verdict=PASS incomplete=false; not synthesized in this closeout |
| Integrity/evidence seal | PROVEN | integrity_manifest.json + evidence_manifest.sha256; 0 tamper |
| Bundle verifier PASS | PROVEN | WALLCLOCK_OBSERVATION_EVIDENCE_VERIFIED |
| Contiguous MD / HB / cycles | PROVEN | seq contiguous; HB n=1..1052; cycles 3152/3152 |
| ORDER_EFFECT=NONE | PROVEN | intents NONE/HOLD/0; orders_submitted=0; fills=0 |
| No Canary / Live / Testnet / submit | PROVEN | GO/art flags false; no such processes at start or closeout |
| No unexplained killstate/traceback | PROVEN | killstate empty; harness no Traceback |
| Historical abort reclassified | REFUTED | pso_wallclock_prod_3faa0a7558c6c7851b16459dc1bd7be5 remains OPEN_BLOCKED_WITH_EXACT_REASON |
| Failed start used as qualification | REFUTED | pso_wallclock_prod_4e992d5a604f5f94324ac433a1d9d445 remains NOT_QUALIFICATION |

## 3. Canonical status (confirmed)

```text
EG_I17_SHADOW_STATUS=CLOSED_PROVEN
I17_CANONICAL_CLOSEOUT_STATUS=CLOSED_PROVEN_PASS
PRODUCTIVE_SHADOW_EVIDENCE_PROVEN=true
QUALIFICATION_DURATION_PROVEN=true
ORDER_EFFECT=NONE
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
SUCCESSOR_PHASE_AUTHORIZED=false
RELAUNCH_AUTHORIZED=false
```

This closeout does not authorize Live, Testnet, Canary, orders, economic-validity PASS, promotion, or any successor phase.
Extended soak 21600s remains supported and non-blocking (`I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE=false`).
