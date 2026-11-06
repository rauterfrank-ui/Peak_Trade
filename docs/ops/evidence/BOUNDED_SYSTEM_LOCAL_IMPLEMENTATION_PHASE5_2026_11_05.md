# Local implementation phase 5: simulated accounting entry source

Local additive source/test work on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Source contract and limits](../specs/BOUNDED_SIMULATED_ACCOUNTING_ENTRY_SOURCE_V1.md).

The phase-3 low-level port accepts caller-declared anchors. This optional adapter
adds an independently replay-checked, retained simulated accounting source for
initial episode creation/reload. It is not real venue authentication. All
previous product sources remain byte-identical to phase 4; only a new adapter,
new tests and additive documentation are introduced.

Final connected run through `scripts/pt`: **42 PASS, no failures/errors/skips**:

- New simulated entry-source controls: 27.
- Existing canonical futures accounting binding controls: 15.

Long and short histories use the original fill model and actual accounting owner:
open 0.3, increase 0.3, reduce 0.2, leaving 0.4. Entry average differs from the
current mark and last reduction fill. The first opening time differs from later
fill times. Source archive/readback and original Exit reload preserve the actual
average/first-open anchors. Real current-core tests reach TimeExit. Additional
long/short N1 scenarios replace only the episode setup with this new adapter;
existing actual N1/S7/Exit/DP/quantity/full-close processing reaches the entire
remaining reduce-only quantity. Existing forbidden-entry-sizing and no-permit/
zero-POST controls remain in those scenarios.

An unknown initial opening time stays unknown despite later known fill times and
does not fabricate TimeExit. Full simulated close rejects an open-episode source;
a subsequent opposite opening receives a distinct key and fresh anchor, leaving
the old context unchanged. This tests explicit new contexts, not automatic
confirmed-flat release of the old context.

Six fill-lineage interventions reject missing/reordered/changed-price/changed-time/
changed-ID/unapplied inputs before source or Exit writes. Four non-simulation modes
reject. Damaged archives remain unchanged and cannot be repaired by creation;
tampered source cannot recover/reanchor an existing episode. Original checkpoint
reload, later mark-to-market, unknown time, invalid time values, wrong opening key
and unsupported funding are checked separately. All verification replays use fresh
original accounting sessions and preserve the supplied session's bytes/projection.

The first focused 15-case run exposed a missing direction argument in one new
test helper call (14 PASS, one setup failure). That fixture call was corrected;
it did not reveal a product defect. Intermediate 23/27-case runs are not added to
the final 42-case population. Scoped lint/format, runtime isolation and Git
whitespace checks pass. Final JUnit and source hashes are retained in the local
phase-5 implementation report.

Phase 4's 159-case receipt is retained with unchanged product/test source hashes;
its suite is not rerun merely to duplicate evidence. Its population is separate
from this run and is not summed into a whole-system certificate. Phase 2's twelve
reproduced baseline failures remain explicitly recorded there.

No Accounting/Scope/trading formula, configuration, original ledger, old source
artifact or earlier evidence is changed. Entry source is simulated and explicitly
caller-bound to account scope, not independently authenticated. Automatic host
source selection, session lifecycle, existing-context average-entry updates,
funding chronology, Decision/fill causal association, real venue origins and
whole-system acceptance remain open. No credentials, network, venue requests,
actual orders, capital actions, activation, commit, push or publication.
