FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Pin optional via build arg (falls du später reproduzierbar werden willst)
ARG MLFLOW_VERSION=2.15.1
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir "mlflow==${MLFLOW_VERSION}"

EXPOSE 5000
