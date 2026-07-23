"""In-memory API response store."""

from __future__ import annotations

import asyncio

from models.api_record import ApiRecord


class ApiLogger:
    def __init__(self) -> None:
        self._records: list[ApiRecord] = []
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
