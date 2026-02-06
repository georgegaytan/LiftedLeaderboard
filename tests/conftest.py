import contextlib
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

import pytest


@dataclass
class FakeDB:
    fetchone_results: list[Any] = field(default_factory=list)
    fetchall_results: list[Any] = field(default_factory=list)
    executed: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)
    last_query: str | None = None
    last_params: tuple[Any, ...] | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def fetchone(self, query: str, params=None):
        self.last_query = query
        self.last_params = tuple(params or ())
        if self.fetchone_results:
            return self.fetchone_results.pop(0)

    def fetchall(self, query: str, params=None):
        self.last_query = query
        self.last_params = tuple(params or ())
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def execute(self, query: str, params=None) -> None:
        self.executed.append((query, tuple(params or ())))


class FakeDBManager:
    def __init__(self, db: FakeDB):
        self._db = db

    def __call__(self):
        return self._db


@contextlib.contextmanager
def patched_dbmanager(monkeypatch, target_module, db: FakeDB) -> Iterator[FakeDB]:
    monkeypatch.setattr(target_module, 'DBManager', FakeDBManager(db))
    yield db


@pytest.fixture()
def fake_db() -> FakeDB:
    return FakeDB()


@pytest.fixture()
def clean_registry():
    from src.achievements.registry import registry

    before = list(registry.all())
    registry._rules.clear()  # type: ignore[attr-defined]
    try:
        yield registry
    finally:
        registry._rules.clear()  # type: ignore[attr-defined]
        for r in before:
            registry.register(r)
