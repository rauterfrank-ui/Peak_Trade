# Search Terms and Scope

## Pre-flight
- REPO_ROOT=`/Users/frnkhrz/Peak_Trade`
- BRANCH=`main`
- HEAD=`43558204d4f7bcab30ce9e8357d2513a9a5f0970`
- ORIGIN_MAIN=`43558204d4f7bcab30ce9e8357d2513a9a5f0970`
- WORKTREE: only untracked prior evidence dirs (EXPECTED_PRIOR_EVIDENCE)
- STASHES: 3 entries left untouched
- UNEXPECTED_PRODUCTIVE_CHANGES=false → audit continued

## Scope searched
1. Peak_Trade repo (full tree, excluding `.git` / `node_modules`)
2. Adjacent local paths (read-only, depth-limited): `~/Documents`, `~/Desktop`, sibling `Peak_Trade_*` worktrees, runtime evidence archives under `~/Documents/Peak_Trade_runtime_evidence_archive_*`
3. No runtime, scheduler, testnet, order, or live activation
4. No overwrite of prior evidence directories

## A) EL KAROUI terms used
`El Karoui`, `ElKaroui`, `El_Karoui`, `el karoui`, `elkaroui`, `el_karoui`, `Nicole El Karoui`, `NicoleElKaroui`, `Karoui`, `stochastic control`, `backward stochastic differential equation`, `BSDE`, `reflected BSDE`, `stochastic target`, `hedging`, `superhedging`, `dynamic risk measure`, `optimal stopping`, `stochastic optimization`, `nonlinear pricing`, `risk-sensitive control`

## B) ARMSTRONG terms used
`Armstrong`, `Armstrong cycle(s)`, `Armstrong model`, `Economic Confidence Model`, `ECM`, `8.6 year cycle`, `8.6-year cycle`, `3141 days`, `Pi cycle`, `pi cycle`, `confidence cycle`, `capital flow cycle`, `sovereign debt cycle`, `market cycle`, `cyclical timing`, `cycle forecast`

## Verification rule
Name hits alone were not accepted. Each hit was classified via context (source comments, formulas, docs, imports). False positives (generic “market cycle”, synthetic `pi_cycle` noise in demo scripts, unrelated ECM acronyms where context fails) are listed in `false_positive_inventory.md`.

## Hit volume (approx.)
- Files mentioning El Karoui variants: ~156
- Files mentioning Armstrong/ECM/3141: ~201
- Productive owners concentrated under `src/strategies/{el_karoui,armstrong}/`, `src/strategies/ecm.py`, `src/experiments/armstrong_elkaroui_combi_experiment.py`
