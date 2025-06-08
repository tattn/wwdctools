"""Main CLI entry point for WWDC Tools."""

import click

from .utils import configure_logging, logger


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging output.",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Tools for fetching videos, scripts, and code from Apple WWDC sessions."""
    # Store verbose setting in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Configure logging based on verbosity
    configure_logging(verbose)

    if verbose:
        logger.debug("Verbose logging enabled")


# Import and register commands
from .code import code  # noqa: E402
from .download import download  # noqa: E402
from .transcript import transcript  # noqa: E402
from .webvtt import webvtt  # noqa: E402

main.add_command(download)
main.add_command(transcript)
main.add_command(code)
main.add_command(webvtt)


if __name__ == "__main__":
    # Use a dict for ctx.obj
    main(obj={})
