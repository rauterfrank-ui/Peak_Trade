# Stability Gate

Purpose:
- Daily check for recent GitHub Actions evidence on `main`. PR-J must have completed its smoke and evidence upload. PR-K must have fetched real GitHub run data and published a report that names the exact PR-J run. The gate rejects mock reports.
- Both sources expire 36 hours after their original run creation. A manual run keeps its original `workflow_dispatch` event. The receipt identifies such a pair as `ON_DEMAND`. A pair of scheduled runs is marked `SCHEDULED`.
- The readiness scorecards recompute age from the original run timestamps when reading the receipt. Live Readiness checks both PR-K file digests against the gate and enforces an explicit `NO_TRADE` in the PR-K health report.
- The scorecards provide operational evidence. Trading and execution authorization use their own contracts.

Workflow:
- .github&#47;workflows&#47;prbc-stability-gate.yml

Artifacts:
- reports&#47;status&#47;stability&#95;gate.json
- reports&#47;status&#47;stability&#95;gate.md

Manual run:
- gh workflow run prbc-stability-gate.yml --ref main

Local/offline test:
- python3 scripts&#47;ci&#47;stability&#95;gate.py --prk-runs-json &lt;file&gt; --prj-runs-json &lt;file&gt; --now &lt;iso&gt;
