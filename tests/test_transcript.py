"""Tests for transcript fetching functionality."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from wwdctools.transcript import fetch_transcript


class TestTranscriptFunctions:
    """Tests for transcript-related functions."""

    @pytest.mark.anyio
    @patch("wwdctools.transcript.httpx.AsyncClient")
    async def test_fetch_transcript_http_error(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test HTTP error handling in fetch_transcript."""
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )

        mock_client.get.return_value = mock_response

        with pytest.raises(HTTPStatusError):
            await fetch_transcript("https://example.com/transcript.vtt")

    @pytest.mark.anyio
    @patch("wwdctools.transcript.httpx.AsyncClient")
    async def test_fetch_transcript_request_error(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test request error handling in fetch_transcript."""
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get.side_effect = RequestError("Connection error")

        with pytest.raises(RequestError):
            await fetch_transcript("https://example.com/transcript.vtt")
