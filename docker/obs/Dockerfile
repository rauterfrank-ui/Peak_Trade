# Peak_Trade – Phase 16L: Ops Runner for Stage1 Monitoring
# Reproducible Docker environment for daily snapshot + weekly trend reports

FROM python:3.11-slim

# Install uv for fast, reproducible dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (cache layer for uv lock)
COPY pyproject.toml uv.lock ./

# Copy entire repo (needed for uv sync to build the project)
COPY . .

# Install deps + project into .venv (single sync so .venv survives)
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Default ENV: reports go to /reports (mounted volume)
ENV PEAK_REPORTS_DIR=/reports

# Entrypoint dispatches commands
COPY docker/obs/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--help"]
