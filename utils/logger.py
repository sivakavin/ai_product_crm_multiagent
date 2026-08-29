"""
Central, config-driven logging for the CRM multi-agent app.

Everything tunable — level, directory, retention, console/color — comes from
``config.settings`` (backed by ``.env``). Nothing is hardcoded here except the
line *format*, which is intentionally kept in code so every log line stays
aligned and readable.

Usage (one line per module):

    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("something happened")

The first ``get_logger`` call configures logging exactly once and, automatically:
  * creates the log directory,
  * writes to a dated file   <log_dir>/<base>_<YYYY-MM-DD>.log,
  * mirrors to the console (optionally colored) when enabled,
  * deletes log files older than LOG_RETENTION_DAYS.
"""
import logging
import os
import sys
import time
from datetime import datetime
from glob import glob

from config import settings

# --- Formatting (kept in code so output is consistent, not a config knob) ----
# File: level padded by logging's own width spec (%(levelname)-8s).
_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
# Console: level padded manually inside ColorFormatter (ANSI codes would break
# logging's width counting), so no width spec here.
_CONSOLE_FORMAT = "%(asctime)s | %(levelname)s | %(name)-24s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ANSI colors applied to the level name on the console handler only.
_LEVEL_COLORS = {
    "DEBUG": "\033[36m",      # cyan
    "INFO": "\033[32m",       # green
    "WARNING": "\033[33m",    # yellow
    "ERROR": "\033[31m",      # red
    "CRITICAL": "\033[1;31m",  # bold red
}
_RESET = "\033[0m"

_ROOT_NAME = "crm"
_configured = False


class ColorFormatter(logging.Formatter):
    """Console formatter that colors (and pads) just the level name."""

    def format(self, record: logging.LogRecord) -> str:
        original = record.levelname
        color = _LEVEL_COLORS.get(original, "")
        # Pad to width 8 first, then wrap in color, so alignment survives the
        # ANSI codes. Restore the plain name afterwards for any other handler.
        record.levelname = f"{color}{original:<8}{_RESET}" if color else f"{original:<8}"
        try:
            return super().format(record)
        finally:
            record.levelname = original


def _cleanup_old_logs(log_dir: str, base: str, retention_days: int) -> int:
    """Delete ``<base>_*.log`` files older than ``retention_days``.

    Matches only our own log files, never touches the current day's file (its
    mtime is ~now), and never raises — logging setup must not crash the app.
    Returns the number of files removed.
    """
    if retention_days <= 0:
        return 0

    cutoff = time.time() - retention_days * 86400
    removed = 0
    for path in glob(os.path.join(log_dir, f"{base}_*.log")):
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
                removed += 1
        except OSError:
            # File already gone or locked by another process — skip it.
            pass
    return removed


def _configure() -> None:
    """Configure the ``crm`` logger once, from settings."""
    global _configured
    if _configured:
        return
    _configured = True  # set early so a log call during setup can't recurse

    os.makedirs(settings.log_dir, exist_ok=True)

    logger = logging.getLogger(_ROOT_NAME)
    logger.setLevel(settings.log_level.upper())
    logger.propagate = False       # don't double-log through the root logger
    logger.handlers.clear()        # idempotent even if reconfigured

    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(settings.log_dir, f"{settings.log_file_name}_{today}.log")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(file_handler)

    if settings.log_to_console:
        # Console logs go to STDERR, never stdout. stdio-based MCP servers use
        # stdout as their JSON-RPC channel, so any log line on stdout corrupts
        # the protocol ("Failed to parse JSONRPC message"). stderr is the
        # conventional destination for logs and is still shown in the terminal.
        console = logging.StreamHandler(sys.stderr)
        if settings.log_color and sys.stderr.isatty():
            console.setFormatter(ColorFormatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))
        else:
            console.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
        logger.addHandler(console)

    removed = _cleanup_old_logs(
        settings.log_dir, settings.log_file_name, settings.log_retention_days
    )
    logger.info(
        "Logging started -> %s (level=%s, retention=%dd)",
        log_path, settings.log_level.upper(), settings.log_retention_days,
    )
    if removed:
        logger.info(
            "Removed %d log file(s) older than %d day(s)",
            removed, settings.log_retention_days,
        )


def get_logger(name: str = "app") -> logging.Logger:
    """Return a child of the configured ``crm`` logger (configures on first call)."""
    _configure()
    return logging.getLogger(_ROOT_NAME).getChild(name)
