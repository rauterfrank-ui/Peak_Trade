# Quarto Smoke Report

## Overview

The **Quarto smoke report** is a minimal test report that verifies Quarto rendering is working correctly in the Peak Trade project.

**Template**: `templates/quarto/smoke.qmd`
**Output**: `reports/quarto/smoke.html` (gitignored)

## Purpose

- **Smoke test**: Quickly verify Quarto installation and basic functionality
- **CI/CD validation**: Test report generation in GitHub Actions
- **Self-contained output**: HTML with embedded resources (no external dependencies)
- **Minimal dependencies**: Only requires Python, NumPy, Pandas, and Matplotlib

## Quick Start

### Local Rendering

```bash
# Render smoke report
make report-smoke

# Render and open in browser (macOS only)
make report-smoke-open
```

### Direct Script Usage

```bash
# Run the smoke report script directly
./scripts/dev/report_smoke.sh
```

### Manual Quarto Command

```bash
# Render with Quarto CLI directly
quarto render templates/quarto/smoke.qmd --to html --output-dir reports/quarto
```

## Requirements

### Software

- **Quarto**: >= 1.3.0 (install via homebrew: `brew install quarto`)
- **Python**: >= 3.10
- **Git**: For repository context

### Python Packages

```bash
pip install numpy pandas matplotlib
```

These are typically already installed in the Peak Trade development environment.

## Output

### Local

- **Output file**: `reports/quarto/smoke.html`
- **Format**: Self-contained HTML (all resources embedded)
- **Size**: ~500KB (includes base64-encoded plots)

### CI Artifact

- **Name**: `quarto-smoke-html`
- **Retention**: 7 days
- **Location**: GitHub Actions > Workflow run > Artifacts
- **Graceful handling**: Uses `if-no-files-found: warn` to avoid hard failures

## What's Tested

The smoke report includes:

1. **Markdown rendering**: Headers, lists, tables, formatting
2. **Python code execution**: Simple computations with NumPy/Pandas
3. **Matplotlib plots**: Bar charts with embedded images
4. **Environment info**: Python version, platform, timestamp
5. **Self-contained HTML**: No external resource dependencies

## CI/CD Integration

### GitHub Actions Workflow

File: `.github/workflows/quarto_smoke.yml`

**Triggers:**
- Push to `main`, `develop`, `feat/**`, `fix/**`
- Pull requests to `main`, `develop`
- Manual workflow dispatch

**Steps:**
1. Checkout repository
2. Set up Python 3.11 with pip cache
3. Install Python dependencies (numpy, pandas, matplotlib)
4. Set up Quarto (latest release)
5. Verify Quarto installation
6. Render smoke report via `make report-smoke`
7. Upload HTML artifact (7-day retention)
8. Validate output file exists

**Artifact access:**
1. Navigate to GitHub Actions workflow run
2. Scroll to "Artifacts" section at bottom
3. Download `quarto-smoke-html.zip`
4. Extract and open `smoke.html` in browser

## Troubleshooting

### Quarto not found

```bash
# Install Quarto (macOS)
brew install quarto

# Verify installation
quarto --version
```

### Python packages missing

```bash
# Install required packages
pip install numpy pandas matplotlib

# Or use requirements if available
pip install -r requirements.txt
```

### Permission denied on script

```bash
# Make script executable
chmod +x scripts/dev/report_smoke.sh
```

### CI artifact not found

Check workflow logs for errors:
1. Verify Quarto setup step succeeded
2. Check render step output for errors
3. Confirm `reports/quarto/smoke.html` was created
4. Review upload-artifact step logs

### Output file not generated

```bash
# Check for errors in render
make report-smoke

# Try direct Quarto command with verbose output
quarto render templates/quarto/smoke.qmd --to html --output-dir reports/quarto --verbose
```

## Extending the Smoke Report

To add more smoke tests:

1. **Edit** `templates/quarto/smoke.qmd`
2. **Add** new code blocks with `{python}` or `{r}` (if R support added)
3. **Test locally**: `make report-smoke`
4. **Commit** changes and verify CI workflow

### Example: Adding a new section

```markdown
## New Test Section

Description of what you're testing.

{python}
# Your test code here
import some_module
result = some_module.test_function()
print(result)
```

## Related Documentation

- [General Reporting Guide](REPORTING.md)
- [Quarto Documentation](https://quarto.org/docs/guide/)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

## Notes

- **No Jupyter required**: Quarto executes Python code directly
- **No R/TinyTeX required**: Using HTML output only (no PDF)
- **Self-contained**: Single HTML file with all resources embedded
- **Fast**: Renders in ~5-10 seconds locally, ~30-60 seconds in CI
- **Graceful degradation**: CI won't fail if artifact upload has issues (uses `warn` mode)
