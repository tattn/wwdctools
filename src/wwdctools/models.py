"""Data models for WWDC content."""

from pydantic import BaseModel

from .logger import logger


class WWDCSampleCode(BaseModel):
    """Represents a code sample from a WWDC session."""

    time: float  # timestamp in seconds
    title: str
    code: str


class WWDCSession(BaseModel):
    """Represents a WWDC session with its metadata and content links."""

    id: str  # e.g., "10001"
    title: str
    description: str
    year: int  # e.g., 2024
    url: str
    video_id: str | None = None  # e.g., "4/8A69C683-3259-454B-9F94-5BBE98999A1B"
    hls_url: str | None = None  # URL to the cmaf.m3u8 HLS stream
    subtitles_url: str | None = None  # URL to the English subtitles
    webvtt_urls: list[str] = []  # URLs to WebVTT subtitle files
    webvtt_content: list[str] = []  # Content of WebVTT subtitle files
    transcript_content: str | None = None
    sample_code_url: str | None = None
    sample_codes: list[WWDCSampleCode] = []

    def generate_video_url(self, quality: str = "hd") -> str | None:
        """Generate download video URL from video ID.

        Args:
            quality: The video quality. Either "hd" or "sd". Defaults to "hd".

        Returns:
            The download video URL, or None if video_id is not available.
        """
        if not self.video_id:
            return None

        base_url = f"https://devstreaming-cdn.apple.com/videos/wwdc/{self.year}/{self.id}/{self.video_id}/downloads"
        return f"{base_url}/wwdc{self.year}-{self.id}_{quality}.mp4?dl=1"

    async def fetch_webvtt(self) -> list[str]:
        """Fetch WebVTT content from URLs.

        This method fetches the WebVTT content if it hasn't been fetched already.
        For efficiency, the content is fetched only once and cached.

        Returns:
            A list of WebVTT content strings.
        """
        if not self.webvtt_urls:
            logger.debug("No WebVTT URLs available")
            return []

        # Return cached content if already fetched
        if self.webvtt_content:
            logger.debug("Returning cached WebVTT content")
            return self.webvtt_content

        # Import here to avoid circular dependency
        from .session import fetch_webvtt_from_urls

        # Fetch content from URLs
        self.webvtt_content = await fetch_webvtt_from_urls(self.webvtt_urls)
        return self.webvtt_content


class WWDCTranscript(BaseModel):
    """Represents a transcript from a WWDC session."""

    session_id: str
    content: str
    timestamps: dict[str, float]
