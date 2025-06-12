"""Code command for WWDC Tools CLI."""

import asyncio
import json
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
@handle_command_errors
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

    print_panel(f"[bold]Extracting code samples from[/bold] {url}")

    # Fetch session data
    logger.debug("Fetching session data...")
    session = asyncio.run(fetch_session_data(url))
    logger.debug(f"Session data fetched: ID={session.id}, Title={session.title}")

    # Check if code samples are available
    if not session.sample_codes:
        console.print(f"[yellow]No code samples found for:[/yellow] {session.title}")
        sys.exit(0)

    logger.debug(f"Found {len(session.sample_codes)} code samples")

    # Format the code samples
    formatted_samples = _format_sample_code(session, format)

    # Output the code samples
    if output:
        # Save to file
        if os.path.isdir(output):
            # Use session ID and title for filename
            filename = f"{session.id}_{session.title.replace(' ', '_')}_code.{format}"
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


def _format_sample_code(session: WWDCSession, format: str) -> str:
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

            # Create a timestamp link to the video
            timestamp_seconds = int(sample.time)
            timestamp_link = f"{session.url}?time={timestamp_seconds}"

            lines.append(f"## {sample.title}")
            lines.append(f"Time: [{time_str}]({timestamp_link})\n")
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

            # Create a timestamp link to the video
            timestamp_seconds = int(sample.time)
            timestamp_link = f"{session.url}?time={timestamp_seconds}"

            lines.append(f"=== {sample.title} ===")
            lines.append(f"Time: {time_str} ({timestamp_link})\n")
            lines.append(sample.code)
            lines.append("\n" + "-" * 80 + "\n")

    return "\n".join(lines)
