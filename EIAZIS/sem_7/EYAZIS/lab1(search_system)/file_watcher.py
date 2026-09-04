import os
import time
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from search_service import SearchService

logger = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    def __init__(self, watch_directory, search_service, debounce_seconds=2.0):
        self.watch_directory = watch_directory
        self.search_service = search_service
        self.observer = Observer()
        self.debounce_timers = {}
        self.debounce_seconds = debounce_seconds
        self.processing_files = set()
        self.processing_lock = threading.Lock()
        self.timer_lock = threading.Lock()
        self.observer_lock = threading.Lock()  # Lock for observer operations

    def start(self):
        """Запуск мониторинга"""
        with self.observer_lock:
            self.observer.schedule(self, self.watch_directory, recursive=True)
            self.observer.start()
            logger.info(f"Мониторинг запущен для директории: {self.watch_directory}")

    def stop(self):
        """Остановка мониторинга"""
        with self.observer_lock:
            if self.observer:
                self.observer.stop()
                self.observer.join()

        with self.timer_lock:
            for timer in self.debounce_timers.values():
                timer.cancel()
            self.debounce_timers.clear()

        logger.info("Мониторинг остановлен")

    def schedule_indexing(self, file_path):
        """Debounce file indexing to handle rapid saves"""
        # Normalize file path for consistent handling
        file_path = os.path.normpath(file_path)

        with self.timer_lock:
            # Cancel existing timer for this file
            if file_path in self.debounce_timers:
                logger.debug(f"Cancelling existing timer for: {file_path}")
                self.debounce_timers[file_path].cancel()
                del self.debounce_timers[file_path]

            # Schedule new indexing
            logger.debug(f"Scheduling new timer for: {file_path}")
            timer = threading.Timer(self.debounce_seconds, self._perform_indexing, [file_path])
            self.debounce_timers[file_path] = timer
            timer.start()

    def _perform_indexing(self, file_path):
        """Actual indexing implementation with proper locking"""
        file_path = os.path.normpath(file_path)

        # Clean up timer first
        with self.timer_lock:
            if file_path in self.debounce_timers:
                del self.debounce_timers[file_path]

        # Check if already processing this file
        with self.processing_lock:
            if file_path in self.processing_files:
                logger.info(f"Already processing {file_path}, skipping duplicate")
                return
            self.processing_files.add(file_path)

        try:
            # Check if file still exists
            if not os.path.exists(file_path):
                logger.info(f"File no longer exists, skipping indexing: {file_path}")
                return

            logger.info(f"Starting indexing: {file_path}")
            success = self.search_service.index_file(file_path)
            if success:
                logger.info(f"Successfully indexed: {file_path}")
            else:
                logger.error(f"Failed to index: {file_path}")

        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
        finally:
            with self.processing_lock:
                self.processing_files.discard(file_path)

    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self._is_text_file(event.src_path):
            logger.info(f"New file detected: {event.src_path}")
            self.schedule_indexing(event.src_path)

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self._is_text_file(event.src_path):
            logger.info(f"File modified: {event.src_path}")
            self.schedule_indexing(event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and self._is_text_file(event.src_path):
            file_path = os.path.normpath(event.src_path)

            # Cancel any pending indexing
            with self.timer_lock:
                if file_path in self.debounce_timers:
                    logger.debug(f"Cancelling timer for deleted file: {file_path}")
                    self.debounce_timers[file_path].cancel()
                    del self.debounce_timers[file_path]

            # Remove from processing set
            with self.processing_lock:
                self.processing_files.discard(file_path)

            logger.info(f"File deleted: {file_path}")
            # Use a separate thread for deletion to avoid blocking
            threading.Thread(target=self._perform_deletion, args=(file_path,), daemon=True).start()

    def _perform_deletion(self, file_path):
        """Perform document deletion in a separate thread"""
        try:
            success = self.search_service.remove_document(file_path)
            if success:
                logger.info(f"Successfully removed document: {file_path}")
            else:
                logger.warning(f"Document not found or already removed: {file_path}")
        except Exception as e:
            logger.error(f"Error removing document {file_path}: {e}")

    def _is_text_file(self, file_path):
        """Check if file is a text file we should process"""
        filename = os.path.basename(file_path)
        return (filename.endswith('.txt') and
                not filename.endswith('.tmp') and
                not filename.startswith('.') and
                not filename.startswith('~'))  # Ignore temporary files

    def scan_existing_files(self):
        """Scan existing files on startup"""
        logger.info("Scanning existing files...")
        files_found = 0
        files_indexed = 0

        for root, dirs, files in os.walk(self.watch_directory):
            for file in files:
                if self._is_text_file(file):
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        files_found += 1
                        try:
                            logger.info(f"Indexing existing file: {file_path}")
                            success = self.search_service.index_file(file_path)
                            if success:
                                files_indexed += 1
                            else:
                                logger.error(f"Failed to index existing file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error indexing existing file {file_path}: {e}")

        logger.info(f"File scan completed: {files_found} files found, {files_indexed} files indexed")