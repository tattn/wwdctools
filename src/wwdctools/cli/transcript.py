"""Transcript command for WWDC Tools CLI."""

import asyncio
import json
import os
import sys
from collections.abc import Sequence

import click

from wwdctools.session import WWDCSession, fetch_session_data

from .utils import console, handle_command_errors, logger, print_panel


@click.command()
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
@handle_command_errors
def transcript(  # noqa: PLR0912, PLR0915
    ctx: click.Context,  # noqa: ARG001
    urls: Sequence[str],
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
        print_panel(f"[bold]Fetching transcript from[/bold] {url}")
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

        except Exception as e:
            logger.error(f"Error with URL {url}: {e!s}", exc_info=True)
            console.print(f"[bold red]Error with {url}:[/bold red] {e!s}")
            if len(urls) == 1:
                raise

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
                logger.debug("Creating combined JSON document")
                combined_data = [
                    {
                        "id": session.id,
                        "title": session.title,
                        "year": session.year,
                        "transcript": transcript_text,
                    }
                    for session, transcript_text in zip(
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
                for i, (session, transcript_text) in enumerate(
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

                    f.write(transcript_text)

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
