"""Tests for WebVTT content extraction."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import Response

from wwdctools.session import fetch_session_data


def test_simple():
    """A simple test to verify test collection works."""
    assert True


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_webvtt_content(mock_client_class: Any) -> None:
    """Test retrieving WebVTT content from WebVTT URLs."""
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

    # Add mock responses for WebVTT content
    mock_webvtt_responses = []
    for i in range(5):
        mock_webvtt = MagicMock(spec=Response)
        mock_webvtt.text = (
            f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\nSubtitle {i}"
        )
        mock_webvtt.raise_for_status = MagicMock()
        mock_webvtt_responses.append(mock_webvtt)

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

        # Handle WebVTT URL requests
        for i in range(5):
            webvtt_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_{i}.webvtt"
            if url == webvtt_url:
                return mock_webvtt_responses[i]

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

    # Verify WebVTT URLs
    assert len(session.webvtt_urls) == 5
    for i in range(5):
        assert (
            session.webvtt_urls[i]
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_{i}.webvtt"
        )

    # Verify WebVTT content
    assert len(session.webvtt_content) == 5
    for i in range(5):
        assert (
            session.webvtt_content[i]
            == f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\nSubtitle {i}"
        )

    # Verify mocks were called correctly
    assert (
        mock_client.get.call_count == 8
    )  # Main page + HLS + subtitles manifest + 5 WebVTT files
    mock_client.get.assert_any_call(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
    )
    mock_client.get.assert_any_call(
        f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )
    # WebVTT files assertions
    for i in range(5):
        mock_client.get.assert_any_call(
            f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_{i}.webvtt"
        )
