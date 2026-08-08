"""
Centralized ANSI color utilities for Scratchy.

Provides colored text helpers and a colored logging formatter.
Respects NO_COLOR / TERM=dumb env vars and disables colors when
stdout is not a TTY.
"""

from __future__ import annotations

import os
import sys

# ── ANSI escape codes ──────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
GRAY = "\033[90m"
WHITE = "\033[97m"

# Bold foreground
BOLD_RED = "\033[1;91m"
BOLD_GREEN = "\033[1;92m"
BOLD_YELLOW = "\033[1;93m"
BOLD_BLUE = "\033[1;94m"
BOLD_CYAN = "\033[1;96m"

# Background colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"

# ── Color support detection ────────────────────────────────────────────────


def _colors_enabled() -> bool:
    """Return True if ANSI colors should be emitted."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


_COLORS = _colors_enabled()


def set_colors(enabled: bool) -> None:
    """Manually enable or disable colored output."""
    global _COLORS
    _COLORS = enabled


def colored(text: str, color: str) -> str:
    """Wrap *text* in the given ANSI color escape sequence."""
    if not _COLORS:
        return text
    return f"{color}{text}{RESET}"


# ── Convenience helpers ────────────────────────────────────────────────────


def success(text: str) -> str:
    """Green text — success / pass."""
    return colored(text, GREEN)


def error(text: str) -> str:
    """Red text — error / failure."""
    return colored(text, RED)


def warning(text: str) -> str:
    """Yellow text — warning."""
    return colored(text, YELLOW)


def info(text: str) -> str:
    """Cyan text — informational."""
    return colored(text, CYAN)


def debug(text: str) -> str:
    """Gray text — debug / verbose."""
    return colored(text, GRAY)


def bold(text: str) -> str:
    """Bold text."""
    return colored(text, BOLD)


def tool_call(name: str, args_preview: str = "") -> str:
    """Blue label for tool call start."""
    label = colored(f"[tool] {name}", BLUE)
    if args_preview:
        return f"{label}{DIM}({args_preview}){RESET}"
    return label


def tool_result(success_flag: bool, preview: str = "") -> str:
    """Green [ok] or red [FAIL] for tool call end."""
    if success_flag:
        tag = colored("[ok]", GREEN)
    else:
        tag = colored("[FAIL]", RED)
    if preview:
        return f"{tag} {preview}"
    return tag


def thinking(text: str) -> str:
    """Gray italic for reasoning / thinking."""
    return colored(text, GRAY)


def step(num: int | str, text: str) -> str:
    """Blue step indicator."""
    return f"{colored(f'[step {num}]', BLUE)} {text}"


def banner(text: str) -> str:
    """Bold cyan banner line."""
    return colored(text, BOLD_CYAN)


def section(text: str) -> str:
    """Bold blue section header."""
    return colored(text, BOLD_BLUE)


def header(text: str) -> str:
    """Bold white header."""
    return colored(text, BOLD + WHITE)


def label(name: str, color: str = CYAN) -> str:
    """Bracketed label like [MCP Client]."""
    return colored(f"[{name}]", color)


# ── Colored logging formatter ──────────────────────────────────────────────

import logging


class ColoredFormatter(logging.Formatter):
    """A logging.Formatter that color-codes by log level."""

    _LEVEL_COLORS = {
        logging.DEBUG: GRAY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt or "%(asctime)s %(levelname)-5s %(name)s | %(message)s",
                         datefmt=datefmt or "%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        level_color = self._LEVEL_COLORS.get(record.levelno, "")
        # Temporarily wrap levelname in color
        orig_levelname = record.levelname
        if _COLORS and level_color:
            record.levelname = f"{level_color}{record.levelname}{RESET}"
        result = super().format(record)
        record.levelname = orig_levelname  # restore for other handlers
        return result
