"""In-memory API response store."""

from __future__ import annotations

import asyncio
from collections import deque

from models.api_record import ApiRecord


class ApiLogger:
    def __init__(self, max_records: int = 1000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be at least 1")
        self._records: deque[ApiRecord] = deque(maxlen=max_records)
        self._lock = asyncio.Lock()

    async def add(self, record: ApiRecord) -> None:
        async with self._lock:
            self._records.append(record)

    async def records(self) -> tuple[ApiRecord, ...]:
        async with self._lock:
            return tuple(self._records)

    async def clear(self) -> None:
        async with self._lock:
            self._records.clear()
