# Reproducibility Guide

## Overview

Peak_Trade implements comprehensive reproducibility tracking to ensure that backtest results can be reliably reproduced, debugged, and audited. This is critical for:

- **Debugging**: Reproduce issues exactly as they occurred
- **Performance Comparison**: Compare results across different code versions
- **Regulatory Compliance**: Demonstrate consistent, verifiable results
- **Research Validation**: Ensure scientific rigor in strategy development

## Key Concepts

### Run ID

Every backtest run is assigned a unique **run_id** (8-character UUID) that serves as the primary identifier. This ID is used to:

- Organize results in the `results/` directory
- Link reproducibility metadata to specific runs
- Reference runs in logs and reports

Example: `abc12345`

### Reproducibility Context

The `ReproContext` captures all metadata necessary to reproduce a run:

```python
@dataclass
class ReproContext:
    run_id: str                    # Unique identifier (8 chars)
    git_sha: str                   # Git commit hash
    config_hash: str               # Hash of strategy config
    seed: int                      # Random seed
    dependencies_hash: str         # Hash of requirements.txt
    timestamp: str                 # ISO 8601 timestamp (UTC)
    hostname: str                  # Machine identifier
    python_version: str            # Python version
```

This context is automatically saved to `results/{run_id}/repro.json` for every backtest.

## Usage

### Running a Reproducible Backtest

```python
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals
import pandas as pd

# Load your data
df = pd.read_parquet("data/BTC_EUR_1h.parquet")

# Initialize engine
engine = BacktestEngine()

# Run backtest with explicit seed for reproducibility
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={
        'fast_period': 10,
        'slow_period': 30,
        'stop_pct': 0.02
    },
    seed=42,  # Explicit seed ensures reproducibility
    save_repro=True  # Save reproducibility metadata (default)
)

# Access run ID and metadata
print(f"Run ID: {result.metadata['repro_context']['run_id']}")
print(f"Results saved to: results/{result.metadata['repro_context']['run_id']}/")
```

### Reproducing a Run

Use the CLI tool to load and validate a previous run:

```bash
# List available runs
python scripts/reproduce_run.py --list

# Load and validate a specific run
python scripts/reproduce_run.py --run-id abc12345

# Skip validation (faster)
python scripts/reproduce_run.py --run-id abc12345 --no-validate
```

The tool will:
1. Load the `repro.json` file
2. Display all captured metadata
3. Validate environment (git SHA, Python version, dependencies)
4. Provide instructions for reproducing the run

### Programmatic Reproduction

```python
from src.core.repro import ReproContext, set_global_seed
from src.backtest.engine import BacktestEngine
from pathlib import Path

# Load repro context
run_id = "abc12345"
repro_ctx = ReproContext.load(Path(f"results/{run_id}/repro.json"))

# Set the same seed
set_global_seed(repro_ctx.seed)

# Run backtest with same parameters
# (You need to reconstruct config from config_hash or save it separately)
engine = BacktestEngine()
result = engine.run_realistic(
    df=df,  # Same data
    strategy_signal_fn=strategy_fn,  # Same strategy
    strategy_params=params,  # Same parameters
    seed=repro_ctx.seed
)

# Results should be identical (within floating-point precision)
```

## Run ID Conventions

### Format

- **Length**: 8 characters
- **Format**: Lowercase hexadecimal
- **Example**: `a1b2c3d4`

### Uniqueness

Run IDs are generated using `uuid.uuid4()[:8]`, providing sufficient uniqueness for most use cases:

- **Collision probability**: ~1 in 4 billion for 8-char hex
- **Namespace**: Per repository instance

### Organization

Results are organized by run ID:

```
results/
├── a1b2c3d4/
│   ├── repro.json       # Reproducibility metadata
│   ├── results.csv      # Backtest results (if saved)
│   └── plots/           # Visualizations (if generated)
├── b2c3d4e5/
│   └── repro.json
└── ...
```

## Best Practices

### 1. Always Use Explicit Seeds

```python
# ✅ GOOD: Explicit seed
result = engine.run_realistic(df, strategy_fn, params, seed=42)

# ⚠️ ACCEPTABLE: Uses default seed (42)
result = engine.run_realistic(df, strategy_fn, params)

# ❌ BAD: No seed tracking (old code)
# Don't do this - results won't be reproducible
```

### 2. Document Config Changes

When changing strategy parameters, document the change:

```python
# Version 1: Initial parameters
params_v1 = {'fast': 10, 'slow': 30}

# Version 2: Optimized parameters
# Change rationale: Reduced lag while maintaining signal quality
params_v2 = {'fast': 8, 'slow': 25}
```

### 3. Pin Dependencies

Update `requirements.txt` when adding/updating packages:

```bash
# After installing new package
pip freeze > requirements.txt

# Dependencies hash will change, alerting you to environment differences
```

### 4. Commit Before Important Runs

```bash
# Commit your changes before running backtests
git add .
git commit -m "Update strategy parameters for experiment X"

# Run backtest - git SHA will be captured
python run_backtest.py

# Results are now linked to exact code version
```

### 5. Use Descriptive Branch Names

```bash
# Good branch names for experiments
git checkout -b experiment/volatility-filter
git checkout -b feature/stop-loss-optimization
git checkout -b fix/regime-detection-bug
```

## Determinism Validation

### Testing Seed Determinism

```python
from src.core.repro import set_global_seed, verify_determinism
import random

def my_random_function():
    """Example function that uses randomness."""
    return [random.random() for _ in range(10)]

# Verify function is deterministic when seeded
is_deterministic = verify_determinism(
    func=my_random_function,
    seed=42,
    num_runs=3
)

assert is_deterministic, "Function is not deterministic!"
```

### Testing Backtest Reproducibility

```python
# Run backtest twice with same seed
results_1 = engine.run_realistic(df, strategy_fn, params, seed=42)
results_2 = engine.run_realistic(df, strategy_fn, params, seed=42)

# Compare results
import numpy as np

equity_diff = np.abs(results_1.equity_curve - results_2.equity_curve)
max_diff = equity_diff.max()

print(f"Max equity difference: {max_diff}")
assert max_diff < 1e-10, f"Results differ by {max_diff}"
```

## Troubleshooting

### Non-Deterministic Results

**Problem**: Same seed produces different results.

**Common Causes**:

1. **Different NumPy versions**
   ```bash
   # Check version
   python -c "import numpy; print(numpy.__version__)"
   
   # Pin exact version in requirements.txt
   numpy==1.24.0
   ```

2. **Floating-point operations order**
   - Use `np.sum()` instead of Python's `sum()` for arrays
   - Be careful with parallel operations

3. **Data loading issues**
   - Ensure data is sorted by timestamp
   - Check for NaN handling differences

4. **External randomness**
   - Network calls (timestamps, market data)
   - File system operations (directory ordering)

**Solution**: Use `verify_determinism()` to isolate non-deterministic code.

### Missing repro.json

**Problem**: `reproduce_run.py` can't find run ID.

**Solutions**:

1. **List available runs**:
   ```bash
   python scripts/reproduce_run.py --list
   ```

2. **Check results directory**:
   ```bash
   ls -la results/
   ```

3. **Verify save_repro was True**:
   ```python
   # Ensure save_repro=True (default)
   result = engine.run_realistic(..., save_repro=True)
   ```

### Git SHA Mismatch

**Problem**: Current git SHA doesn't match original run.

**This is expected when**:
- You've made commits since the run
- You're on a different branch
- You're testing on a different machine

**Solutions**:

1. **Checkout original commit**:
   ```bash
   git checkout abc1234  # Use original git SHA
   python scripts/reproduce_run.py --run-id xyz789
   ```

2. **Accept mismatch** (if intentional):
   ```bash
   # Skip validation
   python scripts/reproduce_run.py --run-id xyz789 --no-validate
   ```

### Python Version Mismatch

**Problem**: Python version differs from original run.

**Solutions**:

1. **Use pyenv to match version**:
   ```bash
   pyenv install 3.11.5
   pyenv local 3.11.5
   ```

2. **Use Docker** (recommended for production):
   ```dockerfile
   FROM python:3.11.5-slim
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   ```

### Dependencies Hash Mismatch

**Problem**: `requirements.txt` has changed.

**This indicates**:
- Package versions have changed
- New packages were added
- Packages were removed

**Solutions**:

1. **Restore original dependencies**:
   ```bash
   # If you have the original requirements.txt
   pip install -r requirements.old.txt
   ```

2. **Document differences**:
   ```bash
   # Compare current vs original
   diff requirements.txt results/abc12345/requirements.txt
   ```

3. **Accept risk** (for minor version bumps):
   ```bash
   # Proceed with warning
   python scripts/reproduce_run.py --run-id abc12345
   ```

## Advanced Usage

### Custom Metadata

Add custom fields to repro context:

```python
from src.core.repro import ReproContext

# Create with custom metadata
ctx = ReproContext.create(
    seed=42,
    config_dict={
        'strategy': 'ma_crossover',
        'params': {'fast': 10, 'slow': 30},
        # Custom fields
        'experiment_id': 'EXP-001',
        'researcher': 'alice',
        'notes': 'Testing new stop-loss logic'
    }
)
```

### Stable Config Hashing

```python
from src.core.repro import stable_hash_dict

# Hash is independent of key order
config1 = {'a': 1, 'b': 2, 'c': 3}
config2 = {'c': 3, 'a': 1, 'b': 2}

hash1 = stable_hash_dict(config1)
hash2 = stable_hash_dict(config2)

assert hash1 == hash2  # ✅ Same hash despite different order
```

### Batch Reproduction

```python
from pathlib import Path
from src.core.repro import ReproContext

# Load all runs and check for issues
results_dir = Path("results")
for run_dir in results_dir.iterdir():
    if not run_dir.is_dir():
        continue
    
    repro_file = run_dir / "repro.json"
    if not repro_file.exists():
        continue
    
    ctx = ReproContext.load(repro_file)
    
    # Check for issues
    if ctx.seed is None:
        print(f"⚠️  {run_dir.name}: No seed set")
    if ctx.git_sha is None:
        print(f"⚠️  {run_dir.name}: No git SHA")
```

## API Reference

### ReproContext

```python
class ReproContext:
    """Reproducibility context for a backtest run."""
    
    @classmethod
    def create(
        cls,
        seed: Optional[int] = None,
        git_sha: Optional[str] = None,
        config_dict: Optional[Dict] = None,
        dependencies_hash: Optional[str] = None,
    ) -> "ReproContext":
        """Create context from current environment."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-compatible dict."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ReproContext":
        """Deserialize from dict."""
        ...
    
    def save(self, path: Path) -> None:
        """Save to JSON file."""
        ...
    
    @classmethod
    def load(cls, path: Path) -> "ReproContext":
        """Load from JSON file."""
        ...
```

### Helper Functions

```python
def set_global_seed(seed: int) -> None:
    """Set seed for all random number generators."""
    ...

def generate_run_id() -> str:
    """Generate unique run ID (8 chars)."""
    ...

def hash_dependencies() -> Optional[str]:
    """Hash requirements.txt for environment reproducibility."""
    ...

def stable_hash_dict(d: Dict[str, Any], short: bool = True) -> str:
    """Compute stable hash of dict (key-order-independent)."""
    ...

def get_git_sha(short: bool = True) -> Optional[str]:
    """Get current git commit SHA."""
    ...

def verify_determinism(
    func: Callable,
    seed: int,
    num_runs: int = 2,
    **kwargs
) -> bool:
    """Verify that a function produces deterministic results."""
    ...
```

## Related Documentation

- [Backtest Engine](BACKTEST_ENGINE.md) - Core backtesting functionality
- [Config Registry](CONFIG_REGISTRY_USAGE.md) - Strategy configuration management
- [Developer Workflow](DEVELOPER_WORKFLOW_GUIDE.md) - Best practices for development

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review existing issues in the issue tracker
3. Create a new issue with:
   - Run ID (if applicable)
   - Error message
   - Steps to reproduce
   - Environment details (`python --version`, `git rev-parse HEAD`)
