"""Tests for language-specific subtitle selection."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import Response

from wwdctools.session import fetch_session_data

# Mark all tests as anyio
pytestmark = pytest.mark.anyio


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_japanese_subtitles(mock_client_class: Any) -> None:
    """Test fetching Japanese WebVTT subtitles."""
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

    # Add mock response for HLS manifest request with multiple languages
    mock_hls_response = MagicMock(spec=Response)
    mock_hls_response.text = """
    #EXTM3U
    #EXT-X-VERSION:6
    #EXT-X-INDEPENDENT-SEGMENTS
    #EXT-X-STREAM-INF:RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",BANDWIDTH=5780915,AVERAGE-BANDWIDTH=1206063,FRAME-RATE=29.970,AUDIO="program_audio_0",SUBTITLES="subs"
    cmaf/avc/1080p_6000/avc_1080p_6000.m3u8
    #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="program_audio_0",LANGUAGE="eng",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="cmaf/aac/lc_192/aac_lc_192.m3u8",FORCED=NO,CHANNELS="2"
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="subtitles/eng/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="zh",NAME="简体中文",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/zho/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="ja",NAME="日本語",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/jpn/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="ko",NAME="한국어",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/kor/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="fr",NAME="Français",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/fra/prog_index.m3u8",FORCED=NO
    """
    mock_hls_response.raise_for_status = MagicMock()

    # Add mock response for Japanese subtitles manifest
    mock_ja_subtitles_response = MagicMock(spec=Response)
    mock_ja_subtitles_response.text = """
    #EXTM3U
    #EXT-X-TARGETDURATION:7
    #EXT-X-VERSION:3
    #EXT-X-MEDIA-SEQUENCE:0
    #EXT-X-PLAYLIST-TYPE:VOD
    #EXTINF:6.006
    sequence_0.webvtt
    #EXTINF:6.006
    sequence_1.webvtt
    #EXT-X-ENDLIST
    """
    mock_ja_subtitles_response.raise_for_status = MagicMock()

    # Add mock responses for Japanese WebVTT content
    mock_ja_webvtt_responses = []
    for i in range(2):
        mock_webvtt = MagicMock(spec=Response)
        mock_webvtt.text = (
            f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\n日本語字幕 {i}"
        )
        mock_webvtt.raise_for_status = MagicMock()
        mock_ja_webvtt_responses.append(mock_webvtt)

    # Set up the client to return different responses based on the URL
    def mock_get_side_effect(url: str) -> Response:
        if url == f"https://developer.apple.com/videos/play/wwdc{test_year}/10144":
            return mock_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/cmaf.m3u8"
        ):
            return mock_hls_response
        if (
            url
            == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/jpn/prog_index.m3u8"
        ):
            return mock_ja_subtitles_response

        # Handle Japanese WebVTT URL requests
        for i in range(2):
            webvtt_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/jpn/sequence_{i}.webvtt"
            if url == webvtt_url:
                return mock_ja_webvtt_responses[i]

        raise ValueError(f"Unexpected URL: {url}")

    mock_client.get.side_effect = mock_get_side_effect

    # Call function with Japanese language
    session = await fetch_session_data(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144", language="ja"
    )

    # Verify session data
    assert session.id == "10144"
    assert session.title == "Building Great Apps"
    assert session.year == test_year

    # Verify Japanese subtitles URL is correctly extracted
    assert (
        session.subtitles_url
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/jpn/prog_index.m3u8"
    )

    # Verify WebVTT URLs are correctly extracted
    assert len(session.webvtt_urls) == 2
    for i in range(2):
        expected_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/jpn/sequence_{i}.webvtt"
        assert session.webvtt_urls[i] == expected_url

    # Test fetching WebVTT content
    content = await session.fetch_webvtt()
    assert len(content) == 2
    for i in range(2):
        expected_content = (
            f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\n日本語字幕 {i}"
        )
        assert content[i] == expected_content


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fallback_subtitles(mock_client_class: Any) -> None:
    """Test fallback to English when requested language is unavailable."""
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

    # Add mock response for HLS manifest without the requested language
    mock_hls_response = MagicMock(spec=Response)
    mock_hls_response.text = """
    #EXTM3U
    #EXT-X-VERSION:6
    #EXT-X-INDEPENDENT-SEGMENTS
    #EXT-X-STREAM-INF:RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",BANDWIDTH=5780915,AVERAGE-BANDWIDTH=1206063,FRAME-RATE=29.970,AUDIO="program_audio_0",SUBTITLES="subs"
    cmaf/avc/1080p_6000/avc_1080p_6000.m3u8
    #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="program_audio_0",LANGUAGE="eng",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="cmaf/aac/lc_192/aac_lc_192.m3u8",FORCED=NO,CHANNELS="2"
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES,URI="subtitles/eng/prog_index.m3u8",FORCED=NO
    #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="fr",NAME="Français",AUTOSELECT=YES,DEFAULT=NO,URI="subtitles/fra/prog_index.m3u8",FORCED=NO
    """
    mock_hls_response.raise_for_status = MagicMock()

    # Add mock response for English subtitles manifest (fallback)
    mock_en_subtitles_response = MagicMock(spec=Response)
    mock_en_subtitles_response.text = """
    #EXTM3U
    #EXT-X-TARGETDURATION:7
    #EXT-X-VERSION:3
    #EXT-X-MEDIA-SEQUENCE:0
    #EXT-X-PLAYLIST-TYPE:VOD
    #EXTINF:6.006
    sequence_0.webvtt
    #EXTINF:6.006
    sequence_1.webvtt
    #EXT-X-ENDLIST
    """
    mock_en_subtitles_response.raise_for_status = MagicMock()

    # Add mock responses for English WebVTT content
    mock_en_webvtt_responses = []
    for i in range(2):
        mock_webvtt = MagicMock(spec=Response)
        mock_webvtt.text = (
            f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\nEnglish subtitle {i}"
        )
        mock_webvtt.raise_for_status = MagicMock()
        mock_en_webvtt_responses.append(mock_webvtt)

    # Set up the client to return different responses based on the URL
    def mock_get_side_effect(url: str) -> Response:
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
            return mock_en_subtitles_response

        # Handle English WebVTT URL requests
        for i in range(2):
            webvtt_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_{i}.webvtt"
            if url == webvtt_url:
                return mock_en_webvtt_responses[i]

        raise ValueError(f"Unexpected URL: {url}")

    mock_client.get.side_effect = mock_get_side_effect

    # Call function with a language that doesn't exist in the manifest
    session = await fetch_session_data(
        f"https://developer.apple.com/videos/play/wwdc{test_year}/10144",
        language="ja",  # Japanese is not available in this mock
    )

    # Verify session data
    assert session.id == "10144"
    assert session.title == "Building Great Apps"
    assert session.year == test_year

    # Verify English subtitles URL is used as fallback
    assert (
        session.subtitles_url
        == f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/prog_index.m3u8"
    )

    # Verify WebVTT URLs are correctly extracted (English as fallback)
    assert len(session.webvtt_urls) == 2
    for i in range(2):
        expected_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{test_year}/10144/4/8A69C683-3259-454B-9F94-5BBE98999A1B/subtitles/eng/sequence_{i}.webvtt"
        assert session.webvtt_urls[i] == expected_url

    # Test fetching WebVTT content
    content = await session.fetch_webvtt()
    assert len(content) == 2
    for i in range(2):
        expected_content = (
            f"WEBVTT\n\n00:00:0{i}.000 --> 00:00:0{i + 1}.000\nEnglish subtitle {i}"
        )
        assert content[i] == expected_content
