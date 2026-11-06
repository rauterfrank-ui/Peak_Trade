# Local implementation phase 4: bounded Exit/cursor publication recovery

Local uncommitted work on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract and remaining transaction limits](../specs/BOUNDED_EXIT_CURSOR_PUBLICATION_RECOVERY_V1.md).

The concrete phase-3 gap is sequential publication without a persisted pair
association: the core commits Exit state and returns a cursor; S7 subsequently
publishes that cursor. Its old file could remain valid after an interruption.
The original cursor owner also wrote by direct truncation. The new association
lives inside the existing Exit state; cursor publication uses the existing cursor
owner with locked replacement/readback and optional expected-prior comparison.

Final connected run: **159 PASS, zero failures/errors/skips**, via `scripts/pt`:

- New pair-recovery and cursor-publication controls: 18.
- Phase-3 explicit episode/Exit continuity: 29.
- Exit restore integrity: 9.
- Existing Exit producer binding: 9.
- Occupied Scope continuity: 11.
- Occupied management dispatch: 25.
- Full-close handoff: 19.
- Existing decision-path atomic restart tests: 7.
- N5 runtime orchestrator: 17.
- Existing one-shot SideState/confirmation cursor join: 15.

The new controls run real current-core decisions on injected offline observations.
For long and short, TimeExit commits an existing Exit obligation before cursor
publication. Faults immediately before and immediately after cursor replacement
exercise both outcomes. A new handle reloads the retained state; an old incoming
cursor is rejected without advancing Exit state. Explicit recovery publishes the
exact retained cursor or acknowledges it as already published. A forbidden-call
guard on the core entry point demonstrates recovery does not invoke that decision
API. A subsequent actual cycle succeeds, retaining the original pending Exit
identity and advancing its sequence once.

Six recovery interventions reject missing, foreign or torn cursor files, wrong
root/account and a stale Exit handle without overwriting current cursor bytes.
Locked cursor CAS rejects a stale publication; a held cursor lock rejects a
simultaneous recovery attempt and permits recovery once released. A real N1
scenario with an injected old file rejects the pair before changing its existing
governed ledger. Four malformed association cases block the core. Serialization
preserves the historical field set when absent and detaches retained dictionaries
so a returned projection cannot mutate the owner record.

An earlier 16-case focused population and 157-case connected population passed
before adding post-replacement interruptions. They are superseded by the final
18/159 populations, not added together. Phase-2's twelve independently reproduced
baseline failures remain separately recorded. No suite-wide claim follows from
these selected passing files.

Runtime isolation, scoped Ruff lint/format and Git whitespace checks pass. The
local phase-4 report retains final JUnit, exact working-file hashes and comparison
to phase 3. No default byte-parity probe was repeated in this phase; the phase-3
controlled parity receipt remains tied to its earlier source hashes. Current
legacy controls verify original serialization shape and existing behavior within
the specified tests, not complete system parity.

The historical Cap 6.4 source/document publication-order discrepancy is retained
as a review finding rather than silently used as a transaction guarantee. That
owner and its original evidence are unchanged. Source/fill authenticity, all-owner
crash consistency, process/power-loss testing and automatic session/N5 recovery
remain open. No Scope/trading formula, config, original ledger or historical
evidence mutation; no credentials, network, orders, capital action, activation,
commit, push or publication.
