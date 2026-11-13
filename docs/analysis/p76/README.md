# P76 — online-readiness-go-no-go-v1

P76 is retired. Its P71 and P72 dependencies were removed in PR #6580.
The wrapper records `P76_NOT_READY` and exits with status 3. P86 and the
legacy daemon and supervisor also report that their readiness chain is
retired. The supervisor retains its stop interface for existing processes.

For the current bounded preparation and its evidence requirements, see
[Paper and Shadow wallclock preparation](../../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.md).

Entrypoint: `scripts&#47;ops&#47;online_readiness_go_no_go_v1.sh`
