# P5B — Evidence Pack Automation Kickoff

## Source
- Runbook: docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026.md
- Extract: out/ops/next_phase_after_p5a_20260211_113337/NEXT_PHASE_SECTION.txt

## Deliverables (paste from runbook)
- Evidence Pack Generator CLI (`scripts/aiops/generate_evidence_pack.py`)
  - Auto-populate: run_id, model_id, timestamp, git_ref
  - Template selection: layer-specific templates
  - Validation on save (exit code 1 if invalid)
- Integrate Evidence Pack Validator into CI workflow
- Add Evidence Index auto-update script (append new entries)
- Operator Cheatsheet for Evidence Pack CLI

## Guardrails
- Safety-first, dry-run by default
- Deterministic evidence under out&#47;ops&#47;p5b&#47;

## Next steps
- [ ] Confirm inputs/outputs + schema versions
- [ ] Implement minimal scaffolding + tests
- [ ] PR via scripts&#47;ops&#47;pr_safe_flow.sh
