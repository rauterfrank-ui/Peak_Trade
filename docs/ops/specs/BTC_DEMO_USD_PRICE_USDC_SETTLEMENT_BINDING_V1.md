---
docs_token: DOCS_TOKEN_BTC_DEMO_USD_PRICE_USDC_SETTLEMENT_BINDING_V1
status: development
scope: Slot 3 TESTNET preparation; no run start or order
---

# BTC Demo: USD price and USDC settlement

The original market observation remains USD per BTC. The selected account
margin and the private instrument settlement currency are USDC. Neither a
blank quoteCcy nor settleCcy alone supplies a USD/USDC market conversion.

The explicit binding in xperp_settlement_v1 combines the original private
account and exact instrument GETs with the linear EEA X-Perp payoff rule.
The original payloads are retained unchanged. The normalized sizing source
uses schema v2 and retains those same observations for cold reconstruction.
Legacy monetary sources keep their original v1 serialization.

The source interpretation is based on the venue's
[EEA calculation formula](https://www.okx.com/en-eu/help/calculation-of-contracts-profit-and-loss-eea)
(updated 2026-08-13), its
[selected-margin currency description](https://www.okx.com/en-eu/help/faq-on-usd-margined-futures-contracts)
(updated 2026-09-02), and the
[API fillPnl definition](https://www.okx.com/docs-v5/en/).
The formula directly expresses the linear payoff using quantity, face value,
multiplier and the price difference; the selected account currency determines
its cash unit. Applying this combination to the exact private instrument is an
explicit contract interpretation. It is not a measured settlement or a claim
that one USDC trades at one USD.

The implementation admits only the already supported EEA single-currency
account, cross/net mode, USDC selected and enabled, autoLoan=false, a live
linear USD_UM_XPERP instrument with its matching USD underlying, empty native
quoteCcy, base-denominated ctVal and ctMult=1. It keeps the USD price label
through the cost consumers and separately records the USDC cash rule.
An incompatible account, underlying, instrument or supplied market FX route
is rejected.

This produces modeled risk, book-depth costs and initial-margin requirements.
It does not produce a fill, paid fee, funding payment, realized PnL or exchange
balance. Those remain subject to their original confirmed venue-evidence
consumers. No order or run is authorized by this document.

The V3 Demo budget owner uses the existing durable store and original risk,
cost and recovery calculations. Its TESTNET envelope is rejected by the
generic owner and by Live execution identity binding. The sealed generic
budget contract and host remain unchanged from the target main revision.

The offline first-entry tests cover both original Core directions, once-funded
25 USDC allocation despite a larger observed account balance, executable
multi-level depth, fees, cold readback, and rejection before a hold when
source or monetary identities disagree. They do not prove the complete
scheduled five-lane runtime or its subsequent Demo reversal chain.

RUNTIME_AUTHORIZATION_EFFECT=NONE
