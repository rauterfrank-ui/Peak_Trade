# Test Fixture — PASS

This fixture contains valid references and patterns that should be ignored.

## Valid References (these targets exist)

- Link to ops README: [docs/ops/README.md](docs/ops/README.md)
- Link to ops center: `scripts/ops/ops_center.sh`
- Bare path: docs/ops/README.md

## Patterns That Should Be Ignored

### Wildcards (should not be checked)
- Glob pattern: docs/*.md
- Recursive glob: docs/**/README.md
- Question mark: scripts/ops/ops?.sh

### Commands with spaces (should not be checked)
- Command invocation: ./scripts/ops/ops_center.sh doctor
- Another command: scripts/ops/verify_docs_reference_targets.sh --help

### Directory references (trailing slash, should not be checked)
- Directory: docs/ops/
- Another dir: scripts/

### References inside code blocks (should be ignored)

Here's an example command that references a missing file:

```bash
# This reference should NOT be checked (inside code block)
cat docs/ops/__fixture_missing_target__347__nope.md
```

The script should ignore the missing target above because it's in a code block.
