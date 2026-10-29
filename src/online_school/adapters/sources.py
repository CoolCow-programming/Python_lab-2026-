from __future__ import annotations

import copy
from collections.abc import Iterator, Generator
from contextlib import AbstractAsyncContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..domain.errors import SubmissionError
from .parser import decode_json


@dataclass(frozen=True, slots=True)
class SourceRecord:
    line_no: str
    raw: object | None = None
    error: SubmissionError | None = None


class SubmissionSource(Protocol):
    def open(self) -> AbstractAsyncContextManager[Iterator[SourceRecord]]: ...


class InMemorySource:
    def __init__(self, values: list[dict[str, object]]) -> None:
        self._values = copy.deepcopy(values)

    @contextmanager
    def open(self) -> Generator[Iterator[SourceRecord], None, None]:
        def records() -> Iterator[SourceRecord]:
            for number, raw in enumerate(self.values, start=1):
                yield SourceRecord(number, copy.deepcopy(raw))
        yield records()


class JSONLSource:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.last_closed: bool | None = None

    @contextmanager
    def open(self) -> Generator[Iterator[SourceRecord], None, None]:
        handle = self.path.open("r", encoding="utf-8")
        try:
            with handle:
                def record() -> Iterator[SourceRecord]:
                    for number, line in enumerate(handle, start=1):
                        try:
                            raw = decode_json(line)
                        except SubmissionError as exc:
                            yield SourceRecord(number, error=exc)
                        else:
                            yield SourceRecord(number, raw=raw)
                yield record()
        finally:
            self.last_closed = handle.closed
