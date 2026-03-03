# Operating Rhythm (Daily) — Runbook

Ziel
- In <5 Minuten pro Slot prüfen, ob die autonome Pipeline stabil ist.
- Ein einziger lokaler Verdict-Command: ``scripts&#47;ops&#47;ops_status.sh``
- Wenn du einen aktuellen PR-BI Verdict brauchst: PRBI Artifact lokal ziehen, dann `ops_status`.

Grundprinzip
- Kein Live-Trade-Trigger.
- Nur Read/Verify/Download von Artifacts.
- Jede Abweichung => CONTINUE_TESTNET / NO_GO.

## Slot 1 — Morning Check (≤ 5 min)

1) Repo Sync
- `git checkout main && git pull --ff-only origin main`

2) Pull latest artifacts (PR-K dashboard + PR-BI scorecard)
- PR-K: ``scripts&#47;ops&#47;fetch_prk_dashboard_artifacts.sh --limit 1``
- PR-BI: ``scripts&#47;ops&#47;pull_latest_prbi_scorecard.sh``

3) Single verdict
- ``scripts&#47;ops&#47;ops_status.sh``
  - Exit 0: OK (inkl. READY_FOR_LIVE_PILOT wenn aktuell)
  - Exit 2: NO_GO/CONTINUE_* (Gate blockt). Details im Output.

4) If exit != 0
- Nichts "fixen" im Blindflug.
- Erst: Run IDs aus den Artifacts notieren.
- Dann: gezielt Workflow rerun / PR-BG/PR-BI neu dispatchen.

## Slot 2 — Midday Spot Check (≤ 2 min)
- Nur:
  - ``scripts&#47;ops&#47;ops_status.sh``
  - Wenn PRBI fehlt/alt: ``scripts&#47;ops&#47;pull_latest_prbi_scorecard.sh``

## Slot 3 — Evening Close (≤ 5 min)
- Wieder Slot 1.
- Zusätzlich: ``scripts&#47;governance&#47;post_merge_closeout.sh`` falls Merges passiert sind.

## Weekly (15 min)
- ``scripts&#47;ops&#47;ops_status.sh``
- `gh pr list --state open`
- ``scripts&#47;governance&#47;post_merge_closeout.sh``
- Optional: `prbc-stability-gate` & `prbd-live-readiness-scorecard` manuell dispatchen und artifacts ziehen.

## Incident Rules (Hard Stop)
Wenn eines davon auftritt:
- AWS Export Write Smoke fail (prcd)
- Stability gate fail
- Drift detector mismatch
- Exec evidence errors > 0
- Policy critic gate fail

=> Stop, Evidence sichern, Ursache isolieren, erst dann weiter.
