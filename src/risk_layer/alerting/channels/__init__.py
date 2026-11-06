"""
Alert Channels
==============

Multi-channel alerting infrastructure with severity-based routing.

Phase 2 Components:
- AlertChannel: Abstract base class for all channels
- ChannelRouter: Routes alerts based on severity and config
- Channels: Console, File, Email, Slack, Telegram, Webhook

Usage:
    from src.risk_layer.alerting.channels import (
        ChannelRouter,
        ConsoleChannel,
        FileChannel,
        EmailChannel,
        SlackChannel,
        TelegramChannel,
        WebhookChannel,
    )
"""

from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)
from src.risk_layer.alerting.channels.channel_router import ChannelRouter
from src.risk_layer.alerting.channels.console_channel import ConsoleChannel
from src.risk_layer.alerting.channels.email_channel import EmailChannel
from src.risk_layer.alerting.channels.file_channel import FileChannel
from src.risk_layer.alerting.channels.slack_channel import SlackChannel
from src.risk_layer.alerting.channels.telegram_channel import TelegramChannel
from src.risk_layer.alerting.channels.webhook_channel import WebhookChannel

__all__ = [
    "AlertChannel",
    "ChannelHealth",
    "ChannelStatus",
    "ChannelRouter",
    "ConsoleChannel",
    "EmailChannel",
    "FileChannel",
    "SlackChannel",
    "TelegramChannel",
    "WebhookChannel",
]
