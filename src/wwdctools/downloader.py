"""Content download functionality for WWDC sessions."""

import os

import httpx

from .logger import logger
from .models import WWDCSession


async def download_session_content(  # noqa: PLR0915
    session: WWDCSession, output_dir: str | None = None
) -> dict[str, str]:
    """Download content (video, transcript, sample code) from a WWDC session.

    Args:
        session: The WWDCSession object containing content links.
        output_dir: Directory to save downloaded content. Defaults to current directory.

    Returns:
        A dictionary mapping content types to their local file paths.

    Raises:
        ValueError: If no content is available for download.
        IOError: If there's an error writing the content to disk.
    """
    # Set default output directory to current directory if not provided
    if not output_dir:
        output_dir = os.getcwd()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Track downloaded files
    downloaded_files: dict[str, str] = {}

    # Check if video ID is available and generate video URL
    video_url = session.generate_video_url()

    # Download video if available
    if video_url:
        # Generate filename from session data
        filename = (
            f"wwdc{session.year}_{session.id}_{session.title.replace(' ', '_')}.mp4"
        )
        filepath = os.path.join(output_dir, filename)

        logger.info(f"Downloading video for session {session.id}: {session.title}")

        # Create a client for HTTP requests
        async with httpx.AsyncClient() as client:
            # Start a streaming request
            response = await client.get(video_url)
            response.raise_for_status()

            # Get total size if available
            total_size = int(response.headers.get("content-length", 0))

            # Write content to file
            with open(filepath, "wb") as f:
                f.write(response.content)

            # Log completion
            if total_size > 0:
                logger.debug(f"Downloaded {total_size / 1024 / 1024:.1f} MB")

        logger.info(f"Video saved to {filepath}")
        downloaded_files["video"] = filepath

    # Download transcript if available
    if session.transcript_content:
        filename = (
            f"wwdc{session.year}_{session.id}_{session.title.replace(' ', '_')}"
            "_transcript.txt"
        )
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(session.transcript_content)

        logger.info(f"Transcript saved to {filepath}")
        downloaded_files["transcript"] = filepath

    # Download WebVTT subtitles if available
    if session.webvtt_urls:
        # Create a directory for WebVTT files
        webvtt_dir = os.path.join(
            output_dir,
            f"wwdc{session.year}_{session.id}_{session.title.replace(' ', '_')}_webvtt",
        )
        os.makedirs(webvtt_dir, exist_ok=True)

        logger.info(f"Downloading {len(session.webvtt_urls)} WebVTT subtitle files")

        # Fetch WebVTT content if not already fetched
        webvtt_content = await session.fetch_webvtt()

        # Save each WebVTT file
        for i, content in enumerate(webvtt_content):
            filename = f"sequence_{i}.webvtt"
            filepath = os.path.join(webvtt_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        logger.info(f"WebVTT files saved to {webvtt_dir}")
        downloaded_files["webvtt"] = webvtt_dir

    # Download sample code if available
    if session.sample_code_url:
        # Extract filename from URL or generate one
        sample_filename = session.sample_code_url.split("/")[-1]
        filepath = os.path.join(output_dir, sample_filename)

        logger.info(f"Downloading sample code from {session.sample_code_url}")
        async with httpx.AsyncClient() as client:
            # Get the response directly without using stream
            response = await client.get(session.sample_code_url)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)

        logger.info(f"Sample code saved to {filepath}")
        downloaded_files["sample_code"] = filepath

    # Extract and save individual code samples if available
    if session.sample_codes:
        # Create a filename for the code samples
        filename = (
            f"wwdc{session.year}_{session.id}_{session.title.replace(' ', '_')}"
            "_code_samples.txt"
        )
        filepath = os.path.join(output_dir, filename)

        logger.info(f"Extracting {len(session.sample_codes)} code samples")

        # Format the code samples as text
        lines = []
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

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Code samples saved to {filepath}")
        downloaded_files["code_samples"] = filepath

    if not downloaded_files:
        raise ValueError(f"No content available to download for session {session.id}")

    return downloaded_files
