import logging
import os

import webvtt as webvtt_py

logger = logging.getLogger("wwdctools")


def combine_webvtt_files(input_files: list[str], output_path: str) -> None:
    """Combine multiple WebVTT files into a single file.

    This function takes a list of WebVTT file paths, parses them,
    deduplicates captions, and writes a combined WebVTT file.
    The function handles:
    - Removing duplicate captions with the same timestamp and text
    - Removing captions whose text is fully contained in the next caption
    - Properly formatting the output WebVTT file

    Args:
        input_files: List of paths to WebVTT files to combine.
        output_path: Path where the combined WebVTT will be saved.

    Example:
        >>> from wwdctools import combine_webvtt_files
        >>> combine_webvtt_files(
        ...     ["subtitle1.webvtt", "subtitle2.webvtt"],
        ...     "combined.webvtt"
        ... )
    """
    logger.debug(f"Combining {len(input_files)} WebVTT files to {output_path}")

    # Process each file and extract captions
    all_captions = []

    for temp_file in input_files:
        # Parse the WebVTT file
        vtt = webvtt_py.read(temp_file)

        # Add captions to the combined list
        all_captions.extend(vtt.captions)

    # Deduplicate captions
    deduplicated_captions = []
    unique_caption_map = {}

    for caption in all_captions:
        # Create clean text from caption
        text = caption.text.strip()

        # Create a unique key for this caption based on timestamp and text
        caption_key = f"{caption.start}_{text}"

        if caption_key not in unique_caption_map:
            unique_caption_map[caption_key] = len(deduplicated_captions)
            deduplicated_captions.append(caption)

    # Remove captions contained in subsequent ones
    final_captions = []

    # Compare each caption with the next one to detect text overlap
    for i in range(len(deduplicated_captions)):
        current = deduplicated_captions[i]

        # Check if this caption's text is repeated in the next caption
        if i < len(deduplicated_captions) - 1:
            next_caption = deduplicated_captions[i + 1]

            # If current caption text is fully contained in the next caption
            # and they have different timestamps, skip this one
            if (
                current.text in next_caption.text
                and current.start != next_caption.start
                and current.end != next_caption.end
            ):
                continue

        final_captions.append(current)

    # Write the combined WebVTT file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")

        for caption in final_captions:
            f.write(f"{caption.start} --> {caption.end}\n")
            f.write(f"{caption.text}\n\n")

    logger.debug(
        f"Combined {len(all_captions)} captions into "
        f"{len(final_captions)} unique captions"
    )


def combine_webvtt_content(webvtt_content: list[str], output_path: str) -> None:
    """Combine multiple WebVTT content strings into a single file.

    This is a convenience function that first saves the WebVTT content
    to temporary files and then uses combine_webvtt_files to combine them.
    The function handles:
    - Creating temporary files for each WebVTT content string
    - Calling combine_webvtt_files to do the actual combination
    - Cleaning up temporary files after combination

    Args:
        webvtt_content: List of WebVTT content strings.
        output_path: Path where the combined WebVTT will be saved.

    Example:
        >>> from wwdctools import combine_webvtt_content
        >>> combine_webvtt_content(
        ...     ["WEBVTT\\n\\n00:00:00.000 --> 00:00:05.000\\nSubtitle 1.",
        ...      "WEBVTT\\n\\n00:00:05.000 --> 00:00:10.000\\nSubtitle 2."],
        ...     "combined.webvtt"
        ... )
    """
    import tempfile

    # First, save individual files to a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save each WebVTT content to a temporary file
        temp_files = []
        for i, content in enumerate(webvtt_content):
            temp_file = os.path.join(temp_dir, f"sequence_{i}.webvtt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
            temp_files.append(temp_file)

        # Process and combine all WebVTT files
        combine_webvtt_files(temp_files, output_path)
