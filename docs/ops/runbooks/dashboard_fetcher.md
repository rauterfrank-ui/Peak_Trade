# Dashboard Fetcher (PR-K Artifacts)

Goal:
- Download the latest successful PR-K artifact bundle and extract dashboard inputs locally (no services, no Grafana).

Script:
- scripts&#47;ops&#47;fetch&#95;prk&#95;dashboard&#95;artifacts.sh

Outputs (local, untracked):
- out&#47;ops&#47;prk&#95;dashboard&#95;latest&#47;latest&#47;
  - prj&#95;status&#95;latest.json / .md
  - prj&#95;health&#95;summary.json / .md
  - prj&#95;health&#95;dashboard.txt / .csv
  - prj&#95;health&#95;dashboard&#95;v1.json (if present)

Examples:
- scripts&#47;ops&#47;fetch&#95;prk&#95;dashboard&#95;artifacts.sh
- scripts&#47;ops&#47;fetch&#95;prk&#95;dashboard&#95;artifacts.sh --run-id 1234567890
- scripts&#47;ops&#47;fetch&#95;prk&#95;dashboard&#95;artifacts.sh --out-dir out&#47;ops&#47;prk&#95;dash&#95;custom

Notes:
- Requires GitHub CLI auth (gh).
- Writes only to out&#47; (ignored).
