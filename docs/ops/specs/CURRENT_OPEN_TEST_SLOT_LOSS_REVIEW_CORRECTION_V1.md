# Open test-slot protection: writer and price-boundary correction

`RUNTIME_AUTHORIZATION_EFFECT=NONE`

This correction follows the two review findings on PR #7208. Its merge
`353268855922f438200bf649a17af7ec94241455` contains the cost/funding and open-slot
protection commits. The required checks passed, but two active review threads
were overlooked at merge. Their fixes are separate from that dated baseline.

## Original owner availability

A closed budget owner, an already failed storage writer, or a missing original
store raises `PortfolioCapitalBudgetError`. The existing N1 owner-error branch
propagates it before Core continues. Missing optional valuation remains a
different condition: it retains the original exit rules and any durable close
request. No hold is released by an unavailable writer.

## Price representation

N1/Core already consumes a float mark. The owner compares the observation mark's
float projection with that same cycle representation, exactly and only when
both projections are finite and positive. No numerical tolerance is added.
The original full Decimal mark remains in the proof and original accounting
valuation. A different representable cycle price is still rejected.

## Verification and limits

Five new connected N1 regressions cover the three unavailable-writer states,
a higher-precision Decimal mark sharing the original float projection, and a
genuinely different mark. Existing open-slot LONG/SHORT, source, persistence,
recovery, and original budget tests provide the scoped regression coverage.

The correction changes only the budget owner's exception and price comparison;
the exact N1/S7 adapter bundle, native Core, recovery implementations, operative
policy and freeze tags remain unchanged. BWP1 remains in progress: ongoing
renewal of funding/cost obligations, full margin/liquidation admission and the
complete financial-framework connection remain open. Simulated tests confer no
live, testnet, order or capital authority.
