# Evidence — Token-Policy Scope Clarification (D7 Closeout Follow-up)

Date: 20260120T095910Z
Scope: docs-only evidence slice
Risk: LOW

## Why this exists
A mismatch was observed between the D7 closeout claim and a fresh validator run:
- D7 closeout evidence claimed **0** remaining offenders for “tracked docs”.
- A subsequent `--tracked-docs` run showed remaining offenders in docs&#47;…

This slice records **ground-truth counts per validator mode** and clarifies that `--tracked-docs` may not mean “git-tracked docs&#47;**&#47;*.md == 0” in the way D7 assumed.

## Ground truth (counts derived from report file lists)
- tracked_docs_offender_files (`--tracked-docs`): **0**
- all_docs_offender_files (`--all`, docs&#47;*.md): **0**
- all_non_docs_offender_files (`--all`, src&#47;tests&#47;scripts&#47;…): **0**
- all_total_offender_files (`--all`, total matched): **0**

## Reports captured
- tracked-docs report: `/tmp/pt_token_policy_tracked_docs_20260120T095910Z.txt`
- fullscan report: `/tmp/pt_token_policy_fullscan_all_20260120T095910Z.txt`

## Top offenders (first 25)
### tracked-docs

### all-scan docs

### all-scan non-docs (selected prefixes)


## Next action
If tracked_docs_offender_files > 0:
- define the intended policy target precisely (Gate scope vs git-tracked docs tree),
- then run a new bounded burn-down wave using the correct selection basis.
