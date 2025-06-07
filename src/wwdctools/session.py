"""Session data retrieval functionality."""

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from .logger import logger
from .models import WWDCSampleCode, WWDCSession


def _validate_session_url(url: str) -> tuple[int, str]:
    """Validate a WWDC session URL and extract year and session ID.

    Args:
        url: The URL of the WWDC session page.

    Returns:
        A tuple of (year, session_id).

    Raises:
        ValueError: If the URL is not a valid WWDC session URL.
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
    return year, session_id


async def _fetch_page_content(url: str) -> BeautifulSoup:
    """Fetch and parse the HTML content from a URL.

    Args:
        url: The URL to fetch.

    Returns:
        A BeautifulSoup object containing the parsed HTML.

    Raises:
        httpx.HTTPError: If there's an error fetching the page.
    """
    async with httpx.AsyncClient() as client:
        logger.debug(f"Fetching content from {url}")
        response = await client.get(url)
        response.raise_for_status()
        # Ensure mock compatibility: status_code may not exist on MagicMock unless set
        status_code = getattr(response, "status_code", None)
        logger.debug(f"Received response: {status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug("Parsing HTML content")
        return soup


def _extract_basic_metadata(soup: BeautifulSoup) -> tuple[str, str]:
    """Extract title and description from the soup object.

    Args:
        soup: The BeautifulSoup object containing the parsed HTML.

    Returns:
        A tuple of (title, description).
    """
    # Extract title
    title_elem = soup.select_one("h1")
    title = title_elem.text.strip() if title_elem else "Unknown Title"

    # Extract description
    desc_elem = soup.select_one("p.description")
    description = desc_elem.text.strip() if desc_elem else ""

    return title, description


def _extract_video_metadata(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extract video ID and HLS URL from the soup object.

    Args:
        soup: The BeautifulSoup object containing the parsed HTML.

    Returns:
        A tuple of (video_id, hls_url).
    """
    video_id = None
    hls_url = None

    # Look for video ID and HLS URL in meta tag (og:video)
    og_video_meta = soup.select_one("meta[property='og:video']")
    if og_video_meta and hasattr(og_video_meta, "get"):
        content = og_video_meta.get("content")  # type: ignore
        if content and isinstance(content, str):
            hls_url = content
            logger.debug(f"Found HLS URL: {hls_url}")

            # Extract video ID from content URL
            # (e.g., "4/8A69C683-3259-454B-9F94-5BBE98999A1B")
            video_id_match = re.search(r"/videos/wwdc/\d+/\d+/([^/]+/[^/]+)", hls_url)
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

    return video_id, hls_url


def _extract_transcript(soup: BeautifulSoup) -> str | None:
    """Extract transcript content from the soup object.

    Args:
        soup: The BeautifulSoup object containing the parsed HTML.

    Returns:
        The transcript content, or None if not available.
    """
    sentence_elements = soup.select(".sentence")
    if not sentence_elements:
        return None

    text = "".join(e.get_text() for e in sentence_elements)  # type: ignore
    text = re.sub(r"(\r\n|\n|\r)", "", text)
    text = re.sub(r"( )", " ", text)
    return re.sub(r"\.", ".\n", text)


def _extract_sample_code_url(soup: BeautifulSoup, base_url: str) -> str | None:
    """Extract sample code URL from the soup object.

    Args:
        soup: The BeautifulSoup object containing the parsed HTML.
        base_url: The base URL for resolving relative URLs.

    Returns:
        The sample code URL, or None if not available.
    """
    sample_code_elem = soup.select_one("a[href*='sample-code']")
    if sample_code_elem and hasattr(sample_code_elem, "get"):
        href = sample_code_elem.get("href")  # type: ignore
        if href and isinstance(href, str):
            return urljoin(base_url, href)
    return None


def _extract_sample_code_time(prev_p: Tag) -> tuple[float, str]:
    """Extract timestamp and title from a paragraph tag.

    Args:
        prev_p: The paragraph tag containing time information.

    Returns:
        A tuple of (time_in_seconds, title).
    """
    # Extract timestamp and title
    time_info = prev_p.get_text().strip() if hasattr(prev_p, "get_text") else ""
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
    return time_in_seconds, title


def _extract_sample_codes(soup: BeautifulSoup) -> list[WWDCSampleCode]:
    """Extract sample codes from the soup object.

    Args:
        soup: The BeautifulSoup object containing the parsed HTML.

    Returns:
        A list of WWDCSampleCode objects.
    """
    sample_codes = []
    code_blocks = soup.select("pre.code-source")

    for code_block in code_blocks:
        # Find the preceding <p> tag with time information
        prev_p = code_block.find_previous("p")
        if prev_p and isinstance(prev_p, Tag):
            time_in_seconds, title = _extract_sample_code_time(prev_p)

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

    return sample_codes


async def fetch_session_data(url: str) -> WWDCSession:
    """Fetch session data from a WWDC session URL.

    Args:
        url: The URL of the WWDC session page.

    Returns:
        A WWDCSession object containing the session metadata and content links.

    Raises:
        ValueError: If the URL is not a valid WWDC session URL.
        httpx.HTTPError: If there's an error fetching the page.
    """
    year, session_id = _validate_session_url(url)
    soup = await _fetch_page_content(url)

    title, description = _extract_basic_metadata(soup)
    video_id, hls_url = _extract_video_metadata(soup)
    transcript_content = _extract_transcript(soup)
    sample_code_url = _extract_sample_code_url(soup, url)
    sample_codes = _extract_sample_codes(soup)

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
