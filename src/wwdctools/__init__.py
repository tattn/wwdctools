"""WWDCTools - Tools for fetching videos, scripts, and code from Apple WWDC sessions."""

# Re-export public API
from .downloader import download_session_content
from .models import WWDCSession, WWDCTranscript
from .session import fetch_session_data
from .transcript import fetch_transcript
from .webvtt_utils import combine_webvtt_content, combine_webvtt_files

# Version information
__version__ = "0.1.0"

__all__ = [
    "WWDCSession",
    "WWDCTranscript",
    "combine_webvtt_content",
    "combine_webvtt_files",
    "download_session_content",
    "fetch_session_data",
    "fetch_transcript",
]
