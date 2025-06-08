# wwdctools

A tool for fetching videos, transcripts, and sample code from Apple's WWDC session pages.

## Features

- Download videos from WWDC session pages (HD/SD quality available)
- Extract transcripts from WWDC sessions (supports txt/md/json formats)
- Download WebVTT subtitle files for video content
- Download sample code files and inline code snippets
- Extract code samples with timestamps and titles
- Support for latest WWDC content
- Command line interface (CLI) and Python API

## Installation

You can install the package using `uv`:

```bash
uv add wwdctools
```

## Requirements

- Python 3.13 or higher

## Usage

### Downloading Content

You can download videos, transcripts, and sample code using a single command:

```bash
# Download all content (video, transcript, sample code) from a session
wwdctools download https://developer.apple.com/videos/play/wwdc2024/10144

# Specify output directory
wwdctools download https://developer.apple.com/videos/play/wwdc2024/10144 --output downloads/
```

#### Use the Python API

```python
import asyncio
from wwdctools import fetch_session_data, download_session_content

async def download_wwdc():
    # Fetch session data
    session = await fetch_session_data("https://developer.apple.com/videos/play/wwdc2024/10144")

    # Download all content (returns a dict of downloaded file paths)
    downloads = await download_session_content(session, "downloads")

    # Access downloaded files
    video_path = downloads.get("video")
    transcript_path = downloads.get("transcript")
    sample_code_path = downloads.get("sample_code")
    code_samples_dir = downloads.get("code_samples")
    webvtt_dir = downloads.get("webvtt")

# Run the async function
asyncio.run(download_wwdc())
```

### Working with Transcripts

#### Display transcript in terminal

```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144
```

#### Save transcript to a file

```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.txt
```

#### Fetch multiple transcripts and save to a directory

```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 https://developer.apple.com/videos/play/wwdc2024/10145 --output transcripts/
```

#### Fetch multiple transcripts and combine them into a single file

```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 https://developer.apple.com/videos/play/wwdc2024/10145 --output combined.txt --combine
```

#### Save transcript in different formats

```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.md --format md
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.json --format json
```

#### Using Python API

```python
import asyncio
from wwdctools import fetch_session_data, fetch_transcript

async def get_transcript(url):
    session = await fetch_session_data(url)
    if session.transcript_content:
        transcript = session.transcript_content
        return transcript
    return None

# Run the async function
transcript = asyncio.run(get_transcript("https://developer.apple.com/videos/play/wwdc2024/10144"))
print(transcript)
```

### Working with Code Samples

Code samples can be extracted and saved in various formats:

```bash
# Extract code samples from a session
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144

# Save code samples to a directory
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144 --output code_samples/

# Choose output format (txt/md/json)
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144 --output samples.md --format md
```

#### Using Python API

```python
import asyncio
from wwdctools import fetch_session_data

async def extract_code():
    # Fetch session data
    session = await fetch_session_data("https://developer.apple.com/videos/play/wwdc2024/10144")

    # Access code samples
    for sample in session.code_samples:
        print(f"Title: {sample.title}")
        print(f"Timestamp: {sample.timestamp}")
        print(f"Code:\n{sample.code}\n")

    # Access downloadable sample code URL if available
    if session.sample_code_url:
        print(f"Sample code download: {session.sample_code_url}")

# Run the async function
asyncio.run(extract_code())
```

### Working with WebVTT Subtitles

You can download WebVTT subtitle files from WWDC session pages:

```bash
# Display WebVTT information in terminal
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144

# Save WebVTT files to a directory
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144 --output subtitles/

# Combine all WebVTT files into a single file
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144 --output combined.webvtt --combine
```

#### Using Python API

```python
import asyncio
from wwdctools import fetch_session_data

async def get_webvtt():
    # Fetch session data
    session = await fetch_session_data("https://developer.apple.com/videos/play/wwdc2024/10144")

    # Fetch WebVTT content
    webvtt_content = await session.fetch_webvtt()

    # Process WebVTT content
    for i, content in enumerate(webvtt_content):
        print(f"WebVTT sequence {i}:\n{content[:100]}...")  # Print first 100 chars

# Run the async function
asyncio.run(get_webvtt())
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/tattn/wwdctools.git
cd wwdctools

# Install development dependencies with uv (not pip)
uv add --dev .[dev]
```

### Testing and Code Quality

```bash
# Run tests (uses pytest with anyio)
uv run --frozen pytest

# If pytest fails to find anyio mark
PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest

# Format code
uv run --frozen ruff format .

# Run linting
uv run --frozen ruff check .

# Fix auto-fixable issues
uv run --frozen ruff check . --fix

# Run type checking
uv run --frozen pyright
```

## License

MIT
