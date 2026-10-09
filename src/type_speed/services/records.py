"""Best-time persistence as a small JSON file."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

_FILENAME: Final[str] = "best_time.json"
_DIR_NAME: Final[str] = ".type_speed"


def default_path() -> Path:
    """Resolve the production storage path under the user's home."""
    return Path.home() / _DIR_NAME / _FILENAME


def load_best(path: Path | None = None) -> float | None:
    """Return the stored best time in seconds, or None if absent/invalid."""
    target = path if path is not None else default_path()
    try:
        data: object = json.loads(target.read_text())
    except OSError, json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    seconds = cast("dict[str, object]", data).get("best_seconds")
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or seconds < 0
    ):
        return None
    return float(seconds)


def save_if_better(seconds: float, path: Path | None = None) -> bool:
    """Persist seconds when it beats the stored best; never raises."""
    target = path if path is not None else default_path()
    try:
        best = load_best(target)
        if best is not None and seconds >= best:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "best_seconds": seconds,
            "achieved_at": datetime.now(UTC).isoformat(),
        }
        target.write_text(json.dumps(payload))
    except OSError:
        return False
    return True
