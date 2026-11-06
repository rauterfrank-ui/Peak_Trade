# MI close-path identity and measurement endpoints — 2026-11-04

Baseline 28515d969. Continues the existing Phase-20/21 consumer construction.
O4 identity binds instrument, interval, open time and revision; it does not bind
close value. The consumer formerly built a dictionary that silently overwrote
duplicate identities and used path endpoints without comparing the already bound
measurement prices. Four pre-fix cases demonstrate accepted conflicting endpoints
and duplicate identities, including identical duplicates.

Duplicate O4 identities now reject as O4_BAR_IDENTITY_DUPLICATE. When both an OK
observation's bound measurement and O4 path are supplied, the closes ordered by
canonical observation bar refs must have matching first/last measurement prices;
otherwise O4_MEASUREMENT_ENDPOINT_PRICE_MISMATCH. Supplied list order is not time
or identity order. No new bar revision, price, measurement or volatility formula.

Five new cases and 38 connected cases PASS; four initial failures preserved.
Full valid behavior output/digest compares identical with baseline. Reversed input
order yields the same full result. Existing Loop-A and DP-attribution tests pass.

This does not authenticate all interior closes or solve the canonical source/
full payload-content binding. Equal endpoints cannot prove equal interior paths.
Unknown classical MFE/MAE and forecast label windows remain separate. No natural
source/run claim, original-ledger mutation, activation or push; U04/GAP-0370 deferred.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[normal comparison](normal_output_comparison.json).
