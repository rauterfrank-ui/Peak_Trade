# Quarto Smoke Report (HTML)

Quick smoke test report for validating reporting infrastructure.

## Overview

The smoke report is a minimal Quarto document that tests the basic reporting pipeline:
- Quarto installation and rendering
- HTML output generation with embedded resources
- Basic document structure and formatting
- Integration with the Peak Trade build system

## Source Files

**Committed smoke report:**
```
reports/quarto/smoke.qmd
```

This is the standard smoke test report that is committed to the repository.

**Output directory:**
```
reports/quarto/_smoke/
```

Generated HTML files are saved here (ignored by git).

## Local Development

### Generate Report

```bash
make report-smoke
```

This will:
1. Check for Quarto installation
2. Render `reports/quarto/smoke.qmd` to HTML
3. Save output to `reports/quarto/_smoke/smoke.html`
4. Display success message with output path

### Generate and Open Report

```bash
make report-smoke-open
```

This will:
1. Generate the report
2. Open the HTML output in your default browser
   - macOS: uses `open`
   - Linux: uses `xdg-open`
   - Other: displays path for manual opening

## Fallback Behavior

If `reports/quarto/smoke.qmd` does not exist (e.g., in older branches), the script automatically creates a minimal fallback report. This ensures the smoke test always works, even in branches without the committed report.

## Troubleshooting

### Quarto Not Found

If you get "quarto: command not found":

```bash
# macOS
brew install quarto

# Other platforms
# Visit: https://quarto.org/docs/get-started/
```

### Output Not Generated

Check that you have write permissions in the `reports/quarto/_smoke/` directory.

## Technical Details

- **Format:** HTML with embedded resources (self-contained)
- **Theme:** Cosmo
- **Dependencies:** None (no Python/R/Jupyter/TinyTeX required)
- **Platform:** Cross-platform (macOS, Linux, Windows)

## Next Steps

- Extend with actual strategy metrics
- Add performance visualizations
- Integrate backtest results
- Add automated report generation in CI/CD
