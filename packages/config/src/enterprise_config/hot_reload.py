"""
Hot reload functionality for configuration files.
"""

import os
import time
from pathlib import Path
from typing import Callable, List, Optional
from threading import Thread, Event

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileModifiedEvent = None
    FileCreatedEvent = None

from .exceptions import HotReloadError


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration files."""

    def __init__(
        self,
        callback: Callable[[str], None],
        debounce_seconds: float = 1.0,
        file_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize file handler.

        Args:
            callback: Function to call when files change
            debounce_seconds: Debounce time to prevent multiple rapid calls
            file_patterns: List of file patterns to watch (e.g., ['*.yaml', '*.json'])
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.file_patterns = file_patterns or ['*.yaml', '*.yml', '*.json', '*.toml']
        self.last_modified = {}

    def _should_handle_file(self, file_path: str) -> bool:
        """Check if file should be handled based on patterns."""
        if not self.file_patterns:
            return True

        file_name = os.path.basename(file_path)
        for pattern in self.file_patterns:
            if self._match_pattern(file_name, pattern):
                return True
        return False

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names."""
        if pattern == '*':
            return True
        if pattern.startswith('*.'):
            extension = pattern[2:]
            return filename.endswith(f'.{extension}')
        return filename == pattern

    def _is_debounced(self, file_path: str) -> bool:
        """Check if file change should be debounced."""
        now = time.time()
        last_time = self.last_modified.get(file_path, 0)
        
        if now - last_time < self.debounce_seconds:
            return True
            
        self.last_modified[file_path] = now
        return False

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        
        if not self._should_handle_file(file_path):
            return
            
        if self._is_debounced(file_path):
            return

        try:
            self.callback(file_path)
        except Exception as e:
            print(f"Error in hot reload callback for {file_path}: {e}")

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        # Treat creation as modification
        self.on_modified(event)


class HotReloadWatcher:
    """
    Hot reload watcher for configuration files.
    
    Monitors configuration directories for changes and triggers callbacks.
    Falls back to polling if watchdog is not available.
    """

    def __init__(
        self,
        watch_paths: List[str],
        callback: Callable[[str], None],
        debounce_seconds: float = 1.0,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
        use_polling: bool = False,
    ):
        """
        Initialize hot reload watcher.

        Args:
            watch_paths: List of paths to watch
            callback: Function to call when files change
            debounce_seconds: Debounce time for rapid changes
            recursive: Whether to watch subdirectories
            file_patterns: File patterns to watch
            use_polling: Force use of polling instead of native watching
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.recursive = recursive
        self.file_patterns = file_patterns
        self.use_polling = use_polling or not WATCHDOG_AVAILABLE

        self.observer: Optional[Observer] = None
        self.polling_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.is_running = False

        # For polling fallback
        self.file_mtimes = {}

    def start(self) -> None:
        """Start watching for file changes."""
        if self.is_running:
            return

        try:
            if self.use_polling:
                self._start_polling()
            else:
                self._start_watching()
            
            self.is_running = True
            
        except Exception as e:
            raise HotReloadError(
                f"Failed to start hot reload watcher: {str(e)}",
                watcher_error=e,
            )

    def _start_watching(self) -> None:
        """Start file system watching using watchdog."""
        if not WATCHDOG_AVAILABLE:
            raise HotReloadError("Watchdog package not available for file watching")

        self.observer = Observer()
        event_handler = ConfigFileHandler(
            callback=self.callback,
            debounce_seconds=self.debounce_seconds,
            file_patterns=self.file_patterns,
        )

        for watch_path in self.watch_paths:
            if watch_path.exists():
                self.observer.schedule(
                    event_handler,
                    str(watch_path),
                    recursive=self.recursive,
                )

        self.observer.start()

    def _start_polling(self) -> None:
        """Start polling-based file watching."""
        self.stop_event.clear()
        self.polling_thread = Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()

    def _polling_loop(self) -> None:
        """Polling loop for file changes."""
        while not self.stop_event.is_set():
            try:
                self._check_file_changes()
                time.sleep(self.debounce_seconds)
            except Exception as e:
                print(f"Error in polling loop: {e}")

    def _check_file_changes(self) -> None:
        """Check for file changes using modification times."""
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            if watch_path.is_file():
                self._check_single_file(watch_path)
            else:
                self._check_directory(watch_path)

    def _check_single_file(self, file_path: Path) -> None:
        """Check single file for changes."""
        try:
            current_mtime = file_path.stat().st_mtime
            file_key = str(file_path)
            
            if file_key in self.file_mtimes:
                if current_mtime > self.file_mtimes[file_key]:
                    self.file_mtimes[file_key] = current_mtime
                    self.callback(file_key)
            else:
                self.file_mtimes[file_key] = current_mtime
                
        except (OSError, IOError):
            # File might have been deleted
            file_key = str(file_path)
            if file_key in self.file_mtimes:
                del self.file_mtimes[file_key]

    def _check_directory(self, dir_path: Path) -> None:
        """Check directory for file changes."""
        try:
            if self.recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in dir_path.glob(pattern):
                if file_path.is_file() and self._should_watch_file(file_path):
                    self._check_single_file(file_path)
                    
        except (OSError, IOError) as e:
            print(f"Error checking directory {dir_path}: {e}")

    def _should_watch_file(self, file_path: Path) -> bool:
        """Check if file should be watched based on patterns."""
        if not self.file_patterns:
            return True

        file_name = file_path.name
        for pattern in self.file_patterns:
            if pattern == '*':
                return True
            if pattern.startswith('*.'):
                extension = pattern[2:]
                if file_name.endswith(f'.{extension}'):
                    return True
            elif file_name == pattern:
                return True
                
        return False

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self.is_running:
            return

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None

            if self.polling_thread:
                self.stop_event.set()
                self.polling_thread.join(timeout=5.0)
                self.polling_thread = None

            self.is_running = False
            
        except Exception as e:
            print(f"Error stopping hot reload watcher: {e}")

    def add_watch_path(self, path: str) -> None:
        """
        Add new path to watch.

        Args:
            path: Path to add to watching
        """
        watch_path = Path(path)
        if watch_path not in self.watch_paths:
            self.watch_paths.append(watch_path)
            
            # If already running, add to observer
            if self.is_running and self.observer and watch_path.exists():
                event_handler = ConfigFileHandler(
                    callback=self.callback,
                    debounce_seconds=self.debounce_seconds,
                    file_patterns=self.file_patterns,
                )
                self.observer.schedule(
                    event_handler,
                    str(watch_path),
                    recursive=self.recursive,
                )

    def remove_watch_path(self, path: str) -> None:
        """
        Remove path from watching.

        Args:
            path: Path to remove from watching
        """
        watch_path = Path(path)
        if watch_path in self.watch_paths:
            self.watch_paths.remove(watch_path)
            
            # Clean up file modification times
            path_str = str(watch_path)
            keys_to_remove = [
                key for key in self.file_mtimes.keys()
                if key.startswith(path_str)
            ]
            for key in keys_to_remove:
                del self.file_mtimes[key]

    def get_watched_files(self) -> List[str]:
        """
        Get list of currently watched files.

        Returns:
            List of file paths being watched
        """
        watched_files = []
        
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue
                
            if watch_path.is_file():
                if self._should_watch_file(watch_path):
                    watched_files.append(str(watch_path))
            else:
                try:
                    if self.recursive:
                        pattern = "**/*"
                    else:
                        pattern = "*"
                        
                    for file_path in watch_path.glob(pattern):
                        if file_path.is_file() and self._should_watch_file(file_path):
                            watched_files.append(str(file_path))
                            
                except (OSError, IOError):
                    continue
                    
        return sorted(watched_files)

    def is_watching(self) -> bool:
        """Check if watcher is currently running."""
        return self.is_running

    def get_status(self) -> dict:
        """
        Get watcher status information.

        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "watch_paths": [str(p) for p in self.watch_paths],
            "recursive": self.recursive,
            "file_patterns": self.file_patterns,
            "use_polling": self.use_polling,
            "debounce_seconds": self.debounce_seconds,
            "watched_files_count": len(self.get_watched_files()),
            "watchdog_available": WATCHDOG_AVAILABLE,
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'is_running') and self.is_running:
            self.stop()