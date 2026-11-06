# Search Terms and Scope

**Mode:** READ-ONLY forensic audit  
**Evidence dir:** `docs/evidence/ehlers_bouchaud_system_integration_audit_v1/`  
**No productive code/test/config/runtime mutations.**

## A) Ehlers search terms (executed)

- Ehlers, John Ehlers, John F. Ehlers, ehlers
- cyber cycle / cybercycle, dominant cycle / period, cycle period
- market/trend/cycle mode
- Hilbert transform / HilbertTransformer / HT_DCPERIOD / HT_DCPHASE
- MAMA / FAMA / Mesa Adaptive Moving Average / MESA
- Fisher Transform / Ehlers Fisher
- Roofing Filter, Super Smoother / supersmoother, Decycler
- Bandpass / high-pass / low-pass filter, zero-lag
- phase accumulation, sinewave / sine wave indicator
- instantaneous trendline, autocorrelation periodogram, homodyne discriminator
- adaptive filter, digital signal processing, DSP

## B) Bouchaud search terms (executed)

- Bouchaud, Jean-Philippe Bouchaud, Jean Philippe Bouchaud, bouchaud
- price/market impact, square-root law / impact law
- order flow / OFI / order-flow imbalance
- long memory / propagator / transient / permanent impact / impact decay
- latent liquidity / liquidity imbalance
- trade sign / signed volume / volume imbalance
- metaorder / meta-order / participation rate / execution impact / impact coefficient
- lead-lag / cross-impact / self-impact
- volatility-volume relation, market microstructure
- anomalous diffusion / diffusive price / response function

## C) Typo / alias variants (executed)

- Bochuard, Bouchard, Bouchaurd, Buchaud, Buchard  
→ **no code hits** for these spellings as Bouchaud aliases.

## Scope boundaries

| In scope | Out of scope |
|---|---|
| Strategy modules, registry, signal binding, R&D presets, offline STEP29M/research bindings, docs, tests, notebooks, evidence refs | Productive Master V2 / Double Play mutation |
| Callgraph / import / encoding-class surfaces | Live/testnet/order activation |
| False-positive classification of microstructure/impact terms | Implementing or promoting either strategy |

## Verification rule

No classification from filename alone. Each real hit is tied to code formula, docs citation, test, or research config claim. Name collisions (German „Fehler“, generic DSP wording, generic market-impact metrics, lead-lag without Bouchaud citation) → `FALSE_POSITIVE`.
