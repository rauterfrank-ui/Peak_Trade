# BOUNDED ACCEPTANCE GO / NO-GO SNAPSHOT

## Purpose
Compact decision snapshot for bounded / acceptance: what is allowed now vs what is not allowed now.

## Proven Now
- Real exchange connectivity through the bounded path
- Session-scoped execution-event evidence capture
- Accepted-and-filled bounded outcome under conservative sizing
- Rejected-order evidence path
- Canonical operator path (local secret launcher, runbook)
- Local secret availability without repeated copy-paste
- Governance framing of the bounded milestone
- Closeout consistency via standard + templates

## Allowed Now
- Bounded / acceptance-oriented runs via the canonical operator path
- Local secret launcher as primary launch mechanism
- Shell export + direct bounded pilot as fallback only
- Conservative sizing (e.g. `position_fraction` 0.0005)
- Evidence capture (execution events, live-session report, closeout, handoff)
- Use of acceptance evidence standard and closeout templates
- Reference to canonical accepted-and-filled example for future closeouts

## Not Allowed Now
- Blanket live-trading authorization
- Unrestricted live trading beyond bounded mode
- Weakening of Entry Contract, Go/No-Go, or bounded caps
- Use of live secrets in paper / shadow / testnet paths
- Bypassing the canonical operator path without documented fallback
- Skipping evidence capture for acceptance-oriented runs
- Treating the bounded milestone as open-ended live readiness

## Required Guardrails
- Entry Contract confirmed before entry
- Go/No-Go acceptable (`GO_FOR_NEXT_PHASE_ONLY`)
- Dry Validation completed
- Ops Cockpit reviewed
- `main` clean and synchronized
- No active bounded-pilot processes
- Valid Kraken credentials via approved launcher path
- `PT_EXEC_EVENTS_ENABLED=true`
- Bounded caps / conservative sizing discipline
- Evidence capture mandatory for every acceptance-oriented run

## Residual Risks
- Broader exchange behavior under other market conditions not covered
- Schema / quality drift of execution-event evidence over time
- Operators bypassing preferred path (shell export misuse)
- Local file hygiene for `.bounded_pilot.env` depends on operator discipline
- Repeated human discipline for preflight on every run
- Paper/shadow/testnet isolation: operational mistakes still possible
- Future readers may over-interpret the bounded milestone

## Next Validation Gates
- Before any bounded acceptance run: run preflight checklist
- After each run: use closeout templates for evidence capture
- If more market-condition coverage is needed: run additional bounded reproducibility
- If broader live enablement is desired: separate governance and validation program required

## References
- `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
- `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`
- `docs&#47;ops&#47;reviews&#47;governance_ops_interpretation_of_canonical_acceptance_path&#47;REVIEW.md`
- `docs&#47;ops&#47;reviews&#47;bounded_acceptance_operational_readiness_matrix&#47;REVIEW.md`
