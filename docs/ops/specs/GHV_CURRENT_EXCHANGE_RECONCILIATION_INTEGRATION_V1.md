---
docs_token: DOCS_TOKEN_GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
status: active
scope: Full-Core exchange reconciliation (offline fixtures and injected read-only transport)
capability: GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-16
---

# GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1

Offline-only Full-Core exchange reconciliation after submit boundary. `GHV_AUTHORITY=NONE`.

## Boundary

After: Full-Core capital guard join, atomic reservation, submit transport boundary (simulated offline).

Before: any productive private GET or live POST.

## Provider

`OFFLINE_STUB` uses supplied fixtures. `OKX_EEA_READ_ONLY_GET_V1` uses an explicitly
injected GET transport. `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED`; importing the
adapter does not create a transport, access credentials, or contact the venue.

The injected transport can explicitly exercise up to eight pages per surface
with `offline_max_pages_per_surface`. Pending orders and order history use the
oldest order ID for the next `after` request. Fills use the oldest bill ID.
The adapter requires a fresh, successful response for the same instrument and
a strictly older page with unique IDs. A short page finishes that surface.
A full last page or an unproven cursor leaves reconciliation incomplete.
The pending-orders observation still contains the original first response.
The default and authenticated proof reader continue to use one page per
surface. See [OKX order list](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-list),
[order history](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-history-last-7-days),
and [fills](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-transaction-details-last-3-days).

Local dependency repair on 2026-11-02 restores the adapter and integration from
commit `b48094917d2575e806610cb2d9569bf75929ebc9` (PR #7094), including fail-closed
identity-conflict handling. The post-submit observation stage comes from preserved
stash commit `d70f527fc7351a4941930a256748a2ea8162ab8f`. Existing lifecycle joins now
import successfully; automatic host wiring and productive execution remain unproven.

## Offline replay through post-close feedback

The [post-close regression](../../../tests/ops/test_current_productive_post_close_feedback_v1.py)
replays synthetic OKX responses through the existing GET receipt decoder and
request-order checks. Each receipt carries the exact request with instrument and
`after` cursor, the decision ID, acquisition time, and original fixture body with
its SHA-256. Order-list cursors use `ordId` and fill cursors use `billId`.

The complete case reaches `RECONCILED_FLAT_REVIEWED` with a filled closing order,
matching fill, a fresh scoped zero position and empty pending orders. With the
same fill and zero position, a missing continuation on any of the three surfaces
or an exhausted page budget keeps the result `HALTED_UNRESOLVED` and blocks
post-close feedback. A missing response is a transport failure. A full final
page at the budget limit yields `INCOMPLETE_PAGINATION`. Both retain the original
reservation and produce no ranking review or Double Play continuation.

The authenticated V1 reader and private close readback expect the fixed
single-page request set. The offline V2 close path below extends the ordered
request set with cursor-bound receipts.

## Authenticated close recovery with simulated HTTP

The [authenticated recovery tests](../../../tests/ops/test_execution_reconciliation_get_provenance_v1.py)
verify the GET signatures with fake K1 keys at the HTTP boundary. From the
original synthetic close attempt, the restarted supervisor sees a full first
page in pending orders, order history or fills. For each case, it also sees the
matching closing order and fill and an empty scoped position response. The
single-page reader returns `CLOSE_READBACK_BLOCKED` with
`INCOMPLETE_PAGINATION`. The close proof and settlement booking remain absent
and the original reservation remains held.

The V1 single-page close and settlement receipts replay after reopening the
budget owner. The booking and database bytes match the original and replay makes
no additional GET requests. The booking reader rejects copies with a missing or
extra GET, a wrong cursor or instrument in the query, or reordered GETs. The
copies have consistent file and body digests. Replay validates acquisition
order and the original requests as part of the booking contract.

### Offline V2 close receipt

The L10 close can use a GET transport supplied with an explicit map of test
responses keyed by the exact signed endpoint. This transport signs each request
and reads the response from memory. Its results carry injected provenance. The
ordinary authenticated collectors and the default V1 close reader reject this
offline path. The V2 proof schema is `peaktrade.offline_authenticated_close_get_proof.v2`.

The same bounded cursor traversal runs at capture and during booking readback.
The proof binds each full endpoint, response bytes and SHA-256, acquisition time,
and the decision ID for the original close envelope. Account configuration,
positions, and the exact order lookup retain their positions in the read set.
Replay checks the account, decision IDs, acquisition order, cursor coverage, and
exact consumption of the stored responses. V1 proof files retain their format.

The positive SWAP and FUTURES fixtures put the matching order and fill on
continuation pages and report empty pending orders. A fresh supervisor reopens
the private store and returns the same booking with no additional GET or
database mutation. Missing or foreign pages and a complete response with open
orders all block booking.
The offline booking carries no counter-order request. Live multi-page capture
requires a separate production integration.

## Owners

- Identity + FSM: `full_core_exchange_reconciliation_v1.py`
- Offline fixtures: `full_core_exchange_reconciliation_offline_provider_v1.py`
- Injected GET adapter: `full_core_exchange_reconciliation_okx_read_only_provider_v1.py`
- Handoff: `full_core_exchange_reconciliation_integration_v1.py`
- GHV stages: `ghv_full_core_exchange_reconciliation_observability_v1.py`

## Invariants

`UNKNOWN_REMAINS_UNKNOWN`, no automatic resubmit, no automatic flatten, `POST_COUNT=0`, reconciliation does not reauthorize Owner-GO.

Local post-close feedback extension, 2026-11-03: lifecycle reconciliation can
explicitly forward a typed close request into the existing position, budget and
membership owners. Providers retain the original scoped positions/pending responses.
Successful empty pending plus a chronologically confirmed explicit flat row and
the exact filled closing order are required before review or capital retirement.
Missing position rows remain unknown. The budget refresh requires fresh admissible
Treasury/Q0 capital and the exact committed same-lane reservation set, with replay
protection; no quantity/PnL-to-money arithmetic is added. Ranking review remains a
proposal without assignment persistence. Productive read-only mode rejects these
mutations. Default lifecycle calls and production-provider authorization are unchanged.
