"""Structured Logger module for application error logging and context tracking.

Rule 1.9: Logs must include enough context for debugging.
Wrap all async functions with try-catch and log context parameters.
"""

import logging
import sys
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("tourism_portal")


def log_error(action: str, message: str, context: Optional[dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
    """Logs an error with explicit debugging context.

    Args:
        action: The function or action name where the error occurred (e.g. 'ingest_events').
        message: Descriptive explanation of what failed.
        context: Dictionary containing input parameters or system state.
        error: The caught exception object if available.
    """
    ctx_str = f" | Context: {context}" if context else ""
    err_str = f" | Exception: {str(error)}" if error else ""
    logger.error(f"[{action}] {message}{ctx_str}{err_str}")


def log_info(action: str, message: str, context: Optional[dict[str, Any]] = None) -> None:
    """Logs an informational message with context.

    Args:
        action: The function or action name.
        message: Info detail string.
        context: Optional dictionary context.
    """
    ctx_str = f" | Context: {context}" if context else ""
    logger.info(f"[{action}] {message}{ctx_str}")
