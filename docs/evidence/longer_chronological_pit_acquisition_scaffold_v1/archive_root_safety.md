# Archive root safety

Env var: `PEAK_TRADE_DATA_ARCHIVE_ROOT`

## Rules

1. No implicit default inside the git repository.
2. Writes (manifest, artifacts, quarantine, state) require the env var or `--archive-root`.
3. Plan &#47; discover &#47; dry-run without write work with root unset.
4. Rejected roots:
   - relative paths
   - filesystem root (`&#47;`)
   - home directory
   - any path equal to or nested under the git repo root
5. Layout under root:

```text
{root}&#47;longer_chronological_pit&#47;chrono_3y_v1&#47;
  raw&#47;
  normalized&#47;
  manifests&#47;
  quarantine&#47;
  state&#47;
  logs&#47;
```

6. Gitignore belt-and-suspenders added for `&#47;datasets&#47;`, `&#47;longer_chronological_pit&#47;`, and chrono raw&#47;normalized&#47;quarantine globs.
7. Immutable create-only writes — existing partition artifacts cannot be overwritten.
