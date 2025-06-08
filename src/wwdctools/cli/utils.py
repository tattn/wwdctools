"""Utility functions for the CLI commands."""

import functools
import logging
import sys
from collections.abc import Callable
from typing import ParamSpec, TypeVar

import httpx
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from wwdctools.logger import logger

console = Console()

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Whether to enable verbose logging.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )
    logger.setLevel(log_level)
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)


def handle_command_errors(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator for handling common command errors.

    Args:
        func: The function to decorate.

    Returns:
        The wrapped function with error handling.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"ValueError: {e!s}", exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {e!s}")
            sys.exit(1)
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {e!s}", exc_info=True)
            console.print(
                f"[bold red]HTTP Error:[/bold red] Failed to fetch content - {e!s}"
            )
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e!s}", exc_info=True)
            console.print(f"[bold red]Unexpected Error:[/bold red] {e!s}")
            sys.exit(1)

    return wrapper


def print_panel(message: str, title: str = "WWDCTools") -> None:
    """Print a panel with a message.

    Args:
        message: The message to display.
        title: The panel title.
    """
    console.print(Panel.fit(message, title=title))
