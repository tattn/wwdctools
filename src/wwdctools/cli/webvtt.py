"""WebVTT command for WWDC Tools CLI."""

import asyncio
import os
import sys

import click

from wwdctools.session import WWDCSession, fetch_session_data

from .utils import console, handle_command_errors, logger, print_panel


@click.command()
@click.argument("url", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=False),
    help=(
        "Directory to save WebVTT files to. "
        "If not provided, prints information to console."
    ),
)
@click.option(
    "--combine",
    "-c",
    is_flag=True,
    help="Combine all WebVTT files into a single file.",
)
@click.pass_context
@handle_command_errors
def webvtt(
    ctx: click.Context,  # noqa: ARG001
    url: str,
    output: str | None = None,
    combine: bool = False,
) -> None:
    """Download WebVTT subtitle files from a WWDC session URL.

    URL: The URL of the WWDC session page.
    """
    logger.debug(f"Starting WebVTT download from {url}")

    print_panel(f"[bold]Downloading WebVTT subtitles from[/bold] {url}")

    # Fetch session data
    logger.debug("Fetching session data...")
    session = asyncio.run(fetch_session_data(url))
    logger.debug(f"Session data fetched: ID={session.id}, Title={session.title}")

    # Check if WebVTT URLs are available
    if not session.webvtt_urls:
        console.print(
            f"[yellow]No WebVTT subtitles available for:[/yellow] {session.title}"
        )
        sys.exit(0)

    logger.debug(f"Found {len(session.webvtt_urls)} WebVTT URLs")

    # Fetch WebVTT content
    webvtt_content = asyncio.run(session.fetch_webvtt())
    logger.debug(f"Fetched {len(webvtt_content)} WebVTT files")

    if output:
        _save_webvtt_files(session, webvtt_content, output, combine)
    else:
        _print_webvtt_info(webvtt_content)


def _save_webvtt_files(
    session: WWDCSession,
    webvtt_content: list[str],
    output: str,
    combine: bool,
) -> None:
    """Save WebVTT files to disk.

    Args:
        session: The session data.
        webvtt_content: List of WebVTT content strings.
        output: Output path.
        combine: Whether to combine all files into one.
    """
    # Create directory if it's a directory path
    if os.path.isdir(output) or not combine:
        # When not combining or output is a directory, create a subdirectory
        if os.path.isdir(output):
            session_dir = os.path.join(output, f"wwdc_{session.year}_{session.id}")
            os.makedirs(session_dir, exist_ok=True)
            webvtt_dir = os.path.join(session_dir, "webvtt")
        else:
            webvtt_dir = output

        os.makedirs(webvtt_dir, exist_ok=True)
        logger.debug(f"Created directory for WebVTT files: {webvtt_dir}")

        # Save individual WebVTT files
        for i, content in enumerate(webvtt_content):
            filename = f"sequence_{i}.webvtt"
            filepath = os.path.join(webvtt_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        console.print(f"[bold green]WebVTT files saved to[/bold green] {webvtt_dir}")
    else:
        # Combine all WebVTT files into a single file
        combined_filepath = output

        with open(combined_filepath, "w", encoding="utf-8") as f:
            for i, content in enumerate(webvtt_content):
                if i > 0:
                    f.write("\n\n" + ("-" * 80) + "\n\n")
                f.write(f"# Sequence {i}\n\n")
                f.write(content)

        console.print(
            f"[bold green]Combined WebVTT saved to[/bold green] {combined_filepath}"
        )


def _print_webvtt_info(webvtt_content: list[str]) -> None:
    """Print information about WebVTT files to console.

    Args:
        webvtt_content: List of WebVTT content strings.
    """
    console.print(f"\n[bold]Found {len(webvtt_content)} WebVTT files:[/bold]\n")

    # Show a sample of the first WebVTT file
    if webvtt_content:
        max_sample_lines = 10
        sample_lines = webvtt_content[0].split("\n")[:max_sample_lines]
        if len(sample_lines) > max_sample_lines - 1:
            sample_lines.append("...")
        sample_text = "\n".join(sample_lines)

        console.print("[bold]Sample from first WebVTT file:[/bold]")
        console.print(sample_text)

    console.print("\n[dim](Use --output to save the WebVTT files)[/dim]")
