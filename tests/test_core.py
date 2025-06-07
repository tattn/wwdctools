"""Tests for the WWDCTools package."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import Response

from wwdctools import WWDCSession
from wwdctools.session import fetch_session_data


def test_wwdc_session_model() -> None:
    """Test that the WWDCSession model can be created with valid data."""
    test_year = 2023
    session = WWDCSession(
        id="123",
        title="Test Session",
        description="This is a test session",
        year=test_year,
        url="https://developer.apple.com/videos/play/wwdc2023/123",
    )

    assert session.id == "123"
    assert session.title == "Test Session"
    assert session.year == test_year


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data(mock_client_class: Any) -> None:
    """Test fetching session data from a URL."""
    test_year = 2023
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
            <video>
                <source src="https://example.com/video.mp4" type="video/mp4">
            </video>
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
        "https://developer.apple.com/videos/play/wwdc2023/123"
    )

    # Verify results
    assert session.id == "123"
    assert session.title == "Building Great Apps"
    assert session.description == "Learn how to build great apps for Apple platforms."
    assert session.year == test_year
    assert session.url == "https://developer.apple.com/videos/play/wwdc2023/123"
    assert (
        session.sample_code_url
        == "https://developer.apple.com/downloads/sample-code/building-great-apps.zip"
    )

    # Verify mocks were called correctly
    mock_client.get.assert_called_once_with(
        "https://developer.apple.com/videos/play/wwdc2023/123"
    )


@pytest.mark.anyio
async def test_fetch_session_data_invalid_url() -> None:
    """Test that fetch_session_data raises ValueError for invalid URLs."""
    with pytest.raises(ValueError, match="Invalid WWDC session URL"):
        await fetch_session_data("https://example.com/not-a-wwdc-url")


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_with_video_id(mock_client_class: Any) -> None:
    """Test extracting video ID from og:video meta tag."""
    test_year = 2024
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
            <video>
                <source src="https://example.com/video.mp4" type="video/mp4">
            </video>
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
        "https://developer.apple.com/videos/play/wwdc2024/10144"
    )

    # Verify results
    assert session.id == "10144"
    assert session.title == "Building Great Apps"
    assert session.description == "Learn how to build great apps for Apple platforms."
    assert session.year == test_year
    assert session.url == "https://developer.apple.com/videos/play/wwdc2024/10144"
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
    assert (
        session.sample_code_url
        == "https://developer.apple.com/downloads/sample-code/building-great-apps.zip"
    )

    # Verify mocks were called correctly
    mock_client.get.assert_called_once_with(
        "https://developer.apple.com/videos/play/wwdc2024/10144"
    )
