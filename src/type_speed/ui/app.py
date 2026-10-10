"""Main application window: wiring, timer loop, and results dialog."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path

from type_speed.core.session import TypingSession
from type_speed.core.stats import calculate_accuracy, calculate_wpm, format_time
from type_speed.services import records
from type_speed.services.paragraphs import ParagraphResult, fetch_paragraph
from type_speed.ui.widgets import ParagraphView

_TIMER_MS = 100


class TypeSpeedApp:
    """Single-window typing speed test."""

    def __init__(
        self,
        root: tk.Tk,
        paragraph: ParagraphResult,
        *,
        record_path: Path | None = None,
        fetcher: Callable[[], ParagraphResult] | None = None,
    ) -> None:
        self.root = root
        self.session = TypingSession(paragraph.text)
        self._paragraph = paragraph
        self._record_path = record_path
        self._fetcher = fetcher if fetcher is not None else fetch_paragraph
        self._best = records.load_best(path=record_path)

        self._build_header()
        self._build_body()
        self._build_input()
        self._build_footer()

        self.text_view.render(self.session)
        self._schedule_tick()
        self.input_entry.focus_set()

    # ------------------------------------------------------------------
    # Public surface used by key bindings and smoke tests
    # ------------------------------------------------------------------

    @property
    def text_view(self) -> ParagraphView:
        return self._text_view

    @property
    def offline_label(self) -> tk.Label:
        return self._offline_label

    @property
    def input_var(self) -> tk.StringVar:
        return self._input_var

    def handle_char(self, ch: str) -> None:
        self.session.handle_char(ch)
        self._after_input()

    def handle_backspace(self) -> None:
        self.session.handle_backspace()
        self._after_input()

    def handle_space(self) -> None:
        self.session.handle_space()
        self._after_input()
        if self.session.is_finished:
            self._finish()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(header, text="Type Speed Test", font=("Helvetica", 16, "bold")).pack(
            side="left"
        )

        self._timer_label = tk.Label(header, text="00:00.00", font=("Helvetica", 14))
        self._timer_label.pack(side="right", padx=(12, 0))

        self._wpm_label = tk.Label(header, text="0 WPM", font=("Helvetica", 14))
        self._wpm_label.pack(side="right", padx=(12, 0))

        self._best_label = tk.Label(
            header, text=self._best_text(), font=("Helvetica", 14)
        )
        self._best_label.pack(side="right", padx=(12, 0))

        self._restart_button = tk.Button(header, text="Restart", command=self.restart)
        self._restart_button.pack(side="right", padx=(12, 0))

    def _build_body(self) -> None:
        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=6)

        scrollbar = tk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")

        self._text_view = ParagraphView(body, yscrollcommand=scrollbar.set)
        self._text_view.pack(fill="both", expand=True)
        scrollbar.config(command=self._text_view.yview)  # type: ignore[arg-type]

    def _build_input(self) -> None:
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=12, pady=(6, 12))

        tk.Label(frame, text="Type:").pack(side="left")
        self._input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            frame, textvariable=self._input_var, font=("Helvetica", 14)
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.input_entry.bind("<Key>", self._on_key)

    def _build_footer(self) -> None:
        self._offline_label = tk.Label(self.root, text="", foreground="#9aa0a6")
        self._offline_label.pack(fill="x", padx=12, pady=(0, 8))
        self._update_offline_label()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _on_key(self, event: tk.Event[tk.Entry]) -> str:
        if event.keysym == "Tab":
            return "break"
        if event.keysym == "BackSpace":
            self.handle_backspace()
            return "break"
        if event.keysym in ("Return", "KP_Enter") or event.char == " ":
            self.handle_space()
            return "break"
        char = event.char
        if len(char) == 1 and char.isprintable():
            self.handle_char(char)
            return "break"
        return "break"

    def _after_input(self) -> None:
        self._input_var.set(self.session.typed_word)
        self.text_view.render(self.session)

    # ------------------------------------------------------------------
    # Timer & stats
    # ------------------------------------------------------------------

    def _schedule_tick(self) -> None:
        self._update_stats_labels()
        self.root.after(_TIMER_MS, self._schedule_tick)

    def _update_stats_labels(self) -> None:
        elapsed = self.session.elapsed_seconds
        self._timer_label.config(text=format_time(elapsed))
        wpm = calculate_wpm(self.session.typed_char_count, elapsed)
        self._wpm_label.config(text=f"{wpm:.0f} WPM")

    def _best_text(self) -> str:
        return format_time(self._best) if self._best is not None else "--:--.--"

    def _update_offline_label(self) -> None:
        if self._paragraph.source == "fallback":
            self._offline_label.config(text="Offline text (API unavailable)")
        else:
            self._offline_label.config(text="")

    # ------------------------------------------------------------------
    # Completion & restart
    # ------------------------------------------------------------------

    def _finish(self) -> None:
        elapsed = self.session.elapsed_seconds
        new_best = records.save_if_better(elapsed, path=self._record_path)
        if new_best:
            self._best = elapsed
            self._best_label.config(text=self._best_text())
        self._show_results(elapsed, new_best)

    def _show_results(self, elapsed: float, new_best: bool) -> None:
        typed_parts = list(self.session.typed_words)
        if self.session.typed_word:
            typed_parts.append(self.session.typed_word)
        typed_text = " ".join(typed_parts)
        target_text = " ".join(self.session.target_words)
        wpm = calculate_wpm(self.session.typed_char_count, elapsed)
        accuracy = calculate_accuracy(target_text, typed_text)

        dialog = tk.Toplevel(self.root)
        dialog.title("Results")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Results", font=("Helvetica", 14, "bold")).pack(
            padx=24, pady=(16, 8)
        )
        tk.Label(dialog, text=f"Time: {format_time(elapsed)}").pack(pady=2)
        tk.Label(dialog, text=f"WPM: {wpm:.0f}").pack(pady=2)
        tk.Label(dialog, text=f"Accuracy: {accuracy:.1f}%").pack(pady=2)
        if new_best:
            tk.Label(dialog, text="New best time!", foreground="#1e8e3e").pack(pady=2)

        button_row = tk.Frame(dialog)
        button_row.pack(pady=16)
        tk.Button(
            button_row,
            text="Restart",
            command=lambda: (self.restart(), dialog.destroy()),
        ).pack(side="left", padx=8)
        tk.Button(button_row, text="Close", command=dialog.destroy).pack(
            side="left", padx=8
        )

    def restart(self) -> None:
        paragraph = self._fetcher()
        self._paragraph = paragraph
        self.session = TypingSession(paragraph.text)
        self._best = records.load_best(path=self._record_path)
        self._input_var.set("")
        self._best_label.config(text=self._best_text())
        self._update_offline_label()
        self._update_stats_labels()
        self.text_view.render(self.session)
        self.input_entry.focus_set()


def main() -> None:
    """Application entry point."""
    root = tk.Tk()
    root.title("Type Speed Test")
    root.geometry("760x480")
    paragraph = fetch_paragraph()
    TypeSpeedApp(root, paragraph=paragraph)
    root.mainloop()
