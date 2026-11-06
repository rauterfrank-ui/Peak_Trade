# Registry Weekly Digest — Runbook

Ziel
- Wöchentliche Zusammenfassung aus der lokalen DONE-Registry (JSONL).
- Outputs sind **untracked** unter ``out&#47;ops&#47;registry&#47;reports&#47;``.

Inputs
- ``out&#47;ops&#47;registry&#47;morning_one_shot_done_registry.jsonl``

Command
- ``python3 scripts&#47;ops&#47;registry_weekly_digest.py``

Optionen
- `--days 7` (default)
- ``--outdir out&#47;ops&#47;registry&#47;reports``

Outputs
- ``out&#47;ops&#47;registry&#47;reports&#47;weekly_digest_latest.md``
- ``out&#47;ops&#47;registry&#47;reports&#47;weekly_digest_latest.json``
