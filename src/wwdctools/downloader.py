"""Content download functionality for WWDC sessions."""

import os

import httpx

from .logger import logger
from .models import WWDCSession
from .utils import format_sample_code


async def _download_video(
    session: WWDCSession,
    output_dir: str,
    quality: str,
    skip_existing: bool,
) -> str | None:
    """Download video for a WWDC session.

    Args:
        session: The WWDCSession object containing content links.
        output_dir: Directory to save downloaded content.
        quality: The video quality. Either "hd" or "sd".
        skip_existing: Skip downloading files that already exist.

    Returns:
        The filepath of the downloaded video, or None if no video was downloaded.
    """
    video_url = session.generate_video_url(quality)
    if not video_url:
        return None

    # Create session directory
    session_dir = os.path.join(output_dir, f"wwdc_{session.year}_{session.id}")
    os.makedirs(session_dir, exist_ok=True)

    # Generate filename from quality
    filename = f"wwdc{session.year}-{session.id}_{quality}.mp4"
    filepath = os.path.join(session_dir, filename)

    # Check if file already exists
    if skip_existing and os.path.exists(filepath):
        logger.info(f"Video file already exists at {filepath}, skipping download")
        return filepath

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
    return filepath


def _save_transcript(
    session: WWDCSession,
    output_dir: str,
) -> str | None:
    """Save transcript content for a WWDC session.

    Args:
        session: The WWDCSession object containing transcript content.
        output_dir: Directory to save transcript content.

    Returns:
        The filepath of the saved transcript, or None if no transcript was saved.
    """
    if not session.transcript_content:
        return None

    # Create session directory
    session_dir = os.path.join(output_dir, f"wwdc_{session.year}_{session.id}")
    os.makedirs(session_dir, exist_ok=True)

    # Generate filename
    filename = "transcript.txt"
    filepath = os.path.join(session_dir, filename)

    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"Transcript file already exists at {filepath}, skipping download")
        return filepath

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(session.transcript_content)

    logger.info(f"Transcript saved to {filepath}")
    return filepath


async def _download_webvtt(
    session: WWDCSession,
    output_dir: str,
) -> str | None:
    """Download WebVTT subtitle files for a WWDC session.

    Args:
        session: The WWDCSession object containing WebVTT URLs.
        output_dir: Directory to save WebVTT files.

    Returns:
        The directory path of the saved WebVTT files, or None if no files were
        downloaded.
    """
    if not session.webvtt_urls:
        return None

    # Create session directory
    session_dir = os.path.join(output_dir, f"wwdc_{session.year}_{session.id}")
    os.makedirs(session_dir, exist_ok=True)

    # Create a directory for WebVTT files
    webvtt_dir = os.path.join(session_dir, "webvtt")

    # Check if WebVTT directory exists and has expected files
    if os.path.exists(webvtt_dir):
        expected_files = [
            f"sequence_{i}.webvtt" for i in range(len(session.webvtt_urls))
        ]
        existing_files = os.listdir(webvtt_dir)
        if all(file in existing_files for file in expected_files):
            logger.info(
                f"WebVTT files already exist in {webvtt_dir}, skipping download"
            )
            return webvtt_dir

    # Download if any files are missing
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
    return webvtt_dir


def _save_sample_code(
    session: WWDCSession,
    output_dir: str,
    format_type: str = "md",
) -> str | None:
    """Extract and save individual code samples for a WWDC session.

    Args:
        session: The WWDCSession object containing code samples.
        output_dir: Directory to save code samples.
        format_type: The output format (txt, md, json). Defaults to "md".

    Returns:
        The filepath of the saved code samples, or None if no code samples were saved.
    """
    if not session.sample_codes:
        return None

    # Create session directory
    session_dir = os.path.join(output_dir, f"wwdc_{session.year}_{session.id}")
    os.makedirs(session_dir, exist_ok=True)

    # Create a filename for the code samples with appropriate extension
    filename = f"sample_code.{format_type}"
    filepath = os.path.join(session_dir, filename)

    logger.info(f"Extracting {len(session.sample_codes)} code samples")

    # Format the code samples using the shared utility function
    formatted_content = format_sample_code(session, format_type)

    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(formatted_content)

    logger.info(f"Code samples saved to {filepath}")
    return filepath


async def download_session_content(
    session: WWDCSession,
    output_dir: str | None = None,
    quality: str = "hd",
    skip_existing: bool = True,
    sample_code_format: str = "md",
) -> dict[str, str]:
    """Download content (video, transcript, sample code) from a WWDC session.

    Args:
        session: The WWDCSession object containing content links.
        output_dir: Directory to save downloaded content. Defaults to current directory.
        quality: The video quality. Either "hd" or "sd". Defaults to "hd".
        skip_existing: Skip downloading files that already exist. Defaults to True.
        sample_code_format: The output format for sample code (txt, md, json).
            Defaults to "md".

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

    # Download video
    video_path = await _download_video(session, output_dir, quality, skip_existing)
    if video_path:
        downloaded_files["video"] = video_path

    # Save transcript
    transcript_path = _save_transcript(session, output_dir)
    if transcript_path:
        downloaded_files["transcript"] = transcript_path

    # Download WebVTT subtitles
    webvtt_dir = await _download_webvtt(session, output_dir)
    if webvtt_dir:
        downloaded_files["webvtt"] = webvtt_dir

    # Extract and save code samples
    sample_code_path = _save_sample_code(session, output_dir, sample_code_format)
    if sample_code_path:
        downloaded_files["sample_code"] = sample_code_path

    if not downloaded_files:
        raise ValueError(f"No content available to download for session {session.id}")

    return downloaded_files
