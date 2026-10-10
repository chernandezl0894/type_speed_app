"""UI smoke tests: window constructs and destroys without a mainloop."""

import tkinter as tk
from collections.abc import Iterator

import pytest

from type_speed.services.paragraphs import ParagraphResult
from type_speed.ui.app import TypeSpeedApp


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    window = tk.Tk()
    window.withdraw()
    yield window
    window.destroy()


def test_app_constructs_and_renders_paragraph(root: tk.Tk) -> None:
    paragraph = ParagraphResult(text="hello world", source="api")
    app = TypeSpeedApp(root, paragraph=paragraph)
    root.update()
    assert app.session.target_words == ["hello", "world"]
    assert app.text_view.get("1.0", "end-1c") == "hello world"


def test_app_shows_offline_indicator_for_fallback(root: tk.Tk) -> None:
    paragraph = ParagraphResult(text="hi", source="fallback")
    app = TypeSpeedApp(root, paragraph=paragraph)
    root.update()
    assert app.offline_label.cget("text") != ""


def test_app_hides_offline_indicator_for_api(root: tk.Tk) -> None:
    paragraph = ParagraphResult(text="hi", source="api")
    app = TypeSpeedApp(root, paragraph=paragraph)
    root.update()
    assert app.offline_label.cget("text") == ""


def test_handle_char_advances_session_and_input(root: tk.Tk) -> None:
    paragraph = ParagraphResult(text="hi", source="api")
    app = TypeSpeedApp(root, paragraph=paragraph)
    root.update()
    app.handle_char("h")
    app.handle_char("i")
    root.update()
    assert app.session.typed_word == "hi"
    assert app.input_var.get() == "hi"


def test_handle_space_completes_single_word(root: tk.Tk) -> None:
    paragraph = ParagraphResult(text="hi", source="api")
    app = TypeSpeedApp(root, paragraph=paragraph)
    root.update()
    for char in "hi":
        app.handle_char(char)
    app.handle_space()
    root.update()
    assert app.session.is_finished is True
