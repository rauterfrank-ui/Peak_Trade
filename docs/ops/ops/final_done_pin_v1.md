# final_done_pin_v1.sh (canonical)

Creates a deterministic **FINAL_DONE** snapshot under `out&#47;ops&#47;final_done_<TS>&#47;` and writes the canonical pin:

- `out&#47;ops&#47;FINAL_DONE.txt`
- `out&#47;ops&#47;FINAL_DONE.txt.sha256`
- Evidence dir + `.bundle.tgz`

## Usage

```bash
./scripts/ops/final_done_pin_v1.sh
# or with explicit UTC timestamp:
./scripts/ops/final_done_pin_v1.sh 20260216T041900Z
```
