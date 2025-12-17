"""
Structured Logging

JSON-basiertes strukturiertes Logging für einfache Auswertung.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON Formatter für strukturierte Logs"""

    def format(self, record: logging.LogRecord) -> str:
        """Formatiere Log-Record als JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Füge Exception-Info hinzu wenn vorhanden
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Füge extra fields hinzu
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class PlainFormatter(logging.Formatter):
    """Plain Text Formatter für lesbare Logs"""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)8s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_structured_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Konfiguriere strukturiertes Logging.
    
    Args:
        level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Wenn True, verwende JSON-Format
        log_file: Optional: Logge auch in Datei
    """
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Entferne existierende Handler
    root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(PlainFormatter())
    root_logger.addHandler(console_handler)
    
    # File Handler falls gewünscht
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())  # Immer JSON in Datei
        root_logger.addHandler(file_handler)


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.LoggerAdapter:
    """
    Hole Logger mit optionalen extra fields.
    
    Args:
        name: Logger-Name
        extra: Extra fields die allen Log-Nachrichten hinzugefügt werden
        
    Returns:
        LoggerAdapter mit extra fields
    """
    logger = logging.getLogger(name)
    if extra:
        return logging.LoggerAdapter(logger, extra)
    return logging.LoggerAdapter(logger, {})


# Default Setup bei Import
if not logging.getLogger().handlers:
    setup_structured_logging(level="INFO", json_format=False)
