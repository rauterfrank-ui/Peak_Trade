# N=1 Standing PRE_EXTERNAL Runtime Supervisor V1

**Authority:** orchestration/liveness only — `SUPERVISOR_ZERO_ECONOMIC_AUTHORITY=true`  
**POST:** forbidden (`POST_ALLOWED=false`, `EXTERNAL_EFFECT_AUTHORIZED=false`)

## Canonical entry point

```bash
./scripts/ops/run_n1_standing_pre_external_runtime_supervisor_v1.py --help
```

Production/scoped runs require:

- Durable store roots (public, private, lane state, evidence)
- Valid `config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json` for the pinned baseline lineage
- Consumed Owner-GO evidence written under the evidence root (supervisor delegates to existing persistent natural-enter wiring)
- Read-only transport scope explicitly configured (no credential auto-discovery)

The launcher performs **one supervisor session** (recovery → public refresh → pretrade refresh → policy-governed continuous run). It does not activate POST or flip `CONTINUOUS_RUN_AUTHORIZED`.

## WP-02 seam (CURRENT-WP-02 closed)

When `StandingSupervisorConfigV1.wp02_productive_default_enabled=true` (default) and
universe inject payloads are configured, the supervisor invokes
`build_default_wp02_hook_v1` → `run_wp02_productive_default_chain_v1` (Cap21 → real B05
→ Cap22 → hard-facts handoff). Set `wp02_productive_default_enabled=false` for explicit
no-op. See `docs/ops/specs/CURRENT_WP02_DEFAULT_PRODUCTIVE_UNIVERSE_HANDOFF_V1.md`.
