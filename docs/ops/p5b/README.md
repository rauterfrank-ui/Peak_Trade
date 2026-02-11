# P5B

Working notes for P5B (Evidence Pack Automation). See `docs/ops/p5b/P5B_TODO.md`.

## Evidence Pack Generator CLI

Create a pack (deterministic):

```bash
python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir "$(git rev-parse --show-toplevel)" \
  --in tests/fixtures/p5b/sample_dir \
  --pack-id fixed
```

Outputs: `manifest.json` + `index.json` under `out&#47;ops&#47;evidence_packs&#47;pack_&lt;id&gt;&#47;`

## Evidence Index updater

Consolidate all packs into a single index:

```bash
python3 scripts/aiops/update_evidence_index.py \
  --root out&#47;ops&#47;evidence_packs \
  --out out&#47;ops&#47;evidence_packs&#47;index_all.json
```
