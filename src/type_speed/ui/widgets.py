"""Custom Tkinter widgets for the typing test UI."""

import tkinter as tk

from type_speed.core.session import CharStatus, TypingSession

_STATUS_TO_TAG: dict[CharStatus, str] = {
    CharStatus.PENDING: "pending",
    CharStatus.TYPED_OK: "ok",
    CharStatus.TYPED_BAD: "bad",
    CharStatus.CURRENT: "current",
}

_FONT = ("Helvetica", 14)


class ParagraphView(tk.Text):
    """Read-only paragraph display that color-codes typing progress."""

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        super().__init__(
            master,
            font=_FONT,
            wrap="word",
            state="disabled",
            padx=12,
            pady=12,
            relief="solid",
            borderwidth=1,
            **kwargs,  # type: ignore[arg-type]
        )
        self.tag_configure("pending", foreground="#9aa0a6")
        self.tag_configure("ok", foreground="#1e8e3e")
        self.tag_configure("bad", foreground="#d93025")
        self.tag_configure("current", background="#fbbc04", foreground="#202124")

    def render(self, session: TypingSession) -> None:
        """Rebuild the displayed paragraph from the session state."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        statuses = session.char_statuses()
        for word_index, word in enumerate(session.target_words):
            if word_index > 0:
                self.insert("end", " ")
            word_statuses = statuses[word_index]
            for char_index, char in enumerate(word):
                tag = _STATUS_TO_TAG[word_statuses[char_index]]
                self.insert("end", char, tag)
        self.configure(state="disabled")
