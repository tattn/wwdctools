"""Utility functions for WWDC Tools."""

import json

from .models import WWDCSession


def format_sample_code(session: WWDCSession, format_type: str = "md") -> str:
    """Format code samples based on the specified output format.

    Args:
        session: The session metadata with code samples.
        format_type: The output format (txt, md, json).

    Returns:
        The formatted code samples.
    """

    if format_type == "json":
        return json.dumps(
            {
                "id": session.id,
                "title": session.title,
                "year": session.year,
                "samples": [
                    {
                        "time": sample.time,
                        "title": sample.title,
                        "code": sample.code,
                    }
                    for sample in session.sample_codes
                ],
            },
            indent=2,
        )

    lines = []

    if format_type == "md":
        lines.append(f"# Code Samples from {session.title}")
        lines.append(f"[WWDC {session.year} - Session {session.id}]({session.url})\n")

        for sample in session.sample_codes:
            # Format time as MM:SS
            minutes = int(sample.time) // 60
            seconds = int(sample.time) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            # Create a timestamp link to the video
            timestamp_seconds = int(sample.time)
            timestamp_link = f"{session.url}?time={timestamp_seconds}"

            lines.append(f"## {sample.title}")
            lines.append(f"Time: [{time_str}]({timestamp_link})\n")
            lines.append("```")
            lines.append(sample.code)
            lines.append("```\n")
    else:
        # txt format
        lines.append(f"Code Samples from {session.title}")
        lines.append(f"WWDC {session.year} - Session {session.id}: {session.url}\n")

        for sample in session.sample_codes:
            # Format time as MM:SS
            minutes = int(sample.time) // 60
            seconds = int(sample.time) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            # Create a timestamp link to the video
            timestamp_seconds = int(sample.time)
            timestamp_link = f"{session.url}?time={timestamp_seconds}"

            lines.append(f"=== {sample.title} ===")
            lines.append(f"Time: {time_str} ({timestamp_link})\n")
            lines.append(sample.code)
            lines.append("\n" + "-" * 80 + "\n")

    return "\n".join(lines)
