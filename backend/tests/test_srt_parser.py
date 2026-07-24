import pytest

from app.services.srt_parser import SrtParseError, parse_srt

VALID_SRT = """1
00:00:01,000 --> 00:00:03,500
Hello there.

2
00:00:04,000 --> 00:00:06,250
General Kenobi.
"""


def test_parse_srt_returns_ordered_entries():
    result = parse_srt(VALID_SRT)

    assert result == [
        (1000, 3500, "Hello there."),
        (4000, 6250, "General Kenobi."),
    ]


def test_parse_srt_handles_multi_line_text():
    content = "1\n00:00:01,000 --> 00:00:03,000\nLine one\nLine two\n"

    result = parse_srt(content)

    assert result == [(1000, 3000, "Line one\nLine two")]


def test_parse_srt_handles_crlf_line_endings():
    content = VALID_SRT.replace("\n", "\r\n")

    result = parse_srt(content)

    assert result == [
        (1000, 3500, "Hello there."),
        (4000, 6250, "General Kenobi."),
    ]


def test_parse_srt_raises_on_empty_content():
    with pytest.raises(SrtParseError):
        parse_srt("")


def test_parse_srt_raises_on_plain_text():
    with pytest.raises(SrtParseError):
        parse_srt("just some plain text\nwith no timing information at all")


def test_parse_srt_raises_on_bad_timing_format():
    content = "1\n00:00:01 --> 00:00:03\nHello\n"

    with pytest.raises(SrtParseError):
        parse_srt(content)


def test_parse_srt_raises_on_missing_text():
    content = "1\n00:00:01,000 --> 00:00:03,000\n"

    with pytest.raises(SrtParseError):
        parse_srt(content)
