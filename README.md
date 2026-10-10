# Type Speed Test

A desktop typing-speed test built with Python and Tkinter. Type a
paragraph as fast as you can; the app highlights your progress live,
measures your completion time, and tracks your personal best.

## Features

- **Live highlighting** — each character is colored as you type:
  green for correct, red for incorrect, with the current cursor position
  highlighted. Completed words turn solid green or red.
- **Real-time metrics** — a running timer, live words-per-minute (WPM),
  and accuracy are shown while you type.
- **Fetched paragraphs** — test text is pulled from a free public API
  ([Bacon Ipsum](https://baconipsum.com)); if the network is unavailable
  the app falls back to an embedded paragraph so it always works offline.
- **Personal best** — your fastest completion time is persisted to a
  local JSON file (`~/.type_speed/best_time.json`) and displayed in the
  header.
- **Results dialog** — on completion you get your time, WPM, accuracy,
  and a "New best time!" notice when you beat your record.

## Requirements

- Python 3.14+ (with Tkinter)
- [uv](https://docs.astral.sh/uv/) for environment management

Tkinter ships with the standard CPython distribution. On most systems it
is available out of the box; if `import tkinter` fails, install your
platform's Tk package (for example `sudo apt install python3-tk` on
Debian/Ubuntu).

## Installation

```bash
git clone <repository-url>
cd type_speed_app
uv sync
```

This creates a virtual environment (`.venv`) and installs the package in
editable mode along with the development tooling.

## Usage

Run the application:

```bash
uv run python -m type_speed
```

- Start typing to begin the timer.
- Press **Space** (or **Enter**) to finish each word. Words you complete
  turn green (correct) or red (incorrect).
- Press **Backspace** to correct the current word before submitting it.
- The test ends when you complete the final word; a results dialog shows
  your stats.
- Click **Restart** (header or results dialog) to fetch a new paragraph
  and try again.

## Development

All commands run inside the uv-managed environment.

| Task | Command |
| ---- | ------- |
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov=type_speed` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type-check | `uv run basedpyright` |

The project follows test-driven development: tests are written and
observed failing before each piece of production logic is implemented.
`core/` and `services/` maintain 100% line coverage.

### Project structure

```
src/type_speed/
├── core/          # Pure logic — no I/O, no Tkinter
│   ├── session.py # TypingSession: input handling, word state, timing
│   └── stats.py   # WPM, accuracy, time formatting
├── services/      # I/O boundaries
│   ├── paragraphs.py # HTTP fetch + embedded fallback
│   └── records.py    # best-time persistence (JSON)
├── ui/            # Tkinter presentation
│   ├── widgets.py # ParagraphView with color tags
│   └── app.py     # main window, timer loop, results dialog
└── __main__.py    # python -m type_speed entry point
tests/             # pytest suite (TDD)
docs/superpowers/specs/  # design specification
```

The dependency rule is one-directional: `ui` may import `core` and
`services`; `services` may import `core`; `core` depends on nothing but
the standard library. This keeps the logic independently testable and the
GUI thin.

## Design

The full design specification lives in
[`docs/superpowers/specs/2026-10-09-type-speed-design.md`](docs/superpowers/specs/2026-10-09-type-speed-design.md).
Current progress is tracked in [`PROGRESS.md`](PROGRESS.md).

## License

This project is released into the public domain under the
[Unlicense](LICENSE). Use it, modify it, and redistribute it freely — no
attribution required.
