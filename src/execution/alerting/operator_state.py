"""
Operator State - Phase 16J

State management for operator actions (ACK, SNOOZE, RESOLVE).
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class OperatorAction:
    """Record of an operator action."""
    
    action: str  # "ack" | "snooze" | "resolve"
    target_type: str  # "dedupe_key" | "rule_id"
    target_value: str
    timestamp: datetime
    expires_at: Optional[datetime] = None
    operator: str = "system"
    reason: Optional[str] = None


class OperatorState:
    """
    Operator state store (file-backed JSON).
    
    Features:
    - ACK dedupe_keys (suppress non-critical alerts)
    - SNOOZE rule_ids (suppress all alerts from rule)
    - TTL support (expires_at)
    - Atomic file writes
    - Auto-cleanup of expired entries
    """
    
    def __init__(
        self,
        state_path: Path,
        enabled: bool = False,
        suppress_critical_on_ack: bool = False,
    ):
        """
        Initialize operator state.
        
        Args:
            state_path: Path to state JSON file
            enabled: Whether operator actions are enabled
            suppress_critical_on_ack: Whether to suppress CRITICAL alerts when acked
        """
        self.state_path = state_path
        self.enabled = enabled
        self.suppress_critical_on_ack = suppress_critical_on_ack
        
        # In-memory state
        self._acked_keys: Dict[str, OperatorAction] = {}
        self._snoozed_rules: Dict[str, OperatorAction] = {}
        
        # Load from file
        if enabled and state_path.exists():
            self._load()
    
    def ack(
        self,
        dedupe_key: str,
        ttl_seconds: Optional[int] = None,
        operator: str = "system",
        reason: Optional[str] = None,
    ) -> bool:
        """
        Acknowledge an alert (suppress future alerts with same dedupe_key).
        
        Args:
            dedupe_key: Alert dedupe key to acknowledge
            ttl_seconds: TTL in seconds (None = permanent)
            operator: Operator who acked
            reason: Optional reason
        
        Returns:
            True if ack succeeded, False otherwise
        """
        if not self.enabled:
            logger.warning("Operator actions disabled, ack ignored")
            return False
        
        now = datetime.now(timezone.utc)
        expires_at = None
        
        if ttl_seconds:
            expires_at = datetime.fromtimestamp(
                now.timestamp() + ttl_seconds,
                tz=timezone.utc,
            )
        
        action = OperatorAction(
            action="ack",
            target_type="dedupe_key",
            target_value=dedupe_key,
            timestamp=now,
            expires_at=expires_at,
            operator=operator,
            reason=reason,
        )
        
        self._acked_keys[dedupe_key] = action
        
        return self._save()
    
    def snooze(
        self,
        rule_id: str,
        ttl_seconds: int,
        operator: str = "system",
        reason: Optional[str] = None,
    ) -> bool:
        """
        Snooze a rule (suppress all alerts from rule for TTL).
        
        Args:
            rule_id: Rule ID to snooze
            ttl_seconds: TTL in seconds (required)
            operator: Operator who snoozed
            reason: Optional reason
        
        Returns:
            True if snooze succeeded, False otherwise
        """
        if not self.enabled:
            logger.warning("Operator actions disabled, snooze ignored")
            return False
        
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(
            now.timestamp() + ttl_seconds,
            tz=timezone.utc,
        )
        
        action = OperatorAction(
            action="snooze",
            target_type="rule_id",
            target_value=rule_id,
            timestamp=now,
            expires_at=expires_at,
            operator=operator,
            reason=reason,
        )
        
        self._snoozed_rules[rule_id] = action
        
        return self._save()
    
    def unsnooze(self, rule_id: str) -> bool:
        """
        Remove snooze for a rule.
        
        Args:
            rule_id: Rule ID to unsnooze
        
        Returns:
            True if unsnooze succeeded, False otherwise
        """
        if not self.enabled:
            return False
        
        if rule_id in self._snoozed_rules:
            del self._snoozed_rules[rule_id]
            return self._save()
        
        return True
    
    def is_acked(self, dedupe_key: str, severity: str = "warn") -> bool:
        """
        Check if dedupe_key is acknowledged.
        
        Args:
            dedupe_key: Alert dedupe key
            severity: Alert severity (for CRITICAL check)
        
        Returns:
            True if acknowledged and not expired, False otherwise
        """
        if not self.enabled:
            return False
        
        # CRITICAL alerts bypass ACK unless explicitly configured
        if severity == "critical" and not self.suppress_critical_on_ack:
            return False
        
        action = self._acked_keys.get(dedupe_key)
        
        if not action:
            return False
        
        # Check expiry
        if action.expires_at:
            now = datetime.now(timezone.utc)
            if now >= action.expires_at:
                # Expired - clean up
                del self._acked_keys[dedupe_key]
                self._save()
                return False
        
        return True
    
    def is_snoozed(self, rule_id: str) -> bool:
        """
        Check if rule is snoozed.
        
        Args:
            rule_id: Rule ID
        
        Returns:
            True if snoozed and not expired, False otherwise
        """
        if not self.enabled:
            return False
        
        action = self._snoozed_rules.get(rule_id)
        
        if not action:
            return False
        
        # Check expiry
        if action.expires_at:
            now = datetime.now(timezone.utc)
            if now >= action.expires_at:
                # Expired - clean up
                del self._snoozed_rules[rule_id]
                self._save()
                return False
        
        return True
    
    def get_acked_keys(self) -> List[OperatorAction]:
        """Get all acknowledged keys."""
        self._cleanup_expired()
        return list(self._acked_keys.values())
    
    def get_snoozed_rules(self) -> List[OperatorAction]:
        """Get all snoozed rules."""
        self._cleanup_expired()
        return list(self._snoozed_rules.values())
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now(timezone.utc)
        
        # Cleanup acked keys
        expired_keys = [
            key
            for key, action in self._acked_keys.items()
            if action.expires_at and now >= action.expires_at
        ]
        
        for key in expired_keys:
            del self._acked_keys[key]
        
        # Cleanup snoozed rules
        expired_rules = [
            rule_id
            for rule_id, action in self._snoozed_rules.items()
            if action.expires_at and now >= action.expires_at
        ]
        
        for rule_id in expired_rules:
            del self._snoozed_rules[rule_id]
        
        if expired_keys or expired_rules:
            self._save()
    
    def _load(self):
        """Load state from file."""
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Load acked keys
            for key, action_data in data.get("acked_keys", {}).items():
                self._acked_keys[key] = self._action_from_dict(action_data)
            
            # Load snoozed rules
            for rule_id, action_data in data.get("snoozed_rules", {}).items():
                self._snoozed_rules[rule_id] = self._action_from_dict(action_data)
            
            logger.info(f"Loaded operator state from {self.state_path}")
        
        except Exception as e:
            logger.error(f"Failed to load operator state: {e}")
    
    def _save(self) -> bool:
        """Save state to file (atomic)."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build data
            data = {
                "acked_keys": {
                    key: self._action_to_dict(action)
                    for key, action in self._acked_keys.items()
                },
                "snoozed_rules": {
                    rule_id: self._action_to_dict(action)
                    for rule_id, action in self._snoozed_rules.items()
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            
            # Atomic write (temp file + rename)
            temp_path = self.state_path.with_suffix(".tmp")
            
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            temp_path.replace(self.state_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save operator state: {e}")
            return False
    
    def _action_to_dict(self, action: OperatorAction) -> dict:
        """Convert action to dict."""
        return {
            "action": action.action,
            "target_type": action.target_type,
            "target_value": action.target_value,
            "timestamp": action.timestamp.isoformat(),
            "expires_at": action.expires_at.isoformat() if action.expires_at else None,
            "operator": action.operator,
            "reason": action.reason,
        }
    
    def _action_from_dict(self, data: dict) -> OperatorAction:
        """Load action from dict."""
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00")
            )
        
        return OperatorAction(
            action=data["action"],
            target_type=data["target_type"],
            target_value=data["target_value"],
            timestamp=timestamp,
            expires_at=expires_at,
            operator=data.get("operator", "system"),
            reason=data.get("reason"),
        )
