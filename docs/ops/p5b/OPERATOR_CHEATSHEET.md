# P5B — Evidence Pack Automation (Operator Cheatsheet)

**Paths:** Docs use token-policy-safe encoding (`out&#47;ops&#47;...`). In your terminal, replace `&#47;` with `/`.

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
# Terminal: use out/ops/... (replace &#47; with /)
python3 scripts/aiops/validate_evidence_pack.py \
  --manifest out/ops/evidence_packs/pack_fixed/manifest.json
```

Exit 0: OK. Exit 2: validation failed.

## Update consolidated index

```bash
# Terminal: use out/ops/... (replace &#47; with /)
python3 scripts/aiops/update_evidence_index.py \
  --root out/ops/evidence_packs \
  --out out/ops/evidence_packs/index_all.json
```

## CI smoke (local)

```bash
scripts/ci/evidence_pack_validation_smoke.sh
```
