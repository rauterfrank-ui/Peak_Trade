# P43 — CI Ops Scaffold Extend

## Goal
Extend `p41_kickoff_scaffold_v1.sh` so a kickoff can optionally generate common ops helpers:

1) PR Watcher (polls gh pr view/checks, stops on MERGED, writes logs)
2) One-shot Closeout skeleton (main sync + evidence dir + tarball + sha256)
3) Required-contexts snapshot helper (reads branch protection + current PR checks)

## Non-goals
No changes to governance rules. No workflow edits. No trading.

## CLI (proposed)
`./scripts/ops/p41_kickoff_scaffold_v1.sh <pNN> <topic> [--ts TS] [--with-pr-ops]`

When `--with-pr-ops` is set, scaffold adds:
- `scripts/ops/<pNN>_pr_watch.sh`
- `scripts/ops/<pNN>_oneshot_closeout.sh`
- `scripts/ops/<pNN>_required_checks_snapshot.sh`

All scripts:
- bash strict mode
- deterministic evidence paths under `out/ops/`
- safe defaults (no destructive actions unless explicit)

## Tests
Integration test asserts the files are created and `bash -n` passes.
