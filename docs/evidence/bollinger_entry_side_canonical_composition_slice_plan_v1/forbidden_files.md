# Forbidden Files / Surfaces

Hard-forbidden for the deferred composition work and for this prep PR:

| Surface | Why |
|---------|-----|
| `src&#47;risk&#47;**` | Risk authority out of scope |
| `src&#47;execution&#47;**` | Execution kernel out of scope |
| Kill-switch &#47; reconciliation owners | Safety surfaces |
| Live&#47;order&#47;shadow&#47;paper&#47;testnet gates | Runtime activation forbidden |
| `src&#47;backtest&#47;engine.py` as direction authority | Classic LONG bypass must stay non-canonical |
| Projecting Bull&#47;Bear into Bollinger `entry_side` carrier | Circular&#47;competing authority (audit REJECT for Option-B anti-pattern) |
| Generic sign→LONG&#47;SHORT heuristics for all strategies | Forbidden |
| Dashboard&#47;adapter reinventing SideState | Consumer only |
| Symmetric short geometry without separate GO | Not authorized |
| Admin-bypass &#47; branch-protection mutation | Forbidden |
