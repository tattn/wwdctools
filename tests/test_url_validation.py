"""Tests for URL validation with language prefixes."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import Response

from wwdctools.session import _validate_session_url, fetch_session_data


def test_validate_standard_session_url() -> None:
    """Test standard URL validation."""
    url = "https://developer.apple.com/videos/play/wwdc2024/10144"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2024
    assert session_id == "10144"
    assert lang_code is None


def test_validate_https_session_url() -> None:
    """Test HTTPS URL validation."""
    url = "https://developer.apple.com/videos/play/wwdc2025/102"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2025
    assert session_id == "102"
    assert lang_code is None


def test_validate_http_session_url() -> None:
    """Test HTTP URL validation."""
    url = "http://developer.apple.com/videos/play/wwdc2025/102"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2025
    assert session_id == "102"
    assert lang_code is None


def test_validate_japanese_session_url() -> None:
    """Test Japanese URL validation."""
    url = "https://developer.apple.com/jp/videos/play/wwdc2025/102/"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2025
    assert session_id == "102"
    assert lang_code == "jp"


def test_validate_other_language_session_url() -> None:
    """Test other language URL validation."""
    url = "https://developer.apple.com/kr/videos/play/wwdc2025/102"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2025
    assert session_id == "102"
    assert lang_code == "kr"


def test_validate_session_url_with_trailing_slash() -> None:
    """Test URL validation with trailing slash."""
    url = "https://developer.apple.com/videos/play/wwdc2025/102/"
    year, session_id, lang_code = _validate_session_url(url)
    assert year == 2025
    assert session_id == "102"
    assert lang_code is None


def test_validate_invalid_session_url() -> None:
    """Test invalid URL validation."""
    invalid_urls = [
        "https://developer.apple.com/videos/wwdc2025/102",
        "https://developer.apple.com/videos/play/not-wwdc/102",
        "https://example.com/videos/play/wwdc2025/102",
        "https://developer.apple.com/videos/play/wwdc/102",
    ]

    for url in invalid_urls:
        with pytest.raises(ValueError, match="Invalid WWDC session URL"):
            _validate_session_url(url)


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_with_localized_url(mock_client_class: Any) -> None:
    """Test fetching session data from a localized URL."""
    test_year = 2025
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

    # Call function with a localized URL
    localized_url = "https://developer.apple.com/jp/videos/play/wwdc2025/102"
    session = await fetch_session_data(localized_url)

    # Verify results
    assert session.id == "102"
    assert session.title == "Building Great Apps"
    assert session.description == "Learn how to build great apps for Apple platforms."
    assert session.year == test_year
    assert session.url == localized_url

    # Verify mocks were called correctly with the localized URL
    mock_client.get.assert_called_once_with(localized_url)


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
async def test_fetch_session_data_with_another_localized_url(
    mock_client_class: Any,
) -> None:
    """Test fetching session data from another localized URL."""
    test_year = 2025
    # Setup mocks
    mock_client = mock_client_class.return_value.__aenter__.return_value
    mock_response = MagicMock(spec=Response)
    mock_response.text = """
    <html>
        <head><title>WWDC Session</title></head>
        <body>
            <h1>素晴らしいアプリの構築</h1>
            <p class="description">
                Apple プラットフォーム向けに素晴らしいアプリを構築する方法を学びます。
            </p>
            <video>
                <source src="https://example.com/video.mp4" type="video/mp4">
            </video>
            <a href="/downloads/sample-code/building-great-apps.zip">
                サンプルコードをダウンロード
            </a>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()

    mock_client.get.return_value = mock_response

    # Call function with another localized URL
    another_localized_url = "https://developer.apple.com/kr/videos/play/wwdc2025/102"
    session = await fetch_session_data(another_localized_url)

    # Verify results
    assert session.id == "102"
    assert session.title == "素晴らしいアプリの構築"
    assert (
        session.description
        == "Apple プラットフォーム向けに素晴らしいアプリを構築する方法を学びます。"
    )
    assert session.year == test_year
    assert session.url == another_localized_url

    # Verify mocks were called correctly with the localized URL
    mock_client.get.assert_called_once_with(another_localized_url)


@pytest.mark.anyio
@patch("wwdctools.session.httpx.AsyncClient")
@patch("wwdctools.session._extract_subtitles_url")
async def test_language_detection_from_url(
    mock_extract_subtitles: Any, mock_client_class: Any
) -> None:
    """Test that language code from URL is used for subtitles."""
    # Setup mocks
    mock_client = mock_client_class.return_value.__aenter__.return_value
    mock_response = MagicMock(spec=Response)
    mock_response.text = """
    <html>
        <head><title>WWDC Session</title></head>
        <body>
            <h1>日本語のセッション</h1>
            <p class="description">
                日本語の説明文です。
            </p>
            <video>
                <source src="https://example.com/video.mp4" type="video/mp4">
            </video>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()

    mock_client.get.return_value = mock_response
    mock_extract_subtitles.return_value = (
        "https://example.com/subtitles/jpn/prog_index.m3u8"
    )

    # Call function with a Japanese localized URL, no explicit language specified
    jp_url = "https://developer.apple.com/jp/videos/play/wwdc2025/102"
    await fetch_session_data(jp_url)  # Default language is "en"

    # Verify that the Japanese language code from URL was used
    mock_extract_subtitles.assert_called_once()
    call_args = mock_extract_subtitles.call_args[0]
    assert call_args[1] == "ja"  # Second arg is language code
