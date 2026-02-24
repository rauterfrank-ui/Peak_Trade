# Stability Gate

Purpose:
- Quick daily check that PR-J and PR-K scheduled pipelines are healthy (fresh schedule success within threshold).
- Produces artifacts only (no dashboards, no services).

Workflow:
- .github&#47;workflows&#47;prbc-stability-gate.yml

Artifacts:
- reports&#47;status&#47;stability&#95;gate.json
- reports&#47;status&#47;stability&#95;gate.md

Manual run:
- gh workflow run prbc-stability-gate.yml --ref main

Local/offline test:
- python3 scripts&#47;ci&#47;stability&#95;gate.py --prk-runs-json &lt;file&gt; --prj-runs-json &lt;file&gt; --now &lt;iso&gt;
