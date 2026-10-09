"""Tests for core.stats pure metric functions."""

from type_speed.core.stats import calculate_accuracy, calculate_wpm, format_time


class TestCalculateWpm:
    def test_standard_case(self) -> None:
        # 60 chars in 60 s = 12.0 WPM (5 chars = 1 word)
        assert calculate_wpm(60, 60.0) == 12.0

    def test_half_minute(self) -> None:
        # 100 chars in 30 s = 100 / 5 / 0.5 = 40.0 WPM
        assert calculate_wpm(100, 30.0) == 40.0

    def test_zero_elapsed_returns_zero(self) -> None:
        assert calculate_wpm(50, 0.0) == 0.0

    def test_negative_elapsed_returns_zero(self) -> None:
        assert calculate_wpm(50, -1.0) == 0.0

    def test_zero_chars(self) -> None:
        assert calculate_wpm(0, 60.0) == 0.0


class TestCalculateAccuracy:
    def test_perfect_match(self) -> None:
        assert calculate_accuracy("hello world", "hello world") == 100.0

    def test_partial_mismatch(self) -> None:
        # 9 of 11 positions correct (target "hello world" has 11 chars)
        assert calculate_accuracy("hello world", "helLo wOrld") == 9 / 11 * 100

    def test_typed_shorter_than_target(self) -> None:
        # 3 of 11 correct; untyped positions count as incorrect
        assert calculate_accuracy("hello world", "hel") == 3 / 11 * 100

    def test_overtyped_chars_do_not_enter_denominator(self) -> None:
        # exact target prefix; extra chars beyond len(target) ignored in score
        assert calculate_accuracy("hi", "hix") == 100.0

    def test_empty_target_returns_hundred(self) -> None:
        assert calculate_accuracy("", "anything") == 100.0

    def test_empty_typed(self) -> None:
        assert calculate_accuracy("abc", "") == 0.0


class TestFormatTime:
    def test_zero(self) -> None:
        assert format_time(0.0) == "00:00.00"

    def test_truncates_centiseconds(self) -> None:
        # 61.239 s -> 01:01.23 (truncate, do not round)
        assert format_time(61.239) == "01:01.23"

    def test_just_under_a_minute(self) -> None:
        assert format_time(59.999) == "00:59.99"

    def test_exact_seconds(self) -> None:
        assert format_time(90.0) == "01:30.00"

    def test_sub_second(self) -> None:
        assert format_time(0.05) == "00:00.05"
