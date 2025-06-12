#!/usr/bin/env python
"""Test script for WebVTT combining functionality."""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wwdctools.cli.webvtt import _save_webvtt_files
from wwdctools.models import WWDCSession


def create_test_webvtt_files():
    """Create test WebVTT files and combine them."""
    # Create test WebVTT content
    webvtt_content = [
        """WEBVTT

00:00:00.000 --> 00:00:05.000
This is the first subtitle from file 1.

00:00:05.000 --> 00:00:10.000
This is the second subtitle from file 1.""",
        """WEBVTT

00:00:10.000 --> 00:00:15.000
This is the first subtitle from file 2.

00:00:15.000 --> 00:00:20.000
This is the second subtitle from file 2.""",
        """WEBVTT

00:00:20.000 --> 00:00:25.000
This is the first subtitle from file 3.

00:00:25.000 --> 00:00:30.000
This is the second subtitle from file 3.""",
    ]

    # Create a test session
    session = WWDCSession(
        id="12345",
        title="Test Session",
        description="Test Description",
        year=2024,
        url="https://example.com",
        webvtt_urls=[
            "https://example.com/1.webvtt",
            "https://example.com/2.webvtt",
            "https://example.com/3.webvtt",
        ],
    )

    # Create a temporary output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    # Test individual file saving
    print("Saving individual WebVTT files...")
    _save_webvtt_files(session, webvtt_content, str(output_dir), False)

    # Test combined file saving
    combined_file = output_dir / "combined.webvtt"
    print(f"Saving combined WebVTT file to {combined_file}...")
    _save_webvtt_files(session, webvtt_content, str(combined_file), True)

    # Print the content of the combined file
    print("\nCombined WebVTT file content:")
    print("-" * 50)
    with open(combined_file, encoding="utf-8") as f:
        print(f.read())
    print("-" * 50)

    print("\nTest completed successfully!")


if __name__ == "__main__":
    create_test_webvtt_files()
