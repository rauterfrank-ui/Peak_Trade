# Stash Export References

Dieses Verzeichnis enthält exportierte Git-Stashes als Referenz.

## Struktur

Jeder Export besteht aus:
- `stash_ref_<timestamp>_<idx>.patch` — Git Patch (git stash show -p)
- `stash_ref_<timestamp>_<idx>.md` — Metadata (Ref, Message, Diffstat, Files)

## Verwendung

Siehe `scripts/ops/stash_triage.sh --help` für Details.
