# Quarto Smoke Report

## Overview

The **Quarto smoke report** is a minimal test report that verifies Quarto rendering is working correctly in the Peak Trade project.

**Template**: `templates/quarto/smoke.qmd`
**Output**: `reports&#47;quarto&#47;smoke.html` (gitignored)

## Purpose

- **Smoke test**: Quickly verify Quarto installation and basic functionality
- **CI/CD validation**: Test report generation in GitHub Actions
- **Self-contained output**: HTML with embedded resources (no external runtime dependencies beyond Quarto/HTML path)
- **No-exec in CI**: The workflow enforces **`execute.enabled: false`** and forbids executable ` ```{python}` / ````{r}`-style chunks in guarded `.qmd` files (`scripts/ci/check_quarto_no_exec.sh`). Rendering is Markdown-to-HTML with static fenced code (syntax highlighting), not Python notebook execution.

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
- **Python**: >= 3.10 (used by tooling; CI uses 3.11 for the Quarto smoke job)
- **Git**: For repository context

### Python packages (local / manual only)

The smoke template illustrates NumPy/Pandas/Matplotlib in **static** fenced ` ```python ` blocks while **`execute.enabled: false`**. CI does **not** `pip install` NumPy/Pandas/Matplotlib for report execution—it only upgrades `pip` and documents that **no Python runtime deps** are required for the no-exec smoke render.

Optional, if you run a separate **manual** Quarto workflow with execution enabled elsewhere (not the CI smoke path):

```bash
pip install numpy pandas matplotlib
```

## Output

### Local

- **Output file**: `reports&#47;quarto&#47;smoke.html`
- **Format**: Self-contained HTML (all resources embedded)
- **Size**: Varies with content; **no-exec CI** renders static examples (no matplotlib output from execution). Larger artifacts only if you deliberately enable execution and produce figures locally—out of scope for the guarded CI smoke posture.

### CI Artifact

- **Name**: `quarto-smoke-html`
- **Retention**: 7 days
- **Location**: GitHub Actions > Workflow run > Artifacts
- **Graceful handling**: Uses `if-no-files-found: warn` to avoid hard failures

## What's Tested

The smoke report includes:

1. **Markdown rendering**: Headers, lists, tables, formatting
2. **Python syntax highlighting**: Fenced `` ```python `` blocks illustrate sample code **without CI execution**
3. **Illustrative “visualization” code**: Presented as non-executable static blocks when `execute.enabled: false`
4. **Environment-style snippets**: Shown as static code, not evaluated in the no-exec CI path
5. **Self-contained HTML**: No Jupyter/R/TinyTeX required for this workflow

## CI/CD Integration

### GitHub Actions Workflow

File: `.github/workflows/quarto_smoke.yml`

**Triggers:**
- Push to `main`, `develop`, `feat&#47;**`, `fix&#47;**`
- Pull requests to `main`, `develop`
- Manual workflow dispatch

**Steps:**
1. Job info summary
2. Checkout repository
3. **Guard**: Quarto no-exec (`bash scripts/ci/check_quarto_no_exec.sh`) — no executable ````{python}` / ````{r}` chunks on guarded paths; expect `execute.enabled: false` where required by the checker
4. Set up Python 3.11 (pip cache)
5. Install Python dependencies: **`pip upgrade` only** plus log line `no-exec Quarto smoke: no Python runtime deps required` (**no** NumPy/Pandas/Matplotlib install in CI for this job)
6. Set up Quarto (release channel)
7. Verify Quarto installation
8. Render smoke report via `make report-smoke`
9. Upload HTML artifact (`quarto-smoke-html`, 7-day retention, `warn` if missing)
10. Check that `reports&#47;quarto&#47;smoke.html` exists

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

If **you** are experimenting with execution-enabled Quarto configs **outside** the CI no-exec smoke path:

```bash
pip install numpy pandas matplotlib

# Or use requirements if available
pip install -r requirements.txt
```

The Quarto smoke **CI job** itself does **not** require these installs.

### Permission denied on script

```bash
# Make script executable
chmod +x scripts/dev/report_smoke.sh
```

### CI artifact not found

Check workflow logs for errors:
1. Verify the no-exec guard and Quarto setup steps succeeded
2. Check render step output for errors
3. Confirm `reports&#47;quarto&#47;smoke.html` was created
4. Review upload-artifact step logs

### Output file not generated

```bash
# Check for errors in render
make report-smoke

# Try direct Quarto command with verbose output
quarto render templates/quarto/smoke.qmd --to html --output-dir reports/quarto --verbose
```

### Guard failures (executable chunks)

Tracked `.qmd` covered by `check_quarto_no_exec.sh` must not use Quarto executable chunk headers like `` ```{python} `` — use fenced `` ```python `` for **static** display only while keeping **`execute.enabled: false`** aligned with CI policy.

## Extending the Smoke Report

To add more smoke-visible content while staying CI-safe:

1. **Edit** `templates/quarto/smoke.qmd` (this doc does not change templates in the alignment slice)
2. **Prefer** Markdown and **static** fenced `` ```python `` blocks and `` ```bash `` blocks; **do not** add executable ````{python}` or ````{r}` chunks on guarded paths if the no-exec guard must keep passing
3. **Keep** `execute.enabled: false` for the no-exec CI workflow unless you intentionally redesign execution policy (separate change, out of scope here)
4. **Test locally**: `make report-smoke`
5. **Commit** changes and verify CI workflow

**Future / manual / out of scope for CI smoke:** turning on engines, `{python}` execution, or scientific-stack installs inside the **guarded** smoke path would require workflow and policy changes beyond this documentation slice.

### Example: Adding a new section

Add headings and prose in Markdown, then a separate **static** fenced Python block (not ````{python}`):

````markdown
## New Test Section

Description of what you're testing.
````

````python
# Static sample only (won't execute with execute.enabled: false)
answer = 42
````

## Related Documentation

- [General Reporting Guide](REPORTING.md)
- [Quarto Documentation](https://quarto.org/docs/guide/)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

## Notes

- **No Jupyter required**: The no-exec CI path renders without running Python kernels
- **Template posture**: YAML `execute.enabled: false`; static code blocks are highlighted, not executed in CI smoke
- **No R/TinyTeX required**: Using HTML output only (no PDF)
- **Self-contained**: Single HTML file with embedded tooling output as applicable
- **Fast**: Typical local render stays in the seconds range; CI includes setup plus render
- **Graceful degradation**: CI won't fail the upload step outright if artifact is missing (`warn` mode)

