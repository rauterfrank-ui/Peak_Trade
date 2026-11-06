# Local implementation phase 6: explicit offline episode session

Local additive work on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract and precise scope](../specs/BOUNDED_OFFLINE_EPISODE_SESSION_V1.md).
Existing product/test sources from phase 5 remain unchanged; the new composition
package, two test files and additive documentation supply this profile.

Final connected validation through `scripts/pt`: **71 PASS, zero failures,
errors or skips**:

- New session/manifest/root controls: 26.
- Applied simulated-accounting source controls: 27.
- Exit/cursor retained-publication recovery controls: 18.

The two positive session controls run actual long/short N1/S7/Exit/DP/full-close
processing with retained accounting sources, leaving no permit/POST. The session
closes and explicitly recovers the same owners; its exhausted one-attempt allowance
remains exhausted even with a new cycle prefix. Calling after close rejects.
The producer/core/quantity owners execute; no mock decision or order result is
substituted in these two positive consumer paths.

Manifest interventions reject non-simulation scope, count above the existing
MaxPos, boolean bound, overlapping roots, conflicting account and malformed implementation
digest before session creation. JSON input rejects unknown signing capability and
duplicate keys. Eight named per-attempt controls reject changed source, disk code
binding, owner override, origin pin, replay bounds, lane generation, receipt and
manifest before charging an attempt or reaching the governed owner. Their final
assertions match the exact intended rejection reason; a forbidden-call spy guards
that technical negative boundary.

Cooperative-lease conflict blocks another live session on the same owner roots.
Persistent registrations additionally block a second session root after leases
are released, with either the same or a different session ID; the original root
still recovers. Budget edits, absent receipt, bool count and `RUNNING` receipt
cannot be recreated, renewed or automatically resumed.

A separate disposable worker launched with the canonical `scripts/pt` is killed
with SIGKILL after the durable charge, immediately before a test-only stand-in
for the real N1 call. The original numeric owner JSON files remain unchanged.
The parent can reacquire all three OS leases; the retained `RUNNING` receipt still
contains its spent attempt/prefix and startup rejects automatic replay. This is
physical process-death evidence for that technical checkpoint only. It does not
prove death/recovery within a real N1 decision or any shared financial transaction.
The worker is a bounded test subprocess, not a started host or service.

Earlier 19/23/24/26 focused and 68/69 connected populations are superseded by the
final 26/71 population, not summed. Review found that initial broad exception
assertions could let several negative cases pass on missing request arguments.
Those controls were strengthened to reach and match their specific preflight
reasons before final acceptance. No product guard was weakened. The original
unattended host's different physical-restart tests were read as pattern evidence,
not imported as proof for this new root.

Runtime isolation, scoped Ruff lint/format, whitespace and final source/report
readback pass. Local phase-6 report retains JUnit, source hashes, actual checkout
binding and comparison to phase 5. Earlier receipts and separately reproduced
phase-2 baseline failures remain preserved. No new whole-system certificate or
default-path byte-parity claim follows.

Source authentication, dynamic entry updates, lifecycle release, all-five-slot
composition and all-owner recovery remain open. Scope/Accounting/trading formulas,
configuration, original ledgers and historical evidence remain untouched. No
credentials, network requests, venue sessions, actual orders, capital action,
activation, service installation, commit, push or publication.
