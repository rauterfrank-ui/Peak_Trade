"""
Structured Logger
==================

Provides JSON-based structured logging for better log analysis and monitoring.

Usage:
    from src.infra.monitoring import get_structured_logger
    
    logger = get_structured_logger(__name__)
    logger.info("Order executed", extra={
        "order_id": "12345",
        "symbol": "BTC/EUR",
        "quantity": 0.1,
    })
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "__dict__"):
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in logging.LogRecord.__dict__ and k != "message"
            }
            if extra:
                log_data["extra"] = extra
        
        return json.dumps(log_data)


def configure_logging(
    level: str = "INFO",
    structured: bool = True,
    output_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON logging
        output_file: Optional file to write logs to
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if output_file:
        file_handler = logging.FileHandler(output_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        
        root_logger.addHandler(file_handler)


def get_structured_logger(name: str) -> logging.Logger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance configured for structured logging
    """
    logger = logging.getLogger(name)
    
    # Ensure at least one handler exists
    if not logger.handlers and not logging.getLogger().handlers:
        configure_logging(structured=True)
    
    return logger
