"""Data models for WWDC content."""

from pydantic import BaseModel


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
    transcript_content: str | None = None
    sample_code_url: str | None = None
    sample_codes: list[WWDCSampleCode] = []

    def generate_video_url(self, quality: str = "hd") -> str | None:
        """Generate the video URL from year, session id, and video id.

        Args:
            quality: The video quality. Either "hd" or "sd". Defaults to "hd".

        Returns:
            The generated video URL or None if video_id is not available.
        """
        if not self.video_id:
            return None

        return (
            f"https://devstreaming-cdn.apple.com/videos/wwdc/{self.year}/"
            f"{self.id}/{self.video_id}/downloads/wwdc{self.year}-{self.id}_{quality}.mp4?dl=1"
        )


class WWDCTranscript(BaseModel):
    """Represents a transcript from a WWDC session."""

    session_id: str
    content: str
    timestamps: dict[str, float]
