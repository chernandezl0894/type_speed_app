"""Typing session state machine: input handling, word tracking, timing."""

import time
from collections.abc import Callable
from enum import Enum


class WordResult(Enum):
    """Outcome of a closed word."""

    CORRECT = "correct"
    INCORRECT = "incorrect"


class CharStatus(Enum):
    """Per-target-position rendering status."""

    PENDING = "pending"
    TYPED_OK = "typed_ok"
    TYPED_BAD = "typed_bad"
    CURRENT = "current"


class TypingSession:
    """Pure state machine over a target paragraph, advanced word by word.

    The clock is injectable for tests; production uses time.monotonic.
    """

    def __init__(
        self, target: str, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._clock = clock
        self._target_words = target.split()
        self._word_index = 0
        self._typed_word = ""
        self._typed_words: list[str] = []
        self._word_results: list[WordResult] = []
        self._started_at: float | None = None
        self._finished_at: float | None = None
        self._is_finished = not self._target_words

    @property
    def target_words(self) -> list[str]:
        return list(self._target_words)

    @property
    def word_index(self) -> int:
        return self._word_index

    @property
    def typed_word(self) -> str:
        return self._typed_word

    @property
    def typed_words(self) -> list[str]:
        return list(self._typed_words)

    @property
    def word_results(self) -> list[WordResult]:
        return list(self._word_results)

    @property
    def is_finished(self) -> bool:
        return self._is_finished

    @property
    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        end = self._finished_at if self._finished_at is not None else self._clock()
        return end - self._started_at

    @property
    def typed_char_count(self) -> int:
        return sum(len(word) for word in self._typed_words) + len(self._typed_word)

    def handle_char(self, ch: str) -> None:
        """Accept a single printable char into the current word."""
        if self._is_finished or len(ch) != 1 or not ch.isprintable():
            return
        if self._started_at is None:
            self._started_at = self._clock()
        self._typed_word += ch

    def handle_backspace(self) -> None:
        """Remove the last typed char of the current word."""
        if self._is_finished or not self._typed_word:
            return
        self._typed_word = self._typed_word[:-1]

    def handle_space(self) -> None:
        """Close the current word and advance; completes on the last word."""
        if self._is_finished or not self._typed_word:
            return
        target_word = self._target_words[self._word_index]
        if self._typed_word == target_word:
            result = WordResult.CORRECT
        else:
            result = WordResult.INCORRECT
        self._typed_words.append(self._typed_word)
        self._word_results.append(result)
        self._typed_word = ""
        if self._word_index == len(self._target_words) - 1:
            self._is_finished = True
            self._finished_at = self._clock()
        else:
            self._word_index += 1

    def char_statuses(self) -> list[list[CharStatus]]:
        """Per-word, per-target-position statuses for rendering.

        Closed words are uniform (all OK or all BAD per the word result).
        The in-progress word marks typed positions OK/BAD and the cursor
        position as CURRENT.
        """
        statuses: list[list[CharStatus]] = []
        for index, word in enumerate(self._target_words):
            is_closed = index < self._word_index or self._is_finished
            if is_closed:
                result = self._word_results[index]
                if result is WordResult.CORRECT:
                    uniform = CharStatus.TYPED_OK
                else:
                    uniform = CharStatus.TYPED_BAD
                statuses.append([uniform] * len(word))
            elif index == self._word_index:
                word_statuses: list[CharStatus] = []
                for position in range(len(word)):
                    if position < len(self._typed_word):
                        expected = word[position]
                        if self._typed_word[position] == expected:
                            word_statuses.append(CharStatus.TYPED_OK)
                        else:
                            word_statuses.append(CharStatus.TYPED_BAD)
                    elif position == len(self._typed_word):
                        word_statuses.append(CharStatus.CURRENT)
                    else:
                        word_statuses.append(CharStatus.PENDING)
                statuses.append(word_statuses)
            else:
                statuses.append([CharStatus.PENDING] * len(word))
        return statuses
