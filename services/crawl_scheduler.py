import subprocess
import sys
import threading
import time
from pathlib import Path

from services.settings_service import get_settings


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def trigger_crawl():
    return subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


class CrawlScheduler:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_run = 0.0
        self._crawl_process = None
        self._process_lock = threading.Lock()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="crawl-scheduler", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None

    def _run(self):
        while not self._stop_event.is_set():
            try:
                settings = get_settings()
                interval_seconds = settings["crawl_interval_minutes"] * 60
                with self._process_lock:
                    process_running = self._crawl_process is not None and self._crawl_process.poll() is None
                if settings["crawl_enabled"] and not process_running and time.time() - self._last_run >= interval_seconds:
                    with self._process_lock:
                        self._crawl_process = trigger_crawl()
                    self._last_run = time.time()
            except Exception as error:
                print(f"CRAWL SCHEDULER ERROR: {error}")
            if self._stop_event.wait(15):
                break


crawl_scheduler = CrawlScheduler()
