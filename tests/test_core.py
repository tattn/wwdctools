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
    mock_response.text = f"""
    <html>
        <head>
            <title>WWDC Session</title>
            <meta property="og:video" content="https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8">
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

    # Add mock response for HLS manifest request
    mock_hls_response = MagicMock(spec=Response)
    mock_hls_response.text = """
    #EXTM3U
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="subtitles/eng/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="ko",NAME="한국어",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/kor/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="zh",NAME="简体中文",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/zho/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="ja",NAME="日本語",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/jpn/prog_index.m3u8",FORCED=NO
    """
    mock_hls_response.raise_for_status = MagicMock()

    # Add mock response for subtitles manifest request
    mock_subtitles_response = MagicMock(spec=Response)
    mock_subtitles_response.text = """
    #EXTM3U
    #EXT-X-TARGETDURATION:7
    #EXT-X-VERSION:3
    #EXT-X-MEDIA-SEQUENCE:0
    #EXT-X-PLAYLIST-TYPE:VOD
    #EXTINF:6.006
    sequence_0.webvtt
    #EXTINF:6.006
    sequence_1.webvtt
    #EXTINF:6.006
    sequence_2.webvtt
    #EXTINF:6.006
    sequence_3.webvtt
    #EXTINF:6.006
    sequence_4.webvtt
    #EXTINF:6.006
    #EXT-X-ENDLIST
    """
    mock_subtitles_response.raise_for_status = MagicMock()

    # Set up the client to return different responses based on the URL
    def mock_get_side_effect(url: str):
        if url == f"https://developer.apple.com/videos/play/wwdc{test_year}/10144":
            return mock_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
        ):
            return mock_hls_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
        ):
            return mock_subtitles_response
        raise ValueError(f"Unexpected URL: {url}")

    mock_client.get.side_effect = mock_get_side_effect

    # Call function
    session = await fetch_session_data(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )

    # Verify results
    assert session.id == "10144"
    assert session.title == "Building Great Apps"
    assert session.description == "Learn how to build great apps for Apple platforms."
    assert session.year == test_year
    assert (
        session.url == f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )
    assert session.video_id == "4/8A69C683-3259-454B-9F94-5BBE98999A1B"
    # Test the generated video URL
    assert (
        session.generate_video_url()
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/downloads/wwdc{test_year}-10144_hd.mp4?dl=1"
    )
    assert (
        session.generate_video_url("sd")
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/downloads/wwdc{test_year}-10144_sd.mp4?dl=1"
    )
    assert (
        session.subtitles_url
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )
    # Verify webvtt_urls are correctly extracted
    assert len(session.webvtt_urls) == 5
    assert (
        session.webvtt_urls[0]
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_0.webvtt"
    )
    assert (
        session.webvtt_urls[1]
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_1.webvtt"
    )

    # Verify mocks were called correctly with multiple URLs
    assert mock_client.get.call_count == 3
    mock_client.get.assert_any_call(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_with_webvtt_urls(mock_client_class: Any) -> None:
    """Test extracting WebVTT URLs from the subtitles manifest."""
    test_year = 2024
    # Setup mocks
    mock_client = mock_client_class.return_value.__aenter__.return_value
    mock_response = MagicMock(spec=Response)
    mock_response.text = f"""
    <html>
        <head>
            <title>WWDC Session</title>
            <meta property="og:video" content="https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8">
        </head>
        <body>
            <h1>Building Great Apps</h1>
            <p class="description">
                Learn how to build great apps for Apple platforms.
            </p>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()

    # Add mock response for HLS manifest request
    mock_hls_response = MagicMock(spec=Response)
    mock_hls_response.text = """
    #EXTM3U
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="subtitles/eng/prog_index.m3u8",FORCED=NO
    """
    mock_hls_response.raise_for_status = MagicMock()

    # Add mock response for subtitles manifest request
    mock_subtitles_response = MagicMock(spec=Response)
    mock_subtitles_response.text = """
    #EXTM3U
    #EXT-X-TARGETDURATION:7
    #EXT-X-VERSION:3
    #EXT-X-MEDIA-SEQUENCE:0
    #EXT-X-PLAYLIST-TYPE:VOD
    #EXTINF:6.006
    sequence_0.webvtt
    #EXTINF:6.006
    sequence_1.webvtt
    #EXTINF:6.006
    sequence_2.webvtt
    #EXTINF:6.006
    sequence_3.webvtt
    #EXTINF:6.006
    sequence_4.webvtt
    #EXTINF:6.006
    #EXT-X-ENDLIST
    """
    mock_subtitles_response.raise_for_status = MagicMock()

    # Set up the client to return different responses based on the URL
    def mock_get_side_effect(url: str):
        if url == f"https://developer.apple.com/videos/play/wwdc{test_year}/10144":
            return mock_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
        ):
            return mock_hls_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
        ):
            return mock_subtitles_response
        raise ValueError(f"Unexpected URL: {url}")

    mock_client.get.side_effect = mock_get_side_effect

    # Call function
    session = await fetch_session_data(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )

    # Verify results
    assert session.id == "10144"
    assert session.title == "Building Great Apps"
    assert session.year == test_year
    assert (
        session.subtitles_url
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )
    assert len(session.webvtt_urls) == 5
    assert (
        session.webvtt_urls[0]
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_0.webvtt"
    )
    assert (
        session.webvtt_urls[1]
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_1.webvtt"
    )
    assert (
        session.webvtt_urls[2]
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_2.webvtt"
    )

    # Verify mocks were called correctly
    assert mock_client.get.call_count == 3
    mock_client.get.assert_any_call(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )
