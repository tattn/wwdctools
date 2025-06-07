"""Session data retrieval functionality."""

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .logger import logger
from .models import WWDCSampleCode, WWDCSession


async def fetch_session_data(url: str) -> WWDCSession:  # noqa: PLR0912, PLR0915
    """Fetch session data from a WWDC session URL.

    Args:
        url: The URL of the WWDC session page.

    Returns:
        A WWDCSession object containing the session metadata and content links.

    Raises:
        ValueError: If the URL is not a valid WWDC session URL.
        httpx.HTTPError: If there's an error fetching the page.
    """
    logger.debug(f"Validating URL: {url}")
    url_pattern = r"https?://developer\.apple\.com/videos/play/wwdc(\d{4})/(\d+)"
    match = re.match(url_pattern, url)
    if not match:
        logger.error(f"Invalid URL format: {url}")
        raise ValueError(f"Invalid WWDC session URL: {url}")

    year = int(match.group(1))
    session_id = match.group(2)
    logger.debug(f"Extracted year={year}, session_id={session_id}")

    async with httpx.AsyncClient() as client:
        logger.debug(f"Fetching content from {url}")
        response = await client.get(url)
        response.raise_for_status()
        # Ensure mock compatibility: status_code may not exist on MagicMock unless set
        status_code = getattr(response, "status_code", None)
        logger.debug(f"Received response: {status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug("Parsing HTML content")

        # Extract title
        title_elem = soup.select_one("h1")
        title = title_elem.text.strip() if title_elem else "Unknown Title"

        # Extract description
        desc_elem = soup.select_one("p.description")
        description = desc_elem.text.strip() if desc_elem else ""

        # Find video ID and HLS URL
        video_id = None
        hls_url = None

        # Look for video ID and HLS URL in meta tag (og:video)
        og_video_meta = soup.select_one("meta[property='og:video']")
        if og_video_meta and hasattr(og_video_meta, "get"):
            hls_url = og_video_meta.get("content")  # type: ignore
            if hls_url and isinstance(hls_url, str):
                logger.debug(f"Found HLS URL: {hls_url}")

                # Extract video ID from content URL
                # (e.g., "4/8A69C683-3259-454B-9F94-5BBE98999A1B")
                video_id_match = re.search(
                    r"/videos/wwdc/\d+/\d+/([^/]+/[^/]+)", hls_url
                )
                if video_id_match:
                    video_id = video_id_match.group(1)
                    logger.debug(f"Found video ID from meta: {video_id}")

        # If video ID not found in meta, try to extract from download links
        if not video_id:
            download_link = soup.select_one("a[href*='downloads/wwdc']")
            if download_link and hasattr(download_link, "get"):
                href = download_link.get("href")  # type: ignore
                if href and isinstance(href, str):
                    # Extract video ID from download URL
                    video_id_match = re.search(
                        r"/videos/wwdc/\d+/\d+/([^/]+/[^/]+)/downloads/", href
                    )
                    if video_id_match:
                        video_id = video_id_match.group(1)
                        logger.debug(f"Found video ID from download link: {video_id}")

        # Transcript extraction (JS equivalent)
        sentence_elements = soup.select(".sentence")
        if sentence_elements:
            transcript_text = "".join(e.get_text() for e in sentence_elements)  # type: ignore
            transcript_text = re.sub(r"(\r\n|\n|\r)", "", transcript_text)
            transcript_text = re.sub(r"( )", " ", transcript_text)
            transcript_text = re.sub(r"\.", ".\n", transcript_text)
            transcript_content = transcript_text
        else:
            transcript_content = None

        # Find sample code URL
        sample_code_elem = soup.select_one("a[href*='sample-code']")
        sample_code_url = None
        if sample_code_elem and hasattr(sample_code_elem, "get"):
            href = sample_code_elem.get("href")  # type: ignore
            if href and isinstance(href, str):
                sample_code_url = urljoin(url, href)

        # Extract sample codes from the HTML
        sample_codes = []
        code_blocks = soup.select("pre.code-source")
        for code_block in code_blocks:
            # Find the preceding <p> tag with time information
            prev_p = code_block.find_previous("p")
            if prev_p:
                # Extract timestamp and title
                time_info = (
                    prev_p.get_text().strip() if hasattr(prev_p, "get_text") else ""
                )
                time_match = re.search(r"(\d+):(\d+)", time_info)
                time_in_seconds = 0.0

                if time_match:
                    minutes = int(time_match.group(1))
                    seconds = int(time_match.group(2))
                    time_in_seconds = float(minutes * 60 + seconds)

                # Extract title from jump-to-time-sample link
                title = ""
                if hasattr(prev_p, "find"):
                    title_link = prev_p.find("a", {"class": "jump-to-time-sample"})  # type: ignore
                    if title_link and hasattr(title_link, "get_text"):
                        title = title_link.get_text().strip()  # type: ignore

                # Extract code content
                code_content = ""
                if hasattr(code_block, "find"):
                    code_element = code_block.find("code")  # type: ignore
                    if code_element and hasattr(code_element, "get_text"):
                        code_content = code_element.get_text().strip()  # type: ignore

                # Create sample code object
                if code_content:
                    sample_code = WWDCSampleCode(
                        time=time_in_seconds, title=title, code=code_content
                    )
                    sample_codes.append(sample_code)
                    logger.debug(f"Found sample code: {title} at {time_in_seconds}s")

        return WWDCSession(
            id=session_id,
            title=title,
            description=description,
            year=year,
            url=url,
            video_id=video_id,
            hls_url=hls_url,
            transcript_content=transcript_content,
            sample_code_url=sample_code_url,
            sample_codes=sample_codes,
        )
