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


async def _extract_subtitles_url(hls_url: str | None) -> str | None:
    """Extract the English subtitles URL from the HLS manifest.

    Args:
        hls_url: The URL to the HLS manifest file.

    Returns:
        The URL to the English subtitles, or None if not available.
    """
    if not hls_url:
        logger.debug("No HLS URL provided, skipping subtitles extraction")
        return None

    try:
        logger.debug(f"Fetching HLS manifest from {hls_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(hls_url)
            response.raise_for_status()

            manifest_content = response.text
            logger.debug("Parsing HLS manifest for subtitles")

            # Regular expression to find the English subtitles entry
            # Looking for: #EXT-X-MEDIA:TYPE=SUBTITLES,.*LANGUAGE="en",.*URI="(.+?)"
            subtitles_pattern = re.compile(
                r'#EXT-X-MEDIA:.*TYPE=SUBTITLES,.*LANGUAGE="en".*URI="(.+?)"',
                re.IGNORECASE,
            )

            match = subtitles_pattern.search(manifest_content)
            if match:
                subtitles_uri = match.group(1)
                logger.debug(f"Found English subtitles URI: {subtitles_uri}")

                # Construct the full URL by joining with the base HLS URL
                base_url = hls_url.rsplit("/", 1)[0] + "/"
                full_subtitles_url = urljoin(base_url, subtitles_uri)
                logger.debug(f"Constructed subtitles URL: {full_subtitles_url}")
                return full_subtitles_url

            logger.debug("No English subtitles found in the manifest")
            return None
    except httpx.HTTPError as e:
        logger.error(f"Error fetching HLS manifest: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting subtitles URL: {e}")
        return None


async def _extract_webvtt_urls(subtitles_url: str | None) -> list[str]:
    """Extract WebVTT URLs from the subtitles manifest.

    Args:
        subtitles_url: The URL to the subtitles manifest file.

    Returns:
        A list of URLs to WebVTT subtitle files.
    """
    if not subtitles_url:
        logger.debug("No subtitles URL provided, skipping WebVTT extraction")
        return []

    try:
        logger.debug(f"Fetching subtitles manifest from {subtitles_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(subtitles_url)
            response.raise_for_status()

            manifest_content = response.text
            logger.debug("Parsing subtitles manifest for WebVTT URLs")

            # Regular expression to find the WebVTT segment entries in m3u8 playlist
            # Looking for lines that don't start with # and end with .webvtt
            webvtt_pattern = re.compile(r"^(?!#).*\.webvtt$", re.MULTILINE)

            matches = webvtt_pattern.findall(manifest_content)
            if matches:
                base_url = subtitles_url.rsplit("/", 1)[0] + "/"
                webvtt_urls = [urljoin(base_url, uri) for uri in matches]
                logger.debug(f"Found {len(webvtt_urls)} WebVTT URLs")
                return webvtt_urls

            logger.debug("No WebVTT URLs found in the subtitles manifest")
            return []
    except httpx.HTTPError as e:
        logger.error(f"Error fetching subtitles manifest: {e}")
        return []
    except Exception as e:
        logger.error(f"Error extracting WebVTT URLs: {e}")
        return []


async def fetch_webvtt_from_urls(webvtt_urls: list[str]) -> list[str]:
    """Fetch content of WebVTT files from the provided URLs.

    Args:
        webvtt_urls: A list of URLs to WebVTT subtitle files.

    Returns:
        A list of WebVTT content strings.
    """
    if not webvtt_urls:
        logger.debug("No WebVTT URLs provided, skipping content fetching")
        return []

    webvtt_content = []
    try:
        logger.debug(f"Fetching content from {len(webvtt_urls)} WebVTT URLs")
        async with httpx.AsyncClient() as client:
            for url in webvtt_urls:
                try:
                    logger.debug(f"Fetching WebVTT content from {url}")
                    response = await client.get(url)
                    response.raise_for_status()
                    webvtt_content.append(response.text)
                    logger.debug(f"Successfully fetched WebVTT content from {url}")
                except httpx.HTTPError as e:
                    logger.error(f"Error fetching WebVTT content from {url}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error fetching WebVTT from {url}: {e}")

        logger.debug(f"Fetched content from {len(webvtt_content)} WebVTT files")
        return webvtt_content
    except Exception as e:
        logger.error(f"Error in WebVTT content fetching: {e}")
        return []


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
    subtitles_url = await _extract_subtitles_url(hls_url)
    webvtt_urls = await _extract_webvtt_urls(subtitles_url)

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
        subtitles_url=subtitles_url,
        webvtt_urls=webvtt_urls,
        webvtt_content=[],
    )
