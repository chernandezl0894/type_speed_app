"""Paragraph fetching over HTTP with an embedded local fallback."""

import urllib.error
import urllib.request
from typing import Final, Literal, NamedTuple

API_URL: Final[str] = (
    "https://baconipsum.com/api/?type=meat-and-filler&paras=2&format=text"
)
DEFAULT_TIMEOUT: Final[float] = 3.0
FALLBACK_TEXT: Final[str] = (
    "The quick brown fox jumps over the lazy dog while the sun sets "
    "behind the distant mountains. A gentle breeze carries the scent of "
    "pine trees across the quiet valley where the old stone bridge spans "
    "the river."
)


class ParagraphResult(NamedTuple):
    """A paragraph to type and where it came from."""

    text: str
    source: Literal["api", "fallback"]


def normalize_text(text: str) -> str:
    """Collapse all whitespace runs into single spaces and trim."""
    return " ".join(text.split())


def fetch_paragraph(timeout: float = DEFAULT_TIMEOUT) -> ParagraphResult:
    """Fetch a paragraph from the API; fall back locally on any failure.

    Never raises: network errors, timeouts, HTTP errors, and empty or
    whitespace-only payloads all yield the embedded fallback text.
    """
    try:
        with urllib.request.urlopen(API_URL, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError:
        return ParagraphResult(text=FALLBACK_TEXT, source="fallback")
    text = normalize_text(payload)
    if not text:
        return ParagraphResult(text=FALLBACK_TEXT, source="fallback")
    return ParagraphResult(text=text, source="api")
