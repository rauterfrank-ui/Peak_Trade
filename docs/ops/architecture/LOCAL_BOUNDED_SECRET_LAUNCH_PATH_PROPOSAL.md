# LOCAL BOUNDED SECRET LAUNCH PATH PROPOSAL

## Goal
Design a local secret-launch path for bounded/acceptance runs that:
- removes repeated manual secret copy-paste
- preserves strict gates
- keeps paper/shadow isolated
- preserves evidence and audit trail

## Current State
- bounded/acceptance runs currently rely on secrets being exported in a manually opened terminal
- terminal-scoped env works, but is fragile and disappears when the shell is closed
- bounded-pilot acceptance path is now proven with real exchange acceptance/fill
- execution-event evidence is working for both rejected and accepted paths
- preflight and acceptance closeout docs already exist on `main`

## Constraints
- no global secret auto-load into paper/shadow/testnet paths
- no git-tracked secret material
- no weakening of Entry Contract / Go-No-Go / Ops Cockpit / evidence gates
- no loss of session-scoped execution-event evidence
- local developer/operator ergonomics should improve without bypassing controls

## Threat Model
Primary risks:
1. live secrets become available to the wrong mode
2. bounded/acceptance launcher bypasses gates
3. secrets exist but evidence/audit trail is weaker than before
4. terminal/session loss causes confusing partial state
5. operator uses wrong launcher and accidentally runs paper/shadow with live env
6. secret source is present but unreadable / stale / misconfigured
7. background services auto-load secrets outside explicit operator intent

## Design Principle
Secret availability must become more reliable, but launch authorization must remain explicit and gated.

## Secret Source Options

### Option A — Manual Terminal Export
Description:
- operator exports `KRAKEN_API_KEY` and `KRAKEN_API_SECRET` in an interactive terminal before launch

Pros:
- simple
- already proven

Cons:
- fragile
- repeated copy-paste
- lost on shell close
- not scalable for consistent operator workflow

### Option B — Local Non-Git Env File Loaded Only By Explicit Launcher
Description:
- secrets live in a local ignored file such as a dedicated bounded-launch env file
- only a dedicated bounded/acceptance launcher reads that file

Pros:
- simple local ergonomics
- easy to audit launcher behavior
- avoids repeated copy-paste
- can keep paper/shadow isolated if only the dedicated launcher loads it

Cons:
- requires disciplined file permissions and ignore rules
- still file-based secret storage on disk

### Option C — macOS Keychain / OS Secret Store
Description:
- dedicated launcher resolves secrets from macOS Keychain at runtime

Pros:
- stronger local secret hygiene
- no plaintext env file required
- good fit for local operator-driven launches

Cons:
- more implementation complexity
- requires reliable retrieval tooling and error handling

### Option D — Background Service / LaunchAgent Injects Secrets
Description:
- background local service injects live secrets for relevant runs

Pros:
- high convenience

Cons:
- highest risk of accidental mode bleed
- easiest way to contaminate paper/shadow boundaries
- not recommended for first rollout

## Recommended Secret Source
Recommended phased approach:
- Phase 1: Option B
- Phase 2: optionally evolve to Option C

Rationale:
- Option B gives immediate usability gains with low implementation cost
- secret loading can remain explicit and launcher-scoped
- paper/shadow isolation is easier to enforce than with background injection
- later migration to Keychain can happen after launcher boundaries are stable

## Launcher / Wrapper Design

### Explicit Local Launcher
Proposed dedicated entrypoint:
- proposed dedicated bounded launcher script (not yet implemented)
- for example: `scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py`
- or a shell wrapper with equivalent behavior

Responsibilities:
1. load secrets only from the approved local source
2. export only the minimum required vars into the child process
3. set `PT_EXEC_EVENTS_ENABLED=true` when evidence is required
4. call existing bounded-pilot wrapper
5. preserve existing session/report/evidence outputs
6. fail closed if secret source is missing or unreadable

### Required Non-Goals
The launcher must not:
- auto-load secrets for paper/shadow/testnet runs
- silently bypass Go/No-Go or Entry Contract checks
- start background services
- mutate governance state

## Mode Separation
Required hard boundary:
- paper/shadow/testnet/live-adjacent tooling must never auto-read the bounded secret source
- only the explicit bounded/acceptance launcher may read it

Recommended implementation rules:
- dedicate a file name and path clearly scoped to bounded/acceptance only
- never source that file from shell startup scripts
- never let generic wrappers load it
- require an explicit bounded/acceptance command to use it

## Gate Integration
The launcher must still route through the existing bounded path:
- preflight checklist
- `run_bounded_pilot_session.py`
- Entry Contract
- Go/No-Go evaluation
- Ops Cockpit / evidence / dependencies checks

Secret presence must not become authorization.
Secret loading is prerequisite plumbing only.

## Evidence / Audit Integration
The launcher must preserve existing evidence behavior:
- session-scoped execution events
- live-session report
- closeout docs and handoffs
- clear operator-visible run mode and path

Recommended additions:
- write a launcher note into stdout/stderr indicating:
  - bounded local secret source used
  - mode intended
  - evidence mode intended
- do not print secrets or secret-derived values

## Failure Modes and Expected Behavior
1. Secret source missing
   - fail closed
   - do not launch bounded session

2. Secret source present but incomplete
   - fail closed
   - report which variable names are missing without revealing values

3. Attempt to run non-bounded mode through bounded secret launcher
   - deny by design

4. Evidence flag missing when acceptance evidence is expected
   - fail closed or force explicit operator acknowledgement

5. Gates red
   - launch aborts after normal bounded checks
   - no secret success path bypass

6. Shell closed after launcher start
   - running child process may continue normally if intended
   - launcher should not be required to remain interactive for evidence integrity

## Recommended Phased Rollout
### Phase 1
- docs-only proposal
- choose local secret source
- define exact launcher contract
- define ignore/file-permission expectations

### Phase 2
- implement explicit bounded/acceptance local secret launcher
- add tests proving no paper/shadow bleed
- add operator runbook for the launcher

### Phase 3
- optional Keychain-based secret retrieval
- keep explicit launcher boundary unchanged

## Recommendation
Proceed with:
1. docs proposal completion
2. implement explicit local bounded secret launcher using a local non-git env source
3. add safety tests for mode isolation
4. add operator runbook
5. later evaluate Keychain as an implementation refinement
