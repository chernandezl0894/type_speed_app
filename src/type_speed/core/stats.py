"""Pure metric calculations for typing tests."""

from typing import Final

_CHARS_PER_WORD: Final[int] = 5


def calculate_wpm(typed_chars: int, elapsed_seconds: float) -> float:
    """Return words per minute using the 5-characters-per-word convention."""
    if elapsed_seconds <= 0:
        return 0.0
    return typed_chars / _CHARS_PER_WORD / (elapsed_seconds / 60)


def calculate_accuracy(target: str, typed: str) -> float:
    """Return the percentage of correctly typed target positions."""
    if not target:
        return 100.0
    correct = sum(
        1
        for target_char, typed_char in zip(target, typed, strict=False)
        if target_char == typed_char
    )
    return correct / len(target) * 100


def format_time(seconds: float) -> str:
    """Format seconds as mm:ss.cs with truncated centiseconds."""
    total_centiseconds = int(seconds * 100)
    centiseconds = total_centiseconds % 100
    total_seconds = total_centiseconds // 100
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}.{centiseconds:02d}"
