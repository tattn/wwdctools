"""Download command for WWDC Tools CLI."""

import asyncio

import click

from wwdctools.downloader import download_session_content
from wwdctools.session import fetch_session_data

from .utils import console, handle_command_errors, logger, print_panel


@click.command()
@click.argument("url", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    help="Directory to save downloaded content.",
)
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["hd", "sd"]),
    default="hd",
    help="Video quality. Either 'hd' or 'sd'. Defaults to 'hd'.",
)
@click.pass_context
@handle_command_errors
def download(
    ctx: click.Context,  # noqa: ARG001
    url: str,
    output: str | None = None,
    quality: str = "hd",
) -> None:
    """Download video, transcript, and sample code from a WWDC session URL.

    URL: The URL of the WWDC session page.
    """
    logger.debug(f"Starting download from {url}")

    print_panel(f"[bold]Downloading content from[/bold] {url}")

    # Fetch session data
    logger.debug("Fetching session data...")
    session = asyncio.run(fetch_session_data(url))
    logger.debug(f"Session data fetched: ID={session.id}, Title={session.title}")

    # Check if video can be generated
    if not session.video_id:
        console.print(f"[yellow]No video available for:[/yellow] {session.title}")

    # Download content
    console.print(f"Downloading content for [bold]{session.title}[/bold]...")
    downloads = asyncio.run(download_session_content(session, output, quality))

    # Display results
    console.print("\n[bold green]Download Summary:[/bold green]")
    for content_type, filepath in downloads.items():
        console.print(f"• {content_type.capitalize()}: [bold]{filepath}[/bold]")
