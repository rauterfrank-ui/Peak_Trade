# MI Realized-Behavior measurement binding — 2026-11-04

Baseline 614a00f8d. Phase-20 origin 6d4de4652, Phase-21 caller continuation
716ac2cf3 (both 2026-09-26). Original specification identifies the N_BARS supplier
as outcome backbone. The consumer formerly checked measurement schema/producer
labels but did not verify measurement content references or complete observation
context before exporting forward-return and derived behavior.

Nine before-cases show acceptance of changed numeric values/reference and foreign
or rehashed instrument, horizon, n_bars and scalar-kind content. The existing
supplier artifact validator already owns the required measurement checks. Its
measurement-only part is now shared as validate_n_bars_measurement_evidence_v1;
the complete measurement/information-set validator still validates both artifacts.
The MI consumer invokes that check before using supplied measurement when the
observation is OK, translating rejection to MEASUREMENT_EVIDENCE_BINDING_INVALID.
No information-set object is fabricated for consumers that do not receive one.

49 direct cases PASS, including all nine formerly failing cases, existing MI
behavior, supplier handoff, N_BARS chain and Pending artifact persistence. Another
17 Loop-A, DP-attribution and Phase-20 governance cases PASS. Full successful
Realized-Behavior output including identity/digest compares identical to the
original function. No return/volatility/excursion formula or output schema changes.

This validates content identity and declared context, not truth of arbitrary
self-consistent newly minted numeric payloads, original external source, all O4
close-path values, classical MFE/MAE, instrument alias equivalence or forecast
label windows. Those remain separate. No natural-run claim, original-ledger
mutation, activation or push. U04/GAP-0370 remain deferred.

G2 followthrough at this revision confirms the previously documented older
adapter still lacks the later required outcome provenance. It already returns
REJECTED. A review verdict does not supply those facts; the adapter and its
historical mapping were retained. The old nine failures were not rerun or
reclassified as fixed. Existing DDO-to-G2 primary-ingress separation is preserved.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[downstream](downstream.xml), [normal comparison](normal_output_comparison.json).
