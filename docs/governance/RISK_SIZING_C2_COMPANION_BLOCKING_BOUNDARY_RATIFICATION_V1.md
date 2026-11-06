# Risk sizing C2 companion blocking boundary ratification v1

See umbrella: `POST_6828_ARCHITECTURE_CLOSURE_V1.md`.

Machine contract: `config/governance/risk_sizing_c2_companion_blocking_boundary_ratification_v1.json`

C2 here is **Companion Shadow/Live Fraction→Units conversion input authority** (`risk_sizing_c2_input_authority_closure_v1.json`), not Master-V2 directional confirmation C2.

```text
C2_VERDICT=C2_AUTHORITY_RATIFICATION_REQUIRED
C2_STATUS=UNRESOLVED
C2_AUTHORITY_OWNER=UNRESOLVED
C2_BLOCKS_Q0=false
C2_BLOCKS_Q1=false
C2_BLOCKS_TREASURY_ENTER_LIVE=false
C2_BLOCKS_MV2_DP=false
C2_BLOCKS_PRE_EXTERNAL=false
C2_BLOCKS_EXTERNAL_EFFECT=false
```

Resolving Companion C2 still requires a separate Owner decision on conversion handoff and repo-wide `CANONICAL_RISK_SIZING_OWNER` — not invented in this closure.
