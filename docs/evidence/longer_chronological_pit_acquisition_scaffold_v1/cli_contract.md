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

## Defaults

- dry-run semantics
- `--allow-network` off
- `--write-manifest` off
- no credentials flags exist

## Explicit gates

| Flag | Effect |
|---|---|
| `--allow-network` | Permit adapter network path (still needs configured fetcher; CI tests never enable real network) |
| `--write-manifest` | Persist manifest under external archive root |
| `--archive-root` | Explicit external root (else env) |
| `--max-partitions` | Cap planned partitions |
| `--probe-one` | Force max 1 partition |

No flag activates orders, runtime, trading, paper, shadow, or testnet.
