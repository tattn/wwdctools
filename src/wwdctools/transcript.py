"""Transcript retrieval and processing functionality."""

import re

import httpx
from bs4 import BeautifulSoup


async def fetch_transcript(url: str) -> str:
    """Fetch and parse transcript content from a WWDC session URL.

    Args:
        url: The URL of the WWDC session page.

    Returns:
        The transcript content as text.

    Raises:
        httpx.HTTPError: If there's an error fetching the transcript.
        ValueError: If the transcript content is not found.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        sentence_elements = soup.select(".sentence")
        if sentence_elements:
            transcript_text = "".join(e.get_text() for e in sentence_elements)
            transcript_text = re.sub(r"(\r\n|\n|\r)", "", transcript_text)
            transcript_text = re.sub(r"( )", " ", transcript_text)
            return re.sub(r".", ".\n", transcript_text)
        raise ValueError("Transcript content not found on the page.")
