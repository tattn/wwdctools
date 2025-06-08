"""Tests for video download functionality."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from wwdctools import WWDCSession
from wwdctools.downloader import download_session_content
from wwdctools.session import fetch_session_data


@pytest.mark.anyio
async def test_download_session_content_video_only():
    """Test downloading a video from a session."""
    # Setup mock for AsyncClient
    with patch("wwdctools.downloader.httpx.AsyncClient") as mock_client_class:
        # Setup mock response for download
        mock_client = mock_client_class.return_value.__aenter__.return_value

        # Create a mock response
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.content = b"test" * 250
        mock_response.raise_for_status = MagicMock()

        # Make client.get return the mock response
        mock_client.get = AsyncMock(return_value=mock_response)

        # Create a temporary directory for output
        output_dir = Path("test_output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Create test session
            session = WWDCSession(
                id="123",
                title="Test Session",
                description="Test description",
                year=2024,
                url="https://developer.apple.com/videos/play/wwdc2024/123",
                video_id="1/test",  # Now using video_id instead of video_url
                transcript_content=None,
                sample_code_url=None,
            )

            # Download content
            result = await download_session_content(session, str(output_dir))

            # Verify results
            assert "video" in result
            assert os.path.exists(result["video"])
            assert result["video"].endswith("_hd.mp4")  # Default quality is "hd"

            # Test with SD quality
            result_sd = await download_session_content(session, str(output_dir), "sd")
            assert "video" in result_sd
            assert os.path.exists(result_sd["video"])
            assert result_sd["video"].endswith("_sd.mp4")

            # Verify mocks were called correctly
            assert mock_client.get.call_count == 2

        finally:
            # Clean up test files
            for file in output_dir.glob("*"):
                file.unlink()
            if output_dir.exists():
                output_dir.rmdir()


@pytest.mark.anyio
async def test_download_session_content_no_content():
    """Test that ValueError is raised when no content is available."""
    # Create test session with no downloadable content
    session = WWDCSession(
        id="123",
        title="Test Session",
        description="Test description",
        year=2024,
        url="https://developer.apple.com/videos/play/wwdc2024/123",
        video_id=None,
        transcript_content=None,
        sample_code_url=None,
    )

    # Verify that ValueError is raised
    with pytest.raises(ValueError, match="No content available to download"):
        await download_session_content(session, "test_output")


@pytest.mark.anyio
async def test_fetch_session_data_download_video_url():
    """Test extracting download video URL from session page."""
    # Setup mocks
    with patch("wwdctools.session.httpx.AsyncClient") as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock(spec=Response)
        mock_response.text = """
        <html>
            <head><title>WWDC Session</title></head>
            <body>
                <h1>Building Great Apps</h1>
                <p class="description">
                    Learn how to build great apps for Apple platforms.
                </p>
                <a href="https://devstreaming-cdn.apple.com/videos/wwdc/2024/10138/4/A149C0AB-2AB1-48C1-B259-4D5621873D5F/downloads/wwdc2024-10138_sd.mp4?dl=1">Download SD</a>
                <a href="/downloads/sample-code/building-great-apps.zip">
                    Download Sample Code
                </a>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Call function
        session = await fetch_session_data(
            "https://developer.apple.com/videos/play/wwdc2024/10138"
        )

        # Verify video URL was extracted correctly
        assert session.id == "10138"
        assert session.year == 2024
        assert session.video_id is not None  # Should extract video_id, not video_url
        # Check the generated URL
        video_url = session.generate_video_url()
        assert video_url is not None


@pytest.mark.anyio
@patch("wwdctools.downloader.httpx.AsyncClient")
async def test_download_session_content_no_content(  # noqa: F811
    mock_client_class: MagicMock,  # noqa: ARG001
) -> None:
    """Test that ValueError is raised when no content is available."""
    # Create test session with no downloadable content
    session = WWDCSession(
        id="123",
        title="Test Session",
        description="Test description",
        year=2024,
        url="https://developer.apple.com/videos/play/wwdc2024/123",
        video_id=None,
        transcript_content=None,
        sample_code_url=None,
    )

    # Verify that ValueError is raised
    with pytest.raises(ValueError, match="No content available to download"):
        await download_session_content(session, "test_output")


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_download_video_url(  # noqa: F811
    mock_client_class: MagicMock,
) -> None:
    """Test extracting download video URL from session page."""
    # Setup mocks
    mock_client = mock_client_class.return_value.__aenter__.return_value
    mock_response = MagicMock(spec=Response)
    mock_response.text = """
    <html>
        <head><title>WWDC Session</title></head>
        <body>
            <h1>Building Great Apps</h1>
            <p class="description">
                Learn how to build great apps for Apple platforms.
            </p>
            <a href="https://devstreaming-cdn.apple.com/videos/wwdc/2024/10138/4/A149C0AB-2AB1-48C1-B259-4D5621873D5F/downloads/wwdc2024-10138_sd.mp4?dl=1">Download SD</a>
            <a href="/downloads/sample-code/building-great-apps.zip">
                Download Sample Code
            </a>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response

    # Call function
    session = await fetch_session_data(
        "https://developer.apple.com/videos/play/wwdc2024/10138"
    )

    # Verify video URL was extracted correctly
    assert session.id == "10138"
    assert session.year == 2024

    # Extract video_id from the URL in the mock HTML
    expected_video_id = "4/A149C0AB-2AB1-48C1-B259-4D5621873D5F"
    assert session.video_id == expected_video_id

    # Test the generated URLs
    hd_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/2024/10138/{expected_video_id}/downloads/wwdc2024-10138_hd.mp4?dl=1"
    sd_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/2024/10138/{expected_video_id}/downloads/wwdc2024-10138_sd.mp4?dl=1"
    assert session.generate_video_url() == hd_url
    assert session.generate_video_url("sd") == sd_url


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_with_video_id_meta(
    mock_client_class: MagicMock,
) -> None:
    """Test extracting video ID from og:video meta tag."""
    # Setup mocks
    mock_client = mock_client_class.return_value.__aenter__.return_value
    mock_response = MagicMock(spec=Response)
    mock_response.text = """
    <html>
        <head>
            <title>WWDC Session</title>
            <meta property="og:video" content="https://devstreaming-cdn.apple.com/videos/wwdc/2024/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8">
        </head>
        <body>
            <h1>Building Great Apps</h1>
            <p class="description">
                Learn how to build great apps for Apple platforms.
            </p>
            <a href="https://devstreaming-cdn.apple.com/videos/wwdc/2024/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/downloads/wwdc2024-10144_sd.mp4?dl=1">Download SD</a>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response

    # Call function
    session = await fetch_session_data(
        "https://developer.apple.com/videos/play/wwdc2024/10144"
    )

    # Verify video ID was extracted correctly
    assert session.id == "10144"
    assert session.year == 2024
    assert session.video_id == "4/8A69C683-3259-454B-9F94-5BBE98999A1B"
    # Test the generated video URL
    assert (
        session.generate_video_url()
        == "https://devstreaming-cdn.apple.com/videos/wwdc/2024/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/downloads/wwdc2024-10144_hd.mp4?dl=1"
    )
    assert (
        session.generate_video_url("sd")
        == "https://devstreaming-cdn.apple.com/videos/wwdc/2024/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/downloads/wwdc2024-10144_sd.mp4?dl=1"
    )
