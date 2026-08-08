"""
Minimal print-based logging for the RAG system.

Each module creates a logger via `get_logger("component")` and uses
`log.info()`, `log.error()`, etc. — all backed by print().

Verbosity controlled by setup_rag_logging(level=...).
"""

from __future__ import annotations

from typing import Optional

_LEVEL = "INFO"
_LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
    "RESET": "\033[0m",
}


def setup_rag_logging(level: str = "INFO", log_file: Optional[str] = None, console: bool = True):
    global _LEVEL
    _LEVEL = level.upper()


class _PrintLogger:
    """A logger whose methods call print()."""

    def __init__(self, component: str):
        self._component = component

    def _emit(self, level: str, msg: str):
        if _LEVEL_ORDER.get(level, 1) < _LEVEL_ORDER.get(_LEVEL, 1):
            return
        color = _COLORS.get(level, "")
        reset = _COLORS["RESET"]
        print(f"{color}[{level:8s}]{reset} {self._component}: {msg}", flush=True)

    def info(self, msg: str, *args):
        if args:
            msg = msg % args
        self._emit("INFO", msg)

    def warning(self, msg: str, *args):
        if args:
            msg = msg % args
        self._emit("WARNING", msg)

    def error(self, msg: str, *args):
        if args:
            msg = msg % args
        self._emit("ERROR", msg)

    def debug(self, msg: str, *args):
        if args:
            msg = msg % args
        self._emit("DEBUG", msg)

    def critical(self, msg: str, *args):
        if args:
            msg = msg % args
        self._emit("CRITICAL", msg)

    def exception(self, msg: str, *args):
        import traceback
        self._emit("ERROR", msg)
        tb = traceback.format_exc()
        if tb and tb.strip() != "NoneType: None":
            for line in tb.rstrip().splitlines():
                print(f"  {line}", flush=True)


_loggers: dict[str, _PrintLogger] = {}

def get_logger(component: str) -> _PrintLogger:
    if component not in _loggers:
        _loggers[component] = _PrintLogger(component)
    return _loggers[component]