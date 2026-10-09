"""Tests for core.session TypingSession state machine."""

from type_speed.core.session import CharStatus, TypingSession, WordResult


class FakeClock:
    """Deterministic clock for session timing tests."""

    def __init__(self, start: float = 100.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def make_session(
    target: str = "hello world", start: float = 100.0
) -> tuple[TypingSession, FakeClock]:
    clock = FakeClock(start)
    return TypingSession(target, clock=clock), clock


def type_word(session: TypingSession, word: str) -> None:
    for char in word:
        session.handle_char(char)


class TestInit:
    def test_splits_target_into_words(self) -> None:
        session, _ = make_session("one two  three")
        assert session.target_words == ["one", "two", "three"]

    def test_starts_at_first_word(self) -> None:
        session, _ = make_session()
        assert session.word_index == 0
        assert session.typed_word == ""
        assert session.is_finished is False

    def test_elapsed_is_zero_before_start(self) -> None:
        session, _ = make_session()
        assert session.elapsed_seconds == 0.0

    def test_empty_target_is_finished_immediately(self) -> None:
        session, _ = make_session("")
        assert session.is_finished is True


class TestHandleChar:
    def test_appends_char_to_current_word(self) -> None:
        session, _ = make_session()
        type_word(session, "hel")
        assert session.typed_word == "hel"

    def test_starts_timer_on_first_accepted_char(self) -> None:
        session, clock = make_session()
        assert session.elapsed_seconds == 0.0
        session.handle_char("h")
        clock.now = 105.0
        assert session.elapsed_seconds == 5.0

    def test_ignores_empty_and_multichar_and_control(self) -> None:
        session, _ = make_session()
        session.handle_char("")
        session.handle_char("ab")
        session.handle_char("\n")
        assert session.typed_word == ""
        assert session.elapsed_seconds == 0.0  # timer not started by no-ops

    def test_noop_when_finished(self) -> None:
        session, _ = make_session("hi")
        type_word(session, "hi")
        session.handle_space()
        session.handle_char("x")
        assert session.is_finished is True
        assert session.typed_word == ""


class TestHandleBackspace:
    def test_removes_last_char(self) -> None:
        session, _ = make_session()
        type_word(session, "hel")
        session.handle_backspace()
        assert session.typed_word == "he"

    def test_noop_on_empty_word(self) -> None:
        session, _ = make_session()
        session.handle_backspace()
        assert session.typed_word == ""
        assert session.elapsed_seconds == 0.0

    def test_noop_when_finished(self) -> None:
        session, _ = make_session("hi")
        type_word(session, "hi")
        session.handle_space()
        session.handle_backspace()
        assert session.typed_word == ""
        assert session.is_finished is True


class TestHandleSpace:
    def test_closes_correct_word_and_advances(self) -> None:
        session, _ = make_session()
        type_word(session, "hello")
        session.handle_space()
        assert session.typed_words == ["hello"]
        assert session.word_results == [WordResult.CORRECT]
        assert session.word_index == 1
        assert session.typed_word == ""

    def test_closes_incorrect_word(self) -> None:
        session, _ = make_session()
        type_word(session, "hallo")
        session.handle_space()
        assert session.word_results == [WordResult.INCORRECT]

    def test_overtyped_word_is_incorrect(self) -> None:
        session, _ = make_session("hi there")
        type_word(session, "hix")
        session.handle_space()
        assert session.word_results == [WordResult.INCORRECT]
        assert session.typed_words == ["hix"]

    def test_noop_on_empty_word(self) -> None:
        session, _ = make_session()
        session.handle_space()
        assert session.word_index == 0
        assert session.is_finished is False

    def test_completes_on_last_word(self) -> None:
        session, clock = make_session("hi yo")
        type_word(session, "hi")
        session.handle_space()
        type_word(session, "yo")
        clock.now = 110.0
        session.handle_space()
        assert session.is_finished is True
        assert session.elapsed_seconds == 10.0

    def test_double_space_is_noop(self) -> None:
        session, _ = make_session()
        type_word(session, "hello")
        session.handle_space()
        session.handle_space()
        assert session.word_index == 1
        assert session.is_finished is False

    def test_elapsed_frozen_after_completion(self) -> None:
        session, clock = make_session("hi")
        type_word(session, "hi")
        clock.now = 104.0
        session.handle_space()
        clock.now = 500.0
        assert session.elapsed_seconds == 4.0


class TestTypedCharCount:
    def test_counts_closed_and_current_word_chars(self) -> None:
        session, _ = make_session()
        type_word(session, "hello")
        session.handle_space()
        type_word(session, "wo")
        assert session.typed_char_count == 7


class TestCharStatuses:
    def test_initial_first_char_current_rest_pending(self) -> None:
        session, _ = make_session("hi yo")
        assert session.char_statuses() == [
            [CharStatus.CURRENT, CharStatus.PENDING],
            [CharStatus.PENDING, CharStatus.PENDING],
        ]

    def test_current_and_typed_positions(self) -> None:
        session, _ = make_session("hi yo")
        type_word(session, "hz")
        statuses = session.char_statuses()
        assert statuses[0] == [CharStatus.TYPED_OK, CharStatus.TYPED_BAD]
        # "z" is typed; cursor would sit past the target word (no CURRENT anchor)
        assert statuses[1] == [CharStatus.PENDING, CharStatus.PENDING]

    def test_current_char_marked(self) -> None:
        session, _ = make_session("hi")
        session.handle_char("h")
        assert session.char_statuses()[0] == [CharStatus.TYPED_OK, CharStatus.CURRENT]

    def test_closed_correct_word_uniform(self) -> None:
        session, _ = make_session("hi yo")
        type_word(session, "hi")
        session.handle_space()
        assert session.char_statuses()[0] == [CharStatus.TYPED_OK, CharStatus.TYPED_OK]

    def test_closed_incorrect_word_uniform(self) -> None:
        session, _ = make_session("hi yo")
        type_word(session, "hz")
        session.handle_space()
        assert session.char_statuses()[0] == [
            CharStatus.TYPED_BAD,
            CharStatus.TYPED_BAD,
        ]

    def test_finished_session_renders_all_closed(self) -> None:
        session, _ = make_session("hi")
        type_word(session, "hi")
        session.handle_space()
        assert session.char_statuses() == [[CharStatus.TYPED_OK, CharStatus.TYPED_OK]]
