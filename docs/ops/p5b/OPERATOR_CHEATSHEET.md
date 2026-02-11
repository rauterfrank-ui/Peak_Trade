# P5B — Evidence Pack Automation (Operator Cheatsheet)

## Generate a pack (deterministic)

```bash
python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir "$(git rev-parse --show-toplevel)" \
  --in tests/fixtures/p5b/sample_dir \
  --pack-id fixed
```

Outputs: `manifest.json` + `index.json` under `out&#47;ops&#47;evidence_packs&#47;pack_&lt;id&gt;&#47;`

## Validate a pack

```bash
python3 scripts/aiops/validate_evidence_pack.py \
  --manifest out&#47;ops&#47;evidence_packs&#47;pack_fixed&#47;manifest.json
```

Exit 0: OK. Exit 2: validation failed.

## Update consolidated index

```bash
python3 scripts/aiops/update_evidence_index.py \
  --root out&#47;ops&#47;evidence_packs \
  --out out&#47;ops&#47;evidence_packs&#47;index_all.json
```

## CI smoke (local)

```bash
scripts/ci/evidence_pack_validation_smoke.sh
```
