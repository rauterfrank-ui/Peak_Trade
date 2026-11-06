# CLI Run-Manifest: `run_id` (Forward / Evaluate / Sweep)

Das Feld **`run_id`** in den JSON-Run-Manifesten (`*_run_manifest.json`) ist ein **deterministischer SHA-256-Hex** über: **`script_name`**, **`argv`**, **`config_path`**, **`git_sha`** (sortiertes JSON, dann Hash).

**`generated_at_utc`** steht **nicht** in diesem Hash — es dokumentiert nur den Schreibzeitpunkt; sonst wäre `run_id` bei jedem Lauf anders und nicht als stabiler „Fingerprint“ der Eingaben nutzbar.

Betroffene Einstiege: u. a. `generate_forward_signals.py`, `evaluate_forward_signals.py`, `sweep_parameters.py` (siehe `scripts/_forward_run_manifest.py`).
