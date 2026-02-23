# ops_status

Local operator one-shot checks for:
- PR-K generators + tests
- PR-U drift detector
- YAML parse sanity for PR-K/PR-O workflows

Run:
- scripts&#47;ops&#47;ops_status.sh

## Related runbooks

- **Operating rhythm**: Daily/weekly cadence and incident playbooks — see `operating_rhythm.md`
- **Required checks deadlocks**: When required checks are "Expected" but never start, see `required_checks_deadlocks.md` and use `scripts&#47;ops&#47;ci_trigger_required_checks.sh`.
