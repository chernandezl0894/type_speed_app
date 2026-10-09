"""Tests for services.records best-time persistence."""

import json
from pathlib import Path
from typing import Any

import pytest

from type_speed.services import records


class TestLoadBest:
    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert records.load_best(path=tmp_path / "missing.json") is None

    def test_valid_file_returns_seconds(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        payload = {"best_seconds": 12.34, "achieved_at": "2026-01-01T00:00:00Z"}
        path.write_text(json.dumps(payload))
        assert records.load_best(path=path) == 12.34

    def test_corrupt_json_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text("{not json")
        assert records.load_best(path=path) is None

    def test_non_dict_json_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text(json.dumps([1, 2, 3]))
        assert records.load_best(path=path) is None

    def test_missing_key_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text(json.dumps({"achieved_at": "2026-01-01T00:00:00Z"}))
        assert records.load_best(path=path) is None

    def test_wrong_type_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text(json.dumps({"best_seconds": "fast"}))
        assert records.load_best(path=path) is None

    def test_negative_seconds_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text(json.dumps({"best_seconds": -5.0}))
        assert records.load_best(path=path) is None

    def test_boolean_seconds_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        path.write_text(json.dumps({"best_seconds": True}))
        assert records.load_best(path=path) is None

    def test_path_is_directory_returns_none(self, tmp_path: Path) -> None:
        assert records.load_best(path=tmp_path) is None


class TestSaveIfBetter:
    def test_first_record_is_saved(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        assert records.save_if_better(10.0, path=path) is True
        assert records.load_best(path=path) == 10.0

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "dir" / "best.json"
        assert records.save_if_better(10.0, path=path) is True
        assert records.load_best(path=path) == 10.0

    def test_faster_time_replaces_record(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        records.save_if_better(10.0, path=path)
        assert records.save_if_better(8.0, path=path) is True
        assert records.load_best(path=path) == 8.0

    def test_slower_time_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        records.save_if_better(10.0, path=path)
        assert records.save_if_better(12.0, path=path) is False
        assert records.load_best(path=path) == 10.0

    def test_equal_time_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        records.save_if_better(10.0, path=path)
        assert records.save_if_better(10.0, path=path) is False

    def test_unwritable_path_returns_false(self, tmp_path: Path) -> None:
        # tmp_path itself is a directory; a file cannot be created there
        assert records.save_if_better(10.0, path=tmp_path) is False

    def test_saved_file_has_expected_shape(self, tmp_path: Path) -> None:
        path = tmp_path / "best.json"
        records.save_if_better(10.5, path=path)
        data: Any = json.loads(path.read_text())
        assert data["best_seconds"] == 10.5
        assert isinstance(data["achieved_at"], str)


class TestDefaultPath:
    def test_default_path_is_under_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(records.Path, "home", lambda: tmp_path)
        assert records.default_path() == tmp_path / ".type_speed" / "best_time.json"

    def test_load_and_save_use_default_path_when_omitted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(records.Path, "home", lambda: tmp_path)
        assert records.load_best() is None
        assert records.save_if_better(9.0) is True
        assert records.load_best() == 9.0
