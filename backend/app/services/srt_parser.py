import re

_TIMESTAMP_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
_TIMING_LINE_RE = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})")


class SrtParseError(Exception):
    """Raised when the given content is not well-formed SRT."""


def _parse_timestamp(raw: str) -> int:
    match = _TIMESTAMP_RE.match(raw.strip())
    if not match:
        raise SrtParseError(f"Invalid timestamp: {raw!r}")
    hours, minutes, seconds, millis = (int(part) for part in match.groups())
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def parse_srt(content: str) -> list[tuple[int, int, str]]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise SrtParseError("SRT content is empty")

    blocks = re.split(r"\n\s*\n", normalized)

    results: list[tuple[int, int, str]] = []
    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip() != ""]
        if len(lines) < 3:
            raise SrtParseError(f"Malformed SRT block: {block!r}")

        index_line = lines[0].strip()
        if not index_line.isdigit():
            raise SrtParseError(f"Expected numeric index line, got: {index_line!r}")

        timing_match = _TIMING_LINE_RE.match(lines[1].strip())
        if not timing_match:
            raise SrtParseError(f"Invalid timing line: {lines[1]!r}")

        start_ms = _parse_timestamp(timing_match.group(1))
        end_ms = _parse_timestamp(timing_match.group(2))

        text = "\n".join(lines[2:]).strip()
        if not text:
            raise SrtParseError(f"Subtitle block missing text: {block!r}")

        results.append((start_ms, end_ms, text))

    if not results:
        raise SrtParseError("No subtitle entries found")

    return results
