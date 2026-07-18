# Semantic validation

## Method
1. Recover Write/heredoc payloads from Cursor agent transcripts.
2. Re-run probe harnesses in detached temp worktrees at historical SHAs (`a55c4000`) for post-5337 and scope-event packs.
3. Regenerate El Karoui/Armstrong inventories at `43558204` in a temp worktree.
4. Mark unrecovered runtime logs as explicit placeholders (no invented pass/fail).

## Pack outcomes
See `recovery_inventory.tsv`.

## Hard checks
- `bearish_bar_samples.csv` SHA256 unchanged: `3d420d4d90b1f8dd869ab8fee336bf4ed0d1a2f6bb802f9f2199fb3587c941f7`
- `ORIGINAL_BYTES_AVAILABLE=false` for all reconstructed packs
- No productive `src/` / risk / execution / live mutation
- No claim of byte-identity to deleted untracked originals
