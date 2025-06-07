"""Tests for sample code extraction functionality."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import Response

from wwdctools.session import fetch_session_data


@pytest.mark.anyio
async def test_sample_code_extraction() -> None:
    """Test sample code extraction from session page."""
    # Mock the httpx.AsyncClient to return our custom HTML
    with patch("wwdctools.session.httpx.AsyncClient") as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        # HTML with sample code as shown in the example
        mock_response.text = """
        <html>
            <head><title>WWDC Session</title></head>
            <body>
                <h1>Session Title</h1>
                <p class="description">Session description text</p>

                <p>0:02 - <a class="jump-to-time-sample" href="/videos/play/wwdc2024/10118/?time=2"
                   data-start-time="2">Setting failure requirements between gestures</a></p>
                <pre class="code-source"><code><span class="syntax-comment">// Inner SwiftUI double tap gesture</span>

<span class="syntax-type">Circle</span>()
.gesture(doubleTap, name: <span class="syntax-string">"SwiftUIDoubleTap"</span>)


<span class="syntax-comment">// Outer UIKit single tap gesture</span>

<span class="syntax-keyword">func</span> <span class="syntax-title function_">gestureRecognizer</span>(
<span class="syntax-keyword">_</span> <span class="syntax-params">gestureRecognizer</span>:
<span class="syntax-type">UIGestureRecognizer</span>,
<span class="syntax-params">shouldRequireFailureOf</span> <span class="syntax-params">other</span>:
<span class="syntax-type">UIGestureRecognizer</span>
) -&gt; <span class="syntax-type">Bool</span> {
other.name <span class="syntax-operator">==</span>
<span class="syntax-string">"SwiftUIDoubleTap"</span>
}</code></pre>

                <p>1:30 - <a class="jump-to-time-sample" href="/videos/play/wwdc2024/10118/?time=90"
                   data-start-time="90">Another sample code</a></p>
                <pre class="code-source"><code><span class="syntax-keyword">let</span> x =
                <span class="syntax-number">42</span></code></pre>
            </body>
        </html>
        """

        mock_client.get.return_value = mock_response

        # Call the function
        session = await fetch_session_data(
            "https://developer.apple.com/videos/play/wwdc2024/10118"
        )

        # Verify the sample codes were extracted correctly
        assert len(session.sample_codes) == 2

        # Verify first sample code
        assert session.sample_codes[0].time == 2.0
        assert (
            session.sample_codes[0].title
            == "Setting failure requirements between gestures"
        )
        # Check code content in parts due to whitespace preservation
        assert "// Inner SwiftUI double tap gesture" in session.sample_codes[0].code
        assert "Circle()" in session.sample_codes[0].code
        assert "other.name" in session.sample_codes[0].code
        assert "SwiftUIDoubleTap" in session.sample_codes[0].code

        # Verify second sample code
        assert session.sample_codes[1].time == 90.0
        assert session.sample_codes[1].title == "Another sample code"
        # Check code content in parts due to whitespace preservation
        assert "let x =" in session.sample_codes[1].code
        assert "42" in session.sample_codes[1].code
