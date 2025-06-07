"""Command-line interface for WWDC Tools."""

import asyncio
import json
import logging
import os
import sys

import click
import httpx
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from .logger import logger
from wwdctools.downloader import download_session_content
from wwdctools.session import WWDCSession, fetch_session_data

console = Console()


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


@main.command()
@click.argument("url", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    help="Directory to save downloaded content.",
)
@click.pass_context
def download(ctx: click.Context, url: str, output: str | None = None) -> None:  # noqa: ARG001
    """Download video, transcript, and sample code from a WWDC session URL.

    URL: The URL of the WWDC session page.
    """
    logger.debug(f"Starting download from {url}")

    console.print(
        Panel.fit(f"[bold]Downloading content from[/bold] {url}", title="WWDCTools")
    )

    try:
        # Fetch session data
        logger.debug("Fetching session data...")
        session = asyncio.run(fetch_session_data(url))
        logger.debug(f"Session data fetched: ID={session.id}, Title={session.title}")

        # Check if video can be generated
        if not session.video_id:
            console.print(f"[yellow]No video available for:[/yellow] {session.title}")

        # Download content
        console.print(f"Downloading content for [bold]{session.title}[/bold]...")
        downloads = asyncio.run(download_session_content(session, output))

        # Display results
        console.print("\n[bold green]Download Summary:[/bold green]")
        for content_type, filepath in downloads.items():
            console.print(f"• {content_type.capitalize()}: [bold]{filepath}[/bold]")

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


@main.command()
@click.argument("urls", type=str, nargs=-1, required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=False),
    help="Directory to save transcripts to. If not provided, prints to console.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["txt", "md", "json"]),
    default="txt",
    help="Output format for saving transcripts. Default is text.",
)
@click.option(
    "--combine",
    "-c",
    is_flag=True,
    help="Combine all transcripts into a single file.",
)
@click.pass_context
def transcript(  # noqa: PLR0912, PLR0915
    ctx: click.Context,  # noqa: ARG001
    urls: tuple[str, ...],
    output: str | None = None,
    format: str = "txt",
    combine: bool = False,
) -> None:
    """Fetch transcripts from one or more WWDC session URLs.

    URLS: The URLs of the WWDC session pages.
    """
    logger.debug(f"Processing {len(urls)} URLs with format={format}, combine={combine}")

    if not urls:
        console.print("[bold red]Error:[/bold red] No URLs provided.")
        sys.exit(1)

    if len(urls) > 1 and output and not combine and not os.path.isdir(output):
        console.print(
            "[bold red]Error:[/bold red] When fetching multiple transcripts, "
            "output must be a directory unless --combine is used."
        )
        sys.exit(1)

    # Create a list to store all sessions and their transcripts
    all_sessions = []
    all_transcripts = []

    logger.debug(f"Starting to process {len(urls)} URLs")

    for url in urls:
        console.print(
            Panel.fit(f"[bold]Fetching transcript from[/bold] {url}", title="WWDCTools")
        )
        logger.debug(f"Processing URL: {url}")

        try:
            logger.debug("Fetching session data...")
            session = asyncio.run(fetch_session_data(url))
            logger.debug(
                f"Session data fetched: ID={session.id}, Title={session.title}"
            )

            if not session.transcript_content:
                console.print(
                    f"[yellow]No transcript available for:[/yellow] {session.title}"
                )
                continue
            transcript_text = session.transcript_content
            logger.debug(f"Transcript fetched: {len(transcript_text)} characters")

            all_sessions.append(session)
            all_transcripts.append(transcript_text)

            if output and not combine:
                # Save individual transcript
                if os.path.isdir(output):
                    # Use session ID and title for filename
                    filename = (
                        f"{session.id}_{session.title.replace(' ', '_')}.{format}"
                    )
                    filepath = os.path.join(output, filename)
                    logger.debug(f"Using directory path: {output}")
                else:
                    filepath = output
                    logger.debug(f"Using direct file path: {filepath}")

                # Format and save transcript
                logger.debug(f"Formatting transcript in {format} format")
                formatted_content = _format_transcript(transcript_text, session, format)
                logger.debug(
                    f"Writing {len(formatted_content)} characters to {filepath}"
                )
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                console.print(
                    f"[bold green]Transcript saved to[/bold green] {filepath}"
                )
            elif not output and len(urls) == 1:
                # Print single transcript to console
                console.print("\n[bold]Transcript:[/bold]\n")
                console.print(transcript_text)
                console.print("\n[dim](Use --output to save the transcript)[/dim]")

        except ValueError as e:
            logger.error(f"ValueError with URL {url}: {e!s}", exc_info=True)
            console.print(f"[bold red]Error with {url}:[/bold red] {e!s}")
            if len(urls) == 1:
                sys.exit(1)
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error with URL {url}: {e!s}", exc_info=True)
            console.print(
                f"[bold red]HTTP Error with {url}:[/bold red] "
                f"Failed to fetch content - {e!s}"
            )
            if len(urls) == 1:
                sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error with URL {url}: {e!s}", exc_info=True)
            console.print(f"[bold red]Unexpected Error with {url}:[/bold red] {e!s}")
            if len(urls) == 1:
                sys.exit(1)

    # Check if we have any successful transcripts
    if not all_transcripts:
        logger.error("No transcripts were successfully fetched")
        console.print(
            "[bold red]Error:[/bold red] No transcripts were successfully fetched."
        )
        sys.exit(1)

    logger.debug(f"Successfully fetched {len(all_transcripts)} transcripts")

    # Handle combined output if requested
    if output and combine and all_transcripts:
        filepath = (
            output
            if not os.path.isdir(output)
            else os.path.join(output, f"combined_transcripts.{format}")
        )

        logger.debug(f"Combining {len(all_transcripts)} transcripts to {filepath}")

        with open(filepath, "w", encoding="utf-8") as f:
            if format == "json":
                # Create a JSON document with all transcripts
                import json

                logger.debug("Creating combined JSON document")
                combined_data = [
                    {
                        "id": session.id,
                        "title": session.title,
                        "year": session.year,
                        "transcript": transcript,
                    }
                    for session, transcript in zip(
                        all_sessions, all_transcripts, strict=True
                    )
                ]
                logger.debug(
                    f"Writing combined JSON with {len(combined_data)} sessions"
                )
                f.write(json.dumps(combined_data, indent=2))
            else:
                # Create a text or markdown document with all transcripts
                logger.debug(f"Creating combined {format} document")
                for i, (session, transcript) in enumerate(
                    zip(all_sessions, all_transcripts, strict=True)
                ):
                    if i > 0:
                        f.write("\n\n" + ("-" * 80) + "\n\n")

                    if format == "md":
                        logger.debug(f"Adding session {session.id} in markdown format")
                        f.write(f"# {session.title}\n\n")
                        f.write(f"WWDC {session.year} - Session {session.id}\n\n")
                    else:
                        logger.debug(f"Adding session {session.id} in text format")
                        f.write(f"{session.title}\n")
                        f.write(f"WWDC {session.year} - Session {session.id}\n\n")

                    f.write(transcript)

                logger.debug(f"Completed writing combined {format} document")

        console.print(
            f"[bold green]Combined transcripts saved to[/bold green] {filepath}"
        )

    # Summary if multiple URLs were processed
    if len(urls) > 1:
        console.print(
            f"\n[bold green]Summary:[/bold green] "
            f"Successfully fetched {len(all_transcripts)} out of {len(urls)} "
            f"transcripts."
        )


def _format_transcript(transcript: str, session: WWDCSession, format: str) -> str:
    """Format transcript based on the specified output format.

    Args:
        transcript: The transcript text.
        session: The session metadata.
        format: The output format (txt, md, json).

    Returns:
        The formatted transcript.
    """
    if format == "json":
        return json.dumps(
            {
                "id": session.id,
                "title": session.title,
                "year": session.year,
                "transcript": transcript,
            },
            indent=2,
        )
    if format == "md":
        return (
            f"# {session.title}\n\n"
            f"WWDC {session.year} - Session {session.id}\n\n"
            f"{transcript}"
        )
    # txt
    return (
        f"{session.title}\nWWDC {session.year} - Session {session.id}\n\n{transcript}"
    )


@main.command()
@click.argument("url", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=False),
    help="Directory to save code samples. If not provided, prints to console.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["txt", "md", "json"]),
    default="txt",
    help="Output format for saving code samples. Default is text.",
)
@click.option(
    "--combine",
    "-c",
    is_flag=True,
    help="Combine all code samples into a single file.",
)
@click.pass_context
def code(
    ctx: click.Context,  # noqa: ARG001
    url: str,
    output: str | None = None,
    format: str = "txt",
    combine: bool = False,
) -> None:
    """Extract code samples from a WWDC session URL.

    URL: The URL of the WWDC session page.
    """
    logger.debug(
        f"Extracting code samples from {url} with format={format}, combine={combine}"
    )

    console.print(
        Panel.fit(f"[bold]Extracting code samples from[/bold] {url}", title="WWDCTools")
    )

    try:
        # Fetch session data
        logger.debug("Fetching session data...")
        session = asyncio.run(fetch_session_data(url))
        logger.debug(f"Session data fetched: ID={session.id}, Title={session.title}")

        # Check if code samples are available
        if not session.sample_codes:
            console.print(
                f"[yellow]No code samples found for:[/yellow] {session.title}"
            )
            sys.exit(0)

        logger.debug(f"Found {len(session.sample_codes)} code samples")

        # Format the code samples
        formatted_samples = _format_code_samples(session, format)

        # Output the code samples
        if output:
            # Save to file
            if os.path.isdir(output):
                # Use session ID and title for filename
                filename = (
                    f"{session.id}_{session.title.replace(' ', '_')}_code.{format}"
                )
                filepath = os.path.join(output, filename)
            else:
                filepath = output

            logger.debug(f"Saving code samples to {filepath}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(formatted_samples)

            console.print(f"[bold green]Code samples saved to[/bold green] {filepath}")
        else:
            # Print to console
            console.print("\n[bold]Code Samples:[/bold]\n")
            console.print(formatted_samples)
            console.print("\n[dim](Use --output to save the code samples)[/dim]")

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


def _format_code_samples(session: WWDCSession, format: str) -> str:
    """Format code samples based on the specified output format.

    Args:
        session: The session metadata with code samples.
        format: The output format (txt, md, json).

    Returns:
        The formatted code samples.
    """
    if format == "json":
        return json.dumps(
            {
                "id": session.id,
                "title": session.title,
                "year": session.year,
                "samples": [
                    {
                        "time": sample.time,
                        "title": sample.title,
                        "code": sample.code,
                    }
                    for sample in session.sample_codes
                ],
            },
            indent=2,
        )

    lines = []

    if format == "md":
        lines.append(f"# Code Samples from {session.title}")
        lines.append(f"WWDC {session.year} - Session {session.id}\n")

        for sample in session.sample_codes:
            # Format time as MM:SS
            minutes = int(sample.time) // 60
            seconds = int(sample.time) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            lines.append(f"## {sample.title}")
            lines.append(f"Time: {time_str}\n")
            lines.append("```")
            lines.append(sample.code)
            lines.append("```\n")
    else:
        # txt format
        lines.append(f"Code Samples from {session.title}")
        lines.append(f"WWDC {session.year} - Session {session.id}\n")

        for sample in session.sample_codes:
            # Format time as MM:SS
            minutes = int(sample.time) // 60
            seconds = int(sample.time) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            lines.append(f"=== {sample.title} ===")
            lines.append(f"Time: {time_str}\n")
            lines.append(sample.code)
            lines.append("\n" + "-" * 80 + "\n")

    return "\n".join(lines)


@main.command()
@click.argument("search_term", type=str)
@click.pass_context
def search(ctx: click.Context, search_term: str) -> None:  # noqa: ARG001
    """Search for WWDC sessions by keyword.

    SEARCH_TERM: The term to search for in session titles and descriptions.
    """
    logger.debug(f"Searching with term: {search_term}")

    click.echo(f"Searching for sessions with term: {search_term}")
    # Implementation will be added later
    pass


if __name__ == "__main__":
    # Use a dict for ctx.obj
    main(obj={})
