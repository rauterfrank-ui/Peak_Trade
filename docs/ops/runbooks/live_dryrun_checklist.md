# Live Dry-Run Checklist

Purpose:
- Verify operational preconditions before any live step.
- This tool performs **NO&#95;TRADE** actions only.

Run (local):
- python3 scripts&#47;ops&#47;live&#95;dryrun&#95;checklist.py --stability reports&#47;status&#47;stability&#95;gate.json --readiness reports&#47;status&#47;live&#95;readiness&#95;scorecard.json

Output (local, untracked):
- out&#47;ops&#47;live&#95;dryrun&#95;checklist&#95;*.md
