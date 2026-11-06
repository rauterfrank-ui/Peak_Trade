# Prior MI measurement checks versus original Phase20 construction — 2026-11-04

Pin e3edad282; Blueprint 76. Individual read-only review, no new guard or algorithm.
The complete original Sep26 17:03 Phase20 request has been read and preserved.
It requires canonical N_BARS ownership, explicit start/end observations and price
semantics, an exact future interval through t+N, finalization, provenance and
replay. It explicitly does not require a forecast to create realized behavior,
allows unresolved transition/classical MFE/MAE semantics and forbids inventing
missing families, thresholds or a new Learning writer for the following phase.

614a00f8d compares the forecast's explicit target end with the existing outcome
helper's last canonical bar close. Target time is not the later time when the
result becomes known. An equal n_bars count and bar-spec token alone cannot prove
an equal target interval. The check is supported as an interval consistency
constraint; it is not a complete forecast/context/decision/instrument association
proof, and it does not make forecast mandatory for Phase20 behavior production.

28515d969 makes the MI consumer reuse supplier-owned measurement validation:
content-bound actual_outcome_ref, schema/bridge/producer, instrument/bar spec,
horizon/count, close times/bar identities, scalar kind and evaluation time must
agree with the observation. The full supplier pair validator additionally checks
its information-set artifact; the measurement-only consumer does not invent that
missing artifact. This supports the original provenance/no-second-outcome-owner
requirement, not an external-source authenticity claim or new return formula.

5dcc84a9c orders O4 closes by the observation's existing identities, rejects
ambiguous duplicate identities and requires supplied path endpoints to match the
bound measurement endpoints. Original interval/explicit start/end requirements
support these consistency constraints. They neither authenticate intermediate
closes nor establish a complete historic price path. A self-consistent digest is
not proof all underlying prices were observed. Preserve strongest supported
close-path excursion; do not label it classical trade-direction MFE/MAE.

Decision reference marks, measurement-specific start/end bar closes, executed
fills and realized position PnL have different meanings. The original request
forbids generic close substitution where canonical mark semantics apply; this
review does not globally equate those contracts or certify every price-basis
supplier. New caller binding/adapter work must keep the source owner's explicit
basis and horizon rather than silently switch it for convenience.

These three changes have original invariant/owner-contract support at the stated
fields; full historical episode and natural numeric effect are not ratified.
No blanket reversal or certification of the remaining earlier wave follows.
[Original request](historical_phase20_request.json), [sources](sources.json),
[assessment/limits](receipt.json). Earlier tests were not rerun. No code change,
original-ledger write, operations, source/freshness work or authority expansion.
