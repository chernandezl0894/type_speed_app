"""Tests for services.paragraphs HTTP fetch with local fallback."""

import io
import urllib.error
from email.message import Message

import pytest

from type_speed.services import paragraphs
from type_speed.services.paragraphs import (
    FALLBACK_TEXT,
    ParagraphResult,
    normalize_text,
)


def make_response(payload: bytes) -> io.BytesIO:
    return io.BytesIO(payload)


def patch_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: bytes | None = b"Some sample paragraph text.",
    error: Exception | None = None,
) -> list[dict[str, object]]:
    """Patch urllib.request.urlopen; record call args; simulate payload or error."""
    calls: list[dict[str, object]] = []

    def fake_urlopen(url: str, timeout: float) -> io.BytesIO:  # noqa: ARG001
        calls.append({"url": url, "timeout": timeout})
        if error is not None:
            raise error
        assert payload is not None
        return make_response(payload)

    monkeypatch.setattr(paragraphs.urllib.request, "urlopen", fake_urlopen)
    return calls


class TestNormalizeText:
    def test_collapses_whitespace_and_newlines(self) -> None:
        assert normalize_text("hello\n\n  world\tfoo") == "hello world foo"

    def test_trims(self) -> None:
        assert normalize_text("  spaced out  ") == "spaced out"

    def test_empty_stays_empty(self) -> None:
        assert normalize_text("   \n\n  ") == ""


class TestFetchParagraphSuccess:
    def test_returns_api_source_and_normalized_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patch_urlopen(monkeypatch, payload=b"Hello\n\n  world.")
        result = paragraphs.fetch_paragraph()
        assert result == ParagraphResult(text="Hello world.", source="api")

    def test_passes_timeout_to_urlopen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = patch_urlopen(monkeypatch)
        paragraphs.fetch_paragraph(timeout=5.0)
        assert calls[0]["timeout"] == 5.0

    def test_calls_api_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = patch_urlopen(monkeypatch)
        paragraphs.fetch_paragraph()
        assert "baconipsum.com" in str(calls[0]["url"])

    def test_default_timeout_is_three_seconds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = patch_urlopen(monkeypatch)
        paragraphs.fetch_paragraph()
        assert calls[0]["timeout"] == 3.0


class TestFetchParagraphFallback:
    def test_network_error_returns_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patch_urlopen(monkeypatch, error=urllib.error.URLError("down"))
        result = paragraphs.fetch_paragraph()
        assert result.source == "fallback"
        assert result.text == FALLBACK_TEXT

    def test_timeout_error_returns_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patch_urlopen(monkeypatch, error=TimeoutError("too slow"))
        result = paragraphs.fetch_paragraph()
        assert result.source == "fallback"

    def test_http_error_returns_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        error = urllib.error.HTTPError(
            "https://example.com", 500, "Server Error", hdrs=Message(), fp=None
        )
        patch_urlopen(monkeypatch, error=error)
        result = paragraphs.fetch_paragraph()
        assert result.source == "fallback"

    def test_empty_payload_returns_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patch_urlopen(monkeypatch, payload=b"")
        result = paragraphs.fetch_paragraph()
        assert result.source == "fallback"
        assert result.text == FALLBACK_TEXT

    def test_whitespace_only_payload_returns_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patch_urlopen(monkeypatch, payload=b"  \n\n \t ")
        result = paragraphs.fetch_paragraph()
        assert result.source == "fallback"


class TestFallbackText:
    def test_is_non_empty_normalized_english_text(self) -> None:
        assert FALLBACK_TEXT
        assert FALLBACK_TEXT == normalize_text(FALLBACK_TEXT)

    def test_paragraph_result_is_named_tuple(self) -> None:
        result = ParagraphResult(text="abc", source="fallback")
        assert result.text == "abc"
        assert result.source == "fallback"
