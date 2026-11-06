# Phase U — Data Node Bootstrap (Ubuntu) + Hardening (Checklist)

> Goal: Bring up an always-on Data Node capable of running Docker stacks + scheduled exports.
> Non-goal: no execution endpoints, no live trading.

## 1) Provision
- Ubuntu LTS (server)
- SSH key auth only
- Dedicated user: `peaktrade` (sudo)
- Optional: static IP / DNS

## 2) Baseline hardening
- Firewall: allow SSH only (and VPN if used)
- Unattended upgrades enabled
- Time sync enabled

## 3) Docker installation
- Install Docker Engine + compose plugin
- Verify `docker version` and `docker compose version`

## 4) Filesystem
- Create data dirs:
  - `/srv/peaktrade/compose/`
  - `/srv/peaktrade/data/`
  - `/srv/peaktrade/out/ops/exports/`

## 5) Secrets (never commit)
- Object storage write creds stored on server only:
  - `/etc/peaktrade/exporter.env` (600)
- GitHub uses read-only token in repo secrets

## 6) Export job
- Schedule exporter via systemd timer or cron
- Exporter writes:
  - `manifest.json`
  - `SHA256SUMS.stable.txt`
  - payload data
- Upload outbound to object storage prefix

## 7) Validation
- Produce one export pack
- Verify locally:
  - `shasum -a 256 -c SHA256SUMS.stable.txt`
- Verify from GitHub (download+verify)
