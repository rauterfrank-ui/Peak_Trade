# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Minimal OS deps (adjust if your deps need more, but keep small)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Workdir inside container (repo will be mounted read-only here)
WORKDIR /work

# Optional: speed up pip + keep cache in /cache (mounted rw)
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_COLOR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal python tooling
RUN python -m pip install --no-cache-dir -U pip

# Install project deps at build time (no network at run time with --network=none).
# Skip "-e ." so we do not need the repo in the image; repo is mounted at /work at run time.
COPY requirements.txt /tmp/requirements.txt
RUN grep -v '^-e ' /tmp/requirements.txt > /tmp/deps.txt \
 && python -m pip install --no-cache-dir -r /tmp/deps.txt \
 && rm -f /tmp/requirements.txt /tmp/deps.txt

# NOTE: We do NOT COPY the repo; you mount it read-only at /work at run time.

CMD ["bash", "-lc", "python3 --version && echo 'L3 image ready'"]
ENV PYTHONPATH=/work
