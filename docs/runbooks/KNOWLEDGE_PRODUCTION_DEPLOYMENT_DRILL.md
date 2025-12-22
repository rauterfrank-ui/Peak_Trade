# Knowledge DB Production Deployment Drill

**Version:** v1.0  
**Last Updated:** 2025-12-22  
**Owner:** Platform Ops

---

## Goal & Scope

Verify Knowledge DB API functionality in production/staging environments without disrupting service:

- ✅ Read endpoints are accessible (GET)
- ✅ Write endpoints are properly gated (POST → 403)
- ✅ Graceful degradation works (501 when backend unavailable)
- ✅ Authentication/Authorization is enforced

**Scope:**
- Remote smoke tests via HTTP
- No server restarts required
- Safe for production (read-only + blocked write probes)

**Out of Scope:**
- Performance/load testing
- Data integrity validation
- Backend ChromaDB health checks

---

## Preconditions

### Required

1. **Target URL accessible**
   ```bash
   curl -I https://prod.example.com/api/health
   ```

2. **Network access**
   - Operator machine → Target deployment
   - Ports: 443 (HTTPS) or 80 (HTTP)

3. **Script available**
   ```bash
   ls -lh scripts/ops/knowledge_prod_smoke.sh
   # Must be executable (chmod +x)
   ```

### Optional

- **Bearer token** (if API requires authentication)
- **VPN/Bastion access** (for internal deployments)
- **kubectl/cloud CLI** (for container logs, if needed)

---

## Steps

### Quick Start (No Auth)

```bash
# Basic smoke test
BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh
```

### With Authentication

```bash
# Using token
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --token "${PROD_API_TOKEN}"
```

### Advanced Options

```bash
# Custom prefix (if API is not at /api/knowledge)
./scripts/ops/knowledge_prod_smoke.sh https://staging.example.com \
  --prefix /v1/knowledge

# Strict mode (501 counts as failure)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --strict

# With custom headers
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --header "X-Request-ID: drill-$(date +%s)" \
  --header "X-Environment: production"

# Verbose output (shows URLs and response previews)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --verbose

# Insecure (skip SSL verification, for dev/staging only)
./scripts/ops/knowledge_prod_smoke.sh https://staging.example.com \
  --insecure
```

### Via Environment Variables

```bash
export BASE_URL=https://prod.example.com
export TOKEN="${PROD_API_TOKEN}"
export PREFIX=/api/knowledge
export TIMEOUT=15
export VERBOSE=1

./scripts/ops/knowledge_prod_smoke.sh
```

---

## Expected Results

### Healthy Production (Default Config)

```
✅ PASS: Stats endpoint (200)
✅ PASS: Snippets list (200)
✅ PASS: Strategies list (200)
✅ PASS: Search (GET) (200)
✅ PASS: Write gating probe (403 - correctly blocked)

📊 Summary
✅ PASS:     5
🟡 DEGRADED: 0
❌ FAIL:     0

🎉 All checks passed
```

**Exit Code:** 0

### Degraded (Backend Unavailable, Non-Strict)

```
🟡 DEGRADED: Stats endpoint (501 - backend unavailable)
🟡 DEGRADED: Snippets list (501 - backend unavailable)
🟡 DEGRADED: Strategies list (501 - backend unavailable)
🟡 DEGRADED: Search (GET) (501 - backend unavailable)
✅ PASS: Write gating probe (403 - correctly blocked)

📊 Summary
✅ PASS:     1
🟡 DEGRADED: 4
❌ FAIL:     0

🎉 All checks passed
```

**Exit Code:** 0 (degraded is acceptable in non-strict mode)

### Degraded (Backend Unavailable, Strict Mode)

```
🟡 DEGRADED: Stats endpoint (501 - backend unavailable)
...

⚠️  Tests DEGRADED (strict mode enabled)
```

**Exit Code:** 2

### Failed (Unexpected Responses)

```
✅ PASS: Stats endpoint (200)
❌ FAIL: Snippets list (expected: 200 or 501, got: 500)
     Body: {"error": "Internal Server Error"}
...

❌ Tests FAILED
```

**Exit Code:** 1

---

## Failure Matrix

### Status Code Interpretation

| Code | Meaning | Action |
|------|---------|--------|
| **200** | Success | ✅ Expected for GET endpoints |
| **201** | Created | ⚠️  Write probe should NOT succeed in production |
| **401** | Unauthorized | Check token/auth configuration |
| **403** | Forbidden | ✅ Expected for write probe (gating working) |
| **404** | Not Found | Check PREFIX and endpoint paths |
| **405** | Method Not Allowed | API may use different HTTP method |
| **500** | Internal Server Error | ❌ Backend issue, check logs |
| **501** | Not Implemented | Graceful degradation (backend unavailable) |
| **502/503** | Bad Gateway/Unavailable | Infrastructure/proxy issue |
| **504** | Gateway Timeout | Network/timeout issue, try --timeout 30 |

### Common Failure Scenarios

#### 1. All Endpoints Return 401

**Cause:** Missing or invalid authentication

**Fix:**
```bash
# Check token is set
echo $PROD_API_TOKEN

# Test token manually
curl -H "Authorization: Bearer $PROD_API_TOKEN" \
  https://prod.example.com/api/knowledge/stats

# Run with correct token
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --token "${PROD_API_TOKEN}"
```

#### 2. All Endpoints Return 404

**Cause:** Wrong PREFIX or base URL

**Fix:**
```bash
# Check actual API path
curl -I https://prod.example.com/api/knowledge/stats
curl -I https://prod.example.com/v1/knowledge/stats

# Use correct prefix
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --prefix /v1/knowledge
```

#### 3. Write Probe Returns 200/201

**Cause:** ⚠️ **CRITICAL** — Write gating is NOT working in production!

**Immediate Actions:**
1. **Stop deployment** if this is a new release
2. Check configuration:
   ```bash
   # Expected in production:
   KNOWLEDGE_READONLY=true
   KNOWLEDGE_WEB_WRITE_ENABLED=false
   ```
3. Verify environment variables are loaded:
   ```bash
   kubectl exec -it <pod> -- env | grep KNOWLEDGE
   ```
4. Check application logs for startup config
5. **Rollback** if misconfigured

#### 4. All Endpoints Return 500

**Cause:** Backend application error

**Fix:**
```bash
# Check application logs
kubectl logs -f deployment/knowledge-api --tail=100

# Or for cloud deployments:
# AWS: aws logs tail /ecs/knowledge-api --follow
# GCP: gcloud logging read "resource.type=k8s_container" --limit 50

# Check if chromadb dependency is available
curl http://internal-chromadb:8000/api/v1/heartbeat
```

#### 5. Timeout Errors (000 status code)

**Cause:** Network timeout, slow responses

**Fix:**
```bash
# Increase timeout
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --timeout 30

# Check network connectivity
ping prod.example.com
traceroute prod.example.com

# Check if API is responding at all
time curl -I https://prod.example.com/api/health
```

---

## Rollback / Escalation

### When to Rollback

Rollback immediately if:

- ✅ Write probe returns 200/201 (writes are NOT blocked)
- ✅ Multiple 500 errors (application crashes)
- ✅ All endpoints return errors (total outage)

### Rollback Steps

```bash
# 1. Revert to previous deployment
kubectl rollout undo deployment/knowledge-api

# 2. Verify rollback
kubectl rollout status deployment/knowledge-api

# 3. Re-run smoke tests against reverted version
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com

# 4. Check logs for errors
kubectl logs -f deployment/knowledge-api
```

### Escalation Path

If smoke tests fail after rollback:

1. **Notify Platform Ops team** (Slack #platform-alerts)
2. **Create incident ticket** (include smoke test output)
3. **Check infrastructure:**
   - DNS resolution
   - Load balancer health
   - Database/ChromaDB connectivity
4. **Review recent changes:**
   - Config changes (env vars, secrets)
   - Infrastructure changes (networking, scaling)
   - Dependency updates (chromadb, uvicorn)

---

## Logs & Diagnostics

### Application Logs

```bash
# Kubernetes
kubectl logs -f deployment/knowledge-api --tail=100

# Docker Compose
docker-compose logs -f knowledge-api

# Systemd
journalctl -u knowledge-api -f
```

### Key Log Patterns

Look for:

```
# Startup config (should show READONLY=true in production)
KNOWLEDGE_READONLY: true
KNOWLEDGE_WEB_WRITE_ENABLED: false

# Access control logs
403 Forbidden: KNOWLEDGE_READONLY is enabled
403 Forbidden: KNOWLEDGE_WEB_WRITE_ENABLED is false

# Graceful degradation
501 Not Implemented: ChromaDB backend unavailable

# Errors (should NOT appear in production)
500 Internal Server Error
Uncaught exception in /api/knowledge/*
```

### Environment Variable Check

```bash
# Kubernetes
kubectl exec -it <pod> -- env | grep KNOWLEDGE

# Docker
docker exec <container> env | grep KNOWLEDGE

# Expected in production:
# KNOWLEDGE_READONLY=true
# KNOWLEDGE_WEB_WRITE_ENABLED=false
```

---

## Safety Notes

### Safe for Production

✅ **This drill is safe for production:**

- Only performs HTTP requests (no state changes)
- Write probe is designed to be blocked by API (returns 403)
- No data is persisted (even if write probe somehow succeeded)
- Read operations do not modify data
- Short timeout prevents hanging requests
- Can be run multiple times without side effects

### Not Safe If...

⚠️ **DO NOT run if:**

- API is known to be down (wastes time, use uptime check first)
- You don't have proper authentication (will just get 401s)
- Network access is restricted (VPN/bastion required)

⚠️ **STOP immediately if:**

- Write probe returns 200/201 (**writes are NOT blocked!**)
- You see data being created in logs
- Multiple 500 errors appear after drill starts

---

## Integration with CI/CD

### Pre-Deployment Gate

```yaml
# .github/workflows/deploy.yml
- name: Smoke Test Staging
  run: |
    ./scripts/ops/knowledge_prod_smoke.sh ${{ secrets.STAGING_URL }} \
      --token ${{ secrets.STAGING_TOKEN }} \
      --strict
  if: failure()
    run: |
      echo "❌ Staging smoke tests failed, blocking production deploy"
      exit 1
```

### Post-Deployment Verification

```yaml
- name: Deploy to Production
  run: kubectl apply -f k8s/production/

- name: Wait for Rollout
  run: kubectl rollout status deployment/knowledge-api --timeout=5m

- name: Production Smoke Test
  run: |
    ./scripts/ops/knowledge_prod_smoke.sh ${{ secrets.PROD_URL }} \
      --token ${{ secrets.PROD_TOKEN }}
```

### Scheduled Health Checks

```yaml
# .github/workflows/scheduled-smoke.yml
name: Scheduled Production Smoke

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Smoke Test
        run: |
          ./scripts/ops/knowledge_prod_smoke.sh ${{ secrets.PROD_URL }} \
            --token ${{ secrets.PROD_TOKEN }}
      - name: Alert on Failure
        if: failure()
        run: |
          # Send alert to Slack/PagerDuty/etc
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d '{"text":"🔥 Production smoke tests failed!"}'
```

---

## Quick Reference

### One-Liners

```bash
# Basic prod smoke
BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh

# With auth
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --token "$TOKEN"

# Strict mode (fail on 501)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --strict

# Verbose (show URLs and responses)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --verbose

# Custom timeout
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --timeout 30
```

### Exit Codes

- **0** = All checks passed (or degraded in non-strict mode)
- **1** = One or more checks failed
- **2** = Degraded in strict mode

### Help

```bash
./scripts/ops/knowledge_prod_smoke.sh --help
```

---

**Related Documentation:**
- [Knowledge API Implementation Summary](../KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md)
- [Knowledge API Smoke Tests](../KNOWLEDGE_API_SMOKE_TESTS.md)
- [Knowledge Smoke README](../../scripts/ops/KNOWLEDGE_SMOKE_README.md)
