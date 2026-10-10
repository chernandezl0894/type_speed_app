# Progress

Checklist of delivered work per phase. Updated at the end of every phase.

**Status: COMPLETE** — all phases delivered.

## Phase 0 — Repo + Spec

- [x] Initialize git repository and base commit (editor/tooling configs)
- [x] Write design spec (`docs/superpowers/specs/2026-10-09-type-speed-design.md`)
- [x] Spec review loop with subagent (5 iterations, approved)
- [x] Create this PROGRESS checklist
- [x] User reviews the spec (gate)

## Phase 1 — Environment + tooling

- [x] Complete `pyproject.toml`: dev deps (pytest, pytest-cov, ruff, basedpyright)
- [x] Configure ruff (lint E,F,I,UP,B + format, line length 88)
- [x] Configure pytest (`testpaths`, coverage addopts) and coverage
- [x] Configure basedpyright in `pyproject.toml` (strict)
- [x] `uv sync` and verify: `uv run ruff check . && uv run pytest` clean

## Phase 2 — Core (TDD)

- [x] `core/stats.py`: `calculate_wpm` (red → green)
- [x] `core/stats.py`: `calculate_accuracy` (red → green)
- [x] `core/stats.py`: `format_time` (red → green)
- [x] `core/session.py`: `TypingSession` init/target splitting (red → green)
- [x] `core/session.py`: `handle_char` + timer start on first accepted char
- [x] `core/session.py`: `handle_backspace` (in-word, empty no-op)
- [x] `core/session.py`: `handle_space` (close word, empty no-op, completion)
- [x] `core/session.py`: post-completion no-ops; `elapsed_seconds` freeze
- [x] `core/session.py`: `typed_words`, `typed_char_count`, `char_statuses`
- [x] All tests green; core coverage 100%

## Phase 3 — Services (TDD)

- [x] `services/paragraphs.py`: normalization helper
- [x] `services/paragraphs.py`: `fetch_paragraph` success (mocked HTTP)
- [x] `services/paragraphs.py`: fallback on timeout/HTTP error/empty payload
- [x] `services/records.py`: `load_best` (missing/corrupt/OSError → None)
- [x] `services/records.py`: `save_if_better` (new/improve/no-improve/mkdir/OSError)
- [x] All tests green; services coverage 100%

## Phase 4 — UI (Tkinter)

- [x] `ui/widgets.py`: `ParagraphView.render` with tags (ok/bad/current/pending)
- [x] `ui/app.py`: layout (header with timer/WPM/best/Restart, paragraph + scrollbar, Entry)
- [x] `ui/app.py`: key bindings (printable, Backspace, Space/Enter, Tab consumed)
- [x] `ui/app.py`: timer loop (`after(100)`), live WPM
- [x] `ui/app.py`: results dialog (WPM, accuracy, time, new-best, Restart)
- [x] `ui/app.py`: offline indicator when fallback text is used
- [x] `__main__.py` entry point
- [x] `tests/test_ui_smoke.py` (window construct, offline indicator, typing flow)
- [x] Manual verification: real API fetch + end-to-end typing simulation

## Phase 5 — Docs & polish

- [x] Professional `README.md` (description, install, usage, development, structure, license)
- [x] `LICENSE` (Unlicense)
- [x] Final `PROGRESS.md` update
- [x] Final gate: `uv run ruff check --fix . && uv run ruff format . && uv run pytest`
