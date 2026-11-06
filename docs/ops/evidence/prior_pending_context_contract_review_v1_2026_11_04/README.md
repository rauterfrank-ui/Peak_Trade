# Prior Pending context changes: existing field-contract review — 2026-11-04

Pin 2a905d387; Blueprint 75. Owner-requested individual review of earlier changes,
not another patch and not a whole-construction completion claim.

The existing typed DPO field contract explicitly requires the producer's exact
canonical serialized decision payload when available and references a generic
DecisionEvent parent. Capture produces those two records together with common
cycle/correlation/capture time. The generic event enum deliberately does not encode
all DP ENTER semantics; it cannot replace the typed producer observation. Policy
decision identity and generic event record identity have different roles.

85491657b transports the already consumed CMC mark/time/context and actual DP
producer payload through the normal invocation. This has an existing exact-source
contract basis and avoids selecting an unrelated last-ENTER trace. The transported
price is a decision reference mark, not an executed fill price or a proof of fresh
public market data. Existing CMC time semantics are copied, not repaired here.

02b5fa9b3 checks stored DPO and parent via the existing validated owner reader,
then checks present owner/cycle/correlation/time/mapped-enum fields before admitting
context-bound Pending creation. Preserving an explicit False is required to retain
the producer's eligibility meaning. This checks the actual parent relation; it
does not invent policy/input fields absent from the generic event. Legacy calls
without that context keep their earlier contract and are not certified by the gate.

2858f6079 copies actual stored parent correlation and exact producer policy ID into
Pending rather than reconstructing one from naming conventions. Resolver downstream
uses that correlation for evaluation, Learning ingest and export; the old scoped
controlled consumer proof is preserved at its original receipt. These three changes
therefore have an existing source/identity contract basis at the reviewed fields.
They do not imply that all clocks, bars, economic labels, episodes or natural inputs
are mutually equivalent, or that the entire earlier implementation wave is ratified.

No original record migration or blanket reversal is warranted by this inspection.
Pending N_BARS reference-price outcome, simulated filled-position economics and
research experiment scores remain distinct measurement contracts. Whole original
business construction and end-to-end numeric use require further separate proof.

[Sources](sources.json), [assessment and limits](receipt.json). Prior tests were
not rerun. No product change, ledger write, activation, network or authority change;
U04 and GAP-0370 remain deferred.
