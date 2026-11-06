# Closeout Index (JSONL)

Tracked file:
- out&#47;ops&#47;index_post_merge_closeouts.jsonl

Contract:
- Append-only JSON Lines (one JSON object per line)
- Required keys:
  - timestamp (UTC ISO8601, Z)
  - kind
  - evidence_dir
  - head (short git sha)
  - notes (string, may be empty)

Helper:
- scripts&#47;ops&#47;append_closeout_index.py

Usage:
- PT_EVIDENCE_DIR=out&#47;ops&#47;some_evidence_dir PT_CLOSEOUT_KIND=PRK_CLOSEOUT PT_CLOSEOUT_NOTES="..." python3 scripts&#47;ops&#47;append_closeout_index.py

Test:
- tests&#47;ops&#47;test_append_closeout_index_contract.py
