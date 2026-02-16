# final_done_pin_v1.sh (canonical)

Creates a deterministic **FINAL_DONE** snapshot under `out/ops/final_done_<TS>/` and writes the canonical pin:

- `out/ops/FINAL_DONE.txt`
- `out/ops/FINAL_DONE.txt.sha256`
- Evidence dir + `.bundle.tgz`

## Usage

```bash
./scripts/ops/final_done_pin_v1.sh
# or with explicit UTC timestamp:
./scripts/ops/final_done_pin_v1.sh 20260216T041900Z
```
