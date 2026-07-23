import asyncio
from datetime import datetime

from models.api_record import ApiRecord
from services.api_logger import ApiLogger


def make_record(index: int) -> ApiRecord:
    return ApiRecord(
        timestamp=datetime.now(),
        method="GET",
        url=f"https://example.test/{index}",
        status=200,
        elapsed_ms=1,
        response_headers={},
        response_body=None,
        response_size=0,
    )


def test_api_logger_uses_fifo_limit() -> None:
    async def exercise() -> None:
        logger = ApiLogger(max_records=2)
        await logger.add(make_record(1))
        await logger.add(make_record(2))
        await logger.add(make_record(3))
        assert [item.url for item in await logger.records()] == [
            "https://example.test/2",
            "https://example.test/3",
        ]

    asyncio.run(exercise())
