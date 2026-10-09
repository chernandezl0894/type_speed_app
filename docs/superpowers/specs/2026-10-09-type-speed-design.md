# Type Speed Test — Design Specification

- Date: 2026-10-09
- Status: Approved
- Scope: Desktop GUI typing-speed test app (Python + Tkinter + uv)

## 1. Goal

A desktop application that measures typing speed over a paragraph of text.
The user types the displayed paragraph; the app highlights progress live,
measures completion time, reports WPM/accuracy, and persists the best
(all-time) completion time. Secondary goal: a clean, small codebase to
practice TDD and tooling with OpenCode.

## 2. Acceptance criteria

- All source code, tests, and identifiers in English.
- Tests written before implementation (TDD) for all non-GUI logic.
- Clean 3-layer architecture (core / services / ui) — organized but not
  enterprise-heavy (no hexagonal, no DI frameworks).
- Environment configured with linters/formatters/type checkers usable from
  Zed (ruff formatter, basedpyright).
- Highlight letters as they are typed; completed words turn green if
  correct, red if incorrect.
- Measure total time to complete the test.
- Paragraphs fetched from a free HTTP service; embedded fallback text if
  the service is unreachable.
- Best (fastest) time persisted across runs.

## 3. User-facing behavior

### 3.1 Test flow

1. On launch, the app fetches a paragraph (or uses the embedded fallback
   immediately if the network call fails or exceeds 3 s).
2. The paragraph is displayed; the timer starts on the first accepted
   character (a stray Backspace or Space does not start it).
3. Typed characters are highlighted live: correct vs incorrect vs current
   position vs pending.
4. Pressing Space (or Enter) closes the current word: the whole word is
   colored green if it matches the target, red otherwise; the cursor
   advances. The paragraph panel always displays the target characters
   (color conveys correctness), never the typed characters — typed text
   is visible in the input Entry while the word is in progress.
5. Backspace edits within the current (unfinished) word only; closed words
   cannot be reopened. On an empty current word, Backspace is a no-op.
6. The test finishes when the user presses Space (or Enter) after typing
   the last word (with or without errors) and the timer stops. Space on
   an empty word (double space, or space right after closing a word) is
   a no-op.
7. A results dialog (modal) shows: WPM, accuracy (%), total time, and
   "New best time!" when `save_if_better` returned True. The dialog
   offers Restart; it may also be closed without restarting — input
   stays inert (post-completion no-ops) until Restart is used. The
   header best-time label updates only when the save succeeded.
8. A "Restart" action (button in the header, always available; also
   offered by the results dialog) fetches a new paragraph and starts
   over. The best time remains displayed in the header.

### 3.2 Metrics

- **Time**: wall-clock from the first accepted character to completion,
  shown as `mm:ss.cs` (minutes, seconds, centiseconds).
- **WPM**: total typed characters / 5 / minutes (standard: 5 characters
  = 1 word), counting all characters of closed words plus the current
  in-progress word. If elapsed time is 0 (or negative), WPM is 0.0.
- **Accuracy**: `correct_positions / target_length * 100`, where
  `correct_positions` counts positions where the final typed char equals
  the target char; untyped positions count as incorrect. Overtyped chars
  do not enter the denominator; in non-final words they shift subsequent
  positional comparisons (§4.2's space-joined positional algorithm is
  operative), and they always mark the word red.
- **Best time**: minimum completion time ever achieved, persisted locally.

### 3.3 UI layout (simple, single window ~700x400)

- Header: title, live timer, live WPM (updated on the timer tick), best
  time (shown as `--:--.--` when `load_best()` returns None), and a
  persistent **Restart** button (always available — this is how Restart
  stays reachable after the results dialog is dismissed).
- Body: paragraph panel (Tk `Text` with color tags, with vertical
  scrollbar — 2-paragraph API payloads can exceed the window height).
  Input is captured
  via a focused visible `Entry` that displays the current word being
  typed (session is the source of truth; Entry is the focus target).
  Chosen over a bare `Text` with raw `<Key>` bindings for more reliable
  accented-character handling.
- Footer/status: subtle "offline text" indicator when the fallback
  paragraph is used.
- Results: modal dialog on completion with metrics and Restart button.

### 3.4 Visual encoding (tags)

| Tag       | Meaning                          | Style            |
|-----------|----------------------------------|------------------|
| `pending` | not yet typed                    | gray foreground  |
| `current` | cursor position                  | highlight / bold |
| `ok`      | typed correctly                  | green foreground |
| `bad`     | typed incorrectly                | red foreground   |

## 4. Architecture

```
src/type_speed/
  core/        # pure logic, no I/O, no Tkinter — fully unit-testable
    session.py # TypingSession: input handling, word state, timing
    stats.py   # WPM, accuracy, time formatting
  services/    # I/O boundaries
    paragraphs.py # HTTP fetch + embedded fallback (never raises to UI)
    records.py    # best-time persistence (JSON file)
  ui/          # Tkinter only
    widgets.py # paragraph Text widget with tag-based rendering
    app.py     # main window, timer loop, event wiring, results dialog
  __main__.py  # entry point: python -m type_speed
```

Dependency rule: `ui -> core, services`; `services -> core` (types only);
`core` depends on nothing (stdlib `time` injected for testability).
No layer imports `ui`.

### 4.1 core/session.py

`TypingSession(target: str, clock: Callable[[], float] = time.monotonic)`

State machine over the target text, word by word:

- `current_word_index`, `typed_word` (chars typed for the current word),
  `word_results: list[WordResult]` (`CORRECT` | `INCORRECT`), and
  `typed_words: list[str]` (the actual typed text of every closed word —
  the core→ui contract for final accuracy).
- `typed_char_count` property: total characters typed so far (closed
  words + current in-progress word) — used for live and final WPM.
- `handle_char(ch: str)`: accepts any single printable char into the
  current word. There is no hard length cap: chars typed beyond the
  target word's length stay in `typed_word` (visible in the Entry until
  the word is closed) and make the word INCORRECT. `CharStatus` tracks
  target positions only; overtyped chars have no anchor in the paragraph
  view. A word is CORRECT only when `typed_word == target_word` exactly.
- `handle_backspace()`: removes the last typed char of the current word;
  no-op when the current word is empty (closed words cannot be reopened).
- `handle_space()`: closes the current word (records its result) and
  advances to the next word; no-op when the current word is empty.
  Completion rule: the test finishes when the user presses Space after
  typing the last word (the UI also routes Enter to this handler);
  `is_finished` becomes True and the timer stops.
- Timer: starts on the first accepted char (first `handle_char` call) —
  stray no-op Backspace/Space does not start the clock;
  `elapsed_seconds` property is 0.0 before the timer starts and frozen
  at completion; `is_finished`.
- **Post-completion**: once `is_finished` is True, `handle_char`,
  `handle_backspace`, and `handle_space` are all no-ops (safe even if
  the Entry is refocused after the results dialog is dismissed).
- Exposes per-character status for rendering via
  `char_statuses() -> list[list[CharStatus]]`, target-driven (one list
  per target word, over its target positions) so a finished session with
  no current word still renders all words closed/uniform. **Closed words
  are uniform**: every char of a closed word is TYPED_OK if the word
  result is CORRECT, else TYPED_BAD (word-level green/red per §3.1;
  per-char nuance applies only to the in-progress word and PENDING
  words).

### 4.2 core/stats.py

Pure functions, exact signatures:

- `calculate_wpm(typed_chars: int, elapsed_seconds: float) -> float` —
  returns 0.0 when `elapsed_seconds <= 0`.
- `calculate_accuracy(target: str, typed: str) -> float` — aligns the
  two strings positionally; positions beyond `len(typed)` count as
  incorrect, and chars beyond `len(target)` never count as correct (they
  are ignored in the score, per §3.2); returns percentage in `[0, 100]`.
  An empty target returns 100.0. For the final accuracy, the UI builds
  `typed` by joining the session's `typed_words` with single spaces and
  appending the current in-progress word; the target comes from the same
  word list joined with single spaces (guaranteed by §4.3 normalization).
- `format_time(seconds: float) -> str` → `mm:ss.cs` (centiseconds
  truncated, not rounded).

### 4.3 services/paragraphs.py

- `fetch_paragraph(timeout: float = 3.0) -> ParagraphResult` where
  `ParagraphResult` is a `NamedTuple(text: str, source: Literal["api",
  "fallback"])`.
- Endpoint: `https://baconipsum.com/api/?type=meat-and-filler&paras=2&format=text`
  (plain text; verified reachable). Uses stdlib `urllib.request` only.
- **Normalization**: the returned text is normalized with
  `" ".join(text.split())` (collapses `\n\n`, runs of spaces; trims) so
  the target word list is always `text.split()` of non-empty single-
  spaced text. This keeps positional alignment in `calculate_accuracy`
  correct and guarantees a non-empty target.
- On any failure (timeout, HTTP error, payload empty or empty after
  normalization) returns embedded `FALLBACK_TEXT` (2-3 sentences,
  English, normalized the same way). Never raises.
- The fetch is synchronous at app startup / restart (before `mainloop`
  resumes rendering); a stall of at most the timeout (3 s) is accepted
  for this scope.

### 4.4 services/records.py

- Storage file: `~/.type_speed/best_time.json`
  `{"best_seconds": 12.34, "achieved_at": "2026-10-09T12:00:00Z"}`.
- `load_best(path: Path | None = None) -> float | None` — missing,
  corrupt, or unreadable file (any OSError, e.g. the path is a directory
  or permission denied) returns `None` (heals by overwriting on next
  save).
- `save_if_better(seconds: float, path: Path | None = None) -> bool` —
  returns True and persists when `seconds < best` (or no record),
  creating the parent directory (`mkdir(parents=True, exist_ok=True)`)
  inside the try block so first-run persistence of `~/.type_speed/`
  works. If the file or directory cannot be written (OSError), returns
  False and never raises (best time simply won't persist).
- Tests use `tmp_path`; production default path resolved at call time.

### 4.5 ui/

- `widgets.ParagraphView(tk.Text)`: read-only; `render(session:
  TypingSession)` rebuilds the paragraph from the session's target and
  CharStatus accessors (§4.1) with tags; constant font for stable
  alignment.
- `ui.app.TypeSpeedApp`: wires session + services + widgets; timer via
  `root.after(100, ...)`. Input: a focused `Entry` bound with per-key
  events (primary approach) — printable chars (`event.char`) go to
  `session.handle_char`, Backspace to `session.handle_backspace`,
  Space/Return to `session.handle_space` (then the Entry is cleared);
  the Entry's content is always re-synced from the session's current
  typed word. A key is treated as a typed character iff
  `len(event.char) == 1 and event.char.isprintable()`. `<Tab>` is
  consumed (bound) to prevent focus loss
  mid-test, and control characters / paste are ignored so the Entry
  display can't diverge from the session. `event.char` delivers
  composed accented characters, so no StringVar trace/diffing is
  needed. Results dialog; the persistent Restart button fetches a new
  paragraph.
- GUI logic kept minimal; anything non-trivial pushed down to `core`.

## 5. Testing strategy

- Framework: `pytest` + `pytest-cov`; config in `pyproject.toml`.
- `core/` and `services/`: 100% line coverage target; TDD red-green-
  refactor; no network in tests (`monkeypatch` urllib), no real home-dir
  writes (`tmp_path`).
- `ui/`: one smoke test (create window with `withdraw()`, inject a
  session, destroy) — requires a DISPLAY; skipped gracefully otherwise.
- Commands: `uv run pytest`, `uv run pytest --cov=type_speed`.

## 6. Tooling & environment

- Python 3.14 (uv-managed; Tkinter 9.0 verified working with DISPLAY).
- Package manager: uv (`uv sync`, `uv run ...`).
- Dev deps: pytest, pytest-cov, ruff, basedpyright.
- ruff: lint (E, F, I, UP, B) + format (line length 88); Zed is
  configured (`.zed/settings.json`, committed in the repo) to format on
  save with ruff and organize imports.
- basedpyright: strict-ish config in pyproject; Zed already references it.
- Entry: `uv run python -m type_speed`.

## 7. Deliverables & phases

0. Repo init, this spec, PROGRESS.md checklist.
1. Environment: pyproject complete, dev deps, tool configs.
2. Core (TDD): session + stats.
3. Services (TDD): paragraphs + records.
4. UI: Tkinter app, highlighting, timer, results dialog, smoke test.
5. Docs & polish: professional README, LICENSE (Unlicense), final
   PROGRESS.md, lint/format/test gate.

Each phase ends with a technical summary, verification commands for
manual review, and an updated PROGRESS.md checklist.

## 8. Out of scope (YAGNI)

- Multiplayer, accounts, leaderboards, cloud sync.
- Multiple paragraph languages / user-supplied text.
- Configurable test lengths, themes, sound.
- Packaging as an executable (pip/uv run is enough).

## 9. Risks & mitigations

- **Accented input via Tkinter**: mitigated by using a focused `Entry`
  with per-key `event.char` delivery (composed accented characters
  arrive as single chars); smoke-tested manually in Phase 4.
- **External API down**: embedded fallback text; 3 s timeout; UI shows a
  subtle offline indicator.
- **Tk 9.0 differences**: only standard `Text`/tags/`after` used — stable
  APIs across Tk 8.6/9.0.

## 10. License

Unlicense (public domain dedication): anyone may use, modify, and
distribute without attribution.
