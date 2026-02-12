# P4C — L2 Market Outlook Integration (Kickoff)

## Target deliverables
- [ ] L2 runner script: `scripts/aiops/run_l2_market_outlook.py` (existing) + capsule scaffold `scripts/aiops/run_l2_market_outlook_capsule.py`
- [ ] Regime scenarios + NO-TRADE triggers (documented)
- [ ] Evidence pack fixtures (deterministic inputs/outputs)
- [ ] Tests/smoke for runner determinism + schema validation

## Constraints / Guardrails
- Safety-first: runner must be dry-run by default; no live trading effects.
- Deterministic outputs: fixed seeds; stable ordering; explicit versions in metadata.
- Evidence: write to `out&#47;ops&#47;p4c&#47;` only, with timestamped subdirs; include hashes.

## Next concrete steps
1) Define L2 input schema (from L1/L4 operational outputs).
2) Define regime scenario taxonomy + trigger rules (NO-TRADE).
3) Implement runner skeleton that:
   - loads input capsule
   - computes regimes/triggers
   - emits JSON summary + evidence manifest
4) Add minimal pytest smoke + determinism test.
