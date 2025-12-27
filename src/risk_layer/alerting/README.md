# Risk-Layer Multi-Channel Alerting System

Production-grade alert delivery across redundant channels with safe defaults and full mocking.

## Features

- **Multiple Notification Channels**: Console, File, Email, Slack, Telegram, Webhook
- **Severity-Based Routing**: Route alerts to different channels based on severity (INFO, WARN, CRITICAL)
- **Failover Support**: Automatic failover to backup channels when primary channels fail
- **Async Dispatch**: Parallel delivery to multiple channels for low-latency alerting
- **Safe Defaults**: External channels disabled by default, require explicit configuration
- **Environment-Based Config**: Secrets managed via environment variables (no hardcoded credentials)
- **Comprehensive Testing**: 52+ tests with full mocking (urllib, smtplib, file I/O)

## Quick Start

### Basic Usage

```python
from src.risk_layer.alerting import (
    AlertDispatcher,
    AlertEvent,
    AlertSeverity,
    ConsoleChannel,
    FileChannel,
)

# Create channels
console = ConsoleChannel()
file_channel = FileChannel(file_path="/var/log/risk-alerts.jsonl")

# Create dispatcher
dispatcher = AlertDispatcher(channels=[console, file_channel])

# Send alert
alert = AlertEvent(
    source="risk_gate",
    severity=AlertSeverity.CRITICAL,
    title="Position Limit Exceeded",
    body="Portfolio exposure exceeds configured limit",
    labels={"portfolio": "main", "limit_pct": "105"},
)

results = dispatcher.dispatch(alert)
print(f"Dispatch results: {results}")
```

### Custom Routing Matrix

```python
from src.risk_layer.alerting import AlertSeverity

# Define custom routing based on severity
custom_routing = {
    AlertSeverity.INFO: ["console", "file"],
    AlertSeverity.WARN: ["console", "file", "slack"],
    AlertSeverity.CRITICAL: ["console", "file", "email", "slack", "telegram"],
}

dispatcher = AlertDispatcher(
    channels=[console, file_channel, slack, email],
    routing_matrix=custom_routing,
)
```

## Notification Channels

### Console Channel

Always enabled, prints formatted alerts to stdout with color coding.

```python
from src.risk_layer.alerting.channels import ConsoleChannel

console = ConsoleChannel(color=True)  # Enable ANSI color codes
```

**Features:**
- Emoji indicators for severity
- Color-coded output (cyan/yellow/red)
- Always succeeds (no external dependencies)

---

### File Channel

Appends alerts to JSONL file for persistent logging. Disabled by default.

```python
from src.risk_layer.alerting.channels import FileChannel

# Option 1: Direct configuration
file_channel = FileChannel(file_path="/var/log/risk-alerts.jsonl")

# Option 2: Environment variable
# Set RISK_ALERTS_FILE=/var/log/risk-alerts.jsonl
file_channel = FileChannel()
```

**Environment Variables:**
- `RISK_ALERTS_FILE`: Path to alerts file

**Features:**
- JSONL format (one alert per line)
- Automatic directory creation
- Append-only (safe for concurrent writes)

---

### Email Channel

Sends alerts via SMTP. Disabled by default.

```python
from src.risk_layer.alerting.channels import EmailChannel

email = EmailChannel(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="alerts@example.com",
    smtp_password="app-specific-password",
    from_email="alerts@example.com",
    to_emails=["admin@example.com", "ops@example.com"],
)
```

**Environment Variables:**
- `RISK_ALERTS_SMTP_HOST`: SMTP server host
- `RISK_ALERTS_SMTP_PORT`: SMTP server port (default: 587)
- `RISK_ALERTS_SMTP_USER`: SMTP username
- `RISK_ALERTS_SMTP_PASSWORD`: SMTP password
- `RISK_ALERTS_EMAIL_FROM`: From email address
- `RISK_ALERTS_EMAIL_TO`: Comma-separated recipient emails

**Features:**
- HTML email formatting
- Color-coded by severity
- Multiple recipients
- TLS/STARTTLS support

---

### Slack Channel

Sends alerts to Slack via webhook. Disabled by default.

```python
from src.risk_layer.alerting.channels import SlackChannel

slack = SlackChannel(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)
```

**Environment Variables:**
- `RISK_ALERTS_SLACK_WEBHOOK`: Slack webhook URL

**Features:**
- Rich message formatting with attachments
- Color-coded by severity
- Timestamp and source fields
- Emoji indicators

**Setup:**
1. Create Slack App: https://api.slack.com/apps
2. Add Incoming Webhooks
3. Copy webhook URL to environment variable

---

### Telegram Channel

Sends alerts to Telegram via Bot API. Disabled by default.

```python
from src.risk_layer.alerting.channels import TelegramChannel

telegram = TelegramChannel(
    bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    chat_id="123456789",
)
```

**Environment Variables:**
- `RISK_ALERTS_TELEGRAM_BOT_TOKEN`: Telegram bot token
- `RISK_ALERTS_TELEGRAM_CHAT_ID`: Telegram chat ID

**Features:**
- Markdown formatting
- Emoji indicators
- Labels and metadata display

**Setup:**
1. Create bot with @BotFather
2. Get bot token
3. Get chat ID (send message to bot, call getUpdates API)

---

### Webhook Channel

Sends alerts as JSON POST to generic webhook. Disabled by default.

```python
from src.risk_layer.alerting.channels import WebhookChannel

webhook = WebhookChannel(
    webhook_url="https://your-webhook.example.com/alerts",
    timeout=10,
)
```

**Environment Variables:**
- `RISK_ALERTS_WEBHOOK_URL`: Webhook URL

**Features:**
- JSON payload with full alert data
- Configurable timeout
- Standard HTTP POST

**Payload Format:**
```json
{
  "id": "uuid",
  "timestamp_utc": "2025-12-27T10:00:00+00:00",
  "source": "risk_gate",
  "severity": "critical",
  "title": "Alert Title",
  "body": "Alert body text",
  "labels": {"key": "value"},
  "metadata": {}
}
```

## Advanced Features

### Async Dispatch

Dispatch to multiple channels in parallel using thread pool:

```python
results = dispatcher.dispatch_async(alert)
```

**Benefits:**
- Low-latency alerting
- Parallel channel delivery
- Timeout protection (30s per channel)

---

### Failover

Automatic failover to backup channels when primary channels fail:

```python
dispatcher = AlertDispatcher(
    channels=[slack, email, console],
    routing_matrix={
        AlertSeverity.CRITICAL: ["slack", "email"],
    },
    enable_failover=True,  # Enable failover
)
```

**Fallback Order:**
1. console
2. file
3. slack
4. email
5. telegram
6. webhook

---

### Custom Channel Implementation

Implement the `NotificationChannel` protocol:

```python
from src.risk_layer.alerting.channels import NotificationChannel
from src.risk_layer.alerting.models import AlertEvent

class MyCustomChannel:
    @property
    def enabled(self) -> bool:
        """Check if channel is enabled."""
        return True  # Your logic here

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to channel."""
        # Your implementation here
        return True  # Return success status
```

## Testing

Run the comprehensive test suite:

```bash
# Run all alerting tests
pytest tests/risk_layer/alerting -q

# Run specific test file
pytest tests/risk_layer/alerting/test_channels.py -v

# Run with coverage
pytest tests/risk_layer/alerting --cov=src.risk_layer.alerting
```

**Test Coverage:**
- 52+ tests covering all channels, dispatcher, and models
- Full mocking of external dependencies (urllib, smtplib)
- Temporary file paths for file I/O tests
- Environment variable mocking with pytest-monkeypatch

## Demo

Run the demo script to see all features in action:

```bash
PYTHONPATH=/path/to/Peak_Trade python3 scripts/demo_risk_alerting.py
```

## Security & Best Practices

### ✅ Safe Defaults
- External channels disabled by default
- No hardcoded credentials
- Environment variable configuration

### ✅ Secret Management
```bash
# Export secrets as environment variables
export RISK_ALERTS_SMTP_PASSWORD="your-secret-password"
export RISK_ALERTS_SLACK_WEBHOOK="https://hooks.slack.com/services/xxx"
export RISK_ALERTS_TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."

# Use secret management tools (recommended)
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

### ✅ Error Handling
- All channels catch and log exceptions
- Failed sends return `False` (don't crash)
- Failover ensures at least one channel succeeds

### ✅ Production Readiness
- Async dispatch for low latency
- Timeout protection (10-30s per channel)
- Thread-safe execution
- Deterministic behavior

## Integration Examples

### With Risk Gate

```python
from src.risk_layer import RiskGate
from src.risk_layer.alerting import AlertDispatcher, AlertEvent, AlertSeverity

# Create alerting dispatcher
dispatcher = AlertDispatcher(channels=[console, slack])

# Risk gate validation
result = risk_gate.validate(order)

if result.decision.severity == "BLOCK":
    # Send critical alert
    alert = AlertEvent(
        source="risk_gate",
        severity=AlertSeverity.CRITICAL,
        title="Order Blocked by Risk Gate",
        body=result.decision.reason,
        labels={"order_id": order.id},
        metadata={"violations": [v.code for v in result.decision.violations]},
    )
    dispatcher.dispatch(alert)
```

### With VaR Gate

```python
from src.risk_layer import VaRGate
from src.risk_layer.alerting import AlertEvent, AlertSeverity

var_gate = VaRGate(threshold=0.05)
result = var_gate.check(portfolio)

if result.var > result.threshold * 0.9:
    # Warn when approaching threshold
    alert = AlertEvent(
        source="var_gate",
        severity=AlertSeverity.WARN,
        title="VaR Approaching Threshold",
        body=f"Portfolio VaR at {result.var:.4f} (threshold: {result.threshold})",
        metadata={"var": result.var, "threshold": result.threshold},
    )
    dispatcher.dispatch(alert)
```

## Architecture

```
src/risk_layer/alerting/
├── __init__.py              # Main exports
├── models.py                # AlertEvent, AlertSeverity
├── dispatcher.py            # AlertDispatcher with routing + failover
└── channels/
    ├── __init__.py          # Channel exports
    ├── base.py              # NotificationChannel protocol
    ├── console.py           # Console channel (always enabled)
    ├── file.py              # File channel (JSONL)
    ├── email.py             # Email channel (SMTP)
    ├── slack.py             # Slack channel (webhook)
    ├── telegram.py          # Telegram channel (Bot API)
    └── webhook.py           # Generic webhook channel

tests/risk_layer/alerting/
├── __init__.py
├── test_models.py           # Model tests
├── test_channels.py         # Channel tests (with mocking)
└── test_dispatcher.py       # Dispatcher tests
```

## References

- **Risk-Layer Production Alerting Roadmap**: Phase 3 - Notification Channels
- **Execution Alerting**: Similar system in `src/execution/alerting/` for execution-layer alerts
- **Phase 16I/16J**: Telemetry alerting with lifecycle management

## License

Proprietary - Part of Peak_Trade trading framework.
