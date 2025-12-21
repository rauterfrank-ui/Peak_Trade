"""
Peak_Trade Config File Watcher
===============================
File system watcher for automatic config hot-reload.

This module provides a background file watcher that monitors the config file
for changes and automatically triggers a reload when changes are detected.

Dependencies:
    - watchdog: File system event monitoring

Usage:
    from src.config.watcher import start_config_watcher
    from src.config.registry import get_registry
    
    registry = get_registry()
    registry.load(Path("config.toml"))
    
    # Start watching for changes
    observer = start_config_watcher(registry, Path("config.toml"))
    
    # Later, stop watching
    observer.stop()
    observer.join()
"""

import logging
from pathlib import Path
from typing import Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore
    FileSystemEventHandler = None  # type: ignore
    FileSystemEvent = None  # type: ignore

logger = logging.getLogger(__name__)


class ConfigWatcher(FileSystemEventHandler):
    """
    Watch config file for changes and auto-reload.
    
    This handler monitors a specific config file and triggers a reload
    when the file is modified. It handles failures gracefully by logging
    errors and continuing to use the previous config.
    
    Attributes:
        registry: ConfigRegistry instance to reload
        config_path: Path to the config file being watched
    """
    
    def __init__(self, registry, config_path: Path):
        """
        Initialize the config watcher.
        
        Args:
            registry: ConfigRegistry instance
            config_path: Path to config file to watch
        """
        super().__init__()
        self.registry = registry
        self.config_path = config_path.resolve()  # Use absolute path for comparison
        logger.info(f"ConfigWatcher initialized for {self.config_path}")
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events.
        
        Args:
            event: File system event
        """
        # Only react to modifications of our specific config file
        event_path = Path(event.src_path).resolve()
        
        if event.is_directory:
            return
        
        if event_path != self.config_path:
            return
        
        logger.info(f"Config file changed: {self.config_path}")
        
        # Attempt reload with automatic rollback on failure
        success = self.registry.reload(self.config_path)
        
        if not success:
            logger.warning(
                "Config reload failed, using previous version. "
                "Check logs for details."
            )
        else:
            logger.info("Config reloaded successfully")


def start_config_watcher(registry, config_path: Path) -> Optional[Observer]:
    """
    Start background thread watching config file.
    
    This function starts a watchdog Observer that monitors the config file's
    directory for changes. When the config file is modified, it automatically
    triggers a reload.
    
    Args:
        registry: ConfigRegistry instance
        config_path: Path to config file to watch
        
    Returns:
        Observer instance if watchdog is available, None otherwise
        
    Raises:
        ImportError: If watchdog is not installed
        
    Example:
        >>> from src.config.registry import get_registry
        >>> from src.config.watcher import start_config_watcher
        >>> 
        >>> registry = get_registry()
        >>> registry.load(Path("config.toml"))
        >>> 
        >>> observer = start_config_watcher(registry, Path("config.toml"))
        >>> # Config will now auto-reload on changes
        >>> 
        >>> # Later, to stop:
        >>> observer.stop()
        >>> observer.join()
    """
    if not WATCHDOG_AVAILABLE:
        logger.error(
            "Watchdog library not installed. "
            "Install with: pip install watchdog"
        )
        raise ImportError(
            "watchdog is required for config hot-reload. "
            "Install with: pip install watchdog"
        )
    
    config_path = config_path.resolve()
    
    if not config_path.exists():
        logger.warning(f"Config file does not exist: {config_path}")
        return None
    
    # Watch the directory containing the config file
    watch_dir = config_path.parent
    
    event_handler = ConfigWatcher(registry, config_path)
    observer = Observer()
    observer.schedule(event_handler, path=str(watch_dir), recursive=False)
    observer.start()
    
    logger.info(
        f"Config watcher started for {config_path} "
        f"(watching directory: {watch_dir})"
    )
    
    return observer


def is_watchdog_available() -> bool:
    """
    Check if watchdog library is available.
    
    Returns:
        True if watchdog is installed, False otherwise
    """
    return WATCHDOG_AVAILABLE
