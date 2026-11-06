# CLI contract

```text
python -m src.research.longer_chronological_pit_acquisition_v1 <command> [options]
```

## Commands

| Command | Behavior |
|---|---|
| `plan` | Dry-run partition plan + qualification text |
| `discover` | Plan + public source definitions |
| `manifest` | Emit deterministic manifest JSON (stdout) |
| `qualify-dry-run` | Alias of plan-style dry-run report |
| `probe` | Bounded probe; **network disabled by default** |
| `history-depth-probe` | Public OKX history-depth probe; **network/write disabled by default** |
| `seal-lifecycle` | Bind production lifecycle registry + public candle enrichment; seal long panel |
| `acquire-long-panel` | Bounded PT1H acquisition for sealed long-panel common window |

## Defaults

- dry-run semantics
- `--allow-network` off
- `--allow-network-probe` off
- `--allow-write-probe` off
- `--write-manifest` off
- no credentials flags exist

## Explicit gates

| Flag | Effect |
|---|---|
| `--allow-network` | Permit adapter network path (still needs configured fetcher; CI tests never enable real network) |
| `--allow-network-probe` | Explicit freigabe for `history-depth-probe` public HTTP calls |
| `--allow-write-probe` | Explicit freigabe to write small probe artifacts under external archive root |
| `--request-budget` | Hard request cap (required when network probe enabled; max 25) |
| `--write-manifest` | Persist manifest under external archive root |
| `--archive-root` | Explicit external root (else env) |
| `--max-partitions` | Cap planned partitions |
| `--probe-one` | Force max 1 partition |
| `--max-instruments` | Cap history-depth sample (1..5) |

No flag activates orders, runtime, trading, paper, shadow, or testnet.
