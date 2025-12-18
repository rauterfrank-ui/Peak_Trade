# PR #114 — Merge Log

## PR
- Title: fix(reporting): make Quarto smoke report truly no-exec
- URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/114
- Base: main
- Head: fix/quarto-smoke-pure-markdown

## Merge
- Merge SHA: 781e3142c59f9fe1601b66c9dc50a7613eee7830
- Merged at: 2025-12-17T21:04:59Z
- Diffstat: +12 / -12 (files changed: 2)

## Summary
- Convert executable Quarto chunks to non-executable code blocks (pure Markdown → HTML)
- Set `execute: enabled: false` in the Quarto front matter
- CI smoke rendering no longer requires Python/Jupyter runtime deps
- More robust and reproducible CI/CD runs
- Avoids fragile kernel / nbformat / numpy / pandas / matplotlib requirements at render time

## Files Changed
- `templates/quarto/smoke.qmd` - Converted `{python}` chunks to `python` syntax highlighting
- `.github/workflows/quarto_smoke.yml` - Removed Python dependency installation

## Verification
- ✓ Rendered successfully with `quarto render smoke.qmd --to html`
- ✓ Verified no `\`\`\`{python}` chunks remain
- ✓ Output is self-contained HTML
- ✓ CI workflow no longer installs numpy/pandas/matplotlib/jupyter/nbformat
