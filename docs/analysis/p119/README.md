# P119 — Execution Wiring Plan v1

Goal: networkless provider wiring plan (paper/shadow only), with normalization + error taxonomy + client stubs.

## Dev notes (tests)

- When selecting a *pack directory*, filter for directories only (avoid matching `.bundle.tgz` / `.sha256`).
- `sha256sums_no_xargs_v1.sh` emits repo-root-relative paths; run test dirs *inside the repo* (e.g. `out&#47;ops&#47;_scratch&#47;...`) so paths are not absolute.
