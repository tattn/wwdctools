# wwdctools

Unlock the full potential of WWDC content with `wwdctools`! Download videos, transcripts, sample code, and subtitles from Apple's WWDC sessions seamlessly. Whether you're a developer, researcher, or simply keen to learn, `wwdctools` provides the tools you need to access and manage WWDC content with ease, through a powerful Command Line Interface (CLI) and a flexible Python API.

## Key features

- **Download complete session content**: Get videos, transcripts, and code with a single command.
- **Fetch detailed transcripts**: Obtain session transcripts in various formats (TXT, Markdown, JSON).
- **Extract all code samples**: Access inline snippets and downloadable sample code files.
- **Retrieve WebVTT subtitles**: Download subtitle files for session videos.
- **Latest WWDC content**: Always updated to support the newest sessions.
- **Dual interface**: Use it as a CLI tool or integrate it as a Python library.

## Quick start

You can use `wwdctools` via its CLI or as a Python library. Here’s how to quickly download all content for a single session:

**CLI example:**
```bash
wwdctools download <session_url> --output downloads/
```

**Python API example:**
```python
import asyncio
from wwdctools import fetch_session_data, download_session_content

async def main():
    session_url = "https://developer.apple.com/videos/play/wwdc2024/10144"  # Example URL
    session = await fetch_session_data(session_url)
    downloads = await download_session_content(session, "downloads")
    print(f"Downloaded content: {downloads}")

asyncio.run(main())
```

## Installation

To install `wwdctools` for use, run the following command in your terminal:

```bash
uv pip install wwdctools
```
This will download and install `wwdctools` and its dependencies from PyPI.

## Requirements

- Python 3.13 or higher

## Advanced transcript handling

This section details how to work with transcripts using both the CLI and Python API.

### CLI usage

Display the transcript directly in your terminal:
```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144
```

Save the transcript to a file:
```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.txt
```

Fetch multiple transcripts and save them to a directory:
```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 https://developer.apple.com/videos/play/wwdc2024/10145 --output transcripts/
```

Fetch multiple transcripts and combine them into a single file:
```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 https://developer.apple.com/videos/play/wwdc2024/10145 --output combined.txt --combine
```

Save the transcript in different formats (e.g., Markdown or JSON):
```bash
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.md --format md
wwdctools transcript https://developer.apple.com/videos/play/wwdc2024/10144 --output transcript.json --format json
```

### Python API usage
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

## Advanced Code Extraction

Extract code samples from sessions and save them in various formats.

### CLI usage

Extract code samples from a session and print to console:
```bash
# Extract code samples from a session
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144
```

Save code samples to a directory:
```bash
# Save code samples to a directory
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144 --output code_samples/
```

Choose the output format (e.g., Markdown or JSON):
```bash
# Choose output format (txt/md/json)
wwdctools code https://developer.apple.com/videos/play/wwdc2024/10144 --output samples.md --format md
```

### Python API usage
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

## Advanced Subtitle Management

Download WebVTT subtitle files from WWDC session pages.

### CLI usage

Display WebVTT information in your terminal:
```bash
# Display WebVTT information in terminal
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144
```

Save WebVTT files to a directory:
```bash
# Save WebVTT files to a directory
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144 --output subtitles/
```

Combine all WebVTT files into a single file:
```bash
# Combine all WebVTT files into a single file
wwdctools webvtt https://developer.apple.com/videos/play/wwdc2024/10144 --output combined.webvtt --combine
```

### Python API usage
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

If you want to contribute to `wwdctools` or run it from the source code, follow these instructions to set up a development environment.

### Setup development environment
```bash
# Clone the repository
git clone https://github.com/tattn/wwdctools.git
cd wwdctools

# Install development dependencies, including wwdctools in editable mode
uv pip install -e .[dev]
# Alternatively, if you have a uv.lock file and want to sync exactly:
# uv sync --dev
```

### Testing and code quality
All testing and quality checks are run using `uv run`. These commands assume you are in the root of the project directory.

```bash
# Run tests (uses pytest with anyio)
uv run --frozen pytest

# If pytest fails to find anyio mark (e.g., in some CI environments)
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
